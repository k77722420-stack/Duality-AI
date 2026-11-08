# Related Work — Kindred Theories and Prior Art

**For:** The Duality AI (Kenneth Lee Blum Jr, 2026)
**Compiled:** November 7, 2026, from a sourced web review
**Rule of this document:** everything here belongs to its named authors.
The Duality AI adopts nothing silently — anything borrowed enters the
design with its credit attached.

## The headline finding

**No published work was found that combines all five Duality elements
into one architecture.** The novelty of the Duality AI is
*combinatorial*: its elements have distinguished ancestors — some very
close — but the assembly (two reasoning hemispheres + a weighing hub +
a morality-clause gate with bounded leniency + a gatekeeper barrier
with sandbox doctrine and sized replication + hat-tile handshakes) does
not appear in the literature reviewed.

## A. Two-mode reasoning and the hub (Element 1) — overlapping

- **Mixture-of-Agents** — Wang et al. (Together AI), 2024,
  arXiv:2406.04692; ICLR 2025. Several proposer models generate answers;
  an aggregator synthesizes one final answer (65.1% on AlpacaEval 2.0
  vs GPT-4o's 57.5%). *The closest published relative of the hub* — but
  its proposers are not logical/creative hemispheres.
- **Deep learning in a bilateral brain with hemispheric
  specialization** — Rajagopalan, Rawlinson, Goldberg & Kowadlo, 2022,
  arXiv:2209.06862. Left network learns specificities, right network
  generalities, merged by a weighted-attention head. *The closest
  scholarly hemisphere+merger structure* — for image classification,
  not language-model reasoning modes.
- **Multi-agent debate** — Du et al., 2023 (ICML 2024); **Self-Refine**
  — Madaan et al., NeurIPS 2023; **Society of Mind** — Minsky, 1986
  (many agents, explicitly *no* central hub — an instructive contrast).
  Lateralized networks also appear in Hu & Rostami (NeurIPS 2024).
- Two self-published pieces use nearly the Duality wording (a
  "Dual-Core Silicon Mind" essay; the Manglekit "Dual-Brain" docs) —
  blog/documentation tier, no peer review or evaluation. Noted for
  completeness, not relied on.
- **Verdict:** no peer-reviewed work proposes logical + creative LLM
  hemispheres merged by a weighing hub. Element 1 is a recombination.

## B. The morality-clause gate (Element 2) — the same core idea, published

- **Constitutional AI** — Bai et al. (Anthropic), 2022,
  arXiv:2212.08073. A written constitution (~16 principles) is used to
  critique and revise model outputs; Anthropic explicitly does *not*
  claim the model understands morality — the same disclaimer the
  Duality AI makes. Originally training-time, not a runtime gate.
- **Constitutional Classifiers** — Sharma et al. (Anthropic), 2025,
  arXiv:2501.18837. The runtime form: input/output classifiers trained
  from a constitution. Jailbreak success fell 86% → 4.4%, at +0.38
  points of over-refusal, over ~3,000 hours of red-teaming. *The
  closest working relative of the morality gate.*
- **Leniency's closest formal analogue:** **Safe Reinforcement
  Learning via Shielding** — Alshiekh et al., AAAI 2018. A shield
  corrects an action *only if* it would violate the specification —
  an explicit principle of **minimum interference**. Companion ideas:
  OpenAI's Rule-Based Rewards (Mu et al., NeurIPS 2024) and
  safe-completions (Yuan et al., 2025) — graded help instead of hard
  refusal when a request is partly allowable.
- **Cautionary, different:** the Moral Machine (Awad et al., Nature
  2018) — its own authors warn against turning crowd preferences
  directly into rules.
- **Verdict:** strict written clauses judging outputs is established.
  *No source pairs them with a named, bounded "leniency within
  reason" principle.* That pairing appears to be the Duality AI's own.

## C. Gatekeepers and immune systems (Element 3) — overlapping to same

- **Llama Guard** — Inan et al. (Meta), 2023, arXiv:2312.06674: an
  LLM safeguard screening inputs and outputs against a written
  taxonomy. **LlamaFirewall** — Chennabasappa et al. (Meta), 2025,
  arXiv:2505.03574: PromptGuard 2 + AlignmentCheck (inspects an
  agent's chain-of-thought) + CodeShield. **NeMo Guardrails** —
  Rebedea et al. (NVIDIA), EMNLP 2023: rails at input, dialog,
  retrieval, execution, output. **ShieldGemma** (Google, 2024).
- **The immune-system line:** Forrest et al. (1994) and Hofmeyr &
  Forrest (2000), artificial immune systems for computer security;
  Darktrace's "Enterprise Immune System"/Antigena applies the metaphor
  commercially to networks (not LLM gatekeeping). **AICA** — Kott
  et al. (NATO), 2018 / Springer 2023, arXiv:2304.12408: a reference
  architecture for autonomous intelligent cyber-defense agents, with
  five agent functions the barrier's checklist can be measured against.
- **Verdict:** screening everything in and out is standard practice.
  No "blood-brain barrier"-branded AI gatekeeper was found — **the
  label appears to be the Duality AI's own**; the mechanism is not new.

## D. Sized replication and standing populations (Element 4) — the formula was not found

- **CLONALG** — de Castro & Von Zuben, IEEE Transactions on
  Evolutionary Computation, 2002: an immune algorithm where clones are
  produced **proportionally to affinity** with the antigen, inside a
  **fixed-size repertoire** whose lowest-affinity members are replaced.
  *The closest relative of both the sizing rule and the standing
  population.*
- **Hofmeyr & Forrest (2000):** detectors pass through a life cycle
  (immature → mature → memory) and **die if never matched** — the
  expiry analogue of the decode rule.
- **Different:** DARPA Cyber Grand Challenge (2016; Mayhem et al.) —
  autonomous find/prove/patch, no replication; Moving Target Defense
  (Jajodia et al., Springer 2011) — randomization, not replication;
  "proportional response" in the literature is a doctrine of state
  retaliation (law/policy), not agent-population sizing.
- **Verdict:** Ken's specific parameterization — threat size + 20–30%
  margin, fixed standing population, post-attack self-termination of
  the surplus — **was not found in the open literature** (defense
  venues index poorly, so this is stated as "not found," not "proven
  nonexistent"). Best described as a novel parameterization of clonal
  selection.

## E. The sandbox doctrine (Element 3, second half) — the same idea, 25 years mature

- **The Honeynet Project** — Spitzner, IEEE Security & Privacy, 2003:
  a honeypot is "a resource whose value lies in being probed,
  attacked, or compromised."
- **Honeypot Deception Tactics** — Rowe, in *Autonomous Cyber
  Deception* (Springer, 2018): "deception in result" — simulate a
  vulnerability so the adversary believes their attack succeeded, and
  route them to a sandbox site. *Nearly the Duality wording, published
  eight years earlier.* The design adopts this doctrine knowingly.
- **Cuckoo Sandbox** — Guarnieri (Honeynet Project, 2010/11): every
  sample detonates in a fresh isolated VM and is observed/recorded.
  **MITRE Engage** and CISA's cyber-decoys guidance frame modern
  practice (Expose / Affect / Elicit). LLM-driven honeypots aligned to
  Engage appear in Hwang et al. (IEEE TNSM, 2025/26).
- **Verdict:** same idea, mature doctrine. The Duality AI's
  contribution is placement — the doctrine as the barrier's default
  Level 2, inside an AI architecture — not the doctrine itself.

## F. Hat-tile geometry and handshakes (Element 5) — no hat scheme found; two corrections

- **The source geometry:** Smith, Myers, Kaplan & Goodman-Strauss,
  "An Aperiodic Monotile," 2023, arXiv:2303.10798 — the hat's tilings
  **require reflected copies** (roughly 1 in 7–8 tiles). Their
  follow-up, "A Chiral Aperiodic Monotile," 2023, arXiv:2305.17743,
  introduced the **Spectre**, which tiles *without* reflections.
  **Correction recorded:** the mirrored/dual-handed character of the
  hat is the original authors' published observation, not a Duality
  discovery. The Mirror Twin's claim is narrower and honest: applying
  a dual derivation to a *handshake* is the proposed twist.
- **Real aperiodic cryptography exists — for quasicrystals, not the
  hat:** Patera, Pelantová & Masáková, US Patent 6,792,108 (2004) —
  a quasicrystal function generating an infinite aperiodic keystream
  from a few key parameters. Yan et al. (2020) used Penrose tiling for
  visual secret sharing. One 2024 preprint uses Spectre tiling for
  sensor *placement* against clone attacks — placement, not keys.
- **No peer-reviewed hat-tile key or handshake scheme was found.**
  One student-tier preprint merely asserts hat patterns "can be
  leveraged" for keys, with no scheme. (The author's own public posts
  about hat keystreams, Aug–Sep 2026, exist as a self-published trail;
  they are disclosed here, not relied on as prior art.)
- **Standing warning (adopted into the thesis):** aperiodicity alone
  gives no security proof. Tiling rules are public and deterministic;
  any real security must come from secret key material and vetted
  cryptographic primitives — the position the Duality AI's stack
  recommendations already take.

## Adoptable, with attribution (candidates for the author's decision)

1. **The gate's report card** — from Constitutional Classifiers
   (Sharma et al. 2025): evaluate the morality gate by *violation
   rate, over-refusal rate, and runtime overhead*; write the allowed
   side of the clause library as carefully as the disallowed side.
2. **"Minimum interference"** — from Shielding (Alshiekh et al.
   2018): adopt as the *formal definition* of leniency within reason
   — the gate intervenes only on violation, and then only as much as
   the clause requires.
3. **Immune lifecycle language** — from CLONALG (2002) and Hofmeyr &
   Forrest (2000): name the replication stages (spawn → active →
   memory/decoded) after the published immune model, and cite
   affinity-proportional cloning as the sizing rule's ancestor.
4. **MITRE Engage (Expose / Affect / Elicit)** — adopt as the
   sandbox's stated goals and measures, replacing ad-hoc observation
   notes with the field's own frame.
5. **AICA's five functions** — adopt as a completeness checklist for
   what a barrier bot must be able to do (sensing, planning, action,
   learning, governance) — with the NATO architecture cited.
6. **The hub's evaluation method** — from Mixture-of-Agents (Wang
   et al. 2024): test the hub's weighing by comparing merged output
   against each hemisphere alone, on a public benchmark — the
   adoptable *method*, whatever the results.

## What this means for the Duality AI

The concept stands as an original *combination* with honest ancestors.
Its strongest claims to novelty, on current evidence: the
logical/creative hemisphere pairing over an LLM with a weighing hub
(Element 1 as assembled), strict-clauses-plus-named-leniency
(Element 2's pairing), the blood-brain-barrier framing (Element 3's
label), the exact replication parameterization (Element 4), and the
hat-tile handshake application (Element 5). Its most candid debts:
Constitutional AI for the clause gate, the Honeynet tradition for the
sandbox, and the Smith–Myers–Kaplan–Goodman-Strauss papers for the
geometry itself.
