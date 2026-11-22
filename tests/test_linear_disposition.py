"""Disposition round for Linear's whole-tree audit (2026-11-13).

Linear's whole-branch review supported the three Perplexity fixes
but kept the merge gate on HOLD and raised three further issues.
Each test here pins one disposition, reproduced by execution first:

1. Parser robustness — an oversized integer literal in a model
   reply made json.loads raise a plain ValueError (the interpreter's
   int-string conversion limit), which escaped LivePipeline.run()
   instead of producing the documented stopped trace.
2. Audit accuracy — (a) leniency granted by two different clauses
   was recorded as if only the first had applied; (b) in a
   three-party conflict, a clause that merely shared the winning
   directive was recorded as "prevails", and a pair of non-decisive
   clauses was recorded with the non-governing one as winner.
3. Documentation drift — KNOWN-LIMITATIONS.md #10 / the README
   inventory (fixed in the documents themselves; no test here).
"""

import json

from duality_ai.live import LivePipeline
from duality_ai.model import FakeModelClient
from duality_ai.morality import MoralityGate

GOOD_LOGICAL = (
    '{"checks": [], "flags": [], "signals": [], "pros": [], '
    '"cons": [], "stance": "explains"}'
)
GOOD_CREATIVE = (
    '{"alternatives": [{"id": "alt-direct", "text": "A plain answer."}]}'
)
GIANT_INT = "9" * 6000


def _pipeline(logical_reply, creative_reply=GOOD_CREATIVE):
    def responder(system, user):
        return logical_reply if "LOGICAL" in system else creative_reply

    return LivePipeline(FakeModelClient(responder))


def _gate(tmp_path, clauses):
    path = tmp_path / "clauses.json"
    path.write_text(
        json.dumps({"library": "disposition test library", "clauses": clauses}),
        encoding="utf-8",
    )
    return MoralityGate(path)


# --- 1. Parser robustness -------------------------------------------


def test_giant_int_logical_reply_fails_closed():
    reply = (
        '{"checks": [], "flags": [], "signals": [], "pros": ['
        + GIANT_INT
        + '], "cons": []}'
    )
    trace = _pipeline(reply).run("Tell me about gardening.")
    assert trace["decision"] == "stop"
    assert trace["released"] is False
    assert any(
        stage.get("error") == "format_failure"
        for stage in trace["stages"]
    )


def test_giant_int_creative_reply_fails_closed():
    reply = (
        '{"alternatives": [{"id": "alt-direct", "text": '
        + GIANT_INT
        + "}]}"
    )
    trace = _pipeline(GOOD_LOGICAL, reply).run("Tell me about gardening.")
    assert trace["decision"] == "stop"
    assert trace["released"] is False
    assert any(
        stage.get("error") == "format_failure"
        for stage in trace["stages"]
    )


# --- 2a. Leniency record names every covering clause -----------------


def test_split_leniency_cover_names_both_clauses(tmp_path):
    gate = _gate(
        tmp_path,
        [
            {
                "id": "H1",
                "kind": "hard",
                "signals": ["wrongdoing", "deception"],
            },
            {
                "id": "L-wrong",
                "kind": "leniency",
                "signals": ["wrongdoing"],
                "condition": "educational",
            },
            {
                "id": "L-dec",
                "kind": "leniency",
                "signals": ["deception"],
                "condition": "educational",
            },
        ],
    )
    decision, reasons = gate.evaluate(
        {"signals": ["wrongdoing", "deception"], "contexts": ["educational"]}
    )
    assert decision == "proceed_with_leniency"
    detail = next(
        r["detail"] for r in reasons if r["outcome"] == "engaged_but_lenient"
    )
    assert "L-wrong" in detail
    assert "L-dec" in detail


def test_single_clause_cover_keeps_classic_wording(tmp_path):
    gate = _gate(
        tmp_path,
        [
            {
                "id": "H1",
                "kind": "hard",
                "signals": ["wrongdoing", "deception"],
            },
            {
                "id": "L-both",
                "kind": "leniency",
                "signals": ["wrongdoing", "deception"],
                "condition": "educational",
            },
        ],
    )
    decision, reasons = gate.evaluate(
        {"signals": ["wrongdoing", "deception"], "contexts": ["educational"]}
    )
    assert decision == "proceed_with_leniency"
    detail = next(
        r["detail"] for r in reasons if r["outcome"] == "engaged_but_lenient"
    )
    assert detail == (
        "Signal(s) ['wrongdoing', 'deception'] engage this hard clause, "
        "but leniency clause L-both applies: its condition "
        "('educational') holds in this context. The step proceeds and "
        "the leniency is recorded."
    )


# --- 2b. Conflict winner attribution ---------------------------------


def _three_party_gate(tmp_path):
    return _gate(
        tmp_path,
        [
            {
                "id": "A-top-stop",
                "kind": "hard",
                "signals": ["wrongdoing"],
                "priority": 10,
            },
            {
                "id": "B-low-proceed",
                "kind": "hard",
                "signals": ["deception"],
                "priority": 0,
                "directive": "proceed",
            },
            {
                "id": "C-low-stop",
                "kind": "hard",
                "signals": ["deception"],
                "priority": 0,
            },
        ],
    )


def test_non_governing_clause_concurs_but_does_not_prevail(tmp_path):
    gate = _three_party_gate(tmp_path)
    decision, reasons = gate.evaluate(
        {"signals": ["wrongdoing", "deception"], "contexts": []}
    )
    assert decision == "stop"
    outcomes = {r["clause"]: r["outcome"] for r in reasons}
    assert outcomes["A-top-stop"] == "prevails"
    assert outcomes["B-low-proceed"] == "overridden"
    assert outcomes["C-low-stop"] == "concurs_with_outcome"
    detail = next(r["detail"] for r in reasons if r["clause"] == "C-low-stop")
    assert "A-top-stop" in detail


def test_non_decisive_pair_has_no_winner(tmp_path):
    gate = _three_party_gate(tmp_path)
    _, reasons = gate.evaluate(
        {"signals": ["wrongdoing", "deception"], "contexts": []}
    )
    gate_entry = next(r for r in reasons if "conflicts" in r)
    pairs = {tuple(c["clauses"]): c for c in gate_entry["conflicts"]}
    assert pairs[("A-top-stop", "B-low-proceed")]["winner"] == "A-top-stop"
    assert pairs[("B-low-proceed", "C-low-stop")]["winner"] is None
    assert pairs[("B-low-proceed", "C-low-stop")]["resolution"] == "R1"


def test_r2_trace_names_each_tied_scope(tmp_path):
    gate = _gate(
        tmp_path,
        [
            {
                "id": "X-stop",
                "kind": "hard",
                "signals": ["wrongdoing"],
                "priority": 0,
                "scope": "for class today",
            },
            {
                "id": "Y-proceed",
                "kind": "hard",
                "signals": ["deception"],
                "priority": 0,
                "directive": "proceed",
                "scope": "at home",
            },
            {
                "id": "Z-stop",
                "kind": "hard",
                "signals": ["deception"],
                "priority": 0,
                "scope": "in the lab",
            },
        ],
    )
    decision, reasons = gate.evaluate(
        {"signals": ["wrongdoing", "deception"], "contexts": []}
    )
    assert decision == "stop"
    gate_entry = next(r for r in reasons if "conflicts" in r)
    trace = "\n".join(gate_entry["conflicts"][0]["rules_applied"])
    assert "for class today" in trace
    assert "in the lab" in trace
