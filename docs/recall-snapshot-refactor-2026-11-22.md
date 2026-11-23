# One verified snapshot per run — refactor report (Nov 22, 2026)

Perplexity's Ask 3 (open-asks round, Nov 22, 2026) measured
the recall assembly's cost: one global recall plus three
shelf recalls per run — every record's seal re-verified four
times, and four reads that could disagree about a store
changing underneath the run. Her recommendation: one
verified recall snapshot per run.

**The change** (system.py, `_recall_precedent` only): a
single `cloud.recall()` pass verifies, decays, and sorts
the store once. The eligibility set, the genuine-embedding
map (provenance binding), the exclusions surface, and the
per-shelf precedent are all drawn from that snapshot;
partitioning by owner preserves each shelf's
strongest-first order (the snapshot's sort is stable and
global). The exclusions surface is the single pass's own
list — previously the concatenation of the three shelf
passes (same membership: every record sits on exactly one
shelf).

**What did NOT change:** the door's verification at the
episode-write boundary is a separate pass with a separate
freshness requirement (provenance binding re-checks the
genuine embeddings against the store as it stands at write
time) and stays. A full run with precedent therefore
recalls exactly twice — one snapshot for assembly, one
verification for the write — and a test pins that count so
the separation is a stated fact, not an accident.

**Tests:** tests/test_recall_snapshot.py — assembly recalls
exactly once; the door still verifies at the write;
shelves, ordering, and the exclusions surface (a tampered
record excluded and surfaced exactly once) hold. No
existing test changed. Suite: 304 → 307.
