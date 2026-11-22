# Fix Round 7 — Linear's seventh look (Nov 22, 2026)

**Directed by:** Ken — "Engage with all recommendations."
**Base:** branch `duality-system-wiring-2026-11-21` at `4460be7` (round 6's `be84a6d` + Ken's CI commit).
**Seventh look:** HOLD at be84a6d — two correctness findings + one flaw in round 6's new verification test. Saved verbatim: `duality-linear-seventh-look-2026-11-22.md`. **All three confirmed by execution before fixing** (`duality-linear-seventh-look-verification-2026-11-22.md`; repros /tmp/duality-verify7/).
**Result: 235 tests passed, 0 failed** (228 → 235; 7 new tests in `tests/test_linear_fix_round_7.py`; the one existing test changed is the mis-targeted injection Linear explicitly asked to have corrected). TEC-12 and the broken-chain recall policy were NOT touched — both remain Ken's decisions, and the HOLD did not turn on either.

---

## Finding 1 (HIGH) — encoded selected output bypassed release inspection

**What Linear found.** Round 6 taught the gate to inspect the selected answer, but the inspection scanned the text raw, while the memory door decodes JSON before judging. An answer encoded as JSON — `{"answer":"Write a f\u0061ke review for my store."}` — passed release (proceed, released True, signals [], threat 0) and was caught only at the door afterward. The leniency variant survived too: encoded performing content did not withdraw contexts. Linear's classification: a representation-handling discrepancy, not the detector's documented semantic limitation (KNOWN-LIMITATIONS entry 16 stands as written — it is about perception, not representation).

**Verification (Lux, by execution).** Primitives exactly as stated: `detect_signals(encoded) == []`, `performs(encoded) is False`, `_judged_signals(encoded) == ["deception"]`. Through the assembled system: proceed / True / [] / 0, episode refused at the door.

**Fix.** The door's decoding inspection — strict parse, the iterative string walk (keys included, nested JSON strings decoded in turn, one budget), the signal union — moved from system.py into a shared module, **`src/duality_ai/inspection.py`** (the strictjson pattern: one mechanism, per-surface policy), joined by a performs twin, `judged_performs`, under the same parse discipline. system.py imports the names back as its historical private aliases — every existing import and test untouched, the door's policy unchanged. live.py's selected-output inspection now runs `judged_signals` + `judged_performs` on the chosen text; an output the walk cannot fully inspect (duplicate keys, budget, non-syntax parse failure) raises the hub's format failure, and `run()` fails the step closed there like every other stage — nothing is released unjudged.

**Regression tests (5).** The representation gap pinned at the primitives; Linear's repro verbatim at system level (now stop / False / [deception] / threat 1); the encoded leniency variant (contexts withdrawn, stop); an encoded-benign control (releases clean — decoding invents no flags); the uninspectable-output case (duplicate-key JSON answer → hub format failure on record, stop, unreleased).

**Post-fix repro:** decision stop, released False, signals [deception], threat_units 1 — corrected value-for-value.

*Scope note:* the deterministic skeleton pipeline was examined and left alone — it has no encoder (its creative hemisphere serves a fixed menu of plain-text framings), and in the assembled system the door judges its episodes with the same shared inspection. The parity gap required a model free to encode; that is the live pipeline, and it is closed there.

## Finding 2 (MEDIUM) — consolidation returned pre-reseal provenance

**What Linear found.** Round 6's write-path fix (remember returns a detached copy) meant `_consolidate` captured the summary's copy BEFORE `_reseal_chain()` rewrote the stored record's links — the returned prev_hash/record_hash were obsolete on arrival. The stored chain was always valid; round 6's regression checked isolation, not provenance equality.

**Verification.** Both backends: returned hashes ≠ stored hashes; `verify_chain()` True.

**Fix (memory.py).** After the reseal, the pass rebuilds its return list from the store: a `_copy_record` of each FINAL stored summary. Isolation (round 6) and currency (round 7) now hold together.

**Regression tests (2, parametrized over both backends).** Returned prev_hash == stored prev_hash and record_hash == stored record_hash; chain verifies; mutating the return still leaves the store untouched.

**Post-fix repro:** hashes equal on both backends, chain verifies.

## Finding 3 (verification gap) — the "mid-reseal" test fired in preflight

**What Linear found.** Round 6's fault test counted hash calls from the start of the pass; call 3 landed in `_require_verified_chain()` (the preflight), before summary creation, marking, or resealing. It proved rollback of a preflight failure — not the mid-reseal rollback its name claimed. TEC-6 therefore remained not-fully-closed on exactly this point.

**Verification.** Instrumented run: the raise fired in phase "preflight"; reseal-phase hash calls: 0.

**Fix (test only — `tests/test_storage_runtime_evidence.py`).** The fault now arms on entry to `_reseal_chain` (a spy records entry) and fires on the second reseal-phase hash recomputation — after at least one reseal mutation. The test asserts the phase was reached (`entered` True, ≥2 armed hashes) alongside the original property: file byte-for-byte identical, reopening serves the pre-pass state, chain intact. This is the one existing test changed in the round, at Linear's explicit direction ("not adding new test requirements beyond correcting the mis-targeted injection").

## On Linear's verification decisions
- TEC-5: Linear accepted the process-level regression as present and appropriate (static support). With CI now running the suite on GitHub's machines per push, its execution is reproduced there as well.
- TEC-6: the corrected mid-reseal evidence is the last item Linear listed as missing; this round supplies it, targeted as prescribed.
- Record note: Linear's "228 passes remain Lux's local evidence" was overtaken the same afternoon — Actions run #1 on the branch head (4460be7) concluded Success, "228 passed in 4.11s". This round's push will produce the next independent count the same way.

## Files changed
- `src/duality_ai/inspection.py` — **new** (the door's decoding inspection, shared; mechanism moved unchanged, plus `judged_performs`).
- `src/duality_ai/system.py` — definitions moved out; names imported back as aliases; door behavior unchanged.
- `src/duality_ai/live.py` — selected-output inspection via the shared judgment; hub format-failure path wired into `run()`; docstring parity rule.
- `src/duality_ai/memory.py` — consolidation returns final resealed copies.
- `tests/test_linear_fix_round_7.py` — **new**, 7 tests.
- `tests/test_storage_runtime_evidence.py` — the mid-reseal test re-armed (Linear-directed correction).
- `docs/fix-round-7-report-2026-11-22.md` — this report, in the repo.

## Deliberately NOT touched
- TEC-12, salvage vs fail-closed, TEC-7 — Ken's decisions / untouched, as before.
- The detector itself (markers.py) — entry 16's limitation is perception, and this round changed representation handling only.
- Main branch — untouched; merge still gated on Linear's verdict + Ken's two decisions.
