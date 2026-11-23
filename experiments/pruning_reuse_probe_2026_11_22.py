"""Pruning-reuse probe — Perplexity's test, run as specified (Nov 22, 2026).

Question: an inline quote survives pruning of its source record
(confirmed by code reading). Is the surviving copy only historical
evidence, or can it become active context again?

Protocol (hers, with two disclosed adaptations):
  - Store unprotected source record A with a unique harmless
    marker, through the normal write path; verify A is eligible
    for recall.
  - Run the normal episode builder so episode B recalls A; verify
    the marker appears only in B's structured recalled section.
  - Advance the clock; prune so A is removed and B survives;
    verify both facts from a fresh cloud; verify the chain.
  - Run a new step through the normal recall path, B eligible,
    marker not in the request. Report the marker at three
    boundaries: (1) still stored inside B; (2) visible in the new
    step's assembled context; (3) copied into episode C.
  - A pre-prune control on a parallel store proves the recall
    path can surface the marker while A is present.
  - Consolidation never runs in this probe (it is an explicit
    cloud operation; run() does not invoke it).

Adaptations, disclosed: (a) the "clock" is the records' ages —
A is backdated 100 days and pruning is invoked at +40 days, the
two moments her fixed clock names; runs themselves execute at
real time. (b) Boundary 2 is reported in two parts, because in
this architecture recall is assembled by the system but NOT fed
to the pipeline (seam 1): 2a = the marker in the new run's
structured recall output; 2b = the marker in the exact inputs
sent to the model (live pipeline, recording fake client).

Setup facts are asserted. The three boundary results are
OBSERVATIONS, not policy votes.
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
    """Store with A written and episode B recalling it."""
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
    assert a is not None, "setup: A's write was refused"
    recalled = system.cloud.recall(owner="shared")
    assert any(r.id == a.id for r in recalled), "setup: A not recall-eligible"
    result_b = system.run("What notes are on the shared shelf today?")
    assert result_b["episode"]["written"] is True, "setup: B not written"
    b_id = result_b["episode"]["record_id"]
    b = next(r for r in store.all() if r.id == b_id)
    payload_b = json.loads(b.content)
    recalled_blob = json.dumps(payload_b.get("recalled", {}))
    own_blob = json.dumps(
        {k: v for k, v in payload_b.items() if k != "recalled"}
    )
    assert MARKER in recalled_blob, "setup: marker not in B's recalled section"
    assert MARKER not in own_blob, "setup: marker leaked into B's own sections"
    return store, a.id, b_id


def _control():
    """Pre-prune control: the recall path surfaces the marker
    while A is still present."""
    store, a_id, b_id = _build_store()
    system = DualitySystem(store=store)
    result = system.run("Give me a plain status summary.")
    blob = json.dumps(result["recall"])
    return MARKER in blob


def main():
    print("=== PRUNING-REUSE PROBE — raw output ===")
    print(f"marker: {MARKER}")
    control = _control()
    print(f"CONTROL (pre-prune, A present): marker in new run's "
          f"recall output = {control}")

    store, a_id, b_id = _build_store()
    print(f"setup: A stored (id {a_id[:8]}…), backdated 100 days; "
          f"B written recalling A; marker only in B's recalled section")

    cloud = MemoryCloud(store=store)
    pruned_count = cloud.decay_and_prune(now=PRUNE_AT)
    fresh = MemoryCloud(store=store)
    ids = {r.id for r in fresh.store.all()}
    a_gone = a_id not in ids
    b_kept = b_id in ids
    chain_ok = fresh.verify_chain()
    print(f"prune at +40d: pruned_count={pruned_count} "
          f"A_removed={a_gone} B_survived={b_kept} chain_valid={chain_ok}")
    assert a_gone and b_kept and chain_ok, "setup: prune facts failed"

    b = next(r for r in fresh.store.all() if r.id == b_id)
    boundary1 = MARKER in b.content
    print(f"BOUNDARY 1 — marker still stored inside B: {boundary1}")

    calls: list = []
    system_c = DualitySystem(store=store, model=_recording_model(calls))
    result_c = system_c.run("Give me a plain status summary.")
    recall_ids = [
        entry["id"]
        for entries in result_c["recall"].values()
        for entry in entries
    ]
    b_selected = b_id in recall_ids
    print(f"new run: B selected by recall = {b_selected}")
    if not b_selected:
        print("RESULT: INCONCLUSIVE — recall did not select B.")
        return
    boundary2a = MARKER in json.dumps(result_c["recall"])
    model_blob = json.dumps(calls)
    boundary2b = MARKER in model_blob
    print(f"BOUNDARY 2a — marker in the new run's structured "
          f"recall output: {boundary2a}")
    print(f"BOUNDARY 2b — marker in the exact inputs sent to "
          f"the model ({len(calls)} calls): {boundary2b}")

    boundary3 = None
    if result_c["episode"]["written"]:
        c_id = result_c["episode"]["record_id"]
        c = next(r for r in store.all() if r.id == c_id)
        boundary3 = MARKER in c.content
    print(f"BOUNDARY 3 — marker copied into episode C: {boundary3} "
          f"(C written = {result_c['episode']['written']})")
    print("=== END ===")


if __name__ == "__main__":
    main()
