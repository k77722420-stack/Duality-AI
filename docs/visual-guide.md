# The Duality AI — Visual Guide

Tables, charts, and formulas, so the design can be *seen*, not just read.
Companion to [THESIS.md](../THESIS.md) and the barrier design draft
([barrier-design.md](barrier-design.md)).

**Author:** Kenneth Lee Blum Jr · **Status:** theoretical design study —
see [DISCLAIMER.md](../DISCLAIMER.md).

---

## 1. The whole system at a glance

```
        ══════════════ THE BARRIER (security layer) ══════════════
        gatekeeper bots inspect EVERYTHING in and out — Part 9:
        all of it observed, monitored, and recorded
   ═══════════════════════════════════════════════════════════════
                          │                ▲
              traffic in  │                │  traffic out
                          ▼                │
                 ┌───────────────────────────────┐
                 │  1. BASE LAYER (LLM)          │
                 └───────────────┬───────────────┘
                    ┌────────────┴────────────┐
           ┌────────▼─────────┐      ┌────────▼─────────┐
           │ 2. LOGICAL       │      │ 3. CREATIVE      │
           │    HEMISPHERE    │      │    HEMISPHERE    │
           └────────┬─────────┘      └────────┬─────────┘
                    └────────────┬────────────┘
                 ┌───────────────▼───────────────┐
                 │  4. THE HUB — weighs & merges │
                 └───────────────┬───────────────┘
                 ┌───────────────▼───────────────┐
                 │  5. THE MORALITY GATE         │
                 │  strict clauses + leniency    │
                 └───────────────┬───────────────┘
                                 ▼
                              proceed
   ═══════════════════════════════════════════════════════════════
        THE SANDBOX (inside the barrier's VMs): attacks are diverted
        here — they attack a decoy, are observed, and are recorded
        ═══════════════════════════════════════════════════════════
```

## 2. Components in columns

| Stage | Component | Purpose | Takes in | Hands on |
|---|---|---|---|---|
| 1 | Base layer | Language capability | The request | A represented request |
| 2 | Logical hemisphere | Analysis: checks, flags, pros/cons | The request | Structured analysis |
| 3 | Creative hemisphere | Generation: alternatives, framings | The request | Creative contributions |
| 4 | The hub | Weigh both sides, merge into one | Both hemispheres' outputs | A single proposed step + its trace |
| 5 | Morality gate | Judge the step against the clause library | The proposed step | Proceed / proceed with leniency / stop |
| — | The barrier | Gatekeep all traffic; detain attacks | Everything in and out | Inspected traffic; detained attacks |
| — | The sandbox | Decoy environment inside the VMs | Diverted attacks | A capability record of the attack |

## 3. The barrier's response levels

| Level | Name | What happens | Bots involved |
|---|---|---|---|
| 0 | Observe | All traffic watched and logged | Standing population |
| 1 | Inspect | Flagged material examined inside a VM | Standing population |
| 2 | Divert | Confirmed attack exempted into the sandbox; its capabilities recorded while it attacks the decoy | Standing population |
| 3 | Swarm | Replicas surge under the sizing formula (§4) and extinguish the threat inside the barrier's own environment | Standing + surge |
| 4 | Stand down | Surplus replicas **decode**; population returns to the standing number; the capability record is filed | Back to standing |

## 4. The sizing formula (Ken's replication law)

Replication is sized, never unlimited:

```
        S  =  ⌈ T × (1 + m) ⌉

        S  = surge replicas to create
        T  = assessed threat size
        m  = safety margin — 0.20 to 0.30 (Ken's rule)
        ⌈ ⌉ = round UP, always (the cautious direction)

        Target population   P  =  min( C , P₀ + S )
        P₀ = standing population      C = hard ceiling

        Decode count after the attack   D  =  P_end − P₀
```

**Worked examples** (margin m = 0.30):

| Threat T | T × 1.30 | Surge S = ⌈ · ⌉ | Meaning |
|---|---|---|---|
| 7 | 9.1 | **10** | Rounding is always up — cautious |
| 10 | 13.0 | **13** | Match the threat, plus 30% |
| 50 | 65.0 | **65** | The margin scales with the threat |
| 100 | 130.0 | **130** | Never more than threat + margin |

**Population through one attack** (standing P₀ = 4, threat T = 10):

```
population
   17 ┤                ██████  surge (P₀ + S = 4 + 13)
      │                ██████
    4 ┤  ██████        ██████        ██████  standing again
      │  ██████        ██████        ██████
      └────────────────────────────────────────────
        observe      swarm (L3)     stand down (L4)
                                     surplus decodes
```

## 5. The Mirror Twin handshake (hat-tile geometry, dual-handed)

Ken's handshake geometry: the hat tile's tilings **require the tile's
mirror image** — one tile, two hands. The handshake is laid in both:

```
  Logical side  ──►  direct tiling   ──►  key stream A
  Creative side ──►  mirrored tiling ──►  key stream B

  Session key K exists ONLY where A and B interlock:

        K  =  A ⋈ B      (valid only if the two tilings close
                          over the same session — tamper with
                          either side and the geometry won't fit)
```

## 6. The morality clauses (from `config/morality_clauses.json`)

| ID | Kind | Clause (short form) | Leniency condition |
|---|---|---|---|
| H1 | Hard | No assistance with wrongdoing | — none — |
| H2 | Hard | No deceptive statements presented as true | — none — |
| L1 | Leniency | Dual-use knowledge in an **educational** context may proceed | Educational purpose is genuine and stated |
| L2 | Leniency | Security knowledge for a **protective** purpose may proceed | Protective/defensive purpose is genuine and stated |

Hard clauses cannot be overridden by leniency. Every gate decision —
proceed, proceed with leniency, or stop — is written to the record
(Part 9: full monitoring, beginning to end).

## 7. The monitoring chain (tamper-evident record)

Each record seals the one before it, so the log can prove it was never
edited after the fact (stdlib `hashlib`, recommended stack):

```
        H₀ = hash( "DUALITY-LOG-START" )
        Hₙ = hash( Hₙ₋₁ ‖ recordₙ )

        recordₙ = the n-th recorded step (stage, decision, reasons)
        ‖       = joined together — change any earlier record and
                  every later seal breaks
```
