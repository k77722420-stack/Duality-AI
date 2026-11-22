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
