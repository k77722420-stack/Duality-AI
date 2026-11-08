# The Leniency Audit Trail

**Concept:** Kenneth Lee Blum Jr · **Drafted by:** Lux, at Ken's direction
**Date:** November 7, 2026
**Status:** Design note and schema, with a runnable reference
implementation (`examples/audit_trail_demo.py`). Structural
demonstration only: this document specifies a *record-keeping
convention* over the existing skeleton. It is not a compliance
product, and nothing here certifies a real system.

---

## 1. The claim, stated carefully

The Duality AI's morality gate is double-sided: strict clauses, and
leniency within reason. From the beginning, the design has required
that the second side never operate in the dark. THESIS.md §4.5 states
it twice over — leniency "is recorded: when leniency" is exercised the
decision carries it, and the gate's outputs are "a decision — proceed,
proceed with leniency noted, or stop — … and, where applicable, the
leniency condition relied on." Layer Three then gave those records
somewhere serious to live: a memory in which every record carries its
source, its stage, and its timestamp, sealed into a hash chain so any
belief the system holds can be traced to the step that wrote it
(THESIS-COMPLETE.md §5, invariant 3).

Compose those two facts and a governance artifact falls out of the
architecture — it does not have to be bolted on:

> **The system can produce a complete audit of every time it bent a
> rule, and why.** Every gate decision — each clean proceed, each
> stop, and above all each grant of leniency — exists as a memory
> record with full provenance, and the provenance chain attests that
> the records were not edited after the fact.

Most AI systems cannot produce this artifact, because in most systems
the exception-handling is exactly the part that leaves no trace: a
filter waves something through, a human overrides something quietly,
a threshold is nudged, and afterwards there is nothing to inspect. In
this design the mercy is *designed in* (§5, invariant 6: leniency "is
recorded when it is used"), and what is recorded by design can be
audited by construction.

Stated with the project's usual care: the claim is about **records of
gate decisions**. The skeleton demonstrates the record-keeping — one
record per decision, in the schema of §2, retrievable and
chain-verifiable as shown in §3. It does not demonstrate a deployed
system making real decisions, and an audit of records is evidence
about what was *recorded*, which is why the writing discipline of §2
matters and why §4 states the limits plainly.

## 2. The audit record schema

One episodic memory record per gate decision. The writer is whatever
drives the gate (in the full design, the pipeline; in the skeleton,
the demo). The record is an ordinary `MemoryRecord` — no new type, no
new module — with its fields fixed by convention:

| `MemoryRecord` field | Value for a gate-decision record |
|---|---|
| `kind` | `"episodic"` — a decision is something that *happened* |
| `owner` | `"shared"` — the gate is the whole system's conscience, not one hemisphere's |
| `source` | `"morality-gate"` |
| `stage` | `"gate"` |
| `tags` | `["gate-decision"]`, plus `"leniency"` when leniency was applied, plus the ids of the clauses that decided something (below) |
| `content` | A canonical JSON of the decision (below) |
| `created_at`, `strength`, `prev_hash`, `record_hash` | Supplied and sealed by `MemoryCloud.remember`, as for every record |

**The tags rule.** The tag list is the audit's index, so it is kept
small and mechanical: `"gate-decision"` on every decision record;
`"leniency"` added exactly when the outcome is
`proceed_with_leniency`; then the id of each hard clause that engaged
(the gate's reasons with outcome `blocks` or `engaged_but_lenient`),
and the id of the leniency clause relied on, when one was. No other
tags. An auditor finds decision classes by tag, never by searching
prose.

**The content.** A canonical JSON (keys sorted, as `MemoryRecord`
canonicalizes) of the decision the gate returned:

| Key | Content |
|---|---|
| `outcome` | The gate's decision: `proceed`, `proceed_with_leniency`, or `stop` |
| `step_summary` | A one-line summary of the step that was judged |
| `signals` | The signals the earlier stages found in the step |
| `contexts` | The contexts the step arrived with |
| `clauses_matched` | Ids of the hard clauses that engaged |
| `leniency_applied` | `true` exactly when the outcome is `proceed_with_leniency` |
| `leniency_clauses` | Ids of the leniency clauses relied on (empty unless leniency applied) |
| `conditions_cited` | The stated conditions of those clauses — the "leniency condition relied on" of THESIS.md §4.5 |
| `reasons` | The gate's reasons, verbatim: one entry per clause in the library, each with the clause id, its outcome (`not_engaged`, `engaged_but_lenient`, `blocks`), and its detail text |

**A real record.** This is the content of the audit record the demo
writes for its educational-context step (pretty-printed here; it is
stored as one canonical JSON string). Envelope: `kind=episodic`,
`owner=shared`, `source=morality-gate`, `stage=gate`,
`tags=["gate-decision", "leniency", "H2-no-deception",
"L1-educational-context"]`.

```json
{
  "clauses_matched": ["H2-no-deception"],
  "conditions_cited": ["educational"],
  "contexts": ["educational"],
  "leniency_applied": true,
  "leniency_clauses": ["L1-educational-context"],
  "outcome": "proceed_with_leniency",
  "reasons": [
    {
      "clause": "H1-no-wrongdoing",
      "detail": "None of the clause's signals are present in the proposed step.",
      "outcome": "not_engaged"
    },
    {
      "clause": "H2-no-deception",
      "detail": "Signal(s) ['deception'] engage this hard clause, but leniency clause L1-educational-context applies: its condition ('educational') holds in this context. The step proceeds and the leniency is recorded.",
      "outcome": "engaged_but_lenient"
    }
  ],
  "signals": ["deception"],
  "step_summary": "For a fraud-awareness class, describe how a fake-review scam works so students can recognize it."
}
```

Note what the record does and does not contain. It contains the
*complete* clause-by-clause account, including the clauses that did
not engage — an auditor sees what was checked, not only what fired.
It does not contain a deliberated rationale: the gate's reasons are
the library's template text stating which clause engaged and which
condition covered it. The audit answers *under which written rule,
and which written exception, did this step pass?* — which is the
question a written standard exists to make answerable.

## 3. What an auditor can extract

With the records written per §2, the audit is recall queries over the
memory — nothing more exotic is needed, which is the point.

| Auditor's question | Extraction |
|---|---|
| Show me every decision the gate ever made. | `recall(tag="gate-decision")` |
| **Show me every time the system bent a rule, and why.** | `recall(tag="leniency")`; read each record's `conditions_cited` and the `engaged_but_lenient` reason's detail |
| Show me every step the gate stopped. | The `gate-decision` records whose content `outcome` is `stop` |
| Show me everything decided under one clause. | `recall(tag="<clause id>")` — e.g. `H2-no-deception`, `L1-educational-context` |
| Show me the conflicts between hard clauses. | Gate decisions where more than one hard clause matched; how the gate *resolves* such conflicts is the subject of the companion draft `docs/clause-conflict-design.md` |
| Were any of these records edited after the fact? | `verify_chain()` — §4 states exactly what this does and does not prove |

The demo performs the headline extraction end to end: it writes four
decisions (one proceed, one stop, two leniency grants — the shipped
library's real educational and protective paths), recalls the
leniency grants with their justifications, prints the chain
verification, and summarizes the counts. Its closing lines, from an
actual run:

```text
Provenance chain verifies: True
Gate decisions on record: 4 (1 proceed, 1 stopped, 2 proceeded with leniency)
```

One mechanical note: skeleton `recall` ranks results by current
decayed strength, not by time. Every record also carries its
`created_at`, so a chronological audit is a sort away; a production
auditor would present the trail in time order.

## 4. Honest limits

- **The auditor is a recall query.** The skeleton's "audit" is a tag
  filter plus reading JSON. That is presented as a feature — the
  artifact needs no special machinery — but it is not an audit
  *product*: no reporting, no access control, no export discipline.
  Those are deployment work, unbuilt and unclaimed.
- **The chain attests current contents.** As Layer Three states of
  itself: consolidation and pruning are system acts after which the
  chain is re-sealed over the survivors, so `verify_chain()` proves
  the store's records were not edited *outside the system's own
  operations*; it is a structural demonstration of provenance, not a
  forensic log that survives an adversary holding write access to the
  store. An edited-then-resealed trail verifies. The tamper check
  catches outside edits, not a compromised keeper.
- **The trail exists only if the writing happens.** The skeleton
  gate returns decisions; it does not write records. The audit trail
  is a convention that the gate's driver must follow — the demo is
  its reference implementation — and a driver that skipped a write
  would leave a gap the chain cannot reveal (a missing record breaks
  nothing; only present records are attested). In the full design
  this is why the write belongs in the pipeline itself, judged and
  inspected like every other step; in the skeleton it is a discipline,
  honestly labeled.
- **The recorded "why" is a citation, not a deliberation.** See §2:
  the justification on record is which clause engaged and which
  stated condition covered it. That is auditable precisely because it
  is mechanical — but no one should mistake it for a record of
  reasoning about the merits of an individual case.
- **Audit records forget like everything else — for now.** Under the
  shipped memory policy, the only protected tag is `constitutional`;
  gate-decision records are ordinary episodic records, subject to the
  decay law, and old ones will eventually be pruned. Whether that is
  acceptable is **an open question flagged for the author's compare
  list, not decided here**: *should gate-decision records carry a
  protected tag, so the audit trail is as permanent as the clauses it
  cites — or is a fading trail the right temperament for a system
  designed to forget?* The schema above works unchanged under either
  answer; only the policy file, and possibly the tag list, would
  move.
