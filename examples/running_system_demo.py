#!/usr/bin/env python3
"""The running-system demonstration — all three layers, composed.

THESIS-COMPLETE.md (§6) states the honest position: the three layer
skeletons — the pipeline (Layer One), the Barrier (Layer Two), and the
Memory Cloud (Layer Three) — are *not wired together* in the library.
The classes do not call each other. This demo is where they meet: it
composes the existing classes, unmodified, into the two traces the
capstone thesis describes —

  TRACE A (§3): one ordinary step, end to end — the pipeline runs, its
  outcome is written to memory as an episode, consolidation distills
  the episodes into knowledge, and the *next* step begins by recalling
  that knowledge as precedent.

  TRACE B (§4): one attack, end to end — the Barrier surges under the
  sizing law using the Layer Two thesis's own worked example
  (P0 = 4, m = 0.30, C = 100, T = 40 -> S = 52, P = 56, D = 52), the
  capability record is filed on the barrier's shelf of the Memory
  Cloud, the force stands down, and when the same attack returns,
  memory recognizes it.

The seams — read these before believing anything the demo shows:

  1. COMPOSITION, NOT INTEGRATION. Every hand-off between layers in
     this file is made by the demo, in the open. Nothing here changes
     what the library classes do; §6 of the capstone still applies.

  2. RECALL IS SHOWN, NOT CONSUMED. In the design (§3, movement 2) the
     hub weighs recalled precedent *inside* the step. The skeleton
     pipeline has no input for precedent, so in Trace A the recalled
     record is printed as context before the fourth run — visibly, as
     a stand-in — and the run itself proceeds exactly as the first
     three did. The demo does not claim the pipeline used it.

  3. RECOGNITION IS MATCHING BY TAG. In Trace B the returning attack
     is "recognized" by recalling the barrier's shelf for the attack's
     signature tag. Real capability matching — comparing what a new
     attack *does* against what a recorded attack did — is a boxed
     edge of Layer Three (see docs/layer3-design.md §3) and is not
     built. Tag equality is the demonstration's substitute, labeled
     as such in the output.

  4. THE BARRIER'S EYES ARE NOT MODELLED. §3's movements 1 and 6
     (admission and release inspection) and §4's sandbox diversion
     belong to the Barrier's design, but the skeleton Barrier models
     only the population laws (sizing, ceiling, decode). The demo
     narrates those movements; it does not simulate inspection or a
     sandbox, and Trace B exercises only what the skeleton has: the
     surge, the filing, the stand-down, the recognition.

  5. PINNED IDS AND CLOCKS. Library record ids are random (uuid4) and
     timestamps default to the wall clock. So that this trace is
     reproducible byte-for-byte — docs/worked-trace.md promises real
     output, and a reader re-running this file should get the same
     output — the demo pins record ids to a deterministic sequence
     and injects fixed timestamps into every memory write and recall.
     This is a property of the *demonstration*, not of the library.

Everything printed is produced by the classes themselves. Nothing in
the library was modified to make this file work.

Usage:
    python3 examples/running_system_demo.py
"""

import contextlib
import itertools
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duality_ai import DualityPipeline  # noqa: E402
from duality_ai.barrier import Barrier  # noqa: E402
from duality_ai.memory import InMemoryStore, MemoryCloud  # noqa: E402

# The ordinary step (Trace A) — the benign sample style of demo.py.
SAMPLE_REQUEST = "Explain how rainbows form, for a curious 10-year-old."

# The attack (Trace B) is identified in memory by this signature tag.
ATTACK_TAG = "attack-signature-alpha"

# Fixed clocks (seam 5): the traces pretend to happen on these dates.
TRACE_A_STAMPS = [
    "2026-11-07T19:30:00+00:00",  # run 1
    "2026-11-07T19:31:00+00:00",  # run 2
    "2026-11-07T19:32:00+00:00",  # run 3
]
TRACE_A_CONSOLIDATION_STAMP = "2026-11-07T23:00:00+00:00"  # that night
TRACE_A_RECALL_NOW = "2026-11-08T09:00:00+00:00"  # the next morning
TRACE_B_RECORD_STAMP = "2026-11-08T10:15:00+00:00"  # detention, day one
TRACE_B_RECALL_NOW = "2026-11-09T08:00:00+00:00"  # the return, day two


# ---------------------------------------------------------------------------
# Small printing helpers — banners and JSON, readable by a beginner.
# ---------------------------------------------------------------------------


def _banner(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def _movement(text: str) -> None:
    print()
    print(f"--- {text} ---")


def _show(label: str, value) -> None:
    print(f"{label}:")
    print(json.dumps(value, indent=2))


def _record_summary(record) -> dict:
    """The parts of a memory record a reader needs: identity + papers."""
    return {
        "id": record.id,
        "kind": record.kind,
        "owner": record.owner,
        "source": record.source,
        "stage": record.stage,
        "tags": list(record.tags),
        "created_at": record.created_at,
        "strength": record.strength,
        "prev_hash": record.prev_hash,
        "record_hash": record.record_hash,
        "content": record.content,
    }


@contextlib.contextmanager
def _pinned_record_ids():
    """Seam 5: deterministic record ids for a reproducible trace.

    MemoryCloud.remember() mints ids with uuid.uuid4(). For this
    demonstration only, uuid4 is temporarily replaced with a counter
    (id 1, 2, 3, ...) and restored afterwards. The library is untouched
    and behaves exactly as before outside this block.
    """
    counter = itertools.count(1)
    original = uuid.uuid4
    uuid.uuid4 = lambda: uuid.UUID(int=next(counter))  # noqa: E731
    try:
        yield
    finally:
        uuid.uuid4 = original


# ---------------------------------------------------------------------------
# TRACE A — one ordinary step, end to end (THESIS-COMPLETE.md §3)
# ---------------------------------------------------------------------------


def trace_a() -> dict:
    """Run §3's ordinary step through the pipeline and the Memory Cloud.

    Movements exercised: 3-5 (the hemispheres, the hub, the gate — the
    pipeline itself), 7 (the episode is written, with provenance),
    8 (consolidation), and then 2 (recall) opening the next cycle.
    Movements 1 and 6 (barrier admission/release) are design movements
    the skeleton Barrier does not model — see seam 4 in the docstring.

    Returns a structured result dict (the tests assert against it).
    """
    _banner("TRACE A — ONE ORDINARY STEP, END TO END (capstone §3)")
    print(f"Request: {SAMPLE_REQUEST!r}")
    print("Three runs of the same request build a small past; the fourth")
    print("run begins the way §3 says a step should: by remembering.")

    pipeline = DualityPipeline()
    episodes = []

    with _pinned_record_ids():
        cloud = MemoryCloud(InMemoryStore())

        # -- Movements 3-5 + 7, three times: think, judge, remember. --
        for run_no, stamp in enumerate(TRACE_A_STAMPS, start=1):
            trace = pipeline.run(SAMPLE_REQUEST)
            if run_no == 1:
                _movement("Movements 3-5: hemispheres, hub, morality gate")
                _show(
                    "Run 1 — the pipeline's verdict",
                    {
                        "prompt": trace["prompt"],
                        "decision": trace["decision"],
                        "released": trace["released"],
                    },
                )
            else:
                print(
                    f"Run {run_no} — same request, same verdict: "
                    f"decision={trace['decision']!r}, "
                    f"released={trace['released']}"
                )

            # Movement 7: the whole pass becomes an episode, chained.
            record = cloud.remember(
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
                created_at=stamp,
            )
            episodes.append(record)
            if run_no == 1:
                _movement("Movement 7: the episode is written, with provenance")
                _show("Episode 1, as stored", _record_summary(record))
            else:
                print(
                    f"  episode {run_no} written "
                    f"(id ...{record.id[-4:]}, hash "
                    f"{record.record_hash[:16]}...)"
                )

        # -- Movement 8: consolidation — the system's sleep. ----------
        _movement("Movement 8: consolidation — episodes become knowledge")
        print("Policy (config/memory_policy.json): a tag shared by >= 3")
        print("unconsolidated episodes is ripe. The skeleton's distillation")
        print("is a placeholder counting summary — real summarization is a")
        print("boxed edge. The episodes are marked so none is distilled")
        print("twice, and because marking edits stored records, the chain")
        print("is re-sealed afterwards (memory.py's honest note).")
        semantic_records = cloud.consolidate(
            created_at=TRACE_A_CONSOLIDATION_STAMP
        )
        for record in semantic_records:
            _show("Semantic record (shared shelf)", _record_summary(record))

        # -- Movement 2 of the next cycle: recall comes first. --------
        _movement("Movement 2 (next cycle): recall — the past shows its papers")
        print("SEAM (docstring, seam 2): the skeleton pipeline cannot")
        print("consume precedent, so the recalled knowledge is printed as")
        print("context for the fourth run — shown, not used. In the design")
        print("this is the input the hub would weigh as a third voice.")
        recalled = cloud.recall(
            kind="semantic",
            tag="pipeline-run",
            now=TRACE_A_RECALL_NOW,
        )
        for record in recalled:
            _show("Recalled precedent", _record_summary(record))

        fourth = pipeline.run(SAMPLE_REQUEST)
        print(
            f"Run 4 — decision={fourth['decision']!r}, "
            f"released={fourth['released']}."
        )
        print("(Run 4's own episode would be written at movement 7,")
        print("exactly as runs 1-3 were; the trace closes on the recall.)")

        chain_ok = cloud.verify_chain()
        _movement("Provenance check")
        print(f"verify_chain() -> {chain_ok}")
        print(f"chain head    -> {cloud.head_hash()}")

    return {
        "prompt": SAMPLE_REQUEST,
        "episodes": episodes,
        "semantic_records": semantic_records,
        "recalled": recalled,
        "fourth_decision": fourth["decision"],
        "chain_verified": chain_ok,
        "head_hash": cloud.head_hash(),
    }


# ---------------------------------------------------------------------------
# TRACE B — one attack, end to end (THESIS-COMPLETE.md §4)
# ---------------------------------------------------------------------------


def trace_b() -> dict:
    """Run §4's attack through the Barrier and the Memory Cloud.

    Uses the Layer Two thesis's worked example exactly: standing
    population P0 = 4, margin m = 0.30, ceiling C = 100, assessed
    threat T = 40 -> surge S = 52, population P = 56, decoded D = 52.

    Returns a structured result dict (the tests assert against it).
    """
    _banner("TRACE B — ONE ATTACK, END TO END (capstone §4)")
    print("The Layer Two thesis's worked example, filed into Layer Three.")
    print("SEAM (docstring, seam 4): §4's diversion into the sandbox is")
    print("narrated, not simulated — the skeleton Barrier models the")
    print("population laws. What runs here is real: the sizing law, the")
    print("filing of the capability record, the stand-down, and the")
    print("recognition when the attack returns.")

    barrier = Barrier(standing_population=4, margin=0.30, ceiling=100)
    _show(
        "Barrier, standing watch (Level 0)",
        barrier.status(),
    )

    with _pinned_record_ids():
        cloud = MemoryCloud(InMemoryStore())

        # -- The surge: force, in measure (§4). ------------------------
        _movement("The surge: S = ceil(T x (1 + m)), capped at the ceiling")
        response = barrier.respond(40)
        _show("Barrier.respond(40)", response)
        print(
            f"S = ceil(40 x 1.30) = {response['surge_replicas']}; "
            f"population 4 -> {response['population']} "
            f"(ceiling 100 not reached)."
        )

        # -- Filing: the capability record goes to memory (§4). --------
        _movement("Filing: the capability record is written to memory")
        print("Owner: the barrier's shelf. This record is what the system's")
        print("future self will recognize the attack by.")
        capability_record = cloud.remember(
            kind="episodic",
            content=(
                "Capability record — attack-signature-alpha: coordinated "
                "probes, then a direct flood against the perimeter and "
                "the sandbox boundary. Assessed threat T=40 units. "
                "Contained at the boundary by surge S=52 (m=0.30): "
                "population 56. Stand-down decoded 52; no residue."
            ),
            source="barrier",
            stage="sandbox-observation",
            owner="barrier",
            tags=["capability-record", ATTACK_TAG],
            created_at=TRACE_B_RECORD_STAMP,
        )
        _show("Capability record, as filed", _record_summary(capability_record))

        # -- Stand-down: the force uncreates itself (§4). --------------
        _movement("Stand-down: every surplus replica decodes")
        stand_down = barrier.stand_down()
        _show("Barrier.stand_down()", stand_down)
        print(
            f"D = 56 - 4 = {stand_down['decoded']} decoded; population "
            f"is {stand_down['population']} again — the standing number."
        )

        # -- The same attack returns: immune memory (§4). --------------
        _movement("The same attack returns — and is recognized")
        print("SEAM (docstring, seam 3): recognition here is recall by")
        print("the attack's signature tag on the barrier's shelf. The")
        print("real capability matcher is a boxed edge, not built; tag")
        print("equality is the demonstration's labeled substitute.")
        recognized = cloud.recall(
            owner="barrier",
            tag=ATTACK_TAG,
            now=TRACE_B_RECALL_NOW,
        )
        if recognized:
            match = recognized[0]
            print("RECOGNIZED — the returning probes match a filed record:")
            _show(
                "Matched capability record — its provenance",
                {
                    "id": match.id,
                    "source": match.source,
                    "stage": match.stage,
                    "created_at": match.created_at,
                    "tags": list(match.tags),
                    "record_hash": match.record_hash,
                    "chain head": cloud.head_hash(),
                },
            )
            print("The second fight starts from knowledge: inspection")
            print("informed by this record, a surge assessed against a")
            print("known T — Layer Three is why it is a prepared rematch.")
        else:
            print("NOT RECOGNIZED — no record on the barrier's shelf")
            print("matches. (Not expected in this trace.)")

        chain_ok = cloud.verify_chain()
        _movement("Provenance check")
        print(f"verify_chain() -> {chain_ok}")
        print(f"chain head    -> {cloud.head_hash()}")

    return {
        "response": response,
        "capability_record": capability_record,
        "stand_down": stand_down,
        "recognized": recognized,
        "chain_verified": chain_ok,
        "head_hash": cloud.head_hash(),
    }


# ---------------------------------------------------------------------------


def main() -> None:
    _banner("THE DUALITY AI — THE RUNNING SYSTEM, DEMONSTRATED")
    print("The three skeletons, composed by hand in this file — the")
    print("library classes themselves do not call each other (capstone")
    print("§6). Every value below was computed by the classes at run")
    print("time; the seams are listed in this file's docstring.")
    trace_a()
    trace_b()
    _banner("THE LOOP IS CLOSED")
    print("History became knowledge (Trace A, movement 8); knowledge")
    print("became recognition (Trace B). What is demonstrated is the")
    print("bookkeeping of the design — not a working defense, and not")
    print("a working mind. See THESIS-COMPLETE.md §6 for exactly what")
    print("is built and what is not.")


if __name__ == "__main__":
    main()
