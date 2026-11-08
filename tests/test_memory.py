"""Tests for the Layer Three (Memory Cloud) structural demonstration.

These tests verify the foundation's bookkeeping as implemented in the
skeleton: writes chain into a provenance hash chain, tampering with a
stored record breaks the chain, recall ranks by decayed strength,
graceful forgetting prunes faded records but never protected ones,
consolidation distills a ripe cluster of episodes into one semantic
record exactly once, and a refusing write hook blocks a write. They
test the demonstration's arithmetic and record-keeping — not any real
learning, summarization, or memory service.
"""

from datetime import datetime, timedelta, timezone

import pytest

from duality_ai.memory import (
    GENESIS_HASH,
    InMemoryStore,
    JsonFileStore,
    MemoryCloud,
)

T0 = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)
ONE_DAY = timedelta(days=1)


def make_cloud(store):
    return MemoryCloud(store=store)


@pytest.fixture(params=["memory", "json"])
def store(request, tmp_path):
    if request.param == "memory":
        return InMemoryStore()
    return JsonFileStore(tmp_path / "memory.json")


# -- write / recall round-trip, both stores -------------------------------


def test_remember_recall_round_trip(store):
    cloud = make_cloud(store)
    record = cloud.remember(
        kind="episodic",
        content="The barrier detained a probe at the north gate.",
        source="barrier",
        owner="barrier",
        tags=["attack"],
        created_at=T0,
    )
    assert record is not None
    found = cloud.recall(owner="barrier", now=T0)
    assert [r.id for r in found] == [record.id]
    assert found[0].content == record.content
    # A recall at the moment of writing shows full, undecayed strength.
    assert found[0].strength == pytest.approx(1.0)
    # Recall returns copies: mutating one must not touch the store.
    found[0].content = "edited copy"
    assert cloud.store.get(record.id).content == record.content


def test_recall_filters_by_kind_owner_tag_and_text(store):
    cloud = make_cloud(store)
    cloud.remember("episodic", "a proof was checked", "hub",
                   owner="logical", tags=["proof"], created_at=T0)
    cloud.remember("episodic", "a story was drafted", "hub",
                   owner="creative", tags=["story"], created_at=T0)
    cloud.remember("semantic", "proofs are checked stepwise", "consolidation",
                   owner="shared", tags=["proof"], created_at=T0)
    assert len(cloud.recall(kind="episodic", now=T0)) == 2
    assert len(cloud.recall(owner="creative", now=T0)) == 1
    assert len(cloud.recall(tag="proof", now=T0)) == 2
    text_hits = cloud.recall(text="PROOF", now=T0)
    assert {r.owner for r in text_hits} == {"logical", "shared"}


# -- the provenance chain ---------------------------------------------------


def test_genesis_head_on_empty_store(store):
    cloud = make_cloud(store)
    assert cloud.head_hash() == GENESIS_HASH
    assert cloud.verify_chain() is True  # an empty chain is a true chain


def test_chain_verifies_after_several_writes(store):
    cloud = make_cloud(store)
    first = cloud.remember("episodic", "one", "test", created_at=T0)
    second = cloud.remember("episodic", "two", "test", created_at=T0)
    third = cloud.remember("semantic", "three", "test", created_at=T0)
    assert first.prev_hash == GENESIS_HASH
    assert second.prev_hash == first.record_hash
    assert third.prev_hash == second.record_hash
    assert cloud.head_hash() == third.record_hash
    assert cloud.verify_chain() is True


def test_tampering_with_stored_content_breaks_the_chain(store):
    cloud = make_cloud(store)
    record = cloud.remember("episodic", "the original words", "test",
                            created_at=T0)
    cloud.remember("episodic", "a later record", "test", created_at=T0)
    assert cloud.verify_chain() is True
    # An edit made outside the system's own operations: the stored
    # record's words change, but its seals do not.
    cloud.store.get(record.id).content = "words it never held"
    assert cloud.verify_chain() is False


# -- decay and graceful forgetting -------------------------------------------


def test_decay_after_ten_half_lives_falls_below_threshold():
    cloud = make_cloud(InMemoryStore())
    ten_half_lives_ago = T0 - timedelta(days=30 * 10)
    record = cloud.remember("episodic", "an old, faint memory", "test",
                            created_at=ten_half_lives_ago)
    decayed = cloud.recall(now=T0)[0]
    assert decayed.id == record.id
    # 0.5 ** 10 < 0.001 — far below the 0.05 prune threshold.
    assert decayed.strength < cloud.prune_threshold


def test_prune_forgets_faded_but_never_protected():
    cloud = make_cloud(InMemoryStore())
    old = T0 - timedelta(days=30 * 10)
    cloud.remember("episodic", "faded and unprotected", "test",
                   created_at=old)
    protected = cloud.remember(
        "semantic", "clause H1: the system shall not assist wrongdoing",
        "clause-library", tags=["constitutional"], created_at=old)
    fresh = cloud.remember("episodic", "written just now", "test",
                           created_at=T0)
    pruned = cloud.decay_and_prune(now=T0)
    assert pruned == 1
    remaining = {r.id for r in cloud.store.all()}
    # The faded record is gone; the equally old constitutional record
    # survives — the clauses are never forgettable — and so does the
    # fresh one. The chain re-seals over the survivors.
    assert remaining == {protected.id, fresh.id}
    assert cloud.verify_chain() is True


def test_recall_sorts_by_decayed_strength():
    cloud = make_cloud(InMemoryStore())
    cloud.remember("episodic", "written two half-lives ago", "test",
                   created_at=T0 - timedelta(days=60))
    cloud.remember("episodic", "written one half-life ago", "test",
                   created_at=T0 - timedelta(days=30))
    newest = cloud.remember("episodic", "written now", "test",
                            created_at=T0)
    ranked = cloud.recall(now=T0)
    assert ranked[0].id == newest.id
    assert [r.strength for r in ranked] == sorted(
        (r.strength for r in ranked), reverse=True)
    assert ranked[0].strength == pytest.approx(1.0)
    assert ranked[1].strength == pytest.approx(0.5)
    assert ranked[2].strength == pytest.approx(0.25)
    # Recall computed the decay without mutating the stored records.
    stored = cloud.store.get(newest.id)
    assert stored.strength == 1.0


# -- consolidation: the system's sleep ----------------------------------------


def test_consolidation_distills_a_ripe_cluster_once(store):
    cloud = make_cloud(store)
    for i in range(3):
        cloud.remember("episodic", f"probe number {i} at the gate",
                       "barrier", owner="barrier", tags=["probe"],
                       created_at=T0)
    created = cloud.consolidate(created_at=T0)
    assert len(created) == 1
    summary = created[0]
    assert summary.kind == "semantic"
    assert summary.content == "Consolidated 3 episodes about 'probe'."
    assert "consolidation" in summary.tags
    # The episodes are marked, so a second pass distills nothing new.
    episodes = cloud.store.find(kind="episodic")
    assert all("consolidated" in r.tags for r in episodes)
    assert cloud.consolidate(created_at=T0) == []
    # Marking and writing were system acts: the chain still verifies.
    assert cloud.verify_chain() is True


def test_consolidation_waits_for_a_ripe_cluster():
    cloud = make_cloud(InMemoryStore())
    for i in range(2):  # policy minimum is 3
        cloud.remember("episodic", f"rumor {i}", "test", tags=["rumor"],
                       created_at=T0)
    assert cloud.consolidate(created_at=T0) == []


# -- the guarded write ---------------------------------------------------------


def test_write_hook_can_refuse_a_write():
    cloud = make_cloud(InMemoryStore())
    cloud.set_write_hook(lambda record: False)
    assert cloud.remember("episodic", "never stored", "test",
                          created_at=T0) is None
    assert cloud.store.all() == []
    cloud.set_write_hook(None)
    assert cloud.remember("episodic", "stored once the hook clears",
                          "test", created_at=T0) is not None


def test_remember_validates_kind_and_owner():
    cloud = make_cloud(InMemoryStore())
    with pytest.raises(ValueError):
        cloud.remember("dream", "not a memory kind", "test")
    with pytest.raises(ValueError):
        cloud.remember("episodic", "bad shelf", "test", owner="middle")


# -- the reference backend: persistence -----------------------------------------


def test_json_file_store_persists_across_instances(tmp_path):
    path = tmp_path / "memory.json"
    first_cloud = MemoryCloud(store=JsonFileStore(path))
    first_cloud.remember("episodic", "written by the first instance",
                         "test", tags=["durable"], created_at=T0)
    first_cloud.remember("semantic", "and a second record", "test",
                         created_at=T0)
    # A new store instance over the same file sees the same memory,
    # and the provenance chain still verifies end to end.
    second_cloud = MemoryCloud(store=JsonFileStore(path))
    contents = {r.content for r in second_cloud.store.all()}
    assert contents == {"written by the first instance",
                        "and a second record"}
    assert second_cloud.verify_chain() is True
    assert second_cloud.head_hash() == first_cloud.head_hash()


def test_policy_is_loaded_from_json_by_default():
    cloud = MemoryCloud(store=InMemoryStore())
    assert cloud.halflife_days == 30
    assert cloud.prune_threshold == 0.05
    assert cloud.protected_tags == ["constitutional"]
    assert cloud.consolidate_min_episodes == 3
