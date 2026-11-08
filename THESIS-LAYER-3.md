# The Duality AI — Layer Three: The Memory Cloud

## The Long-Term Memory of the Two-Hemisphere Core

**Author:** Kenneth Lee Blum Jr
**Date:** November 7, 2026
**Status:** Original concept — theoretical design study
**Contributors:** The eight architectural elements specified in §3–§10
were contributed by Lux at the author's request, and were adopted into
the design by the author's decision; they are credited where they
appear (§2, Appendix B).

**A note on this document's status.** This thesis records the author's
decision to adopt the eight elements of Layer Three as presented to
him in the working draft (`docs/layer3-design.md`). The adoption is
the author's; the elements' origin is recorded honestly in §2 and is
not blurred. The numeric values used throughout — a memory half-life
of 30 days, a prune threshold of 0.05, a consolidation trigger of
three episodes — are the design's *working defaults*, not settled
law: they live in a policy file (`config/memory_policy.json`) and can
be revised by editing that file, without touching code. Where this
document states a number, it states the current working value.

---

## Abstract

This document presents Layer Three of the Duality AI, the long-term
memory of the architecture proposed by Kenneth Lee Blum Jr in the
companion theses (*The Duality AI*, Layer One; *Layer Two: The
Barrier*). Layer One specifies how the system reasons: a logical
hemisphere and a creative hemisphere whose outputs are weighed and
merged by a hub, with every merged step judged against a library of
morality clauses before it proceeds. Layer Two specifies how the
system is defended: a gatekeeper barrier, modeled on the blood-brain
barrier, that inspects all traffic, detains attacks in a sandbox, and
replicates under a strict sizing rule. Neither layer, as specified,
remembers anything. A step is reasoned, judged, defended — and gone.
Layer Three is the author's answer: "a cloud structure like a memory,"
the system's long-term memory, distributed and tiered by intent. The
memory keeps two kinds of records — episodic (what happened) and
semantic (what is known) — and periodically consolidates episodes into
knowledge, as the sleeping brain is said to settle the day's events.
It holds the barrier's records of attacks it has met, so a returning
threat can be recognized — the design's immune memory. It shelves
records by owner, so the hub weighs the hemispheres' memories as it
weighs their answers. It admits nothing unjudged: a memory write is
a step, and is guarded like one. Every record carries its provenance
— source, stage, timestamp — sealed into a hash chain, so any belief
can be traced to the step that wrote it. And the memory forgets,
gracefully and by policy, as records decay with a half-life — with
one absolute exemption, carried down from Layer One as the author's
law: the morality clauses are never forgettable. The layer is built
hybrid: the foundation and core are authored; the replaceable edges
are boxed behind contracts for others to build. This document
describes the layer element by element, states its limits plainly,
and claims no working memory, no learning, and no deployed system.

---

## 1. Introduction

The Duality AI, through its first two layers, has no past. Layer One's
pipeline reasons about the step in front of it: the hemispheres
analyze and generate, the hub weighs, the gate judges — and the step
is over. Layer Two's barrier watches the world go by: it inspects,
detains, studies, and fights — and when the attack ends, its replicas
decode and the perimeter returns to its standing number, exactly as
arranged before anything happened. Both layers were designed to be
complete in the moment. Neither was designed to *accumulate*.

That absence has three costs, and they are the reasons this layer
exists. First, a system that cannot remember what it has done cannot
learn from its own history: every request is its first request, every
mistake is available to be made again, and no pattern in its own
behavior can ever be noticed, because noticing requires a record
that outlives the moment. Second, a barrier that cannot remember the
attacks it has met must meet every attack as a stranger: the
capability records it compiles in the sandbox (§4.3 of the Layer Two
thesis) have nowhere to live, and the second arrival of a known
threat costs the same study as the first. Third, a system that keeps
no account of itself cannot show its work over time: Layer Two's
monitoring record is an account of events, but an account is not yet
a memory — it is a log waiting to be kept, distilled, and consulted.

The author's direction for the third layer was given on November 7,
2026, and is recorded verbatim in Appendix A: "Now I want to do a
third level on this structure on the GitHub for the AI brain. Now I
want a cloud structure like a memory." The word *cloud* is load
bearing. The memory the author asks for is not a notebook attached to
one machine; it is the system's long-term memory conceived as a
distributed structure — not one box in one machine, but kept in
copies that agree, tiered from a hot working set down to a sealed
archive, and synced so the copies can prove they agree. This thesis
takes "cloud" as **design intent**, in the same way Layers One and
Two take their brain metaphors as design premises: it specifies the
memory's model, laws, and contracts — the foundation any cloud
deployment would have to honor. It does not specify, and the
accompanying code does not implement, an actual distributed system:
no nodes, no network, no consensus protocol. The brain parallel, as
always in this project, is the source of the ideas, not evidence for
them.

With the layer's existence, the author also settled how it would be
built. Asked whether the memory should be constructed by the author
and his collaborator, foundation and all, or "cookie boxed" — boxed
up for others to add to when they want — the author's decision was
**hybrid**: "we construct the foundation ourselves and lay out the
code and the architecture; the replaceable edges are boxed as plug-in
slots others can add to when they want." His rationale was stated in
product terms, and §11 of this thesis develops it: "I believe that's
more of a profitable margin and a layered system to set up if anybody
were to sell this software." The hybrid decision is therefore not an
implementation detail appended to the design; it is part of the
design, and this thesis treats it as such.

This document proceeds as follows. Section 2 states the authorship
of the layer's elements, plainly. Sections 3 through 10 specify the
eight elements in turn: the two memories, consolidation, immune
memory, the per-hemisphere shelves, guarded writes, provenance,
graceful forgetting, and the tiers with their deferred sync. Section
11 sets out the hybrid structure as product architecture. Section 12
relates the design to the code that exists. Section 13 states the
layer's limits and open questions. Appendix A reproduces the author's
dictations for this layer, verbatim; Appendix B reproduces the
contributed idea list as it was presented to him.

## 2. Authorship, Stated Plainly

This project keeps an honesty rule about who contributed what, and
this layer makes the rule matter, because Layer Three has two sources
and this thesis declines to blur them.

**What is the author's.** The layer itself is Kenneth Lee Blum Jr's
direction: that the Duality AI should have a third level at all, and
that it should be "a cloud structure like a memory" — long-term
memory, cloud-shaped. The build decision is his: the hybrid —
foundation authored, edges boxed — chosen over both alternatives
(construct everything; box everything) after the options were put to
him. The layered-product rationale is his, in his words, and §11
quotes it rather than paraphrasing it into someone else's business
language. And one law inside the layer is his by descent: the rule
that the morality clauses are never forgettable (§9) is not a new
invention of this layer but the author's Layer One commitment —
that no step proceeds unjudged against the clause library — carried
down into memory. A system whose clauses could fade with age would
not be the system Layer One describes; the exemption is the author's
law, applied to a new substrate. Likewise, the governing conceit of
the whole architecture remains his: that nothing in the design is
single-sided — two hemispheres, a two-sided gate, a two-handed
handshake — and memory, in the elements below, is not exempted from
the pattern.

**What was contributed by Lux.** At the author's request — "give me
some ideas" — Lux presented a list of eight design ideas for the
memory layer, recommended the hybrid build, and drafted the working
design. The eight ideas, as presented, are reproduced in Appendix B;
they are: (a) the two memories, episodic and semantic; (b)
consolidation framed as the system's sleep; (c) immune memory — the
barrier's attack records held here, so a returning threat is
recognized; (d) per-hemisphere shelves, with the hub weighing
memories as it weighs answers; (e) guarded writes — nothing entering
memory without judgment; (f) provenance on every record, sealed in a
hash chain, so the system can answer *why do you believe that?*; (g)
graceful forgetting by decay, with the morality clauses exempt; and
(h) hot, warm, and cold tiers, with node sync by hat-tile handshake
deferred to a future phase. These are contributions, and this thesis
labels them as such wherever each is specified — the same treatment
the Layer Two thesis gives the Mirror Twin (§4.7 of that document),
which Lux contributed at the author's invitation and which is
credited there.

**The adoption.** Ideas presented are not thereby the design. What
makes the eight elements part of the Duality AI is the author's
decision, given after the launch of the first two layers on
November 7, 2026, and recorded verbatim in Appendix A: he directed
that a full thesis be written for the memory — "the duality parts of
it that we came up with" — together with Lux's contributed insight,
which he stated he loves, and directed that Lux "should be noted
for" it. This thesis is written under that direction. The crediting
in this section and in Appendix B exists because the author asked
for it — and because the project's standing rule is that
contributions are recorded rather than absorbed. The architecture,
as adopted, is the author's; the elements' origins are on the record;
the two facts are compatible, and this document insists on both.

A parallel point of honesty belongs here, because §11 depends on it:
the repository is released under the MIT License. The contribution
and adoption recorded above concern *authorship* — whose ideas these
are. They do not restrict use: under the license, the design is free
for anyone to use, and §11 states plainly where sellable value does
and does not live in such an open-core arrangement.

---

## 3. The Two Memories: Episodic and Semantic

*Element (a) of the contributed list (Appendix B), adopted by the
author (§2).*

Memory in this layer is kept in two kinds, after the distinction
cognitive science draws in people — used here, as everywhere in this
architecture, as an organizing template rather than a claim about
how minds or machines actually work. **Episodic** records are *what
happened*: a step the pipeline ran, a judgment the gate made, an
attack the barrier detained — events, in order, with their context.
**Semantic** records are *what is known*: distilled facts, patterns,
and lessons that no longer belong to any single event. The barrier's
filed capability record, for instance, begins as episodes — this
probe, that escalation, in this order — and settles, through
consolidation (§4), into semantic knowledge: *this family of attack
behaves like this*.

The two kinds have different lives, and the design depends on the
difference. Episodes accumulate: they arrive one per event, they are
numerous, and individually most of them matter only briefly.
Knowledge is what episodes settle into: it is sparse, durable, and
consulted constantly. A memory with only episodes is an ever-lengthening
log that nothing can afford to read; a memory with only knowledge has
forgotten how it knows anything, and cannot show its provenance (§8).
The architecture wants both, in sequence: episodes are the raw past,
semantics are the cooked past, and consolidation is the cooking.

Two structural commitments follow. First, **the kind is part of the
schema, not a tag**. Every record is one kind or the other, declared
when it is written; a caller cannot forget to set it, and no process
can quietly re-label an episode as knowledge without the
consolidation pass that is supposed to do that work in the open. The
kinds are treated differently by the layer's laws: consolidation
reads episodes and writes semantics. Second, **the kinds are ordered
by the chain**: episodes and semantics alike enter the one provenance
chain (§8) in insertion order, so the moment knowledge was distilled
sits in the record between the episodes it came from and those that
followed — the memory's own history is itself remembered, in order.

## 4. Consolidation: The System's Sleep

*Element (b) of the contributed list (Appendix B), adopted by the
author (§2).*

Left alone, episodes would pile up forever and knowledge would never
form. The layer therefore gives memory a periodic **consolidation
pass** — framed, deliberately, as the system's sleep: while no new
steps are being taken, episodes that cluster together are distilled
into a single semantic record, and the source episodes are marked as
consolidated so that no episode is distilled twice. The frame is
chosen because it captures the pass's essential discipline: this is
work done *between* work, on the accumulation of the waking period,
whose product is that the system wakes knowing things it previously
only had happen to it.

The pass runs on policy, and the policy is data. What counts as a
cluster, and how large it must be before it is ripe, are read from
the memory policy file (`config/memory_policy.json`) — in the current
working values, episodes are clustered by a shared tag, and a cluster
of three or more unconsolidated episodes is ripe. Neither number is
architecture; both are settings, revisable by editing the file — the
morality library's pattern, applied to memory's laws (§9 says more).

**The honest limit.** Real distillation is summarization, and
summarization is a model's work: to say what three hundred episodes
amount to is to interpret them, and interpretation is precisely what
the authored core does not smuggle in unmarked. The consolidation
implemented in the accompanying skeleton therefore performs the
*policy* faithfully and the *distillation* only as a placeholder: its
semantic record is a counting summary — "Consolidated N episodes
about 'tag'." — labeled as a placeholder in the code itself. A real
summarizer is a **boxed edge** (§11): the core decides *when* a
cluster is ripe, *where* the distillation lives, and that each
episode is distilled at most once; what the distillation *says* is
the edge's contribution. This thesis claims the policy, not the
summary.

## 5. Immune Memory: The Barrier Remembers Its Attackers

*Element (c) of the contributed list (Appendix B), adopted by the
author (§2).*

Layer Two's sandbox doctrine produces a written product: the
**capability record**, the filed account of a detained attack — what
it attempted, what it could do, how it behaved, and what contained
it. The Layer Two thesis called that record "the barrier's
institutional memory," and the phrase exposed the gap this layer
fills: an institution whose memory has no home keeps it nowhere.
Layer Three is the home. Capability records live here, on the
barrier's own shelf of the memory (§6), under the provenance chain
(§8), beside everything else the system remembers.

The design's claim for them is recognition. A threat the barrier has
met before is **recognized on return** — matched against the recorded
capabilities — the way an immune system remembers a pathogen it has
already answered: the second response is faster and better aimed
than the first because the first is *retained*, not merely survived.
This is the layer where the architecture's immune metaphor stops
being only a metaphor for *response* — replication, detention,
stand-down, all Layer Two's — and becomes one for *retention*:
response is Layer Two's; the remembering that makes the second
response faster is Layer Three's. The barrier, in this design, does
not merely fight; it *learns in writing*, and this layer is the
writing's shelf.

**Attribution.** The idea that a security system should keep a
long-lived population of *memory* records — detectors that have
matched before, retained so the next match is met sooner — is not
original to this design, and this thesis does not present it as such.
It is adopted, with credit, from the artificial immune systems
literature: Hofmeyr and Forrest's architecture (2000) gives detectors
a life cycle — immature, mature, and, on matching, **memory** cells
with extended life — and the CLONALG algorithm (de Castro and Von
Zuben, 2002) maintains a fixed-size repertoire in which successful
detectors persist as memory. The project's related-work review lists
the immune lifecycle language among its candidates for adoption
*with attribution*; this element is that adoption, made explicit.
What the Duality AI contributes is the placement and the company the
idea keeps: immune memory as one shelf of a general two-kind memory,
under a provenance chain and a forgetting law — not the memory-detector
idea itself.

**Scope, stated plainly.** Recognition *matching* — deciding that
this arriving traffic is the threat in that record — is a boxed edge
(§11), not part of the authored core: the core contributes the shelf,
the schema, and the provenance of every capability record. The
skeleton implements the shelf and the schema only. Nothing in the
accompanying code recognizes anything.

## 6. Per-Hemisphere Shelves

*Element (d) of the contributed list (Appendix B), adopted by the
author (§2).*

Nothing in this design is single-sided, and memory is no exception.
Records carry an **owner** — the shelf they belong to. The *logical*
shelf holds what the logical hemisphere keeps: procedures, proofs,
worked derivations, checks that have been run and their outcomes.
The *creative* shelf holds what the creative hemisphere keeps:
stories, associations, framings, the alternative that was not chosen
but might be wanted again. The *shared* shelf holds what belongs to
the system as a whole — the hub's merged results and the records no
single side owns. And the *barrier's* shelf holds the capability
records of §5: the perimeter's memory, kept apart from the reasoning
core's, as the perimeter itself is kept apart.

The point of the shelves is the hub. In Layer One, the hub weighs
the hemispheres' *answers*: the two sides' contributions arrive as
distinguishable inputs, kept distinguishable in the merger's trace.
The shelves give the hub the same discipline over *precedent*. A
recall can be drawn per shelf, so each side's precedent arrives as a
separate contribution to be weighed — not as one blended pile in
which a story and a proof carry the same apparent authority. Memory,
in this design, does not flatten the duality it serves; the weighing
that defines the architecture applies to what the system remembers
exactly as it applies to what the system thinks.

**The implementation choice, and its reason.** The working design
takes the shelves as **one store with the owner as a field on each
record**, not as separate stores per shelf. The reason is stated in
the draft and kept here: one store keeps **one chain and one
policy**. Provenance (§8) is defined over a single insertion order;
four stores would mean four chains and the question of how their
orders interleave — a merger problem at the memory's foundation,
duplicating the hub's problem in a place it does not belong. The
forgetting law (§9) likewise applies as one policy over one
population. Separate stores would give each hemisphere a memory it
literally cannot read across — stronger separation, weaker hub — and
that trade was considered and not taken for the foundation. The
choice is a working default of the design's first version, recorded
with its reasoning so a future revision can argue against it on the
record rather than around it.

---

## 7. Guarded Writes: Nothing Is Remembered Unjudged

*Element (e) of the contributed list (Appendix B), adopted by the
author (§2).*

The architecture's oldest rule is that no step proceeds unjudged:
before a merged result may proceed, it is judged against the morality
clauses (Layer One, §4.5). This layer extends the rule to memory,
because a memory write *is* a step — one whose effects outlast every
other kind. An answer is spoken once; a memory is consulted forever.
In the full design, therefore, every write passes the barrier's
inspection and the morality gate's judgment before it is remembered:
a memory the system should not keep — planted by an adversary,
poisoned in transit, or clause-violating in content — is refused at
the door. The design's reason is stated flatly in the idea list
(Appendix B): *a poisoned memory is an attack that lasts forever.*
The barrier exists to keep attacks from reaching the core once; the
guarded write exists to keep one from taking up residence in the
past the core will trust for the rest of its life.

Guarded writes are also where this layer's defense differs in kind
from Layer Two's. The barrier inspects *traffic* — things in motion,
crossing a boundary. A memory write is traffic that intends to stop
moving and become part of the house. The gate's two-sided character
applies here as everywhere in this design: strictness about what may
enter, leniency within reason about honest material whose form is
unusual. What the doctrine adds is the placement — judgment stands
at memory's door as it stands at the hub's exit and the barrier's
wall, so that in the whole architecture there is no door at which
judgment is absent.

**The skeleton's honest position.** In the accompanying code, the
guarded write is a `write_hook` extension point, and it is labeled
as exactly that. A registered hook sees each record before it is
stored and may refuse it; a refusing hook blocks the write entirely
— nothing is stored, and the caller is told so. **The hook is where
the gate will stand; the skeleton does not pretend the gate is
standing there yet.** No barrier inspection and no clause judgment
are implemented in the memory module, and this thesis does not
describe the extension point as if they were. What the foundation
builds is the doorway, in the right place, with the refusal semantics
the doctrine requires — the judgment itself is future work, and is
recorded as such in §13.

## 8. Provenance: Every Memory Can Show Its Papers

*Element (f) of the contributed list (Appendix B), adopted by the
author (§2).*

Layer Two's monitoring promised a record in which every act could be
reviewed; this element makes the same promise for *beliefs*. Every
record in the memory carries its **source** (what wrote it), its
**stage** (where in the system it came from), and its **timestamp** —
and is linked into a **hash chain**: each record's hash covers the
previous record's hash together with the record's own contents, in
insertion order, from a genesis link (`DUALITY-MEMORY-START`). The
construction is the same one Layer Two adopts for its monitoring log
— a standard hash chain, deliberately unoriginal — applied here to
the store's contents rather than to an event log.

The consequence the design wants is traceability of belief. Any
record the system holds can be walked back: *which step wrote this,
when, out of what, and after which other records* — and the chain
lets the store answer a stronger question than any single record
can: *has anything here been changed since it was written?* Edits
made to stored records outside the system's own operations — a word
altered, a record swapped, a link forged — break the chain and are
detectable by recomputing it (`verify_chain()` in the code, §12). In
the vocabulary of the idea list, the system can always answer the
question *why do you believe that?* — not with an interpretation of
its own contents, but with the receipt: this record, written by this
stage, at this time, in this position in the chain.

**The honest limit, stated in the code as well.** Consolidation and
pruning are *system* acts that change stored records — consolidation
marks episodes; pruning removes records outright — and after either
one, the chain is **re-sealed** over what survives: the surviving
records are re-linked, in order, over their current contents. The
chain therefore attests to what the store *now* holds, in order, and
catches edits made outside the system's own operations. It is a
structural demonstration of provenance — **not a forensic log that
could survive an adversary with write access to the store itself**;
an attacker who can rewrite the whole store can re-seal a whole
chain, and this design does not claim otherwise. There is also a
deliberate tension with §9, and the design resolves it openly:
forgetting wins over total recall. A pruned record is gone, link and
all. Provenance governs what is kept; it does not resurrect what the
design chose to forget. A memory that could prove everything it ever
held would be a memory that could forget nothing — and §9 is the
author's adopted position that such a memory is a hoard, not a mind.

## 9. Graceful Forgetting, and the One Exemption

*Element (g) of the contributed list (Appendix B), adopted by the
author (§2). The exemption itself is the author's law, carried down
from Layer One (§2).*

A memory that keeps everything forever is a hoard, not a mind. It
grows without bound, its recall drowns in the obsolete, and it makes
no distinction between the formative and the trivia of a Tuesday.
This layer therefore forgets — by law, not by accident. A record's
**strength decays with a half-life**: in the current working policy,
an unreinforced record loses half its strength every 30 days.
Recall ranks by *current* strength, so what is old and unreinforced
sinks below what is recent or reinforced, and the memory's attention
— like the design's namesake — favors what has proven worth keeping.
When a record's decayed strength falls below the **prune threshold**
(working value: 0.05, roughly four and a third half-lives out), the
record is **forgotten**: removed from the store, with the chain
re-sealed over the survivors (§8). Forgetting is a *policy*, set in
data — half-life, threshold, and the protected list of the next
paragraph all live in `config/memory_policy.json` — so the memory's
temperament is readable, debatable, and revisable in the open, in the
same way the morality library's contents are. Which is the point:
how fast a mind lets go of its past is a values decision, and this
architecture's habit is to put values decisions in files where they
can be argued with, not to bury them in code where they cannot.

**The exemption is absolute.** Records carrying a **protected tag**
are never pruned, however faint they become. In the current policy
the protected tag is `constitutional` — the tag under which the
morality clauses themselves ride. The system may forget what
happened last spring; **it may not forget what it holds to be
right.** This is the author's law carried down from Layer One (§2):
the gate judges every step against the clause library, and a library
that could decay out of the memory with age would make the gate's
judgment a function of the calendar. The clauses are therefore not
subject to the forgetting they govern. Everything else in the memory
— every episode, every lesson, every capability record — lives under
the decay law; the constitution of the system does not.

One boundary of the law deserves its own sentence, because it is
the kind of detail that decides whether a doctrine is real. The
exemption protects records from *pruning*; it does not freeze them.
A protected record's strength still decays for the purposes of
recall ranking — the clauses can sink in a ranked list like anything
else — but sinking is not vanishing, and the floor the exemption
sets is existence, not prominence. The design accepts that trade
openly: what the law guarantees is that the clauses will always
*be there* to be consulted, which is the property the gate actually
depends on.

## 10. Tiers, and the Future of Sync

*Element (h) of the contributed list (Appendix B), adopted by the
author (§2). Sync is a future phase, by the element's own terms.*

A cloud memory is tiered by temperature. **Hot** memory is the
working set — small, fast, always at hand. **Warm** memory is the
recent past, kept close: episodes not yet consolidated, lessons
still being tested. **Cold** memory is the sealed archive:
consolidated, rarely opened, kept for provenance. In the foundation,
tier is a *placement property the design reserves*: a function of a
record's kind, age, and strength — fresh episodes run hot,
consolidated semantics cool, and pruned records are gone rather than
frozen. The skeleton stores everything in one place and implements
no tiering; it marks the property so the model reserves room for it —
the foundation everywhere builds the doorway before the room.

**Node sync — a future phase, explicitly not built.** The author's
word *cloud* (§1) carries a commitment the foundation does not yet
keep: that this memory will one day be *distributed* — kept by more
than one node, in copies that agree. When that phase comes, the
design already knows how its nodes will establish trust, because the
handshake is the architecture's own: before a node accepts another's
records, the two will agree on the chain head (§8) by the **hat-tile
handshake of Layer Two**, in its two-handed **Mirror Twin** form —
a node accepts a sync only where the two derivations interlock and
agree, so a copy that cannot close the geometry is refused, failing
closed like the handshake itself. None of that is built here: no
nodes, no transport, no agreement protocol, no conflict rules. The
foundation's job is narrower and, the design holds, prior: one
store, one chain, and laws a distributed version would have to
preserve — because a memory whose laws only work in a single box was
never a cloud design, only a box with ambitions.

---

## 11. The Hybrid Structure as Product Architecture

The build decision (§1) is part of the design, and this section
states it as one. The hybrid divides Layer Three into an **authored
core** — what the author and his collaborator construct themselves —
and **boxed edges** — plug-in slots, defined by interface and
contract, that others can add to when they want. The division is not
about difficulty; it is about identity. The core is what Layer Three
*is*: change the core and you have a different design. The edges are
what Layer Three *runs on and with*: change an edge and the design is
untouched, better implemented. The core therefore does not move when
a contributor arrives; the edges exist precisely so that arrival is
easy.

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
| Recognition matching for immune memory | **Boxed edge** | Given arriving traffic and the barrier shelf's capability records, judge whether a known threat has returned; the core keeps the records and their provenance — you decide what counts as a match. |
| Sync transports (future phase) | **Boxed edge** | Carry chain heads and records between nodes and report agreement; the handshake and the acceptance rule stay core design (Layer Two, Parts 3–4). |

The author's rationale for building this way was given in product
terms, and it is quoted, not paraphrased: "I believe that's more of
a profitable margin and a layered system to set up if anybody were
to sell this software." The structure follows the reasoning. A
layered system sells in layers. The **core is the owned asset** — the
model, the laws, the contracts, the reference implementation —
authored once, held by the author, and the thing every other piece
depends on. The **boxed edges invite an ecosystem**: contributors and
customers build backends, rankers, indexers, and matchers against
stable contracts, and every edge anyone builds makes the core more
useful without diluting who owns it. The margins in such a system
live in the core and in the services around it — hosting, support,
integration, and future layers — not in re-selling the replaceable
parts, which competition drives toward free. The hybrid is thus the
product architecture and the engineering architecture at once: the
same line that separates what the design *is* from what it *runs
with* separates what an author *holds* from what an ecosystem
*supplies*.

**The honest sentence.** The published repository is MIT-licensed,
so the design itself — this thesis, the architecture, the core as
published — is free for anyone to use, including commercially. That
fact does not contradict the paragraph above; it locates it.
Sellable value in an open-core model is not the published design's
exclusivity, which the license gives away on purpose. It is the
hosted service (a running Memory Cloud, operated and backed up),
support and integration for those who build on the core, and any
future layers the author chooses to keep proprietary. The author's
layered structure sets all of those up; the license decides which of
them exist, and this thesis records both facts side by side rather
than letting the product note imply a moat the license does not
build.

## 12. Relation to the Code

As with the earlier layers, a structural skeleton accompanies this
thesis: `src/duality_ai/memory.py`, its laws in
`config/memory_policy.json`, and its tests in
`tests/test_memory.py`. The module's own docstring states its
standing — *structural demonstration only* — and this section keeps
the same discipline: what follows is what the code actually does,
method by method, and then what it deliberately does not do.

**The record.** `MemoryRecord` is the schema of §11: `id`, `kind`
(`episodic` or `semantic`), `owner` (`logical`, `creative`,
`shared`, or `barrier`), `content`, `source`, `stage`, `tags`,
`created_at` (ISO 8601 UTC), `strength` (default 1.0), and the two
chain links, `prev_hash` and `record_hash`. Its hash is computed as
SHA-256 over the previous link plus a canonical JSON form of every
field except the hashes themselves — so the seal covers the record's
whole content, its kind and owner included.

**The store.** `MemoryStore` is the boxed-edge contract, an abstract
class of five methods — `put`, `get`, `all`, `find`, `remove` —
with insertion order as part of the contract, because the provenance
chain is defined over that order. Two implementations ship:
`InMemoryStore`, a dictionary that persists nothing, for tests and
demonstrations; and `JsonFileStore`, the authored reference backend —
one JSON file, rewritten whole on every mutation via a temporary
file and an atomic rename, so a crash mid-write leaves the previous
file intact.

**The cloud.** `MemoryCloud` is the authored core facade, constructed
with a store and a policy — the policy loaded by default from
`config/memory_policy.json`, whose current working values are the
numbers cited throughout this thesis (half-life 30 days, prune
threshold 0.05, protected tags `["constitutional"]`, consolidation
at three episodes). Its operations are the layer's laws, one by one:

- `remember()` — validates kind and owner, chains the new record to
  the current head, offers it to the `write_hook` if one is
  registered (a refusal stores nothing and returns `None`), and
  stores it. This is §7's guarded write, as an extension point.
- `recall()` — filters by kind, owner, tag, and a case-insensitive
  text substring, and returns *copies* carrying each record's current
  decayed strength, ranked strongest first (§9). Recall never mutates
  the store: reading the past does not rewrite it.
- `verify_chain()` and `head_hash()` — the provenance machinery of
  §8: recompute every link from the genesis string and report
  whether the store's current contents are exactly what the chain
  seals.
- `consolidate()` — §4's policy: clusters of at least three
  unconsolidated episodes sharing a tag each produce one semantic
  record whose content is the placeholder counting summary, owned by
  the shared shelf; the source episodes are marked `consolidated`;
  the chain is re-sealed (§8's honest limit, implemented as
  described).
- `decay_and_prune()` — §9's law: each record's strength is decayed
  by the policy half-life to the present moment; records below the
  threshold are removed *unless* any of their tags is protected, in
  which case they are skipped however faint they are; the chain is
  re-sealed over the survivors; the count pruned is returned.

**What the code deliberately does not do.** It does not learn: no
record changes any behavior of any component. It does not summarize
with a model: consolidation's distillation is the labeled counting
placeholder of §4. It does not match embeddings or meanings: recall
is filters and substring search, ranked by decayed strength. It does
not tier: §10's temperatures are a reserved property, not an
implementation. It does not network, distribute, or sync: there are
no nodes. And it does not stand the gate in the write hook: §7's
doorway is built and empty, as labeled. The accompanying tests verify
the bookkeeping — round-trips and filtering against *both* stores,
chain linking and tamper detection, decay arithmetic, pruning with
the constitutional exemption, consolidation ripeness and mark-once
behavior, hook refusal, and JSON persistence across instances — and
nothing beyond the bookkeeping.

## 13. Limits and Open Questions

This section exists so that the layer cannot honestly be misread,
and so that its undecided questions are recorded as undecided.

**What Layer Three is not.** It is not a working memory: the skeleton
demonstrates the bookkeeping of the design's laws and stores text
records; nothing in it learns, understands, or summarizes. It is not
a cloud system: "cloud" is design intent (§1), and no distribution,
replication, or sync is implemented or claimed. It is not a
neuroscience claim: the episodic/semantic distinction, consolidation
as sleep, and immune memory are organizing templates borrowed —
with attribution where the borrowing is specific (§5) — and no
finding about brains is asserted or needed. Its provenance chain is
not a forensic guarantee: it attests to the store's current contents
and catches outside edits, and §8 states exactly the adversary it
does not survive. And nothing in this layer has been tested against
a real deployment, a real adversary, or a real workload; the design
positions are stated with their reasoning, and their empirical worth
is an open question, not a result.

**The revisable defaults.** The working numbers — half-life 30 days,
prune threshold 0.05, consolidation at three episodes — were adopted
as defaults, not derived. A faster half-life (say 7 days) makes the
memory nimble and lossy; a slower one (90 days) makes it retentive
and heavy. The policy file exists so this temperament can be tuned
without pretending the tuning is architecture; the right values, if
the design is ever run, will come from watching it run.

**Open questions, recorded as they stand.**

- **Episodes: verbatim or summarized at write time?** The skeleton
  stores episode content exactly as written. Verbatim is honest and
  auditable but grows without bound; summarizing on the way in is
  compact but lets a summarizer decide, at the door, what the past
  was. Consolidation summarizes later either way — the question is
  whether it should also summarize first.
- **The protected list.** The current policy protects only
  `constitutional`. Should the barrier's capability records (§5) be
  protected too — immune memory that never fades, however old the
  threat — or should even they be allowed to decay once a threat is
  extinct? The arguments cut both ways: a forgotten attacker can
  return as a stranger; a memory that protects everything protects
  nothing. The draft policy protects the clauses alone, and the
  question is left open on the record.
- **Recognition matching.** §5's matcher is a boxed edge by design,
  but the design does not yet say what standard a matcher must meet
  before its "recognized" verdict may speed a response — a false
  recognition is a false accusation at machine speed. The criteria
  are future work.
- **The gate in the doorway.** §7's write hook awaits the morality
  gate itself: which clauses govern memory writes, and whether
  leniency within reason has the same shape at memory's door as at
  the hub's exit, are undecided.
- **Sync.** §10 defers the whole distributed phase — nodes,
  chain-head agreement under the Mirror Twin handshake, conflict
  rules for copies that disagree. It is the layer's largest single
  piece of future work, deferred deliberately: the foundation's laws
  come first, because they are what a distributed version must
  preserve.

The author leaves these questions open in the same spirit as the
earlier layers': recorded, attributed to the parts of the design
they belong to, and awaiting the compare-and-decide process by which
this architecture has been built from its first dictation.

---

## Appendix A — The Author's Dictations for Layer Three (verbatim)

The direction for Layer Three was dictated by Kenneth Lee Blum Jr on
November 7, 2026. It is reproduced here exactly as recorded, so the
reader may verify this thesis against its source.

**Part 10 — the memory cloud, and the hybrid decision:**

> "Now I want to do a third level on this structure on the GitHub for the AI brain. Now I want a cloud structure like a memory. Give me some ideas — should we have it constructed ourselves and lay out the code and the foundation of the architecture, or should we cookie box it and have others add to when they want?"

The hybrid decision, and the author's rationale in his words:

> "I believe that's more of a profitable margin and a layered system to set up if anybody were to sell this software."

**The adoption of the contributed elements (§2)** — the author's
direction for this thesis, dictated November 7, 2026:

> "I want you to put a thesis a full on thesis for the memory the duality parts of it that um we came up with and then your insight into the excess of extra to it that I love and you should be noted for yeah let's do it."

## Appendix B — The Contributed Idea List, as Presented

The eight ideas below were presented to the author by Lux on
November 7, 2026, at his request ("give me some ideas"), together
with the recommendation of the hybrid build the author adopted.
They are reconstructed here faithfully from the working draft
(`docs/layer3-design.md`, §2) and the record of the presentation, and
are credited to Lux in §2 of this thesis. The author adopted all
eight into the design (§2); each is specified in the section noted.

1. **Two memories, like everything else** — *episodic* (what
   happened: conversations, decisions, detained attacks) and
   *semantic* (what's known: facts, lessons, attack signatures).
   (§3)
2. **Consolidation = sleep** — a periodic pass distills raw episodes
   into lasting knowledge, the way the brain consolidates overnight.
   (§4)
3. **Immune memory** — the barrier's attack records live here; a
   known attack returning gets recognized instantly, like the body's
   memory cells. (§5)
4. **Each hemisphere keeps its own shelf** — logic remembers proofs
   and procedures; creativity remembers stories and associations;
   the hub weighs *memories* the same way it weighs answers. (§6)
5. **Guarded writes** — nothing enters memory without passing the
   barrier + the gate; a poisoned memory is an attack that lasts
   forever. (§7)
6. **Provenance on every memory** — who wrote it, when, and why,
   sealed in a hash chain (the design extends Layer Two's sealed
   monitoring record), so the system can always answer *"why do you
   believe that?"* (§8)
7. **Graceful forgetting** — memories decay unless reinforced;
   leniency applied to memory; the morality clauses are the one
   thing never forgettable. (§9)
8. **Hot / warm / cold tiers** — working memory (fast, small),
   recent episodes, and a sealed cold archive; nodes sync using the
   hat-tile handshakes. (§10)
