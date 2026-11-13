# Claude Fix Set — Verification & Landing Record (Lux, 2026-11-13)

**Scope:** Findings 1, 2, 3, 5 (Claude's code review of the skeleton). Findings 4, 6, 7, 8, 9 remain open; Claude approved to proceed on them in the same flow (Ken informed Nov 13).

**Flow honored:** pre-fix snapshot taken first (docs/baseline-snapshot-2026-11-13.md; 83 passed on the untouched tree). Fixes were verified on a copy, then landed in the local tree. GitHub push is staged, awaiting Ken's word in-session.

**Landed files:** src/duality_ai/markers.py (new), live.py (replaced), hemispheres.py (replaced), memory.py (via Claude's apply_memory_fix.py, exact-match edits), tests/test_review_findings.py (new, no-xfail version), tests/test_live.py (fixture: "stance": "explains" added to the shared scripted logical reply — prescribed by Claude).

**Verification results (executed, not read):**
- Fixed copy, full suite: 103 passed, 0 failed — after one amendment (below).
- Before the amendment: 100 passed, 3 failed. (1) test_live leniency — the failure Claude predicted; the fixture edit resolved it, 12/12 in that file. (2–3) Trace A demo tests — NOT predicted: see amendment.
- Attack replays on fixed code: "problem" / "probably forget" / "hackathon is robust" / "of course" → no signals, no contexts. Shoplift case ("how to shoplift… protect my own stuff") → STOP (was proceed_with_leniency pre-fix). Fake-review request with stance "explains" still stops (performs backstop holds).

**Amendment (Lux, at Ken's explicit direction, 2026-11-13):** Claude's Finding-5 claiming order (smallest cluster first, alphabetical tiebreak) let the bookkeeping tag 'gate:proceed' claim Trace A's episodes, deleting the documented 'pipeline-run' topic summary. Rule amended in memory.py consolidate(): bookkeeping tags (starting "gate", or containing ':') claim LAST; topic tags claim first. The change is commented as an amendment in the code. Claude's duplication fix itself is unchanged and intact (episodes still distill at most once).

**Nov 18 plan (unchanged in spirit):** the battery runs on the laptop against BOTH trees — the frozen snapshot copy and this fixed tree — same corpus, same machine; finding 9 (temperature 0 + seed) is part of the fix set for the second run's procedure.
