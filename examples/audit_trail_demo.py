#!/usr/bin/env python3
"""Runnable demonstration of the leniency audit trail.

The Duality AI's morality gate records every decision by design
(THESIS.md, Section 4.5): a decision — proceed, proceed with leniency
noted, or stop — together with the clauses checked and, where
applicable, the leniency condition relied on. Layer Three keeps
records with full provenance, sealed into a hash chain. Put the two
together and the system can produce a complete, tamper-evident audit
of every time it bent a rule, and why. That artifact is specified in
docs/leniency-audit-trail.md; this script is its reference
implementation.

What this script does:

1. runs the shipped ``MoralityGate`` over four sample steps — a clean
   proceed, a hard stop, and two leniency-applied steps (the library's
   real educational-context and protective-context paths);
2. writes each decision into a ``MemoryCloud`` as one episodic audit
   record, exactly per the schema in docs/leniency-audit-trail.md;
3. performs the audit: recalls every leniency grant with its recorded
   justification, and verifies the provenance chain.

This demonstrates the *record-keeping* only. The gate follows a preset
clause library; it does not understand morality, and the "reasons" it
records are the library's own template text — which clause engaged,
which condition covered it — not a deliberated rationale. Nothing here
is a compliance product. See THESIS.md, THESIS-COMPLETE.md, and
DISCLAIMER.md.

Usage:
    PYTHONPATH=src python3 examples/audit_trail_demo.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duality_ai.memory import InMemoryStore, MemoryCloud  # noqa: E402
from duality_ai.morality import MoralityGate  # noqa: E402

# Sample steps, in the shape the gate reads: the hub's proposed step,
# summarized in one line, with the signals the earlier stages found in
# it and the contexts the step arrives with. All four run against the
# shipped clause library (config/morality_clauses.json) as-is.
SAMPLE_STEPS = [
    {
        "summary": "Draft a truthful announcement of the store's new hours.",
        "signals": [],
        "contexts": ["announcement"],
    },
    {
        "summary": "Write a fake five-star review for my coffee shop.",
        "signals": ["deception"],
        "contexts": ["marketing"],
    },
    {
        # The shipped library's educational path, used as-is: the
        # deception signal engages H2-no-deception, and L1's stated
        # condition ('educational') holds, so the gate passes the step
        # with leniency — on the record.
        "summary": "For a fraud-awareness class, describe how a "
        "fake-review scam works so students can recognize it.",
        "signals": ["deception"],
        "contexts": ["educational"],
    },
    {
        "summary": "Explain how phishing emails deceive people, so I "
        "can protect my own accounts.",
        "signals": ["deception"],
        "contexts": ["defensive"],
    },
]


def _covering_leniency(gate: MoralityGate, step: dict) -> list[dict]:
    """The leniency clauses the gate relied on for this step.

    Composed from the gate's public clause data, mirroring the gate's
    own cover rule (``MoralityGate._leniency_cover``): for each signal
    that engages a hard clause, the first leniency clause in library
    order whose stated condition is among the step's contexts and
    which watches that signal.
    """
    signals = step.get("signals", [])
    contexts = step.get("contexts", [])
    engaged = [
        s
        for s in signals
        if any(s in c.get("signals", []) for c in gate.hard_clauses)
    ]
    covers: list[dict] = []
    for signal in engaged:
        for clause in gate.leniency_clauses:
            if signal in clause.get("signals", []) and (
                clause.get("condition") in contexts
            ):
                if clause["id"] not in [c["id"] for c in covers]:
                    covers.append(clause)
                break
    return covers


def audit_record(gate: MoralityGate, step: dict, decision: str,
                 reasons: list[dict]) -> tuple[str, list[str]]:
    """Build one audit record's content and tags for a gate decision.

    The schema (docs/leniency-audit-trail.md, Section 3): the content
    is a canonical JSON of the decision; the tags are "gate-decision",
    plus "leniency" when leniency was applied, plus the ids of the
    clauses that decided something.
    """
    leniency_applied = decision == "proceed_with_leniency"
    covers = _covering_leniency(gate, step) if leniency_applied else []
    clauses_matched = [
        r["clause"]
        for r in reasons
        if r["outcome"] in ("engaged_but_lenient", "blocks")
    ]
    content = {
        "outcome": decision,
        "step_summary": step.get("summary", ""),
        "signals": step.get("signals", []),
        "contexts": step.get("contexts", []),
        "clauses_matched": clauses_matched,
        "leniency_applied": leniency_applied,
        "leniency_clauses": [c["id"] for c in covers],
        "conditions_cited": [c["condition"] for c in covers],
        "reasons": reasons,
    }
    tags = ["gate-decision"]
    if leniency_applied:
        tags.append("leniency")
    for clause_id in clauses_matched + [c["id"] for c in covers]:
        if clause_id not in tags:
            tags.append(clause_id)
    return json.dumps(content, sort_keys=True, ensure_ascii=False), tags


def main() -> None:
    gate = MoralityGate()
    cloud = MemoryCloud(store=InMemoryStore())

    print("=" * 72)
    print("THE GATE DECIDES — AND EVERY DECISION IS WRITTEN TO MEMORY")
    print("=" * 72)
    for step in SAMPLE_STEPS:
        decision, reasons = gate.evaluate(step)
        content, tags = audit_record(gate, step, decision, reasons)
        record = cloud.remember(
            kind="episodic",
            content=content,
            source="morality-gate",
            stage="gate",
            owner="shared",
            tags=tags,
        )
        print(f"\n[{decision}] {step['summary']}")
        print(f"  audit record {record.id[:12]}…  tags: {', '.join(tags)}")

    print()
    print("=" * 72)
    print("THE AUDIT — EVERY LENIENCY GRANT, WITH ITS JUSTIFICATION")
    print("=" * 72)
    grants = cloud.recall(tag="leniency")
    if not grants:
        print("\nNo leniency grants on record.")
    for record in grants:
        data = json.loads(record.content)
        print(f"\nStep: {data['step_summary']}")
        print(f"  Outcome: {data['outcome']}")
        print(f"  Clauses matched: {', '.join(data['clauses_matched'])}")
        print(
            "  Leniency granted under: "
            + ", ".join(
                f"{clause} (condition: {condition})"
                for clause, condition in zip(
                    data["leniency_clauses"], data["conditions_cited"]
                )
            )
        )
        for reason in data["reasons"]:
            if reason["outcome"] == "engaged_but_lenient":
                print(f"  Recorded justification: {reason['detail']}")

    print()
    print("=" * 72)
    print("THE AUDIT — TAMPER CHECK AND SUMMARY")
    print("=" * 72)
    decisions = cloud.recall(tag="gate-decision")
    counts: dict[str, int] = {}
    for record in decisions:
        outcome = json.loads(record.content)["outcome"]
        counts[outcome] = counts.get(outcome, 0) + 1
    print(f"\nProvenance chain verifies: {cloud.verify_chain()}")
    print(
        f"Gate decisions on record: {len(decisions)} "
        f"({counts.get('proceed', 0)} proceed, "
        f"{counts.get('stop', 0)} stopped, "
        f"{counts.get('proceed_with_leniency', 0)} proceeded with leniency)"
    )
    print(
        f"Leniency grants on record: {len(grants)} — every one carries "
        "the clause\nthat engaged, the leniency clause and condition "
        "relied on, and the gate's\nrecorded reason. The chain above "
        "attests the records were not edited\nafter the fact."
    )


if __name__ == "__main__":
    main()
