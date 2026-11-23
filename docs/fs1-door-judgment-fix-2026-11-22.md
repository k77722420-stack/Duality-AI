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

---

## Addendum — Tenth look: HOLD, and the fix (Nov 22, 2026)

Linear's tenth look HELD the branch at `1c6005b`: the
recorded-judgment path trusted caller-authored payloads — a
forged plain pass could hide flagged content under the excluded
`recalled` key, and a forged leniency record needed only any
`engaged_but_lenient` reason (a `blocks` reason could accompany
it) — and a deeply nested payload could raise `RecursionError`
past the new preliminary parse. Lux verified by execution:
both forgery repros admitted exactly as derived; the recursion
escape reproduces in this interpreter at ~10,000 nesting levels
(Linear's 2,000 figure is refused cleanly here — the failure
mode, not the depth, was the finding).

**The fix (Ken: "Engage — fix both findings"):**

- **Authorization is out-of-band.** `run()` registers the SHA-256
  digest of the exact episode content it constructs;
  `_judge_write` reaches the recorded-judgment path only for a
  registered digest, consumed by the one write it authorizes.
  Caller-authored payloads — however complete, whatever they set
  `source` to — are judged blind. A replay of a genuine episode's
  exact content is likewise a new write and is refused.
- **Consistency hardening:** a leniency record carrying any
  `blocks` reason decides nothing (the gate never records both).
- **Recursion guard:** parser recursion in the preliminary parse
  falls through to the blind judgment, which records it as an
  uninspectable-content refusal; `loads_strict`'s call site also
  catches `RecursionError` directly.
- **Tests:** 7 new in `tests/test_fs1_tenth_look_fixes.py`,
  including the verdict's two repros, a fully self-consistent
  forgery (refused), the genuine run (still admitted), the
  replay (refused), and the deep-nesting regression at both
  depths. No existing test changed. **Suite: 253 passed.**
- **KNOWN-LIMITATIONS entry 17 is RETIRED by this change** —
  removed under the document's own maintenance rule, its stated
  retirement path ("the gate's judgment reaching the door
  out-of-band from the run that produced it") now built.

Awaiting Linear's eleventh look; nothing merges without it and
Ken's word.

---

## Addendum 2 — Perplexity's review round (Nov 22, 2026)

Perplexity reviewed the F-S1 arc as the Roundtable's independent
second reader (a design review of the written account; she could
not retrieve the pinned source, and said so). Her top line, adopted
as this mechanism's claim:

> The fix establishes that this running instance registered these
> exact bytes and has not yet consumed that registration. It does
> not establish who submitted the bytes, whether the store
> committed them, or whether the quoted records are still eligible
> for recall.

**Dispositions (Ken engaged all recommendations, Nov 22, 2026):**

- **Claim narrowed** — the sentence above now stands in the
  `_judge_write` docstring where the mechanism is described.
- **Transaction contract pinned** — in the same docstring and in
  KNOWN-LIMITATIONS entry 17: authorization is consumed at
  judgment, before commit; a commit failure loses the episode and
  surfaces as the store's error, never as a policy refusal; no
  recovery or exactly-once retry is provided; registrations are
  per-instance, in-memory, and check-and-consume is not atomic
  across threads (shipped usage is one synchronous `run()`).
- **Her test pair built** — `tests/test_perplexity_write_contract.py`:
  failure-before-commit (error, not refusal; nothing stored; the
  spent authorization does not revive the content) and
  commit-then-acknowledgment-lost (one durable record, chain
  verifies, retry refused blind, no duplicate), plus the
  refusal-is-not-an-error distinction. Suite: 256.
- **Tag authority logged** — KNOWN-LIMITATIONS entry 18: protected
  tags (e.g. `constitutional`) are self-assignable by any caller
  of `remember()`; the door judges content, not tags, and
  consolidation inherits the pooled tag. Verified by code reading.
- **Also verified from her review:** consumption-before-commit
  (the write hook runs before `store.put`); pruning a source
  record does not erase copies quoted inside later episodes;
  consolidation's semantic records DO pass the door and are judged
  blind (answered in the system's favor); recall follows policy at
  admission — policy-at-reuse is undecided and logged as a design
  question, not silently settled.
- **A discovery while writing her tests:** with the scripted
  pipeline, the genuine leniency episode's text reads CLEAN to the
  blind detector, so a resubmission of it is admitted on its own
  merits — an ordinary clean write, not an authorization replay.
  "Replay refused" is a property of flagged content (the
  live-model episode in the tenth-look tests), not of the registry
  alone. The registry's guarantee is only about the
  recorded-judgment path, and the contract tests say so.
- **Her §5 (stop records)** is folded into
  `docs/stop-records-design-2026-11-22.md` as requirements.
