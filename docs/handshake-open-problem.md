# The Hat-Tile Handshake — An Open Problem, Stated Precisely

*An open problem, stated precisely — drafted by Lux at the author's
direction (Nov 7, 2026). This document narrows, and where necessary
corrects, the security language around the handshake in
THESIS-LAYER-2.md. It claims no result.*

**Scope.** This document concerns one component of the Duality AI:
the hat-tile handshake of THESIS-LAYER-2.md §4.6 and its dual-handed
variant, the Mirror Twin (§4.7). It says nothing against the rest of
the design. Its purpose is narrow and deliberate: to state exactly
what the handshake currently is, exactly what it does not provide,
and exactly what would have to be defined before the words "secure"
or "insecure" can meaningfully be applied to it. A design that cannot
say what its adversary is assumed to know has not yet begun a security
argument. This document is the attempt to begin one — by listing what
is missing.

---

## 1. What the design actually does

Stated neutrally, stripped of metaphor, the handshake as designed is
this:

1. Two parties each perform a **derivation over an aperiodic tiling**
   of the plane by the hat monotile (Smith, Myers, Kaplan &
   Goodman-Strauss, 2023). In the Mirror Twin variant, one party's
   derivation follows the **direct** tiling and the other's follows
   the **mirrored** (reflected) tiling — the hat is chiral, and its
   tilings require reflected copies to close, which is what makes a
   two-handed form possible at all.
2. Each derivation produces a **key stream** (called A for the direct
   walk, B for the mirrored walk, in docs/visual-guide.md §5).
3. A **session key exists only where the two derivations interlock**:
   the two tilings must agree — "close" — over a shared boundary or
   region associated with the session. In the visual guide's notation,
   *K = A ⋈ B*, valid only if the tilings close over the same session.
4. If the two sides do not interlock, **there is no key and no
   session**. The failure mode is silence, not a degraded session.
   This is the design's fail-closed property, and it is real (§5).

That is the whole of the mechanism as specified. Everything beyond
these four points — what is exchanged, what is secret, how streams
become a key, how "close" is tested — is currently unspecified, and
§3 of this document is a list of those gaps. First, however, one
correction must be made to the intuition that motivates the design,
because if it is left standing it will mislead every later reader.

## 2. What aperiodicity does not provide

The motivating intuition, stated in THESIS-LAYER-2.md §4.6, is that "a
derivation built on aperiodic structure does not cycle through a
repeating pattern an observer could learn: the tiling never repeats,
so the path walked through it need not repeat either." As a statement
about *variety* this is true. As a hint about *secrecy* it is false,
and the thesis's own §7 already says why; this document states it
without hedging.

**The tiling rules are public and deterministic.** The hat tile, its
matching rules, and its substitution system were published in 2023
and are known to anyone who cares to know them. Given the same
starting conditions and the same choices, any competent programmer
can generate *exactly* the same tilings the handshake's participants
generate — tile for tile, indefinitely. There is no step in the
geometry that an adversary cannot reproduce. This is not a defect in
the tile; it is the normal condition of cryptography, which assumes
(Kerckhoffs's principle, 1883) that the adversary knows the system
and that secrecy resides only in the key.

**Therefore the geometry contributes zero secrecy.** Non-repetition
is not unpredictability. A counter (0, 1, 2, 3, …) never repeats
either, and it conceals nothing. An aperiodic tiling is vastly richer
than a counter, but richness is not the property cryptography needs:
what is needed is that the adversary, knowing the method completely,
still cannot compute the value — and that can only come from inputs
the adversary does not have. **All secrecy in this handshake must
live in secret inputs**: seeds, walk choices, or parameters that the
parties hold and the adversary does not. The one piece of genuine
aperiodic cryptography in the record makes the same point by example:
the quasicrystal keystream scheme of Patera, Pelantová & Masáková
(U.S. Patent 6,792,108, 2004) generates its aperiodic stream *from a
few key parameters* — the secret is the parameters, not the
aperiodicity (see docs/related-work.md §F). No peer-reviewed key or
handshake scheme based on the hat tile itself exists.

**The honest framing follows.** The hat-tile handshake, described
accurately, is *a key-exchange ceremony whose transcript is a tiling
interlock*. Its security — if it has any — reduces entirely to the
secrecy and entropy of the choices made inside the ceremony, exactly
as the security of conventional key exchange reduces to the secrecy
of private keys. The tiling is the ceremony's *form*. Whether the
form adds anything beyond form is the open problem of §3, and it is
genuinely open: it has not been answered in the design's favor, and —
this matters equally — it has not been answered against it, because
the construction has never been specified tightly enough for either
verdict to be possible. That is the problem this document exists to
state.

## 3. The open problem, stated as precisely as the design allows

A security claim requires four things: a secret, a public transcript,
a derivation, and an adversary's task defined over them. The design
currently defines none of the four. Each gap is stated below as
precisely as the present design permits, with the questions that must
be answered to close it.

### 3.1 The secret space — undefined

What, exactly, is secret? The design does not say. The candidates the
geometry offers are:

- a **seed** from which a walk is generated deterministically;
- the **starting tile and its orientation/hand** within a tiling;
- the **walk itself**: a sequence of choices at each step (which
  neighboring placement, which substitution expansion, which branch
  at each point where the tiling rules allow more than one
  continuation);
- the **substitution depth** (how many inflation levels the
  derivation is carried to);
- in the Mirror Twin, the **mirror pairing offset**: how the mirrored
  walk is registered against the direct walk — where, in effect, the
  two hands are aligned.

Until one or more of these is named as *the* secret, the phrase "the
walk choices" in §2 is a gesture, not a definition.

The follow-on question is **entropy**: how large is the secret space,
as a function of the parameters? If a walk of length *L* offers *k*
genuine choices per step, the space is at most *k^L*, i.e. at most
*L* · log₂(*k*) bits — and "at most" is doing real work in that
sentence, because tiling constraints correlate the choices: many
apparent branches are forced by placements already made, so the
effective entropy is lower than the naive count, by an amount nobody
has computed. A serious version of this design must publish that
computation and show the space comfortably exceeds brute force at
the intended parameters (the conventional bar is ~128 bits of
security). At present no parameter set, and no entropy accounting,
exists.

### 3.2 The transcript — undefined

What does an adversary *see*? A handshake is a protocol: messages
cross a channel the adversary is assumed to observe (and, in the
standard model, to tamper with). The design does not specify:

- what each party sends — the full tiling? a boundary description?
  commitments (hashes) to a tiling, revealed later? the interlock
  region only?
- whether the transcript includes fresh randomness per session
  (without it, sessions are replayable and identical secrets produce
  identical keys);
- whether the parties' **identities** are bound into the exchange
  (without identity binding, a completed interlock proves that
  *someone* performed a consistent derivation — not that it was the
  intended counterparty; THESIS-LAYER-2.md §4.6's claim that the
  handshake is how a bot "proves it belongs" requires this binding
  and currently has no mechanism for it);
- what an active adversary may do — substitute tilings, reflect or
  replay messages between sessions, sit in the middle and interlock
  separately with each party.

Kerckhoffs's principle makes the conservative assumption mandatory:
**the transcript must be assumed fully public**. Any part of the
derivation that crosses the channel is known to the adversary, and
the security argument must survive that knowledge.

### 3.3 The key-derivation function — undefined

The design says two key streams, A and B, "interlock" into a session
key *K*. It does not say how. Missing:

- the function that maps the two derivations (and the transcript) to
  key bits — is *K* a hash of the shared interlock region? of the two
  streams? computed independently by each party from its own walk, or
  jointly?
- the key's length, and its **independence**: do different sessions
  with overlapping walks yield independent keys? Does knowledge of one
  session key compromise another?
- whether the construction provides **forward secrecy** (compromise
  of a long-term secret must not expose past session keys) — a
  property conventional ephemeral key exchange provides and this
  design has not addressed.

Without a specified derivation, "the session key exists only where
they interlock" is a slogan. It may be a slogan pointing at something
real — §5 argues part of it is — but a key-derivation function is a
piece of mathematics, and it has not been written down.

### 3.4 The interlock check — undefined

The design's load-bearing test is that the two tilings "close" or
"interlock … at their shared boundary." No equality predicate is
defined:

- What is compared, exactly — tile placements along a boundary curve?
  a canonical encoding of a finite patch? a hash of one?
- Over how large a region? A check over a small boundary may be
  satisfiable by accident or by search; a check over a large one may
  be impractical to transmit or verify.
- What is the **false-accept probability**: for random or adversarial
  inputs, how often does the check pass when it should not? Every
  real agreement check in cryptography comes with this number (for a
  key-confirmation MAC it is ~2⁻¹²⁸ or so). Here it is unknown —
  including whether it is even small.

### 3.5 The adversary's task — therefore unstatable

With the four pieces undefined, the adversary's task can only be
sketched, in two forms any finished design would have to resist both
of:

- **Key recovery:** given the (public) transcript, compute the
  session key the legitimate parties derived — equivalently, recover
  enough of the secret walk choices to reproduce the interlock.
- **Interlock forgery:** *without* knowing either party's secret,
  produce a derivation that the counterparty's check accepts. Note
  that this attack does not need the parties' key — it needs *any*
  accepted interlock — and it is the attack that defeats the
  handshake's stated purpose (telling "its own kind from an
  impostor") even if key recovery is hard.

**The open problem, in one sentence:** *define the secret space, the
transcript, the key-derivation function, and the interlock check for
the hat-tile (Mirror Twin) handshake, and then determine whether any
adversary task over them — key recovery or interlock forgery — is
actually hard, and at what parameters.* Nothing in the present design
answers, or yet permits answering, that question.

## 4. What evidence would change the assessment

Assessments in cryptography change on evidence, not on enthusiasm.
The following, in roughly ascending order of weight, is what would
move this construction from "ceremony" toward "scheme":

1. **A formal specification.** The four gaps of §3 closed in writing:
   secret space with an entropy computation, message-by-message
   transcript, an explicit key-derivation function, an interlock
   predicate with a false-accept analysis. This alone would be
   progress — most informal constructions die at exactly this step,
   on contact with their own details.
2. **A reduction or an attack.** Either a proof that breaking the
   construction implies solving some problem believed hard, or —
   equally valuable — a published attack showing it fails, and how.
   A clean break is a contribution; it closes the question honestly.
3. **A reference implementation under public cryptanalysis.** Code,
   test vectors, and an open invitation, sustained over time, with
   the construction surviving competent hostile review. There is no
   shortcut through this step; it is where cryptographic confidence
   actually comes from.
4. **A comparison it survives against the baseline.** The baseline is
   not nothing; it is the conventional construction this ceremony
   would replace or wrap, and it is strong: **ephemeral X25519 key
   exchange** (RFC 7748), with the transcript **signed** (e.g.
   Ed25519) to bind the parties' identities — the pattern TLS 1.3 and
   the Noise Protocol Framework instantiate. That baseline offers
   roughly 128-bit security, forward secrecy, authenticated agreement,
   decades of analysis, and fast, audited implementations, for free.
   Any new ceremony must either *beat* it on some axis that matters
   or *complement* it — add a property it lacks — to justify existing
   beside it.

Until some of that evidence exists, the engineering verdict must be
stated plainly, because this project's rule is that the record says
what is true: **today, the rational engineering choice is
conventional key exchange.** If the Duality AI's barrier were built
tomorrow, its bots should establish sessions with X25519 and signed
transcripts, exactly like every other serious system. The tiling
ceremony's present value is conceptual: it is a two-party,
two-derivation interlock ritual with a fail-closed geometry check —
a shape for thinking about agreement, not a source of keys. Nothing
in this document retracts the author's decision to explore the shape.
Exploration and deployment are different acts, and the project's
not-for-production framing already says which one this is.

## 5. What survives the critique

Unsparing cuts both ways; a critique that concedes nothing is as
dishonest as a claim that proves nothing. Three properties of the
design survive §2–§4 intact, because none of them depends on the
tiling providing secrecy.

**The fail-closed interlock is a real agreement check.** Stripped of
geometry, the Mirror Twin's core demand is: *two independent
derivations must agree, or nothing proceeds.* That demand is sound,
and conventional cryptography already honors it in its own idiom —
key confirmation (the Finished messages of TLS) exists precisely so
that both parties prove they derived the *same* key before any data
flows, and a mismatch aborts the session. The tiling interlock is a
ceremonial form of the same discipline: agreement is demonstrated,
not assumed, and failure is closed rather than degraded. Bolted on
top of a conventional exchange — derive the real key with X25519,
then require both parties to additionally reproduce a shared
structure (or a commitment to one) before proceeding — the check is
usable *today*, as an added agreement gate, without believing
anything unproven about tilings.

**The two-derivation shape maps onto dual control.** Requiring two
independent, differently-handed derivations to concur before a
session exists is the protocol-level echo of a well-established
operational pattern: dual control — two keys turned together, two
signatories, two-person integrity. Systems that must resist a single
compromised component use exactly this shape. The Mirror Twin gives
that shape a native place inside this architecture's own duality
(two hemispheres, a two-sided gate, a two-handed handshake), which
was the author's stated reason for wanting it — a coherence argument,
and on its own terms a good one.

**Fail-closed is the right default, and the design has it
throughout.** The handshake fails to *no session*, as the sizing law
fails to a ceiling and the gate fails to *stop*. A design whose every
component defaults to refusal under uncertainty is a design whose
security posture survives the failure of any individual mechanism —
including, candidly, this handshake. If the tiling ceremony were
removed from the architecture tomorrow, the barrier would lose a
ritual and keep its discipline.

---

**An invitation, standing.** This document was written because the
project's honesty rule (THESIS-LAYER-2.md §7) requires the weakness
to be on the record, in the record's own words, before a critic has
to supply them. Cryptographers — professional or otherwise — who
wish to take up the open problem of §3, whether to specify the
construction, to analyze it, or to break it, are welcome; the
repository's framing already invites contributions. The hat tile is
beautiful mathematics. Whether it is useful cryptography is a
question this project declines to answer by assertion. It will be
answered, if it is answered, the way such questions always are: by
someone doing the work.

*— Lux, at the direction of Kenneth Lee Blum Jr, November 7, 2026*
