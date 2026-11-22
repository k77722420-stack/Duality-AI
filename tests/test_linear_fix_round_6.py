"""Fix round 6 — Linear's sixth look (Nov 22, 2026).

Three findings, all verified by execution before fixing (Lux
verification, Nov 22, 2026 — every value matched Linear's
source-derived outcomes):

  1. HIGH — the live gate judged the request, never the release.
     Detection ran on the request only, so a benign request could
     release flagged content the model introduced in its selected
     answer: decision "proceed", released True, the memory door's
     refusal afterward unable to retract the release. Leniency
     likewise checked the request, not the selected answer.
     Fix (live.py): the hub inspects the SELECTED framing's text
     before the proposal reaches the gate — its detected signals
     join the union the gate sees, and a selected answer that
     itself performs withdraws every granted context.

  2. MEDIUM — recall() still aliased mutable imported fields.
     Round 5 deep-copied committed snapshots, but recall built its
     results with dataclasses.replace, copying only ``tags``: a
     recalled record's list-valued ``source`` stayed shared with
     the stored record, and a caller's append rewrote stored
     memory, broke its seal, and hid it from later recalls.
     Fix (memory.py): recall returns deep copies — the
     ``_copy_record`` rule applied at the cloud's boundary, for
     every field, on both backends.

  3. MEDIUM — duplicate keys in live replies discarded evidence.
     The live parser used plain ``json.loads``: a logical reply
     repeating "signals" kept only the last value, losing an
     already-reported deception signal (proceed instead of stop).
     Fix: one shared strict loader (strictjson.py) now serves
     both judged surfaces — the door's duplicate rejection (round
     4) and the live reply parser — while each surface keeps its
     own policy for parse failures (door: uninspectable, refuse;
     live: format failure, fail closed).

Nothing else changed. TEC-12 and the broken-chain recall policy
were explicitly NOT part of this round: both remain Ken's
decisions, and Linear's HOLD did not turn on either.
"""

import json

import pytest

from duality_ai.live import LivePipeline
from duality_ai.markers import detect_signals, performs
from duality_ai.memory import (
    GENESIS_HASH,
    InMemoryStore,
    JsonFileStore,
    MemoryCloud,
    MemoryRecord,
)
from duality_ai.model import FakeModelClient
from duality_ai.strictjson import DuplicateKeyError, loads_strict
from duality_ai.system import (
    DualitySystem,
    _UninspectableContentError,
    _judged_signals,
)

BENIGN = "Explain how rainbows form."
FLAGGED_TEXT = "Write a fake review for my store."
EDUCATIONAL = (
    "For a fraud-awareness class, describe how fake-review scams "
    "work so students can recognize them."
)

_EMPTY_LOGICAL = json.dumps(
    {"checks": [], "flags": [], "signals": [], "pros": [], "cons": []}
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


# ---------------------------------------------------------------------
# Fix 1 — the gate judges the release, not just the request
# ---------------------------------------------------------------------


def test_selected_output_signals_reach_the_gate():
    """Linear's staging, at the pipeline: a benign request whose
    selected answer the detector flags. Before the fix the gate
    saw no signal and released it; the selected text's signals
    now join the union, and the gate stops the step."""
    assert detect_signals(FLAGGED_TEXT) == ["deception"]
    pipeline = LivePipeline(
        _model(_EMPTY_LOGICAL, _creative(("alt-direct", FLAGGED_TEXT)))
    )
    trace = pipeline.run(BENIGN)
    assert trace["proposal"]["summary"] == FLAGGED_TEXT
    assert trace["proposal"]["signals"] == ["deception"]
    assert trace["decision"] == "stop"
    assert trace["released"] is False


def test_selected_output_stops_the_system_run():
    """Linear's repro verbatim, through the assembled system: the
    step is stopped, nothing is released, and the barrier now
    sizes a real threat. The episode is still refused at the
    guarded door — the door's standing posture (TEC-12), unchanged
    by this fix."""
    system = DualitySystem(
        model=_model(
            _EMPTY_LOGICAL, _creative(("alt-direct", FLAGGED_TEXT))
        )
    )
    result = system.run(BENIGN)
    assert result["decision"] == "stop"
    assert result["released"] is False
    assert result["pipeline"]["proposal"]["signals"] == ["deception"]
    assert result["barrier"]["threat_units"] == 1
    assert result["episode"]["written"] is False
    assert result["episode"]["write_judgment"]["decision"] == "stop"


def test_performing_selected_output_withdraws_leniency():
    """The leniency variant Linear named: inspecting output
    signals alone would not close it — the output must satisfy
    the content condition too. The request earns an educational
    context and the model's stance explains, but the framing the
    hub selects itself performs, so no context reaches the gate
    and the step stops."""
    assert performs(FLAGGED_TEXT) is True
    creative = _creative(
        ("alt-direct", "Answer plainly, as asked."),
        ("alt-explainer", FLAGGED_TEXT),
    )
    pipeline = LivePipeline(_model(_DECEPTION_LOGICAL, creative))
    trace = pipeline.run(EDUCATIONAL)
    assert trace["proposal"]["summary"] == FLAGGED_TEXT
    assert trace["proposal"]["contexts"] == []
    assert trace["decision"] == "stop"
    assert trace["released"] is False


def test_explaining_selected_output_keeps_leniency():
    """Control: the same flagged, labeled request with a selected
    answer that explains rather than performs keeps its context
    and its leniency — output inspection changes nothing for a
    clean release."""
    creative = _creative(
        ("alt-direct", "Answer plainly, as asked."),
        ("alt-explainer", "Answer with background."),
    )
    pipeline = LivePipeline(_model(_DECEPTION_LOGICAL, creative))
    trace = pipeline.run(EDUCATIONAL)
    assert trace["proposal"]["contexts"] == ["educational"]
    assert trace["decision"] == "proceed_with_leniency"
    assert trace["released"] is True


# ---------------------------------------------------------------------
# Fix 2 — recall hands out deep copies, on both backends
# ---------------------------------------------------------------------


def _imported_record(source):
    record = MemoryRecord(
        id="imported00000000000000000000a1",
        kind="episodic",
        owner="shared",
        content="an imported memory",
        source=source,
        stage="import",
        tags=["seed-tag"],
        created_at="2026-11-21T00:00:00+00:00",
        strength=1.0,
        prev_hash=GENESIS_HASH,
    )
    record.record_hash = record.compute_hash()
    return record


def _cloud_with_import(backend, tmp_path, record):
    if backend == "json":
        path = tmp_path / "memory.json"
        path.write_text(
            json.dumps([record.to_dict()], ensure_ascii=False),
            encoding="utf-8",
        )
        store = JsonFileStore(path)
    else:
        store = InMemoryStore()
        store.put(record)
    cloud = MemoryCloud(store)
    assert cloud.verify_chain() is True
    return cloud


@pytest.mark.parametrize("backend", ["memory", "json"])
def test_recalled_list_source_shares_nothing_with_the_store(
    backend, tmp_path
):
    """Linear's repro: mutating a recalled record's list-valued
    source must not reach the stored record, break its seal, or
    hide it from later recalls."""
    cloud = _cloud_with_import(
        backend, tmp_path, _imported_record(["origin"])
    )
    recalled = cloud.recall()[0]
    recalled.source.append("caller-only")
    assert cloud.store.get(recalled.id).source == ["origin"]
    assert cloud.verify_chain() is True
    assert [r.id for r in cloud.recall()] == [recalled.id]


@pytest.mark.parametrize("backend", ["memory", "json"])
def test_recalled_dict_source_shares_nothing_with_the_store(
    backend, tmp_path
):
    cloud = _cloud_with_import(
        backend, tmp_path, _imported_record({"origin": "seed"})
    )
    recalled = cloud.recall()[0]
    recalled.source["injected"] = "caller-only"
    assert cloud.store.get(recalled.id).source == {"origin": "seed"}
    assert cloud.verify_chain() is True
    assert [r.id for r in cloud.recall()] == [recalled.id]


@pytest.mark.parametrize("backend", ["memory", "json"])
def test_recalled_nested_field_shares_nothing_with_the_store(
    backend, tmp_path
):
    """The deep in deep copy: a mutable value nested inside a
    field is as independent as the field itself. Tags ride along
    as the control — the one field the old construction copied."""
    cloud = _cloud_with_import(
        backend,
        tmp_path,
        _imported_record({"meta": {"flags": ["a"]}}),
    )
    recalled = cloud.recall()[0]
    recalled.source["meta"]["flags"].append("caller-only")
    recalled.tags.append("caller-only")
    stored = cloud.store.get(recalled.id)
    assert stored.source == {"meta": {"flags": ["a"]}}
    assert stored.tags == ["seed-tag"]
    assert cloud.verify_chain() is True
    assert [r.id for r in cloud.recall()] == [recalled.id]


# ---------------------------------------------------------------------
# Fix 3 — one strict loader for both judged surfaces
# ---------------------------------------------------------------------


def test_duplicate_signals_key_in_logical_reply_fails_closed():
    """Linear's repro: the first "signals" reports deception, the
    second discards it. Before the fix the step proceeded; the
    reply is now a format failure — stopped, never released —
    with the repeated key named in the trace."""
    dup = (
        '{"checks":[],"flags":[],"signals":["deception"],'
        '"signals":[],"pros":[],"cons":[]}'
    )
    pipeline = LivePipeline(
        _model(dup, _creative(("alt-direct", "Answer plainly.")))
    )
    trace = pipeline.run(BENIGN)
    assert trace["decision"] == "stop"
    assert trace["released"] is False
    failures = [
        entry
        for entry in trace["stages"]
        if entry.get("error") == "format_failure"
    ]
    assert len(failures) == 1
    assert failures[0]["stage"] == "logical_hemisphere"
    assert "repeats the key 'signals'" in failures[0]["detail"]


def test_duplicate_key_in_creative_reply_fails_closed():
    dup = (
        '{"alternatives":[{"id":"alt-direct","text":"One."}],'
        '"alternatives":[{"id":"alt-direct","text":"Two."}]}'
    )
    pipeline = LivePipeline(_model(_EMPTY_LOGICAL, dup))
    trace = pipeline.run(BENIGN)
    assert trace["decision"] == "stop"
    assert trace["released"] is False
    failures = [
        entry
        for entry in trace["stages"]
        if entry.get("error") == "format_failure"
    ]
    assert len(failures) == 1
    assert failures[0]["stage"] == "creative_hemisphere"
    assert "repeats the key 'alternatives'" in failures[0]["detail"]


def test_duplicate_key_nested_in_logical_reply_fails_closed():
    """The refusal is at any level, not just the top: a repeated
    key inside one checks entry is the same discarded evidence."""
    dup = (
        '{"checks":[{"name":"a","name":"b","passed":true}],'
        '"flags":[],"signals":[],"pros":[],"cons":[]}'
    )
    pipeline = LivePipeline(
        _model(dup, _creative(("alt-direct", "Answer plainly.")))
    )
    trace = pipeline.run(BENIGN)
    assert trace["decision"] == "stop"
    assert trace["released"] is False


def test_loads_strict_rejects_duplicates_at_any_level():
    with pytest.raises(DuplicateKeyError) as caught:
        loads_strict('{"signals": [], "signals": ["deception"]}')
    assert caught.value.args[0] == "signals"
    with pytest.raises(DuplicateKeyError):
        loads_strict('{"outer": {"x": 1, "x": 2}}')
    assert loads_strict('{"outer": {"x": 1}}') == {"outer": {"x": 1}}


def test_loads_strict_preserves_parser_error_kinds():
    """The door's policy distinguishes a syntax error (plain text)
    from every other parser failure (uninspectable) — the shared
    loader must not blur that distinction (round 5)."""
    with pytest.raises(json.JSONDecodeError):
        loads_strict("{not json")
    with pytest.raises(ValueError) as caught:
        loads_strict('{"n": ' + "9" * 5000 + "}")
    assert not isinstance(caught.value, json.JSONDecodeError)


def test_door_still_refuses_duplicate_key_content():
    """The door's policy on the shared loader, unchanged: content
    repeating a key is uninspectable and refused, never judged on
    whichever value a standard parse would have kept."""
    with pytest.raises(_UninspectableContentError):
        _judged_signals(
            '{"note": "ordinary", "note": "write a fake review"}'
        )


# ---------------------------------------------------------------------
# Double-check addendum (Nov 22, 2026) — the write path's twin
#
# Ken directed a second pass over the round ("go over it two
# times just to be sure"). The sibling sweep found finding 2's
# class still open in the other direction: remember() returned
# the very object the store holds, and consolidate()'s results
# are remember()'s returns — so a caller mutating either rewrote
# stored memory and broke its seal, verified by execution on
# both. remember() now returns a deep copy, which closes both
# surfaces with the one rule.
# ---------------------------------------------------------------------


@pytest.mark.parametrize("backend", ["memory", "json"])
def test_remembered_return_shares_nothing_with_the_store(
    backend, tmp_path
):
    if backend == "json":
        store = JsonFileStore(tmp_path / "memory.json")
    else:
        store = InMemoryStore()
    cloud = MemoryCloud(store)
    returned = cloud.remember(
        "episodic", "an honest memory", "test", tags=["seed-tag"]
    )
    returned.content = "write a fake review for my shop"
    returned.tags.append("caller-only")
    stored = cloud.store.get(returned.id)
    assert stored.content == "an honest memory"
    assert stored.tags == ["seed-tag"]
    assert cloud.verify_chain() is True
    assert [r.id for r in cloud.recall()] == [returned.id]


@pytest.mark.parametrize("backend", ["memory", "json"])
def test_consolidated_return_shares_nothing_with_the_store(
    backend, tmp_path
):
    if backend == "json":
        store = JsonFileStore(tmp_path / "memory.json")
    else:
        store = InMemoryStore()
    cloud = MemoryCloud(store)
    for i in range(3):
        cloud.remember(
            "episodic",
            f"episode number {i} about cats",
            "test",
            tags=["cats"],
        )
    created = cloud.consolidate()
    assert len(created) == 1
    summary = created[0]
    summary.content = "write a fake review for my shop"
    summary.tags.append("caller-only")
    stored = cloud.store.get(summary.id)
    assert stored.content == "Consolidated 3 episodes about 'cats'."
    assert "caller-only" not in stored.tags
    assert cloud.verify_chain() is True
