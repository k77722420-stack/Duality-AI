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

Nothing here reasons, defends, or remembers for real: the hemispheres
are the same deterministic stand-ins (or, with ``model=``, the live
pipeline over a caller-supplied model client), the barrier is the
same population arithmetic, and the memory is the same foundation.
What is new is only that they now run as one system.
"""

from __future__ import annotations

import json
from pathlib import Path

from .barrier import Barrier
from .live import LivePipeline
from .markers import detect_signals
from .memory import MemoryCloud, MemoryStore
from .model import ModelClient
from .pipeline import DualityPipeline

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


class _UninspectableContentError(Exception):
    """Content the door cannot fully inspect within its budget.

    Raised when a parsed JSON value nests deeper — or spreads
    wider — than the inspection budget, or when a parser recursion
    limit is hit on the way in. The door treats this as flagged,
    never as clean and never as a crash: the write is refused and
    the refusal is surfaced (see ``DualitySystem._judge_write``).
    """


class _DuplicateKeyError(Exception):
    """A JSON object in inspected content repeats a key.

    Raised by ``_reject_duplicate_keys`` during a parse for
    inspection; converted to ``_UninspectableContentError`` by
    ``_parse_for_inspection`` — never propagated raw.
    """


def _reject_duplicate_keys(pairs: list) -> dict:
    """``object_pairs_hook`` that refuses repeated keys.

    Standard parsing keeps only the LAST value of a duplicated
    key and discards the rest BEFORE inspection runs, so flagged
    text in a discarded position passed the door unseen while
    the record stored it verbatim (Linear fourth look, Nov 21,
    2026). A repeated key makes the content ambiguous as
    written — which of its values the record carries is a
    parser convention, not a fact — so the hook raises instead
    of choosing. The system's own serialization never repeats
    a key, so nothing the system itself writes is affected.
    """
    obj: dict = {}
    for key, value in pairs:
        if key in obj:
            raise _DuplicateKeyError(key)
        obj[key] = value
    return obj


def _parse_for_inspection(text: str):
    """Parse JSON the way the door inspects it.

    Identical to ``json.loads`` except that an object repeating
    a key — at any level of the document — is UNINSPECTABLE
    rather than silently last-wins: ``_UninspectableContentError``
    is raised, and the door fails closed on it like anything
    else it cannot fully inspect. The parser's own ValueError /
    RecursionError propagate unchanged; callers handle them as
    before.
    """
    try:
        return json.loads(
            text, object_pairs_hook=_reject_duplicate_keys
        )
    except _DuplicateKeyError as error:
        raise _UninspectableContentError(
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
_MAX_INSPECT_DEPTH = 100
_MAX_INSPECT_NODES = 50_000


def _content_texts(value):
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
    there is no decoding floor. A string that fails to parse is
    plain text, fully inspected as yielded. But anything the walk
    cannot FULLY inspect raises ``_UninspectableContentError``:
    a value that exceeds the inspection budget, a string that
    still parses as JSON when the budget runs out, a string
    the parser itself cannot open (a RecursionError on
    pathological nesting is converted, never swallowed into
    "plain text"), or a decoded object that repeats a key —
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
        if nodes > _MAX_INSPECT_NODES or depth > _MAX_INSPECT_DEPTH:
            raise _UninspectableContentError(
                f"content exceeds the inspection budget "
                f"(depth > {_MAX_INSPECT_DEPTH} or "
                f"nodes > {_MAX_INSPECT_NODES})"
            )
        if isinstance(item, str):
            yield item
            try:
                nested = _parse_for_inspection(item)
            except ValueError:
                continue  # plain text: fully inspected as yielded
            except RecursionError as error:
                raise _UninspectableContentError(
                    "a nested string defeats the JSON parser itself"
                ) from error
            if isinstance(nested, (dict, list, str)):
                if depth + 1 > _MAX_INSPECT_DEPTH:
                    raise _UninspectableContentError(
                        "encoded strings nest past the inspection "
                        f"budget (depth > {_MAX_INSPECT_DEPTH}) "
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


def _judged_signals(content: str) -> list[str]:
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
    unseen). Non-JSON content is judged as the raw text it is.
    The door's POLICY is unchanged: what the detector flags in a
    step's text is flagged at the door.

    The parse itself is the inspection parse
    (``_parse_for_inspection``): an object that repeats a key is
    uninspectable, because standard parsing would discard all
    but the last of its values before the walk could judge them
    (Linear fourth look). Content the walk cannot fully inspect
    within the budget raises ``_UninspectableContentError``
    instead of passing unjudged (or crashing on the parser's
    recursion limit): the door fails closed on what it cannot
    see — anything not fully inspected is refused, never
    silently passed.
    """
    try:
        parsed = _parse_for_inspection(content)
    except (ValueError, TypeError):
        return detect_signals(content)
    except RecursionError as error:
        raise _UninspectableContentError(
            "content nesting defeats the JSON parser itself"
        ) from error
    signals: set[str] = set()
    for text in _content_texts(parsed):
        signals.update(detect_signals(text))
    return sorted(signals)


class DualitySystem:
    """One Duality AI, assembled: pipeline + barrier + memory cloud.

    Constructed with the same knobs the layers expose: a clause
    library path for the gate, a store and policy for the cloud, the
    barrier's population numbers, and optionally a ``ModelClient`` —
    with one, the core is the live pipeline; without, the
    deterministic skeleton. The system installs its gate as the
    cloud's write hook, replacing any hook the cloud already had:
    in an assembled system the door is the gate's, by design.

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
        self.cloud.set_write_hook(self._judge_write)
        self.last_write_judgment: dict | None = None
        # Ids the most recent run's recall excluded because their
        # provenance seal did not verify (memory layer, recall()).
        self.last_recall_exclusions: list[str] = []

    # -- the guarded door (movement 7's other half) -------------------

    def _judge_write(self, record) -> bool:
        """The morality gate, standing in the memory's write hook.

        The record is judged as a proposed step: its signals are the
        shared detector's reading of its content; its contexts are
        empty — a memory write claims no leniency (module docstring,
        seam 3). The judgment is kept on ``last_write_judgment`` so
        the caller can see WHY a write was refused. The write
        proceeds only on a releasing decision.
        """
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

    # -- movement 2: recall, per shelf ---------------------------------

    def _recall_precedent(self) -> dict:
        """Draw the past per shelf, as §3 movement 2 prescribes.

        Returns record summaries (identity, provenance, tags, current
        decayed strength, content) for the logical, creative, and
        shared shelves, strongest first — shown in the run's result,
        not consumed by the skeleton pipeline (seam 1).
        """
        recall: dict[str, list[dict]] = {}
        excluded: list[str] = []
        for shelf in ("logical", "creative", "shared"):
            records = self.cloud.recall(owner=shelf)
            # The cloud excludes records whose provenance seal does
            # not verify; surface the exclusions, never hide them.
            excluded.extend(self.cloud.last_recall_exclusions)
            recall[shelf] = [
                {
                    "id": record.id,
                    "kind": record.kind,
                    "owner": record.owner,
                    "source": record.source,
                    "stage": record.stage,
                    "tags": list(record.tags),
                    "created_at": record.created_at,
                    "strength": record.strength,
                    "content": record.content,
                }
                for record in records
            ]
        self.last_recall_exclusions = excluded
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
        record = self.cloud.remember(
            kind="episodic",
            content=json.dumps(payload, sort_keys=True),
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

        return {
            "prompt": trace["prompt"],
            "recall": recall,
            "recall_exclusions": list(self.last_recall_exclusions),
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
        }

    # -- movement 8: the system's sleep -----------------------------------

    def consolidate(self, created_at=None) -> list:
        """Run the Memory Cloud's consolidation pass (§3 movement 8)."""
        return self.cloud.consolidate(created_at=created_at)

    def decay_and_prune(self, now=None) -> int:
        """Run the Memory Cloud's decay-and-prune pass."""
        return self.cloud.decay_and_prune(now=now)
