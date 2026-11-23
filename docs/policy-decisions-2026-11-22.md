# Duality — Ken's Two Policy Decisions (Nov 22, 2026)

**Decided by:** Ken, on Lux's full recommendation ("fill it out with the full upright recommendation").
**Context:** Linear's ninth look returned MERGE for the wiring branch at `65aa9e6` with no remaining findings; these two decisions were the last items at the merge gate. Neither was a code defect — both are policy: what the system *should* do, which is the owner's call by design.

---

## Decision 1 — TEC-12 (guarded-door fork): METADATA-ONLY STOP RECORDS

When the gate stops a flagged step, the memory door no longer leaves the attempt wholly unrecorded — and it does not swallow the flagged content either. A stopped step writes a **stop record** carrying only the facts of the refusal:

- the signals that fired,
- the gate's decision and the governing reasons,
- the timestamp,
- a cryptographic fingerprint (hash) of the request — enough to recognize the same attempt again, never the flagged text itself.

The flagged payload is **not** stored. Memory can therefore remember that it was tested, recognize a repeated attempt, and let consolidation see a pattern of attempts — while a poisoned payload still never enters the store. A poisoned memory is an attack that lasts forever; a forgotten refusal is a lesson never learned. This road refuses both failures.

*Implementation note:* the current branch refuses outright; stop records are a follow-up build round against this decision (new record kind at the door, excluded from ordinary recall evidence, counted by consolidation as attempts, not knowledge). The decision is the policy; the build follows it.

## Decision 2 — Broken memory chain: FAIL-CLOSED; salvage only as a deliberate, owner-ordered repair

If the provenance chain ever breaks — a record altered outside the system's control — the system **fails closed**: maintenance refuses, broken records stay excluded, and memory does not operate on a book that cannot prove it is unrewritten. That proof is the chain's whole purpose; trusting a tampered book "partially" by default would spend the one guarantee the design exists to keep.

**Salvage is not automatic and never silent.** It exists only as a deliberate repair the owner orders, performed as its own recorded act: the verified prefix may be preserved, the broken link and everything downstream quarantined, and the repair itself entered into the record — what was kept, what was quarantined, and why — so the book's history includes its own injury and recovery, attested by the owner's decision rather than hidden by the system's convenience.

*Implementation note:* fail-closed is the branch's current behavior and stands. The owner-ordered salvage procedure is a follow-up build round against this decision.

---

## What this unblocks

The merge gate is now fully satisfied on every side: Linear's verdict (MERGE, ninth look, Nov 22, 2026), the storage verifications (TEC-5 accepted, TEC-6 closed), and both owner decisions (this record). The merge itself proceeds on Ken's word, as every push has. The two follow-up builds (stop records; the salvage-repair procedure) are scoped by this record and land as their own reviewed rounds.

---

## Addendum — Decision 3: the reuse policy (Ken, Nov 22, 2026, evening)

**Question** (raised by Perplexity's pruning probe, run the same
evening on `a1343ce`): a quotation embedded in a surviving record
outlives its pruned source and re-enters assembled recall. Does
reuse require the quotation's own current eligibility?

**Perplexity's recommendation:** yes, for model-facing recall —
quoted material needs current reuse eligibility; unverifiable
quotations are omitted from model input; the filter sits at
model-input construction, and the policy must name the surface
it protects. She did not recommend filtering structured recall
itself.

**Ken's decision: STRICTER — the filter applies at BOTH
surfaces.** A quotation embedded in a record is served only
while its source record still exists and verifies:

1. **Structured recall assembly** — when a run assembles its
   recall, embedded `recalled` entries whose referenced source
   is gone (pruned, never existed) or fails verification are
   dropped from the served copy. The drops are surfaced in the
   run's result (`recall_quotation_drops`), never hidden.
2. **Model-input construction** — when seam 1 is wired, the
   model receives only the assembled, already-filtered recall;
   Perplexity's two-case A/B test (positive control with the
   source present; pruned case asserting absence from every
   model-bound call) is the acceptance gate for that wiring.

**The archive is not a surface.** Stored records are never
rewritten by the filter; a surviving record keeps its embedded
quotations as stored evidence. The policy governs what recall
SERVES, not what memory HOLDS — the same distinction the probe
measured (retention vs recall vs model exposure).

**Status:** surface 1 implemented and tested the same evening
(`tests/test_reuse_policy_filter.py`; the probe re-run shows
boundary 2a flip from True to False under the policy, boundary
1 unchanged). Surface 2 BUILT Nov 22, 2026: seam 1 is wired
(docs/seam1-wiring-build-2026-11-22.md) and Perplexity's
two-case A/B acceptance PASSES — positive control (marker
reaches the model input with the source present) and pruned
case (marker absent from every model-bound call). Surface 2
was a recorded gate on a future build,
not present behavior. The merge gate for the current branch is
unchanged: this decision is not a gate on it (Perplexity's own
framing, adopted).
