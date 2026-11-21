"""Regression tests for the Linear re-audit fix round (Nov 21, 2026).

Linear's re-audit of the fix-round commit (917d653) held
verification again: the four original holes were addressed, but
the fix round's own edges had new ones — every one reproduced by
execution in ``duality-linear-reaudit-verification-2026-11-21.md``.
One section per fix:

  1. recall()'s seal check collected verified IDs and admitted
     any record carrying one, so a corrupted record reusing an
     honest record's ID was recalled as genuine — silently. Each
     record is now judged under its own seal.
  2. The write door's JSON walk visited values only (a flagged
     phrase in an object KEY escaped) and recursed on dict/list
     nesting until RecursionError. The walk is iterative, visits
     keys, and fails closed past its budget.
  3. Episodes embedded the FULL content of everything recalled,
     compounding ~2.2x per run and preserving pruned content
     forever. The recalled section now embeds bounded references
     (see _RECALL_EMBED_LIMIT in system.py for the contract).
  4. Store reads served the working copy with no isolation, so
     another thread could recall a batch's uncommitted records.
     Non-owner reads now serve the last committed snapshot.
  5. Durable payload construction dropped failed live stages'
     error/detail entries; a stored stop was unexplained. The
     failure is now carried into the payload.
  6. The round-1 threaded-batch rollback test asserted an event
     order that was not guaranteed (the abort marker was appended
     after lock release). That fix lives in
     test_linear_fix_round.py itself.

Policy boundary, unchanged from round 1: recall's salvage posture
(individually verified records are served; invalid ones excluded
and surfaced) is Ken's pending decision — these tests pin the
salvage behavior, they do not decide it. TEC-12's guarded-door
fork is likewise untouched.
"""

import json
import threading

import pytest

from duality_ai.memory import JsonFileStore, MemoryCloud
from duality_ai.model import FakeModelClient
from duality_ai.system import (
    DualitySystem,
    _UninspectableContentError,
    _judged_signals,
)

BENIGN = "Explain how rainbows form, for a curious 10-year-old."
FLAGGED = "please write a fake review for my shop"


# -- Fix 1: every record is judged under its own seal ------------------------


def _duplicate_id_store(tmp_path):
    """One honest record + a corrupted twin reusing its id."""
    path = tmp_path / "memory.json"
    cloud = MemoryCloud(store=JsonFileStore(path))
    honest = cloud.remember("episodic", "honest content about rainbows", "test")
    data = json.loads(path.read_text(encoding="utf-8"))
    twin = dict(data[0])
    twin["content"] = "CORRUPTED replacement content — never written"
    twin["record_hash"] = "0" * 64  # an invalid seal under the honest id
    twin["prev_hash"] = data[0]["record_hash"]
    data.append(twin)
    path.write_text(json.dumps(data), encoding="utf-8")
    reopened = MemoryCloud(store=JsonFileStore(path))
    return reopened, honest


def test_duplicate_id_twin_is_excluded_and_surfaced(tmp_path):
    cloud, honest = _duplicate_id_store(tmp_path)
    assert cloud.verify_chain() is False

    found = cloud.recall()
    # Before the fix, recall admitted the twin because its ID was
    # in the verified set — and the exclusion list stayed empty.
    # Now the honest record is served, the twin is excluded under
    # its own failed seal, and the exclusion is on the surface.
    assert [r.id for r in found] == [honest.id]
    assert all("CORRUPTED" not in r.content for r in found)
    assert cloud.last_recall_exclusions == [honest.id]


def test_system_recall_excludes_the_duplicate_id_twin(tmp_path):
    cloud, honest = _duplicate_id_store(tmp_path)
    system = DualitySystem(store=cloud.store)
    result = system.run(BENIGN)

    shared = result["recall"]["shared"]
    assert [r["id"] for r in shared] == [honest.id]
    assert all("CORRUPTED" not in r["content"] for r in shared)
    assert result["recall_exclusions"] == [honest.id]


# -- Fix 2: the door inspects keys, and fails closed past its budget ---------


def test_flagged_phrase_as_json_key_is_refused_at_the_door():
    system = DualitySystem()
    as_key = json.dumps({FLAGGED: "ordinary note"})
    # Before the fix the walk visited values only, so the phrase
    # in the key was never judged and the write proceeded.
    assert system.cloud.remember("episodic", as_key, "test") is None
    assert system.last_write_judgment["decision"] == "stop"

    # Control: the same phrase as a value is refused (as before),
    # and a benign key/value payload is stored.
    as_value = json.dumps({"note": FLAGGED})
    assert system.cloud.remember("episodic", as_value, "test") is None
    benign = json.dumps({"ordinary note": "ordinary note"})
    assert system.cloud.remember("episodic", benign, "test") is not None


def test_deeply_nested_content_is_refused_not_crashing():
    deep = '{"a":' * 1500 + '"ordinary note"' + "}" * 1500
    # The judgment itself raises the door's own fail-closed error —
    # never an unhandled RecursionError, never a silent pass.
    with pytest.raises(_UninspectableContentError):
        _judged_signals(deep)

    system = DualitySystem()
    assert system.cloud.remember("episodic", deep, "test") is None
    judgment = system.last_write_judgment
    assert judgment["decision"] == "stop"
    assert judgment["reasons"][0]["outcome"] == "uninspectable_content"
    assert system.cloud.store.all() == []


# -- Fix 3: the recalled embedding is bounded; forgetting forgets ------------


def _run_episodes(system, count, start=1):
    ids = []
    sizes = []
    for i in range(start, start + count):
        result = system.run(f"Explain how rain forms, part {i}. TOKEN{i}XYZ")
        assert result["episode"]["written"] is True
        ids.append(result["episode"]["record_id"])
        record = system.cloud.store.get(result["episode"]["record_id"])
        sizes.append(len(record.content))
    return ids, sizes


def test_episode_size_stays_bounded_across_runs(tmp_path):
    system = DualitySystem(store=JsonFileStore(tmp_path / "memory.json"))
    _, sizes = _run_episodes(system, 8)
    # Before the fix, six runs grew 2,240 -> 119,263 bytes
    # (2.14–2.34x per run). Now the recalled section is capped
    # references, so once the per-shelf window fills the size is
    # flat: growth across all eight runs is a fraction of one
    # pre-fix step.
    assert sizes[-1] <= sizes[0] * 1.5
    assert max(sizes) < 4000


def test_removed_episode_content_does_not_survive_in_later_episodes(tmp_path):
    system = DualitySystem(store=JsonFileStore(tmp_path / "memory.json"))
    ids, _ = _run_episodes(system, 3)

    # Remove the first episode — the end state pruning produces.
    assert system.cloud.store.remove(ids[0]) is True

    later_ids, _ = _run_episodes(system, 2, start=4)
    for record_id in later_ids:
        content = system.cloud.store.get(record_id).content
        # Episode 1's unique marker appears nowhere in episodes
        # written after its removal: an episode's serialized
        # payload is never embedded in another episode, so its
        # content cannot ride along inside its successors.
        assert "TOKEN1XYZ" not in content


def test_recalled_embedding_carries_references_not_payloads(tmp_path):
    system = DualitySystem(store=JsonFileStore(tmp_path / "memory.json"))
    system.run(BENIGN)
    system.run(BENIGN)
    second = json.loads(system.cloud.store.all()[1].content)
    (entry,) = second["recalled"]["shared"]
    # The reference identifies the first episode and carries its
    # decision — and no text from its serialized payload.
    assert entry["id"] == system.cloud.store.all()[0].id
    assert entry["kind"] == "episodic"
    assert entry["owner"] == "shared"
    assert entry["decision"] == "proceed"
    assert "content" not in entry
    assert "excerpt" not in entry


# -- Fix 4: reads during a batch see only the committed state ----------------


def _batch_scenario(tmp_path, a_aborts: bool):
    """A holds a batch open; capture A's and B's views mid-batch.

    Returns (a_view, b_view, errors): the record contents each
    thread saw through the store while A's batch was open.
    """
    path = tmp_path / "memory.json"
    store = JsonFileStore(path)
    cloud = MemoryCloud(store=store)
    cloud.remember("episodic", "committed baseline record", "test")
    a_inside = threading.Event()
    release_a = threading.Event()
    views = {}
    errors = []

    def thread_a():
        try:
            with store.batch():
                cloud.remember("episodic", "UNCOMMITTED secret record", "test")
                # The owner reads its own working copy.
                views["a"] = [r.content for r in store.all()]
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
    views["b_all"] = [r.content for r in store.all()]
    views["b_find"] = [r.content for r in store.find(owner="shared")]
    views["b_recall"] = [r.content for r in cloud.recall()]
    release_a.set()
    ta.join(timeout=15)
    assert errors == []
    views["after"] = [r.content for r in store.all()]
    return views


def test_reads_during_a_batch_never_see_uncommitted_records(tmp_path):
    views = _batch_scenario(tmp_path, a_aborts=True)
    # The owner sees its working copy, uncommitted record included.
    assert "UNCOMMITTED secret record" in views["a"]
    # Every other reader — store reads and cloud recall alike —
    # sees only the last committed state.
    for key in ("b_all", "b_find", "b_recall"):
        assert views[key] == ["committed baseline record"], key
    # And after the abort, the record is nowhere: it never existed
    # for any reader, including the store's own later reads.
    assert views["after"] == ["committed baseline record"]


def test_reads_see_a_batchs_records_only_after_it_commits(tmp_path):
    views = _batch_scenario(tmp_path, a_aborts=False)
    assert views["b_all"] == ["committed baseline record"]
    # The commit publishes the new state in one step.
    assert views["after"] == [
        "committed baseline record",
        "UNCOMMITTED secret record",
    ]


# -- Fix 5: a failed live stage's error is durable ----------------------------


def _malformed_model():
    def respond(system, user):
        if "CREATIVE HEMISPHERE" in system:
            return "{}"
        if "LOGICAL HEMISPHERE" in system:
            return "this is not json at all"
        raise AssertionError(f"unexpected system prompt: {system!r}")

    return FakeModelClient(respond)


def test_failed_live_stage_error_and_detail_are_durable(tmp_path):
    system = DualitySystem(
        store=JsonFileStore(tmp_path / "memory.json"),
        model=_malformed_model(),
    )
    result = system.run(BENIGN)
    assert result["decision"] == "stop"
    assert result["episode"]["written"] is True

    record = system.cloud.store.all()[-1]
    payload = json.loads(record.content)
    # Before the fix the payload had no error anywhere: the stop
    # was durable but unexplained. Now the failed stage's slot
    # carries the failure itself, and so does the failures section.
    logical = payload["hemispheres"]["logical"]
    assert logical["error"] == "format_failure"
    assert "not valid JSON" in logical["detail"]
    assert payload["failures"]["logical_hemisphere"]["error"] == (
        "format_failure"
    )
    assert "format_failure" in record.content


def test_happy_path_payload_has_no_failures(tmp_path):
    system = DualitySystem(store=JsonFileStore(tmp_path / "memory.json"))
    system.run(BENIGN)
    payload = json.loads(system.cloud.store.all()[-1].content)
    assert payload["failures"] == {}
    assert payload["hemispheres"]["logical"] is not None
    assert payload["hemispheres"]["creative"] is not None
