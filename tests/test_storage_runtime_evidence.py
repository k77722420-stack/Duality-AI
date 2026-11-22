"""Runtime evidence for TEC-5 and TEC-6 (Nov 22, 2026).

Linear verified both issues' mechanisms STATICALLY across six
looks and declined — correctly — to close their verification:
the existing concurrent-writer coverage used threads, and no
fault had ever been injected into an actual maintenance pass.
This file supplies the missing runtime evidence, at Ken's
direction (senior-hat recommendations, Nov 22, 2026):

  TEC-5 — two independent PROCESSES append to one JSON store
  file concurrently. The claim under test: the file lock held
  across reload–modify–save, plus reload-before-save with
  re-linking, loses no record and keeps the chain verifiable
  across process boundaries, not just threads.

  TEC-6 — faults injected into ACTUAL consolidation and pruning
  passes: the final write failing, and the pass's own hash
  recomputation failing partway (the mid-reseal case). The claim
  under test: maintenance computes the whole changed + resealed
  chain in memory and commits in exactly ONE atomic save, so a
  failure anywhere before the commit leaves the file
  byte-for-byte identical and reopening serves the pre-pass
  state, chain intact.
"""

import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from duality_ai.memory import (
    JsonFileStore,
    MemoryCloud,
    MemoryRecord,
)

T0 = "2026-11-21T00:00:00+00:00"
SRC = Path(__file__).resolve().parents[1] / "src"


def _fresh_cloud(path):
    return MemoryCloud(store=JsonFileStore(path))


# ---------------------------------------------------------------------
# TEC-5 — independent-process contention
# ---------------------------------------------------------------------

_WORKER = """
import sys
from duality_ai.memory import JsonFileStore, MemoryCloud

path, prefix, count = sys.argv[1], sys.argv[2], int(sys.argv[3])
cloud = MemoryCloud(store=JsonFileStore(path))
for i in range(count):
    cloud.remember(
        "episodic",
        f"{prefix} memory {i}",
        "evidence",
        tags=["evidence"],
        created_at="2026-11-21T00:00:00+00:00",
    )
"""


def test_two_processes_append_without_loss(tmp_path):
    """Two processes, one file, fifteen appends each, launched
    together. Every record lands, and the chain verifies — the
    lock + reload/relink discipline holds across processes."""
    path = tmp_path / "memory.json"
    worker = tmp_path / "worker.py"
    worker.write_text(_WORKER, encoding="utf-8")
    env = {"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"}
    processes = [
        subprocess.Popen(
            [sys.executable, str(worker), str(path), prefix, "15"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for prefix in ("alpha", "beta")
    ]
    for process in processes:
        _, stderr = process.communicate(timeout=180)
        assert process.returncode == 0, stderr

    cloud = _fresh_cloud(path)
    contents = sorted(r.content for r in cloud.store.all())
    expected = sorted(
        f"{prefix} memory {i}"
        for prefix in ("alpha", "beta")
        for i in range(15)
    )
    assert contents == expected
    assert cloud.verify_chain() is True


# ---------------------------------------------------------------------
# TEC-6 — fault injection into actual maintenance passes
# ---------------------------------------------------------------------


def _seed_episodes(path, tag="cats", count=3):
    cloud = _fresh_cloud(path)
    for i in range(count):
        cloud.remember(
            "episodic",
            f"episode number {i} about {tag}",
            "test",
            tags=[tag],
            created_at=T0,
        )
    return cloud


def test_consolidation_final_write_failure_leaves_file_untouched(
    tmp_path, monkeypatch
):
    """The commit itself fails: the batch discards its in-memory
    work, the file keeps its previous bytes, and reopening serves
    the pre-pass state — no summary, no consolidated tags, chain
    intact."""
    path = tmp_path / "memory.json"
    cloud = _seed_episodes(path)
    before = path.read_bytes()

    def failing_save(self):
        raise RuntimeError("injected final-write failure")

    monkeypatch.setattr(JsonFileStore, "_save_locked", failing_save)
    with pytest.raises(RuntimeError):
        cloud.consolidate(created_at=T0)

    assert path.read_bytes() == before
    reopened = _fresh_cloud(path)
    assert len(reopened.store.all()) == 3
    assert all(
        "consolidated" not in r.tags for r in reopened.store.all()
    )
    assert reopened.verify_chain() is True


def test_consolidation_mid_reseal_failure_leaves_file_untouched(
    tmp_path, monkeypatch
):
    """The pass dies partway through its own hash recomputation —
    the mid-reseal case. Nothing was committed, so the file is
    the pre-pass file, byte for byte."""
    path = tmp_path / "memory.json"
    cloud = _seed_episodes(path)
    before = path.read_bytes()

    original = MemoryRecord.compute_hash
    calls = {"n": 0}
    armed = {"on": True}

    def flaky_hash(self):
        if armed["on"]:
            calls["n"] += 1
            if calls["n"] >= 3:
                raise RuntimeError("injected mid-reseal failure")
        return original(self)

    monkeypatch.setattr(MemoryRecord, "compute_hash", flaky_hash)
    with pytest.raises(RuntimeError):
        cloud.consolidate(created_at=T0)
    armed["on"] = False  # the verification below hashes honestly

    assert calls["n"] >= 3  # the failure fired inside the pass
    assert path.read_bytes() == before
    reopened = _fresh_cloud(path)
    assert len(reopened.store.all()) == 3
    assert reopened.verify_chain() is True


def test_pruning_final_write_failure_leaves_file_untouched(
    tmp_path, monkeypatch
):
    """Same property on the other maintenance pass: a pruning
    whose commit fails forgets nothing on disk."""
    path = tmp_path / "memory.json"
    cloud = _fresh_cloud(path)
    from datetime import datetime, timezone

    t0 = datetime(2026, 11, 21, tzinfo=timezone.utc)
    old = (t0 - timedelta(days=300)).isoformat()
    cloud.remember(
        "episodic", "faded and unprotected", "test", created_at=old
    )
    cloud.remember("episodic", "written just now", "test", created_at=T0)
    before = path.read_bytes()

    def failing_save(self):
        raise RuntimeError("injected final-write failure")

    monkeypatch.setattr(JsonFileStore, "_save_locked", failing_save)
    with pytest.raises(RuntimeError):
        cloud.decay_and_prune(now=T0)

    assert path.read_bytes() == before
    reopened = _fresh_cloud(path)
    assert len(reopened.store.all()) == 2
    assert reopened.verify_chain() is True


def test_changed_consolidation_performs_exactly_one_save(
    tmp_path, monkeypatch
):
    """Linear's remaining TEC-6 assertion: maintenance that
    changes records commits through ONE save, not one per edit."""
    path = tmp_path / "memory.json"
    cloud = _seed_episodes(path)

    original = JsonFileStore._save_locked
    calls = {"n": 0}

    def counting_save(self):
        calls["n"] += 1
        return original(self)

    monkeypatch.setattr(JsonFileStore, "_save_locked", counting_save)
    created = cloud.consolidate(created_at=T0)
    assert len(created) == 1
    assert calls["n"] == 1
    assert _fresh_cloud(path).verify_chain() is True
