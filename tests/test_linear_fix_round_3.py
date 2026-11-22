"""Regression tests for the Linear third-look fix round (Nov 21, 2026).

Linear's third look at the fix-round-2 commit (e36b6d2) held
verification again: the round-2 fixes hold on the paths they
target, but three gaps remain — every one reproduced by execution
in ``duality-linear-third-look-verification-2026-11-21.md``. One
section per fix:

  1. recall()'s seal filter collected (id, record_hash) pairs and
     admitted any record presenting a verified pair, so a
     corrupted twin copying an honest record's id AND stored hash
     was recalled as genuine — silently. Admission now judges the
     physical record itself, in place.
  2. The committed snapshot copied the record LIST but shared the
     record objects, so in-place edits leaked to other readers
     mid-batch; and appends were visible before their save
     landed. The snapshot now holds independent copies, and reads
     publish on save success only.
  3. The write door's JSON inspection had a decoding floor:
     top-level strings were scanned raw (escapes undecoded),
     string decoding stopped after four levels WITHOUT refusal,
     and parser recursion errors were swallowed into "plain
     text". Decoding is now complete-or-refused: anything not
     fully inspected fails closed.
  4. The recall embedding bound was not unconditional: a recalled
     episode's gate ``decision`` rode through whole, so an
     imported record with a huge decision value produced a huge
     episode. Every embedded string is now capped.

Policy boundary, unchanged from rounds 1–2: recall's salvage
posture (individually verified records are served; invalid ones
excluded and surfaced) is Ken's pending decision — these tests
pin the salvage behavior, they do not decide it. TEC-12's
guarded-door fork is likewise untouched.
"""

import json
import os
import threading

import pytest

from duality_ai.memory import JsonFileStore, MemoryCloud
from duality_ai.system import (
    DualitySystem,
    _RECALL_EXCERPT_CHARS,
    _UninspectableContentError,
    _judged_signals,
)

BENIGN = "Explain how rainbows form, for a curious 10-year-old."
RAW_PHRASE = "please write a fake\nreview for my shop"


# -- Fix 1: admission judges the physical record, not a copied pair ---------


def _copied_pair_twin_store(tmp_path):
    """One honest record + a twin copying its id AND stored hash.

    The exact case round 2's test missed: it changed the twin's
    hash, so the (id, hash) pair it presented was never verified.
    This twin keeps the honest record's id and its stored
    record_hash verbatim and alters only the content — its own
    hash does not recompute over what it now says.
    """
    path = tmp_path / "memory.json"
    cloud = MemoryCloud(store=JsonFileStore(path))
    honest = cloud.remember("episodic", "honest record about rain", "test")
    data = json.loads(path.read_text(encoding="utf-8"))
    twin = dict(data[0])
    twin["content"] = "CORRUPTED twin content — never happened"
    twin["prev_hash"] = data[0]["record_hash"]
    assert twin["id"] == data[0]["id"]
    assert twin["record_hash"] == data[0]["record_hash"]
    data.append(twin)
    path.write_text(json.dumps(data), encoding="utf-8")
    reopened = MemoryCloud(store=JsonFileStore(path))
    return reopened, honest


def test_copied_id_and_hash_twin_is_excluded_and_surfaced(tmp_path):
    cloud, honest = _copied_pair_twin_store(tmp_path)
    assert cloud.verify_chain() is False
    # The twin presents a verified (id, hash) pair — earned by the
    # honest record. Its OWN seal does not recompute.
    twin = cloud.store.all()[1]
    assert twin.record_hash != twin.compute_hash()

    found = cloud.recall()
    # Before the fix, set membership admitted the twin and the
    # exclusion list stayed empty — the bypass was silent. Now
    # the twin is judged in place and fails on its own contents;
    # the honest record is served and the exclusion is surfaced.
    assert [r.content for r in found] == ["honest record about rain"]
    assert cloud.last_recall_exclusions == [honest.id]


def test_system_recall_excludes_the_copied_pair_twin(tmp_path):
    cloud, honest = _copied_pair_twin_store(tmp_path)
    system = DualitySystem(store=cloud.store)
    result = system.run(BENIGN)

    shared = result["recall"]["shared"]
    assert [r["id"] for r in shared] == [honest.id]
    assert all("CORRUPTED" not in r["content"] for r in shared)
    assert result["recall_exclusions"] == [honest.id]


# -- Fix 2: the committed snapshot is deep, and publishes on save -----------


def _inplace_batch_scenario(tmp_path, a_aborts: bool):
    """A holds a batch open and edits a committed record in place.

    Returns the views each thread took: A's own tags for the seed
    record mid-batch, B's views (all/find/recall) mid-batch, and
    the store's views after the batch ends.
    """
    path = tmp_path / "memory.json"
    store = JsonFileStore(path)
    cloud = MemoryCloud(store=store)
    seed = cloud.remember(
        "episodic", "seed record", "test", tags=["seed"]
    )
    a_inside = threading.Event()
    release_a = threading.Event()
    views = {}
    errors = []

    def thread_a():
        try:
            with store.batch():
                # The owner reads its working copy and edits the
                # record in place — the way consolidation marks
                # episodes with a tag.
                record = next(
                    r for r in store.all() if r.id == seed.id
                )
                record.tags.append("UNCOMMITTED-TAG")
                views["a_tags"] = list(record.tags)
                a_inside.set()
                release_a.wait(timeout=15)
                if a_aborts:
                    raise RuntimeError("A aborts")
        except RuntimeError:
            pass
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    ta = threading.Thread(target=thread_a)
    ta.start()
    assert a_inside.wait(timeout=10), "A never entered its batch"
    # Thread B (this thread) reads while A's batch is still open.
    views["b_all_tags"] = [
        list(r.tags) for r in store.all() if r.id == seed.id
    ][0]
    views["b_find"] = store.find(tag="UNCOMMITTED-TAG")
    views["b_recall"] = [r.content for r in cloud.recall()]
    release_a.set()
    ta.join(timeout=15)
    assert errors == []
    views["after_all_tags"] = [
        list(r.tags) for r in store.all() if r.id == seed.id
    ][0]
    views["after_find"] = store.find(tag="UNCOMMITTED-TAG")
    return views


def test_inplace_batch_edit_is_invisible_until_commit(tmp_path):
    views = _inplace_batch_scenario(tmp_path, a_aborts=False)
    # The owner sees its own uncommitted edit.
    assert "UNCOMMITTED-TAG" in views["a_tags"]
    # Every other reader sees the committed record, untouched:
    # the snapshot holds independent copies, so the in-place edit
    # cannot show through — and cannot break the record's seal in
    # B's view either (before the fix, recall served NOTHING for
    # the seed mid-batch: the shared object's hash no longer
    # recomputed, so the committed record vanished until abort).
    assert views["b_all_tags"] == ["seed"]
    assert views["b_find"] == []
    assert views["b_recall"] == ["seed record"]
    # The commit publishes the edit in one step.
    assert views["after_all_tags"] == ["seed", "UNCOMMITTED-TAG"]
    assert len(views["after_find"]) == 1


def test_inplace_batch_edit_never_visible_after_abort(tmp_path):
    views = _inplace_batch_scenario(tmp_path, a_aborts=True)
    assert views["b_all_tags"] == ["seed"]
    assert views["b_find"] == []
    assert views["b_recall"] == ["seed record"]
    # The abort publishes nothing: the edit never existed for any
    # reader, including the store's own later reads.
    assert views["after_all_tags"] == ["seed"]
    assert views["after_find"] == []


def test_append_is_invisible_until_its_save_lands(tmp_path, monkeypatch):
    path = tmp_path / "memory.json"
    store = JsonFileStore(path)
    cloud = MemoryCloud(store=store)
    cloud.remember("episodic", "committed seed", "test")

    real_replace = os.replace
    entered = threading.Event()
    release = threading.Event()
    blocked = {"done": False}

    def blocking_replace(src, dst):
        if path.name in str(src) and not blocked["done"]:
            blocked["done"] = True
            entered.set()
            release.wait(timeout=15)
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", blocking_replace)
    errors = []

    def thread_a():
        try:
            cloud.remember("episodic", "mid-save record", "test")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    ta = threading.Thread(target=thread_a)
    ta.start()
    try:
        assert entered.wait(timeout=10), "put() never reached os.replace"
        # The rename has not landed and the disk does not hold the
        # record — so no other reader may see it either, through
        # the store or through recall. Before the fix, reads
        # served the working copy and B saw the record here; had
        # the save then failed, B would have read a record that
        # never existed.
        assert [r.content for r in store.all()] == ["committed seed"]
        assert [r.content for r in cloud.recall()] == ["committed seed"]
        assert "mid-save record" not in path.read_text(encoding="utf-8")
    finally:
        release.set()
        ta.join(timeout=15)
    assert errors == []
    # Once the save lands, the record is published.
    assert [r.content for r in store.all()] == [
        "committed seed",
        "mid-save record",
    ]


# -- Fix 3: decoding is complete, or the door refuses ------------------------


def test_top_level_encoded_strings_are_decoded_and_refused():
    single = json.dumps(RAW_PHRASE)  # a JSON string literal
    double = json.dumps(single)  # encoded twice
    # Before the fix, a value that parsed as a plain string was
    # scanned in its raw serialized form — escapes undecoded —
    # and the flagged phrase inside passed with zero signals.
    assert _judged_signals(single) == ["deception"]
    assert _judged_signals(double) == ["deception"]

    system = DualitySystem()
    assert system.cloud.remember("episodic", double, "test") is None
    assert system.last_write_judgment["decision"] == "stop"
    assert system.cloud.store.all() == []


def _encoded_phrase(wraps: int) -> str:
    """The flagged phrase under wraps+2 layers of string encoding."""
    s = json.dumps({"note": RAW_PHRASE})
    for _ in range(wraps):
        s = json.dumps({"note": s})
    return json.dumps({"note": s})


@pytest.mark.parametrize("wraps", [3, 4, 6])  # ≈5, 6, 8 decodings
def test_phrase_behind_five_plus_encodings_is_detected(wraps):
    # Before the fix the decoding stopped after four levels —
    # silently: five or more encodings put the phrase beneath a
    # floor the door never looked under. There is no floor now.
    assert _judged_signals(_encoded_phrase(wraps)) == ["deception"]


def test_encoding_past_the_budget_is_refused_not_passed():
    # The phrase sits under ~95 levels of plain object nesting —
    # cheap depth, linear size — with a few string encodings of
    # its own (an encoding chain long enough to exhaust the
    # budget by itself would double in size per layer and could
    # not be built at all). The walk spends the depth budget on
    # the way in and runs out while the phrase is still encoded:
    # uninspectable, and uninspectable fails closed — never a
    # silent pass on the still-encoded remainder.
    content = _encoded_phrase(3)
    for _ in range(95):
        content = '{"a":' + content + "}"
    with pytest.raises(_UninspectableContentError):
        _judged_signals(content)

    system = DualitySystem()
    assert system.cloud.remember("episodic", content, "test") is None
    judgment = system.last_write_judgment
    assert judgment["decision"] == "stop"
    assert judgment["reasons"][0]["outcome"] == "uninspectable_content"
    assert system.cloud.store.all() == []


def test_parser_recursion_in_a_nested_string_fails_closed():
    # At this nesting depth the JSON parser itself raises
    # RecursionError (verified on this interpreter). Before the
    # fix the walker swallowed it and judged the string as plain
    # text — the escape-hidden phrase inside was never seen and
    # the write proceeded.
    deep_inner = (
        "[" * 50_000
        + json.dumps("please write a fake\nreview")
        + "]" * 50_000
    )
    content = json.dumps({"note": deep_inner})
    with pytest.raises(_UninspectableContentError):
        _judged_signals(content)

    system = DualitySystem()
    assert system.cloud.remember("episodic", content, "test") is None
    judgment = system.last_write_judgment
    assert judgment["decision"] == "stop"
    assert judgment["reasons"][0]["outcome"] == "uninspectable_content"
    assert system.cloud.store.all() == []


# -- Fix 4: every embedded string is capped ----------------------------------


def test_giant_imported_decision_cannot_blow_the_embedding_bound(tmp_path):
    system = DualitySystem(store=JsonFileStore(tmp_path / "memory.json"))
    big_decision = "D" * 200_000
    imported = system.cloud.remember(
        "episodic",
        json.dumps({"prompt": "imported prompt", "decision": big_decision}),
        "import",
    )
    assert imported is not None

    result = system.run(BENIGN)
    assert result["episode"]["written"] is True
    record = system.cloud.store.get(result["episode"]["record_id"])
    # Before the fix this episode measured 202,337 bytes: the
    # imported decision rode through the embedding whole. Now
    # the decision is capped like every other embedded string,
    # and the episode stays in the ordinary size range.
    assert len(record.content) < 10_000
    payload = json.loads(record.content)
    (entry,) = [
        e for e in payload["recalled"]["shared"] if "decision" in e
    ]
    assert entry["decision"] == "D" * _RECALL_EXCERPT_CHARS
