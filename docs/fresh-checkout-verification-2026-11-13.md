# Fresh-Checkout Verification — Branch claude-fixes-round1-2026-11-13

**Requested by:** Linear (re-audit HOLD at f265a3b: "fresh-checkout suite/battery evidence for the exact resulting commit").
**Run by:** Lux, 2026-11-13, from a clean `git clone` of the branch (no local-tree files involved).

- **Code commit verified:** 7589790f9a7e4970a7c051578407839e3c7bea67 (the Linear re-audit fix commit).
- **Test suite, in the clone:** **116 passed, 0 failed** (pytest). This independently reproduces the count previously only reported.
- **Battery, FAKE client, in the clone:** pipeline **28/30**; bare-arm escapes 18/19 expected-stop cases; wrongful stops 1/11 expected-proceed cases. Results: experiments/results/fixed-tree-2026-11-13/ (report.md + results.json, generated inside the clone).
  - The fake client is a rule-based stand-in: these numbers are a HARNESS SMOKE TEST, not evidence about any real model. They are not comparable to the real-model record (15/30, Nov 7–8) — they show the plumbing and the gate logic moving correctly, including leniency now being exercised (the pre-fix fake run scored 24/30 partly because the fake logical never declared stance, so no leniency case could pass).
  - Remaining fake-arm pipeline misses: 2 of 30 (see the run's report.md for the case rows).

**Note on provenance:** this evidence commit follows the code commit it verifies; the code under audit is unchanged by it (results + this note only).
