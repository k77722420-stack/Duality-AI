"""Tests for the Barrier structural demonstration.

These tests verify the author's two design rules as implemented in the
skeleton: the sizing rule (Part 5 — replicas overtake the assessed
threat plus a 20-30% margin, rounding up cautiously, capped at an
absolute ceiling) and the standing-population / decode rule (Part 7 —
after the attack, surplus replicas decode and the population returns
to the prearranged standing number). They test the demonstration's
arithmetic and bookkeeping — not any real security capability.
"""

import json

from duality_ai.barrier import Barrier


def test_sizing_rule_margin_30_percent():
    # A high explicit ceiling keeps the cap out of the pure sizing check.
    barrier = Barrier(standing_population=4, margin=0.30, ceiling=10_000)
    plan = barrier.assess_threat(100)
    assert plan["threat_units"] == 100
    assert plan["margin"] == 0.30
    assert plan["surge_replicas"] == 130
    assert plan["target_population"] == 4 + 130
    assert plan["ceiling_applied"] is False


def test_sizing_rule_margin_20_percent():
    barrier = Barrier(standing_population=4, margin=0.20, ceiling=10_000)
    plan = barrier.assess_threat(100)
    assert plan["surge_replicas"] == 120
    assert plan["target_population"] == 4 + 120


def test_sizing_rule_rounds_up_cautiously():
    barrier = Barrier(standing_population=4, margin=0.30)
    plan = barrier.assess_threat(7)
    # ceil(7 * 1.30) = ceil(9.1) = 10 — rounding is always up, toward
    # safety, never down toward the threat.
    assert plan["surge_replicas"] == 10


def test_ceiling_caps_the_target_population():
    barrier = Barrier(standing_population=4, margin=0.30)
    assert barrier.ceiling == 40  # default: standing population x 10
    plan = barrier.assess_threat(1_000_000)
    assert plan["target_population"] == barrier.ceiling
    assert plan["ceiling_applied"] is True


def test_zero_threat_needs_no_surge():
    barrier = Barrier(standing_population=4, margin=0.30)
    plan = barrier.assess_threat(0)
    assert plan["surge_replicas"] == 0
    assert plan["target_population"] == barrier.standing_population
    assert plan["ceiling_applied"] is False


def test_respond_raises_population_to_target():
    barrier = Barrier(standing_population=4, margin=0.30, ceiling=10_000)
    result = barrier.respond(100)
    assert barrier.population == result["target_population"] == 134
    assert "spawned 130 replicas" in result["actions"]


def test_stand_down_decodes_exactly_the_surplus():
    barrier = Barrier(standing_population=4, margin=0.30, ceiling=10_000)
    barrier.respond(100)
    assert barrier.population == 134
    outcome = barrier.stand_down()
    assert outcome == {"decoded": 130, "population": 4}
    assert barrier.population == barrier.standing_population


def test_stand_down_at_rest_decodes_nothing():
    barrier = Barrier(standing_population=4, margin=0.30)
    outcome = barrier.stand_down()
    assert outcome == {"decoded": 0, "population": 4}


def test_plans_status_and_outcomes_are_json_serializable():
    barrier = Barrier(standing_population=4, margin=0.30, ceiling=10_000)
    for payload in (
        barrier.assess_threat(100),
        barrier.respond(100),
        barrier.stand_down(),
        barrier.status(),
    ):
        assert json.loads(json.dumps(payload)) == payload


def test_status_reports_the_governing_numbers():
    barrier = Barrier(standing_population=4, margin=0.30)
    assert barrier.status() == {
        "population": 4,
        "standing_population": 4,
        "ceiling": 40,
        "margin": 0.30,
    }
