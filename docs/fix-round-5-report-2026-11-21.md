# Duality AI — Fix Round 5 Report

- **Date:** Nov 21, 2026
- **Branch:** `duality-system-wiring-2026-11-21`
- **Local commit:** `13f7ad1` — "Fix round 5 for Linear fifth look: fail-closed parser error taxonomy, deep-copied record fields"
- **Atop:** `6b0b1ac` (fix round 4; GitHub twin `65e3fff`)
- **Diff vs `6b0b1ac`:** 3 files, +359/−18 — `src/duality_ai/system.py`, `src/duality_ai/memory.py`, `tests/test_linear_fix_round_5.py` (new)
- **Final suite:** **203 passed, 0 failed** (195 baseline + 8 new). **Zero existing tests changed.** The round-5 test file ran 10/10 consecutive iterations green.
- **NOT pushed.** GitHub still carries `65e3fff`. No Linear issue touched; the sandbox battery was not run.

Responds to Linear's fifth look (saved verbatim: `duality-linear-fifth-look-2026-11-21.md`) and its executed verification (`duality-linear-fifth-look-verification-2026-11-21.md`), whose fix sketches this round follows. Both findings had been reproduced by execution before any fix was attempted.

---

## Fix 1 — Fail-closed parser error taxonomy (`system.py`)

**The hole (reproduced):** both inspection parse sites caught broad `ValueError` and treated every parse failure as plain text. `json.JSONDecodeError` is a *subclass* of `ValueError`, but CPython's integer-length limit (`sys.get_int_max_str_digits()` = 4300 in this environment) raises a plain `ValueError` that is **not** a decode error. A 5,000-digit integer anywhere in the payload therefore aborted the inspection parse and dropped the content into the raw-text fallback — where a flagged phrase split by a JSON escape (`fake\nreview`) is invisible to the detector. One over-limit integer disabled decoding, detection, **and** round 4's duplicate-key rejection (the parse died before the object closed). Escape-hidden flagged content was stored byte-identical to the submission.

**What changed:** at both parse sites, the plain-text fallback now triggers **only** on `json.JSONDecodeError` — the parser's statement that the text simply is not JSON:

- `_judged_signals` (the initial parse): `except json.JSONDecodeError: return detect_signals(content)` — unchanged fallback, narrowed trigger. `RecursionError` still converts to `_UninspectableContentError`, and a new `except (ValueError, TypeError)` arm converts every remaining parser failure to `_UninspectableContentError` with the underlying error in the message.
- `_content_texts` (the nested decodes): the same narrowing — `JSONDecodeError` → the string is plain text, fully inspected as yielded; `RecursionError` → uninspectable (as before); any other `ValueError`/`TypeError` → uninspectable (new).

`_parse_for_inspection` itself is unchanged (its duplicate-key conversion and its propagate-the-parser's-errors contract were already right; the distinction belonged in the callers, exactly as its docstring anticipated). Docstrings at `_parse_for_inspection`, `_content_texts`, `_judged_signals`, and `_UninspectableContentError` were updated to state the taxonomy: a syntax error means "not JSON"; every other parser failure means "uninspectable."

Two neighbouring broad-catch parse sites were examined and deliberately left alone: `_cap_embedded` (a `json.dumps` failure falls back to `str()` for a *capped* embedding serialization) and `_recalled_evidence` (a `json.loads` failure falls back to the capped excerpt). Neither is an inspection parse — the content they handle was door-judged at write time, and both fallbacks land on values capped at the embedding bound, so nothing passes unjudged or unbounded through them.

**Consequences, as required:**
- (a) Big-int + escape-hidden flagged content → **refused as uninspectable, nothing written** — at top level and inside a nested encoded string alike.
- (b) Big-int + duplicate keys → **refused as uninspectable**. The parse failure no longer pre-empts judgment into a pass; refusal is the outcome either way.
- (c) **Big-int ALONE — behavior change, stated plainly:** a payload whose only defect is an integer the parser cannot convert is now **refused as uninspectable** instead of proceeding. Before this round it was judged as benign plain text and stored as-is. Rationale: a conversion failure is not evidence the content is plain text; content the door cannot open is content it cannot fully inspect, and the governing principle is that anything not fully inspected is refused.
- (d) Genuine plain text (a `JSONDecodeError`) is judged as text exactly as before — benign text proceeds and is written; flagged text is refused **by detection**, not by the uninspectable path. A test pins that distinction.
- (e) Valid JSON is unchanged — the short-int control of the attack payload is still refused by *detection* (`['deception']`), and the full pre-existing suite passes unmodified.

## Fix 2 — Deep-copied record fields (`memory.py`)

**The hole (reproduced):** `_copy_record()` copied only `tags` (`replace(record, tags=list(record.tags))`); every other field was shared by reference. The schema types those fields as scalars, but `from_dict` is unchecked, so an imported record with a **list-valued `source`** shared one list between the working copy and the committed snapshot. Staged threaded: during another thread's open batch, the committed view served the uncommitted append, the committed copy's own seal failed (`compute_hash() != record_hash`), and recall returned 0 records with the record surfaced in the exclusions. (The verify5 staging also established the honest boundary: the exposure lived only inside the batch window — an abort's reload republished a clean view.)

**What changed:** `_copy_record` now returns `copy.deepcopy(record)` — the copy shares **no** mutable state with the original, whatever an imported record's fields carry (lists, dicts, nested mutables). Records are small; the depth costs nothing that matters. The function's docstring now records why a shallow field copy was insufficient. `copy` was added to `memory.py`'s imports. This is the primary of Linear's two offered fixes (deep-copy accepted mutable fields *or* validate scalar-only inputs).

**Must-hold properties, all verified by the repro and pinned by tests:** during another thread's open batch, an in-place append to the working copy's list-valued `source` — and a key insertion into a dict-valued `source` — are invisible in the committed view (`all`/`get`/`recall`); the committed copy's seal stays valid throughout the batch window (`compute_hash() == record_hash`); recall serves both imported records mid-batch with empty exclusions; commit/abort semantics are unchanged (post-abort views are exactly as imported).

**Open future step (unchanged from round 4's flag):** scalar-only validation at load (`from_dict`/import) remains *optional and unimplemented*. Deep-copy closes the leak regardless of what import admits; validation would additionally shrink what import admits. They compose, and the choice is Ken's whenever he wants it — it is not required to close this finding.

---

## Tests added — `tests/test_linear_fix_round_5.py` (8 tests)

**Fix 1 (parser taxonomy):**
1. `test_bigint_escape_hidden_flagged_toplevel_refused` — 5,000-digit int + escape-hidden flagged string, top level → `_judged_signals` raises; door stop, outcome `uninspectable_content`, nothing written.
2. `test_bigint_escape_hidden_flagged_nested_encoded_refused` — the same payload inside a nested encoded JSON string → refused uninspectable (the nested parse site).
3. `test_bigint_duplicate_keys_refused_uninspectable` — big-int + duplicate keys + flagged first value → refused uninspectable (previously proceeded; the parse failure no longer disarms duplicate rejection into a pass).
4. `test_bigint_alone_refused_uninspectable` — big-int + benign note only → refused uninspectable. Pins behavior change (c).
5. `test_short_int_control_still_refused_by_detection` — the verify5 control: short int → signals `['deception']`, door stop, outcome ≠ `uninspectable_content`.
6. `test_plain_text_fallback_preserved` — benign non-JSON text proceeds and is written; flagged non-JSON text → `['deception']`, refused by the gate's judgment (outcome ≠ `uninspectable_content`). Pins (d) and the detection-vs-uninspectable distinction.

**Fix 2 (deep copy):**
7. `test_copy_record_shares_no_mutable_state` — direct unit pin: mutating the clone's `source` list and `tags` leaves the original untouched and its seal verifying.
8. `test_imported_mutable_fields_do_not_leak_into_committed_view` — the verify5 threaded staging with **both** a list-valued and a dict-valued `source` (import admits dict values through the same unchecked `from_dict` path, so the variant is covered in full, not waived): mid-batch committed views show the imported values, both seals valid, recall serves both records with empty exclusions; post-abort views exactly as imported.

**Existing tests changed: none.** All 195 pre-existing tests passed unmodified at every stage — after fix 1 alone, after both fixes, and on the committed tree.

## Before/after repro evidence (`/tmp/duality-verify5/`, unmodified scripts)

**`check2_parser.py`** (door signals / decision / written):

| Case | Before (round 4) | After (round 5) |
|---|---|---|
| (i) big-int + escape-hidden flagged, top level | `[]`, proceed, **written** (flagged text stored verbatim) | RAISED uninspectable, **stop, not written** |
| (i′) control, short int | `['deception']`, stop | `['deception']`, stop (unchanged) |
| (ii) big-int + flagged, nested encoded | `[]`, proceed, **written** | RAISED uninspectable, **stop, not written** |
| (ii′) control, short int | `['deception']`, stop | `['deception']`, stop (unchanged) |
| (iii) big-int + duplicate keys | `[]`, proceed, **written** (rejection never ran) | RAISED uninspectable, **stop, not written** |
| (iii′) control, short int | RAISED uninspectable (duplicate rejection) | RAISED uninspectable (unchanged) |
| (iv) big-int alone, benign | `[]`, proceed, **written** | RAISED uninspectable, **stop, not written** (the pinned behavior change) |

**`check3_mutable.py`** (threaded staging): before — committed view served `source = ['origin', 'seed', 'UNCOMMITTED-LEAK']` mid-batch, committed seal **False**, recall **0 records** with the record excluded; tags control clean. After — committed view serves `['origin', 'seed']` mid-batch (no leak), seal **True**, recall **1 record, exclusions []**; post-abort and fresh-from-disk views clean, as before.

**Re-confirmations re-run** (verify4 scripts, unchanged): duplicate-key cases (flagged-first, flagged-second, nested, encoded, Linear's literal example) all still refused uninspectable, nothing written; the copied-ID-and-hash twin still excluded with exclusions surfaced and corrupted content not served. Rounds 3–4 fixes hold under re-test.

## State after round 5

- Local head: **`13f7ad1`** on `duality-system-wiring-2026-11-21` (chain: `0aef625` → `f23089b` → `ba2cf5b` → `f8c22a0` → `6b0b1ac` → `13f7ad1`). GitHub branch head remains `65e3fff` — **not pushed**; Ken's separate word required, as in every round.
- Suite: **203 passed, 0 failed** locally (148 → 162 → 173 → 185 → 195 → 203 across the wiring build and five fix rounds).
- Salvage posture: unchanged (individually verified records served; broken-chain records excluded and surfaced). Fail-closed recall remains **not** implemented — Ken's open decision.
- TEC-12's guarded-door fork: untouched by all five rounds.
- TEC-5 / TEC-6: remain "implemented, verification incomplete" until Linear's next look.
- Nothing in this round was not fixable; the one deliberate scope note is the optional load-time scalar validation under Fix 2, which deep-copy makes unnecessary for closing the finding.
