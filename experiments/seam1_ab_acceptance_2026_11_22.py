"""Seam-1 A/B acceptance — Perplexity's gate for wiring recall
into the pipeline (her protocol, from the pruning-probe
conclusion, Nov 22, 2026; Ken's Decision 3 made the policy
stricter: the filter applies at BOTH surfaces).

Fixture: the pruning probe's A/B pair — source record A with a
unique marker; episode B quoting A in its recalled section.
A recording model client captures every model-bound call.

Case A (positive control): A present and eligible. Assert B
is selected by the new run's recall AND the marker reaches
the model input. (Proves the wiring is active and the test
can detect the quotation.)

Case B (pruned): A pruned first. Assert B is still selected;
B's STORED quotation is unchanged (the archive is not a
surface); the marker is absent from every model-bound call;
and — Ken's stricter surface-1 rule — absent from the new
run's structured recall as well.

Run before wiring: Case A's model assertion fails (the seam
is disconnected) — the baseline this gate exists to measure.
Run after wiring: every assertion passes.
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
A_CREATED = T0 - timedelta(days=100)
PRUNE_AT = T0 + timedelta(days=40)

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
    store = InMemoryStore()
    system = DualitySystem(store=store)
    a = system.cloud.remember(
        kind="episodic",
        content=A_CONTENT,
        source="field-note",
        stage="intake",
        owner="shared",
        tags=["field-note"],
        created_at=A_CREATED,
    )
    assert a is not None
    result_b = system.run("What notes are on the shared shelf today?")
    assert result_b["episode"]["written"] is True
    b_id = result_b["episode"]["record_id"]
    b = next(r for r in store.all() if r.id == b_id)
    assert MARKER in json.dumps(json.loads(b.content).get("recalled", {}))
    return store, a.id, b_id


def _run_case(prune: bool) -> dict:
    store, a_id, b_id = _build_store()
    # Linear's alignment (seam-1 re-verdict, Nov 22, 2026):
    # B's stored content is captured BEFORE any pruning and
    # compared exactly at every stage — the full invariant
    # the stronger probe asserts, not marker presence.
    before = next(r for r in store.all() if r.id == b_id).content
    stored_after_prune = before
    if prune:
        cloud = MemoryCloud(store=store)
        cloud.decay_and_prune(now=PRUNE_AT)
        fresh = MemoryCloud(store=store)
        ids = {r.id for r in fresh.store.all()}
        assert a_id not in ids and b_id in ids and fresh.verify_chain()
        stored_after_prune = next(
            r for r in store.all() if r.id == b_id
        ).content
    calls: list = []
    system = DualitySystem(store=store, model=_recording_model(calls))
    result = system.run("Give me a plain status summary.")
    stored_after_run = next(
        r for r in store.all() if r.id == b_id
    ).content
    recall_ids = [
        e["id"] for entries in result["recall"].values() for e in entries
    ]
    # A is itself selected, so generic marker presence does
    # not prove B's QUOTATION rendered: assert the specific
    # quoted line in BOTH hemisphere messages.
    quote_line = "  - quoted [episodic]: " + A_CONTENT
    return {
        "b_selected": b_id in recall_ids,
        "stored_exact": before == stored_after_prune == stored_after_run,
        "quote_in_both": len(calls) == 2
        and all(quote_line in c["user"] for c in calls),
        "marker_in_model": MARKER in json.dumps(calls),
        "marker_in_recall": MARKER in json.dumps(result["recall"]),
        "calls": len(calls),
    }


def main():
    a = _run_case(prune=False)
    print(f"CASE A (A present):  B selected={a['b_selected']}  "
          f"B quotation in both model messages={a['quote_in_both']}  "
          f"marker in structured recall={a['marker_in_recall']}  "
          f"model calls={a['calls']}")
    b = _run_case(prune=True)
    print(f"CASE B (A pruned):   B selected={b['b_selected']}  "
          f"B stored content exact throughout={b['stored_exact']}  "
          f"marker in model input={b['marker_in_model']}  "
          f"marker in structured recall={b['marker_in_recall']}  "
          f"model calls={b['calls']}")
    ok = (
        a["b_selected"] and a["quote_in_both"]
        and b["b_selected"] and b["stored_exact"]
        and not b["marker_in_model"] and not b["marker_in_recall"]
    )
    print("ACCEPTANCE:", "PASS" if ok else "FAIL")
    # Linear's correction (seam-1 hold, Nov 22, 2026): a FAIL
    # print with a success exit code is a harness that can lie
    # to a script. Exit nonzero on failure.
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
