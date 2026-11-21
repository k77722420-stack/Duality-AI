"""Regression tests for the Linear fifth-look fix round (Nov 21, 2026).

Linear's fifth look at the fix-round-4 commit (65e3fff) held the
merge — the round-4 fixes confirmed correct by inspection, two
gaps remaining, both reproduced by execution in
``duality-linear-fifth-look-verification-2026-11-21.md``. One
section per fix:

  1. The door's parse fallback caught broad ``ValueError`` and
     treated every parse failure as plain text. But
     ``json.JSONDecodeError`` is only one kind of ValueError:
     CPython's integer-length limit (4300 digits) raises a plain
     ValueError that is NOT a decode error, so a 5,000-digit
     integer anywhere in the payload aborted the inspection
     parse and the content fell back to a raw-text scan — in
     which escape-hidden flagged content is invisible, and the
     parse died before round 4's duplicate-key rejection could
     run. The fallback now triggers ONLY on JSONDecodeError
     (the text simply is not JSON); every other parser failure
     is uninspectable and the door fails closed. One deliberate
     behavior change rides along: a big integer ALONE, with no
     flagged content anywhere, is now refused as uninspectable
     instead of proceeding — unparseable structured content is
     no longer judged benign plain text.
  2. ``_copy_record`` copied only ``tags``; every other field
     was shared by reference. An imported record with a
     list-valued ``source`` therefore shared one list between
     the working copy and the committed snapshot — an in-place
     edit during another thread's batch leaked into the
     committed view and broke the committed copy's own seal, so
     recall excluded the record for the batch's duration. The
     copy now deep-copies the whole record: no mutable state is
     shared, whatever an imported record's fields carry.

Policy boundary, unchanged from rounds 1–4: recall's salvage
posture is Ken's pending decision — these tests pin the salvage
behavior, they do not decide it. TEC-12's guarded-door fork is
likewise untouched: fix 1 changes which parser failures the door
treats as plain text, never what it decides about content it can
inspect or about genuinely non-JSON text.
"""

import json
import threading

import pytest

from duality_ai.memory import (
    GENESIS_HASH,
    InMemoryStore,
    JsonFileStore,
    MemoryCloud,
    MemoryRecord,
    _copy_record,
)
from duality_ai.system import (
    DualitySystem,
    _UninspectableContentError,
    _judged_signals,
)

BIG = "9" * 5000  # past CPython's int_max_str_digits (4300)
SHORT = "9" * 3
# In the RAW JSON text this is backslash+n (a JSON escape). Decoded
# it is a real newline, which the detector's whitespace
# normalization turns into the flagged phrase "fake review".
ESC_FLAGGED = "write a fake\\nreview for my shop"
FLAGGED = "write a fake review for my shop"  # -> ['deception']
CLEAN = "ordinary note"  # -> []


def _write(system, content):
    record = system.cloud.remember("episodic", content, "test")
    return record, system.last_write_judgment


def _assert_refused_uninspectable(system, content):
    with pytest.raises(_UninspectableContentError):
        _judged_signals(content)
    record, judgment = _write(system, content)
    assert record is None
    assert judgment["decision"] == "stop"
    assert judgment["reasons"][0]["outcome"] == "uninspectable_content"
    assert system.cloud.store.all() == []


# -- Fix 1: only a JSON syntax error falls back to plain text -----------------


def test_bigint_escape_hidden_flagged_toplevel_refused():
    # Before the fix: signals [], decision proceed, written —
    # the stored content was byte-identical to the submission,
    # escape-hidden flagged text included. The int-limit
    # ValueError is not a JSONDecodeError, so the content is
    # uninspectable now, not plain text.
    system = DualitySystem(store=InMemoryStore())
    content = (
        '{"n": ' + BIG + ', "note": "' + ESC_FLAGGED + '"}'
    )
    _assert_refused_uninspectable(system, content)


def test_bigint_escape_hidden_flagged_nested_encoded_refused():
    # The same payload one encoding down: the top-level parse
    # succeeds (the content is a JSON string), and the nested
    # decode is where the int limit fires. Before the fix the
    # nested site's broad ValueError catch treated the string
    # as plain text and never decoded it: proceed, written.
    system = DualitySystem(store=InMemoryStore())
    inner = '{"n": ' + BIG + ', "note": "' + ESC_FLAGGED + '"}'
    _assert_refused_uninspectable(system, json.dumps(inner))


def test_bigint_duplicate_keys_refused_uninspectable():
    # Before the fix the parse died before the object closed,
    # so round 4's duplicate-key rejection never ran and the
    # write proceeded. Now the parse failure itself is
    # uninspectable — refused either way, nothing written.
    system = DualitySystem(store=InMemoryStore())
    content = (
        '{"note": "' + ESC_FLAGGED + '", "note": "' + CLEAN
        + '", "n": ' + BIG + '}'
    )
    _assert_refused_uninspectable(system, content)


def test_bigint_alone_refused_uninspectable():
    # The pinned behavior change: no flagged content anywhere,
    # only an integer the parser cannot convert. Before the
    # fix this proceeded — unparseable structured content
    # judged as benign plain text. A conversion failure is not
    # evidence the content is plain text, so the door refuses
    # it as uninspectable.
    system = DualitySystem(store=InMemoryStore())
    content = '{"n": ' + BIG + ', "note": "' + CLEAN + '"}'
    _assert_refused_uninspectable(system, content)


def test_short_int_control_still_refused_by_detection():
    # The verify5 control, unchanged by the fix: with a short
    # integer the parse succeeds, the escape-hidden phrase is
    # decoded and DETECTED, and the refusal is the gate's
    # judgment — not the uninspectable path.
    system = DualitySystem(store=InMemoryStore())
    content = (
        '{"n": ' + SHORT + ', "note": "' + ESC_FLAGGED + '"}'
    )
    assert _judged_signals(content) == ["deception"]
    record, judgment = _write(system, content)
    assert record is None
    assert judgment["decision"] == "stop"
    assert judgment["reasons"][0]["outcome"] != "uninspectable_content"


def test_plain_text_fallback_preserved():
    # Genuinely non-JSON content raises JSONDecodeError and is
    # judged as the raw text it is, exactly as before: benign
    # text proceeds and is written; flagged text is refused by
    # DETECTION (the gate's judgment), never by the
    # uninspectable path.
    system = DualitySystem(store=InMemoryStore())
    record, judgment = _write(system, "an ordinary note about "
                                      "the weather")
    assert record is not None
    assert judgment["decision"] == "proceed"

    assert _judged_signals(FLAGGED) == ["deception"]
    record, judgment = _write(system, FLAGGED)
    assert record is None
    assert judgment["decision"] == "stop"
    assert judgment["reasons"][0]["outcome"] != "uninspectable_content"


# -- Fix 2: record copies share no mutable state ------------------------------


def test_copy_record_shares_no_mutable_state():
    record = MemoryRecord(
        id="rec000000000000000000000000001",
        kind="episodic",
        owner="shared",
        content="an imported record",
        source=["origin", "seed"],
        stage="import",
        tags=["seed-tag"],
        created_at="2026-11-21T00:00:00+00:00",
        strength=1.0,
        prev_hash=GENESIS_HASH,
    )
    record.record_hash = record.compute_hash()
    clone = _copy_record(record)
    clone.source.append("MUTATED")
    clone.tags.append("mutated-tag")
    assert record.source == ["origin", "seed"]
    assert record.tags == ["seed-tag"]
    # The original's content never changed, so its seal still
    # verifies — the property the committed snapshot relies on.
    assert record.compute_hash() == record.record_hash


def _imported_record(rid, source, prev_hash):
    record = MemoryRecord(
        id=rid,
        kind="episodic",
        owner="shared",
        content="an imported memory",
        source=source,
        stage="import",
        tags=["seed-tag"],
        created_at="2026-11-21T00:00:00+00:00",
        strength=1.0,
        prev_hash=prev_hash,
    )
    record.record_hash = record.compute_hash()
    return record


def test_imported_mutable_fields_do_not_leak_into_committed_view(
    tmp_path,
):
    """The verify5 staging, threaded: a worker holds a batch
    and mutates the working copies IN PLACE — a list-valued
    ``source`` (append), a dict-valued ``source`` (key insert),
    and ``tags`` as the control. Before the fix the committed
    view served the uncommitted list, the committed copy's seal
    failed, and recall returned 0 records with the record
    excluded. Now the committed view is untouched, its seals
    verify, and recall serves both records mid-batch."""
    list_rec = _imported_record(
        "imported00000000000000000000a1",
        ["origin", "seed"],
        GENESIS_HASH,
    )
    dict_rec = _imported_record(
        "imported00000000000000000000a2",
        {"origin": "seed"},
        list_rec.record_hash,
    )
    path = tmp_path / "memory.json"
    path.write_text(
        json.dumps(
            [list_rec.to_dict(), dict_rec.to_dict()],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    store = JsonFileStore(path)
    cloud = MemoryCloud(store)
    assert cloud.verify_chain() is True

    entered = threading.Event()
    release = threading.Event()
    aborted = threading.Event()

    def worker():
        try:
            with store.batch():
                working_list = store.get(list_rec.id)
                working_list.source.append("UNCOMMITTED-LEAK")
                working_list.tags.append("uncommitted-tag")
                working_dict = store.get(dict_rec.id)
                working_dict.source["injected"] = "UNCOMMITTED-LEAK"
                entered.set()
                release.wait(15)
                raise RuntimeError("abort the batch")
        except RuntimeError:
            pass
        aborted.set()

    thread = threading.Thread(target=worker)
    thread.start()
    assert entered.wait(15)

    # While the batch is OPEN, this thread is a non-owner: it
    # reads the committed view.
    view_list = store.get(list_rec.id)
    assert view_list.source == ["origin", "seed"]
    assert view_list.tags == ["seed-tag"]
    assert view_list.compute_hash() == view_list.record_hash
    view_dict = store.get(dict_rec.id)
    assert view_dict.source == {"origin": "seed"}
    assert view_dict.compute_hash() == view_dict.record_hash
    recalled = cloud.recall()
    assert sorted(r.id for r in recalled) == sorted(
        [list_rec.id, dict_rec.id]
    )
    assert cloud.last_recall_exclusions == []

    release.set()
    assert aborted.wait(15)
    thread.join(15)

    # After the abort the committed view is exactly as imported.
    view_list = store.get(list_rec.id)
    assert view_list.source == ["origin", "seed"]
    assert view_list.tags == ["seed-tag"]
    assert view_list.compute_hash() == view_list.record_hash
    view_dict = store.get(dict_rec.id)
    assert view_dict.source == {"origin": "seed"}
    assert view_dict.compute_hash() == view_dict.record_hash
