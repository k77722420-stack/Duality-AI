"""Salvage — quarantine-and-reseal (Ken's Decision 4).

The failure geometry these tests pin: verify_chain() is
all-or-nothing, so one corrupt record freezes attestation
and maintenance (prune refuses over a broken chain), while
recall() judges per record and keeps serving the intact
past. salvage() is the operator-invoked repair: records
failing their own seal are quarantined verbatim to a side
file; linkage-only breaks are resealed with the gap
recorded; the repair itself is attested in-chain.
"""

import json

import pytest

from duality_ai.memory import InMemoryStore, MemoryCloud


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
