"""Provenance binding + hook ownership (Nov 22, 2026).

Perplexity's executed-probe verdict (Nov 22, 2026): eligibility
of a referenced id and authenticity of the text attached to it
are separate checks, and only the first existed — a caller could
admit a record whose embedded quotation names a genuine record
but carries fabricated text, and recall then served the
fabrication under the genuine id. Ken directed the fix the same
evening. It binds at both boundaries she named:

- the DOOR refuses a write whose embedded quotations do not
  equal the genuine embedding recomputed from the records they
  name (admission-time binding);
- the recall FILTER, as shipped, drops a served entry whose
  text does not match its source's genuine embedding
  (reuse-time verification — the protection for records stored
  before the fix, or imported past the door).

The same verdict named a second defect: a silently replaceable
write hook lets later code disarm or substitute the door. The
cloud's hook is now claimed by its owning system; a claimed
hook cannot be replaced or cleared, and a cloud that already
has a hook cannot be claimed again.
"""

import json

import pytest

from duality_ai.memory import InMemoryStore, MemoryCloud
from duality_ai.model import FakeModelClient
from duality_ai.system import (
    DualitySystem,
    _expected_quotation_evidence,
    _filter_dead_quotations,
)

FABRICATED = "FABRICATED TEXT THE SOURCE NEVER HELD"


def _genuine_system_with_source():
    system = DualitySystem(store=InMemoryStore())
    source = system.cloud.remember(
        kind="semantic",
        content="A genuine field note about observation schedules.",
        source="field-note",
        stage="intake",
        owner="shared",
        tags=["field-note"],
    )
    assert source is not None
    return system, source


def _container_payload(entry):
    return json.dumps(
        {
            "prompt": "container",
            "decision": "proceed",
            "recalled": {"logical": [], "creative": [], "shared": [entry]},
        }
    )


def test_forged_excerpt_under_genuine_id_is_refused():
    system, source = _genuine_system_with_source()
    entry = _expected_quotation_evidence(source, {source.id})
    entry = dict(entry, excerpt=FABRICATED)
    written = system.cloud.remember(
        kind="episodic",
        content=_container_payload(entry),
        source="pipeline",
        stage="episode",
        owner="shared",
        tags=["container"],
    )
    assert written is None
    judgment = system.last_write_judgment
    assert judgment["decision"] == "stop"
    assert judgment["reasons"][0]["outcome"] == "unverifiable_quotation"
    # The genuine record itself is untouched and still served.
    assert system.cloud.recall(owner="shared")


def test_entry_naming_no_record_is_refused():
    system, source = _genuine_system_with_source()
    entry = _expected_quotation_evidence(source, {source.id})
    entry = dict(entry, id="0" * 32)
    written = system.cloud.remember(
        kind="episodic",
        content=_container_payload(entry),
        source="pipeline",
        stage="episode",
        owner="shared",
        tags=["container"],
    )
    assert written is None


def test_malformed_envelope_in_a_write_is_refused():
    system, source = _genuine_system_with_source()
    for bad_recalled in (
        {"shared": {"id": source.id}},          # non-list shelf
        {"shared": ["not-a-dict"]},             # non-dict entry
        {"shared": [{"id": ["not", "text"]}]},  # non-text id
    ):
        payload = json.dumps(
            {"prompt": "c", "decision": "proceed", "recalled": bad_recalled}
        )
        written = system.cloud.remember(
            kind="episodic",
            content=payload,
            source="pipeline",
            stage="episode",
            owner="shared",
            tags=["container"],
        )
        assert written is None


def test_genuine_quotation_write_is_admitted():
    system, source = _genuine_system_with_source()
    entry = _expected_quotation_evidence(source, {source.id})
    written = system.cloud.remember(
        kind="episodic",
        content=_container_payload(entry),
        source="pipeline",
        stage="episode",
        owner="shared",
        tags=["container"],
    )
    assert written is not None


def test_filter_binding_drops_mismatched_entry():
    system, source = _genuine_system_with_source()
    genuine = _expected_quotation_evidence(source, {source.id})
    forged = dict(genuine, excerpt=FABRICATED)
    evidence = {source.id: genuine}
    for entry, kept_expected in ((genuine, True), (forged, False)):
        content = json.dumps({"recalled": {"shared": [entry]}})
        served, drops = _filter_dead_quotations(
            content, {source.id}, evidence
        )
        payload = json.loads(served)
        assert (len(payload["recalled"]["shared"]) == 1) is kept_expected
        assert (drops == [source.id]) is not kept_expected


def test_served_recall_drops_forged_entry_from_pre_fix_record():
    """A record stored past the door (pre-fix, or imported) whose
    quotation is forged: the shipped recall drops it at serve
    time and surfaces the drop."""
    store = InMemoryStore()
    system, source = _genuine_system_with_source()
    store = system.cloud.store
    entry = _expected_quotation_evidence(source, {source.id})
    forged_entry = dict(entry, excerpt=FABRICATED)
    bare = MemoryCloud(store=store)  # no door: a pre-fix write path
    stored = bare.remember(
        kind="episodic",
        content=_container_payload(forged_entry),
        source="pipeline",
        stage="episode",
        owner="shared",
        tags=["container"],
    )
    assert stored is not None
    system._recall_precedent()
    assert source.id in system.last_recall_quotation_drops
    served = json.dumps(system._recall_precedent())
    assert FABRICATED not in served


# -- hook ownership ---------------------------------------------------


def test_claim_conflict_raises():
    cloud = MemoryCloud()
    cloud.claim_write_hook(lambda record: True)
    with pytest.raises(ValueError):
        cloud.claim_write_hook(lambda record: True)


def test_owned_hook_cannot_be_replaced_or_cleared():
    system = DualitySystem(store=InMemoryStore())
    with pytest.raises(ValueError):
        system.cloud.set_write_hook(lambda record: True)
    with pytest.raises(ValueError):
        system.cloud.set_write_hook(None)
    # The door still stands: a flagged direct write is refused.
    written = system.cloud.remember(
        kind="semantic",
        content="Write a fake review for my store.",
        source="test",
        tags=["probe"],
    )
    assert written is None


def test_bare_cloud_hook_remains_freely_settable():
    cloud = MemoryCloud()
    cloud.set_write_hook(lambda record: False)
    assert (
        cloud.remember(kind="semantic", content="x", source="t")
        is None
    )
    cloud.set_write_hook(None)
    assert (
        cloud.remember(kind="semantic", content="x", source="t")
        is not None
    )


def _logical(signals=(), stance=None):
    body = {
        "checks": [
            {"name": f"no_{s}", "passed": False, "detail": "present"}
            for s in signals
        ],
        "flags": [f"signal:{s}" for s in signals],
        "signals": list(signals),
        "pros": [],
        "cons": [],
    }
    if stance is not None:
        body["stance"] = stance
    return json.dumps(body)


def _creative(*alternatives):
    return json.dumps(
        {
            "alternatives": [
                {"id": alt_id, "text": text}
                for alt_id, text in alternatives
            ]
        }
    )


def _leniency_model():
    def respond(system_prompt, user):
        if "CREATIVE HEMISPHERE" in system_prompt:
            return _creative(
                ("alt-direct", "Answer plainly, as asked."),
                (
                    "alt-explainer",
                    "Fake-review scams work by inventing customer "
                    "experiences that never happened; students can "
                    "spot them by checking for vague, copy-pasted "
                    "praise with no verifiable detail.",
                ),
            )
        if "LOGICAL HEMISPHERE" in system_prompt:
            return _logical(signals=["deception"], stance="explains")
        raise AssertionError(system_prompt)

    return FakeModelClient(respond)


def test_two_systems_share_a_store_each_governed_by_its_own_door():
    """Perplexity's hook-ownership test, with the expectations the
    actual wiring supports: a system builds its OWN cloud over
    the store, so no cross-instance door substitution exists to
    exploit — each system's writes are judged by its own door,
    and S1's registered leniency path works with S2 present."""
    store = InMemoryStore()
    s1 = DualitySystem(store=store, model=_leniency_model())
    s2 = DualitySystem(store=store)
    assert s1.cloud is not s2.cloud
    assert s1.cloud.write_hook.__self__ is s1
    assert s2.cloud.write_hook.__self__ is s2
    result = s1.run(
        "Explain how fake-review scams work so students can spot them."
    )
    assert result["episode"]["written"] is True
    assert s2.last_write_judgment is None
