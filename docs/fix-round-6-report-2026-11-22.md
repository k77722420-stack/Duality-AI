# Duality AI — Fix Round 6 Report
Date: Sun Nov 22, 2026 · Builder: Lux · Auditor: Linear (sixth look, HOLD at 64b4f28)
Branch: duality-system-wiring-2026-11-21 · Base head: 64b4f28 (local twin 13f7ad1)
Status: **Fixed locally, verified by execution, double-checked at Ken's direction, and pushed with the full recommendation package on Ken's "engage with all recommendations" (Nov 22, 2026).**

## The round in one line
Linear's three findings are fixed; the two parser/copy findings were closed as CLASSES, not instances — one strict JSON loader now serves both judged surfaces, and one deep-copy rule now governs every record that crosses the memory cloud's boundary. Suite: **203 → 219 passed, 0 failed; zero existing tests changed.**

## Finding 1 (High) — the gate judged the request, never the release — FIXED
- **Was:** live detection ran on the request only. Benign request + flagged selected answer ("Write a fake review for my store.") → decision "proceed", released True, threat 0; the memory door refused the episode afterward, unable to retract the release.
- **Fix (live.py, `LivePipeline._merge`):** the SELECTED framing's text is inspected before the proposal reaches the gate. Its detected signals join the union the gate sees; leniency's content condition must hold for the output too — a selected answer that itself `performs` withdraws every granted context (the variant Linear explicitly said signal-union alone would not close). The hub still proposes; the gate still judges — it now judges what would actually be released.
- **After (Linear's repro, re-run):** decision "stop", released False, proposal signals ["deception"], barrier threat_units 1. Episode still refused at the door — the standing TEC-12 posture, unchanged.

## Finding 2 (Medium) — recall() aliased mutable imported fields — FIXED
- **Was:** recall built results with `dataclasses.replace`, copying only `tags`. A recalled record's list-valued `source` stayed shared with the stored record; a caller's append rewrote stored memory, broke its seal, and hid the record from later recalls (JSON file itself intact; reopening restored it).
- **Fix (memory.py, `MemoryCloud.recall`):** every returned record is now a deep copy via `_copy_record` — the rule round 5 stated, applied at the cloud's boundary to ALL fields. The decayed strength is set on the copy; stored records are never mutated by a recall. The now-unused `dataclasses.replace` import was removed.
- **After (Linear's repro, re-run):** stored source unchanged after recall mutation, chain verifies, record still served by recall.

## Finding 3 (Medium) — duplicate keys in live replies discarded evidence — FIXED AS A CLASS
- **Was:** the live reply parser used plain `json.loads`; a logical reply repeating "signals" kept only the last value — a reported deception signal vanished (proceed instead of stop). The memory door had rejected duplicates since round 4; the live parser had not. Two parsers, two answers to the same hole.
- **Fix:** new shared module **`src/duality_ai/strictjson.py`** — `loads_strict` + `reject_duplicate_keys` + `DuplicateKeyError` (a ValueError, so existing fail-closed handlers catch it). The door's mechanism moved there intact (system.py keeps its names as aliases; its policy — duplicates are uninspectable — is unchanged, and its parser-error-kind distinction is preserved and pinned by test). live.py's `_parse_json_object` now parses through the shared loader and names the repeated key in the format failure. Mechanism shared; policy stays per-surface.
- **After (Linear's repro, re-run):** duplicate "signals" → format failure, decision "stop", released False. Single-key control unchanged (stop).

## Regression tests — tests/test_linear_fix_round_6.py (16 new)
- Fix 1 (4): selected-output signals reach the gate (pipeline); Linear's repro through the assembled system (incl. threat_units == 1); performing selected output withdraws leniency; explaining selected output keeps leniency (control).
- Fix 2 (6): recall-result mutation of list-valued, dict-valued, and nested mutable fields, parametrized over BOTH backends (InMemoryStore, JsonFileStore); tags ride along as the control in the nested test.
- Fix 3 (6): duplicate "signals" in a logical reply fails closed with the key named in the trace; duplicate key in a creative reply; duplicate key nested in a checks entry; `loads_strict` unit tests (rejection at any level; parser error kinds preserved — JSONDecodeError vs plain ValueError on a 5,000-digit integer); the door still refuses duplicate-key content as uninspectable.

## Verification
- Linear's three repros (saved at /tmp/duality-verify6/) re-run post-fix: all three now show the corrected outcomes, value for value.
- Full suite: **219 passed, 0 failed** (3.51s). Baseline before the round: 203 passed.
- Files changed: `src/duality_ai/live.py`, `src/duality_ai/memory.py`, `src/duality_ai/system.py` (modified); `src/duality_ai/strictjson.py`, `tests/test_linear_fix_round_6.py` (new). No existing test file was modified.

## Addendum — the double-check (Ken's direction, Nov 22, 2026: "go over it two times just to be sure")
- **Pass 1 (execution + diff):** full suite re-run — 219 passed again; Linear's three repros re-run — corrected outcomes again; the complete diff read line by line — exactly the intended scope (3 source files modified, strictjson.py + round-6 tests new), no stray edits.
- **Pass 2 (adversarial sibling sweep):** every JSON parse surface enumerated — live replies and door inspection are strict through the shared loader; `_recalled_evidence`'s plain parse is classification only (the door judges the final payload regardless); model.py's HTTP-envelope parse is transport (the extracted reply is strictly parsed downstream); the store-file load is plain, but a duplicate key there breaks the record's seal and the record is excluded at recall — fail-closed outcome (strict-loading the store file noted as possible future hardening, not a hole). Every record-returning surface enumerated: recall is fixed — **but the sweep caught one more of the finding-2 class, verified by execution: the cloud's WRITE-path returns — `remember()` and `consolidate()` — hand the caller the live stored object (InMemoryStore; the working copy for JsonFileStore). Mutating a returned record rewrites stored content and breaks its seal.** Repros: /tmp/duality-verify6/verify_remember.py, verify_consolidate.py.
- **Status of that catch:** NOT yet fixed — surfaced to Ken with the recommendation to fold it into round 6 before pushing (return `_copy_record` from both write-path returns + regression tests), so the round's "copy class closed" claim is complete. Awaiting Ken's word, with the push.

## Addendum 2 — all senior-hat recommendations engaged (Ken's direction, Nov 22, 2026)
Ken approved the full recommendation list from the double-check. All of it is in this push:
- **Write-path fold-in (the double-check's catch):** `remember()` now returns `_copy_record(record)`; since `consolidate()`'s results are `remember()`'s returns, both write-path surfaces are closed by the one rule. 4 regression tests added (both surfaces × both backends). The round's copy-class claim is now complete: read path (recall) and write path (remember/consolidate) alike.
- **TEC-5 runtime evidence:** `tests/test_storage_runtime_evidence.py` — two independent PROCESSES × 15 appends each on one JSON store file: all 30 records land, chain verifies. TEC-5's mechanism now has process-level execution evidence, not only threads.
- **TEC-6 runtime evidence (same file):** final-write failure injected during consolidation AND during pruning (file byte-for-byte identical afterward; reopening serves the pre-pass state, chain intact); a failure injected partway through consolidation's hash recomputation (the mid-reseal case — same property); and the exactly-one-save assertion for a changed consolidation (one `_save_locked` call). What Linear listed as missing is now executed and green.
- **CI:** `.github/workflows/tests.yml` — GitHub Actions runs the suite (Python 3.12) on every push and pull request. From this push onward, the count is reproduced on GitHub's machines — evidence neither Lux nor Linear produced.
- **Docs (the review-flow acts, on Ken's approval):** KNOWN-LIMITATIONS entry 1 marked RETIRED (2026-11-22) in the museum's own format, carrying Linear's qualification verbatim in substance — "structural sequencing, not functional completion"; new entry 16 records the single-detector limitation (all inspection surfaces read `markers.detect_signals` — diverse placement, identical perception); THESIS-COMPLETE §6 gained a dated update note correcting its two stale claims and its test count.
- **Final suite: 228 passed, 0 failed** (203 pre-round → 219 after the three findings → 228 with the fold-in and evidence). Zero existing tests changed across the whole round.

## Deliberately NOT touched (unchanged by this round)
- **TEC-12** (guarded-door fork) and **salvage vs fail-closed** — Ken's decisions; Linear's HOLD did not turn on either, and neither posture moved.
- **TEC-5 / TEC-6 runtime evidence** (independent-process contention; fault/reopen during consolidation and pruning) — still open, hardening-stage work, exactly as Linear left it.
- KNOWN-LIMITATIONS §1 / THESIS §6 wording ("structural sequencing, not functional completion") — a Ken/Linear review-flow act, not a fix-round edit.
- main (f87bc82) untouched; nothing merged; nothing pushed.
