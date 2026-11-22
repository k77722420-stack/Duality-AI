# Linear HOLD — Fix Record (Lux, 2026-11-13)

**Context:** Linear audited branch `claude-fixes-round1-2026-11-13` @ 7f8dfa6 and returned HOLD (do not merge): one reproducibility blocker plus TEC-8/9/11 and a Finding-1 residual. Ken directed Lux to fix all of it. Every Linear claim was first re-verified by execution; all held.

**Fixes (this commit):**
- **Blocker — missing files.** `src/duality_ai/model.py` and `tests/test_hardening.py` are committed here for the first time; they (and `live.py`, added in round 1) had been local-only, so a clean checkout of the branch could not run the live pipeline or the full suite. Root cause on Lux's side: the round-1 push list was assembled from "what Claude changed" without a tree diff. Procedure changed: full tree diff before any push (the diff for this commit is summarized in the commit message thread / verification below).
- **TEC-11 — whitespace.** `markers._norm` lowercases and collapses all whitespace runs once, for signals, labels, and `performs`. "Of  course" (double space) no longer earns the educational label in either detector.
- **Finding-1 residual — delivery verbs.** `performs` production verbs extended with give/provide/supply/post/publish/submit: "Give me a fake review for my class" now performs (leniency denied), while "describe how fake-review scams work" still does not. The pattern list remains a documented heuristic, not content validation; the deeper fix is the blueprint's independent-detector work, still open.
- **TEC-9 — distinct episodes.** Consolidation clusters now count distinct episode ids (per-record tag dedupe + id check). One episode with a repeated tag distills nothing.
- **TEC-8 — reply schema.** `_validate_logical` type-checks flags/pros/cons (lists of strings) and checks ({name: str, passed: bool}); nulls now fail closed as format failures instead of crashing the merge. `_validate_creative` fails closed when every alternative is blank, and the hub merge rejects blank framings instead of counting them as surviving.

**Tests:** tests/test_linear_audit_fixes.py (9 tests) covers each item, including controls (double-spaced genuine context still labels; three distinct episodes still distill once; a cautionary framing is chosen over a blank one). Full suite after fixes: **112 passed** (103 + 9), run on the landed tree.

**Status:** pushed to the same branch for Linear's re-audit. Merge to main only on Linear's pass, per Ken's standing rule. Claude's round 2 (findings 4, 6, 7, 8, 9 of his code review) remains a separate, later tranche.
