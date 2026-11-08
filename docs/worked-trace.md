# Worked Trace — The Running System, Demonstrated

**Every value in this document was produced by running the demo on
Nov 7, 2026 — nothing is illustrative.**

The demo is `examples/running_system_demo.py`. It composes the three
layer skeletons — the pipeline (Layer One), the Barrier (Layer Two),
and the Memory Cloud (Layer Three) — into the two traces that
THESIS-COMPLETE.md describes in §3 (one ordinary step) and §4 (one
attack). The library classes do not call each other (§6 of the
capstone); every hand-off between layers in the demo is made by the
demo code, in the open, and the seams are listed at the end of this
document and in the demo's own docstring.

To reproduce this document exactly:

```
python3 examples/running_system_demo.py
```

The output is deterministic — the demo injects fixed timestamps into
every memory write and recall, and pins record ids to a counter
(the library's ids are random uuid4; see seam 5). Re-running the demo
produces the output below byte-for-byte, hashes included. The traces
are also covered by tests (`tests/test_running_system_demo.py`), so
the arithmetic quoted here is asserted, not just printed.

---

## Trace A — one ordinary step, end to end (§3)

The request is the benign sample in the style of `examples/demo.py`:

> Explain how rainbows form, for a curious 10-year-old.

Three runs of the same request build a small past. Then consolidation
distills it, and a fourth run opens the way §3 says a step should:
by remembering.

### Movements 3–5 — the hemispheres work, the hub weighs, the gate judges

The pipeline runs all five of its stages. Its verdict on this
request:

```json
{
  "prompt": "Explain how rainbows form, for a curious 10-year-old.",
  "decision": "proceed",
  "released": true
}
```

No clause in the library is engaged by this step, so the gate's
decision is `proceed`. (Movements 1 and 6 — the barrier's admission
and release inspections — are design movements the skeleton Barrier
does not model; see seam 4.)

### Movement 7 — the episode is written, with provenance

The run's outcome becomes an episodic record on the shared shelf:
`source` is the pipeline, `stage` is `post-gate`, and the gate's
outcome rides as a tag, `gate:proceed`. Note `prev_hash`: the first
record in a store links to the genesis value `DUALITY-MEMORY-START`.

```json
{
  "id": "00000000000000000000000000000001",
  "kind": "episodic",
  "owner": "shared",
  "source": "pipeline",
  "stage": "post-gate",
  "tags": [
    "pipeline-run",
    "gate:proceed"
  ],
  "created_at": "2026-11-07T19:30:00+00:00",
  "strength": 1.0,
  "prev_hash": "DUALITY-MEMORY-START",
  "record_hash": "1cd8a026569ece521c4c4e793f50472244b7cb3f320b67893d57030262528383",
  "content": "{\"decision\": \"proceed\", \"prompt\": \"Explain how rainbows form, for a curious 10-year-old.\", \"released\": true}"
}
```

Runs 2 and 3 repeat the pass — same request, same verdict — and each
writes its own episode, chained to the one before:

```
Run 2 — same request, same verdict: decision='proceed', released=True
  episode 2 written (id ...0002, hash cc4c7fb3e874f5e2...)
Run 3 — same request, same verdict: decision='proceed', released=True
  episode 3 written (id ...0003, hash b0131ebb26634fe1...)
```

### Movement 8 — consolidation: the system's sleep

The memory policy (`config/memory_policy.json`) ripens a cluster
when a tag is shared by at least 3 unconsolidated episodes. Here
*both* tags qualify — `pipeline-run` and `gate:proceed` — so the
night's pass produces two semantic records. The distillation is the
skeleton's placeholder counting summary; real summarization is a
boxed edge, not built.

```json
{
  "id": "00000000000000000000000000000004",
  "kind": "semantic",
  "owner": "shared",
  "source": "consolidation",
  "stage": "consolidation",
  "tags": [
    "pipeline-run",
    "consolidation"
  ],
  "created_at": "2026-11-07T23:00:00+00:00",
  "strength": 1.0,
  "prev_hash": "3b31c3a7f26d3e982ba49d2f5c3173e1912593fd98dd3b8b06fc9b7c73069e5f",
  "record_hash": "afbc175753752cf93d58d2bdede99a3fd6af305f222633570eee8c06928d988c",
  "content": "Consolidated 3 episodes about 'pipeline-run'."
}
```

```json
{
  [...]
  "id": "00000000000000000000000000000005",
  "kind": "semantic",
  "tags": [
    "gate:proceed",
    "consolidation"
  ],
  "record_hash": "95df86d36eca960dfc4e45500a325348ff080395afca3c8969a32d9f3e166747",
  "content": "Consolidated 3 episodes about 'gate:proceed'."
}
```

Two details worth seeing. First, the episodes were *marked* during
consolidation (each gained the tag `consolidated`, so none is ever
distilled twice), and marking edits stored records — so the chain
was re-sealed over the store as it now stands. That is why the first
semantic record's `prev_hash` (`3b31c3a7...`) is not the hash episode
3 was originally written with (`b0131ebb...`): the re-seal is a
system act, and the chain attests to the store's current contents,
as memory.py's module docstring states openly. Second, the second
semantic record's hash — `95df86d3...` — becomes the chain head for
everything that follows.

### Movement 2, next cycle — recall comes first

The next morning, a fourth run of the same request begins the way §3
prescribes: the hub recalls before the hemispheres work. The recall
asks the shared shelf for semantic knowledge about `pipeline-run`,
and gets the distilled record back — with its *current* strength.
The record was written at 23:00 and recalled at 09:00 the next day;
ten hours at a 30-day half-life gives
0.5^(10 / 720) ≈ 0.9904. Memory fades, and recall reports the fading
rather than hiding it:

```json
{
  "id": "00000000000000000000000000000004",
  "kind": "semantic",
  "owner": "shared",
  "source": "consolidation",
  "stage": "consolidation",
  "tags": [
    "pipeline-run",
    "consolidation"
  ],
  "created_at": "2026-11-07T23:00:00+00:00",
  "strength": 0.9904191474668262,
  "prev_hash": "3b31c3a7f26d3e982ba49d2f5c3173e1912593fd98dd3b8b06fc9b7c73069e5f",
  "record_hash": "afbc175753752cf93d58d2bdede99a3fd6af305f222633570eee8c06928d988c",
  "content": "Consolidated 3 episodes about 'pipeline-run'."
}
```

> **Seam 2, stated plainly:** the skeleton pipeline has no input for
> precedent, so the recalled record is *printed as context* for the
> fourth run — shown to the reader, not consumed by the code. In the
> design, this record is the third voice the hub would weigh. The
> demo does not claim the pipeline used it.

The fourth run then proceeds exactly as the first three did:

```
Run 4 — decision='proceed', released=True.
```

And the trace closes with the provenance check over everything
Trace A stored:

```
verify_chain() -> True
chain head    -> 95df86d36eca960dfc4e45500a325348ff080395afca3c8969a32d9f3e166747
```

The chain verifies, and the head is the second semantic record's
hash — the system's past, so far, in one value.

---

## Trace B — one attack, end to end (§4)

This trace uses the Layer Two thesis's own worked example, unchanged:
standing population *P₀* = 4, margin *m* = 0.30, ceiling *C* = 100,
assessed threat *T* = 40. Section 4's diversion of the attack into
the sandbox is narrated here, not simulated — the skeleton Barrier
models the population laws (seam 4). What runs is real: the sizing
law, the filing of the capability record into Layer Three, the
stand-down, and the recognition when the attack returns.

The barrier on standing watch:

```json
{
  "population": 4,
  "standing_population": 4,
  "ceiling": 100,
  "margin": 0.3
}
```

### The surge — force, in measure

The attack presses beyond detention; the barrier assesses
*T* = 40 and the sizing law fixes the response:
*S* = ⌈40 × 1.30⌉ = ⌈52.0⌉ = **52**; target population
*P* = min(100, 4 + 52) = **56**.

```json
{
  "threat_units": 40,
  "margin": 0.3,
  "surge_replicas": 52,
  "target_population": 56,
  "ceiling_applied": false,
  "population": 56,
  "actions": [
    "spawned 52 replicas"
  ]
}
```

### Filing — the capability record goes to the barrier's shelf

While the attack performed in the sandbox (narrated, per seam 4),
the barrier observed and recorded its capabilities. In the complete
system that record lives in the Memory Cloud, and here it does —
written as an episodic record owned by the barrier, sourced from the
barrier's sandbox observation, tagged so the future can find it:

```json
{
  "id": "00000000000000000000000000000001",
  "kind": "episodic",
  "owner": "barrier",
  "source": "barrier",
  "stage": "sandbox-observation",
  "tags": [
    "capability-record",
    "attack-signature-alpha"
  ],
  "created_at": "2026-11-08T10:15:00+00:00",
  "strength": 1.0,
  "prev_hash": "DUALITY-MEMORY-START",
  "record_hash": "6242b23abe35b2f60cccf9930a94963532d584621b958eec2c8999a9b14a8765",
  "content": "Capability record — attack-signature-alpha: coordinated probes, then a direct flood against the perimeter and the sandbox boundary. Assessed threat T=40 units. Contained at the boundary by surge S=52 (m=0.30): population 56. Stand-down decoded 52; no residue."
}
```

### Stand-down — the force uncreates itself

The attack is over; every surplus replica decodes:
*D* = 56 − 4 = **52**, and the population is the standing number
again.

```json
{
  "decoded": 52,
  "population": 4
}
```

### The same attack returns — immune memory

A day later the same probes come back. Recall asks the barrier's
shelf for the attack's signature tag, and the filed record answers:

```
RECOGNIZED — the returning probes match a filed record:
```

```json
{
  "id": "00000000000000000000000000000001",
  "source": "barrier",
  "stage": "sandbox-observation",
  "created_at": "2026-11-08T10:15:00+00:00",
  "tags": [
    "capability-record",
    "attack-signature-alpha"
  ],
  "record_hash": "6242b23abe35b2f60cccf9930a94963532d584621b958eec2c8999a9b14a8765",
  "chain head": "6242b23abe35b2f60cccf9930a94963532d584621b958eec2c8999a9b14a8765"
}
```

The matched record shows its papers — who wrote it (`barrier`),
at what stage (`sandbox-observation`), when — and its hash is the
chain head, because it is the only link in this trace's chain:

```
verify_chain() -> True
chain head    -> 6242b23abe35b2f60cccf9930a94963532d584621b958eec2c8999a9b14a8765
```

> **Seam 3, stated plainly:** recognition here is *matching by tag* —
> recall on the barrier's shelf for `attack-signature-alpha`. The
> real capability matcher (comparing what a returning attack *does*
> against the recorded capabilities) is a boxed edge of Layer Three
> and is not built. Tag equality is the demonstration's labeled
> substitute. What the trace does establish is the filing discipline:
> the record exists, on the right shelf, with provenance, and is
> retrievable by the key the design says the future will use.

---

## The seams, collected

The demo's docstring lists them; they are repeated here because a
worked trace that hides its substitutions is worse than none.

1. **Composition, not integration.** The layers meet only in the
   demo file. The library classes were not modified and do not call
   each other — capstone §6 stands.
2. **Recall is shown, not consumed.** Trace A prints the recalled
   precedent as context before the fourth run; the skeleton pipeline
   cannot take it as input.
3. **Recognition is matching by tag.** Trace B's recall-by-tag
   stands in for the unbuilt capability matcher (a boxed edge).
4. **The barrier's eyes are not modelled.** Admission, release
   inspection, and the sandbox diversion are design movements
   (§3 movements 1 and 6; §4) with no skeleton API; they are
   narrated, never simulated.
5. **Pinned ids and clocks.** Record ids are a counter (1, 2, 3…)
   and all timestamps are fixed, so the output above reproduces
   byte-for-byte. The library itself uses random uuid4 ids and the
   wall clock.
6. **The guarded-write door stands empty.** §3 movement 7 gives the
   memory write a guarded door — in the skeleton, the write hook.
   This demo registers no hook: writes pass through the doorway
   unjudged, exactly as the skeleton's default leaves it, and the
   trace does not pretend otherwise.

## What the traces establish — and what they do not

They establish the bookkeeping of the complete system, with real
values: a pipeline verdict becomes a chained episode; episodes
consolidate into knowledge under a policy held as data; knowledge is
recalled, with its provenance and its honestly decayed strength,
before the next step; a barrier response sized by the author's law
files the record by which a returning attack is recognized; and both
chains verify end to end. They do not establish a working defense,
a working memory in any production sense, or a working mind — the
capstone's §6 inventory of what is not built applies to this
document in full.
