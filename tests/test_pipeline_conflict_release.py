"""End-to-end wiring check: a gate decision of "conflict" must NOT
release the step. The gate's conflict outcome (docs/clause-conflict-
design.md) is fail-closed by design; pipeline.py originally computed
`released` as `decision != "stop"`, which would have released a
conflicted step. This test drives the real pipeline with a temporary
clause library whose two hard clauses collide irreconcilably, and
asserts the step is held.
"""

import json

from duality_ai.pipeline import DualityPipeline


def _write_library(tmp_path):
    library = {
        "library": "test-conflict-library",
        "version": "0.0.1",
        "clauses": [
            {
                "id": "HX-duty-to-warn",
                "kind": "hard",
                "signals": ["danger"],
                "directive": "proceed",
                "priority": 50,
                "scope": "all steps",
                "text": "When danger is present, the warning step must proceed.",
            },
            {
                "id": "HY-duty-of-silence",
                "kind": "hard",
                "signals": ["danger"],
                "directive": "stop",
                "priority": 50,
                "scope": "all steps",
                "text": "When danger is present, nothing may be disclosed.",
            },
        ],
        "leniency_clauses": [],
    }
    path = tmp_path / "clauses.json"
    path.write_text(json.dumps(library), encoding="utf-8")
    return path


def test_conflict_decision_holds_the_step(tmp_path):
    pipeline = DualityPipeline(clauses_path=_write_library(tmp_path))
    # The hub is a demonstration stub whose signal vocabulary covers the
    # shipped library's patterns; to drive the wiring end to end, stub
    # the stub: the merged proposal carries the "danger" signal both
    # temp clauses watch for. What is under test is the seam itself —
    # gate decision "conflict" in, released=False out.
    pipeline.hub.merge = lambda request, logical, creative: {
        "summary": "A step both temp clauses claim.",
        "signals": ["danger"],
        "contexts": [],
    }
    result = pipeline.run("Assess this danger and respond.")
    assert result["decision"] == "conflict"
    assert result["released"] is False
