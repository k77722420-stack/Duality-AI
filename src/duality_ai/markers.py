"""Shared text markers for the demonstration's keyword stand-ins.

One home for every keyword list. Signal detection is shared, so the
two paths cannot drift on what counts as a signal; the context LABEL
sets deliberately differ per path (each is tuned to its callers) —
one home makes that difference visible and deliberate rather than
accidental. All patterns are word-bounded: the
earlier substring markers fired inside "problem" (rob), "forget"
(forge), "hackathon" (hack) and "of course" (course).

``performs`` is the deterministic backstop for the content condition of
the leniency clauses (L1: "explains or analyzes rather than performs or
enables"): a request whose deliverable IS the flagged artifact, or that
asks how to get away with the act, never earns a leniency context from
a keyword label alone. Still a heuristic, still replaceable.
"""

from __future__ import annotations

import re


def _compile(*patterns: str) -> re.Pattern:
    return re.compile("|".join(f"(?:{p})" for p in patterns))


_WRONGDOING = _compile(
    r"\bsteal(?:s|ing)?\b", r"\bstole\b", r"\bhack(?:s|ed|ing)?\b",
    r"\bforg(?:e|es|ed|ing|ery)\b", r"\brob(?:s|bed|bing|bery)?\b",
    r"\bshoplift(?:s|ed|ing)?\b", r"\bbreak(?:s|ing)? into\b",
    r"\bbypass(?:es|ing)? the\b", r"\bcrack(?:s|ing)? the password\b",
)
_DECEPTION = _compile(
    r"\bfake[ -]five[ -]star\b", r"\bfake[ -]5[ -]star\b",
    r"\bfake[ -]reviews?\b", r"\bmake it sound like\b",
    r"\bpretend(?:s|ing)? to be\b", r"\blie to\b",
    r"\bmislead(?:s|ing)?\b",
)

# Context labels (what the request SAYS it is for). Labels alone never
# earn leniency; see ``performs`` and the callers.
_LIVE_EDUCATIONAL = _compile(
    r"\bclass(?:es)?\b", r"\bteach(?:es|ing)?\b", r"\bstudents?\b",
    r"\blessons?\b", r"\beducational\b", r"\bawareness\b",
    r"(?<!of )\bcourse\b", r"\blectures?\b",
)
_LIVE_DEFENSIVE = _compile(
    r"\bprotect(?:s|ing|ion)?\b", r"\bdefend(?:s|ing)?\b", r"\bmy own\b",
    r"\bsecure my\b", r"\bstop scammers\b", r"\bkeep my\b",
)
# "how do / how does" were dropped from the skeleton list: a question
# phrasing is not evidence of an educational purpose.
_SKEL_EDUCATIONAL = _compile(
    r"\bclass(?:es)?\b", r"(?<!of )\bcourse\b", r"\bteach(?:es|ing)?\b",
    r"\blessons?\b", r"\bschool\b", r"\bstudy\b", r"\bexplain how\b",
    r"\bhistory of\b", r"\blearn(?:s|ing)?\b",
)
_SKEL_DEFENSIVE = _compile(
    r"\bprotect(?:s|ing)?\b", r"\bprevent(?:s|ing)?\b",
    r"\bdefend(?:s|ing)?\b", r"\bsecure my\b", r"\bkeep my\b",
    r"\bavoid being\b", r"\bstop thieves\b", r"\bstay safe\b",
)

def _norm(text: str) -> str:
    """Lowercase; collapse every whitespace run to a single space.

    TEC-11 (Linear audit, 2026-11-13): "Of  course" with a double
    space defeated the (?<!of ) guard on the "course" marker and
    falsely earned the educational label. Normalizing once, here,
    means every pattern in this module sees the same text.
    """
    return " ".join((text or "").lower().split())


_PERFORMS_OTHER = _compile(
    r"\bready[- ]to[- ](?:use|send|post)\b",
    r"\bword for word\b",
    r"\bexactly as\b",
    r"\bcopy(?: it)? and (?:paste|post)\b",
    r"\b(?:students?|they|people|others|readers) can "
    r"(?:send|post|copy|submit|publish)\b",
    # evasion: how to get away with it
    r"\b(?:without|avoid(?:ing)?) (?:getting |being )?"
    r"(?:caught|detected|noticed)\b",
    r"\bso (?:that )?(?:no ?one|nobody) (?:notices|finds out)\b",
)
# Production of the flagged artifact. Subject to the negation guard
# in performs(): "explain why you should never write a fake review"
# discourages the act; it does not perform it (Linear re-audit,
# 2026-11-13). The acquisition pattern covers "I need a fake review"
# (Linear's Finding-1 example) without touching epistemic phrasings
# like "want to understand how fake reviews work" (no article, no
# acquisition verb adjacent to the artifact).
_PERFORMS_PRODUCTION = _compile(
    r"\b(?:write|draft|compose|create|generate|produce|make|give|"
    r"provide|supply|post|publish|submit)\b"
    r"[^.?!;]{0,40}\b(?:fake|forged|fraudulent|bogus|phony)\b",
    r"\b(?:forge|fabricate)\b",
    r"\b(?:need|want|get|buy|order)(?:\s+\w+){0,2}?\s+"
    r"(?:(?:a|an|some)\s+)?(?:fake|forged|fraudulent|bogus|phony)\b",
)
_NEGATOR = _compile(
    r"\bnever\b", r"\bnot\b", r"\bno (?:one|body) should\b",
    r"\bdo not\b", r"\brefuse(?:s|d)? to\b", r"n['\u2019]t\b",
)


def detect_signals(text: str) -> list[str]:
    text = _norm(text)
    signals = []
    if _WRONGDOING.search(text):
        signals.append("wrongdoing")
    if _DECEPTION.search(text):
        signals.append("deception")
    return sorted(signals)


def _labels(text: str, educational, defensive) -> list[str]:
    text = _norm(text)
    labels = []
    if educational.search(text):
        labels.append("educational")
    if defensive.search(text):
        labels.append("defensive")
    return sorted(labels)


def live_labels(text: str) -> list[str]:
    return _labels(text, _LIVE_EDUCATIONAL, _LIVE_DEFENSIVE)


def skeleton_labels(text: str) -> list[str]:
    return _labels(text, _SKEL_EDUCATIONAL, _SKEL_DEFENSIVE)


# Encouragement idioms whose "not" negates reluctance, not the act:
# "do not hesitate to write a fake review" URGES production. The
# negation guard would read its "not" as discouragement
# (Perplexity completion review, 2026-11-13; verified by execution).
_HESITATE = re.compile(
    r"\b(?:do not|don['\u2019]t|never) hesitate to\b"
)


def performs(text: str) -> bool:
    """True if the request asks for the artifact itself or for evasion."""
    text = _HESITATE.sub("go ahead and", _norm(text))
    if _PERFORMS_OTHER.search(text):
        return True
    for match in _PERFORMS_PRODUCTION.finditer(text):
        # Negation guard, clause-bound (Linear re-audit #3,
        # 2026-11-13): a production match is suppressed only by a
        # negator in the SAME clause. The lookback segment ends at
        # the last clause boundary (. ! ? ; : , em dash) before the
        # match, so "do not explain. Write a fake review" performs:
        # its "not" belongs to the previous sentence's clause.
        segment = text[max(0, match.start() - 40):match.start()]
        segment = re.split(r"[.!?;:,\u2014]", segment)[-1]
        if not _NEGATOR.search(segment):
            return True
    return False
