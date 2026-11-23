# Tag authority (KL-18) — build report (Nov 22, 2026)

**The hole** (Perplexity's finding, KL-18): `remember()`
accepted tags from any caller with no authority check. Tags
are not all labels — a policy protected tag (`constitutional`)
makes a record unprunable and sizes the barrier; the
`consolidated` mark makes consolidation skip a record; a
`gate:` tag is the system's own decision claim and steers
consolidation's bookkeeping order. And consolidation carried
a caller-chosen tag into its semantic record, so a forged
assignment propagated into derived knowledge.

**The fix, at her placement verdict** — the authoritative
check at the common write/mutation boundary, covering
initial assignment and propagation, keyed on a trusted
caller capability rather than a caller-supplied claim:

- **Reserved set** (mechanism-derived, not hard-coded
  policy): the cloud's policy `protected_tags`, the
  `consolidated` mark, and the `gate:` prefix.
- **Capability:** `MemoryCloud` creates a tag-authority
  token at construction; `claim_tag_authority()` hands it
  to one claimant (a second claim raises, mirroring the
  write hook's claim). `remember(_authority=...)` refuses
  the whole write — None, offending tags surfaced on
  `last_tag_refusals` — when a reserved tag arrives without
  the cloud's token. The check sits ahead of the door: the
  door judges content and cannot see who is claiming what.
- **The system** claims the capability at construction and
  presents it on its episode writes (the `gate:` tags).
  Its claim grants other callers of the same cloud nothing.
- **Consolidation:** a reserved cluster tag never
  propagates — that cluster's distillation is skipped and
  the refusal surfaced, rather than the derived record
  inheriting authority its clustering never earned.
- **Deliberately not reserved:** `stop-record` (the stop
  kind carries that authority; the tag moves no mechanism)
  and every ordinary label, including `consolidation` and
  `pipeline-run`.

**Bounds** (also in KL-18): in-process discipline, the
same bound as the write hook's claim; store-level imports
bypass remember() as they bypass the door; no re-tag API
exists (copies cross the boundary), so mutation is
in-process object access only.

**Tests:** tests/test_tag_authority.py — 11 tests (refusal,
wholesale refusal on a mixed call, claim-and-protect, second
claim, wrong token, ordinary tags free, the reserved set
following policy, the system's episodes carrying gate tags,
the system's claim granting others nothing, consolidation
propagation refused, ordinary consolidation intact).
**Three existing fixtures updated, disclosed:** the prune
test in test_memory.py, the legacy-record seeding in
test_linear_fix_round.py, and examples/running_system_demo.py
— each seeds a reserved tag acting as curator/system and now
claims and presents the authority; no assertion changed.
Suite: 293 → 304.


## Verdict round (Nov 22, 2026) — Perplexity favorable

Perplexity's verdict was favorable for merging, subject to
Linear's review and Ken's approval, with one precise
acceptance check and one documentation point. The check —
lacking authority stops the write before content judgment
(the recording hook is never called, no record written,
the refusal names the reserved tag); having it lets the
write reach content judgment, which still decides (both
labels persisted when the hook admits) — PASSES as
specified and is adopted as the twelfth test in
tests/test_tag_authority.py. The documentation point is
recorded in KL-18: the claim establishes exclusive
possession, not claimant identity, and the bootstrap rule
is claim-during-trusted-setup, before the cloud is exposed
to other code. Suite on this branch: 305 → 306.

## Review round (Nov 22, 2026) — Linear's hold, fixed

Linear held d2352d8 on two correctness gaps; both of his
exact probes failed as predicted before the fix and pass
after, adopted as permanent tests:

1. Iterator tags were consumed by the authority check and
   materialized again for storage — an admitted record
   written with iterator tags silently lost its labels,
   authorized protection labels included. remember() now
   materializes the tags once and checks and persists the
   same list.
2. The system's stop writer presented no capability, so a
   deployment whose policy protects the "stop-record" tag
   refused its own stop writes — the decision stopped, the
   audit record was lost. The stop writer now presents the
   system's claimed tag authority; the stop-kind digest
   authorization and payload schema checks are unchanged.

Suite on this branch: 306 → 308.
