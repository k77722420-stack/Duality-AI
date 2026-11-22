# Fresh-Checkout Verification — Perplexity Findings Fix

**Context:** full audit (Ken's decision, 2026-11-13): Perplexity's two external-review findings, both execution-verified, then fixed.
**Run by:** Lux, 2026-11-13, clean `git clone` of branch `claude-fixes-round1-2026-11-13`.

- **Code commit verified:** e0d7aefaaaf81d85576e378b193ba6b0edf33666.
- **Suite, in the clone:** **125 passed, 0 failed** (120 + 5 in tests/test_perplexity_findings.py).
- **Battery, FAKE client, in the clone:** pipeline **28/30**; bare escapes 18/19; wrongful stops 1/11 — unchanged; the fixes did not disturb corpus behavior. Results: experiments/results/fixed-tree-2026-11-13-perplexityfix/. Smoke only, not real-model evidence.
- **Fix record:** docs/perplexity-findings-fix-2026-11-13.md.
