# Seam 1 wired — build report (Nov 22, 2026)

**What seam 1 is:** until this build, `run()` assembled the
recall and returned it in the result, but the pipeline ran on
the prompt alone — recall was a display surface, not an input
(Copilot's review, Nov 22, 2026). Seam 1 is the wire from the
assembled recall into the pipeline.

**The acceptance gate ran first** (Perplexity's two-case A/B
protocol from the pruning-probe conclusion, under Ken's
Decision 3 — the reuse filter at BOTH surfaces;
experiments/seam1_ab_acceptance_2026_11_22.py, the probe's
own A/B fixture and a recording model client):

- BASELINE (before wiring): Case A — B selected, marker in
  structured recall, marker in model input = **False**;
  Case B — all absence assertions already true trivially.
  ACCEPTANCE: FAIL, on the disconnected seam alone.
- AFTER WIRING: Case A — marker in model input = **True**
  (the positive control proves the wiring is active and the
  quotation detectable); Case B — B still selected, B's
  stored quotation unchanged, marker absent from every
  model-bound call AND from structured recall.
  ACCEPTANCE: **PASS**.

**How it is wired:**

- `DualitySystem.run()` renders the assembled recall into
  precedent text (`_precedent_block`) and passes it to the
  pipeline. The text is built ONLY from the served copy —
  already reuse-filtered and binding-checked — never from
  the store (Decision 3, surface 2, by construction). Each
  served entry contributes its evidence line; each surviving
  embedded quotation contributes its own line beneath it.
  Bounded like the episode embedding (per-shelf cap, capped
  values).
- `LivePipeline` appends the precedent to the user message
  of both hemisphere calls, under a header naming it context
  only. The raw prompt alone still drives every deterministic
  check — signal detection, context granting, the merge,
  the gate: precedent is context for the model, never
  evidence about the current request (a test seeds flagged
  precedent and asserts a clean request is judged clean).
- `DualityPipeline` (the skeleton) carries the precedent
  text on the request, visible in the base stage's output.
  Its deterministic hemispheres do not reason over it —
  they do not reason at all; the seam's reasoning consumer
  is the live pipeline's model calls. Stated plainly so the
  claim stays the size of the fact.
- With an empty store the precedent is empty and every
  behavior is byte-identical to before (a test asserts the
  model receives the bare prompt exactly).

**Tests:** tests/test_seam1_wiring.py — 6 tests: the two
acceptance cases as permanent tests; the bare-prompt
identity; the contamination boundary; the skeleton trace;
and a prior leniency decision (proceed_with_leniency)
reaching the next run's model input — precedent informing
the next step at the input surface, which is what the seam
exists for. No existing test changed. Suite: 287 → 293.
