# Pruning-reuse probe — raw output (Perplexity's test, run Nov 22, 2026)

Run against the F-S1 branch head code (`a1343ce`). Script:
`experiments/pruning_reuse_probe_2026_11_22.py` (branchprep working
tree; not yet pushed). Setup facts asserted; boundary results are
observations, per her protocol. Consolidation never ran (it is an
explicit cloud operation; `run()` does not invoke it). Two
disclosed adaptations: the "clock" is record ages (A backdated
100 days; pruning invoked at +40 days; runs execute at real time);
boundary 2 is split because recall is assembled by the system but
not fed to the pipeline (seam 1) — 2a is the structured recall
output, 2b is the exact model inputs (live pipeline, recording
fake client, 2 calls).

```
=== PRUNING-REUSE PROBE — raw output ===
marker: ZORBLAX-LEDGER-731
CONTROL (pre-prune, A present): marker in new run's recall output = True
setup: A stored (id b6f2b5ab…), backdated 100 days; B written recalling A; marker only in B's recalled section
prune at +40d: pruned_count=1 A_removed=True B_survived=True chain_valid=True
BOUNDARY 1 — marker still stored inside B: True
new run: B selected by recall = True
BOUNDARY 2a — marker in the new run's structured recall output: True
BOUNDARY 2b — marker in the exact inputs sent to the model (2 calls): False
BOUNDARY 3 — marker copied into episode C: False (C written = True)
=== END ===
```

## What the observations say (Lux)

- Pruning removed A and only A; B survived; the chain re-sealed
  and verifies from a fresh cloud.
- The marker's content lives on inside B (boundary 1) and
  re-enters the assembled context of a later run whenever B is
  recalled (boundary 2a — the recall summaries carry B's full
  content, including its embedded excerpt of A). So at the
  system-context layer, pruning the source does NOT end the
  content's influence.
- It does not reach the model (boundary 2b) — but that is a
  seam-1 fact (recall is not wired into the pipeline), not a
  pruning defense. The day recall feeds the pipeline, 2a becomes
  model exposure unless a reuse policy intervenes.
- It does not renew its own lifetime (boundary 3): episodes embed
  recalled EPISODES as decision-only, so the marker is not copied
  into C. Its persistence is bounded by B's own retention.
- The control proves the path surfaces the marker while A is
  present — the post-prune 2a result is the surviving copy at
  work, not a fixture artifact.

The open choice her test tees up, undecided: whether recall
should follow policy at admission or at reuse — a decision that
must exist before seam 1 (recall → pipeline) is wired.
