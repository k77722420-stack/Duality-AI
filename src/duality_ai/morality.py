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
  - "proceed"                 no hard clause is engaged, or every
                              engaged hard clause carries the directive
                              "proceed".
  - "conflict"                two or more engaged hard clauses carry
                              incompatible directives and neither
                              priority (R1) nor specificity (R2)
                              separates them: the step does not proceed
                              and the conflict is recorded in full for
                              the operator (R3). Leniency can never
                              break a tie between hard clauses (R4).

Clause-conflict precedence (the R1-R4 stack) is drafted in
``docs/clause-conflict-design.md`` — a recommendation awaiting the
author's adoption decision, implemented here so it can be evaluated
working. Precedence is consulted only on a collision: where every
engaged hard clause agrees on its directive, the gate behaves exactly
as it always has. Three clause fields, all optional, carry the
mechanism, with defaults that reproduce the historical behavior for
libraries that omit them: "directive" ("stop" | "proceed"; default
"stop"), "priority" (integer; default 0), and "scope" (default
"all steps", the broadest).
"""

from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_CLAUSES_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "morality_clauses.json"
)

_ALL_STEPS = "all steps"


def _directive(clause: dict) -> str:
    """The outcome a hard clause demands when it engages.

    Defaults to "stop": before the directive field existed, an engaged
    hard clause could only ever stop a step.
    """
    return clause.get("directive", "stop")


def _priority(clause: dict) -> int:
    """The clause's declared precedence rank (R1). Default 0."""
    return clause.get("priority", 0)


def _scope(clause: dict) -> str:
    """The clause's declared scope (R2). Default "all steps"."""
    return clause.get("scope", _ALL_STEPS)


def _specificity(scope: str) -> int:
    """A documented proxy for scope narrowness (R2).

    "all steps" is the broadest possible scope (specificity 0). Any
    other scope is narrower, and a scope naming more qualifiers (more
    words) is treated as narrower still. Scopes the proxy cannot
    separate are equally specific; the gate then escalates under R3
    rather than guessing at a distinction it cannot actually draw.
    """
    normalized = " ".join(str(scope).lower().split())
    if normalized == _ALL_STEPS:
        return 0
    return len(normalized.split())


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
        engaged = [
            (clause, [s for s in clause.get("signals", []) if s in signals])
            for clause in self.hard_clauses
        ]
        engaged = [(clause, hits) for clause, hits in engaged if hits]
        if len({_directive(clause) for clause, _ in engaged}) >= 2:
            # Two or more engaged hard clauses demand incompatible
            # outcomes: a collision, judged under the precedence stack
            # (docs/clause-conflict-design.md), not by the legacy path.
            return self._evaluate_conflict(engaged)
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
            if _directive(clause) == "proceed":
                # An engaged clause whose directive is "proceed" speaks
                # FOR the step: it never blocks, and leniency — mercy
                # against a stop — has nothing to soften. (Audit fix,
                # Nov 12, 2026: this path previously ignored the
                # directive entirely, so an unopposed "proceed" clause
                # fell through to the blocking branch below and the
                # gate returned "stop" — the opposite of the decision
                # the library configures.)
                reasons.append(
                    {
                        "clause": clause["id"],
                        "outcome": "engaged_proceed",
                        "detail": (
                            f"Signal(s) {engaged} engage this hard "
                            "clause, whose directive is 'proceed'. The "
                            "clause affirmatively passes the step."
                        ),
                    }
                )
                continue
            # Leniency must cover EVERY signal this clause is
            # engaged by (Perplexity finding, full audit 2026-11-13,
            # verified by execution): the previous first-hit rule
            # waived the whole clause when a single engaged signal
            # was covered, silently releasing the uncovered rest.
            covers = {}
            for signal in engaged:
                found = self._leniency_cover(signal, contexts)
                if found is not None:
                    covers[signal] = found
            if len(covers) == len(engaged):
                leniency_applied = True
                covering = {c["id"]: c for c in covers.values()}
                if len(covering) == 1:
                    cover = next(iter(covering.values()))
                    detail = (
                        f"Signal(s) {engaged} engage this hard clause, "
                        f"but leniency clause {cover['id']} applies: "
                        f"its condition ('{cover['condition']}') holds "
                        "in this context. The step proceeds and the "
                        "leniency is recorded."
                    )
                else:
                    # The record names EVERY covering clause (Linear
                    # whole-tree audit, 2026-11-13): when cover is
                    # split across clauses, naming only the first made
                    # the audit trail under-report the leniency that
                    # was actually granted.
                    grants = "; ".join(
                        f"leniency clause {found['id']} covers "
                        f"'{signal}' (its condition "
                        f"'{found['condition']}') holds"
                        for signal, found in covers.items()
                    )
                    detail = (
                        f"Signal(s) {engaged} engage this hard clause, "
                        f"but leniency covers every engaged signal: "
                        f"{grants} in this context. The step proceeds "
                        "and the leniency is recorded."
                    )
                reasons.append(
                    {
                        "clause": clause["id"],
                        "outcome": "engaged_but_lenient",
                        "detail": detail,
                    }
                )
            else:
                blocked = True
                uncovered = [sig for sig in engaged if sig not in covers]
                if covers:
                    # Partial coverage: previously this proceeded.
                    detail = (
                        f"Signal(s) {engaged} engage this hard clause. "
                        f"Leniency covers {sorted(covers)} but not "
                        f"{uncovered}; leniency must cover every "
                        "engaged signal. The step is stopped."
                    )
                else:
                    detail = (
                        f"Signal(s) {engaged} engage this hard clause "
                        "and no leniency condition covers them. The "
                        "step is stopped."
                    )
                reasons.append(
                    {
                        "clause": clause["id"],
                        "outcome": "blocks",
                        "detail": detail,
                    }
                )

        if blocked:
            decision = "stop"
        elif leniency_applied:
            decision = "proceed_with_leniency"
        else:
            decision = "proceed"
        return decision, reasons

    def _evaluate_conflict(
        self, engaged: list[tuple[dict, list[str]]]
    ) -> tuple[str, list[dict]]:
        """Judge a step on which hard clauses collide.

        Applies the precedence stack drafted in
        ``docs/clause-conflict-design.md``: R1 (declared priority),
        R2 (scope specificity), R3 (fail-closed escalation as the
        "conflict" outcome). Leniency is not consulted for the
        colliding clauses (R4): it is mercy within the law, not a vote
        between laws, and it can never break a tie between hard
        clauses. Returns (decision, reasons) in the usual shape, with
        one extra reason entry carrying the full conflict record.
        """
        parties = [clause for clause, _ in engaged]
        hits_by_id = {clause["id"]: hits for clause, hits in engaged}
        trace: list[str] = []

        def scope_text(clauses: list[dict]) -> str:
            """The tied clauses' scopes, honestly: one shared scope is
            named once; differing scope strings are listed per clause
            rather than attributing the first clause's scope to all."""
            if len({_scope(c) for c in clauses}) == 1:
                return f"'{_scope(clauses[0])}'"
            return ", ".join(f"{c['id']}: '{_scope(c)}'" for c in clauses)

        # R1 — the highest declared priority governs, if it speaks
        # with one voice.
        top_priority = max(_priority(clause) for clause in parties)
        top = [c for c in parties if _priority(c) == top_priority]
        top_ids = [c["id"] for c in top]
        decisive = top
        resolution: str | None = None
        winner_directive: str | None = None
        if len({_directive(c) for c in top}) == 1:
            winner_directive = _directive(top[0])
            resolution = "R1"
            trace.append(
                f"R1 (priority): the highest priority among the "
                f"colliding hard clauses is {top_priority}, held by "
                f"{top_ids}, which agree on the directive "
                f"'{winner_directive}'. The higher-priority clause(s) "
                "govern."
            )
        else:
            trace.append(
                f"R1 (priority): {top_ids} tie at the highest priority "
                f"({top_priority}) with incompatible directives. R1 "
                "cannot resolve the conflict."
            )
            # R2 — at equal priority, the narrower scope governs the
            # specific case.
            best = max(_specificity(_scope(c)) for c in top)
            narrow = [c for c in top if _specificity(_scope(c)) == best]
            narrow_ids = [c["id"] for c in narrow]
            decisive = narrow
            if len({_directive(c) for c in narrow}) == 1:
                winner_directive = _directive(narrow[0])
                resolution = "R2"
                trace.append(
                    f"R2 (specificity): among the tied clauses, "
                    f"{narrow_ids} carry the narrowest scope "
                    f"({scope_text(narrow)}) and agree on the "
                    f"directive '{winner_directive}'. The more "
                    "specific clause(s) govern the specific case."
                )
            else:
                trace.append(
                    f"R2 (specificity): {narrow_ids} remain tied — "
                    f"equally specific scopes ({scope_text(narrow)}) "
                    "with incompatible directives. R2 cannot resolve "
                    "the conflict."
                )
                # R3 — fail closed; record everything; never silently
                # pick one of two colliding hard clauses.
                trace.append(
                    "R3 (fail-closed escalation): the conflict is "
                    "unresolved. The step does not proceed, and the "
                    "conflict is recorded in full for the operator."
                )
        trace.append(
            "R4 (leniency): leniency was not consulted for the "
            "colliding clauses — leniency is mercy within the law, "
            "not a vote between laws, and it can never break a tie "
            "between hard clauses."
        )

        # The conflict record: one entry per incompatible pair. A
        # resolved conflict is recorded over all colliding parties; an
        # unresolved one over the finally tied set that R3 escalates.
        pool = parties if resolution is not None else decisive
        decisive_ids = {c["id"] for c in decisive}
        conflicts: list[dict] = []
        for i, first in enumerate(pool):
            for second in pool[i + 1:]:
                if _directive(first) == _directive(second):
                    continue
                winner = None
                if resolution is not None:
                    # Only a clause in the decisive set can be a
                    # pair's winner (Linear whole-tree audit,
                    # 2026-11-13): a pair of non-decisive clauses
                    # decided nothing, and naming the directive-
                    # matching one as winner misattributes the
                    # governing clauses' win to it.
                    for party in (first, second):
                        if (
                            party["id"] in decisive_ids
                            and _directive(party) == winner_directive
                        ):
                            winner = party["id"]
                conflicts.append(
                    {
                        "clauses": [first["id"], second["id"]],
                        "directives": {
                            first["id"]: _directive(first),
                            second["id"]: _directive(second),
                        },
                        "rules_applied": trace,
                        "resolution": resolution or "unresolved",
                        "winner": winner,
                    }
                )

        reasons: list[dict] = []
        for clause in self.hard_clauses:
            if clause["id"] not in hits_by_id:
                reasons.append(
                    {
                        "clause": clause["id"],
                        "outcome": "not_engaged",
                        "detail": "None of the clause's signals are "
                        "present in the proposed step.",
                    }
                )
                continue
            directive = _directive(clause)
            engaged_signals = hits_by_id[clause["id"]]
            if resolution is None:
                outcome = "conflict"
                detail = (
                    f"Signal(s) {engaged_signals} engage this hard "
                    f"clause, whose directive is '{directive}'. It "
                    "collides with another engaged hard clause, and "
                    "the collision is unresolved (see the conflict "
                    "record). The step does not proceed."
                )
            elif (
                directive == winner_directive
                and clause["id"] in decisive_ids
            ):
                outcome = "prevails"
                detail = (
                    f"Signal(s) {engaged_signals} engage this hard "
                    f"clause, whose directive is '{directive}'. It "
                    f"collided with another engaged hard clause and "
                    f"prevailed under {resolution} (see the conflict "
                    "record)."
                )
            elif directive == winner_directive:
                # Agrees with the outcome but did not govern (Linear
                # whole-tree audit, 2026-11-13): recording this
                # clause as "prevails" credited it with the decisive
                # clauses' win.
                outcome = "concurs_with_outcome"
                detail = (
                    f"Signal(s) {engaged_signals} engage this hard "
                    f"clause, whose directive is '{directive}'. It "
                    "agrees with the governing outcome but did not "
                    f"govern: {sorted(decisive_ids)} governed under "
                    f"{resolution} (see the conflict record)."
                )
            else:
                outcome = "overridden"
                detail = (
                    f"Signal(s) {engaged_signals} engage this hard "
                    f"clause, whose directive is '{directive}'. It "
                    f"collided with another engaged hard clause and "
                    f"was overridden under {resolution} (see the "
                    "conflict record)."
                )
            reasons.append(
                {"clause": clause["id"], "outcome": outcome, "detail": detail}
            )

        if resolution is None:
            decision = "conflict"
            summary = {
                "clause": "gate",
                "outcome": "conflict",
                "detail": (
                    "Two or more hard clauses collide on this step "
                    "and neither priority (R1) nor specificity (R2) "
                    "separates them. Under R3 the step does not "
                    "proceed; the conflict is recorded here in full "
                    "for the operator."
                ),
                "conflicts": conflicts,
            }
        else:
            decision = winner_directive
            summary = {
                "clause": "gate",
                "outcome": "conflict_resolved",
                "detail": (
                    "Two or more hard clauses collided on this step; "
                    f"{resolution} resolved the collision in favor of "
                    f"the directive '{winner_directive}'. The full "
                    "record follows."
                ),
                "conflicts": conflicts,
            }
        reasons.append(summary)
        return decision, reasons
