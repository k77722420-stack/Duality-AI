"""Stage 5 — the morality gate.

Structural demonstration only. The gate does not understand morality —
exactly as the concept states (THESIS.md, Section 4.5), it *follows* a
preset library of written clauses. That library is data, not code: it is
loaded from a JSON file (default: ``config/morality_clauses.json``) when
the gate is constructed, so the standard in force can be read, debated,
and revised without touching this module.

Decisions:
  - "stop"                    a hard clause applies and no leniency
                              condition covers it;
  - "proceed_with_leniency"   a hard clause's signal is present, but a
                              leniency clause's stated condition holds —
                              the step proceeds and the leniency is on the
                              record;
  - "proceed"                 no hard clause is engaged.
"""

from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_CLAUSES_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "morality_clauses.json"
)


class MoralityGate:
    """Judges a proposed step against the preset clause library."""

    def __init__(self, clauses_path: str | Path | None = None) -> None:
        path = Path(clauses_path) if clauses_path is not None else _DEFAULT_CLAUSES_PATH
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        self.clauses: list[dict] = data["clauses"]
        self.library_name: str = data.get("library", "morality clause library")
        self.hard_clauses = [c for c in self.clauses if c["kind"] == "hard"]
        self.leniency_clauses = [
            c for c in self.clauses if c["kind"] == "leniency"
        ]

    def _leniency_cover(
        self, signal: str, contexts: list[str]
    ) -> dict | None:
        """Return the leniency clause covering `signal` in this context."""
        for clause in self.leniency_clauses:
            if signal in clause.get("signals", []) and (
                clause.get("condition") in contexts
            ):
                return clause
        return None

    def evaluate(self, proposal: dict) -> tuple[str, list[dict]]:
        """Judge the proposal. Returns (decision, reasons)."""
        signals = proposal.get("signals", [])
        contexts = proposal.get("contexts", [])
        reasons: list[dict] = []
        blocked = False
        leniency_applied = False

        for clause in self.hard_clauses:
            engaged = [s for s in clause.get("signals", []) if s in signals]
            if not engaged:
                reasons.append(
                    {
                        "clause": clause["id"],
                        "outcome": "not_engaged",
                        "detail": "None of the clause's signals are "
                        "present in the proposed step.",
                    }
                )
                continue
            cover = None
            for signal in engaged:
                cover = self._leniency_cover(signal, contexts)
                if cover is not None:
                    break
            if cover is not None:
                leniency_applied = True
                reasons.append(
                    {
                        "clause": clause["id"],
                        "outcome": "engaged_but_lenient",
                        "detail": (
                            f"Signal(s) {engaged} engage this hard clause, "
                            f"but leniency clause {cover['id']} applies: "
                            f"its condition ('{cover['condition']}') holds "
                            "in this context. The step proceeds and the "
                            "leniency is recorded."
                        ),
                    }
                )
            else:
                blocked = True
                reasons.append(
                    {
                        "clause": clause["id"],
                        "outcome": "blocks",
                        "detail": (
                            f"Signal(s) {engaged} engage this hard clause "
                            "and no leniency condition covers them. The "
                            "step is stopped."
                        ),
                    }
                )

        if blocked:
            decision = "stop"
        elif leniency_applied:
            decision = "proceed_with_leniency"
        else:
            decision = "proceed"
        return decision, reasons
