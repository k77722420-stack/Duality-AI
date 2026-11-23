# Stop records — build report (Nov 22, 2026)

**Implements:** TEC-12 (Ken's decision, Nov 22, 2026) to the
design in docs/stop-records-design-2026-11-22.md, with
Perplexity's §5 input. **Retention: PROTECTED, Ken's call at
the build** (design open question 1) — stop records do not
decay; the choice is the policy switch
`stop_records_protected` in config/memory_policy.json,
reversible by a later decision.

## What was built

- **Kind `stop`** joins RECORD_KINDS, with its own allowlist
  schema enforced at the write path: `_validate_stop_payload`
  accepts exactly the nine design keys, reason entries of
  exactly {clause, outcome} (codes — the free-form detail
  never crosses), signal labels, and a SHA-256 request
  fingerprint. The flagged payload is never stored.
- **Authorization, bound to the operation and the kind:** run()
  registers the exact payload digest in a stop-only registry;
  the door admits a stop record only on a live registration
  AND a schema match. An episode registration cannot authorize
  a stop record, nor the reverse. A caller-authored stop
  record — however valid its shape — is refused
  (`invalid_stop_record`): audit history is not
  caller-writable.
- **Idempotency:** the durable key is the triple (run_id,
  step_id, request fingerprint), all inside the payload; a
  second recording of the same stop returns
  `already_recorded` with the existing record's id.
- **Failure honesty:** the stop record is written after the
  episode; if its write fails or is refused, the run result
  reports `stop_record: {"status": "failed"}` — the gate's
  decision is unaffected, never converted into a release.
  Non-stop runs report `not_applicable`.
- **Invisibility:** stop records live on the `barrier` shelf
  (never a recall shelf) and are excluded by kind from the
  recall precedent's eligible set, from the door's verified
  evidence map (nothing may quote them), and from
  consolidation (which pools episodic records only).
- **Retention mechanism:** `MemoryCloud.stop_records_protected`
  reads the policy switch; when true, the prune pass skips the
  `stop` kind. When false, stop records decay like any record.
- The gate now retains its library `version`, so a stop
  record's `policy_version` names the library in force
  (`<library>@<version>`).

## Tests

- New: tests/test_stop_records.py — 10 tests (the record and
  its allowlist; the flagged text's absence; caller forgery
  refused; the schema validator; idempotency; a failed audit
  write; recall/quotation invisibility; no consolidation;
  both retention modes).
- Disclosed updates to three existing tests, for the contract
  TEC-12 deliberately changed — "a stopped step leaves the
  cloud empty" is no longer true; it leaves exactly the stop
  record: tests/test_system.py (stopped-step test now asserts
  the stop record alone is stored),
  tests/test_linear_fix_round.py (the three disguised-phrase
  cases assert the same, plus the flagged phrase's absence),
  tests/test_linear_fix_round_2.py (the failed-live-stage test
  now selects the episode record by kind instead of taking
  the last record). No assertion's intent was weakened.
- Suite: 273 → 283, all passing locally at the build commit.
