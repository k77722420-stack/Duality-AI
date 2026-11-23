"""Salvage — quarantine-and-reseal (Ken's Decision 4).

The failure geometry these tests pin: verify_chain() is
all-or-nothing, so one corrupt record freezes attestation
and maintenance (prune refuses over a broken chain), while
recall() judges per record and keeps serving the intact
past. salvage() is the operator-invoked repair: records
failing their own seal are quarantined verbatim to a side
file; linkage-only breaks are resealed with the gap
recorded; the repair itself is attested in-chain.

The fifth test is Perplexity's interruption acceptance test
(Nov 23, 2026), run against the persistent backend: a repair
SIGKILLed after the quarantine append but before the batch
commit must publish nothing — the reopened store is the
original degraded one — and its retry must complete the
repair without preserving the same record twice.
"""

import json
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from duality_ai.memory import InMemoryStore, JsonFileStore, MemoryCloud


def _seeded_cloud(n=4):
    store = InMemoryStore()
    cloud = MemoryCloud(store=store)
    ids = []
    for i in range(n):
        record = cloud.remember(
            kind="semantic",
            content=f"honest record {i}",
            source="test",
            stage="intake",
            owner="shared",
            tags=["seed"],
        )
        ids.append(record.id)
    assert cloud.verify_chain()
    return cloud, store, ids


def test_healthy_store_salvage_is_a_noop(tmp_path):
    cloud, store, _ids = _seeded_cloud()
    quarantine = tmp_path / "quarantine.jsonl"
    report = cloud.salvage(quarantine)
    assert report["status"] == "healthy"
    assert report["quarantined"] == [] and report["gaps"] == []
    assert report["salvage_record_id"] is None
    assert report["chain_verified"] is True
    assert not quarantine.exists()
    assert len(store.all()) == 4  # no event record appended


def test_tampered_record_is_quarantined_and_chain_heals(tmp_path):
    cloud, store, ids = _seeded_cloud()
    victim = next(r for r in store.all() if r.id == ids[1])
    victim.content = "tampered words"  # seal no longer recomputes
    assert not cloud.verify_chain()

    quarantine = tmp_path / "quarantine.jsonl"
    report = cloud.salvage(quarantine)

    assert report["status"] == "repaired"
    assert report["quarantined"] == [ids[1]]
    assert report["chain_verified"] is True
    assert cloud.verify_chain()
    # The victim is out of the store; its honest neighbors serve.
    assert all(r.id != ids[1] for r in store.all())
    served = {r.id for r in cloud.recall()}
    assert ids[0] in served and ids[2] in served
    # The quarantine preserves the record verbatim, as evidence.
    lines = quarantine.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["reason"] == "seal_mismatch"
    assert entry["record"]["id"] == ids[1]
    assert entry["record"]["content"] == "tampered words"
    # The repair is attested in-chain, metadata only.
    event = next(
        r for r in store.all() if r.id == report["salvage_record_id"]
    )
    payload = json.loads(event.content)
    assert payload["event"] == "salvage"
    assert payload["quarantined"] == [
        {"id": ids[1], "reason": "seal_mismatch"}
    ]
    assert "tampered words" not in event.content


def test_deletion_gap_is_resealed_and_recorded(tmp_path):
    cloud, store, ids = _seeded_cloud()
    store.remove(ids[1])  # out-of-band deletion: seals fine, link broken
    assert not cloud.verify_chain()

    report = cloud.salvage(tmp_path / "quarantine.jsonl")

    assert report["status"] == "repaired"
    assert report["quarantined"] == []
    assert len(report["gaps"]) == 1
    assert report["gaps"][0]["record_id"] == ids[2]
    assert report["chain_verified"] is True
    assert len(store.find(kind="semantic")) == 4  # 3 kept + the event


def test_maintenance_thaws_after_salvage(tmp_path):
    cloud, store, ids = _seeded_cloud()
    victim = next(r for r in store.all() if r.id == ids[0])
    victim.content = "tampered words"
    # Maintenance refuses over a broken chain (the freeze).
    with pytest.raises(Exception):
        cloud.decay_and_prune()
    cloud.salvage(tmp_path / "quarantine.jsonl")
    # After the repair, the same maintenance runs.
    assert cloud.decay_and_prune() >= 0


# The salvage child for the interruption test: its reseal
# sleeps, so the parent's kill lands after the quarantine
# append has been written and closed — the implementation's
# durability point for the evidence — but before the store
# batch commits the repaired chain.
_SALVAGE_CHILD = """
import sys, time
sys.path.insert(0, sys.argv[1])
import duality_ai.memory as memory

_original = memory.MemoryCloud._reseal_chain
def _sleepy(self):
    time.sleep(60)
    return _original(self)
memory.MemoryCloud._reseal_chain = _sleepy

store = memory.JsonFileStore(sys.argv[2])
cloud = memory.MemoryCloud(store=store)
cloud.salvage(sys.argv[3])
"""


def test_interrupted_salvage_publishes_nothing_and_retry_preserves_once(
    tmp_path,
):
    store_path = tmp_path / "store.json"
    quarantine = tmp_path / "quarantine.jsonl"
    cloud = MemoryCloud(store=JsonFileStore(store_path))
    ids = []
    for i in range(3):
        record = cloud.remember(
            kind="semantic",
            content=f"honest record {i}",
            source="test",
            stage="intake",
            owner="shared",
            tags=["seed"],
        )
        ids.append(record.id)
    assert cloud.verify_chain()
    # Out-of-band tamper in the file itself: the middle
    # record's content changed, its stored hash did not.
    data = json.loads(store_path.read_text(encoding="utf-8"))
    assert data[1]["id"] == ids[1]
    data[1]["content"] = "tampered words"
    store_path.write_text(json.dumps(data), encoding="utf-8")

    def fresh():
        return MemoryCloud(store=JsonFileStore(store_path))

    degraded = fresh()
    assert not degraded.verify_chain()
    with pytest.raises(Exception):
        degraded.decay_and_prune()

    # Salvage in a separate process; terminate by SIGKILL once
    # the quarantine append is durable — not by an exception
    # that lets normal cleanup run.
    child = tmp_path / "salvage_child.py"
    child.write_text(_SALVAGE_CHILD, encoding="utf-8")
    repo = Path(__file__).resolve().parents[1]
    quarantine.touch()
    proc = subprocess.Popen(
        [
            sys.executable,
            str(child),
            str(repo / "src"),
            str(store_path),
            str(quarantine),
        ],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.time() + 30
    while quarantine.stat().st_size == 0:
        if proc.poll() is not None:
            raise AssertionError(
                f"salvage child exited early:\n{proc.stdout.read()}"
            )
        assert time.time() < deadline, "quarantine append never landed"
        time.sleep(0.05)
    proc.send_signal(signal.SIGKILL)
    proc.wait()
    assert proc.returncode == -signal.SIGKILL

    # Reopened from a fresh instance: the original degraded
    # store — no committed salvage event, maintenance still
    # frozen. The quarantine entry exists but is not a repair.
    reopened = fresh()
    assert [r.id for r in reopened.store.all()] == ids
    assert not reopened.verify_chain()
    assert not any(r.source == "salvage" for r in reopened.store.all())
    with pytest.raises(Exception):
        reopened.decay_and_prune()
    entries = [
        json.loads(line)
        for line in quarantine.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    assert entries[0]["record"]["id"] == ids[1]

    # Retry salvage to completion on a fresh instance.
    report = fresh().salvage(quarantine)
    assert report["status"] == "repaired"
    healed = fresh()
    assert healed.verify_chain()
    remaining = [r.id for r in healed.store.all()]
    assert ids[0] in remaining and ids[2] in remaining
    assert ids[1] not in remaining
    served = {r.id for r in healed.recall()}
    assert ids[1] not in served
    assert ids[0] in served and ids[2] in served
    events = [r for r in healed.store.all() if r.source == "salvage"]
    assert len(events) == 1
    # The evidence is recoverable — and preserved exactly once:
    # the interrupted attempt's append is the same incident,
    # not a second one.
    entries = [
        json.loads(line)
        for line in quarantine.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    victim_entries = [
        e for e in entries if e["record"]["id"] == ids[1]
    ]
    assert len(victim_entries) == 1
    assert victim_entries[0]["record"]["content"] == "tampered words"
    assert victim_entries[0]["reason"] == "seal_mismatch"
