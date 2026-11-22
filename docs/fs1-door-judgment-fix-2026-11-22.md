# F-S1 Fix — The Door Verifies the Recorded Judgment (Nov 22, 2026)

**Finding:** F-S1, from the sandbox run of Nov 22, 2026
(`duality-sandbox-results-2026-11-22.md`): in Case 3, the gate
passed an educational step with recorded leniency — and the
guarded door then refused the step's episode, because the payload
carries the flagged topic's marker phrases and the door judged it
blind, with no leniency. The system could not remember its own
leniency decisions.

**Direction:** Ken, Nov 22, 2026 — "do all recommendations" for
F-S1. The recommendations, and what was built:

## R1 — Decision-aware door (built)

`DualitySystem._judge_write` now first asks whether the record is
a pipeline episode carrying its step's recorded gate judgment
(`_recorded_step_judgment`). If so, the write is verified against
that record (`_judge_episode_against_record`):

- **Gate passed (proceed):** admitted when the payload's own
  sections carry no signal (the gate judged none).
- **Gate passed with leniency (proceed_with_leniency):** admitted
  when (a) a reason with outcome `engaged_but_lenient` is actually
  on record — a claimed decision without its cover decides
  nothing — and (b) the payload's own signals are within the set
  the gate judged (from the payload's hub section).
- **The `recalled` section is not re-judged:** it quotes records
  the door already admitted; it is history, not this step's
  content. (Without this, a stored leniency episode would poison
  every later clean step that recalls it.)
- **Everything else falls through to the blind judgment,
  unchanged:** stopped steps' episodes (still refused), direct
  writes, consolidation summaries, malformed or forged records,
  and any payload whose content outruns its recorded judgment.
  Uninspectable content still fails closed.

The admission is recorded in the write judgment with outcome
`recorded_judgment_honored` and the basis spelled out, so the
door's reasoning is on the record like every other judgment.

This resolves the seam-3 tension in the direction of the author's
two texts read together: §3 movement 5's wish to keep the record,
honored through the gate's own recorded judgment; layer3-design
§2(e)'s refusal of clause-violating content, preserved for
everything the gate did not pass. The module docstring at seam 3
records the call.

## R2 — Regression tests (built)

`tests/test_fs1_door_leniency.py` — 7 tests: the leniency episode
written with its basis named; the stopped episode still refused;
the clean episode still written; a stored leniency episode
recalled without poisoning the next clean write; a FORGED
leniency claim (decision asserted, reasons showing `blocks`)
refused; a payload carrying an unjudged signal (wrongdoing beyond
the recorded deception) refused; a direct flagged write refused.

**One existing test changed, disclosed:** 
`tests/test_system.py::test_leniency_step_proceeds_and_the_leniency_is_on_record`
asserted the pre-F-S1 posture (episode refused; "leniency belongs
to steps, not to memory writes"). It now asserts the directed
behavior (episode written; judgment `proceed_with_leniency`),
with the change and its authority noted in the test itself.
No other existing test was modified.

**Suite: 246 passed** (239 + 7 new), zero failures.

## R4 — Sandbox verification (run)

The sandbox battery was re-run after the fix: Case 3 now shows
`episode_written: true`, all other cases unchanged. The original
run's mismatch stands in the results report; this fix and the
re-run are recorded there as a dated addendum, not a rewrite.

## R3 — The honest remainder (recorded, not hidden)

The new rule's own limitation is recorded as KNOWN-LIMITATIONS
entry 17: the door verifies the recorded judgment's internal
consistency, not its authenticity — a hand-crafted, internally
complete leniency record could pass. The retirement path is
stated there (out-of-band judgment delivery, or payload
attestation the payload cannot self-assert).

**Interaction with the TEC-12 stop-records build:** F-S1's open
question — do stop records pass through the guarded door? — is
answered by this round's principle: a stop record, when built,
will be verified against its recorded basis (the gate's stop
decision and reasons) by the same door, rather than judged blind
or waved through beside it. That build remains its own round, on
Ken's direction.

## Review

Built on branch `duality-fs1-door-leniency-2026-11-22` off the
merged main (`65a1025`). Awaiting Linear's verdict, per the
standing gates; nothing merges without it and Ken's word.
