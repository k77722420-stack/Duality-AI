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

The last three are Linear's preservation cases (his hold on
75ac36d, Nov 23, 2026), kept verbatim in substance: a torn
quarantine tail must not swallow the next entry, a changed
corruption must be preserved on retry (payload-keyed
dedupe, not id-only), and a corrupt copied-id twin must not
take its honest original down with it (exact-record
removal, never delete-by-id).
"""

import json
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

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


# -- Linear's preservation cases (hold on 75ac36d) -------------


def _fresh_file_cloud(path):
    return MemoryCloud(store=JsonFileStore(path))


def _damaged_file_store(tmp_path):
    path = tmp_path / "store.json"
    cloud = _fresh_file_cloud(path)
    for i in range(3):
        assert cloud.remember("semantic", f"honest-{i}", "review")
    data = json.loads(path.read_text())
    data[1]["content"] = "corruption-v1"
    path.write_text(json.dumps(data))
    assert not _fresh_file_cloud(path).verify_chain()
    return path, data


def _quarantine_entries(path):
    result = []
    for line in path.read_text().splitlines():
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return result


@pytest.mark.parametrize("complete_tail", [False, True])
def test_tail_cannot_swallow_evidence(tmp_path, complete_tail):
    path, data = _damaged_file_store(tmp_path)
    quarantine = tmp_path / "quarantine.jsonl"
    prior = {
        "quarantined_at": "earlier",
        "reason": "seal_mismatch",
        "record": dict(data[0], id="earlier-incident"),
    }
    tail = (
        json.dumps(prior) if complete_tail
        else '{"quarantined_at":"unfinished'
    )
    quarantine.write_text(tail)  # No final newline.
    assert _fresh_file_cloud(path).salvage(quarantine)["status"] == "repaired"
    assert _fresh_file_cloud(path).verify_chain()
    assert any(
        e["record"] == data[1] for e in _quarantine_entries(quarantine)
    )


def test_changed_corruption_is_preserved_on_retry(tmp_path):
    path, data = _damaged_file_store(tmp_path)
    quarantine = tmp_path / "quarantine.jsonl"
    before = path.read_bytes()
    with patch(
        "duality_ai.memory.os.replace",
        side_effect=OSError("publication failure"),
    ):
        with pytest.raises(OSError):
            _fresh_file_cloud(path).salvage(quarantine)
    assert path.read_bytes() == before
    assert _quarantine_entries(quarantine)[0]["record"] == data[1]

    # Offline change between attempts; no concurrent writer.
    data[1]["content"] = "corruption-v2"
    path.write_text(json.dumps(data))
    assert _fresh_file_cloud(path).salvage(quarantine)["status"] == "repaired"
    assert _fresh_file_cloud(path).verify_chain()
    assert any(
        e["record"] == data[1] for e in _quarantine_entries(quarantine)
    )


def test_corrupt_twin_does_not_delete_honest_original(tmp_path):
    path = tmp_path / "twins.json"
    cloud = _fresh_file_cloud(path)
    assert cloud.remember("semantic", "honest original", "review")
    honest = json.loads(path.read_text())[0]
    twin = dict(honest)
    twin["content"] = "corrupted copied-id twin"
    twin["prev_hash"] = honest["record_hash"]
    path.write_text(json.dumps([honest, twin]))

    cloud = _fresh_file_cloud(path)
    assert [r.content for r in cloud.recall()] == ["honest original"]
    quarantine = tmp_path / "quarantine.jsonl"
    assert cloud.salvage(quarantine)["status"] == "repaired"
    assert _fresh_file_cloud(path).verify_chain()
    assert _quarantine_entries(quarantine)[0]["record"] == twin
    assert any(
        r.to_dict() == honest for r in _fresh_file_cloud(path).store.all()
    )


# -- Linear's round-2 cases (hold on 9230a5e) ------------------
#
# Classification must judge the sequence the repair batch
# reloaded from disk, not a stale in-memory snapshot; and
# exact removal must use canonical payload identity, never
# Python equality (1.0 == 1, but their hashes differ).


def _canonical(value):
    return json.dumps(value, sort_keys=True)


def test_stale_snapshot_cannot_launder_current_corruption(tmp_path):
    path = tmp_path / "store.json"
    quarantine = tmp_path / "quarantine.jsonl"
    original = _fresh_file_cloud(path)
    assert original.remember("semantic", "honest", "review")

    data = json.loads(path.read_text())
    data[0]["content"] = "corruption-v1"
    path.write_text(json.dumps(data))
    stale = _fresh_file_cloud(path)

    # Completed before salvage starts; no concurrent writer.
    data[0]["content"] = "corruption-v2"
    path.write_text(json.dumps(data))

    assert stale.salvage(quarantine)["status"] == "repaired"
    assert _fresh_file_cloud(path).verify_chain()
    entries = [
        json.loads(line) for line in quarantine.read_text().splitlines()
    ]
    assert any(
        e["record"]["content"] == "corruption-v2" for e in entries
    )
    assert all(
        r.content != "corruption-v2"
        for r in _fresh_file_cloud(path).recall()
    )


def test_python_equal_twin_cannot_replace_honest_original(tmp_path):
    path = tmp_path / "store.json"
    quarantine = tmp_path / "quarantine.jsonl"
    original = _fresh_file_cloud(path)
    assert original.remember("semantic", "honest", "review")

    honest = json.loads(path.read_text())[0]
    twin = dict(honest, strength=1)
    assert twin == honest
    assert _canonical(twin) != _canonical(honest)
    path.write_text(json.dumps([honest, twin]))

    assert _fresh_file_cloud(path).salvage(quarantine)["status"] == (
        "repaired"
    )
    assert _fresh_file_cloud(path).verify_chain()
    assert any(
        _canonical(r.to_dict()) == _canonical(honest)
        for r in _fresh_file_cloud(path).store.all()
    )


# -- Linear's round-3 case (hold on 89de400) -------------------
#
# Healthy salvage is a strict no-op: nothing written, nothing
# appended. Classification lives inside the batch (round 2),
# but an unchanged batch must exit without publication.


def test_healthy_salvage_performs_no_publication(tmp_path):
    path = tmp_path / "store.json"
    quarantine = tmp_path / "quarantine.jsonl"
    path.write_bytes(b"[]\n")
    cloud = MemoryCloud(store=JsonFileStore(path))

    with patch(
        "duality_ai.memory.os.replace",
        side_effect=AssertionError(
            "healthy salvage attempted publication"
        ),
    ):
        result = cloud.salvage(quarantine)

    assert result["status"] == "healthy"
    assert path.read_bytes() == b"[]\n"
    assert not quarantine.exists()


def test_healthy_salvage_creates_no_store_file(tmp_path):
    path = tmp_path / "store.json"
    quarantine = tmp_path / "quarantine.jsonl"
    cloud = MemoryCloud(store=JsonFileStore(path))
    assert cloud.salvage(quarantine)["status"] == "healthy"
    assert not path.exists()
    assert not quarantine.exists()
