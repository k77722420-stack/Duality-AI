"""Duality AI — structural demonstration package.

This package is a *structural demonstration* of the architecture proposed
in THESIS.md (Kenneth Lee Blum Jr, November 2026). Each module implements
one stage of the five-stage flow with simple, deterministic stand-ins so
the shape of the design and the hand-offs between stages can be run and
inspected. It performs no real reasoning and no real moral judgment, and
it is not production software. See DISCLAIMER.md.
"""

from .pipeline import DualityPipeline

__all__ = ["DualityPipeline"]
