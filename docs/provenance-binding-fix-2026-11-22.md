# Provenance-binding fix — Nov 22, 2026

Branch: `duality-provenance-binding-2026-11-22` (from main @ 816c957).
Directed by Ken the evening the finding landed; design follows
Perplexity's verdict on her own executed probes.

## The finding

Eligibility and authenticity are separate checks, and only the
first existed. The reuse filter verified that an embedded
entry's id named a live, seal-verifying record; it never
compared the entry's text with that record. An executed
write-path probe (Lux, Nov 22) confirmed the consequence: a
caller-authored episode-shaped write whose `recalled` entry
named a genuine record's id but carried fabricated text was
admitted through the door, and recall served the fabrication
under the genuine id. The genuine record was never altered —
the defect is false attribution in structured recall.
Perplexity's severity call: a significant recall-integrity
defect, and a blocker for treating embedded quotations as
verified source evidence or exposing them to a model under
that assurance.

## The fix — both boundaries, as she recommended

The embedding contract makes a genuine entry a deterministic
projection of its source (reference fields + the source's gate
decision, or a capped excerpt of its content). The fix
recomputes that projection and compares:

- **Door (admission).** `_judge_write` first verifies every
  embedded entry of any write presenting the `recalled`
  envelope: shelf lists well-formed, entries dicts with text
  ids naming verified records, and each entry EQUAL to
  `_expected_quotation_evidence(source)`. Failure refuses the
  write with judgment outcome `unverifiable_quotation`, before
  any authorization is consumed, on both the recorded and blind
  paths. Kind and source are caller claims and are never
  treated as trusted construction.
- **Filter (serve).** `_recall_precedent` builds the genuine
  embedding of every verified record once per run and passes
  the map to `_filter_dead_quotations`; an entry under an
  eligible id that does not match its source's embedding is
  dropped and reported. This is the protection for pre-fix and
  imported records. The membership-only mode remains available
  when no map is passed (unit isolation); it is not the shipped
  configuration.

Her nesting question is answered by the representation: a
genuine entry has exactly five fields and carries no nested
envelope; nested structures can exist only inside an excerpt,
where they are the source's own first-200-characters — text
attributed correctly by construction.

## The second fix — hook ownership (her Ask 5(b) verdict)

`MemoryCloud` gains `claim_write_hook`: a system claims its
cloud's hook at construction; claiming an already-hooked cloud
raises; a claimed hook cannot be replaced or cleared through
`set_write_hook`. One correction to the verdict's model,
verified in the code: `DualitySystem` builds its OWN cloud
over its store and accepts no cloud parameter, so two systems
sharing a store each govern their own writes through their own
door by construction — her traced substitution (S1's writes
judged by S2's door) is not constructible through the
constructor. The claim guards the surface that does exist:
silent replacement of a live system's door. Her prioritized
test is included with the expectations the actual wiring
supports (each door is its own system's; S1's registered
leniency path works with S2 present on the same store).

## Tests

- New: tests/test_provenance_binding.py — 10 tests (forged
  excerpt refused; unknown id refused; malformed envelope
  refused; genuine quotation admitted; filter binding drops the
  mismatch and keeps the genuine; a pre-fix forged record's
  entry dropped at serve; claim conflict raises; owned hook
  irreplaceable, door still standing; bare-cloud hook still
  freely settable; two systems, one store, own doors).
- Existing tests changed: ONE fixture —
  tests/test_reuse_policy_filter.py's decision-embed test built
  its container entry by hand with a `decision` field for a
  plain-note source whose genuine embedding is an excerpt; the
  door now (correctly) refuses that fabrication. The fixture
  embeds the genuine projection via
  `_expected_quotation_evidence`; every assertion is unchanged.
- Suite: 263 -> 273, all passing locally.

## Record

KNOWN-LIMITATIONS gains entries 19 (quotation binding) and 20
(hook ownership), both marked addressed with their remaining
bounds stated in the entries. Nothing merges without a
reviewer's verdict and Ken's word.
