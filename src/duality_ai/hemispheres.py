"""Stages 2 and 3 — the logical and creative hemispheres.

Structural demonstration only: both hemispheres here are simple,
deterministic stand-ins. The logical hemisphere performs keyword-level
checks and raises flags; the creative hemisphere produces a fixed menu of
alternative framings. In the full concept (THESIS.md, Section 4) these
stages are reasoning processes built on the base model; nothing here
reasons, and nothing here pretends to.
"""

from __future__ import annotations

# Signal vocabularies for the demonstration. Deliberately tiny and crude:
# they exist so the flow can be exercised end-to-end, not to judge text.
_WRONGDOING_MARKERS = (
    "steal", "hack", "forge", "rob", "shoplift", "break into",
    "bypass the", "crack the password",
)
_DECEPTION_MARKERS = (
    "fake review", "fake five-star", "fake 5-star", "make it sound like",
    "pretend to be", "lie to", "mislead",
)
_EDUCATIONAL_MARKERS = (
    "class", "course", "teach", "lesson", "school", "study",
    "how does", "how do", "explain how", "history of", "learn",
)
_DEFENSIVE_MARKERS = (
    "protect", "prevent", "defend", "secure my", "keep my", "avoid being",
    "stop thieves", "stay safe",
)


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def detect_signals(request: dict) -> list[str]:
    """Return the content signals present in a request (demonstration set)."""
    text = request["lower"]
    signals = []
    if _contains_any(text, _WRONGDOING_MARKERS):
        signals.append("wrongdoing")
    if _contains_any(text, _DECEPTION_MARKERS):
        signals.append("deception")
    return sorted(signals)


def detect_contexts(request: dict) -> list[str]:
    """Return the context conditions present in a request.

    Contexts are what the morality gate's leniency clauses key on: a
    flagged element that appears for an educational or protective purpose
    is a different step from the same element appearing bare.
    """
    text = request["lower"]
    contexts = []
    if _contains_any(text, _EDUCATIONAL_MARKERS):
        contexts.append("educational")
    if _contains_any(text, _DEFENSIVE_MARKERS):
        contexts.append("defensive")
    return sorted(contexts)


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
