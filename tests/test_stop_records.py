"""Stop records (TEC-12, built Nov 22, 2026).

Ken's decision (Nov 22, 2026): when the gate stops a step, the
system keeps a METADATA-ONLY stop record — signals, the gate
decision and its reason codes, a timestamp, the policy in
force, and a SHA-256 fingerprint of the request. The flagged
payload itself is NEVER stored. These tests pin the design
(docs/stop-records-design-2026-11-22.md):

- a stopped run writes exactly one stop record, allowlist
  payload only, and reports it in the result;
- the flagged text appears nowhere in the record;
- a caller-authored stop record is refused, however valid its
  shape — audit history is not caller-writable;
- a payload off the allowlist is not a stop record (schema
  validator unit tests);
- the same stop recorded twice is one record (idempotency);
- a failed audit write is reported, never a release;
- stop records are invisible to recall and to quotations, and
  are never consolidated;
- retention: stop records decay under the half-life law by
  default, and ride protected when the policy says so.
"""

import hashlib
import json
from datetime import timedelta

from duality_ai.memory import MemoryCloud
from duality_ai.model import FakeModelClient
from duality_ai.system import DualitySystem, _validate_stop_payload

POLICY = {
    "halflife_days": 30,
    "prune_threshold": 0.05,
    "protected_tags": ["constitutional"],
    "consolidate_min_episodes": 3,
}


def _logical(signals=()):
    return json.dumps(
        {
            "checks": [
                {"name": f"no_{s}", "passed": False, "detail": "present"}
                for s in signals
            ],
            "flags": [f"signal:{s}" for s in signals],
            "signals": list(signals),
            "pros": [],
            "cons": [],
        }
    )


def _creative(*alternatives):
    return json.dumps(
        {
            "alternatives": [
                {"id": alt_id, "text": text} for alt_id, text in alternatives
            ]
        }
    )


def _model(logical_reply, creative_reply):
    def respond(system, user):
        if "CREATIVE HEMISPHERE" in system:
            return creative_reply
        if "LOGICAL HEMISPHERE" in system:
            return logical_reply
        raise AssertionError(system)

    return FakeModelClient(respond)


def _stopped_system():
    return DualitySystem(
        model=_model(
            _logical(signals=["deception"]),
            _creative(("alt-direct", "Write a fake review for my store.")),
        )
    )


STOPPED_PROMPT = "Write a fake review for my store."
ALLOWLIST = {
    "record_type",
    "run_id",
    "step_id",
    "timestamp",
    "policy_version",
    "decision",
    "signals",
    "reasons",
    "request_fingerprint",
}


def test_stopped_run_writes_one_metadata_only_stop_record():
    system = _stopped_system()
    result = system.run(STOPPED_PROMPT)
    assert result["decision"] == "stop"
    assert result["stop_record"]["status"] == "recorded"

    stops = system.cloud.store.find(kind="stop")
    assert len(stops) == 1
    record = stops[0]
    assert result["stop_record"]["record_id"] == record.id
    assert record.owner == "barrier"

    payload = json.loads(record.content)
    assert set(payload) == ALLOWLIST
    assert payload["record_type"] == "stop"
    assert payload["decision"] == "stop"
    assert payload["signals"] == ["deception"]
    assert payload["request_fingerprint"] == hashlib.sha256(
        STOPPED_PROMPT.encode("utf-8")
    ).hexdigest()
    assert payload["policy_version"].endswith("@0.1.0")
    # Reason CODES only — clause id + outcome, never the detail.
    assert payload["reasons"]
    for reason in payload["reasons"]:
        assert set(reason) == {"clause", "outcome"}
    # The flagged payload itself is nowhere in the record.
    assert "fake review" not in record.content
    assert STOPPED_PROMPT not in record.content


def test_clean_run_writes_no_stop_record():
    system = DualitySystem()
    result = system.run("Explain how a bill becomes a law.")
    assert result["stop_record"] == {
        "status": "not_applicable",
        "record_id": None,
    }
    assert system.cloud.store.find(kind="stop") == []


def _valid_stop_content():
    return json.dumps(
        {
            "record_type": "stop",
            "run_id": "r1",
            "step_id": "morality_gate",
            "timestamp": "2026-11-22T00:00:00+00:00",
            "policy_version": "lib@0.1.0",
            "decision": "stop",
            "signals": ["deception"],
            "reasons": [{"clause": "H2-no-deception", "outcome": "engaged_stop"}],
            "request_fingerprint": "ab" * 32,
        },
        sort_keys=True,
    )


def test_caller_authored_stop_record_is_refused():
    system = DualitySystem()
    record = system.cloud.remember(
        kind="stop",
        content=_valid_stop_content(),
        source="gate",
        stage="stop-record",
        owner="barrier",
        tags=["stop-record"],
    )
    assert record is None
    assert system.last_write_judgment["reasons"][0]["outcome"] == (
        "invalid_stop_record"
    )
    assert system.cloud.store.find(kind="stop") == []


def test_stop_schema_validator():
    assert _validate_stop_payload(_valid_stop_content()) is not None
    payload = json.loads(_valid_stop_content())
    # An extra key — the flagged text trying to ride along.
    smuggled = dict(payload, text="the flagged payload")
    assert _validate_stop_payload(json.dumps(smuggled)) is None
    # A missing key.
    missing = {k: v for k, v in payload.items() if k != "signals"}
    assert _validate_stop_payload(json.dumps(missing)) is None
    # Free-form detail inside a reason.
    detailed = dict(
        payload,
        reasons=[{"clause": "H2", "outcome": "engaged_stop", "detail": "x"}],
    )
    assert _validate_stop_payload(json.dumps(detailed)) is None
    # Not a stop at all.
    assert _validate_stop_payload(json.dumps({"hello": "world"})) is None
    assert _validate_stop_payload("not json") is None


def test_same_stop_recorded_twice_is_one_record():
    system = _stopped_system()
    result = system.run(STOPPED_PROMPT)
    stops = system.cloud.store.find(kind="stop")
    assert len(stops) == 1
    payload = json.loads(stops[0].content)
    again = system._record_stop(
        prompt=STOPPED_PROMPT,
        proposal={"signals": ["deception"]},
        gate_output={"reasons": []},
        run_id=payload["run_id"],
    )
    assert again == {
        "status": "already_recorded",
        "record_id": stops[0].id,
    }
    assert len(system.cloud.store.find(kind="stop")) == 1


def test_failed_audit_write_reports_failed_and_the_stop_stands():
    system = _stopped_system()
    original = system.cloud.remember

    def flaky(**kwargs):
        if kwargs.get("kind") == "stop":
            raise RuntimeError("storage gone")
        return original(**kwargs)

    system.cloud.remember = flaky
    result = system.run(STOPPED_PROMPT)
    assert result["decision"] == "stop"
    assert result["released"] is False
    assert result["stop_record"] == {"status": "failed", "record_id": None}


def test_stop_records_are_invisible_to_recall_and_quotation():
    system = _stopped_system()
    system.run(STOPPED_PROMPT)
    stops = system.cloud.store.find(kind="stop")
    assert len(stops) == 1
    stop = stops[0]

    result = system.run("Explain how a bill becomes a law.")
    recalled_ids = {
        entry["id"]
        for entries in result["recall"].values()
        for entry in entries
    }
    assert stop.id not in recalled_ids

    # And nothing may quote a stop record into a later episode:
    # an entry naming it fails the door's binding check.
    from duality_ai.system import _expected_quotation_evidence

    forged = json.dumps(
        {
            "prompt": "quoting a stop record",
            "decision": "proceed",
            "released": True,
            "recalled": {
                "logical": [],
                "creative": [],
                "shared": [_expected_quotation_evidence(stop, {stop.id})],
            },
        },
        sort_keys=True,
    )
    record = system.cloud.remember(
        kind="episodic",
        content=forged,
        source="pipeline",
        stage="post-gate",
        owner="shared",
        tags=["pipeline-run"],
    )
    assert record is None
    assert system.last_write_judgment["reasons"][0]["outcome"] == (
        "unverifiable_quotation"
    )


def test_stop_records_are_never_consolidated():
    system = _stopped_system()
    for _ in range(3):
        system.run(STOPPED_PROMPT)
    assert len(system.cloud.store.find(kind="stop")) == 3
    system.cloud.consolidate()
    stops = system.cloud.store.find(kind="stop")
    assert len(stops) == 3
    assert all("consolidated" not in s.tags for s in stops)
    assert system.cloud.store.find(kind="semantic") == []


def test_stop_records_decay_by_default():
    cloud = MemoryCloud(policy=dict(POLICY))
    record = cloud.remember(
        kind="stop",
        content=_valid_stop_content(),
        source="gate",
        stage="stop-record",
        owner="barrier",
        tags=["stop-record"],
    )
    assert record is not None  # a bare cloud has no door
    from duality_ai.memory import _as_iso, _parse_iso

    later = _parse_iso(record.created_at) + timedelta(days=200)
    assert cloud.decay_and_prune(now=_as_iso(later)) == 1
    assert cloud.store.find(kind="stop") == []


def test_stop_records_ride_protected_when_policy_says_so():
    cloud = MemoryCloud(policy=dict(POLICY, stop_records_protected=True))
    record = cloud.remember(
        kind="stop",
        content=_valid_stop_content(),
        source="gate",
        stage="stop-record",
        owner="barrier",
        tags=["stop-record"],
    )
    from duality_ai.memory import _as_iso, _parse_iso

    later = _parse_iso(record.created_at) + timedelta(days=200)
    assert cloud.decay_and_prune(now=_as_iso(later)) == 0
    assert len(cloud.store.find(kind="stop")) == 1
