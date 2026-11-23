# Stop records — design (Nov 22, 2026)

**Status:** DESIGN ONLY. No code yet. The build is a separate round
on Ken's direction.
**Decision it implements:** TEC-12, decided by Ken Nov 22, 2026 —
when the gate stops a step, the system keeps a METADATA-ONLY stop
record: signals, the gate decision and its reasons, a timestamp,
and a cryptographic fingerprint of the request. The flagged
payload itself is NEVER stored.
**Review input folded in:** Perplexity's §5 (Nov 22, 2026) —
what stop records must NOT inherit from the episode mechanism —
plus the door principle established by the F-S1 rounds: a write's
authority comes out-of-band from the run that produced it, never
from the record's own claims.

## Purpose

Today a stopped step leaves no trace in memory: the refusal exists
only in the run's return value. Stop records give the system an
auditable history of its own refusals — what was stopped, under
which clauses, when — without retaining the material that was
stopped. They serve pattern-spotting (repeated attempts), audit
(the gate's behavior over time), and precedent (a later step can
learn that a class of request was stopped before, and why).

## The record

A stop record is a DISTINCT record kind, `stop`, with its own
narrow schema. Its payload is built from an ALLOWLIST of
system-derived fields — nothing else can enter it:

- `record_type`: "stop"
- `run_id`, `step_id`: the run and step identities, system-issued
- `timestamp`: system clock, at the decision
- `policy_version`: the clause-library / policy version in force
- `decision`: "stop"
- `signals`: the judged signal labels (labels, not text)
- `reasons`: stable reason CODES (clause ids + outcome codes) —
  no free-form detail text
- `request_fingerprint`: SHA-256 of the stopped request, so a
  repeat of the identical request is recognizable without keeping
  the request

**Excluded by schema, not by convention:** the proposal text, the
model's draft, recalled content, free-form reason strings, parser
input, and exception strings. "Metadata-only" is enforced by the
schema validator at the write path: a stop payload carrying any
non-allowlist key is refused.

## Authorization

- The stop write is authorized out-of-band, bound to the
  OPERATION: the system registers the exact stop payload's digest
  at construction (the F-S1 mechanism), and the registration names
  the record kind — an episode authorization can never authorize
  a stop record, nor the reverse.
- The stop DECISION carries a durable idempotency key (run_id +
  step_id + request fingerprint): the same stop, recorded twice
  by accident, is one record.
- **A stop remains a stop even if its audit write fails.** The
  gate's decision never depends on the stop record being written.
  An audit-write failure is surfaced separately (the run's return
  value reports `stop_record: "failed"` distinctly from the
  decision), never silently, and never converted into a release.

## Retention and use

- Stop records are NOT eligible for ordinary recall or
  consolidation by default. They are not episodes; nothing quotes
  them into later episodes, and the consolidation pass ignores
  the `stop` kind (consolidation pools episodic records only —
  the kind separation enforces this by construction).
- A dedicated, explicit read path (e.g. `find_stops(fingerprint)`
  / a precedent check by signal set) is the only consumer, added
  when a real use is built — not speculatively.
- Retention follows the memory policy like other records EXCEPT
  the fingerprint and reason codes are the audit trail: whether
  stop records decay under the half-life law or ride a protected
  tag is an OPEN QUESTION for the build round (see below) — it is
  not decided by this design.

## The door question, answered in advance

The F-S1 rounds settled how a system-built record is authorized;
stop records inherit that answer and Perplexity's sharpening:
verified against their recorded basis AND registered out-of-band,
bound to the operation and the exact validated payload. The door
judges a stop record's payload like any write — an allowlist
payload of labels and codes carries no flagged text, so the blind
judgment passes it on its merits; the registration exists so the
SCHEMA claim ("this is a system-built stop record") is verified,
not merely asserted by the payload's `record_type` field.

## Open questions for the build round

1. Retention: do stop records decay (30-day half-life) or are
   they protected? Audit value argues protected; the
   forgetting-by-design law argues decay. Ken's call.
2. Precedent: should a repeat fingerprint change a later step's
   handling (e.g. faster stop), or is the record purely
   historical until a use is designed?
3. Tag authority (KNOWN-LIMITATIONS 18) interacts here: when tag
   authority is built, stop records' tags are system-assigned
   only.
4. Policy-at-reuse (Perplexity §2a) applies to stop precedent
   too, when a consumer exists: a stop recorded under an older
   clause library is evidence about that library's decision.

## What this design deliberately does not do

- No change to the gate, the blind door judgment, or episode
  handling.
- No salvage: a broken chain stays fail-closed (Ken's decision,
  Nov 22, 2026); stop records do not change that.
- No new record kind lands in `RECORD_KINDS` until the build
  round writes the schema validator and its tests with it.
