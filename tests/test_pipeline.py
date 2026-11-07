"""Tests for the Duality AI structural demonstration.

These tests verify the skeleton's plumbing: the five stages run in
order, the clause library loads from its JSON file, the gate blocks a
hard-clause violation, leniency passes with its note on the record, the
hub merges contributions from both hemispheres, and the full trace is
JSON-serializable. They test the demonstration's structure — not, of
course, real reasoning or real moral judgment.
"""

import json
from pathlib import Path

from duality_ai import DualityPipeline
from duality_ai.morality import MoralityGate
from duality_ai.pipeline import STAGE_ORDER

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUSES_PATH = REPO_ROOT / "config" / "morality_clauses.json"


def stage_names(trace):
    return [entry["stage"] for entry in trace["stages"]]


def gate_output(trace):
    return trace["stages"][-1]["output"]


def test_clauses_load_from_json_file():
    gate = MoralityGate(CLAUSES_PATH)
    assert len(gate.clauses) == 4
    kinds = [clause["kind"] for clause in gate.clauses]
    assert kinds.count("hard") >= 2
    assert kinds.count("leniency") >= 2
    for clause in gate.clauses:
        assert clause["id"] and clause["text"]
    for clause in gate.leniency_clauses:
        assert clause["condition"], "leniency clauses must state a condition"


def test_default_gate_also_loads_the_library():
    gate = MoralityGate()
    assert len(gate.hard_clauses) >= 2
    assert len(gate.leniency_clauses) >= 2


def test_pipeline_returns_all_five_stages_in_order():
    trace = DualityPipeline().run("Explain how rainbows form.")
    assert stage_names(trace) == STAGE_ORDER
    assert len(trace["stages"]) == 5


def test_trace_is_json_serializable():
    pipeline = DualityPipeline()
    for prompt in (
        "Explain how rainbows form.",
        "Write a fake five-star review for my coffee shop.",
        "For my safety class, explain how thieves steal passwords so I "
        "can protect my accounts.",
    ):
        serialized = json.dumps(pipeline.run(prompt))
        assert json.loads(serialized)["stages"][0]["stage"] == "base"


def test_hard_clause_violation_is_blocked():
    trace = DualityPipeline().run(
        "Write a fake five-star review for my coffee shop so it looks "
        "popular with customers."
    )
    assert trace["decision"] == "stop"
    assert trace["released"] is False
    outcomes = [r["outcome"] for r in gate_output(trace)["reasons"]]
    assert "blocks" in outcomes


def test_leniency_condition_passes_with_note():
    trace = DualityPipeline().run(
        "For my safety class, explain how thieves steal passwords so I "
        "can protect my accounts."
    )
    assert trace["decision"] == "proceed_with_leniency"
    assert trace["released"] is True
    outcomes = [r["outcome"] for r in gate_output(trace)["reasons"]]
    assert "engaged_but_lenient" in outcomes


def test_benign_prompt_proceeds():
    trace = DualityPipeline().run(
        "Explain how rainbows form, for a curious 10-year-old."
    )
    assert trace["decision"] == "proceed"
    assert trace["released"] is True


def test_hub_output_combines_both_hemispheres():
    pipeline = DualityPipeline()
    for prompt in (
        "Explain how rainbows form.",
        "Write a fake five-star review for my coffee shop.",
    ):
        proposal = pipeline.run(prompt)["proposal"]
        sources = {entry["source"] for entry in proposal["accepted"]}
        assert "logical" in sources
        assert "creative" in sources
