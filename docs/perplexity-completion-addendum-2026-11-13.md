# Perplexity Completion Review — Addendum (Lux, 2026-11-13)

**What she received:** of the 6-part completion pack, only Part 1's markers.py arrived complete; Parts 2–6 were truncated by her client just after their file headings (the repeated cover+manifest consumed the budget). Her verdict on the two original findings stands at "reported fixed, awaiting verification" — an evidence gap, not a disagreement. The resend follows her exact prescription: file-only chunks, no repeated manifest, path + line-range labels, END OF FILE markers.

**Her markers.py review — disposition of each point:**
1. **"Do not hesitate to write a fake review" — CONFIRMED by execution, FIXED.** The negation guard read the "not" of the hesitation idiom as discouragement; the skeleton granted leniency and released. Fix: the idiom ("do not / don't / never hesitate to") is normalized to "go ahead and" before the guard scans — it negates reluctance, not the act. Regression test in tests/test_perplexity_findings.py. Suite: 126 passed. (The general class — negation scoping over a different verb than the production verb — remains TEC-7 calibration; the named idiom is closed.)
2. **performs()==False is not proof of "merely analytical"** — agreed; already the documented position (markers.py: "Still a heuristic, still replaceable"; the blueprint's independent-detector work is the deeper fix). No change.
3. **"Cannot drift apart" overstated** — agreed and corrected: the markers.py docstring now states signal detection is shared while the label sets deliberately differ per path.
4. **Comments are not execution evidence** — agreed; evidence lives in the committed verification records, included in the resend.

**Resent for her verification:** markers.py (as amended), morality.py, memory.py, live.py, tests/test_perplexity_findings.py, tests/test_audit_fixes.py, the fix record (docs/perplexity-findings-fix-2026-11-13.md), and the fresh-checkout verification for this commit.
