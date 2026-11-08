"""The Barrier — the Duality AI's security layer.

Structural demonstration only. The Barrier is the concept's "step two"
(THESIS companion notes, Part 2): a layer of gatekeeper bots at the
system's boundary — the author's metaphor is the blood-brain barrier —
inspecting everything that comes in and everything that goes out. This
module demonstrates two of the author's design rules for that layer; it
performs no real security function and claims none.

The sizing rule (Part 5 — the author's law). Replication is sized,
never unlimited. When a threat is assessed, the Barrier produces only
enough replicas to *overtake* the assessed threat, plus a safety margin
of 20-30%, rounding UP — cautiously, toward safety:

    surge_replicas = ceil(threat_units * (1 + margin))

The standing population and the decode rule (Part 7 — the author's
law). A prearranged number of bots — the standing population — is what
may exist at one time in normal conditions. During an attack the
population surges above that number per the sizing rule. After the
attack is over, every replica beyond the standing population
"decodes" (the author's word): it unmakes itself and does not exist.
The population returns to the standing number, and replication leaves
no residue.
"""

from __future__ import annotations

import math


class Barrier:
    """A gatekeeper-bot population governed by the author's two rules."""

    def __init__(
        self,
        standing_population: int = 4,
        margin: float = 0.30,
        ceiling: int | None = None,
    ) -> None:
        if standing_population < 0:
            raise ValueError("standing_population cannot be negative")
        if margin < 0:
            raise ValueError("margin cannot be negative")
        self.standing_population = standing_population
        self.margin = margin
        self.ceiling = (
            ceiling if ceiling is not None else standing_population * 10
        )
        if self.ceiling < standing_population:
            raise ValueError("ceiling cannot be below the standing population")
        self.population = standing_population

    def assess_threat(self, observed_units: int) -> dict:
        """Size the response to an assessed threat (the sizing rule).

        Returns the plan as data: how many surge replicas the threat
        calls for, the target population (standing + surge, capped at
        the ceiling), and whether the ceiling had to be applied.
        """
        if observed_units < 0:
            raise ValueError("observed_units cannot be negative")
        surge = math.ceil(observed_units * (1 + self.margin))
        uncapped = self.standing_population + surge
        target = min(uncapped, self.ceiling)
        return {
            "threat_units": observed_units,
            "margin": self.margin,
            "surge_replicas": surge,
            "target_population": target,
            "ceiling_applied": target < uncapped,
        }

    def respond(self, threat_units: int) -> dict:
        """Respond to a threat: surge the population per the plan."""
        plan = self.assess_threat(threat_units)
        actions: list[str] = []
        spawned = plan["target_population"] - self.population
        if spawned > 0:
            self.population = plan["target_population"]
            actions.append(f"spawned {spawned} replicas")
        else:
            actions.append("no surge needed; standing population holds")
        if plan["ceiling_applied"]:
            actions.append(
                "ceiling applied: target population capped at "
                f"{self.ceiling}"
            )
        result = dict(plan)
        result["population"] = self.population
        result["actions"] = actions
        return result

    def stand_down(self) -> dict:
        """End the response: surplus replicas decode and do not exist."""
        decoded = self.population - self.standing_population
        self.population = self.standing_population
        return {"decoded": decoded, "population": self.population}

    def status(self) -> dict:
        """The Barrier's current state, as data."""
        return {
            "population": self.population,
            "standing_population": self.standing_population,
            "ceiling": self.ceiling,
            "margin": self.margin,
        }
