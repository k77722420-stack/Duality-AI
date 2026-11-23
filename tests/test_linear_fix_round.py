"""Regression tests for the Linear audit fix round (Nov 21, 2026).

Linear's audit of the wiring branch (commit 190edaa) held
verification: two High findings, two Medium, one gap — every one
reproduced by execution in
``duality-linear-audit-verification-2026-11-21.md``. This file is
the test set the audit named as missing, one section per fix:

  1. The memory door judged the JSON-serialized episode, so a
     flagged phrase disguised by an escaped newline slipped
     through (TEC-12, widened). The door now judges the parsed
     text. The door's POLICY is unchanged — whether flagged
     stop-records should be kept is still Ken's TEC-12 decision;
     these tests pin only that a disguise no longer changes the
     verdict.
  2. batch() checked an instance-wide flag before the lock, so a
     second thread entered the "nested" path unlocked (TEC-6).
     Batch ownership is now per-thread.
  3. A failed save left the uncommitted record standing in the
     working copy and abandoned its temp file (TEC-6). Saves now
     roll back and clean up, on the batch path and the plain
     append path alike.
  4. Durable episodes carried only {prompt, decision, released};
     they now carry the full THESIS §3 movement-7 evidence.
  5. recall() served records without verifying their provenance
     seal; tampered records are now excluded, and the exclusion
     is surfaced.
"""

import json
import threading
from unittest import mock

import pytest

from duality_ai.memory import JsonFileStore, MemoryCloud
from duality_ai.system import DualitySystem

BENIGN = "Explain how rainbows form, for a curious 10-year-old."


def _tmp_leftovers(tmp_path):
    return sorted(p.name for p in tmp_path.glob("*.tmp-*"))


# -- Fix 1: the door judges the parsed text, not the serialized form ------


@pytest.mark.parametrize(
    "disguised",
    [
        "Please write a fake\nreview for my restaurant.",
        "Please write a fake\treview for my restaurant.",
        "Please write a fake\rreview for my restaurant.",
    ],
    ids=["newline", "tab", "carriage-return"],
)
def test_disguised_flagged_phrase_is_refused_at_the_door(disguised):
    system = DualitySystem()
    result = system.run(disguised)

    # The pipeline's detector normalizes whitespace, so it stops
    # the step — and after the fix the door reaches the same
    # verdict on the parsed episode text. Before the fix the
    # newline case was judged "proceed" and the stopped step's
    # episode was stored.
    assert result["decision"] == "stop"
    assert result["episode"]["written"] is False
    assert result["episode"]["write_judgment"]["decision"] == "stop"
    # TEC-12 (Nov 22, 2026): the cloud no longer stays literally
    # empty — a stopped step leaves its metadata-only stop
    # record. The episode is still refused, and the flagged
    # phrase itself is still never stored (only its fingerprint).
    records = system.cloud.store.all()
    assert [r.kind for r in records] == ["stop"]
    assert disguised not in records[0].content


def test_planted_serialized_payload_cannot_disguise_a_phrase():
    system = DualitySystem()
    disguised = json.dumps(
        {
            "prompt": "Please write a fake\nreview for my restaurant.",
            "decision": "stop",
            "released": False,
        },
        sort_keys=True,
    )
    assert system.cloud.remember("episodic", disguised, "test") is None
    assert system.last_write_judgment["decision"] == "stop"

    benign_payload = json.dumps(
        {"prompt": BENIGN, "decision": "proceed", "released": True},
        sort_keys=True,
    )
    stored = system.cloud.remember("episodic", benign_payload, "test")
    assert stored is not None


# -- Fix 2: batch ownership is per-thread -----------------------------------


def test_concurrent_writers_on_separate_instances_lose_nothing(tmp_path):
    path = tmp_path / "memory.json"
    clouds = [MemoryCloud(store=JsonFileStore(path)) for _ in range(2)]
    start = threading.Barrier(2)
    errors = []

    def write(cloud, label):
        try:
            start.wait(timeout=10)
            for i in range(10):
                cloud.remember("episodic", f"{label} record {i}", "test")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [
        threading.Thread(target=write, args=(cloud, label))
        for cloud, label in zip(clouds, ("A", "B"))
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert errors == []
    fresh = MemoryCloud(store=JsonFileStore(path))
    contents = {r.content for r in fresh.store.all()}
    assert contents == {
        f"{label} record {i}" for label in ("A", "B") for i in range(10)
    }
    assert fresh.verify_chain() is True


def _threaded_batch_scenario(tmp_path, a_aborts: bool):
    """A holds a batch; B's batch must wait, then run as its own.

    Returns (events, fresh_contents): ``events`` records the order
    in which the threads entered/exited, ``fresh_contents`` is what
    a fresh instance reads from disk at the end.
    """
    path = tmp_path / "memory.json"
    store = JsonFileStore(path)
    cloud = MemoryCloud(store=store)
    events = []
    a_inside = threading.Event()
    release_a = threading.Event()
    b_inside = threading.Event()
    errors = []

    def thread_a():
        try:
            with store.batch():
                events.append("a-in")
                a_inside.set()
                release_a.wait(timeout=15)
                cloud.remember("episodic", "A's record", "test")
                if a_aborts:
                    try:
                        raise RuntimeError("A aborts")
                    except RuntimeError:
                        # Recorded while the batch — and its lock —
                        # is still held, so the append is ordered
                        # before B can possibly enter, which the
                        # exact-sequence assertions below rely on.
                        # Appending in the outer handler instead
                        # would happen AFTER lock release and race
                        # B's entry (Linear re-audit, Nov 21, 2026:
                        # the asserted order was not guaranteed).
                        events.append("a-aborted")
                        raise
                events.append("a-out")
        except RuntimeError:
            pass
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def thread_b():
        try:
            with store.batch():
                events.append("b-in")
                b_inside.set()
                cloud.remember("episodic", "B's record", "test")
                events.append("b-out")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    ta = threading.Thread(target=thread_a)
    ta.start()
    assert a_inside.wait(timeout=10), "A never entered its batch"

    tb = threading.Thread(target=thread_b)
    tb.start()
    # While A holds its batch, B must NOT be inside its own: before
    # the fix B took the "nested" path immediately, unlocked.
    assert not b_inside.wait(timeout=1.5), (
        "B entered its batch while A still held one"
    )

    release_a.set()
    ta.join(timeout=15)
    assert b_inside.wait(timeout=10), "B never entered after A finished"
    tb.join(timeout=15)
    assert errors == []

    fresh = MemoryCloud(store=JsonFileStore(path))
    contents = [r.content for r in fresh.store.all()]
    return events, contents


def test_thread_b_waits_for_thread_as_batch_then_commits_its_own(tmp_path):
    events, contents = _threaded_batch_scenario(tmp_path, a_aborts=False)
    # B entered only after A's batch had fully exited, and each
    # thread's record was committed by its own batch.
    assert events == ["a-in", "a-out", "b-in", "b-out"]
    assert contents == ["A's record", "B's record"]


def test_thread_b_survives_thread_as_rollback(tmp_path):
    events, contents = _threaded_batch_scenario(tmp_path, a_aborts=True)
    # A's rollback discarded A's uncommitted record — and ONLY A's:
    # B's later batch was its own, so B's record still landed.
    assert events == ["a-in", "a-aborted", "b-in", "b-out"]
    assert contents == ["B's record"]


def test_same_thread_nested_batch_still_joins_the_outer_one(tmp_path):
    path = tmp_path / "memory.json"
    store = JsonFileStore(path)
    cloud = MemoryCloud(store=store)
    with store.batch():
        cloud.remember("episodic", "outer", "test")
        with store.batch():  # same thread: joins, no second commit
            cloud.remember("episodic", "inner", "test")
    fresh = MemoryCloud(store=JsonFileStore(path))
    assert [r.content for r in fresh.store.all()] == ["outer", "inner"]
    assert fresh.verify_chain() is True


# -- Fix 3: a failed save rolls back and cleans up ---------------------------


def test_failed_batch_commit_rolls_back_memory_and_cleans_up(tmp_path):
    path = tmp_path / "memory.json"
    store = JsonFileStore(path)
    cloud = MemoryCloud(store=store)
    cloud.remember("episodic", "committed seed", "test")
    before = path.read_bytes()

    with pytest.raises(OSError):
        with mock.patch(
            "os.replace", side_effect=OSError("simulated rename failure")
        ):
            with store.batch():
                cloud.remember("episodic", "uncommitted batch record", "test")

    # Disk untouched (as before), and now the working copy agrees:
    # no phantom record, no abandoned temp file.
    assert path.read_bytes() == before
    assert [r.content for r in store.all()] == ["committed seed"]
    assert _tmp_leftovers(tmp_path) == []


def test_failed_plain_append_rolls_back_memory_and_cleans_up(tmp_path):
    path = tmp_path / "memory.json"
    store = JsonFileStore(path)
    cloud = MemoryCloud(store=store)
    cloud.remember("episodic", "committed seed", "test")
    before = path.read_bytes()

    with pytest.raises(OSError):
        with mock.patch(
            "os.replace", side_effect=OSError("simulated rename failure")
        ):
            cloud.remember("episodic", "uncommitted plain record", "test")

    assert path.read_bytes() == before
    assert [r.content for r in store.all()] == ["committed seed"]
    fresh = MemoryCloud(store=JsonFileStore(path))
    assert [r.content for r in fresh.store.all()] == ["committed seed"]
    assert _tmp_leftovers(tmp_path) == []


# -- Fix 4: durable episodes carry the movement-7 evidence -------------------


def test_stored_episode_carries_the_movement_7_evidence():
    system = DualitySystem()
    result = system.run(BENIGN)
    record = system.cloud.store.all()[0]
    payload = json.loads(record.content)

    # THESIS §3 movement 7: the request as admitted, what was
    # recalled, the hemispheres' contributions in summary, the hub's
    # weighing trace, the gate's decision and its reasons, the
    # released answer — alongside the original three fields.
    assert payload["prompt"] == BENIGN
    assert payload["decision"] == "proceed"
    assert payload["released"] is True
    assert payload["recalled"] == {
        "logical": [],
        "creative": [],
        "shared": [],
    }
    logical = payload["hemispheres"]["logical"]
    creative = payload["hemispheres"]["creative"]
    assert logical["checks"] and "pros" in logical
    assert creative["alternatives"]
    assert payload["hub"]["accepted"] and payload["hub"]["rejected"]
    assert payload["gate"]["decision"] == "proceed"
    assert payload["gate"]["reasons"], "gate reasons must be durable"
    assert payload["answer"] == result["pipeline"]["proposal"]["step"]

    # The next run's episode names what it recalled: the first
    # episode, by id, on the shared shelf.
    system.run(BENIGN)
    second = json.loads(system.cloud.store.all()[1].content)
    recalled_ids = [
        entry["id"] for entry in second["recalled"]["shared"]
    ]
    assert recalled_ids == [record.id]


def test_minimal_pre_fix_records_still_read_and_recall(tmp_path):
    # Backward compatibility: an episode in the pre-fix minimal
    # format, written by a plain cloud, is recalled and built on
    # by the assembled system without error.
    path = tmp_path / "memory.json"
    cloud = MemoryCloud(store=JsonFileStore(path))
    # Tag authority (KL-18, Nov 22, 2026): the legacy record
    # carries a gate: tag, so the seeding curator claims the
    # cloud's authority and presents it. (Fixture updated at
    # the KL-18 build; the test's subject — pre-fix records
    # still read and recall — is unchanged.)
    legacy = cloud.remember(
        "episodic",
        json.dumps(
            {"prompt": BENIGN, "decision": "proceed", "released": True},
            sort_keys=True,
        ),
        "pipeline",
        stage="post-gate",
        owner="shared",
        tags=["pipeline-run", "gate:proceed"],
        _authority=cloud.claim_tag_authority(),
    )
    system = DualitySystem(store=JsonFileStore(path))
    result = system.run(BENIGN)
    shared_ids = [r["id"] for r in result["recall"]["shared"]]
    assert legacy.id in shared_ids
    assert result["episode"]["written"] is True
    assert system.cloud.verify_chain() is True


# -- Fix 5: recall excludes records whose seal does not verify ---------------


def _tampered_store(tmp_path):
    path = tmp_path / "memory.json"
    cloud = MemoryCloud(store=JsonFileStore(path))
    tampered = cloud.remember("episodic", "the original honest record", "test")
    honest = cloud.remember("episodic", "a second honest record", "test")
    data = json.loads(path.read_text(encoding="utf-8"))
    data[0]["content"] = "the original honest record — EDITED BY AN OUTSIDER"
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")
    reopened = MemoryCloud(store=JsonFileStore(path))
    return reopened, tampered, honest


def test_recall_excludes_the_tampered_record_and_surfaces_it(tmp_path):
    cloud, tampered, honest = _tampered_store(tmp_path)
    assert cloud.verify_chain() is False  # the chain sees the edit

    found = cloud.recall()
    # Before the fix, recall returned the tampered record as
    # genuine. Now the honest record is served, the tampered one
    # is excluded, and the exclusion is on the surface.
    assert [r.id for r in found] == [honest.id]
    assert cloud.last_recall_exclusions == [tampered.id]


def test_system_recall_excludes_the_tampered_record(tmp_path):
    cloud, tampered, honest = _tampered_store(tmp_path)
    system = DualitySystem(store=cloud.store)
    result = system.run(BENIGN)

    shared = result["recall"]["shared"]
    assert [r["id"] for r in shared] == [honest.id]
    assert all("EDITED BY AN OUTSIDER" not in r["content"] for r in shared)
    assert result["recall_exclusions"] == [tampered.id]
    assert system.last_recall_exclusions == [tampered.id]
