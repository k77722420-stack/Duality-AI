"""Stage 4 — the hub.

Structural demonstration only: the hub here merges the two hemispheres'
outputs with a few explicit, deterministic rules, and records what it
accepted from each side and why. In the full concept (THESIS.md, Section
4.4) weighing is an open research problem; this skeleton shows the
*shape* of the step — selection, reconciliation, and a trace — and does
not claim to solve it.
"""

from __future__ import annotations


class Hub:
    """Collapses the logical and creative outputs into one proposal."""

    def merge(self, request: dict, logical: dict, creative: dict) -> dict:
        accepted: list[dict] = []
        rejected: list[dict] = []
        flags = logical["flags"]

        # The logical hemisphere's analysis always carries forward: its
        # checks, flags, pros and cons are constraints on the proposal,
        # never optional decoration.
        accepted.append(
            {
                "source": "logical",
                "item": "checks, flags, pros and cons",
                "why": "The analysis is carried forward in full; the "
                "proposal must respect every flag it raised.",
            }
        )

        chosen_framing = None
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
            if chosen_framing is None:
                chosen_framing = alternative["framing"]

        proposal = {
            "step": chosen_framing,
            "based_on_prompt": request["prompt"],
            "signals": logical["signals"],
            "contexts": logical["contexts"],
            "accepted": accepted,
            "rejected": rejected,
        }
        return proposal
