"""Regression tests for the fixes arising from Linear's first-pass
audit (Nov 12, 2026), verified by Lux the same day.

Finding 2 — an engaged hard clause whose directive is "proceed",
unopposed by any conflicting directive, fell through the gate's
legacy path and returned "stop": the opposite of the decision the
clause library configures. These tests pin the corrected behavior
for single and multiple "proceed" directives, and pin that "stop"
directives behave exactly as before.

Finding 3 — MemoryCloud.recall returned records built with
dataclasses.replace, which is shallow: the recalled record's tags
list was the SAME list object as the stored record's, so a caller
appending a tag (the audit's example: "constitutional") silently
rewrote stored memory outside the write path, invalidating hashes
and changing pruning eligibility. These tests pin mutation
isolation for the nested tags field on both storage backends,
extending the scalar-field isolation the round-trip test in
test_memory.py already covers.
"""

import json
from datetime import datetime, timezone

import pytest

from duality_ai.memory import InMemoryStore, JsonFileStore, MemoryCloud
from duality_ai.morality import MoralityGate

T0 = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


def make_gate(tmp_path, clauses):
    path = tmp_path / "clauses.json"
    path.write_text(
        json.dumps({"library": "test library", "clauses": clauses}),
        encoding="utf-8",
    )
    return MoralityGate(path)


def hard(clause_id, signal, directive):
    return {
        "id": clause_id,
        "kind": "hard",
        "signals": [signal],
        "directive": directive,
    }


# -- Finding 2: unopposed "proceed" directives ----------------------------


def test_single_proceed_directive_proceeds(tmp_path):
    gate = make_gate(tmp_path, [hard("H1", "x", "proceed")])
    decision, reasons = gate.evaluate({"signals": ["x"], "contexts": []})
    assert decision == "proceed"
    assert reasons[0]["outcome"] == "engaged_proceed"


def test_multiple_proceed_directives_proceed(tmp_path):
    gate = make_gate(
        tmp_path, [hard("H1", "x", "proceed"), hard("H2", "y", "proceed")]
    )
    decision, _ = gate.evaluate({"signals": ["x", "y"], "contexts": []})
    assert decision == "proceed"


def test_single_stop_directive_still_stops(tmp_path):
    gate = make_gate(tmp_path, [hard("H1", "x", "stop")])
    decision, reasons = gate.evaluate({"signals": ["x"], "contexts": []})
    assert decision == "stop"
    assert reasons[0]["outcome"] == "blocks"


def test_unengaged_proceed_directive_still_proceeds_plainly(tmp_path):
    gate = make_gate(tmp_path, [hard("H1", "x", "proceed")])
    decision, reasons = gate.evaluate({"signals": [], "contexts": []})
    assert decision == "proceed"
    assert reasons[0]["outcome"] == "not_engaged"


# -- Finding 3: recall mutation isolation, both backends -------------------


@pytest.fixture(params=["memory", "json"])
def store(request, tmp_path):
    if request.param == "memory":
        return InMemoryStore()
    return JsonFileStore(tmp_path / "memory.json")


def test_recalled_tags_do_not_alias_the_stored_record(store):
    cloud = MemoryCloud(store=store)
    record = cloud.remember(
        kind="episodic",
        content="A probe was detained at the north gate.",
        source="barrier",
        owner="barrier",
        tags=["attack"],
        created_at=T0,
    )
    recalled = cloud.recall(owner="barrier", now=T0)
    assert recalled[0].tags == ["attack"]
    # The audit's example: appending "constitutional" to the recalled
    # copy must not rewrite the stored record.
    recalled[0].tags.append("constitutional")
    stored = cloud.store.get(record.id)
    assert stored.tags == ["attack"]
    assert cloud.verify_chain() is True
