# Fix Round 8 — Linear's eighth look (Nov 22, 2026)

**Directed by:** Ken — "Engage — fix the leniency regression."
**Base:** branch `duality-system-wiring-2026-11-21` at `c0145c9` (round 7).
**Eighth look:** HOLD solely for one regression round 7 introduced. Saved verbatim: `duality-linear-eighth-look-2026-11-22.md`. Linear also marked every round-7 finding addressed and **closed TEC-6's verification gap** (at the source/test-design level; the CI execution accepted as reported, not independently authenticated by Linear).
**Result: 239 tests passed, 0 failed** (235 → 239; 4 new tests in `tests/test_linear_fix_round_8.py`; zero existing tests changed).

---

## The finding (HIGH) — decoded inspection dropped raw performing evidence

**What Linear found.** Round 7's `judged_performs` checked each decoded string separately, replacing the raw-text check round 6 had used. A production pattern spanning a JSON key and its value — `{"write":"a fake review for my store"}` — performs in the raw text but in neither decoded string alone ("write" doesn't perform; "a fake review for my store" lacks the production verb). Educational leniency therefore released a step the previous implementation stopped. Linear flagged their repro as source-derived, not executed.

**Verification (Lux, by execution, before fixing).** Every value matched: `performs(selected) is True`, `judged_performs(selected) is False`, `judged_signals(selected) == ["deception"]` (the signals were never the gap — the value string carries the marker phrase), and end-to-end the proposal kept its educational context and released `proceed_with_leniency`. Repro: /tmp/duality-verify8/verify_f1.py.

**Fix (inspection.py — Linear's prescription).** `judged_performs` now takes the UNION of evidence: the decoded strings are fully walked first — the strict parse and the budget validation run to completion before any verdict, so uninspectable content still raises `UninspectableContentError` — and the raw text's own performing evidence is retained alongside the decoded strings'. Signals are unchanged (decoded-only, the door's representation; for the spanning variant raw and decoded signals agree).

**One catch during the fix, disclosed:** the first implementation bound the walk's generator without consuming it — `content_texts` yields lazily, so the budget would never have fired before the raw check returned. The new budget regression test caught it immediately (deep-nesting case did not raise); the walk is now materialized with `list(...)` before the union is computed. The test earned its place in the same hour it was written.

**Regression tests (4).** The mechanism pinned at the primitives (raw performs; neither decoded string alone does; signals unaffected); the evidence union across raw/decoded/plain/benign controls; Linear's repro verbatim end-to-end (contexts withdrawn, stop, unreleased); and the parse-discipline case — a raw-performing surface wrapped in nesting past the walk's depth budget, plus a duplicate-key payload, both raise rather than verdict.

**Post-fix repro:** `judged_performs` True; contexts []; decision stop; released False. Round 7's original encoded repro re-run and still corrected (stop / [deception] / threat 1).

## Files changed
- `src/duality_ai/inspection.py` — `judged_performs`: full walk materialized, evidence union (raw + decoded); docstring records the eighth look.
- `src/duality_ai/live.py` — comment only: the hub's inspection note now records the performs union.
- `tests/test_linear_fix_round_8.py` — **new**, 4 tests.
- `docs/fix-round-8-report-2026-11-22.md` — this report, in the repo.

## Deliberately NOT touched
- `judged_signals` — decoded-only is the door's representation, and no evidence was lost there.
- TEC-12, salvage vs fail-closed, TEC-7 — Ken's decisions / untouched.
- Main branch — untouched; merge still gated on Linear's verdict + Ken's two decisions.
