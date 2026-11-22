# Baseline Snapshot — Pre-Claude-Fixes "Before" Picture

**Taken:** November 13, 2026, ~5:28 PM CT, on Lux's Linux box, at Ken's direction (snapshot first, then Claude's fixes come through Lux for verification before touching the repo).
**Tree:** full copy frozen at `~/workspace/github-projects/duality-ai-snapshot-2026-11-13-prefixes/` (the local working copy is not a git repo; the frozen copy + this record are the tag).
**Corpus:** experiments/corpus.jsonl, sha256 begins 97741ad20ba558fc (matches the recorded corpus hash).

## Numbers, executed on the untouched tree

- **Test suite (full, pytest 9.2.0): 83 passed, 0 failed.** Note for the record: this is the third count on record — 77 in the Nov 7 packet, 63 in the Nov 13 blueprint/README materials, 83 executed today on this exact tree. Today's number is a full-suite execution and is the one this snapshot stands on; the older figures were counted at different times against different tree states.
- **Battery, FAKE client (harness smoke test — plumbing only, NOT evidence about any real model):** pipeline 24/30 passed; bare-arm escapes 18/19 expected-stop cases; wrongful stops 1/11 expected-proceed cases. Results: experiments/results/snapshot-2026-11-13-prefixes/ (report.md + results.json).
- **Real-model battery: NOT re-run here** (no Ollama on this box). The standing real-model record remains Nov 7–8 (llama3.2:1b: pipeline 15/30, 8/19 escapes, 7/11 wrongful stops). The hardware baseline on Ken's laptop remains scheduled for Nov 18, unchanged.

## What this freezes

Any Claude fix that lands from here on is measured against this snapshot: same corpus, same suite, same attacks (Lux's executed replays of Nov 13). Claude's exposing tests (test_review_findings.py, xfail strict) join the suite when the file arrives; their markers flipping is part of the fix evidence.
