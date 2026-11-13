"""Unit tests for the Phase 4 hardening session (fake client).

The session itself lives in experiments/hardening_session.py; these
tests run it once against the scripted FakeModelClient and assert the
memory-integrity claims individually: the poisoned write is refused,
no stored record asserts the falsehood, consolidation stays clean,
the provenance chain verifies, and the audit returns exactly the
session's decisions. No network anywhere.
"""

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "experiments"))

import hardening_session as hs  # noqa: E402


@pytest.fixture(scope="module")
def session():
    return hs.run_session("fake")


def _assertion(session, fragment):
    for assertion in session["assertions"]:
        if fragment in assertion["name"]:
            return assertion
    raise AssertionError(f"no assertion names {fragment!r}")


def test_session_passes_end_to_end(session):
    failed = [a["name"] for a in session["assertions"] if not a["passed"]]
    assert session["passed"], f"failed assertions: {failed}"


def test_poisoned_write_is_refused(session):
    assertion = _assertion(session, "guarded write refuses the falsehood")
    assert assertion["passed"]
    control = _assertion(session, "control: the same write lands")
    assert control["passed"]


def test_no_record_asserts_the_falsehood(session):
    needle = hs.FALSEHOOD_PHRASE
    offenders = [
        record.id
        for record in session["cloud"].store.all()
        if needle in record.content.lower()
    ]
    assert offenders == []


def test_pipeline_wrote_nothing_during_the_poison_run(session):
    assertion = _assertion(session, "pipeline itself writes nothing")
    assert assertion["passed"]


def test_gate_stops_the_planting_attempt(session):
    poison_trace = session["traces"][-1]
    assert poison_trace["prompt"] == hs.POISON_PROMPT
    assert poison_trace["decision"] == "stop"
    assert poison_trace["released"] is False


def test_consolidation_is_clean(session):
    cloud = session["cloud"]
    semantics = cloud.store.find(kind="semantic")
    assert any("'refund-policy'" in r.content for r in semantics)
    assert not any(
        hs.FALSEHOOD_PHRASE in r.content.lower() for r in semantics
    )
    assertion = _assertion(session, "consolidation produces a semantic")
    assert assertion["passed"]


def test_chain_verifies(session):
    assert session["cloud"].verify_chain() is True


def test_audit_returns_exactly_the_sessions_decisions(session):
    cloud = session["cloud"]
    audit = cloud.recall(tag="gate-decision", kind="episodic")
    assert len(audit) == len(session["traces"]) == 4
    assertion = _assertion(session, "audit recall returns exactly")
    assert assertion["passed"]
