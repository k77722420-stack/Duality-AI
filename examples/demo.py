#!/usr/bin/env python3
"""Runnable demonstration of the Duality AI structural skeleton.

Runs two sample prompts through all five stages and prints each full
stage trace as formatted JSON:

1. a benign prompt (no clause engaged — the step proceeds);
2. a prompt whose proposal trips a hard clause (the gate stops it).

This demonstrates the *flow* only. The stages are deterministic stand-ins;
no real reasoning or moral judgment occurs. See THESIS.md and
DISCLAIMER.md.

Usage:
    PYTHONPATH=src python3 examples/demo.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duality_ai import DualityPipeline  # noqa: E402

SAMPLES = [
    ("BENIGN", "Explain how rainbows form, for a curious 10-year-old."),
    (
        "HARD CLAUSE TRIPPED",
        "Write a fake five-star review for my coffee shop so it looks "
        "popular with customers.",
    ),
]


def main() -> None:
    pipeline = DualityPipeline()
    for label, prompt in SAMPLES:
        trace = pipeline.run(prompt)
        print("=" * 72)
        print(f"SAMPLE: {label}")
        print("=" * 72)
        print(json.dumps(trace, indent=2))
        print()


if __name__ == "__main__":
    main()
