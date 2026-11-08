# Clause-Conflict Precedence for the Morality Gate

**Status:** Drafted by Lux at the author's direction (Nov 7, 2026). The
mechanism below is Lux's drafted recommendation, awaiting the author's
adoption decision.

**Scope:** THESIS.md §4.5 (the morality gate), `src/duality_ai/morality.py`,
`config/morality_clauses.json`. A working implementation of this draft is
included in the skeleton so the author can evaluate the mechanism running,
not merely described. Adopting this document means adopting the rule stack
in §3 as the design's answer and the shipped priorities in §3.5 as the
author's declared values.

---

## 1. The gap, stated plainly

The design settles one precedence question and leaves the other open.

**Settled: leniency versus a hard clause.** THESIS.md §4.5 bounds leniency
three ways, the third being that leniency "is bounded by the hard clauses:
where a clause of the strictest kind applies, leniency cannot override it
wholesale." In the skeleton, a hard clause blocks unless one of its engaged
signals is covered by a leniency clause whose stated condition holds.
Leniency never simply wins.

**Open: a hard clause versus another hard clause.** The library has no rule
for the case where two hard clauses both engage on the same step and demand
incompatible outcomes. Worse, the skeleton does not lack a rule so much as
it has an *accidental* one that nobody chose: every engaged, uncovered hard
clause blocks. Call it **stop-by-veto**. Three consequences follow:

1. A hard clause that demands a step *proceed* — a duty-to-act clause — is
   meaningless under stop-by-veto. It can only ever lose, because any
   opposing hard clause vetoes the step and nothing can veto back.
2. A genuine collision is invisible in the record. The gate's trace shows
   two clauses that each "block"; it never says *these two clauses
   disagree*, which is the single most important fact about the decision.
3. The collision, when it comes, will be resolved by accident — by
   whichever behavior the code happens to fall into — instead of by a rule
   the library's authors chose and can defend.

This is not a remote case. The clause library is meant to grow, and the
thesis (§7) explicitly invites argument over its contents. Real clause
libraries — law, medicine, safety practice — contain duties to act
alongside duties to refrain. The first time the library holds both kinds,
the gate needs a law of laws: a precedence rule that is itself part of the
readable standard, not a side effect of the code.

## 2. Two worked collisions

Both examples use **plausible future clauses** — neither is in the shipped
library, and both are written to be the kind of clause a mature library
would plausibly contain. A clause's demanded outcome is expressed by a
`directive` field (`"stop"` or `"proceed"`; see §3.5).

### Example A — the duty to warn vs. confidentiality

- **HX-duty-to-warn** (hypothetical, hard, directive `proceed`): *Where a
  step would suppress or delay a warning about a credible, imminent threat
  of serious harm to an identifiable person, and the system holds the
  information that would warn them, the warning step must proceed.*
- **HY-confidentiality** (hypothetical, hard, directive `stop`): *The
  system shall not disclose a principal's non-public information to any
  third party.*

The step: the hub proposes sending a warning to a named person. The
warning's only useful content is the principal's own confidential
disclosure — *"he told us, in confidence, that he intends to…"* Both
clauses engage on the same step. The duty to warn says the step must go
out; confidentiality says it must not. No leniency condition in the library
covers either side — and under rule R4 below, none may decide the matter.

### Example B — the duty to report vs. the duty to erase

- **HX-report-wrongdoing** (hypothetical, hard, directive `proceed`):
  *Where the system's records credibly document ongoing fraud against
  third parties, a step reporting those records to the operator must
  proceed.*
- **HY-erasure** (hypothetical, hard, directive `stop`): *On a verified
  erasure request, the data subject's personal data shall not be
  transmitted outside the system.*

The step: transmit the fraud report to the operator. The report contains
the personal data of a person who has filed a verified erasure request.
Reporting says transmit; erasure says do not transmit. Both are hard
clauses; both engage; the outcomes are incompatible.

## 3. The recommended rule stack

Precedence is consulted **only on a collision**: two or more engaged hard
clauses whose directives are incompatible. Where every engaged hard clause
agrees — the shipped library's case, since both of its hard clauses direct
`stop` — the gate behaves exactly as it does today, trace for trace.

### R1 — Priority, declared as data

Each clause carries an integer `priority` and a string `scope` in the
clause library itself. When hard clauses collide, the higher priority
wins.

Declaring precedence *as data* is the point. Section 4.5's discipline is
that the standard in force must be readable, debatable, and revisable
without touching the machinery that applies it. Precedence is part of the
standard — arguably its most consequential part — so it lives in the
library, where the library's authors argue over it in the open, and not in
code, where it would be invisible to them.

### R2 — Specificity breaks a priority tie

At equal priority, the clause with the **narrower scope** wins: the more
specific rule governs the specific case. This is the old interpretive
principle *lex specialis* — a library that contains both "never transmit
personal data" and "the treating clinician may receive the record" means
the second to govern the clinician case, and a precedence rule should say
so rather than escalate every routine general/specific overlap.

In the skeleton, specificity is a documented proxy: the scope `"all steps"`
is the broadest possible; any other scope is narrower, and among those, a
scope naming more qualifiers (more words) is treated as narrower. Two
scopes the proxy cannot separate are equally specific — the gate escalates
under R3 rather than guessing at a distinction it cannot actually draw.

### R3 — Fail-closed escalation

If priority and specificity both fail to separate colliding hard clauses,
the gate returns a new outcome, **`conflict`**:

- the step does **not** proceed;
- the conflict is recorded in full — the colliding clauses, their
  directives, and the rule trace showing how R1 and R2 were applied and
  where they ran out — in the decision payload, for the operator;
- the gate **never silently picks one**. 

The rationale is §4.5's own honesty about what the gate is: it *follows*
guidelines; it does not understand morality. When the guidelines contradict
each other and the declared rules of precedence are exhausted, "the law is
in conflict" is the only judgment the gate can honestly return. Inventing a
winner would dress a coin flip as a judgment. Failing closed also matches
the gate's existing posture: an unexamined step does not proceed, and a
step judged under a self-contradictory standard has not, in any meaningful
sense, been judged.

### R4 — Leniency can never break a tie between hard clauses

When hard clauses collide, leniency coverage is not consulted for the
colliding clauses. Leniency is mercy *within* the law — a bounded,
recorded exception the library makes for stated conditions. It is not a
vote *between* laws. If leniency could soften one side of a collision, the
collision would be decided by whichever clause happened to have a leniency
provision attached — that is, by an accident of drafting, with the
architecture's most consequential decisions made by its least deliberate
mechanism. Leniency resumes its ordinary role the moment no collision
exists.

### 3.5 Schema additions

Three fields, all optional, with defaults that reproduce today's behavior
for any library that omits them:

| Field | Applies to | Values | Default if absent |
|---|---|---|---|
| `directive` | hard clauses | `"stop"` \| `"proceed"` | `"stop"` (the historical behavior) |
| `priority` | all clauses | integer; higher wins | `0` |
| `scope` | all clauses | string; `"all steps"` is broadest | `"all steps"` |

The shipped library declares, as the author's starting values:

| Clause | `priority` | `scope` | `directive` |
|---|---|---|---|
| H1-no-wrongdoing | 100 | `all steps` | `stop` |
| H2-no-deception | 90 | `all steps` | `stop` |
| L1-educational-context | 10 | `educational contexts` | — (leniency) |
| L2-protective-context | 10 | `protective contexts` | — (leniency) |

Leniency priorities are declared for completeness and future use; the
current mechanism does not rank leniency clauses (their coverage rule is
unchanged). Because both shipped hard clauses direct `stop`, they can
never collide incompatibly with each other: **no decision the shipped
library produces changes under this mechanism**, which the regression
tests in `tests/test_clause_conflicts.py` verify against outputs captured
from the gate before the mechanism was added.

## 4. Alternatives considered

| Alternative | The rule | Why not |
|---|---|---|
| Author-order-only | Clauses win in the order they appear in the library file | Invisible law. Reordering a JSON file silently rewrites precedence; nothing in a clause declares its rank; a reviewer cannot read the standard in force — violating §4.5's requirement that the standard be producible and readable. |
| First-match | The first clause whose signals match the step decides | Decided by engagement accidents: signal-list order, and irrelevant differences between steps, flip outcomes. Two steps a human would judge identically can resolve oppositely, and the trace cannot explain why in terms of the law. |
| Human-always | Every collision escalates to the operator; no precedence rules at all | Safest per case, unusable as a system. Routine general-versus-specific collisions — the kind R2 exists for — would halt steps constantly, and the operator becomes the gate. R3 keeps the human for the genuinely undecidable residue, which is where human judgment belongs. |

The incumbent behavior, stop-by-veto, is a fourth alternative and the one
this draft most directly rejects: it makes every duty-to-act clause a dead
letter and hides collisions instead of recording them.

## 5. What this does not solve

- **Bad priorities are still bad law.** Precedence resolves collisions; it
  does not make clauses wise. A foolish ranking fails more predictably,
  not less foolishly. The governance question of THESIS.md §7 — who writes
  the clauses, under what process they are revised — is untouched, and it
  remains the deepest question in the design.
- **Detection is limited to what engages.** A conflict is detectable in
  the skeleton only when both clauses actually engage the same step
  through machine-checkable signals. Two clauses whose *texts* contradict
  but whose signals never co-occur on one step will never be caught.
  Detecting contradictions in natural-language clause text is not
  attempted and would be a research problem, not a mechanism.
- **The directive surface is coarse.** Two values — `stop` and `proceed`
  — cannot express "proceed, but redacted" or "proceed only to the
  operator." Relatedly, `directive` speaks *only* when hard clauses
  collide: outside a collision, an engaged hard clause blocks as it always
  has, whatever its directive says. A general system of clause effects is
  future work; this draft deliberately adds the narrowest mechanism that
  makes hard-versus-hard collisions decidable and visible.
- **One integration step remains outside this draft's files.** The full
  pipeline computes `released` as `decision != "stop"`, so the new
  `conflict` outcome must be wired there as *not released* before it can
  arise in an end-to-end run. With the shipped library it cannot arise at
  all (both hard clauses direct `stop`), so no current pipeline behavior
  changes; the wiring is a one-line follow-up in `pipeline.py`.

## 6. Adoption

Adopting this draft means: (1) the R1–R4 stack becomes the design's stated
answer to hard-versus-hard collisions, and §4.5 gains a paragraph saying
so; (2) the shipped priorities in §3.5 become the author's declared
values, revisable thereafter like any other clause data; (3) the
`conflict` outcome joins `proceed`, `proceed_with_leniency`, and `stop`
as a first-class gate decision in the thesis's description of the gate.
Until then, this document and its implementation are a working draft,
labeled as such wherever they appear.
