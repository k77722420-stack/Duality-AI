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

## Fix round — Linear's hold on 75ac36d (Nov 23, 2026)

Linear's static review held the pushed head with three
preservation defects; his four probe cases were run verbatim
against the unmodified code first and FAILED 4/4, then passed
4/4 after the fixes. All four are permanent tests in
tests/test_salvage.py, alongside Perplexity's process-kill
regression (a different failure boundary — retained).

1. **Torn tail.** The quarantine append did not ensure a
   newline separator: a partial last line, or a complete
   entry whose final newline never landed, concatenated with
   the next entry and the combined line parsed as nothing —
   salvage could remove a record and report success with no
   parseable evidence. Fix: before appending, a non-empty
   side file not ending in a newline is terminated first.
2. **Payload-keyed dedupe.** Idempotency keyed on record id
   alone suppressed different evidence: a record whose
   corruption changed between attempts was removed on retry
   without its new payload being preserved. Fix: dedupe keys
   on the record's full payload (canonical JSON); identical
   retries still preserve exactly once.
3. **Exact-record removal.** Salvage classified individual
   records but removed by id, deleting every record sharing
   the id — a corrupt copied-id twin took its honest
   original with it. Fix: a store-level `remove_one(record)`
   removes a single occurrence matched on full payload
   (JsonFileStore: first equal entry in the sequence;
   InMemoryStore: the payload-checked entry under the id);
   salvage removes exactly the records it classified, and
   the survivor sequence is preserved.

Suite after the round: 322. Perplexity's interruption probe
and snapshot regression re-run after the fixes: both PASS.

Composition, corrected on Linear's note: this branch's tree
also carries experiments/sandbox_real_session.py (the Phase
1.4 real-model session harness, stacked here since Nov 22 —
the session run-sheet checks out this branch) and a
docs/policy-decisions-2026-11-22.md that differs from main
(it records Decision 4, the salvage authorization itself).
Both are declared in this round's scope explicitly; the
earlier "nothing else differs" phrasing is withdrawn.

## Fix round 2 — Linear's hold on 9230a5e (Nov 23, 2026)

Linear's static review held the fix-round head with two
further preservation defects; his two probe cases were run
verbatim against the unmodified code first and FAILED 2/2,
then passed 2/2 after the fixes. Both are permanent tests
in tests/test_salvage.py.

1. **Stale classification.** Salvage classified the records
   an already-open store happened to hold, and only then
   opened the repair batch — which reloads the file store
   from disk. An offline change completed before salvage
   started was therefore never classified: its removal
   silently failed and the unexamined record was resealed
   as valid; a stale healthy snapshot could likewise
   pronounce a damaged disk healthy. No concurrent writer
   is required. Fix: classification now runs INSIDE the
   batch, on the working sequence the batch reloaded, and
   a classified removal that fails raises — the batch
   discards the uncommitted repair and nothing is
   resealed. The quarantine evidence already appended
   stays preserved; a retry reclassifies from disk.
2. **Python-equality removal.** Exact removal compared
   payloads with Python `==`, under which 1.0 == 1 — but
   their canonical encodings, and therefore their record
   hashes, differ. A corrupt copied-id twin (strength=1)
   could cause removal of its honest original
   (strength=1.0) and be resealed in its place. Fix: a
   single canonical-payload identity — the same JSON form
   the seal is computed over — now backs every remove_one
   implementation, the same identity the quarantine
   dedupe already used.

Perplexity's process-kill regression and snapshot
regression were re-run after these fixes: both PASS.
Full suite: 324 passed.

**Merge disposition (Linear's recommendation, Nov 23):**
experiments/sandbox_real_session.py is held back from
the salvage merge for a separate correction round (its
fact-recall case, OLLAMA_HOST enforcement, and same-store
comparison are Phase 1.4's pre-work). Decision 4
(docs/policy-decisions-2026-11-22.md) belongs in the
salvage scope.

## Fix round 3 — Linear's hold on 89de400 (Nov 23, 2026)

The preservation fixes passed static review, but the
in-batch classification introduced a contract regression:
healthy salvage — documented as a strict no-op, nothing
written or appended — now exited the file store's batch,
whose clean exit published unconditionally. A healthy
file was replaced, a nonexistent store became an actual
[] file, and a publication failure could raise where no
repair was needed. Linear's probe (publication patched to
raise) failed pre-fix exactly as predicted, and passes
after; it and the nonexistent-store case are permanent
tests in tests/test_salvage.py.

Fix: the batch itself now detects change. JsonFileStore's
batch fingerprints the working sequence it loaded
(canonical serialization, hashed) and publishes on exit
only if the fingerprint differs. Classification stays
inside the batch; an unchanged repair transaction exits
without publication. The detection compares content, so
in-place edits under a batch (consolidation's marking)
still publish exactly once, as before.

Full suite: 326 passed. Perplexity's interruption and
snapshot probes re-run: PASS.

## Fix round 4 — Linear's hold on 717e361 (Nov 24, 2026)

Linear kept the hold: the healthy no-op fix was correct,
but the batch entry fingerprint was computed AFTER the
ownership flags (_batching, _batch_owner) were set and
BEFORE the try/finally that clears them. A fingerprint
failure — a lone surrogate loaded from JSON, which
json.loads accepts but UTF-8 encoding rejects — left the
flags set forever: later same-thread batches silently
joined the dead batch (no lock, no reload), and every
save deferred indefinitely. His case was reproduced
verbatim pre-fix (raise + wedged flags + a post-wedge
remember that never reached disk + a second batch joining
silently) and is now a permanent test in
tests/test_salvage.py.

Fix: the entry fingerprint is computed BEFORE the
ownership flags are set, inside the same locked section.
If it raises, no flag was ever set, the lock releases,
and the failure is loud at its true point; the store
stays fully usable once the underlying record problem is
repaired. Post-fix probe: the raise still surfaces, the
flags are clean, salvage over the repaired file reports
healthy, and saves reach disk again.

Full suite: 327 passed. Perplexity's interruption and
snapshot probes re-run: PASS.
