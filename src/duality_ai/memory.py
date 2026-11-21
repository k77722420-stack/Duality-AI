"""Layer Three — the Memory Cloud: the system's long-term memory.

Structural demonstration only. Layer Three is the memory of the Duality
AI (design: THESIS-LAYER-3.md; working draft: docs/layer3-design.md):
Layer One thinks, Layer Two
protects, Layer Three remembers. This module implements the *foundation*
of that layer — the record schema, the provenance chain, the decay law,
and a consolidation pass — over a pluggable store. It stores and
retrieves text records; it does not learn, does not summarize with a
model, and is not a deployed memory service.

The build decision (Part 10 — the author's call) is HYBRID: the
foundation and core are authored here, while the replaceable edges are
boxed behind clean interfaces so others can add to them. The store is
the first boxed edge: ``MemoryStore`` is the contract, ``InMemoryStore``
and ``JsonFileStore`` are the implementations that ship — JsonFileStore
is the authored reference backend. Alternative backends, recall ranking
strategies, and embedding/index providers plug in behind the same
contract without touching the core.

The memory policy is data, not code: half-life, prune threshold,
protected tags, and the consolidation trigger are loaded from a JSON
file (default: ``config/memory_policy.json``) when the cloud is
constructed, so the laws in force can be read, debated, and revised
without touching this module — the same pattern as the morality gate's
clause library.

Design laws demonstrated here (the eight elements were ADOPTED by the
author on November 7, 2026, as recorded in THESIS-LAYER-3.md; the
numeric defaults they carry — half-life, prune threshold,
consolidation trigger — remain revisable working values):

  - Two memories. Records are *episodic* (what happened) or *semantic*
    (what is known), and each carries an *owner*: the logical shelf,
    the creative shelf, the shared shelf, or the barrier's shelf.
  - Provenance. Every record carries its source, its stage, and its
    timestamp, and is linked into a hash chain: each record's hash
    covers the previous record's hash, so the current contents of the
    store can be checked for edits made outside system operations.
  - Graceful forgetting. A record's strength decays with a half-life.
    Records that fade below the prune threshold are forgotten — EXCEPT
    records carrying a protected tag. The morality clauses ride under
    the "constitutional" tag: they are never forgettable.
  - Consolidation. Periodically, episodes that share a tag are
    distilled into a single semantic record — the design's "sleep."
    The distillation in this skeleton is a placeholder (a counting
    summary, honestly labeled in the code); real summarization is a
    boxed edge, not part of the authored core.

An honest note on the chain: consolidation (marking episodes) and
pruning (forgetting) are *system* acts, and after either one the chain
is re-sealed — the surviving records are re-linked in order. The chain
therefore attests to what the store now holds and detects edits made
outside the system's own operations; it is a structural demonstration
of provenance, not a forensic log that could survive an adversary with
write access to the store. Forgetting, where it applies, wins over
total recall by design: a forgotten record is gone, link and all.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import datetime, timezone
from pathlib import Path

try:  # POSIX file locking for the Option A storage discipline.
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX platforms
    fcntl = None  # type: ignore[assignment]

_DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "memory_policy.json"
)

GENESIS_HASH = "DUALITY-MEMORY-START"

RECORD_KINDS = ("episodic", "semantic")
RECORD_OWNERS = ("logical", "creative", "shared", "barrier")
CONSOLIDATED_TAG = "consolidated"


# ---------------------------------------------------------------------------
# Timestamps
# ---------------------------------------------------------------------------


def _as_iso(value: datetime | str | None) -> str:
    """Normalize a timestamp to an ISO 8601 UTC string."""
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        moment = value
    else:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat()


def _parse_iso(value: str) -> datetime:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


# ---------------------------------------------------------------------------
# The record
# ---------------------------------------------------------------------------


@dataclass
class MemoryRecord:
    """One memory: what it is, where it came from, and its chain link."""

    id: str
    kind: str  # "episodic" | "semantic"
    owner: str  # "logical" | "creative" | "shared" | "barrier"
    content: str
    source: str
    stage: str
    tags: list[str] = field(default_factory=list)
    created_at: str = ""  # ISO 8601 UTC
    strength: float = 1.0
    prev_hash: str = GENESIS_HASH
    record_hash: str = ""

    def canonical(self) -> str:
        """The record's hashable form: every field but the hashes."""
        body = {
            "id": self.id,
            "kind": self.kind,
            "owner": self.owner,
            "content": self.content,
            "source": self.source,
            "stage": self.stage,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "strength": self.strength,
        }
        return json.dumps(body, sort_keys=True, ensure_ascii=False)

    def compute_hash(self) -> str:
        """sha256 over the previous link plus this record's own form."""
        payload = self.prev_hash + self.canonical()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryRecord":
        return cls(**data)


# ---------------------------------------------------------------------------
# The store — the boxed edge
# ---------------------------------------------------------------------------


class MemoryStore(ABC):
    """The store contract: the first boxed edge of Layer Three.

    Implementations keep records in insertion order — the provenance
    chain is defined over that order, and ``all()`` must return it.
    Alternative backends (databases, vector stores, hosted services)
    implement this contract and plug in without touching the core.
    """

    @abstractmethod
    def put(self, record: MemoryRecord) -> None:
        """Append a record to the store."""

    @abstractmethod
    def get(self, record_id: str) -> MemoryRecord | None:
        """Return the record with this id, or None."""

    @abstractmethod
    def all(self) -> list[MemoryRecord]:
        """Return every record, in insertion order."""

    @abstractmethod
    def find(
        self,
        kind: str | None = None,
        owner: str | None = None,
        tag: str | None = None,
    ) -> list[MemoryRecord]:
        """Return records matching every given filter, in order."""

    @abstractmethod
    def remove(self, record_id: str) -> bool:
        """Remove the record with this id. Returns True if one was."""


def _matches(
    record: MemoryRecord,
    kind: str | None,
    owner: str | None,
    tag: str | None,
) -> bool:
    if kind is not None and record.kind != kind:
        return False
    if owner is not None and record.owner != owner:
        return False
    if tag is not None and tag not in record.tags:
        return False
    return True


class InMemoryStore(MemoryStore):
    """A dict-backed store: insertion-ordered, nothing persisted."""

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}

    def put(self, record: MemoryRecord) -> None:
        self._records[record.id] = record

    def get(self, record_id: str) -> MemoryRecord | None:
        return self._records.get(record_id)

    def all(self) -> list[MemoryRecord]:
        return list(self._records.values())

    def find(self, kind=None, owner=None, tag=None) -> list[MemoryRecord]:
        return [r for r in self._records.values() if _matches(r, kind, owner, tag)]

    def remove(self, record_id: str) -> bool:
        return self._records.pop(record_id, None) is not None


class JsonFileStore(MemoryStore):
    """The authored reference backend: one JSON file, atomically saved.

    Every mutation rewrites the whole file via a temporary file in the
    same directory followed by a rename, so a crash mid-write leaves
    the previous file intact. Records are dicts on disk, MemoryRecords
    in memory; the file can be read, debated, and backed up as data.

    Concurrency discipline — the author's storage decision (Ken,
    Nov 13, 2026; docs/storage-decision-brief-2026-11-12.md, Option A;
    implemented Nov 21, 2026):

    * A file lock (a ``<name>.lock`` file beside the store, flock
      where the platform offers it) is held across every
      reload–modify–save, so two instances — or two processes — cannot
      interleave a save.
    * Every mutation outside a batch first RELOADS the file and
      re-applies its change to the fresh contents, so a stale
      in-memory snapshot never overwrites records another instance
      wrote (TEC-5). An appended record whose chain link no longer
      matches the reloaded head is re-linked to that head before it
      lands, so cross-instance appends keep the provenance chain
      valid.
    * Each save writes a UNIQUE temporary file (``<name>.tmp-<uuid>``)
      and renames it over the store, so simultaneous saves cannot
      collide on a shared temp name.
    * Maintenance batches (``batch()``) reload once, let the core
      compute the full changed state in memory, and commit it in ONE
      atomic save (TEC-6): an interruption mid-maintenance leaves the
      old, still-valid file untouched.
    * Batch ownership is PER-THREAD (Linear audit fix, Nov 21, 2026):
      only the thread that opened a batch may re-enter it as
      "nested"; any other thread's batch waits on the lock and runs
      as its own batch afterwards. And a FAILED save — in a batch
      commit or a plain append — rolls the working copy back to the
      file's contents and removes the abandoned temp file, so an
      uncommitted record never lingers as a phantom.
    * Reads are transaction-isolated (Linear re-audit fix, Nov 21,
      2026): while a batch is open, reads (``get``/``all``/``find``)
      from any thread OTHER than the batch's owner serve the last
      COMMITTED snapshot, never the batch's uncommitted working
      copy; the owner still reads its own working copy. A commit
      publishes the new state in one step; an abort means the
      uncommitted records never existed for any reader.

    Outside a batch, reads serve the working copy, which outside a
    batch IS the committed state (every mutation saves at once or
    rolls back). The file is re-read at construction, before every
    mutation, and at the start of every batch. The discipline's
    limit is the brief's own: it protects against accidents and
    overlapping instances on one machine; it is not a multi-user
    database.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._records: list[MemoryRecord] = []
        self._lock_depth = 0
        self._lock_handle = None
        self._thread_lock = threading.RLock()
        self._batching = False
        self._batch_owner: int | None = None
        if self.path.exists():
            with self.path.open(encoding="utf-8") as handle:
                data = json.load(handle)
            self._records = [MemoryRecord.from_dict(d) for d in data]
        # The last committed state: what the file held at the last
        # successful save (or load). While a batch is open, non-owner
        # reads serve this snapshot, never the working copy.
        self._committed: list[MemoryRecord] = list(self._records)

    # -- the Option A machinery --------------------------------------

    @contextlib.contextmanager
    def _locked(self):
        """Hold the store's file lock (re-entrant within an instance).

        The outermost hold opens ``<name>.lock`` and flocks it, so a
        second JsonFileStore over the same path — in this process or
        another — waits until the reload–modify–save in progress has
        finished. Nested holds within one instance just count.
        """
        with self._thread_lock:
            if self._lock_depth:
                self._lock_depth += 1
                try:
                    yield
                finally:
                    self._lock_depth -= 1
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = (
                self.path.parent / (self.path.name + ".lock")
            ).open("a+")
            self._lock_handle = handle
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            self._lock_depth = 1
            try:
                yield
            finally:
                self._lock_depth = 0
                self._lock_handle = None
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                handle.close()

    def _reload_locked(self) -> None:
        """Replace the working copy with the file's current contents.

        The caller must hold the lock. Objects handed out earlier are
        not updated: after a reload, previously returned records are
        stale copies, exactly as after a fresh construction.
        """
        if self.path.exists():
            with self.path.open(encoding="utf-8") as handle:
                data = json.load(handle)
            self._records = [MemoryRecord.from_dict(d) for d in data]
        else:
            self._records = []
        # A reload makes the working copy the file's contents —
        # which is by definition the committed state.
        self._committed = list(self._records)

    def _save_locked(self) -> None:
        """Write the working copy in one atomic rename. Lock held.

        A failure before the rename completes removes the temporary
        file: a crashed save must not litter the directory with
        abandoned ``.tmp-<uuid>`` files (Linear audit, Nov 21, 2026).
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(
            f"{self.path.name}.tmp-{uuid.uuid4().hex}"
        )
        try:
            with tmp.open("w", encoding="utf-8") as handle:
                json.dump(
                    [r.to_dict() for r in self._records],
                    handle,
                    ensure_ascii=False,
                    indent=1,
                )
            os.replace(tmp, self.path)
            # The rename landed: the working copy IS the committed
            # state now, published to non-owner readers in one step.
            self._committed = list(self._records)
        except BaseException:
            with contextlib.suppress(OSError):
                tmp.unlink()
            raise

    def _save(self) -> None:
        """Save now — unless a batch is deferring the commit."""
        if self._batching:
            return
        with self._locked():
            self._save_locked()

    def _relink_locked(self, record: MemoryRecord) -> None:
        """Re-link an appended record to the reloaded chain head.

        The core chained the record to the head IT saw; if another
        instance has since extended the chain, the append is
        re-applied to the longer chain (the storage brief's
        reload–re-apply rule) so the chain still verifies.
        """
        head = (
            self._records[-1].record_hash
            if self._records
            else GENESIS_HASH
        )
        if record.prev_hash != head:
            record.prev_hash = head
            record.record_hash = record.compute_hash()

    @contextlib.contextmanager
    def batch(self):
        """A maintenance batch: compute in memory, commit once.

        On entry the store reloads under the lock, so the core
        computes over the file's true current contents. Saves are
        deferred while the batch runs; on clean exit the whole
        working copy is committed in ONE atomic save (TEC-6). If the
        body raises — or the commit itself fails — the uncommitted
        in-memory work is discarded by reloading, and the file keeps
        its previous, still-valid contents.

        Ownership is per-thread (Linear audit fix, Nov 21, 2026):
        a batch nested inside the SAME thread's batch simply joins
        the outer one, but a batch opened by any OTHER thread does
        not slip in through the nested path — it waits on the lock
        like every other mutation and runs as its own batch once
        the owner's batch has committed or rolled back. Before this
        fix the instance-wide ``_batching`` flag was checked before
        the lock, so a second thread entered unlocked: its in-place
        edits could leak into the owner's commit, or vanish under
        the owner's rollback.
        """
        if self._batching and self._batch_owner == threading.get_ident():
            yield
            return
        with self._locked():
            self._reload_locked()
            self._batching = True
            self._batch_owner = threading.get_ident()
            try:
                yield
                self._save_locked()
            except BaseException:
                self._reload_locked()  # discard the uncommitted work
                raise
            finally:
                self._batching = False
                self._batch_owner = None

    def _persist_mutation(self, record: MemoryRecord) -> None:
        """Re-save after an in-place change to a stored record.

        Consolidation marks episodes by editing their tags; for the
        file backend that edit must reach disk. Other backends may not
        need this hook — the core calls it only when the store has it.

        Under a maintenance batch the record IS the working copy and
        the batch's single commit carries the edit, so there is
        nothing to do. Outside a batch, the edit is re-applied to the
        freshly reloaded record with the same id, under the lock.
        """
        if self._batching:
            return
        with self._locked():
            self._reload_locked()
            fresh = self.get(record.id)
            if fresh is not None and fresh is not record:
                for f in fields(record):
                    if f.name != "id":
                        setattr(fresh, f.name, getattr(record, f.name))
            try:
                self._save_locked()
            except BaseException:
                # The edit never reached disk; do not leave it
                # standing in the working copy (Linear audit fix).
                self._reload_locked()
                raise

    def put(self, record: MemoryRecord) -> None:
        with self._locked():
            if not self._batching:
                self._reload_locked()
            self._relink_locked(record)
            self._records.append(record)
            try:
                self._save()
            except BaseException:
                if not self._batching:
                    # The save failed: the append never reached
                    # disk, so it must not linger in the working
                    # copy as a phantom record (Linear audit fix,
                    # Nov 21, 2026). Under a batch the batch's own
                    # rollback owns the working copy.
                    self._reload_locked()
                raise

    def _readable(self) -> list[MemoryRecord]:
        """The records a read from THIS thread may serve.

        Transaction isolation (Linear re-audit fix, Nov 21, 2026):
        while a batch owned by another thread is open, the working
        copy holds that batch's uncommitted state, so other threads
        read the last committed snapshot instead. The batch's owner
        — and every reader when no batch is open — reads the working
        copy, which outside a batch is the committed state.
        """
        if self._batching and self._batch_owner != threading.get_ident():
            return list(self._committed)
        return list(self._records)

    def get(self, record_id: str) -> MemoryRecord | None:
        for record in self._readable():
            if record.id == record_id:
                return record
        return None

    def all(self) -> list[MemoryRecord]:
        return self._readable()

    def find(self, kind=None, owner=None, tag=None) -> list[MemoryRecord]:
        return [r for r in self._readable() if _matches(r, kind, owner, tag)]

    def remove(self, record_id: str) -> bool:
        with self._locked():
            if not self._batching:
                self._reload_locked()
            before = len(self._records)
            self._records = [
                r for r in self._records if r.id != record_id
            ]
            if len(self._records) == before:
                return False
            try:
                self._save()
            except BaseException:
                if not self._batching:
                    # As in put(): a removal whose save failed is
                    # not a removal — restore the working copy.
                    self._reload_locked()
                raise
            return True


# ---------------------------------------------------------------------------
# The cloud — the authored core facade
# ---------------------------------------------------------------------------



class ChainIntegrityError(RuntimeError):
    """Maintenance refused to re-seal a provenance chain that does
    not verify (see MemoryCloud._require_verified_chain)."""

class MemoryCloud:
    """Layer Three's core: remember, recall, consolidate, forget.

    Constructed with a store (any ``MemoryStore`` — the boxed edge)
    and a policy (loaded from ``config/memory_policy.json`` unless a
    path or a ready dict is given). An optional ``write_hook`` is the
    guarded-write extension point: in the full design every write
    passes the barrier and the morality gate before it is remembered;
    in this skeleton a registered hook stands in that doorway. A hook
    that returns False refuses the write — nothing is stored, and
    ``remember`` returns None.
    """

    def __init__(
        self,
        store: MemoryStore | None = None,
        policy_path: str | Path | None = None,
        policy: dict | None = None,
        write_hook=None,
    ) -> None:
        self.store: MemoryStore = store if store is not None else InMemoryStore()
        if policy is not None:
            self.policy = dict(policy)
        else:
            path = (
                Path(policy_path)
                if policy_path is not None
                else _DEFAULT_POLICY_PATH
            )
            with path.open(encoding="utf-8") as handle:
                self.policy = json.load(handle)
        self.halflife_days: float = float(self.policy["halflife_days"])
        self.prune_threshold: float = float(self.policy["prune_threshold"])
        self.protected_tags: list[str] = list(self.policy["protected_tags"])
        self.consolidate_min_episodes: int = int(
            self.policy["consolidate_min_episodes"]
        )
        self.write_hook = write_hook
        # Ids of records the most recent recall() excluded because
        # their provenance seal did not verify (see recall()).
        self.last_recall_exclusions: list[str] = []

    def set_write_hook(self, hook) -> None:
        """Register (or clear, with None) the guarded-write hook."""
        self.write_hook = hook

    def _store_batch(self):
        """The store's maintenance batch, when it offers one.

        JsonFileStore implements the Option A batch (reload once,
        compute in memory, one atomic commit — TEC-6). Stores without
        one (InMemoryStore) need no batching: a plain null context.
        """
        batch = getattr(self.store, "batch", None)
        return batch() if batch is not None else contextlib.nullcontext()

    # -- the chain -----------------------------------------------------

    def head_hash(self) -> str:
        """The hash the next record will link to (genesis if empty)."""
        records = self.store.all()
        return records[-1].record_hash if records else GENESIS_HASH

    def verify_chain(self) -> bool:
        """Recompute the chain over the store's current contents.

        Each record's prev_hash must equal the previous record's hash
        (genesis for the first), and each record_hash must equal the
        hash of its own current contents. Any edit made outside the
        system's own operations — a changed word, a swapped link —
        breaks one of those checks.
        """
        prev = GENESIS_HASH
        for record in self.store.all():
            if record.prev_hash != prev:
                return False
            if record.record_hash != record.compute_hash():
                return False
            prev = record.record_hash
        return True

    def _verified_record_seals(self) -> set[tuple[str, str]]:
        """The (id, record_hash) seals of records that verify.

        The same two checks verify_chain() makes — each record's
        prev_hash equals the previous record's hash (genesis for the
        first) and each record_hash equals the hash of its own
        current contents — evaluated per record over the store's
        insertion order, so a caller can exclude exactly the records
        that fail instead of trusting or rejecting the whole shelf.

        The result is keyed by the record's own seal, NOT by its id
        alone (Linear re-audit fix, Nov 21, 2026): the first version
        of this filter collected verified IDs and admitted any
        record carrying one, so a corrupted record that REUSED an
        honest record's id was recalled as genuine — its own seal
        was never checked. Two records sharing an id are now judged
        independently: each is admitted only under its own
        (id, record_hash) pair, and a pair verifies only when the
        record standing under it recomputes to that very hash.
        """
        verified: set[tuple[str, str]] = set()
        prev = GENESIS_HASH
        for record in self.store.all():
            if (
                record.prev_hash == prev
                and record.record_hash == record.compute_hash()
            ):
                verified.add((record.id, record.record_hash))
            prev = record.record_hash
        return verified

    def _require_verified_chain(self, action: str) -> None:
        """Refuse to let maintenance launder a broken chain.

        Perplexity finding (full audit, 2026-11-13; verified by
        execution): an unauthorized edit left verify_chain() False —
        detectable — until ordinary maintenance pruned an old record
        and re-sealed the chain over the forged content, after which
        the tampering verified as genuine. Maintenance therefore
        checks the chain BEFORE it changes anything: a chain that
        does not verify is evidence, and evidence is not re-sealed
        away. The Option A storage discipline (implemented Nov 21,
        2026) makes maintenance atomic; this guard remains in force
        alongside it — atomicity protects against interruption, the
        guard against laundering a tampered chain.
        """
        if not self.verify_chain():
            raise ChainIntegrityError(
                f"{action} refused: the provenance chain does not "
                "verify. Maintenance will not re-seal over a possible "
                "tampering; the records are unchanged."
            )

    def _reseal_chain(self) -> None:
        """Re-link the chain in insertion order after a system act.

        Called after consolidation and pruning change stored records
        (see the module docstring's honest note): the surviving
        records are re-chained over their current contents.
        """
        prev = GENESIS_HASH
        for record in self.store.all():
            record.prev_hash = prev
            record.record_hash = record.compute_hash()
            prev = record.record_hash
            persist = getattr(self.store, "_persist_mutation", None)
            if persist is not None:
                persist(record)

    # -- decay -----------------------------------------------------------

    def _decayed_strength(
        self, record: MemoryRecord, now: datetime
    ) -> float:
        age_days = (
            now - _parse_iso(record.created_at)
        ).total_seconds() / 86400.0
        if age_days <= 0:
            return record.strength
        return record.strength * 0.5 ** (age_days / self.halflife_days)

    # -- writing ---------------------------------------------------------

    def remember(
        self,
        kind: str,
        content: str,
        source: str,
        stage: str = "memory",
        owner: str = "shared",
        tags=(),
        created_at: datetime | str | None = None,
        strength: float = 1.0,
    ) -> MemoryRecord | None:
        """Write a memory, chained to the current head.

        The record is offered to the write hook first (the guarded
        write): a hook returning False refuses the write, nothing is
        stored, and None is returned. Otherwise the stored record is
        returned.
        """
        if kind not in RECORD_KINDS:
            raise ValueError(f"kind must be one of {RECORD_KINDS}")
        if owner not in RECORD_OWNERS:
            raise ValueError(f"owner must be one of {RECORD_OWNERS}")
        record = MemoryRecord(
            id=uuid.uuid4().hex,
            kind=kind,
            owner=owner,
            content=content,
            source=source,
            stage=stage,
            tags=list(tags),
            created_at=_as_iso(created_at),
            strength=float(strength),
            prev_hash=self.head_hash(),
        )
        record.record_hash = record.compute_hash()
        if self.write_hook is not None and not self.write_hook(record):
            return None
        self.store.put(record)
        return record

    # -- reading ---------------------------------------------------------

    def recall(
        self,
        kind: str | None = None,
        owner: str | None = None,
        tag: str | None = None,
        text: str | None = None,
        now: datetime | str | None = None,
    ) -> list[MemoryRecord]:
        """Recall memories, strongest (least decayed) first.

        Returned records are copies carrying their *current* decayed
        strength; the stored records are never mutated by a recall.
        ``text`` matches a case-insensitive substring of the content.

        Provenance is checked on the way out (Linear audit fix,
        Nov 21, 2026): a record whose seal does not verify — content
        edited outside the system's operations, hashes untouched —
        is EXCLUDED from the results instead of being recalled as
        genuine, and its id is surfaced on
        ``last_recall_exclusions`` rather than the exclusion being
        hidden. Maintenance already refused to re-seal over such a
        record; recall now refuses to serve it as the past. The
        check is per record, under the record's own seal: a
        corrupted record that reuses an honest record's id fails
        its own hash check and is excluded — and surfaced — even
        though its honest twin is served (Linear re-audit fix).
        """
        moment = _parse_iso(_as_iso(now))
        found = self.store.find(kind=kind, owner=owner, tag=tag)
        if text is not None:
            needle = text.lower()
            found = [r for r in found if needle in r.content.lower()]
        verified = self._verified_record_seals()
        self.last_recall_exclusions = [
            r.id for r in found if (r.id, r.record_hash) not in verified
        ]
        found = [r for r in found if (r.id, r.record_hash) in verified]
        # tags are copied explicitly: dataclasses.replace is shallow,
        # so without the copy a recalled record would share its tags
        # list with the stored record, and a caller's append would
        # rewrite stored memory outside the write path — invalidating
        # hashes and changing pruning eligibility. (Audit fix,
        # Nov 12, 2026.)
        ranked = [
            replace(
                r,
                tags=list(r.tags),
                strength=self._decayed_strength(r, moment),
            )
            for r in found
        ]
        ranked.sort(key=lambda r: r.strength, reverse=True)
        return ranked

    # -- consolidation: the system's sleep --------------------------------

    def consolidate(
        self, created_at: datetime | str | None = None
    ) -> list[MemoryRecord]:
        """Distill clusters of episodes into semantic records.

        (The full docstring lives on ``_consolidate``.) The pass runs
        inside the store's maintenance batch when it offers one
        (Option A, TEC-6): the whole changed + resealed chain is
        computed in memory and committed in one atomic save, so an
        interruption cannot leave a half-maintained file behind.
        """
        with self._store_batch():
            return self._consolidate(created_at)

    def _consolidate(
        self, created_at: datetime | str | None = None
    ) -> list[MemoryRecord]:
        """Distill clusters of episodes into semantic records.

        For each tag shared by at least ``consolidate_min_episodes``
        episodic records not yet consolidated, one semantic record is
        written — owned by the shared shelf, tagged with the cluster's
        tag and "consolidation" — and the episodes are marked with the
        "consolidated" tag so a later pass leaves them alone.

        The distillation here is a placeholder: the semantic record's
        content is a counting summary ("Consolidated N episodes about
        'tag'."), not a model-written summary. Real summarization is a
        boxed edge. What the core contributes is the *policy*: when a
        cluster is ripe, where its distillation lives, and that each
        episode is distilled at most once.
        """
        self._require_verified_chain("Consolidation")
        stamp = _as_iso(created_at)
        episodes = self.store.find(kind="episodic")
        pending: dict[str, list[MemoryRecord]] = {}
        for record in episodes:
            if CONSOLIDATED_TAG in record.tags:
                continue
            # TEC-9 (Linear audit, 2026-11-13): count DISTINCT
            # episode ids per tag. One episode wearing the same tag
            # three times is one episode; it previously distilled
            # into "knowledge" all by itself.
            for tag in set(record.tags):
                cluster = pending.setdefault(tag, [])
                if all(existing.id != record.id for existing in cluster):
                    cluster.append(record)

        created: list[MemoryRecord] = []
        marked: list[MemoryRecord] = []
        claimed: set[str] = set()
        # Each episode is distilled at most once (review finding 5):
        # an episode carrying several ripe tags is claimed by the most
        # specific (smallest) cluster first; later clusters count only
        # the episodes still unclaimed.
        # Amendment (Lux, at Ken's direction, 2026-11-13): bookkeeping
        # tags (gate-decision, gate:*, any tag containing ':') claim
        # LAST. In Trace A the original order let 'gate:proceed' claim
        # the episodes and the topic summary ('pipeline-run') vanished;
        # topic tags are the knowledge, gate tags are the bookkeeping.
        def _bookkeeping(tag: str) -> bool:
            return tag.startswith("gate") or ":" in tag

        for tag, cluster in sorted(
            pending.items(),
            key=lambda item: (_bookkeeping(item[0]), len(item[1]), item[0]),
        ):
            cluster = [r for r in cluster if r.id not in claimed]
            if len(cluster) < self.consolidate_min_episodes:
                continue
            summary = self.remember(
                kind="semantic",
                content=f"Consolidated {len(cluster)} episodes about '{tag}'.",
                source="consolidation",
                stage="consolidation",
                owner="shared",
                tags=[tag, "consolidation"],
                created_at=stamp,
            )
            if summary is None:
                continue  # the write hook refused the distillation
            created.append(summary)
            for record in cluster:
                claimed.add(record.id)
                if CONSOLIDATED_TAG not in record.tags:
                    record.tags.append(CONSOLIDATED_TAG)
                marked.append(record)

        if marked or created:
            # Remembering the summaries moved the chain head; marking
            # edited stored records. Re-seal so the chain attests to
            # the store as it now stands (module docstring, honest
            # note), and persist the marks for file-backed stores.
            for record in marked:
                persist = getattr(self.store, "_persist_mutation", None)
                if persist is not None:
                    persist(record)
            self._reseal_chain()
        return created

    # -- forgetting --------------------------------------------------------

    def decay_and_prune(
        self, now: datetime | str | None = None
    ) -> int:
        """Forget records that have faded below the prune threshold.

        (The full docstring lives on ``_decay_and_prune``.) Like
        consolidation, the pass runs inside the store's maintenance
        batch when it offers one (Option A, TEC-6): compute in
        memory, commit once.
        """
        with self._store_batch():
            return self._decay_and_prune(now)

    def _decay_and_prune(
        self, now: datetime | str | None = None
    ) -> int:
        """Forget records that have faded below the prune threshold.

        A record's current strength is its stored strength decayed by
        the policy half-life to ``now``. Records below the threshold
        are removed — UNLESS any of their tags is protected. Protected
        records are never pruned, however faint they become: the
        clauses are never forgettable. Returns the count pruned. The
        chain is re-sealed over the survivors.
        """
        self._require_verified_chain("Pruning")
        moment = _parse_iso(_as_iso(now))
        pruned = 0
        for record in self.store.all():
            if any(tag in self.protected_tags for tag in record.tags):
                continue
            if self._decayed_strength(record, moment) < self.prune_threshold:
                if self.store.remove(record.id):
                    pruned += 1
        if pruned:
            self._reseal_chain()
        return pruned
