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

**Interruption fix (Nov 23, 2026, Perplexity's build
gate):** her exact acceptance test — persistent store
(JsonFileStore), repair process killed by signal after
the quarantine append, before publication — passed on
publication behavior (fresh instance saw the original
degraded chain, no salvage event, maintenance still
frozen) but exposed one defect: the retry appended the
same record to quarantine a second time, counting one
incident as two. Quarantine appends are now idempotent:
salvage reads the side file first and appends only
records not already preserved; a line torn by the kill
itself preserves nothing and does not block the retry.
The interruption test is a permanent regression
(tests/test_salvage.py). Perplexity's gates on both the
snapshot and salvage closed Nov 23, 2026 on the reported
local evidence. Suite: 315 → 316.

**Operator contract (Perplexity's closing conditions,
Nov 23, 2026 — stated, not implied):**
- *Exclusive access is a precondition, not an
  implementation guarantee.* Operators must stop other
  writers before the scan begins and keep them stopped
  through publication. The store's batch lock protects
  publication, not the interval between examination and
  repair. "Operator-invoked only" says who may call
  salvage; it does not serialize salvage against
  writers.
- *A linkage-only repair preserves a gap record, not
  the original chain.* That suffices to restore
  maintenance. An operator who needs to reconstruct or
  independently audit the full pre-repair state must
  preserve a separate pre-repair copy BEFORE invoking
  salvage. The post-repair claim is exactly: "The
  current chain verifies; a historical discontinuity
  was recorded."
- *Durability bound:* the interruption evidence
  establishes recovery from a process kill after write
  and close. It does not establish power-loss
  durability; file close alone is not evidence the
  quarantine data reached durable storage.
