# Reuse-policy filter — build report (Nov 22, 2026)

**Decision:** `docs/policy-decisions-2026-11-22.md`, addendum
(Decision 3). Ken chose STRICTER than Perplexity's
recommendation: the quotation filter applies at structured
recall assembly as well as at model-input construction. The
archive is not a surface — stored records are never rewritten.

**Implementation** (`src/duality_ai/system.py`):
`_recall_precedent` computes the eligibility set once per run —
the ids the cloud itself serves as verified (`cloud.recall()`
unfiltered) — and `_filter_dead_quotations` drops, from each
served summary's episode payload, every embedded `recalled`
entry whose referenced id is outside that set (pruned, never
existed, or seal-failed; unverifiable is dropped, fail-closed).
Drops are surfaced on the run result as
`recall_quotation_drops`. Content with nothing dropped is
returned byte-identical. Because episode payloads are built
from this same assembled recall, the filter also governs what
future episodes embed.

**Tests** (`tests/test_reuse_policy_filter.py`, 3): post-prune
excerpt quotation dropped from served recall + drop surfaced +
stored B untouched; live quotation served (no over-blocking);
decision-only embed from a dead source dropped + stored
container untouched. No existing test changed. Suite 260.

**Probe re-run** (Perplexity's protocol, same script): control
True; boundary 1 (stored in B) True — unchanged, by design;
**boundary 2a (structured recall output) flipped True → False
under the policy**; boundaries 2b and 3 False, unchanged. The
difference between the two runs is the filter and nothing else:
same fixture, same selection, same pruning.

**Not built:** surface 2 (model-input construction) — seam 1
is not wired yet. Perplexity's two-case A/B test is recorded in
the decision as that wiring's acceptance gate.
