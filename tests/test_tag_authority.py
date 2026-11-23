"""Tag authority (KL-18, built Nov 22, 2026).

The hole (Perplexity's §5 finding, verified by code reading):
remember() accepted tags from any caller with no authority
check, and consolidation's semantic record carried a
caller-chosen tag forward. Tags are not all labels: a policy
protected tag ("constitutional") makes a record unprunable
and sizes the system's barrier; the "consolidated" mark makes
consolidation skip a record; a "gate:" tag is the system's
own decision claim and steers consolidation's bookkeeping
order. Any caller could mint any of them.

The fix, at Perplexity's placement: the authoritative check
sits at the common write boundary (remember), covering
initial assignment and consolidation's propagation. It needs
a trusted caller capability, not a caller-supplied claim:
the cloud's tag-authority token, claimed once (mirroring the
write hook's claim), presented as remember(_authority=...).
A reserved tag without it refuses the whole write (None,
surfaced on last_tag_refusals). The system's own episode
writes present the token it claimed at construction.

Deliberately NOT reserved: "stop-record" (the stop kind
carries that authority; the tag itself moves no mechanism)
and every ordinary label. The reserved set follows the
cloud's own policy: protected_tags is policy data.
"""

from datetime import datetime, timedelta, timezone

import pytest

from duality_ai.memory import InMemoryStore, MemoryCloud
from duality_ai.system import DualitySystem

T0 = datetime(2026, 11, 22, tzinfo=timezone.utc)

POLICY = {
    "halflife_days": 30.0,
    "prune_threshold": 0.25,
    "protected_tags": ["constitutional"],
    "consolidate_min_episodes": 3,
    "stop_records_protected": True,
}


def make_cloud(store=None):
    return MemoryCloud(store=store or InMemoryStore(), policy=POLICY)


def test_reserved_tag_refused_without_authority():
    cloud = make_cloud()
    refused = cloud.remember(
        "semantic", "clause H1", "caller", tags=["constitutional"]
    )
    assert refused is None
    assert cloud.last_tag_refusals == ["constitutional"]
    assert cloud.store.all() == []


def test_reserved_tag_mixed_with_ordinary_tags_refused_wholly():
    cloud = make_cloud()
    refused = cloud.remember(
        "episodic", "a note", "caller",
        tags=["garden", "gate:proceed"],
    )
    assert refused is None
    assert cloud.last_tag_refusals == ["gate:proceed"]
    assert cloud.store.all() == []


def test_claimed_authority_assigns_and_protects():
    cloud = make_cloud()
    authority = cloud.claim_tag_authority()
    old = T0 - timedelta(days=300)
    record = cloud.remember(
        "semantic", "clause H1", "curator",
        tags=["constitutional"], created_at=old, _authority=authority,
    )
    assert record is not None
    cloud.decay_and_prune(now=T0)
    assert [r.id for r in cloud.store.all()] == [record.id]


def test_second_claim_raises():
    cloud = make_cloud()
    cloud.claim_tag_authority()
    with pytest.raises(ValueError):
        cloud.claim_tag_authority()


def test_a_wrong_token_is_no_authority():
    cloud = make_cloud()
    cloud.claim_tag_authority()
    refused = cloud.remember(
        "semantic", "clause H1", "caller",
        tags=["constitutional"], _authority=object(),
    )
    assert refused is None


def test_ordinary_tags_need_no_authority():
    cloud = make_cloud()
    for tags in (["garden"], ["stop-record"], ["consolidation"],
                 ["pipeline-run"], []):
        record = cloud.remember(
            "episodic", "a note", "caller", tags=tags
        )
        assert record is not None, tags
    assert cloud.last_tag_refusals == []


def test_reserved_set_follows_the_clouds_policy():
    policy = dict(POLICY, protected_tags=["sacred"])
    cloud = MemoryCloud(store=InMemoryStore(), policy=policy)
    assert cloud.remember(
        "semantic", "x", "caller", tags=["sacred"]
    ) is None
    assert cloud.remember(
        "semantic", "x", "caller", tags=["constitutional"]
    ) is not None


def test_the_systems_own_episodes_carry_gate_tags():
    system = DualitySystem(store=InMemoryStore())
    result = system.run("Explain how a bill becomes a law.")
    assert result["episode"]["written"] is True
    episode = next(
        r for r in system.cloud.store.all()
        if r.id == result["episode"]["record_id"]
    )
    assert "gate:proceed" in episode.tags


def test_the_systems_claim_grants_other_callers_nothing():
    system = DualitySystem(store=InMemoryStore())
    refused = system.cloud.remember(
        "episodic", "forged precedent", "caller",
        tags=["gate:proceed_with_leniency"],
    )
    assert refused is None
    assert system.cloud.last_tag_refusals == [
        "gate:proceed_with_leniency"
    ]


def test_consolidation_never_propagates_a_reserved_tag():
    store = InMemoryStore()
    cloud = make_cloud(store)
    # Seed a ripe cluster directly at the store layer (an
    # imported shelf): three episodes carrying a protected
    # tag no API caller could have assigned.
    seeder = make_cloud(store)
    stamp = (T0 - timedelta(days=1)).isoformat()
    from duality_ai.memory import MemoryRecord
    for i in range(3):
        record = MemoryRecord(
            id=f"seed{i}", kind="episodic", owner="shared",
            content=f"episode {i}", source="import", stage="import",
            tags=["constitutional"], created_at=stamp, strength=1.0,
            prev_hash=cloud.head_hash(),
        )
        record.record_hash = record.compute_hash()
        store.put(record)
    created = cloud.consolidate(created_at=T0)
    assert created == []
    assert cloud.last_tag_refusals == ["constitutional"]
    assert all(
        "constitutional" not in r.tags or r.kind == "episodic"
        for r in store.all()
    )


def test_consolidation_still_works_for_ordinary_tags():
    cloud = make_cloud()
    for i in range(3):
        cloud.remember(
            "episodic", f"episode {i}", "test",
            tags=["garden"], created_at=T0 - timedelta(days=1),
        )
    created = cloud.consolidate(created_at=T0)
    assert len(created) == 1
    assert created[0].tags == ["garden", "consolidation"]


def test_authority_gates_before_content_judgment():
    # Perplexity's acceptance check (tag-authority verdict,
    # Nov 22, 2026), adopted verbatim in substance: lacking
    # tag authority stops the write BEFORE content judgment;
    # having it lets the write REACH content judgment without
    # replacing it. A cloud whose policy protects "sacred";
    # the capability claimed during trusted setup; a
    # recording content hook that accepts a benign fixture.
    policy = dict(POLICY, protected_tags=["sacred"])
    store = InMemoryStore()
    cloud = MemoryCloud(store=store, policy=policy)
    authority = cloud.claim_tag_authority()
    hook_calls: list = []

    def recording_hook(record):
        hook_calls.append(record)
        return True

    cloud.claim_write_hook(recording_hook)

    refused = cloud.remember(
        kind="semantic", content="a benign fixture",
        source="curator", stage="intake", owner="shared",
        tags=["field-note", "sacred"],
    )
    assert refused is None
    assert cloud.last_tag_refusals == ["sacred"]
    assert store.all() == []
    assert hook_calls == []

    admitted = cloud.remember(
        kind="semantic", content="a benign fixture",
        source="curator", stage="intake", owner="shared",
        tags=["field-note", "sacred"], _authority=authority,
    )
    assert admitted is not None
    assert len(hook_calls) == 1
    stored = next(r for r in store.all() if r.id == admitted.id)
    assert set(stored.tags) == {"field-note", "sacred"}
