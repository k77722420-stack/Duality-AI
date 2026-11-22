"""Fix round 8 — Linear's eighth look (Nov 22, 2026).

One finding, a regression round 7 introduced, verified by
execution before fixing (Lux verification, Nov 22, 2026 — every
value matched Linear's source-derived outcomes):

  HIGH — decoded inspection dropped previously detected
  performing evidence. Round 7's judged_performs checked each
  decoded string separately, replacing the raw-text check round
  6 had used. A production pattern spanning a JSON key and its
  value — {"write":"a fake review for my store"} — performs in
  the raw text but in neither decoded string alone, so
  educational leniency released a step the previous
  implementation stopped.

  Fix (inspection.py, Linear's prescription verbatim in
  effect): judged_performs retains the raw text's performing
  evidence IN ADDITION TO the decoded strings', after the full
  inspection — strict parsing and budget validation run first,
  so uninspectable content still raises rather than verdicts.
  Decoding adds visibility; it does not subtract it.

Linear's eighth look also closed TEC-6's verification gap and
marked every round-7 finding addressed; the HOLD was solely
this regression. TEC-12 and the broken-chain recall policy
remain Ken's decisions.
"""

import json

import pytest

from duality_ai.inspection import (
    UninspectableContentError,
    judged_performs,
    judged_signals,
)
from duality_ai.live import LivePipeline
from duality_ai.markers import performs
from duality_ai.model import FakeModelClient

SPANNING = '{"write":"a fake review for my store"}'
ENCODED_FLAGGED = r'{"answer":"Write a f\u0061ke review for my store."}'
FLAGGED_TEXT = "Write a fake review for my store."
BENIGN = "Explain how rainbows form."
EDUCATIONAL = (
    "For a fraud-awareness class, describe how fake-review scams "
    "work so students can recognize them."
)

_DECEPTION_LOGICAL = json.dumps(
    {
        "checks": [
            {
                "name": "no_deception_signal",
                "passed": False,
                "detail": "deception marker present",
            }
        ],
        "flags": ["signal:deception"],
        "signals": ["deception"],
        "stance": "explains",
        "pros": ["The request states a goal the system can address."],
        "cons": ["The request asks for content that would mislead."],
    }
)


def _model(logical_reply, creative_reply):
    def respond(system, user):
        if "CREATIVE HEMISPHERE" in system:
            return creative_reply
        if "LOGICAL HEMISPHERE" in system:
            return logical_reply
        raise AssertionError(f"unexpected system prompt: {system!r}")

    return FakeModelClient(respond)


def _creative(*alternatives):
    return json.dumps(
        {
            "alternatives": [
                {"id": alt_id, "text": text}
                for alt_id, text in alternatives
            ]
        }
    )


def test_spanning_pattern_is_raw_evidence_only():
    """The mechanism, pinned: the pattern performs in the raw
    text and in NEITHER decoded string alone — which is why a
    decoded-only check lost it, and why the signals (which the
    value string does carry) were never the gap."""
    assert performs(SPANNING) is True
    assert performs("write") is False
    assert performs("a fake review for my store") is False
    assert judged_signals(SPANNING) == ["deception"]


def test_judged_performs_unions_raw_and_decoded_evidence():
    """Raw evidence (the spanning pattern), decoded evidence
    (the escaped-letter answer), plain evidence, and the benign
    controls — the union keeps every source and invents none."""
    assert judged_performs(SPANNING) is True
    assert judged_performs(ENCODED_FLAGGED) is True
    assert judged_performs(FLAGGED_TEXT) is True
    assert judged_performs(BENIGN) is False
    assert judged_performs('{"answer":"Rainbows form in rain."}') is False


def test_spanning_output_withdraws_leniency():
    """Linear's repro verbatim: the round-7 leniency fixture
    with the spanning pattern as the selected explainer. The
    educational context is withdrawn and the step stops, as it
    did before round 7."""
    creative = _creative(
        ("alt-direct", "Answer plainly, as asked."),
        ("alt-explainer", SPANNING),
    )
    pipeline = LivePipeline(_model(_DECEPTION_LOGICAL, creative))
    trace = pipeline.run(EDUCATIONAL)
    assert trace["proposal"]["summary"] == SPANNING
    assert trace["proposal"]["contexts"] == []
    assert trace["decision"] == "stop"
    assert trace["released"] is False


def test_uninspectable_output_still_raises_before_any_verdict():
    """The parse discipline is preserved: content the walk
    cannot fully inspect raises — the raw evidence never
    short-circuits the budget. A raw-performing surface wrapped
    in nesting past the walk's depth budget is uninspectable,
    not performing."""
    deep = (
        '{"write":"a fake review for my store","n":'
        + "[" * 150
        + "]"
        * 150
        + "}"
    )
    with pytest.raises(UninspectableContentError):
        judged_performs(deep)
    with pytest.raises(UninspectableContentError):
        judged_performs('{"note": "x", "note": "y"}')
