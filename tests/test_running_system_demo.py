"""Tests for examples/running_system_demo.py — the composed system.

The demo wires the three skeletons together *in the example* (the
library classes do not call each other — THESIS-COMPLETE.md §6).
These tests assert the values the traces claim, so the worked trace
in docs/worked-trace.md rests on checked arithmetic, not on prose:

  Trace A (capstone §3): three pipeline runs are written to the
  Memory Cloud as episodic records; consolidation yields at least
  one semantic record; the provenance chain verifies.

  Trace B (capstone §4): the Layer Two thesis's worked example —
  Barrier(P0=4, m=0.30, C=100).respond(40) surges 52 replicas to a
  population of 56; stand_down() decodes 52 and restores 4; the
  capability record is recallable from the barrier's shelf by its
  signature tag (the demo's labeled substitute for the unbuilt
  recognition matcher); the chain verifies.
"""

import importlib.util
from pathlib import Path

_DEMO_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "running_system_demo.py"
)
_spec = importlib.util.spec_from_file_location(
    "running_system_demo", _DEMO_PATH
)
demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(demo)


# ---------------------------------------------------------------------------
# Trace A — one ordinary step (§3)
# ---------------------------------------------------------------------------


def test_trace_a_writes_three_episodic_records():
    result = demo.trace_a()
    episodes = result["episodes"]
    assert len(episodes) == 3
    for record in episodes:
        assert record.kind == "episodic"
        assert record.owner == "shared"
        assert record.source == "pipeline"
        assert record.stage == "post-gate"
        # The gate's outcome rides on every episode as a tag.
        assert "gate:proceed" in record.tags


def test_trace_a_consolidation_yields_semantic_knowledge():
    result = demo.trace_a()
    semantic = result["semantic_records"]
    assert len(semantic) >= 1
    for record in semantic:
        assert record.kind == "semantic"
        assert record.owner == "shared"
    contents = [record.content for record in semantic]
    assert "Consolidated 3 episodes about 'pipeline-run'." in contents


def test_trace_a_recall_returns_the_consolidated_precedent():
    result = demo.trace_a()
    recalled = result["recalled"]
    assert len(recalled) == 1
    assert recalled[0].kind == "semantic"
    assert recalled[0].content == (
        "Consolidated 3 episodes about 'pipeline-run'."
    )
    assert result["fourth_decision"] == "proceed"


def test_trace_a_chain_verifies():
    result = demo.trace_a()
    assert result["chain_verified"] is True
    assert result["head_hash"] != "DUALITY-MEMORY-START"


# ---------------------------------------------------------------------------
# Trace B — one attack (§4), the Layer Two thesis's worked example
# ---------------------------------------------------------------------------


def test_trace_b_sizing_law_matches_the_thesis_example():
    result = demo.trace_b()
    response = result["response"]
    # S = ceil(T x (1 + m)) = ceil(40 x 1.30) = 52; P = min(100, 56).
    assert response["threat_units"] == 40
    assert response["surge_replicas"] == 52
    assert response["target_population"] == 56
    assert response["population"] == 56
    assert response["ceiling_applied"] is False


def test_trace_b_stand_down_decodes_every_surplus_replica():
    result = demo.trace_b()
    # D = P - P0 = 56 - 4 = 52; the standing number is restored.
    assert result["stand_down"] == {"decoded": 52, "population": 4}


def test_trace_b_capability_record_is_filed_on_the_barriers_shelf():
    result = demo.trace_b()
    record = result["capability_record"]
    assert record.kind == "episodic"
    assert record.owner == "barrier"
    assert record.source == "barrier"
    assert "capability-record" in record.tags
    assert demo.ATTACK_TAG in record.tags


def test_trace_b_returning_attack_is_recognized_by_its_record():
    result = demo.trace_b()
    recognized = result["recognized"]
    assert len(recognized) == 1
    match = recognized[0]
    assert match.id == result["capability_record"].id
    assert match.owner == "barrier"
    assert demo.ATTACK_TAG in match.tags


def test_trace_b_chain_verifies():
    result = demo.trace_b()
    assert result["chain_verified"] is True
    # The single filed record is the chain's only link, so the head
    # is that record's own hash.
    assert result["head_hash"] == result["capability_record"].record_hash
