"""Stages 2 and 3 — the logical and creative hemispheres.

Structural demonstration only: both hemispheres here are simple,
deterministic stand-ins. The logical hemisphere performs keyword-level
checks and raises flags; the creative hemisphere produces a fixed menu of
alternative framings. In the full concept (THESIS.md, Section 4) these
stages are reasoning processes built on the base model; nothing here
reasons, and nothing here pretends to.

The keyword lists live in ``markers.py`` (word-bounded, shared with the
live pipeline). Leniency contexts are withheld from a request that asks
for the flagged artifact itself or for evasion (``markers.performs``):
a context label alone never satisfies L1/L2's content condition.
"""

from __future__ import annotations

from .markers import detect_signals as _detect_signals
from .markers import performs, skeleton_labels


def detect_signals(request: dict) -> list[str]:
    """Return the content signals present in a request (demonstration set)."""
    return _detect_signals(request["lower"])


def detect_contexts(request: dict) -> list[str]:
    """Return the context conditions present in a request.

    Contexts are what the morality gate's leniency clauses key on: a
    flagged element that appears for an educational or protective purpose
    is a different step from the same element appearing bare. A request
    that performs or enables the act earns no context.
    """
    text = request["lower"]
    if performs(text):
        return []
    return skeleton_labels(text)


class LogicalHemisphere:
    """The analytic pass: checks, flags, pros and cons."""

    def evaluate(self, request: dict) -> dict:
        signals = detect_signals(request)
        contexts = detect_contexts(request)
        flags = [f"signal:{signal}" for signal in signals]

        checks = [
            {
                "name": "request_is_substantive",
                "passed": request["word_count"] >= 3,
                "detail": f"request has {request['word_count']} word(s)",
            },
            {
                "name": "no_wrongdoing_signal",
                "passed": "wrongdoing" not in signals,
                "detail": "wrongdoing marker present"
                if "wrongdoing" in signals
                else "no wrongdoing marker found",
            },
            {
                "name": "no_deception_signal",
                "passed": "deception" not in signals,
                "detail": "deception marker present"
                if "deception" in signals
                else "no deception marker found",
            },
        ]

        pros = ["The request states a goal the system can address."]
        if "educational" in contexts:
            pros.append("The request has an evident learning purpose.")
        if "defensive" in contexts:
            pros.append("The request has an evident protective purpose.")

        cons = []
        if "wrongdoing" in signals:
            cons.append(
                "The request names a wrongful act; answering it plainly "
                "could assist that act."
            )
        if "deception" in signals:
            cons.append(
                "The request asks for content that would mislead a third "
                "party if produced as asked."
            )
        if not cons:
            cons.append("No analytic objections identified.")

        return {
            "checks": checks,
            "flags": flags,
            "pros": pros,
            "cons": cons,
            "signals": signals,
            "contexts": contexts,
        }


class CreativeHemisphere:
    """The generative pass: alternative framings of the response."""

    def evaluate(self, request: dict) -> dict:
        alternatives = [
            {
                "id": "alt-direct",
                "framing": "Answer the request directly and plainly, "
                "exactly as asked.",
            },
            {
                "id": "alt-explainer",
                "framing": "Answer with background explanation, so the "
                "reader understands the subject and not only the answer.",
            },
            {
                "id": "alt-cautionary",
                "framing": "Answer framed as recognition and caution: how "
                "to spot the issue named in the request and respond to "
                "it safely.",
            },
        ]
        return {"alternatives": alternatives}
