"""Tests for the Option A storage discipline — TEC-5 and TEC-6.

The author's decision (Ken, Nov 13, 2026;
docs/storage-decision-brief-2026-11-12.md): keep the JSON file
store, and fix the two audit findings with reload-before-save, a
file lock across the reload–modify–save, unique temp files, and
compute-then-commit-once maintenance. Implemented Nov 21, 2026.

TEC-5 was: two JsonFileStore instances over one file each hold a
snapshot; the second to save silently overwrites the first's
records. TEC-6 was: maintenance saves part-way through its work, so
an interruption can leave a readable file with a broken chain.

These tests stage exactly those situations — both instances are
constructed BEFORE either writes, so the second instance's snapshot
is genuinely stale — and verify nothing is lost, the provenance
chain still verifies end to end, and a failed maintenance batch
leaves the previous file byte-for-byte intact. They test the
discipline's bookkeeping, not a multi-user database: the brief's
own stated limit.
"""

from datetime import datetime, timedelta, timezone

import pytest

from duality_ai.memory import JsonFileStore, MemoryCloud

T0 = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)


def fresh_cloud(path):
    """A new cloud over a new store instance on the same file."""
    return MemoryCloud(store=JsonFileStore(path))


# -- TEC-5: no lost updates across instances ------------------------------


def test_second_instance_writes_do_not_lose_the_firsts_records(tmp_path):
    path = tmp_path / "memory.json"
    # Both stores constructed first: the second one's snapshot is
    # empty and stale before anyone writes.
    cloud_a = MemoryCloud(store=JsonFileStore(path))
    cloud_b = MemoryCloud(store=JsonFileStore(path))

    cloud_a.remember("episodic", "written by A", "test", created_at=T0)
    cloud_b.remember(
        "episodic", "written by B over a stale snapshot", "test",
        created_at=T0,
    )

    contents = {r.content for r in fresh_cloud(path).store.all()}
    assert contents == {
        "written by A",
        "written by B over a stale snapshot",
    }


def test_cross_instance_append_relinks_to_the_chain_head(tmp_path):
    path = tmp_path / "memory.json"
    cloud_a = MemoryCloud(store=JsonFileStore(path))
    cloud_b = MemoryCloud(store=JsonFileStore(path))

    first = cloud_a.remember("episodic", "A's record", "test",
                             created_at=T0)
    second = cloud_b.remember("episodic", "B's record", "test",
                              created_at=T0)

    # B chained its record to the genesis head it saw in its stale
    # snapshot; the reload–re-apply rule re-linked the append to the
    # real head, so the chain verifies over both records.
    assert second.prev_hash == first.record_hash
    assert fresh_cloud(path).verify_chain() is True


def test_alternating_instances_keep_every_record(tmp_path):
    path = tmp_path / "memory.json"
    clouds = [MemoryCloud(store=JsonFileStore(path)) for _ in range(2)]
    for round_no in range(3):
        for index, cloud in enumerate(clouds):
            cloud.remember(
                "episodic", f"round {round_no} from instance {index}",
                "test", created_at=T0,
            )
    stored = fresh_cloud(path)
    assert len(stored.store.all()) == 6
    assert stored.verify_chain() is True


# -- TEC-6: maintenance computes in memory and commits once -----------------


def test_stale_instance_prune_preserves_partner_records(tmp_path):
    path = tmp_path / "memory.json"
    cloud_a = MemoryCloud(store=JsonFileStore(path))
    cloud_b = MemoryCloud(store=JsonFileStore(path))  # stale snapshot

    old = T0 - timedelta(days=300)  # ten half-lives: far below 0.05
    cloud_a.remember("episodic", "old and faded", "test", created_at=old)
    cloud_a.remember("episodic", "fresh, from A", "test", created_at=T0)

    # B prunes from its stale snapshot. Without the batch reload, its
    # commit would rewrite the file from that snapshot and A's fresh
    # record would vanish with the faded one.
    assert cloud_b.decay_and_prune(now=T0) == 1
    stored = fresh_cloud(path)
    assert [r.content for r in stored.store.all()] == ["fresh, from A"]
    assert stored.verify_chain() is True


def test_stale_instance_consolidation_sees_partner_episodes(tmp_path):
    path = tmp_path / "memory.json"
    cloud_a = MemoryCloud(store=JsonFileStore(path))
    cloud_b = MemoryCloud(store=JsonFileStore(path))  # stale snapshot

    for i in range(3):
        cloud_a.remember(
            "episodic", f"probe number {i} at the gate", "barrier",
            owner="barrier", tags=["probe"], created_at=T0,
        )

    created = cloud_b.consolidate(created_at=T0)
    assert len(created) == 1
    stored = fresh_cloud(path)
    episodes = stored.store.find(kind="episodic")
    assert len(episodes) == 3
    assert all("consolidated" in r.tags for r in episodes)
    assert stored.verify_chain() is True


def test_failed_batch_leaves_the_file_untouched(tmp_path):
    path = tmp_path / "memory.json"
    cloud = MemoryCloud(store=JsonFileStore(path))
    record = cloud.remember("episodic", "committed", "test",
                            created_at=T0)
    before = path.read_bytes()

    store = JsonFileStore(path)
    with pytest.raises(RuntimeError):
        with store.batch():
            store.put(record)  # uncommitted work inside the batch
            raise RuntimeError("interrupted mid-maintenance")

    assert path.read_bytes() == before
    assert [r.content for r in fresh_cloud(path).store.all()] == [
        "committed"
    ]


# -- the mechanics: unique temp files, the lock file -------------------------


def test_saves_leave_no_temp_files_behind(tmp_path):
    path = tmp_path / "memory.json"
    cloud = MemoryCloud(store=JsonFileStore(path))
    for i in range(3):
        cloud.remember("episodic", f"record {i}", "test", created_at=T0)
    names = {p.name for p in tmp_path.iterdir()}
    assert names == {"memory.json", "memory.json.lock"}
