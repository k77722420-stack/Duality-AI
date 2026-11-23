# Salvage build — quarantine-and-reseal (Nov 22, 2026)

Ken's Decision 4 adopted the design's recommendations in
full (Option A; side-file quarantine; the salvage event
recorded in-chain, metadata only; operator-invoked only,
forever). Built the same evening on
duality-salvage-2026-11-22, stacked on the snapshot branch.

**MemoryCloud.salvage(quarantine_path)** walks the store
once, judging each record by the two checks verify_chain()
makes, per record: a record whose stored hash does not
recompute from its contents is quarantined — removed and
preserved verbatim (JSON lines, with the failure reason)
in the operator-named side file. A record whose own seal
verifies but whose linkage is broken is kept; each gap
(position, record id, expected vs found prev-hash) is
recorded. Removals and resealing happen inside the store's
maintenance batch (TEC-6), and the repair appends its own
record in-chain — kind semantic, source "salvage", metadata
only: timestamp, the quarantined ids + reasons, the gaps,
the kept count. A healthy store is a strict no-op: nothing
written, nothing appended, status "healthy".

**What the tests pin** (tests/test_salvage.py, 4): the
healthy no-op; a tampered record quarantined verbatim with
the chain healed and its honest neighbors still serving,
the in-chain event carrying ids and reasons but never the
tampered content; an out-of-band deletion resealed as a
recorded gap with nothing quarantined; and the design's
central claim end-to-end — pruning REFUSES over the broken
chain (the maintenance freeze) and runs again after
salvage (the thaw).

**Bounds:** salvage judges seals and linkage, not truth —
a record corrupted so its hash was recomputed by the
corruptor is indistinguishable from honesty (the chain's
standing bound, unchanged). The quarantine file is
append-only across runs. Nothing calls salvage except the
operator. Suite: 311 → 315.
