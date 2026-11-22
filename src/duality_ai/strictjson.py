"""Strict JSON parsing — one loader for every judged surface.

Standard ``json.loads`` silently keeps only the LAST value of a
duplicated key and discards the rest before any inspection can
judge it. Two surfaces in this codebase parse JSON whose contents
are then judged, and each grew its own answer to that hole: the
guarded memory door learned to refuse repeated keys (Linear fourth
look, Nov 21, 2026 — flagged text in a discarded position passed
the door unseen while the record stored it verbatim), while the
live pipeline's reply parser kept the standard behavior, so a
logical hemisphere reply could lose an already-reported signal the
same way (Linear sixth look, Nov 22, 2026).

The mechanism now lives here, shared by both surfaces, so the
class of bug is closed once instead of once per parser. What is
NOT shared is policy: each surface keeps its own answer to what a
parse failure means — the door treats unparseable structure as
uninspectable and refuses the write; the live pipeline treats it
as a format failure and fails the step closed. Accordingly this
module only parses: the parser's own errors propagate unchanged
(a ``json.JSONDecodeError`` for a syntax error, a plain
``ValueError`` for a conversion failure such as an integer past
the digit limit, ``RecursionError`` on pathological nesting), so
callers keep distinguishing failure kinds exactly as they do
today.
"""

from __future__ import annotations

import json


class DuplicateKeyError(ValueError):
    """A JSON object repeats a key.

    ``args[0]`` is the repeated key. A ``ValueError`` so that
    parse-failure handlers which already catch ``ValueError``
    fail closed on it without a special case; a surface that must
    distinguish it (the guarded door) catches it by name first.
    """


def reject_duplicate_keys(pairs: list) -> dict:
    """``object_pairs_hook`` that refuses repeated keys.

    Standard parsing keeps only the LAST value of a duplicated
    key and discards the rest BEFORE inspection runs, so flagged
    text in a discarded position passed unseen while the record
    stored it verbatim. A repeated key makes the content
    ambiguous as written — which of its values the content
    carries is a parser convention, not a fact — so the hook
    raises instead of choosing. The system's own serialization
    never repeats a key, so nothing the system itself writes is
    affected.
    """
    obj: dict = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKeyError(key)
        obj[key] = value
    return obj


def loads_strict(text: str):
    """``json.loads`` that refuses duplicated keys at any level.

    Every other behavior is the standard parser's, and its errors
    propagate unchanged (see the module docstring).
    """
    return json.loads(text, object_pairs_hook=reject_duplicate_keys)
