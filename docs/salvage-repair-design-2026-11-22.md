# Salvage — repairing a broken chain (DESIGN, Nov 22, 2026)

Status: DESIGN ONLY — nothing built. The decision points at
the end are Ken's; the build follows the TEC-12 rhythm
(design → decision → build → review).

## The failure geometry (verified from the code)

The chain attests two different ways, and they fail
differently:

- `verify_chain()` is SEQUENTIAL and all-or-nothing: each
  record's `prev_hash` must equal the previous record's
  hash, and each `record_hash` must recompute. One tampered
  record, one out-of-band deletion, or one insertion makes
  the whole store's attestation False.
- `recall()` judges PER RECORD, in place: a record whose
  own seal fails is excluded and surfaced; its intact
  neighbors still serve. Recall degrades gracefully;
  attestation does not.

So a single corruption does NOT blind the system — recall
keeps serving the intact past. What it does do:

1. `verify_chain()` reports False forever after. There is
   no repair path at all today.
2. Maintenance freezes: consolidation and pruning refuse
   to re-seal over a record that does not verify (the
   reseal would launder the corruption into a fresh
   attestation). A long-lived store with one bad record
   can only grow.
3. The corrupt record sits in the store permanently —
   excluded from recall, present in every snapshot,
   poisoning every future attestation.

## Options

**A — Quarantine-and-reseal (recommended).** An explicit,
operator-invoked `salvage()` on the cloud:
- Records failing their OWN seal are moved out of the
  store into a quarantine (preserved verbatim, never
  deleted, never resealed over).
- If every remaining record verifies individually but the
  linkage is broken (the deletion/insertion case), the
  chain is resealed over the current sequence.
- Either way, salvage appends its own record AFTER the
  repair — metadata only, in the stop-record discipline:
  timestamp, counts, the quarantined ids, the gap
  positions and neighbor ids for a linkage repair — so
  the chain itself attests that a salvage happened and
  what it cost. The quarantine is evidence, kept apart;
  nothing is silently dropped.
This is prune's emergency cousin: pruning already removes
records and reseals over survivors, with the removal
surfaced. Salvage extends the same honesty to damage.

**B — Truncate-at-break.** Keep the verified prefix (in
chain order); quarantine the entire tail from the first
chain failure. More conservative for the linkage case —
an insertion poisons trust in everything after it — but
it throws away records that per-record verification
proves individually intact, for an ordering sin they did
not commit.

**C — Status quo.** No repair, ever: recall degrades
per-record, maintenance stays frozen, attestation stays
False. Honest, and a dead end for any store meant to
live for years.

## Recommendation

Option A, with three hard rules: salvage is
OPERATOR-invoked only (never automatic in run, recall, or
maintenance — a repair that fires itself can be made to
fire by whoever can corrupt a record); the quarantined
records are preserved verbatim outside the store, at a
location the operator names; and the salvage event is
recorded in-chain, metadata only, so the repair is part
of the attested history rather than a gap in it.

## Decision points for Ken

1. A, B, or C?
2. If A: quarantine location — a side file beside the
   store (recommended for the file store) — and is the
   in-chain salvage record acceptable, or should the
   report live outside the chain entirely?
3. May salvage ever run on a schedule, or operator-only
   forever? (Recommendation: operator-only, forever.)
