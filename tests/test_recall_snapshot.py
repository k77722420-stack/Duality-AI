"""One verified snapshot per run (Perplexity's Ask 3, Nov 22,
2026; built the same evening).

_recall_precedent used to call cloud.recall() four times per
run — one global pass for the eligibility set, then one per
shelf — re-verifying every record's seal four times and
letting the four reads disagree about a store changing
underneath the run. Now a run recalls ONCE and draws the
eligibility set, the genuine-embedding map, the exclusions
surface, and the per-shelf precedent from that single
verified snapshot.
"""

import json

from duality_ai.memory import InMemoryStore
from duality_ai.system import DualitySystem


def _count_recalls(system):
    calls = []
    original = system.cloud.recall

    def counting(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    system.cloud.recall = counting
    return calls


def test_precedent_assembly_recalls_exactly_once():
    system = DualitySystem(store=InMemoryStore())
    system.run("Explain how rainbows form.")
    calls = _count_recalls(system)
    recall = system._recall_precedent()
    assert calls == [1]
    # The first run's episode is in the assembled precedent.
    assert any(recall[shelf] for shelf in recall)


def test_the_door_still_verifies_at_the_write_boundary():
    # The snapshot replaced the assembly's four passes with
    # one. The door's own verification recall at the episode
    # write is a DIFFERENT boundary — it re-checks the genuine
    # embeddings against the store as it stands at write time
    # (provenance binding) — and stays its own pass: a full
    # run with precedent recalls exactly twice.
    system = DualitySystem(store=InMemoryStore())
    system.run("Explain how rainbows form.")
    calls = _count_recalls(system)
    result = system.run("Explain how a bill becomes a law.")
    assert result["episode"]["written"] is True
    assert len(calls) == 2


def test_snapshot_keeps_shelves_strengths_and_exclusions():
    system = DualitySystem(store=InMemoryStore())
    cloud = system.cloud
    older = cloud.remember(
        kind="episodic", content="an older shared note",
        source="test", owner="shared",
    )
    newer = cloud.remember(
        kind="episodic", content="a newer shared note",
        source="test", owner="shared",
    )
    logical = cloud.remember(
        kind="episodic", content="a logical note",
        source="test", owner="logical",
    )
    assert older is not None and newer is not None and logical is not None
    # Corrupt one record out-of-band: it must be excluded and
    # surfaced, from the single pass, exactly once.
    victim = next(r for r in cloud.store.all() if r.id == newer.id)
    victim.content = "tampered"

    result = system.run("Give me a plain status summary.")
    shared_ids = [e["id"] for e in result["recall"]["shared"]]
    logical_ids = [e["id"] for e in result["recall"]["logical"]]
    assert older.id in shared_ids
    assert newer.id not in shared_ids
    assert logical_ids == [logical.id]
    assert system.last_recall_exclusions == [newer.id]
    assert json.dumps(result["recall"])
