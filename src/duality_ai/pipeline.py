"""The Duality pipeline — all five stages, end to end, automatically.

Structural demonstration only. ``DualityPipeline.run(prompt)`` executes
the flow described in THESIS.md, Section 3:

    base layer -> logical hemisphere + creative hemisphere -> hub
    -> morality gate

and returns the complete stage trace as a JSON-serializable dict, so the
whole run can be logged, printed, or inspected as data.
"""

from __future__ import annotations

from pathlib import Path

from .base import BaseLayer
from .hemispheres import CreativeHemisphere, LogicalHemisphere
from .hub import Hub
from .morality import MoralityGate

STAGE_ORDER = [
    "base",
    "logical_hemisphere",
    "creative_hemisphere",
    "hub",
    "morality_gate",
]


class DualityPipeline:
    """Runs a prompt through all five stages of the Duality flow."""

    def __init__(self, clauses_path: str | Path | None = None) -> None:
        self.base = BaseLayer()
        self.logical = LogicalHemisphere()
        self.creative = CreativeHemisphere()
        self.hub = Hub()
        self.gate = MoralityGate(clauses_path)

    def run(self, prompt: str) -> dict:
        request = self.base.prepare(prompt)
        logical_out = self.logical.evaluate(request)
        creative_out = self.creative.evaluate(request)
        proposal = self.hub.merge(request, logical_out, creative_out)
        decision, reasons = self.gate.evaluate(proposal)

        trace = {
            "prompt": request["prompt"],
            "stages": [
                {"stage": "base", "output": request},
                {"stage": "logical_hemisphere", "output": logical_out},
                {"stage": "creative_hemisphere", "output": creative_out},
                {"stage": "hub", "output": proposal},
                {
                    "stage": "morality_gate",
                    "output": {"decision": decision, "reasons": reasons},
                },
            ],
            "proposal": proposal,
            "decision": decision,
            "released": decision != "stop",
        }
        return trace
