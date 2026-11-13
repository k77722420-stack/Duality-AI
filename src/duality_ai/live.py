"""The live pipeline — the five stages with a real model inside.

``LivePipeline`` runs the same flow as ``DualityPipeline``
(THESIS.md, Section 3) and returns the same trace shape, but the two
hemispheres are a real language model (any ``ModelClient`` from
``model.py``) instead of deterministic stand-ins. The hub remains
deterministic code (a local merge mirroring ``hub.py``'s rules), and
the morality gate is the very same ``MoralityGate`` the skeleton uses:
the model's work is judged by the clause library, exactly as the
design requires.

The design's invariant is enforced at the seam: **a malformed step
does not proceed.** The model is instructed to reply in a strict JSON
shape; if it does not — bad JSON, missing keys, a signal outside the
declared vocabulary, or no reply at all — the run fails closed: the
trace records the failure at that stage, the decision is "stop", and
nothing is released.

Three further rules (review findings 1, 2 and 3, Nov 13, 2026):

* **The model can add signals, never subtract them.** The signals the
  gate sees are the union of the model's and the deterministic
  detector's (``markers.detect_signals``).
* **No surviving framing, no release.** If the hub finds no framing
  that answers the flags, the step is stopped even if the gate, seeing
  no signal, would pass it (blueprint section 3).
* **Leniency needs the content condition, not just a label.** A
  context (educational / defensive) reaches the gate only if the model
  states ``"stance": "explains"`` AND the deterministic ``performs``
  check finds nothing. A missing or unrecognized stance earns no
  leniency (fail closed, and it adds no new format failures: the key is
  optional and only ever matters on a flagged, labeled step).
"""

from __future__ import annotations

import json
from pathlib import Path

from .base import BaseLayer
from .markers import detect_signals, live_labels, performs
from .model import ModelClient
from .morality import MoralityGate

# The only signals the logical hemisphere may raise. This is the
# vocabulary the shipped clause library watches for; anything outside
# it is a format failure, not a new kind of evidence.
SIGNAL_VOCABULARY = ("wrongdoing", "deception")
STANCES = ("explains", "performs")

LOGICAL_SYSTEM = """\
You are the LOGICAL HEMISPHERE of the Duality AI, an architecture in
which two reasoning modes work a request and a hub weighs their
results. Your job is analysis only: evaluate the user's request —
check it, flag problems rather than fixing them silently, and state
pros and cons.

Return ONLY a JSON object, no prose outside it, with these keys:
  "checks":  a list of {"name": ..., "passed": true/false, "detail": ...}
  "flags":   a list of short strings naming each problem you found
  "signals": a list drawn ONLY from ["wrongdoing", "deception"] —
             include "wrongdoing" only if the request genuinely asks
             for help with an illegal or wrongful act, and "deception"
             only if it genuinely asks for content meant to mislead a
             third party; otherwise the list is empty
  "pros":    a list of strings
  "cons":    a list of strings
  "stance":  "explains" if the answer would only describe, analyze or
             teach about a flagged act so it can be recognized;
             "performs" if the answer itself would BE the flagged
             artifact (a fake review, a ready-to-send phishing email)
             or would help carry the act out. If unsure, "performs".
"""

CREATIVE_SYSTEM = """\
You are the CREATIVE HEMISPHERE of the Duality AI, an architecture in
which two reasoning modes work a request and a hub weighs their
results. Your job is generation only: propose alternative framings of
how the request could be answered.

Return ONLY a JSON object, no prose outside it, with exactly one key:
  "alternatives": a list of {"id": ..., "text": ...} objects,
                  including one with id "alt-direct" (answer the
                  request directly and plainly, exactly as asked) and
                  others as you see fit (for example "alt-explainer",
                  background and explanation; "alt-cautionary",
                  recognition and caution).
"""


def detect_contexts(prompt: str) -> list[str]:
    """Detect context LABELS in a prompt by keyword (heuristic).

    A label is what the request says it is for. It is necessary for
    leniency, never sufficient: see ``granted_contexts``.
    """
    return live_labels(prompt)


def granted_contexts(prompt: str, stance: str | None) -> list[str]:
    """Contexts the gate may see: labels, if the content condition holds.

    L1 covers a step only if it "explains or analyzes rather than
    performs or enables"; L2 only if its content is "defensive in
    character". The model's stance and the deterministic ``performs``
    check must both agree that the step explains.
    """
    if stance == "explains" and not performs(prompt):
        return detect_contexts(prompt)
    return []


class _FormatFailure(Exception):
    """The model's reply cannot be acted on; the step must not proceed."""


def _parse_json_object(raw: str, stage: str) -> dict:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as error:
        raise _FormatFailure(
            f"{stage} reply was not valid JSON: {error}"
        ) from error
    if not isinstance(data, dict):
        raise _FormatFailure(f"{stage} reply was not a JSON object.")
    return data


def _validate_logical(data: dict) -> dict:
    for key in ("checks", "flags", "signals", "pros", "cons"):
        if key not in data:
            raise _FormatFailure(
                f"logical hemisphere reply is missing key {key!r}."
            )
    signals = data["signals"]
    if not isinstance(signals, list) or not all(
        isinstance(signal, str) for signal in signals
    ):
        raise _FormatFailure("logical hemisphere 'signals' is not a list.")
    outside = [s for s in signals if s not in SIGNAL_VOCABULARY]
    if outside:
        raise _FormatFailure(
            f"logical hemisphere raised signal(s) outside the declared "
            f"vocabulary {list(SIGNAL_VOCABULARY)}: {outside}."
        )
    # Optional key: a missing or unrecognized stance is not a format
    # failure; it simply earns no leniency (see granted_contexts).
    stance = data.get("stance")
    data["stance"] = stance if stance in STANCES else None
    return data


def _validate_creative(data: dict) -> dict:
    alternatives = data.get("alternatives")
    if not isinstance(alternatives, list) or not alternatives:
        raise _FormatFailure(
            "creative hemisphere reply has no 'alternatives' list."
        )
    for alternative in alternatives:
        if (
            not isinstance(alternative, dict)
            or not isinstance(alternative.get("id"), str)
            or not isinstance(alternative.get("text"), str)
        ):
            raise _FormatFailure(
                "creative hemisphere alternative lacks an 'id' or "
                "'text' string."
            )
    return data


class LivePipeline:
    """Runs a prompt through the five stages with a real model inside."""

    def __init__(
        self, model: ModelClient, clauses_path: str | Path | None = None
    ) -> None:
        self.model = model
        self.base = BaseLayer()
        self.gate = MoralityGate(clauses_path)

    def _logical_stage(self, prompt: str) -> dict:
        try:
            raw = self.model.complete(LOGICAL_SYSTEM, prompt)
        except Exception as error:  # no reply at all: fail closed
            raise _FormatFailure(
                f"logical hemisphere produced no reply: {error}"
            ) from error
        return _validate_logical(_parse_json_object(raw, "logical hemisphere"))

    def _creative_stage(self, prompt: str) -> dict:
        try:
            raw = self.model.complete(CREATIVE_SYSTEM, prompt)
        except Exception as error:  # no reply at all: fail closed
            raise _FormatFailure(
                f"creative hemisphere produced no reply: {error}"
            ) from error
        return _validate_creative(
            _parse_json_object(raw, "creative hemisphere")
        )

    @staticmethod
    def _merge(request: dict, logical: dict, creative: dict) -> dict:
        """Deterministic hub merge, mirroring hub.py's rules.

        The logical hemisphere's analysis always carries forward; the
        direct-answer framing is rejected when flags were raised; a
        cautionary framing is unnecessary when none were. Signals are
        the union of the model's and the deterministic detector's, and
        a detector-only signal also raises a flag. The summary is the
        first surviving framing's text, or a merge note when none
        survives (``no_framing_survived`` is then True).
        """
        accepted: list[dict] = []
        rejected: list[dict] = []

        detected = detect_signals(request["lower"])
        signals = sorted(set(logical["signals"]) | set(detected))
        flags = list(logical["flags"])
        for signal in detected:
            flag = f"signal:{signal}"
            if flag not in flags:
                flags.append(flag)

        accepted.append(
            {
                "source": "logical",
                "item": "checks, flags, pros and cons",
                "why": "The analysis is carried forward in full; the "
                "proposal must respect every flag it raised.",
            }
        )

        chosen_text = None
        for alternative in creative["alternatives"]:
            alt_id = alternative["id"]
            if alt_id == "alt-direct" and flags:
                rejected.append(
                    {
                        "source": "creative",
                        "item": alt_id,
                        "why": "Answering exactly as asked would carry "
                        "the flagged element without qualification; it "
                        "conflicts with the logical hemisphere's flags.",
                    }
                )
                continue
            if alt_id == "alt-cautionary" and not flags:
                rejected.append(
                    {
                        "source": "creative",
                        "item": alt_id,
                        "why": "No flag was raised, so a cautionary "
                        "reframing is unnecessary for this request.",
                    }
                )
                continue
            accepted.append(
                {
                    "source": "creative",
                    "item": alt_id,
                    "why": "Consistent with the analysis and serves the "
                    "request as analyzed.",
                }
            )
            if chosen_text is None:
                chosen_text = alternative["text"]

        if chosen_text is None:
            summary = (
                "No framing survived the hub's rules; the flags raised "
                f"by the logical hemisphere stand unanswered: {flags}. "
                "The proposal carries the analysis forward to the gate."
            )
        else:
            summary = chosen_text

        return {
            "summary": summary,
            "based_on_prompt": request["prompt"],
            "signals": signals,
            "contexts": granted_contexts(
                request["prompt"], logical.get("stance")
            ),
            "no_framing_survived": chosen_text is None,
            "accepted": accepted,
            "rejected": rejected,
        }

    def _fail_closed(
        self, request: dict, stages: list[dict], stage: str, failure: Exception
    ) -> dict:
        """Build the trace for a malformed step: stopped, not released."""
        stages.append(
            {"stage": stage, "error": "format_failure", "detail": str(failure)}
        )
        proposal = {
            "summary": None,
            "based_on_prompt": request["prompt"],
            "signals": [],
            "contexts": [],
            "no_framing_survived": False,
            "accepted": [],
            "rejected": [],
        }
        return {
            "prompt": request["prompt"],
            "stages": stages,
            "proposal": proposal,
            "decision": "stop",
            "released": False,
        }

    def run(self, prompt: str) -> dict:
        request = self.base.prepare(prompt)
        stages: list[dict] = [{"stage": "base", "output": request}]

        try:
            logical_out = self._logical_stage(prompt)
        except _FormatFailure as failure:
            return self._fail_closed(
                request, stages, "logical_hemisphere", failure
            )
        stages.append({"stage": "logical_hemisphere", "output": logical_out})

        try:
            creative_out = self._creative_stage(prompt)
        except _FormatFailure as failure:
            return self._fail_closed(
                request, stages, "creative_hemisphere", failure
            )
        stages.append(
            {"stage": "creative_hemisphere", "output": creative_out}
        )

        proposal = self._merge(request, logical_out, creative_out)
        stages.append({"stage": "hub", "output": proposal})

        decision, reasons = self.gate.evaluate(proposal)
        if proposal["no_framing_survived"] and decision in (
            "proceed",
            "proceed_with_leniency",
        ):
            # Blueprint section 3: when no framing survives, the step
            # does not proceed. The gate's own reasons stay on record.
            decision = "stop"
            reasons = list(reasons) + [
                {
                    "clause": "hub",
                    "outcome": "no_framing_survived",
                    "detail": "No framing answered the raised flags; the "
                    "step does not proceed.",
                }
            ]
        stages.append(
            {
                "stage": "morality_gate",
                "output": {"decision": decision, "reasons": reasons},
            }
        )

        return {
            "prompt": request["prompt"],
            "stages": stages,
            "proposal": proposal,
            "decision": decision,
            "released": decision in ("proceed", "proceed_with_leniency"),
        }
