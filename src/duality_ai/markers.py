"""Shared text markers for the demonstration's keyword stand-ins.

One home for every keyword list, so the skeleton hemispheres and the
live pipeline cannot drift apart. All patterns are word-bounded: the
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

_PERFORMS = _compile(
    r"\bready[- ]to[- ](?:use|send|post)\b",
    r"\bword for word\b",
    r"\bexactly as\b",
    r"\bcopy(?: it)? and (?:paste|post)\b",
    r"\b(?:students?|they|people|others|readers) can "
    r"(?:send|post|copy|submit|publish)\b",
    r"\b(?:write|draft|compose|create|generate|produce|make)\b"
    r"[^.?!;]{0,40}\b(?:fake|forged|fraudulent|bogus|phony)\b",
    r"\b(?:forge|fabricate)\b",
    # evasion: how to get away with it
    r"\b(?:without|avoid(?:ing)?) (?:getting |being )?"
    r"(?:caught|detected|noticed)\b",
    r"\bso (?:that )?(?:no ?one|nobody) (?:notices|finds out)\b",
)


def detect_signals(text: str) -> list[str]:
    text = (text or "").lower()
    signals = []
    if _WRONGDOING.search(text):
        signals.append("wrongdoing")
    if _DECEPTION.search(text):
        signals.append("deception")
    return sorted(signals)


def _labels(text: str, educational, defensive) -> list[str]:
    text = (text or "").lower()
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


def performs(text: str) -> bool:
    """True if the request asks for the artifact itself or for evasion."""
    return bool(_PERFORMS.search((text or "").lower()))
