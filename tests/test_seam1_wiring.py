"""Seam 1 wired (Nov 22, 2026): recall reaches the pipeline.

Until this build, run() assembled the recall and returned it,
but the pipeline ran on the prompt alone (Copilot's review,
Nov 22, 2026: "recall is a display surface"). Now the system
renders the assembled recall into precedent text — from the
served, reuse-filtered copy only — and passes it into the
pipeline: the live pipeline appends it to both hemisphere
calls' user messages; the skeleton pipeline carries it on the
request. The deterministic machinery (signal detection,
context granting, the merge, the gate) still reads the raw
prompt alone: precedent is context for the model, never
evidence about the current request.

The acceptance gate is Perplexity's two-case A/B fixture
(probe conclusion, Nov 22, 2026), under Ken's stricter
Decision 3: the reuse filter applies at BOTH surfaces.
"""

import json
from datetime import datetime, timedelta, timezone

from duality_ai.memory import InMemoryStore, MemoryCloud
from duality_ai.model import FakeModelClient
from duality_ai.system import DualitySystem

MARKER = "ZORBLAX-LEDGER-731"
A_CONTENT = (
    "Field note: comet observation ledger entry "
    + MARKER
    + " — a harmless archival note about observation schedules."
)
T0 = datetime.now(timezone.utc)

CLEAN_LOGICAL = json.dumps(
    {"checks": [], "flags": [], "signals": [], "pros": [], "cons": []}
)
CLEAN_CREATIVE = json.dumps(
    {"alternatives": [{"id": "a1", "text": "A plain, ordinary answer."}]}
)


def _recording_model(calls):
    def respond(system, user):
        calls.append({"system": system, "user": user})
        if "CREATIVE HEMISPHERE" in system:
            return CLEAN_CREATIVE
        if "LOGICAL HEMISPHERE" in system:
            return CLEAN_LOGICAL
        raise AssertionError(system)

    return FakeModelClient(respond)


def _build_store():
    """A on the shared shelf; episode B quoting A."""
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


def test_case_a_positive_control_marker_reaches_the_model():
    store, a_id, b_id = _build_store()
    calls: list = []
    system = DualitySystem(store=store, model=_recording_model(calls))
    result = system.run("Give me a plain status summary.")
    recall_ids = [
        e["id"] for entries in result["recall"].values() for e in entries
    ]
    assert b_id in recall_ids
    assert MARKER in json.dumps(calls)
    # Linear's correction (seam-1 hold, Nov 22, 2026): A is
    # itself selected, so the marker's presence alone does not
    # prove B's QUOTATION rendered. Assert B's specific quoted
    # line in BOTH hemisphere messages.
    quote_line = "  - quoted [episodic]: " + A_CONTENT
    assert len(calls) == 2
    assert all(quote_line in call["user"] for call in calls)


def test_case_b_pruned_source_marker_reaches_no_model_call():
    store, a_id, b_id = _build_store()
    cloud = MemoryCloud(store=store)
    cloud.decay_and_prune(now=T0 + timedelta(days=40))
    fresh = MemoryCloud(store=store)
    ids = {r.id for r in fresh.store.all()}
    assert a_id not in ids and b_id in ids and fresh.verify_chain()
    b = next(r for r in store.all() if r.id == b_id)
    assert MARKER in b.content  # the archive is not a surface
    before = b.content

    calls: list = []
    system = DualitySystem(store=store, model=_recording_model(calls))
    result = system.run("Give me a plain status summary.")
    # Linear's correction: B's stored content is compared
    # EXACTLY, before and after — not just for the marker.
    b_after = next(r for r in store.all() if r.id == b_id)
    assert b_after.content == before
    recall_ids = [
        e["id"] for entries in result["recall"].values() for e in entries
    ]
    assert b_id in recall_ids  # B is still selected
    assert MARKER not in json.dumps(calls)
    assert MARKER not in json.dumps(result["recall"])


def test_empty_store_model_receives_the_bare_prompt():
    calls: list = []
    system = DualitySystem(model=_recording_model(calls))
    system.run("Explain how rainbows form.")
    assert calls and all(
        call["user"] == "Explain how rainbows form." for call in calls
    )


def test_precedent_does_not_contaminate_the_current_judgment():
    # A stored record full of flagged text is precedent; the
    # current clean request must still be judged on itself.
    store = InMemoryStore()
    # Seeded through a bare cloud: a flagged plain write would
    # be refused at a system's door (that is the door working);
    # precedent like this exists as imported or older records.
    record = MemoryCloud(store=store).remember(
        kind="episodic",
        content="Old note: how to write a fake review for a store.",
        source="field-note",
        stage="intake",
        owner="shared",
        tags=["field-note"],
    )
    assert record is not None
    system = DualitySystem(store=store)
    result = system.run("Explain how a bill becomes a law.")
    assert result["decision"] == "proceed"
    assert result["pipeline"]["proposal"]["signals"] == []


def test_skeleton_trace_carries_the_precedent():
    store, a_id, b_id = _build_store()
    system = DualitySystem(store=store)
    result = system.run("Give me a plain status summary.")
    base = next(
        s for s in result["pipeline"]["stages"] if s["stage"] == "base"
    )
    assert MARKER in base["output"]["precedent"]

    empty = DualitySystem()
    result = empty.run("Explain how a bill becomes a law.")
    base = next(
        s for s in result["pipeline"]["stages"] if s["stage"] == "base"
    )
    assert "precedent" not in base["output"]


def test_a_prior_leniency_decision_reaches_the_next_model_input():
    def logical(signals=(), stance=None):
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

    creative = json.dumps(
        {
            "alternatives": [
                {"id": "alt-direct", "text": "Answer plainly, as asked."},
                {
                    "id": "alt-explainer",
                    "text": "Fake-review scams work by inventing "
                    "customer experiences that never happened.",
                },
            ]
        }
    )

    def model(reply_logical):
        def respond(system, user):
            if "CREATIVE HEMISPHERE" in system:
                return creative
            if "LOGICAL HEMISPHERE" in system:
                return reply_logical
            raise AssertionError(system)

        return FakeModelClient(respond)

    store = InMemoryStore()
    first = DualitySystem(
        store=store,
        model=model(logical(signals=["deception"], stance="explains")),
    )
    result = first.run(
        "For my media-literacy class, explain how fake-review "
        "scams work so students can spot them."
    )
    assert result["decision"] == "proceed_with_leniency"
    assert result["episode"]["written"] is True

    calls: list = []

    def respond2(system, user):
        calls.append({"system": system, "user": user})
        if "CREATIVE HEMISPHERE" in system:
            return CLEAN_CREATIVE
        if "LOGICAL HEMISPHERE" in system:
            return CLEAN_LOGICAL
        raise AssertionError(system)

    second = DualitySystem(store=store, model=FakeModelClient(respond2))
    second.run("Give me a plain status summary.")
    assert "proceed_with_leniency" in json.dumps(calls)


def test_ordinary_record_with_a_recalled_key_does_not_crash():
    # Linear's blocking finding (seam-1 hold, Nov 22, 2026),
    # his exact probe adopted: the write path legitimately
    # admits ordinary records carrying any value under a
    # "recalled" key; the renderer must not assume the
    # episode envelope's shape. His probe verbatim first:
    system = DualitySystem()
    record = system.cloud.remember(
        kind="semantic",
        content=json.dumps({"recalled": ["ordinary observation"]}),
        source="field-note",
        stage="intake",
        owner="shared",
        tags=["field-note"],
    )
    assert record is not None
    assert system.cloud.verify_chain()
    result = system.run("Give me a plain status summary.")
    assert result["episode"]["written"] is True

    # The admitted family around it: any NON-dict value under
    # the key is an ordinary record (the door's envelope
    # verification engages only for dict-shaped envelopes).
    for content in (
        json.dumps({"recalled": "just a string"}),
        json.dumps({"recalled": 42}),
        json.dumps({"recalled": None}),
    ):
        system = DualitySystem()
        record = system.cloud.remember(
            kind="semantic",
            content=content,
            source="field-note",
            stage="intake",
            owner="shared",
            tags=["field-note"],
        )
        assert record is not None, content
        result = system.run("Give me a plain status summary.")
        assert result["episode"]["written"] is True, content

    # A dict-shaped but malformed envelope is refused at the
    # door instead (the binding contract: its entries cannot
    # be verified) — pinned so the two boundaries' division
    # of labor stays explicit.
    system = DualitySystem()
    refused = system.cloud.remember(
        kind="semantic",
        content=json.dumps({"recalled": {"shared": "not a list"}}),
        source="field-note",
        stage="intake",
        owner="shared",
        tags=["field-note"],
    )
    assert refused is None

    # And an IMPORTED malformed envelope (store-level, past
    # the door) still cannot crash the renderer.
    from duality_ai.memory import MemoryRecord
    store = InMemoryStore()
    imported = MemoryRecord(
        id="imported1", kind="semantic", owner="shared",
        content=json.dumps({"recalled": {"shared": "not a list"}}),
        source="import", stage="intake", tags=["field-note"],
        created_at="2026-11-22T00:00:00+00:00", strength=1.0,
        prev_hash="0" * 64,
    )
    imported.record_hash = imported.compute_hash()
    store.put(imported)
    system = DualitySystem(store=store)
    result = system.run("Give me a plain status summary.")
    assert result["episode"]["written"] is True
