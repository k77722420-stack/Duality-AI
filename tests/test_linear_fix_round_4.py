"""Regression tests for the Linear fourth-look fix round (Nov 21, 2026).

Linear's fourth look at the fix-round-3 commit (b11dc26) held
verification again — the round-3 fixes confirmed on their paths,
two gaps and one rider remaining, all reproduced by execution in
``duality-linear-fourth-look-verification-2026-11-21.md``. One
section per fix:

  1. recall() joined TWO store reads by object identity —
     find() for candidates, all() inside the verification pass —
     so a save landing between the reads, or any backend handing
     out fresh copies per query, made every honest record fail
     as a provenance failure while the chain verified. Recall
     now judges and selects from ONE snapshot.
  2. The door's JSON parsing discarded all but the last value
     of a duplicated key before inspection, so flagged text in
     a discarded position passed and was stored verbatim. The
     inspection parse now REJECTS duplicate keys — at any
     level, nested decodings included — as uninspectable, and
     the door fails closed: duplicate keys are never produced
     by the system's own serialization, so rejection costs
     nothing legitimate.
  3. The embedding bound covered strings only: a non-string
     field of an imported record (a ~200 KB list in ``source``)
     passed through whole into the next episode. Every value
     the embedding selects is now capped — strings truncated,
     non-strings embedded as capped serializations — and the
     contract states the guarantee at its true width.

Policy boundary, unchanged from rounds 1–3: recall's salvage
posture (individually verified records are served; invalid ones
excluded and surfaced) is Ken's pending decision — these tests
pin the salvage behavior, they do not decide it. TEC-12's
guarded-door fork is likewise untouched: fix 2 changes what the
door can see (and what it refuses as uninspectable), never what
it decides about content it can inspect.
"""

import copy
import json

import pytest

from duality_ai.memory import (
    GENESIS_HASH,
    InMemoryStore,
    JsonFileStore,
    MemoryCloud,
    MemoryRecord,
)
from duality_ai.system import (
    DualitySystem,
    _RECALL_EXCERPT_CHARS,
    _UninspectableContentError,
    _judged_signals,
    _recalled_evidence,
)

FLAGGED = "write a fake review for my shop"  # -> ['deception']
CLEAN = "ordinary note"  # -> []


# -- Fix 1: recall judges and selects from ONE snapshot ----------------------


def _seed(cloud, n=3):
    return [
        cloud.remember(
            "episodic", f"honest memory number {i}", "test"
        ).id
        for i in range(n)
    ]


def test_recall_survives_a_save_landing_between_its_reads(tmp_path):
    """The verify4 race staging: the committed snapshot is
    re-published (fresh record objects, identical ids, hashes,
    and content) after the candidates are read but before the
    verification pass reads — exactly what a concurrent save
    does. Before the fix, recall returned 0 of 3 and excluded
    every honest record as a provenance failure while
    verify_chain() said True."""
    store = JsonFileStore(tmp_path / "memory.json")
    cloud = MemoryCloud(store=store)
    ids = _seed(cloud)

    orig_all = store.all
    state = {"swapped": False}

    def swapping_all():
        if not state["swapped"]:
            state["swapped"] = True
            store._publish_committed()
        return orig_all()

    store.all = swapping_all
    try:
        found = cloud.recall()
    finally:
        store.all = orig_all

    # One snapshot: the re-published objects are judged and
    # selected within the same read — all honest records are
    # served, and nothing is excluded.
    assert sorted(r.id for r in found) == sorted(ids)
    assert cloud.last_recall_exclusions == []
    assert cloud.verify_chain() is True


class _FreshCopyStore(InMemoryStore):
    """A backend whose every query returns deep copies — a
    legitimate reading of the store contract."""

    def all(self):
        return copy.deepcopy(super().all())

    def find(self, kind=None, owner=None, tag=None):
        return copy.deepcopy(
            super().find(kind=kind, owner=owner, tag=tag)
        )

    def get(self, record_id):
        record = super().get(record_id)
        return copy.deepcopy(record) if record is not None else None


def test_recall_works_with_a_fresh_copies_backend():
    """No race, no concurrency: before the fix, the identity
    join across two reads failed structurally and recall
    returned 0 of 3, permanently, while the chain verified.
    From one snapshot, the copies are judged in place and
    served."""
    cloud = MemoryCloud(store=_FreshCopyStore())
    ids = _seed(cloud)
    assert cloud.verify_chain() is True

    found = cloud.recall()
    assert sorted(r.id for r in found) == sorted(ids)
    assert cloud.last_recall_exclusions == []


# -- Fix 2: duplicate keys are uninspectable at the door ---------------------


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


def test_duplicate_key_flagged_first_is_refused():
    # Before the fix: signals [], decision proceed, written,
    # flagged text stored verbatim — the parse discarded the
    # flagged value before inspection ever ran.
    system = DualitySystem(store=InMemoryStore())
    content = '{"note": "' + FLAGGED + '", "note": "' + CLEAN + '"}'
    _assert_refused_uninspectable(system, content)


def test_duplicate_key_flagged_second_is_refused():
    # The control case: standard parsing kept the flagged value,
    # so this was refused by detection before. Under the
    # rejection approach it is refused as uninspectable — a
    # duplicate is ambiguous as written, whichever position the
    # flagged value sits in.
    system = DualitySystem(store=InMemoryStore())
    content = '{"note": "' + CLEAN + '", "note": "' + FLAGGED + '"}'
    _assert_refused_uninspectable(system, content)


def test_duplicate_key_in_a_nested_object_is_refused():
    system = DualitySystem(store=InMemoryStore())
    content = (
        '{"outer": {"note": "' + FLAGGED + '", "note": "'
        + CLEAN + '"}}'
    )
    _assert_refused_uninspectable(system, content)


def test_duplicate_key_inside_an_encoded_string_is_refused():
    # The d2 staging: the flagged phrase is escape-split inside
    # a duplicate key in a JSON string the walk must decode —
    # before the fix the decode's last-wins parse discarded it
    # and the write proceeded.
    system = DualitySystem(store=InMemoryStore())
    inner_text = (
        '{"note": "write a fake\\nreview for my shop", '
        '"note": "ordinary note"}'
    )
    content = json.dumps(inner_text)
    _assert_refused_uninspectable(system, content)


def test_duplicate_keys_benign_are_refused_as_uninspectable():
    # The rejection approach, pinned: even with no flagged value
    # anywhere, a repeated key is ambiguous as written — which
    # value the record carries is a parser convention — so the
    # door refuses it as uninspectable rather than choosing.
    system = DualitySystem(store=InMemoryStore())
    content = '{"note": "ordinary note", "note": "another note"}'
    _assert_refused_uninspectable(system, content)


def test_content_without_duplicates_behaves_as_before():
    system = DualitySystem(store=InMemoryStore())
    # Benign, duplicate-free JSON: judged on its values, written.
    record, judgment = _write(system, '{"note": "ordinary note"}')
    assert record is not None
    assert judgment["decision"] == "proceed"
    # A flagged value under a single key: detected, and refused
    # by the gate's judgment — not by the uninspectable path.
    assert _judged_signals('{"note": "' + FLAGGED + '"}') == [
        "deception"
    ]
    record, judgment = _write(
        system, '{"note": "' + FLAGGED + '"}'
    )
    assert record is None
    assert judgment["decision"] == "stop"
    assert judgment["reasons"][0]["outcome"] != "uninspectable_content"


# -- Fix 3: every embedded value is capped, non-strings included -------------


def test_giant_nonstring_source_cannot_blow_the_embedding_bound(
    tmp_path,
):
    """The verify4 staging: an imported record (written straight
    into the store file) whose ``source`` is a ~200 KB list.
    Before the fix the episode embedding passed it through
    whole — a 203,102-byte episode against a 2,317-byte
    control. Now the embedded source is its capped
    serialization."""
    path = tmp_path / "memory.json"
    imported = MemoryRecord(
        id="imported0000000000000000000001",
        kind="episodic",
        owner="shared",
        content="a perfectly ordinary imported memory",
        source=["x" * 1000] * 200,  # ~200 KB serialized
        stage="import",
        tags=[],
        created_at="2026-11-21T00:00:00+00:00",
        strength=1.0,
        prev_hash=GENESIS_HASH,
    )
    imported.record_hash = imported.compute_hash()
    path.write_text(
        json.dumps([imported.to_dict()], ensure_ascii=False),
        encoding="utf-8",
    )
    store = JsonFileStore(path)
    system = DualitySystem(store=store)
    assert system.cloud.verify_chain() is True

    result = system.run("Explain how rainbows form.")
    episode = result["episode"]
    assert episode["written"] is True
    record = store.get(episode["record_id"])
    payload = json.loads(record.content)
    assert len(record.content.encode("utf-8")) < 10_000
    entries = payload["recalled"]["shared"]
    (entry,) = [e for e in entries if e["id"] == imported.id]
    assert isinstance(entry["source"], str)
    assert len(entry["source"]) == _RECALL_EXCERPT_CHARS


def test_nonstring_decision_and_content_embed_as_capped_serializations():
    # A recalled episode whose gate decision is a non-string
    # (an imported payload can carry one): embedded as its JSON
    # serialization, capped — the round-3 behavior, now via the
    # one cap every selected value passes through.
    entry = {
        "id": "episode-1",
        "kind": "episodic",
        "owner": "shared",
        "source": "test",
        "content": json.dumps(
            {"prompt": "p", "decision": ["x" * 5000]}
        ),
    }
    evidence = _recalled_evidence(entry)
    assert isinstance(evidence["decision"], str)
    assert len(evidence["decision"]) == _RECALL_EXCERPT_CHARS

    # A plain record whose content is itself a non-string:
    # the excerpt is its capped serialization, not a slice of
    # the object.
    entry = {
        "id": "plain-1",
        "kind": "episodic",
        "owner": "shared",
        "source": "test",
        "content": ["y" * 5000],
    }
    evidence = _recalled_evidence(entry)
    assert isinstance(evidence["excerpt"], str)
    assert len(evidence["excerpt"]) == _RECALL_EXCERPT_CHARS
