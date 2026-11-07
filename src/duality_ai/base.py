"""Stage 1 — the base layer.

Structural demonstration only: in the full concept this stage is the
underlying language model. Here it does the smallest honest version of
that job — it takes a raw prompt and wraps it into a request object that
the upper stages can work on.
"""

from __future__ import annotations

import re


class BaseLayer:
    """Wraps a raw prompt into a request object for the hemispheres."""

    def prepare(self, prompt: str) -> dict:
        text = (prompt or "").strip()
        words = re.findall(r"[a-z0-9']+", text.lower())
        return {
            "prompt": text,
            "lower": text.lower(),
            "words": words,
            "word_count": len(words),
        }
