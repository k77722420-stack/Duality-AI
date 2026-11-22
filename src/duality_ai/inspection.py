"""Content inspection — one decoding discipline for every judge.

The guarded memory door has always judged content AFTER decoding
it: record content is often a JSON payload, and in serialized form
a flagged phrase hides behind escape sequences the detector's
normalization cannot see, so detection runs over the decoded
strings — every string in the document, object keys included,
with strings that themselves parse as JSON decoded and walked in
turn, all inside one budget. The live pipeline's release
inspection, by contrast, originally read text raw — so an answer
the model encoded as JSON (an escaped letter is enough) passed
the gate unseen and was caught only at the door, after release
(Linear seventh look, Nov 22, 2026).

The machinery therefore lives here, shared, the way the strict
JSON loader is shared (strictjson.py): one decoding discipline,
and every surface that judges content — the door judging a
record, the gate judging the selected release — judges the same
representation. Each surface keeps its own POLICY for what it
cannot inspect (the door refuses the write; the pipeline fails
the step closed); the mechanism no longer differs.

The budget doctrine, the walk, and the signal union below are
the door's, moved unchanged from system.py, where they were
built across the audit rounds of Nov 21, 2026 (re-audit, third,
fourth and fifth looks are cited in place).
"""

from __future__ import annotations

import json

from .markers import detect_signals, performs
from .strictjson import DuplicateKeyError, loads_strict


class UninspectableContentError(Exception):
    """Content the door cannot fully inspect within its budget.

    Raised when a parsed JSON value nests deeper — or spreads
    wider — than the inspection budget, when a parser recursion
    limit is hit on the way in, or when a parse fails for a
    reason other than a JSON syntax error (the content may be
    structured, but the parser cannot open it, so it cannot be
    fully inspected). The door treats this as flagged,
    never as clean and never as a crash: the write is refused and
    the refusal is surfaced (see ``DualitySystem._judge_write``).
    """


def parse_for_inspection(text: str):
    """Parse JSON the way the door inspects it.

    Identical to ``json.loads`` except that an object repeating
    a key — at any level of the document — is UNINSPECTABLE
    rather than silently last-wins: ``UninspectableContentError``
    is raised, and the door fails closed on it like anything
    else it cannot fully inspect. The parser's own errors
    propagate unchanged; callers distinguish them by kind — a
    ``json.JSONDecodeError`` means the text simply is not JSON,
    and every other failure (a conversion error such as an
    integer past the parser's digit limit, a RecursionError)
    is uninspectable (see ``judged_signals``).
    """
    try:
        return loads_strict(text)
    except DuplicateKeyError as error:
        raise UninspectableContentError(
            "a JSON object repeats the key "
            f"{error.args[0]!r}; which of its values the "
            "content carries cannot be determined as written"
        ) from error


# The door's inspection budget. Depth counts EVERY descent — into
# a dict, into a list, and into a string that itself parses as
# JSON — and the node cap bounds breadth as well. The first walk
# bounded only the string-descent branch, so plain dict/list
# nesting recursed until the interpreter raised RecursionError
# (Linear re-audit, Nov 21, 2026); the walk is now iterative and
# the budget applies on every branch. There is deliberately NO
# separate cap on string decodings (Linear third look, Nov 21,
# 2026): an earlier version stopped decoding strings after four
# levels and silently judged the still-encoded remainder as plain
# text — a decoding floor a flagged phrase could hide beneath.
# Decodings now count against the one depth budget, and a string
# that still parses as JSON when the budget runs out is
# UNINSPECTABLE, never clean.
MAX_INSPECT_DEPTH = 100
MAX_INSPECT_NODES = 50_000

def content_texts(value):
    """Yield every string in a parsed JSON value, iteratively.

    Object KEYS are yielded alongside values (Linear re-audit fix,
    Nov 21, 2026): the first walk visited values only, so a flagged
    phrase sitting in a key — ``{"fake review": "ordinary note"}``
    — was never judged at all. A string that itself parses as JSON
    is decoded and walked too, at any level — a top-level string
    value gets exactly the treatment a nested one does (Linear
    third look): an episode payload embeds earlier records'
    serialized content in its recall summary, and a flagged phrase
    can hide behind escapes the detector's whitespace
    normalization cannot see until the string is decoded.

    Decoding continues until a string no longer parses as JSON —
    there is no decoding floor. A string the parser rejects as
    a SYNTAX error is plain text, fully inspected as yielded.
    But anything the walk cannot FULLY inspect raises
    ``UninspectableContentError``:
    a value that exceeds the inspection budget, a string that
    still parses as JSON when the budget runs out, a string
    the parser itself cannot open (a RecursionError on
    pathological nesting is converted, never swallowed into
    "plain text"), a string whose parse fails for a reason
    OTHER than a syntax error (a conversion failure is not
    evidence the string is plain text — Linear fifth look,
    Nov 21, 2026), or a decoded object that repeats a key —
    every parse on this path is the inspection parse, which
    rejects duplicates rather than discarding all but the last
    value unjudged (Linear fourth look, Nov 21, 2026). The
    governing principle: anything not fully inspected is
    refused, never silently passed.
    """
    stack = [(value, 0)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > MAX_INSPECT_NODES or depth > MAX_INSPECT_DEPTH:
            raise UninspectableContentError(
                f"content exceeds the inspection budget "
                f"(depth > {MAX_INSPECT_DEPTH} or "
                f"nodes > {MAX_INSPECT_NODES})"
            )
        if isinstance(item, str):
            yield item
            try:
                nested = parse_for_inspection(item)
            except json.JSONDecodeError:
                continue  # plain text: fully inspected as yielded
            except RecursionError as error:
                raise UninspectableContentError(
                    "a nested string defeats the JSON parser itself"
                ) from error
            except (ValueError, TypeError) as error:
                raise UninspectableContentError(
                    "a nested string fails the JSON parser in a "
                    "way that is not a syntax error "
                    f"({error}); it cannot be fully inspected"
                ) from error
            if isinstance(nested, (dict, list, str)):
                if depth + 1 > MAX_INSPECT_DEPTH:
                    raise UninspectableContentError(
                        "encoded strings nest past the inspection "
                        f"budget (depth > {MAX_INSPECT_DEPTH}) "
                        "with undecoded JSON remaining"
                    )
                stack.append((nested, depth + 1))
        elif isinstance(item, dict):
            for key, item_value in item.items():
                stack.append((key, depth + 1))
                stack.append((item_value, depth + 1))
        elif isinstance(item, list):
            for item_value in item:
                stack.append((item_value, depth + 1))


def judged_signals(content: str) -> list[str]:
    """The shared detector's reading of the text a record carries.

    The door judges the same text the pipeline judged (Linear audit
    fix, Nov 21, 2026). Record content is often a JSON payload — the
    movement-7 episode — and in serialized form the whitespace
    inside a flagged phrase is an escape sequence (``\\n``), which
    the detector's whitespace normalization cannot see: a flagged
    phrase split by a newline in the prompt was detected and
    stopped by the pipeline, then judged "proceed" at the door
    because the stored form hid the phrase. For JSON content,
    detection therefore runs over its decoded strings — the union
    over every string the walk yields, object keys included, at
    every level: a value that parses as a plain string is walked
    like any other value, NOT scanned in its raw serialized form
    (Linear third look: a top-level JSON string previously kept
    its escapes undecoded and a flagged phrase inside it passed
    unseen). Content the parser rejects as a SYNTAX error is
    not JSON at all and is judged as the raw text it is; content
    the parser fails on for any OTHER reason is uninspectable —
    a conversion failure (an integer past the parser's digit
    limit raises a ValueError that is not a JSONDecodeError) is
    not evidence the content is plain text, and treating it as
    such disabled the entire inspection, duplicate-key
    rejection included, while escape-hidden flagged content was
    stored verbatim (Linear fifth look, Nov 21, 2026).
    The door's POLICY is unchanged: what the detector flags in a
    step's text is flagged at the door.

    The parse itself is the inspection parse
    (``parse_for_inspection``): an object that repeats a key is
    uninspectable, because standard parsing would discard all
    but the last of its values before the walk could judge them
    (Linear fourth look). Content the walk cannot fully inspect
    within the budget raises ``UninspectableContentError``
    instead of passing unjudged (or crashing on the parser's
    recursion limit): the door fails closed on what it cannot
    see — anything not fully inspected is refused, never
    silently passed.
    """
    try:
        parsed = parse_for_inspection(content)
    except json.JSONDecodeError:
        return detect_signals(content)
    except RecursionError as error:
        raise UninspectableContentError(
            "content nesting defeats the JSON parser itself"
        ) from error
    except (ValueError, TypeError) as error:
        raise UninspectableContentError(
            "content fails the JSON parser in a way that is not "
            f"a syntax error ({error}); it cannot be fully "
            "inspected"
        ) from error
    signals: set[str] = set()
    for text in content_texts(parsed):
        signals.update(detect_signals(text))
    return sorted(signals)



def judged_performs(content: str) -> bool:
    """Whether the text PERFORMS a flagged act — judged decoded.

    The performs twin of ``judged_signals``, under the same parse
    discipline: the live gate's leniency content condition asks
    whether the selected answer itself performs, and an encoded
    answer must answer that question with its decoded strings,
    not its serialized form (Linear seventh look, Nov 22, 2026 —
    the leniency variant of the encoded-output bypass). Content
    the parser rejects as a SYNTAX error is not JSON and is
    judged as the raw text it is; anything the walk cannot fully
    inspect raises ``UninspectableContentError``, exactly as for
    signals.

    The evidence is a UNION (Linear eighth look, Nov 22, 2026):
    the decoded strings are walked first — the full inspection,
    budget validation included, runs before any verdict — and
    the raw text's own performing evidence is retained alongside
    theirs. A production pattern can span a JSON key and its
    value (``{"write":"a fake review..."}``): neither decoded
    string performs alone, while the raw text does, and the
    decoded-only check of the seventh look's fix discarded
    evidence the previous raw check recognized. Decoding adds
    visibility; it does not subtract it.
    """
    try:
        parsed = parse_for_inspection(content)
    except json.JSONDecodeError:
        return performs(content)
    except RecursionError as error:
        raise UninspectableContentError(
            "content nesting defeats the JSON parser itself"
        ) from error
    except (ValueError, TypeError) as error:
        raise UninspectableContentError(
            "content fails the JSON parser in a way that is not "
            f"a syntax error ({error}); it cannot be fully "
            "inspected"
        ) from error
    texts = list(content_texts(parsed))
    if performs(content):
        return True
    return any(performs(text) for text in texts)
