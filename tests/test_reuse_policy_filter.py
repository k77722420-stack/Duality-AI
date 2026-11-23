"""The reuse policy at the recall surface (Ken's decision, Nov 22, 2026).

Perplexity's pruning probe established that a quotation embedded
in a surviving record outlives its pruned source and re-enters
assembled recall. Ken's decision — stricter than her
recommendation — is that the filter applies at BOTH surfaces:
model-input construction (a future gate, when seam 1 is wired)
and structured recall assembly itself. A quotation is served
only while its source record still exists and verifies. The
stored archive is never rewritten by the filter.

These tests pin the recall-assembly surface:
  - post-prune, the dead quotation is dropped from served recall
    and the drop is surfaced; the stored record keeps it;
  - pre-prune (source present), the quotation is served — the
    filter does not over-block;
  - a decision-only embed from a dead source is dropped too.
"""

import json
from datetime import datetime, timedelta, timezone

from duality_ai.memory import InMemoryStore, MemoryCloud
from duality_ai.system import (
    DualitySystem,
    _expected_quotation_evidence,
    _filter_dead_quotations,
)

MARKER = "ZORBLAX-LEDGER-731"
A_CONTENT = (
    "Field note: comet observation ledger entry "
    + MARKER
    + " — a harmless archival note about observation schedules."
)
T0 = datetime.now(timezone.utc)


def _fixture():
    """A (backdated source) -> episode B recalling it."""
    store = InMemoryStore()
    system = DualitySystem(store=store)
    a = system.cloud.remember(
        kind="episodic",
        content=A_CONTENT,
        source="field-note",
        stage="intake",
        owner="shared",
        tags=["field-note"],
        created_at=T0 - timedelta(days=100),
    )
    assert a is not None
    result_b = system.run("What notes are on the shared shelf today?")
    assert result_b["episode"]["written"] is True
    return store, a.id, result_b["episode"]["record_id"]


def test_dead_quotation_dropped_from_served_recall_archive_untouched():
    store, a_id, b_id = _fixture()
    # Exact stored content, captured before any filtered run
    # (eleventh-look test ask: compare exactly, not loosely).
    before = next(r for r in store.all() if r.id == b_id).content
    MemoryCloud(store=store).decay_and_prune(now=T0 + timedelta(days=40))
    system = DualitySystem(store=store)
    result = system.run("Give me a plain status summary.")
    # B was selected, its quotation dropped, the drop surfaced.
    recall_ids = [
        entry["id"]
        for entries in result["recall"].values()
        for entry in entries
    ]
    assert b_id in recall_ids
    assert MARKER not in json.dumps(result["recall"])
    assert a_id in result["recall_quotation_drops"]
    # The archive is not a surface: B as STORED is byte-identical.
    after = next(r for r in store.all() if r.id == b_id).content
    assert after == before
    assert MARKER in after


def test_live_quotation_is_served():
    store, a_id, b_id = _fixture()
    system = DualitySystem(store=store)
    result = system.run("Give me a plain status summary.")
    assert result["recall_quotation_drops"] == []
    # B's quotation specifically — not the marker just anywhere
    # (eleventh-look test ask): B's served summary carries an
    # entry referencing A whose excerpt holds the marker.
    served_b = next(
        entry
        for entries in result["recall"].values()
        for entry in entries
        if entry["id"] == b_id
    )
    payload = json.loads(served_b["content"])
    quoted = [
        e
        for e in payload["recalled"]["shared"]
        if isinstance(e, dict) and e.get("id") == a_id
    ]
    assert len(quoted) == 1
    assert MARKER in quoted[0].get("excerpt", "")


def test_dead_decision_embed_is_dropped():
    store = InMemoryStore()
    system = DualitySystem(store=store)
    source = system.cloud.remember(
        kind="episodic",
        content="A short-lived source note.",
        source="field-note",
        stage="intake",
        owner="shared",
        tags=["field-note"],
        created_at=T0 - timedelta(days=100),
    )
    assert source is not None
    payload = {
        "prompt": "container",
        "decision": "proceed",
        "recalled": {
            "logical": [],
            "creative": [],
            "shared": [
                # The genuine embedding of the source, exactly as
                # the system's own projection computes it (the
                # provenance-binding fix, Nov 22, 2026, requires
                # embedded entries to be genuine; the source is a
                # plain note, so its embedding carries an excerpt,
                # not a decision).
                _expected_quotation_evidence(source, {source.id})
            ],
        },
    }
    container = system.cloud.remember(
        kind="episodic",
        content=json.dumps(payload),
        source="test-fixture",
        stage="intake",
        owner="shared",
        tags=["container"],
    )
    assert container is not None
    MemoryCloud(store=store).decay_and_prune(now=T0 + timedelta(days=40))
    result = system.run("Give me a plain status summary.")
    served = next(
        entry
        for entries in result["recall"].values()
        for entry in entries
        if entry["id"] == container.id
    )
    served_payload = json.loads(served["content"])
    assert served_payload["recalled"]["shared"] == []
    assert source.id in result["recall_quotation_drops"]
    # Stored container is untouched.
    stored = next(r for r in store.all() if r.id == container.id)
    assert source.id in stored.content


def test_malformed_reference_ids_are_dropped_not_raised():
    """Eleventh look, finding 1: a list- or dict-valued id must be
    omitted and reported — never a TypeError."""
    for bad_id in ([], {}):
        content = json.dumps(
            {"recalled": {"shared": [{"id": bad_id, "excerpt": MARKER}]}}
        )
        served, drops = _filter_dead_quotations(content, set())
        assert MARKER not in served
        assert len(drops) == 1


def test_malformed_shelf_is_emptied_not_served():
    """Eleventh look, finding 2: a non-list shelf must not pass
    its contents through unfiltered."""
    content = json.dumps(
        {"recalled": {"shared": {"id": "missing", "excerpt": MARKER}}}
    )
    served, drops = _filter_dead_quotations(content, set())
    assert MARKER not in served
    assert drops == ["missing"]
    assert json.loads(served)["recalled"]["shared"] == []


def test_corrupt_source_quotation_is_dropped():
    """A source whose stored content was altered outside the
    system's operations fails its integrity check; it is excluded
    from recall, and quotations of it are dropped with it."""
    store, a_id, b_id = _fixture()
    for record in store.all():
        if record.id == a_id:
            record.content = record.content + " (altered)"
    system = DualitySystem(store=store)
    recall = system._recall_precedent()
    assert a_id in system.last_recall_exclusions
    assert a_id in system.last_recall_quotation_drops
    assert MARKER not in json.dumps(recall)
