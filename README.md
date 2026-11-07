# Duality AI

An original architecture concept by **Kenneth Lee Blum Jr** (November 7,
2026): an AI built the way its author believes a mind is organized — a base
language model topped by two separate reasoning hemispheres, one logical
and one creative; a central hub that weighs both sides' work and collapses
it into a single proposed step; and, before that step may proceed, a final
judgment against a preset library of morality clauses — strict, fully
detailed guidelines — weighed together with leniency within reason.

The full design, its limits, and the author's original dictation are in
[THESIS.md](THESIS.md). Read [DISCLAIMER.md](DISCLAIMER.md) before forming
any opinion about what this is: a theoretical design study, not production
software.

## Open Source — Contributions Welcome

This project is **public and open source**, released under the
[MIT License](LICENSE). Everybody is welcome to contribute and add to it:
read the thesis, argue with it, improve the clause library, build a better
implementation of the flow. See [CONTRIBUTING.md](CONTRIBUTING.md) for how
to take part and for the ground rules that keep contributions faithful to
the concept (the five-stage core stays intact, and the honesty rule —
no claims of consciousness or genuine moral understanding — is absolute).

## The flow

1. **Base layer** — the underlying language model; the foundation, not the
   whole system.
2. **Logical hemisphere** — evaluates: consistency checks, flags, pros and
   cons.
3. **Creative hemisphere** — generates: alternatives, framings, options.
4. **The hub** — weighs both outputs, keeps what is acceptable, consistent,
   and logical for the task, and merges them into one proposed step, with a
   trace of what was accepted and why.
5. **The morality gate** — judges the proposed step one final time against
   the preset morality-clause library: strict, fully detailed clauses,
   balanced by leniency within reason. It can pass the step, pass it with
   leniency recorded, or stop it.

## The clause library is data

The morality clauses are not hard-coded. They live in
[`config/morality_clauses.json`](config/morality_clauses.json) — a
human-readable JSON file the gate loads at startup. Each clause is a
record: an `id`, a `kind` (`hard` or `leniency`), the clause `text`, and,
for leniency clauses, the `condition` under which leniency applies. The
library can be inspected, debated, and revised without changing any code —
which is the point: in this design, the moral standard in force must be
something people can read.

## Repository structure

```
THESIS.md                     the full thesis (read this first)
README.md                     this file
DISCLAIMER.md                 status and limits of the project
config/
  morality_clauses.json       the preset morality-clause library (data)
docs/
  original-dictation.md       the author's original words, verbatim
src/duality_ai/
  __init__.py
  base.py                     stage 1: base layer
  hemispheres.py              stages 2–3: logical & creative stand-ins
  hub.py                      stage 4: the weighing/merging hub
  morality.py                 stage 5: the gate (loads the JSON library)
  pipeline.py                 runs all five stages end-to-end
examples/
  demo.py                     runnable demo; prints the trace as JSON
tests/
  test_pipeline.py            pytest suite for the skeleton
```

## Running the demonstration

The code is a **structural demonstration** of the flow — deterministic
stand-ins for each stage, pure Python 3, no external dependencies. It shows
the shape of the architecture and the hand-offs between stages; it is not
an implementation of real reasoning or real moral judgment.

```bash
PYTHONPATH=src python3 examples/demo.py
PYTHONPATH=src python3 -m pytest tests/
```

`DualityPipeline.run(prompt)` executes all five stages automatically and
returns the complete stage trace as a JSON-serializable dict; the demo
prints that trace as formatted JSON for a benign prompt and for a prompt
whose proposal trips a hard clause.

## Status

Public open-source concept by Kenneth Lee Blum Jr, November 2026, released
under the MIT License with contributions welcomed (see
[CONTRIBUTING.md](CONTRIBUTING.md)). Not production software; no claims of
consciousness, understanding, or moral judgment by the machine are made
anywhere in this repository — including, especially, in the thesis.
