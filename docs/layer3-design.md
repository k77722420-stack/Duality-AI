# Layer Three — The Memory Cloud

## Layer Three design draft — v0.1. Ken's build decision (Nov 7, 2026): HYBRID — foundation authored, edges boxed. Ideas marked PROPOSED await Ken's compare decisions.

**Concept:** Kenneth Lee Blum Jr · **Drafted by:** Lux, at Ken's direction
**Date:** November 7, 2026
**Status:** Working draft. Nothing in this document enters the thesis
until Ken has compared it, decided the open questions in Section 5,
and approved the joint final version. The foundation code described in
Section 6 is built and published as a structural skeleton — it
demonstrates the architecture's bookkeeping, not a working memory.

---

## 1. Premise

Layer One thinks. Layer Two protects. Layer Three remembers.

The Duality AI, as designed through its first two layers, has no past.
The pipeline reasons, the hub weighs, the gate judges, the barrier
watches — and then the step is gone. A system that cannot remember what
it has done cannot learn from its own history, cannot recognize a
threat it has already met, and cannot show its work over time. Ken's
direction for the third layer (Part 10) is "a cloud structure like a
memory": the system's long-term memory, given the same layered
treatment as everything else in the design.

"Cloud" is stated here as **design intent**, the way the hemispheres
are the design's premise: the memory is meant to be *distributed* (not
one box in one machine), *tiered* (hot working memory through cold
sealed archive), and *synced* (the copies agree, and can prove they
agree). This draft specifies the memory's model, laws, and contracts —
the foundation any cloud deployment would have to honor. It does not
specify, and the skeleton does not implement, an actual distributed
system: no nodes, no network, no consensus protocol. As with the rest
of the Duality AI, this is a theoretical design study and a structural
demonstration, not production software and not a neuroscience or
engineering claim. The brain parallel is the source of the ideas, not
evidence for them.

The build decision is the author's, recorded in Part 10:
**HYBRID** — *we construct the foundation ourselves and lay out the
code and the architecture; the replaceable edges are boxed as plug-in
slots others can add to when they want.* Section 3 is the map of which
is which.

---

## 2. The architecture

Each element below is marked **PROPOSED**: all eight come from the idea
list Lux presented at Ken's request (Part 10), and none has yet been
individually picked by Ken. They enter the final design only through
his compare decisions (Section 5).

### (a) Two memories — episodic and semantic — PROPOSED

Memory is kept in two kinds, after the distinction cognitive science
draws in people. **Episodic** records are *what happened*: a step the
pipeline ran, a judgment the gate made, an attack the barrier
detained — events, in order, with their context. **Semantic** records
are *what is known*: distilled facts, patterns, and lessons that no
longer belong to one event. The two kinds have different lives:
episodes accumulate; knowledge is what episodes settle into. Every
record is one kind or the other, and the kind is part of its schema —
not a tag a caller can forget to set.

### (b) Consolidation — the system's sleep — PROPOSED

Left alone, episodes would pile up forever and knowledge would never
form. So the design gives memory a periodic **consolidation pass** —
framed, deliberately, as the system's sleep: while no new steps are
being taken, episodes that cluster together (in the skeleton: sharing
a tag, at or above a policy-set count) are distilled into a single
semantic record, and the episodes are marked as consolidated so no
episode is distilled twice. The policy — what counts as a cluster, how
large it must be — is data (`config/memory_policy.json`), revisable
without touching code. **Honest limit:** real distillation is
summarization, and summarization is a model's work. The skeleton's
distillation is a placeholder counting summary, labeled as such in the
code; a real summarizer is a boxed edge (Section 3), not part of the
authored core.

### (c) Immune memory — the barrier remembers its attackers — PROPOSED

The barrier (Layer Two) observes and records an attack's capabilities
while the attack performs in the sandbox (Part 6). Those capability
records live here, on the barrier's own shelf of the memory. The
design's claim: a threat the barrier has met before is **recognized on
return** — matched against the recorded capabilities — the way an
immune system remembers a pathogen it has already answered. This is
the layer where the design's immune metaphor stops being only a
metaphor for response and becomes one for *retention*: response is
Layer Two's; the remembering that makes the second response faster is
Layer Three's. Recognition matching is a boxed edge (Section 3); the
core contributes the shelf, the schema, and the provenance of every
capability record.

### (d) Per-hemisphere shelves — PROPOSED

Nothing in this design is single-sided, and memory is no exception.
Records carry an **owner**: the *logical* shelf (procedures, proofs,
worked derivations), the *creative* shelf (stories, associations,
framings), the *shared* shelf (what belongs to the system as a whole),
and the *barrier's* shelf (Section 2(c)). The hub, which weighs the
hemispheres' answers, also weighs their memories: a recall can be
drawn per shelf, so the logical side's precedent and the creative
side's precedent arrive at the merger as distinguishable contributions
rather than one blended pile. Open question (Section 5): separate
stores per shelf, or one store with the owner as a field — the
skeleton takes the field, because it keeps one chain and one policy;
the question is Ken's to settle.

### (e) Guarded writes — nothing is remembered unjudged — PROPOSED

The architecture's rule is that no step proceeds unjudged, and a
memory write is a step. In the full design, every write passes the
barrier's inspection and the morality gate's judgment before it is
remembered: a memory the system should not keep — planted, poisoned,
or clause-violating — is refused at the door, because a false memory
is worse than a missing one. **In the skeleton** this is a
`write_hook` extension point, honestly labeled: a registered hook sees
each record before it is stored and may refuse it. The hook is where
the gate will stand; the skeleton does not pretend the gate is
standing there yet.

### (f) Provenance — every memory can show its papers — PROPOSED

Every record carries its **source** (what wrote it), its **stage**
(where in the system it came from), and its **timestamp**, and is
linked into a **hash chain**: each record's hash covers the previous
record's hash plus its own contents, in insertion order, from a
genesis link (`DUALITY-MEMORY-START`). The consequence the design
wants: any belief the system holds can be traced — *which step wrote
this, when, out of what* — and edits made to stored records outside
the system's own operations break the chain and are detectable
(`verify_chain()`).

**Honest limit, stated in the code as well:** consolidation and
pruning are system acts that change stored records, and after either
one the chain is re-sealed over what survives. The chain therefore
attests to what the store *now* holds, in order, and catches outside
edits — it is a structural demonstration of provenance, not a forensic
log that survives an adversary holding write access to the store
itself. And forgetting (Section 2(g)) deliberately wins over total
recall: a forgotten record is gone, link and all. Provenance governs
what is kept; it does not resurrect what the design chose to forget.

### (g) Graceful forgetting — with one exemption — PROPOSED

A memory that keeps everything forever is a hoard, not a mind. In this
design a record's **strength decays with a half-life** (policy:
30 days in the draft). Recall ranks by *current* strength, so what is
old and unreinforced sinks. When a record's strength falls below the
prune threshold (policy: 0.05), it is **forgotten** — removed, chain
re-sealed over the survivors. The exemption is absolute and is the
author's law carried down from Layer One: records carrying a
**protected tag** are never pruned, however faint they become. In the
draft policy the protected tag is `constitutional` — the morality
clauses ride under it. The system may forget what happened last
spring; it may not forget what it holds to be right. Forgetting is a
policy, set in data, arguable in the open — which tags are protected
is exactly the kind of decision the clause-library pattern exists to
make visible.

### (h) Tiers — hot, warm, cold — PROPOSED; sync is a FUTURE phase

A cloud memory is tiered by temperature. **Hot** memory is the working
set — small, fast, always at hand. **Warm** memory is the recent past,
kept close. **Cold** memory is the sealed archive: consolidated,
rarely opened, kept for provenance. In the skeleton, tier is a
*placement property* the design reserves — a function of a record's
kind, age, and strength (fresh episodes run hot; consolidated
semantics cool; pruned records are gone rather than frozen). The
skeleton stores everything in one place and implements no tiering;
it marks the property so the model reserves room for it.

**Node sync — marked plainly as a FUTURE phase, not in the
skeleton:** when the memory is one day actually distributed, its
nodes will agree on the chain head before they trust each other's
records, and the handshake for that agreement is the design's own —
the hat-tile handshake of Layer Two (Part 3), two-handed in the
Mirror Twin form (Part 4): a node accepts a sync only where the two
derivations interlock. None of that is built here. The foundation's
job is narrower: one store, one chain, laws that a distributed
version would have to preserve.

---

## 3. Core vs boxed-edge map

The hybrid decision (Part 10) made concrete. The **authored core** is
what we construct ourselves: it defines what Layer Three *is*, and it
does not change when a contributor arrives. The **boxed edges** are
plug-in slots: an interface, a contract, and room for others to build.

| Part | Core or edge | Contract / content |
|---|---|---|
| Memory model + record schema (kind, owner, source, stage, tags, strength, chain links) | **Authored core** | `MemoryRecord` in `src/duality_ai/memory.py`; the schema every backend and strategy must honor. |
| Provenance hash chain (genesis, linking, verification, re-sealing) | **Authored core** | `MemoryCloud.verify_chain()` / `head_hash()`; the order is insertion order, defined by the store contract. |
| Consolidation policy (cluster rule, minimum size, mark-once) | **Authored core** | `MemoryCloud.consolidate()`; thresholds from `config/memory_policy.json`. |
| Decay law (half-life, prune threshold, protected tags) | **Authored core** | `MemoryCloud.decay_and_prune()`; numbers from the same policy file — data, not code. |
| Store interface | **Authored core** | `MemoryStore`: `put` / `get` / `all` (insertion order) / `find` / `remove`. The contract itself is core; implementations are edges. |
| Reference backend (`JsonFileStore`; `InMemoryStore` for tests) | **Authored core** | One JSON file, atomically rewritten; the backend every other backend is compared against. |
| Policy file (`config/memory_policy.json`) | **Authored core** | The memory laws in force, as data: readable, debatable, revisable without a code change. |
| Alternative storage backends | **Boxed edge** | Implement `MemoryStore` (five methods, insertion order preserved); pass the round-trip and chain tests against your backend. |
| Recall ranking strategies | **Boxed edge** | Given the candidate records and the query, return them ranked; the core's default ranks by decayed strength — beat it or specialize it without changing the schema. |
| Embedding / index providers | **Boxed edge** | Given record content, return vectors or index keys, and given a query return candidate record ids; the core never sees your model, only ids and scores. |
| Real summarization for consolidation | **Boxed edge** | Given a cluster of episode records, return the semantic record's content; the core decides *when* a cluster is ripe and *where* the distillation lives — you decide what it says. |
| Sync transports (future phase) | **Boxed edge** | Carry chain heads and records between nodes and report agreement; the handshake and the acceptance rule stay core design (Layer Two, Parts 3–4). |

---

## 4. The layered-product note

Ken's rationale for the hybrid, in his words (Part 10): *"I believe
that's more of a profitable margin and a layered system to set up if
anybody were to sell this software."* The structure follows the
reasoning. A layered system sells in layers: the **core is the owned
asset** — the model, the laws, the contracts, the reference
implementation — authored once, held by the author, and the thing
every other piece depends on. The **boxed edges invite an ecosystem**:
contributors and customers build backends, rankers, and indexers
against stable contracts, and every edge anyone builds makes the core
more useful without diluting who owns it. The margins in such a system
live in the core and in the services around it — hosting, support,
integration, and future layers — not in re-selling the replaceable
parts, which competition drives toward free.

One honest sentence, because this project's rule is that the record
says what is true: the published repo is MIT, so the design itself is
free to use; sellable value in open-core models is the hosted service,
support, and any future layers the author keeps proprietary.

---

## 5. Open questions for Ken

For the compare session — Ken decides; Lux records and revises.

1. **Keep or cut, each of the eight ideas** (Section 2): (a) episodic /
   semantic split — (b) consolidation-as-sleep — (c) immune memory —
   (d) per-hemisphere shelves — (e) guarded writes — (f) provenance
   chain — (g) graceful forgetting with protected tags — (h) tiers.
2. **The decay half-life.** The draft policy uses 30 days. Faster
   forgetting (7 days) makes the memory nimble and lossy; slower
   (90 days) makes it retentive and heavy. Which temperament?
3. **Episodes: verbatim or summarized at write time?** The skeleton
   stores episode content exactly as written. Verbatim is honest and
   auditable but grows without bound; summarizing on the way in is
   compact but lets a summarizer decide what the past was. (The
   consolidation pass already summarizes later, either way.)
4. **The shelves: separate stores, or one store with an owner
   field?** The skeleton uses one store + owner field (one chain, one
   policy). Separate stores would give each hemisphere a memory it
   literally cannot read across — stronger separation, weaker hub.
5. **Sync: in scope now, or a later phase?** The draft marks node sync
   via hat-tile handshakes as a future phase (Section 2(h)). Pulling
   it forward means designing nodes, chain-head agreement, and
   conflict rules now; leaving it means the foundation hardens first.
6. **The protected list.** The draft protects only `constitutional`.
   Should barrier capability records (immune memory) be protected too —
   never forgotten, however old — or should even they be allowed to
   fade once a threat is extinct?

---

## 6. Code status

**Built** (`src/duality_ai/memory.py`, `config/memory_policy.json`,
`tests/test_memory.py`; full suite green):

- `MemoryRecord` — the schema of Section 3, with its canonical form
  and hash.
- `MemoryStore` — the boxed-edge contract (abstract), with two
  implementations shipped: `InMemoryStore` and the authored reference
  backend `JsonFileStore` (atomic whole-file saves; persists across
  instances; the chain verifies end to end across a reload).
- `MemoryCloud` — the authored core facade:
  - `remember()` — chained writes, with the `write_hook` guarded-write
    extension point (a refusing hook blocks the write);
  - `recall()` — filtered retrieval (kind / owner / tag / text),
    ranked by current decayed strength, computed on copies — recall
    never mutates the store;
  - `verify_chain()` / `head_hash()` — the provenance chain
    (Section 2(f)), including re-sealing after system acts;
  - `consolidate()` — the consolidation policy with the placeholder
    counting distillation, honestly labeled (Section 2(b));
  - `decay_and_prune()` — the decay law with the protected-tag
    exemption (Section 2(g)).
- Tests: round-trip, filtering, and consolidation against **both**
  stores (parametrized); chain linking and tamper detection; decay
  arithmetic at ten half-lives; pruning with the constitutional
  exemption; consolidation ripeness and mark-once; hook refusal;
  kind/owner validation; JSON persistence across instances; policy
  loading from the JSON file by default.

**Marked as extension points, not built:** the morality gate standing
in the write hook (2(e)); real summarization (boxed edge); embedding /
semantic recall (boxed edge — skeleton recall is substring and
filters); tier placement (2(h) — reserved as a property, no tiering
implemented); node sync and hat-tile handshakes (future phase);
recognition matching for immune memory (boxed edge — the barrier's
shelf and schema are built, the matcher is not).
