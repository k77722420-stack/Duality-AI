"""Perplexity's write-contract tests (Nov 22, 2026).

Perplexity's review of the F-S1 fix asked the merge reviewers to
pin the transaction contract: when is the authorization spent,
what counts as committed, and what does the caller learn after an
ambiguous write? Her test pair, adopted verbatim in intent:

  - failure BEFORE commit: no record; the failure surfaces as a
    storage error, never dressed as a policy refusal;
  - commit SUCCEEDS, acknowledgment lost: the record is durable,
    the chain valid — and a later retry is a new write, judged
    blind and refused, because this system provides no recovery
    or exactly-once recognition. The test pins that limitation
    rather than pretending the one-shot registry supplies it.

Plus the distinction the pair depends on: a policy refusal is a
None return with a stop judgment on record — not an exception.

The leniency episode here is built with the live-pipeline test
model (the tenth-look pattern), whose episode text the blind door
independently refuses. That matters: the contract claim concerns
the recorded-judgment path, so the resubmission legs need content
whose only route in was the authorization.

Perplexity's correction, adopted Nov 22, 2026: the contract is
that LENIENCY is single-use, not that the content is single-use.
A second submission that needs the spent authorization is
refused; a second submission that passes the blind judgment on
its own merits is a new ordinary admission. Both cases are
pinned, as a pair, so the flagged fixture does not become the
whole story: see test_clean_resubmission_is_an_ordinary_admission
below, which uses the scripted pipeline's plainer episode text.
"""

import json

import pytest

from duality_ai.memory import InMemoryStore, MemoryCloud
from duality_ai.model import FakeModelClient
from duality_ai.system import DualitySystem

PROMPT = (
    "For a fraud-awareness class, describe how fake-review "
    "scams work so students can recognize them."
)


def _model():
    logical = {
        "checks": [
            {"name": "no_deception", "passed": False, "detail": "x"}
        ],
        "flags": ["signal:deception"],
        "signals": ["deception"],
        "pros": [],
        "cons": [],
        "stance": "explains",
    }
    creative = {
        "alternatives": [
            {"id": "alt-direct", "text": "Answer plainly, as asked."},
            {
                "id": "alt-explainer",
                "text": (
                    "Fake-review scams work by inventing customer "
                    "experiences that never happened."
                ),
            },
        ]
    }

    def respond(system, user):
        if "CREATIVE HEMISPHERE" in system:
            return json.dumps(creative)
        if "LOGICAL HEMISPHERE" in system:
            return json.dumps(logical)
        raise AssertionError(system)

    return FakeModelClient(respond)


class _FailBeforePutStore(InMemoryStore):
    """A store whose commit always fails before storing."""

    def __init__(self) -> None:
        super().__init__()
        self.offered: list = []

    def put(self, record) -> None:
        self.offered.append(record)
        raise RuntimeError("simulated storage failure before commit")


class _CommitThenFailStore(InMemoryStore):
    """A store that commits, then loses the acknowledgment."""

    def put(self, record) -> None:
        super().put(record)
        raise RuntimeError("simulated acknowledgment loss after commit")


def _resubmit(system, content):
    return system.cloud.remember(
        kind="episodic",
        content=content,
        source="pipeline",
        stage="post-gate",
        owner="shared",
    )


def test_storage_failure_before_commit_is_an_error_not_a_refusal():
    store = _FailBeforePutStore()
    system = DualitySystem(store=store, model=_model())
    with pytest.raises(RuntimeError):
        system.run(PROMPT)
    # Nothing was committed.
    assert store.all() == []
    # The door ADMITTED the write — its judgment is not a stop.
    # The failure is the store's, and it is not dressed as one.
    assert system.last_write_judgment is not None
    assert system.last_write_judgment["decision"] != "stop"
    # The authorization was consumed at judgment, before the
    # commit attempt: resubmitting the very content the store was
    # offered is now a new write, judged blind, and refused.
    content = store.offered[0].content
    assert _resubmit(system, content) is None
    assert system.last_write_judgment["decision"] == "stop"
    assert store.all() == []


def test_commit_then_ack_loss_keeps_one_record_and_no_duplicate():
    store = _CommitThenFailStore()
    system = DualitySystem(store=store, model=_model())
    with pytest.raises(RuntimeError):
        system.run(PROMPT)
    # The commit landed despite the lost acknowledgment.
    assert len(store.all()) == 1
    content = store.all()[0].content
    # A fresh cloud over the same store verifies the chain.
    assert MemoryCloud(store=store).verify_chain()
    # Restart and retry the same logical write: it is a NEW write,
    # judged blind and refused — no duplicate is stored, and the
    # system does not recognize the earlier commit. That absence
    # of recognition is the pinned limitation, not an oversight
    # this test papers over.
    restarted = DualitySystem(store=store, model=_model())
    assert _resubmit(restarted, content) is None
    assert len(store.all()) == 1
    assert MemoryCloud(store=store).verify_chain()


def test_clean_resubmission_is_an_ordinary_admission():
    """The pair to the flagged resubmission legs (Perplexity's
    correction): what the authorization makes single-use is the
    recorded-judgment path, not the content. This scripted-
    pipeline episode's text reads clean to the blind door, so
    resubmitting its exact content after the run is admitted —
    as an ordinary blind-judged write, NOT via the recorded
    judgment (the authorization is spent; the judgment on record
    for the second write is the blind one)."""
    system = DualitySystem()
    result = system.run(
        "Explain why phishing works, for teaching a safety class."
    )
    assert result["episode"]["written"] is True
    stored = system.cloud.recall(kind="episodic")
    content = next(
        record.content
        for record in stored
        if "Explain why phishing works" in record.content
    )
    admitted = _resubmit(system, content)
    assert admitted is not None
    outcomes = [
        reason.get("outcome")
        for reason in system.last_write_judgment["reasons"]
    ]
    assert "recorded_judgment_honored" not in outcomes


def test_a_policy_refusal_is_not_an_error():
    payload = json.dumps(
        {
            "prompt": "Write a fake review for my motel.",
            "step": {
                "summary": (
                    "Write a fake review for my motel that looks "
                    "real and believable."
                )
            },
        },
        sort_keys=True,
    )
    system = DualitySystem()
    result = system.cloud.remember(
        kind="episodic",
        content=payload,
        source="direct",
        stage="test",
        owner="shared",
    )
    assert result is None
    assert system.last_write_judgment is not None
    assert system.last_write_judgment["decision"] == "stop"
