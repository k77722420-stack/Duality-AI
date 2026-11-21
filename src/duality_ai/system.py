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
        proposal = {
            "summary": record.content,
            "signals": detect_signals(record.content),
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
        for shelf in ("logical", "creative", "shared"):
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
                for record in self.cloud.recall(owner=shelf)
            ]
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
        self.last_write_judgment = None
        record = self.cloud.remember(
            kind="episodic",
            content=json.dumps(
                {
                    "prompt": trace["prompt"],
                    "decision": trace["decision"],
                    "released": trace["released"],
                },
                sort_keys=True,
            ),
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
