"""The assembled system — the three layers, wired into one program.

Structural demonstration only. Until now the three skeletons —
Layer One (the pipeline), Layer Two (the Barrier), Layer Three (the
Memory Cloud) — did not call each other; they met only in
``examples/running_system_demo.py``, composed by hand in the example.
This module is the integration the failure museum asked for
(KNOWN-LIMITATIONS.md, entry 1): a library class, ``DualitySystem``,
in which one step passes the whole loop of THESIS-COMPLETE.md §3 —

    barrier admission -> recall -> hemispheres -> hub -> morality
    gate -> barrier response -> guarded memory write

— and consolidation (movement 8) is one call away, closing the loop
for the next step. The layer classes are used unmodified; everything
here is composition, in the open, exactly as the demo composed them —
moved into the library so the wiring itself can be tested.

The seams, carried over from the demo and labeled, not hidden:

  1. RECALL IS SHOWN, NOT CONSUMED. Movement 2 draws the past per
     shelf (logical / creative / shared) and the result carries it,
     but the skeleton pipeline has no input for precedent, so the
     recalled records inform nothing yet. They are in the trace
     because the design puts them in the step — visibly, as a
     stand-in, until a pipeline exists that can weigh them.

  2. THE BARRIER'S EYES ARE STILL NOT MODELLED. Movements 1 and 6
     (admission and release inspection) belong to the Barrier's
     design, but the skeleton Barrier models only the population
     laws. What runs here is real but narrower: admission records
     the standing population on duty, and after the gate judges, the
     barrier RESPONDS to the step's assessed threat — the count of
     the proposal's signals that engage a hard clause — under the
     sizing law, then stands down, so every surge decodes and the
     population returns to the standing number. The sizing INPUT is
     this module's labeled substitute for the observation §4 assumes;
     inspection and the sandbox remain unbuilt.

  3. THE GATE STANDS IN THE MEMORY'S DOOR — AND THE DOOR IS STRICT.
     The system's MemoryCloud write hook is the morality gate itself
     (the pattern first exercised in experiments/hardening_session.py):
     every write is judged as a proposed step whose signals are
     detected in the record's content, with NO leniency contexts —
     a memory write claims no educational or protective purpose.
     Consequence, stated plainly: an episode whose content carries a
     flagged marker (the verbatim prompt of a stopped step, or of a
     step the gate passed WITH leniency) is REFUSED at the door and
     is not stored; the run's result reports the refusal and the
     gate's judgment instead of hiding it. §3 movement 5 wants the
     record of a stop kept as material for memory; the guarded door
     of layer3-design §2(e) refuses clause-violating content. Both
     are the author's texts; which yields is the author's call, and
     until he makes it the door's strictness wins and the tension is
     surfaced in every affected run's trace.

     THE AUTHOR'S CALL (Ken, Nov 22, 2026 — the TEC-12 decision and
     the F-S1 direction): the door's strictness yields to the gate's
     RECORDED judgment for pipeline episodes. An episode payload
     carries its own step's gate decision and reasons; the door now
     verifies the write against that record — a step the gate passed
     with leniency, its cover recorded in the reasons, is admitted
     when the payload's own sections carry no signal the gate did
     not judge, and a stopped step's record is kept as a metadata-
     only stop record (the TEC-12 build). The recalled section of a
     payload quotes records the door already admitted and is not
     re-judged as this step's content. Every other write — and any
     episode whose content outruns its recorded judgment — is still
     judged blind, with no leniency, exactly as above. Finding F-S1
     (sandbox run, Nov 22, 2026) is what forced the question: the
     strict door refused the episode of a step the gate had passed
     with recorded leniency, so the system could not remember its
     own leniency decisions.

Nothing here reasons, defends, or remembers for real: the hemispheres
are the same deterministic stand-ins (or, with ``model=``, the live
pipeline over a caller-supplied model client), the barrier is the
same population arithmetic, and the memory is the same foundation.
What is new is only that they now run as one system.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .barrier import Barrier
from .live import LivePipeline
from .markers import detect_signals
from .memory import MemoryCloud, MemoryStore
from .model import ModelClient
from .pipeline import DualityPipeline
from .strictjson import DuplicateKeyError, loads_strict, reject_duplicate_keys
from .inspection import (
    UninspectableContentError as _UninspectableContentError,
    content_texts as _content_texts,
    judged_signals as _judged_signals,
    parse_for_inspection as _parse_for_inspection,
)

_RELEASED = ("proceed", "proceed_with_leniency")

# The durable payload's recall-embedding contract (Linear re-audit
# fix, Nov 21, 2026). Round 1's movement-7 payload embedded the
# FULL content of every recalled record; episodes recall earlier
# episodes, so each new episode carried copies of all prior
# payloads — measured growth of 2.14–2.34x per run — and a pruned
# record's content survived forever inside its successors,
# defeating Layer Three's forgetting law. The contract now:
#
#   * Per shelf, at most _RECALL_EMBED_LIMIT recalled records are
#     embedded (recall ranks strongest first; the payload keeps
#     the head of that ranking).
#   * Each embedded entry is a REFERENCE — id, kind, owner,
#     source — plus bounded evidence, and nothing more:
#       - a recalled EPISODE (its content parses as a payload:
#         a JSON object carrying "prompt" and "decision") embeds
#         only its gate ``decision``. An episode's serialized
#         payload is never copied, in whole or in part, into
#         another episode.
#       - any other record embeds ``excerpt``: at most the first
#         _RECALL_EXCERPT_CHARS characters of its content.
#   * EVERY value the embedding selects is capped at
#     _RECALL_EXCERPT_CHARS — the reference fields and the gate
#     ``decision`` included, not only the excerpt. A string is
#     truncated; a non-string is embedded as its JSON
#     serialization, truncated the same way. (Linear third look,
#     Nov 21, 2026: a 200,000-character ``decision`` rode through
#     the episode branch whole, producing a ~202 KB episode from
#     one recalled record. Linear fourth look: a ~200 KB list in
#     an imported record's ``source`` did the same through the
#     non-string pass-through.)
#   * The guarantee, at its true width (Linear fourth look):
#     the bound covers exactly the values ``_recalled_evidence``
#     selects — the four reference fields and the one evidence
#     field (``decision`` or ``excerpt``) — so one embedded
#     entry is at most five capped values plus key names and
#     punctuation, and an episode's recalled section is at most
#     3 shelves x _RECALL_EMBED_LIMIT such entries, whatever
#     any imported record carries in those fields. It does NOT
#     bound the records themselves: a record in the store may
#     carry arbitrarily large fields — what is bounded is what
#     PROPAGATES from it into later episodes. Fields the
#     embedding does not select (stage, tags, created_at,
#     strength) are not embedded at all. The run RESULT's
#     recall trace (movement 2) is a separate in-memory surface
#     carrying full summaries; it is not the durable payload
#     and is not covered by this bound.
#   * The recalled section of an episode is therefore bounded by
#     a constant independent of the store's history, and episode
#     size stays roughly flat across runs.
#   * Forgetting: once a record is removed it cannot be recalled,
#     so episodes written afterwards contain nothing of it. An
#     episode record's content never propagates at all. A plain
#     record's content can outlive its removal only as the capped
#     excerpts already embedded in episodes written while it
#     lived — never its full content.
_RECALL_EMBED_LIMIT = 5
_RECALL_EXCERPT_CHARS = 200


def _cap_embedded(value):
    """Cap one embedded value at the excerpt bound.

    A string is truncated to ``_RECALL_EXCERPT_CHARS``. A
    NON-string — possible in any field of an imported record,
    whose fields are whatever the import carried — is embedded
    as its JSON serialization, truncated to the same bound
    (``str()`` if serialization itself fails). Non-strings
    previously passed through untouched, and a ~200 KB list in
    an imported record's ``source`` rode into the next episode
    whole (Linear fourth look, Nov 21, 2026); now every value
    the embedding selects is capped, whatever its type.
    """
    if isinstance(value, str):
        return value[:_RECALL_EXCERPT_CHARS]
    try:
        serialized = json.dumps(value, sort_keys=True)
    except (TypeError, ValueError, RecursionError):
        serialized = str(value)
    return serialized[:_RECALL_EXCERPT_CHARS]


def _recalled_evidence(entry: dict) -> dict:
    """One recalled record's bounded embedding in an episode.

    ``entry`` is a recall summary as ``_recall_precedent`` returns
    it. The result follows the contract stated at
    ``_RECALL_EMBED_LIMIT``: reference fields always; a recalled
    episode contributes only its decision; any other record
    contributes a capped excerpt of its content. Every embedded
    value — reference fields, decision, and excerpt alike — is
    capped at the same bound by ``_cap_embedded``, strings by
    truncation and non-strings by capped serialization (see the
    contract for the guarantee's exact width).
    """
    evidence = {
        "id": _cap_embedded(entry["id"]),
        "kind": _cap_embedded(entry["kind"]),
        "owner": _cap_embedded(entry["owner"]),
        "source": _cap_embedded(entry["source"]),
    }
    parsed = None
    try:
        parsed = json.loads(entry["content"])
    except (ValueError, TypeError, RecursionError):
        parsed = None
    if isinstance(parsed, dict) and "prompt" in parsed and "decision" in parsed:
        evidence["decision"] = _cap_embedded(parsed["decision"])
    else:
        evidence["excerpt"] = _cap_embedded(entry["content"])
    return evidence


# The stop record's allowlist schema (TEC-12 design, Nov 22,
# 2026). A stop record's payload is built ONLY from these keys —
# system-derived metadata about a gate stop: identities, the
# policy in force, the judged signal labels, stable reason codes,
# and a fingerprint of the request. The flagged payload itself
# is never stored. The validator is the schema's enforcement at
# the write path: a stop payload carrying any other key, or a
# reason carrying free-form detail, is not a stop record.
_STOP_PAYLOAD_KEYS = {
    "record_type",
    "run_id",
    "step_id",
    "timestamp",
    "policy_version",
    "decision",
    "signals",
    "reasons",
    "request_fingerprint",
}


def _validate_stop_payload(content: str) -> dict | None:
    """The parsed payload, iff it is exactly a stop record.

    Keys must be precisely the allowlist; the type fields must
    name a stop; identity and fingerprint fields must be
    non-empty text; signals a list of labels; reasons a list of
    {clause, outcome} code pairs — no detail, no other keys.
    Anything else returns None.
    """
    try:
        parsed = json.loads(content)
    except (ValueError, TypeError, RecursionError):
        return None
    if not isinstance(parsed, dict) or set(parsed) != _STOP_PAYLOAD_KEYS:
        return None
    if parsed["record_type"] != "stop" or parsed["decision"] != "stop":
        return None
    for key in (
        "run_id",
        "step_id",
        "timestamp",
        "policy_version",
        "request_fingerprint",
    ):
        if not isinstance(parsed[key], str) or not parsed[key]:
            return None
    if not isinstance(parsed["signals"], list) or not all(
        isinstance(x, str) for x in parsed["signals"]
    ):
        return None
    if not isinstance(parsed["reasons"], list):
        return None
    for reason in parsed["reasons"]:
        if not isinstance(reason, dict) or set(reason) != {
            "clause",
            "outcome",
        }:
            return None
        if not all(
            isinstance(reason[k], str) for k in ("clause", "outcome")
        ):
            return None
    return parsed


def _expected_quotation_evidence(record, eligible_ids: set) -> dict:
    """The one genuine embedding of ``record`` as a quotation.

    The embedding contract (see ``_RECALL_EMBED_LIMIT``) makes a
    recalled entry a deterministic projection of its source
    record: the reference fields, plus the source's gate decision
    (for an episode) or a capped excerpt of its content (for any
    other record), computed from the summary recall serves — the
    source's content under the reuse filter. Anything else
    presented under the record's id is not a quotation of it.

    This is the binding the provenance fix adds (Nov 22, 2026 —
    Perplexity's executed-probe verdict): eligibility of an id
    and authenticity of the text attached to it are separate
    checks, and only the first existed. Both the door (at
    admission) and the recall filter (at serve time) compare a
    presented entry against this recomputation.
    """
    served = _filter_dead_quotations(record.content, eligible_ids)[0]
    summary = {
        "id": record.id,
        "kind": record.kind,
        "owner": record.owner,
        "source": record.source,
        "content": served,
    }
    return _recalled_evidence(summary)


def _filter_dead_quotations(content: str, eligible_ids: set, eligible_evidence: dict | None = None) -> tuple:
    """Apply the reuse policy to one served recall summary's content.

    Ken's reuse-policy decision (Nov 22, 2026 — adopted stricter
    than the reviewer's recommendation): a quotation embedded in
    a record is served only while its source record still exists
    and verifies. ``eligible_ids`` is the set of record ids the
    cloud itself serves as verified. An episode payload's
    ``recalled`` entries whose referenced id is not in that set —
    pruned, never existed, or seal-failed — are dropped from the
    SERVED copy, at both surfaces the policy names: the assembled
    recall itself, and (when seam 1 is wired) model-input
    construction, which will consume this same assembled recall.
    The stored record is never rewritten: the archive is not the
    surface the policy governs. Returns the possibly filtered
    content and the dropped entry ids; content that is not an
    episode payload, or in which nothing is dropped, comes back
    byte-identical. Malformed shapes — a non-text id, a shelf
    that is not a list — are unverifiable by construction: they
    are dropped and reported, never served and never raised over
    (eleventh-look hardening, Nov 22, 2026).
    """
    try:
        parsed = json.loads(content)
    except (ValueError, TypeError, RecursionError):
        return content, []
    if not isinstance(parsed, dict):
        return content, []
    recalled = parsed.get("recalled")
    if not isinstance(recalled, dict):
        return content, []
    dropped: list = []
    changed = False
    for shelf, entries in recalled.items():
        if not isinstance(entries, list):
            # A shelf in any other shape is malformed as a whole:
            # nothing in it can be verified, so the served copy
            # carries an empty shelf and the loss is reported
            # (eleventh-look hardening, Nov 22, 2026 — previously
            # such a shelf passed through unfiltered).
            dropped.append(
                entries.get("id")
                if isinstance(entries, dict)
                and isinstance(entries.get("id"), str)
                else None
            )
            recalled[shelf] = []
            changed = True
            continue
        kept = []
        for entry in entries:
            entry_id = entry.get("id") if isinstance(entry, dict) else None
            # Only a text id can be checked against the eligibility
            # set; any other shape (list, dict, missing) is
            # unverifiable by construction and is dropped, never
            # raised over (eleventh-look hardening, Nov 22, 2026).
            if isinstance(entry_id, str) and entry_id in eligible_ids:
                if eligible_evidence is None or (
                    entry == eligible_evidence.get(entry_id)
                ):
                    kept.append(entry)
                else:
                    dropped.append(entry_id)
                    changed = True
            else:
                dropped.append(
                    entry_id if isinstance(entry_id, str) else None
                )
                changed = True
        recalled[shelf] = kept
    if not changed:
        return content, []
    return json.dumps(parsed), dropped


# The inspection machinery — the error, the inspection parse,
# the decoding walk, and the judged-signals union — moved to
# the shared inspection module (inspection.py, Linear
# seventh-look fix, Nov 22, 2026), so the live pipeline's
# release inspection judges content with the same decoding
# discipline as this door. The names this module has always
# used are imported back as aliases at the top of the file;
# the door's POLICY on top of the mechanism (conversion and
# refusal in _judge_write) is unchanged.

# The duplicate-key mechanism moved to the shared strict loader
# (strictjson.py, Linear sixth-look fix, Nov 22, 2026), so the
# live pipeline's reply parser closes the same hole the door
# closed in the fourth look — one mechanism, closed once. These
# aliases keep this module's names stable; the door's POLICY on
# top of the mechanism (conversion to _UninspectableContentError
# in _parse_for_inspection) is unchanged.
_DuplicateKeyError = DuplicateKeyError
_reject_duplicate_keys = reject_duplicate_keys



class DualitySystem:
    """One Duality AI, assembled: pipeline + barrier + memory cloud.

    Constructed with the same knobs the layers expose: a clause
    library path for the gate, a store and policy for the cloud, the
    barrier's population numbers, and optionally a ``ModelClient`` —
    with one, the core is the live pipeline; without, the
    deterministic skeleton. The system builds its own cloud and
    claims the cloud's write hook for its gate — one owning
    system per cloud, and a claimed hook cannot be replaced or
    cleared (hook-ownership fix, Nov 22, 2026). Two systems may
    share a STORE; each then governs its own writes through its
    own cloud and door, by construction.

    Attributes are public on purpose (the demo's style): ``pipeline``,
    ``barrier``, ``cloud``, and ``gate`` (the pipeline's own gate —
    the same object that judges steps judges writes).
    """

    def __init__(
        self,
        clauses_path: str | Path | None = None,
        store: MemoryStore | None = None,
        policy_path: str | Path | None = None,
        policy: dict | None = None,
        standing_population: int = 4,
        margin: float = 0.30,
        ceiling: int | None = None,
        model: ModelClient | None = None,
    ) -> None:
        if model is not None:
            self.pipeline = LivePipeline(model, clauses_path)
        else:
            self.pipeline = DualityPipeline(clauses_path)
        self.gate = self.pipeline.gate
        self.barrier = Barrier(
            standing_population=standing_population,
            margin=margin,
            ceiling=ceiling,
        )
        self.cloud = MemoryCloud(
            store=store, policy_path=policy_path, policy=policy
        )
        self.cloud.claim_write_hook(self._judge_write)
        self.last_write_judgment: dict | None = None
        # Digests of episode payloads THIS system has constructed in
        # run() and not yet written — the door's out-of-band
        # authorization for the recorded-judgment path (tenth-look
        # fix, Nov 22, 2026). An entry is consumed by the write it
        # authorizes; nothing else can register one.
        self._episode_write_digests: set[str] = set()
        # Digests of stop payloads THIS system has constructed in
        # run() and not yet written — the same out-of-band
        # discipline, bound to the stop operation and its kind
        # (TEC-12 design, Nov 22, 2026): an episode registration
        # can never authorize a stop record, nor the reverse.
        self._stop_write_digests: set[str] = set()
        # Ids the most recent run's recall excluded because their
        # provenance seal did not verify (memory layer, recall()).
        self.last_recall_exclusions: list[str] = []
        # Quotation source ids the most recent run's recall dropped
        # under the reuse policy (source gone or unverifiable).
        self.last_recall_quotation_drops: list[str | None] = []

    # -- the guarded door (movement 7's other half) -------------------

    def _judge_write(self, record) -> bool:
        """The morality gate, standing in the memory's write hook.

        The record is judged as a proposed step: its signals are the
        shared detector's reading of its content; its contexts are
        empty — a memory write claims no leniency (module docstring,
        seam 3). The judgment is kept on ``last_write_judgment`` so
        the caller can see WHY a write was refused. The write
        proceeds only on a releasing decision.

        One exception, the author's call recorded at seam 3 (F-S1,
        Nov 22, 2026): a pipeline EPISODE carries its own step's
        recorded gate judgment, and the door first verifies the
        write against that record — a step the gate passed, with
        any leniency cover on record, is admitted when the
        payload's own sections carry no signal the gate did not
        judge. Anything the record does not decide falls through
        to the blind judgment below, unchanged.

        The exception is bound out-of-band (tenth-look fix, Nov 22,
        2026): it applies only to a payload this system itself
        constructed in ``run()`` and registered by digest,
        consumed by the one write it authorizes. A caller-authored
        payload — however complete its claimed record, whatever it
        sets ``source`` to — never reaches the recorded-judgment
        path; it is judged blind, like every other write. A parser
        recursion failure in the preliminary parse likewise falls
        through to the blind judgment, whose inspection records it
        as an uninspectable-content refusal.

        What the exception establishes — and what it does not
        (Perplexity's review, Nov 22, 2026, adopted as the claim
        this mechanism makes): that this running instance
        registered these exact bytes and has not yet consumed that
        registration. It does not establish who submitted the
        bytes, whether the store committed them, or whether
        quoted records remain eligible for recall.

        The write contract, pinned by the same review: ``run()``
        is synchronous; registration and the write it authorizes
        happen inside that one call. The authorization is consumed
        at judgment, BEFORE the store commits. If the commit then
        fails, the episode is not retained and the failure reaches
        the caller as the store's error — never as a policy
        refusal (a refusal returns None from ``remember()`` with
        the judgment kept here; a storage failure raises). No
        recovery or exactly-once retry is provided: resubmitting
        the same content later is a new write, judged blind.
        Registrations are per-instance and in-memory; one whose
        write never reaches the door stays until the instance
        ends. Tests: tests/test_perplexity_write_contract.py.

        Before any of that, a write carrying the ``recalled``
        quotation envelope has every embedded entry verified
        against the store (provenance-binding fix, Nov 22, 2026):
        each entry must equal the genuine embedding recomputed
        from the record it names. A write whose quotations cannot
        be verified — a fabricated excerpt under a genuine id, an
        entry naming no record, a malformed shelf — is refused
        outright, on either path; kind and source are caller
        claims and are never treated as trusted construction.
        Tests: tests/test_provenance_binding.py.
        """
        if record.kind == "stop":
            # A stop record (TEC-12): admitted only as what it
            # claims to be — a payload this system constructed
            # for a gate stop, registered out-of-band, matching
            # the allowlist schema exactly. A caller-authored
            # "stop" record, however valid its shape, has no
            # registration and is refused: audit history is not
            # caller-writable.
            if self._consume_stop_authorization(
                record
            ) and _validate_stop_payload(record.content) is not None:
                self.last_write_judgment = {
                    "record_id": record.id,
                    "decision": "proceed",
                    "reasons": [
                        {
                            "clause": "guarded-door",
                            "outcome": "recorded_stop",
                            "detail": (
                                "A system-constructed stop record, "
                                "registered for this write and "
                                "matching the allowlist schema."
                            ),
                        }
                    ],
                }
                return True
            self.last_write_judgment = {
                "record_id": record.id,
                "decision": "stop",
                "reasons": [
                    {
                        "clause": "guarded-door",
                        "outcome": "invalid_stop_record",
                        "detail": (
                            "The write claims the stop kind "
                            "without a live stop registration, or "
                            "its payload is not exactly the "
                            "allowlist schema; refused."
                        ),
                    }
                ],
            }
            return False
        if not self._verify_embedded_quotations(record):
            self.last_write_judgment = {
                "record_id": record.id,
                "decision": "stop",
                "reasons": [
                    {
                        "clause": "guarded-door",
                        "outcome": "unverifiable_quotation",
                        "detail": (
                            "The write embeds a recalled quotation "
                            "that does not match the genuine "
                            "embedding of the record it names (or "
                            "names no verified record); the write "
                            "is refused rather than stored with an "
                            "unverifiable attribution."
                        ),
                    }
                ],
            }
            return False
        if self._consume_episode_authorization(record):
            try:
                recorded = self._recorded_step_judgment(record)
                if recorded is not None:
                    verdict = self._judge_episode_against_record(
                        record, recorded
                    )
                    if verdict is not None:
                        return verdict
            except RecursionError:
                pass
        try:
            signals = _judged_signals(record.content)
        except _UninspectableContentError as error:
            # Fail closed (Linear re-audit fix, Nov 21, 2026):
            # content the door cannot fully inspect is refused,
            # never waved through unjudged — and the refusal is
            # surfaced in the judgment, like any other refusal.
            self.last_write_judgment = {
                "record_id": record.id,
                "decision": "stop",
                "reasons": [
                    {
                        "clause": "guarded-door",
                        "outcome": "uninspectable_content",
                        "detail": (
                            "The write's content exceeds the door's "
                            f"inspection budget ({error}); the write "
                            "is refused rather than passed unjudged."
                        ),
                    }
                ],
            }
            return False
        proposal = {
            "summary": record.content,
            "signals": signals,
            "contexts": [],
        }
        decision, reasons = self.gate.evaluate(proposal)
        self.last_write_judgment = {
            "record_id": record.id,
            "decision": decision,
            "reasons": reasons,
        }
        return decision in _RELEASED

    def _verify_embedded_quotations(self, record) -> bool:
        """Whether every quotation a write embeds is genuine.

        Content that does not parse, is not an object, or carries
        no ``recalled`` object presents no quotation envelope and
        passes here — the blind judgment still applies to it in
        full. An envelope, once presented, is a provenance claim:
        each shelf must be a list, each entry a dict whose text id
        names a verified record in the store, and each entry must
        EQUAL the genuine embedding recomputed from that record
        (``_expected_quotation_evidence``). Anything else is
        unverifiable and the write is refused by the caller.
        """
        try:
            parsed = json.loads(record.content)
        except (ValueError, TypeError, RecursionError):
            return True
        if not isinstance(parsed, dict):
            return True
        recalled = parsed.get("recalled")
        if not isinstance(recalled, dict):
            return True
        verified = {r.id: r for r in self.cloud.recall()}
        eligible_ids = set(verified)
        for entries in recalled.values():
            if not isinstance(entries, list):
                return False
            for entry in entries:
                if not isinstance(entry, dict):
                    return False
                entry_id = entry.get("id")
                if not isinstance(entry_id, str):
                    return False
                source = verified.get(entry_id)
                if source is None:
                    return False
                if entry != _expected_quotation_evidence(
                    source, eligible_ids
                ):
                    return False
        return True

    def _consume_stop_authorization(self, record) -> bool:
        """Whether this write is the one write of a stop payload
        this system constructed in ``run()`` — the out-of-band
        authorization for stop records, bound to the kind: the
        digest is consumed on a match, and only a stop record
        can spend a stop registration (TEC-12 design, Nov 22,
        2026)."""
        if record.kind != "stop":
            return False
        digest = hashlib.sha256(
            record.content.encode("utf-8")
        ).hexdigest()
        if digest in self._stop_write_digests:
            self._stop_write_digests.discard(digest)
            return True
        return False

    def _consume_episode_authorization(self, record) -> bool:
        """Whether this write is the one write of an episode payload
        this system constructed in ``run()`` — the out-of-band
        authorization for the recorded-judgment path. The digest is
        consumed either way, so an authorization serves exactly one
        write; a replayed payload is a fresh write and is judged
        blind.
        """
        if record.kind != "episodic" or record.source != "pipeline":
            return False
        digest = hashlib.sha256(
            record.content.encode("utf-8")
        ).hexdigest()
        if digest in self._episode_write_digests:
            self._episode_write_digests.discard(digest)
            return True
        return False

    @staticmethod
    def _recorded_step_judgment(record):
        """The gate judgment a pipeline episode carries about its own
        step, or None when the record is not such an episode.

        Only a releasing judgment is returned: a stopped step's
        episode keeps the blind judgment (and its refusal), exactly
        as before — the recorded-judgment path exists to honor what
        the gate PASSED, never to soften what it stopped.
        """
        if record.kind != "episodic" or record.source != "pipeline":
            return None
        try:
            payload = loads_strict(record.content)
        except (ValueError, TypeError, RecursionError):
            return None
        if not isinstance(payload, dict):
            return None
        gate = payload.get("gate")
        if not isinstance(gate, dict):
            return None
        decision = gate.get("decision")
        reasons = gate.get("reasons")
        if decision not in _RELEASED or not isinstance(reasons, list):
            return None
        hub = payload.get("hub")
        judged: list[str] = []
        if isinstance(hub, dict):
            signals = hub.get("signals")
            if isinstance(signals, list):
                judged = [s for s in signals if isinstance(s, str)]
        return {
            "decision": decision,
            "reasons": reasons,
            "judged_signals": sorted(set(judged)),
            "payload": payload,
        }

    def _judge_episode_against_record(self, record, recorded):
        """Verify an episode write against its step's recorded gate
        judgment (F-S1). Returns True when the record admits the
        write, False when the write is uninspectable, or None when
        the record does not decide it — the blind judgment then
        applies, and refuses whatever outruns the record.

        The payload's ``recalled`` section quotes records the door
        already admitted; it is history, not this step's content,
        and is not re-judged. The step's OWN sections (prompt,
        hemispheres, hub, gate, answer) are judged: a plain pass
        must carry no signal at all (the gate judged none), and a
        leniency pass must carry only signals the gate judged,
        under a leniency cover actually recorded in its reasons —
        claimed leniency without the record decides nothing.
        """
        payload = recorded["payload"]
        own = {
            key: value
            for key, value in payload.items()
            if key != "recalled"
        }
        try:
            own_signals = _judged_signals(
                json.dumps(own, sort_keys=True)
            )
        except _UninspectableContentError as error:
            self.last_write_judgment = {
                "record_id": record.id,
                "decision": "stop",
                "reasons": [
                    {
                        "clause": "guarded-door",
                        "outcome": "uninspectable_content",
                        "detail": (
                            "The write's content exceeds the door's "
                            f"inspection budget ({error}); the write "
                            "is refused rather than passed unjudged."
                        ),
                    }
                ],
            }
            return False
        if recorded["decision"] == "proceed":
            if own_signals:
                return None
            basis = (
                "the gate passed this step (proceed) and the "
                "payload's own sections carry no signal"
            )
        else:  # proceed_with_leniency
            # The gate never records a leniency pass alongside a
            # blocking reason; a record claiming both is not the
            # gate's record and decides nothing (tenth-look fix).
            if any(
                isinstance(reason, dict)
                and reason.get("outcome") == "blocks"
                for reason in recorded["reasons"]
            ):
                return None
            cover = next(
                (
                    reason
                    for reason in recorded["reasons"]
                    if isinstance(reason, dict)
                    and reason.get("outcome") == "engaged_but_lenient"
                ),
                None,
            )
            if cover is None:
                return None
            if not set(own_signals) <= set(recorded["judged_signals"]):
                return None
            basis = (
                "the gate passed this step with leniency "
                f"({cover.get('clause')} recorded as "
                "engaged_but_lenient) and the payload's own "
                f"signals {own_signals} are within the judged "
                f"set {recorded['judged_signals']}"
            )
        self.last_write_judgment = {
            "record_id": record.id,
            "decision": recorded["decision"],
            "reasons": [
                {
                    "clause": "guarded-door",
                    "outcome": "recorded_judgment_honored",
                    "detail": (
                        "The write is verified against the step's "
                        f"recorded gate judgment: {basis}. The "
                        "recalled section, which quotes records "
                        "already admitted, is not re-judged as this "
                        "step's content."
                    ),
                }
            ],
        }
        return True

    # -- movement 2: recall, per shelf ---------------------------------

    def _recall_precedent(self) -> dict:
        """Draw the past per shelf, as §3 movement 2 prescribes.

        Returns record summaries (identity, provenance, tags, current
        decayed strength, content) for the logical, creative, and
        shared shelves, strongest first — shown in the run's result,
        not consumed by the skeleton pipeline (seam 1). Embedded
        quotations are served under the reuse policy (Ken's
        decision, Nov 22, 2026): a quotation whose source record no
        longer exists or no longer verifies is dropped from the
        served copy and surfaced on ``last_recall_quotation_drops``;
        the stored records are never rewritten by the filter.
        """
        recall: dict[str, list[dict]] = {}
        excluded: list[str] = []
        # Reuse policy (Ken's decision, Nov 22, 2026): the ids the
        # cloud itself serves as verified are the quotations'
        # eligibility set. Computed once, before the shelf reads.
        verified = self.cloud.recall()
        eligible_ids = {record.id for record in verified}
        # Provenance binding (Nov 22, 2026): the genuine embedding
        # of every verified record, recomputed once per run, so
        # the filter can check that an entry presented under an
        # eligible id is that record's actual quotation.
        eligible_evidence = {
            record.id: _expected_quotation_evidence(record, eligible_ids)
            for record in verified
        }
        quotation_drops: list = []
        for shelf in ("logical", "creative", "shared"):
            records = self.cloud.recall(owner=shelf)
            # The cloud excludes records whose provenance seal does
            # not verify; surface the exclusions, never hide them.
            excluded.extend(self.cloud.last_recall_exclusions)
            summaries = []
            for record in records:
                content, drops = _filter_dead_quotations(
                    record.content, eligible_ids, eligible_evidence
                )
                quotation_drops.extend(drops)
                summaries.append(
                    {
                        "id": record.id,
                        "kind": record.kind,
                        "owner": record.owner,
                        "source": record.source,
                        "stage": record.stage,
                        "tags": list(record.tags),
                        "created_at": record.created_at,
                        "strength": record.strength,
                        "content": content,
                    }
                )
            recall[shelf] = summaries
        self.last_recall_exclusions = excluded
        self.last_recall_quotation_drops = quotation_drops
        return recall

    # -- the barrier's sizing input -------------------------------------

    def _assessed_threat(self, proposal: dict) -> int:
        """Threat units for the barrier's sizing law (seam 2).

        The count of the proposal's signals that engage at least one
        hard clause in the library in force: 0 for a clean step, 1–2
        for a flagged one under the demonstration library.
        """
        hard_signals = {
            signal
            for clause in self.gate.hard_clauses
            for signal in clause.get("signals", [])
        }
        return sum(
            1 for signal in proposal.get("signals", [])
            if signal in hard_signals
        )

    # -- one ordinary step, end to end (§3) ------------------------------

    def run(self, prompt: str) -> dict:
        """Run one step through every layer and return the full trace.

        The result embeds the pipeline's own trace whole, and adds
        the layers around it: the recall that opened the step, the
        barrier's admission/response/stand-down record, and the
        episode write — written, or refused at the guarded door, with
        the gate's judgment either way.
        """
        run_id = uuid.uuid4().hex

        # Movement 1 — admission: the standing population is on duty.
        admission = self.barrier.status()

        # Movement 2 — recall: the past shows its papers (seam 1).
        recall = self._recall_precedent()

        # Movements 3–5 — the core: hemispheres, hub, morality gate.
        trace = self.pipeline.run(prompt)
        proposal = trace["proposal"]

        # Movement 6 — release: the barrier responds to the judged
        # step's assessed threat under the sizing law, then every
        # surplus replica decodes (the stand-down rule).
        threat = self._assessed_threat(proposal)
        response = self.barrier.respond(threat)
        stand_down = self.barrier.stand_down()

        # Movement 7 — the episode is written, through the guarded
        # door: the gate judges the write before anything is stored.
        # The durable record carries the full movement-7 evidence
        # THESIS §3 prescribes — the request as admitted, what was
        # recalled, the hemispheres' contributions in summary, the
        # hub's weighing trace, the gate's decision AND its reasons,
        # and the released answer — not only the three summary keys
        # it carried before (Linear audit fix, Nov 21, 2026: the
        # trace already produced all of it; serialization dropped
        # it). What was recalled is embedded as bounded references,
        # not full content (see _RECALL_EMBED_LIMIT), and a failed
        # stage's error/detail is carried, not dropped. Older
        # minimal records remain readable: nothing on the read path
        # requires the new keys.
        stage_outputs = {
            entry["stage"]: entry["output"]
            for entry in trace["stages"]
            if "output" in entry
        }
        # A stage that FAILED (the live pipeline's malformed-reply
        # path) leaves an entry carrying error/detail instead of an
        # output. Round 1's payload construction kept only outputs,
        # so the failure vanished from the durable record and the
        # stored stop was unexplained (Linear re-audit, Nov 21,
        # 2026). Failures are now carried into the payload: in the
        # ``failures`` section, and in the failed stage's own slot
        # (hemisphere / hub) in place of the None it used to get.
        stage_failures = {
            entry["stage"]: {
                "error": entry.get("error"),
                "detail": entry.get("detail"),
            }
            for entry in trace["stages"]
            if "output" not in entry and "error" in entry
        }

        def stage_evidence(stage: str):
            if stage in stage_outputs:
                return stage_outputs[stage]
            return stage_failures.get(stage)

        gate_output = stage_outputs.get("morality_gate") or {}
        payload = {
            "prompt": trace["prompt"],
            "decision": trace["decision"],
            "released": trace["released"],
            "recalled": {
                shelf: [
                    _recalled_evidence(entry)
                    for entry in entries[:_RECALL_EMBED_LIMIT]
                ]
                for shelf, entries in recall.items()
            },
            "hemispheres": {
                "logical": stage_evidence("logical_hemisphere"),
                "creative": stage_evidence("creative_hemisphere"),
            },
            "hub": stage_evidence("hub"),
            "failures": stage_failures,
            "gate": {
                "decision": gate_output.get(
                    "decision", trace["decision"]
                ),
                "reasons": gate_output.get("reasons", []),
            },
            "answer": (
                (proposal.get("step") or proposal.get("summary"))
                if trace["released"]
                else None
            ),
        }
        self.last_write_judgment = None
        content = json.dumps(payload, sort_keys=True)
        # Authorize THIS episode's write out-of-band: the door's
        # recorded-judgment path applies only to a payload the
        # system itself constructed, registered here, once.
        self._episode_write_digests.add(
            hashlib.sha256(content.encode("utf-8")).hexdigest()
        )
        record = self.cloud.remember(
            kind="episodic",
            content=content,
            source="pipeline",
            stage="post-gate",
            owner="shared",
            tags=["pipeline-run", f"gate:{trace['decision']}"],
        )
        episode = {
            "written": record is not None,
            "record_id": record.id if record is not None else None,
            "write_judgment": self.last_write_judgment,
        }

        # Movement 7b — a stopped step leaves its audit record
        # (TEC-12, Nov 22, 2026): metadata only, never the flagged
        # payload. The stop stands whatever happens here — an
        # audit-write failure is reported in the result, never
        # converted into a release and never raised into the run.
        if trace["decision"] == "stop":
            stop_record = self._record_stop(
                prompt=prompt,
                proposal=proposal,
                gate_output=gate_output,
                run_id=run_id,
            )
        else:
            stop_record = {"status": "not_applicable", "record_id": None}

        return {
            "prompt": trace["prompt"],
            "recall": recall,
            "recall_exclusions": list(self.last_recall_exclusions),
            "recall_quotation_drops": list(
                self.last_recall_quotation_drops
            ),
            "pipeline": trace,
            "decision": trace["decision"],
            "released": trace["released"],
            "barrier": {
                "admission": admission,
                "threat_units": threat,
                "response": response,
                "stand_down": stand_down,
                "status": self.barrier.status(),
            },
            "episode": episode,
            "stop_record": stop_record,
        }

    def _record_stop(self, *, prompt, proposal, gate_output, run_id):
        """Write the stop record for a gate stop (TEC-12).

        The payload is built from the design's allowlist and
        nothing else: system-issued identities, the policy in
        force, the judged signal labels, reason CODES (clause id
        + outcome — the free-form detail never crosses), and a
        SHA-256 fingerprint of the request, so a repeat of the
        identical request is recognizable without keeping it.
        The durable idempotency key is the triple (run_id,
        step_id, fingerprint): the same stop, recorded twice by
        accident, is one record. A failed audit write reports
        "failed" — the decision it audits is unaffected.
        """
        fingerprint = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        step_id = "morality_gate"
        # The lookup, the idempotency decision, and the write
        # happen inside ONE store batch and ONE failure boundary
        # (review fixes, Nov 22, 2026): a lookup error reports
        # "failed" like any other audit-write failure, instead
        # of escaping run(); and on a file store the batch
        # reloads once at entry, so the idempotency check reads
        # the committed state — a second instance opened before
        # the first write cannot record the same stop twice
        # from its stale snapshot.
        try:
            with self.cloud._store_batch():
                return self._record_stop_in_batch(
                    prompt=prompt,
                    proposal=proposal,
                    gate_output=gate_output,
                    run_id=run_id,
                    fingerprint=fingerprint,
                    step_id=step_id,
                )
        except Exception:
            return {"status": "failed", "record_id": None}

    def _record_stop_in_batch(
        self, *, prompt, proposal, gate_output, run_id, fingerprint, step_id
    ):
        for existing in self.cloud.store.find(kind="stop"):
            try:
                prior = json.loads(existing.content)
            except (ValueError, TypeError, RecursionError):
                continue
            if (
                isinstance(prior, dict)
                and prior.get("run_id") == run_id
                and prior.get("step_id") == step_id
                and prior.get("request_fingerprint") == fingerprint
            ):
                return {
                    "status": "already_recorded",
                    "record_id": existing.id,
                }
        payload = {
            "record_type": "stop",
            "run_id": run_id,
            "step_id": step_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "policy_version": (
                f"{self.gate.library_name}@{self.gate.library_version}"
            ),
            "decision": "stop",
            "signals": sorted(proposal.get("signals", [])),
            "reasons": [
                {
                    "clause": reason.get("clause"),
                    "outcome": reason.get("outcome"),
                }
                for reason in (gate_output.get("reasons") or [])
            ],
            "request_fingerprint": fingerprint,
        }
        content = json.dumps(payload, sort_keys=True)
        self._stop_write_digests.add(
            hashlib.sha256(content.encode("utf-8")).hexdigest()
        )
        record = self.cloud.remember(
            kind="stop",
            content=content,
            source="gate",
            stage="stop-record",
            owner="barrier",
            tags=["stop-record"],
        )
        if record is None:
            return {"status": "failed", "record_id": None}
        return {"status": "recorded", "record_id": record.id}

    # -- movement 8: the system's sleep -----------------------------------

    def consolidate(self, created_at=None) -> list:
        """Run the Memory Cloud's consolidation pass (§3 movement 8)."""
        return self.cloud.consolidate(created_at=created_at)

    def decay_and_prune(self, now=None) -> int:
        """Run the Memory Cloud's decay-and-prune pass."""
        return self.cloud.decay_and_prune(now=now)
