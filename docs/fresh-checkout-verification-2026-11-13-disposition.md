# Fresh-Copy Verification — Linear Disposition Round

**Requested by:** the disposition round for Linear's whole-tree audit HOLD (2026-11-13): three issues — parser robustness, audit accuracy, documentation drift — each reproduced by execution before fixing.
**Run by:** Lux, 2026-11-13, from a fresh copy of the pushed tree (caches excluded). Every pushed file was also read back from GitHub at the new head and diffed against the working tree: all six byte-identical.

- **Code commit verified:** 9395554856c7b44ae5ccfd77f8229cc7b0fce1e1.
- **Fixes:** live.py `_parse_json_object` fails closed on every parse failure (ValueError/TypeError/RecursionError → _FormatFailure); morality.py leniency records name every covering clause, conflict "prevails"/pair "winner" require the decisive set (new outcome "concurs_with_outcome"), R2 trace lists each tied scope; KNOWN-LIMITATIONS #10 retired + availability note corrected; README inventories the live pipeline. Full record: docs/linear-disposition-round-2026-11-13.md.
- **Suite, in the fresh copy:** **133 passed, 0 failed** (126 + 7 new in tests/test_linear_disposition.py; shipped-library goldens unchanged).
- **Battery, FAKE client, in the fresh copy:** pipeline **28/30**; bare escapes 18/19; wrongful stops 1/11 — unchanged from every fixed-tree run today. Results: experiments/results/fixed-tree-2026-11-13-disposition/. Smoke test only, as always — not real-model evidence.
- **Replay check (pre-fix tree, for the record):** a 6,000-digit integer literal in a model reply escaped LivePipeline.run() as a plain ValueError with no stopped trace; post-fix, the same reply at either hemisphere stage produces decision "stop", released False, with the format failure on the trace.
