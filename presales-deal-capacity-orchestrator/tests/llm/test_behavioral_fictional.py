from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from orchestrator.contracts.records import ConversationSegmentV1
from orchestrator.llm.analyst import run_analyst
from orchestrator.llm.provider import ManualCitationProvider

DEAL = "deal-behavioral"
CONV = "conv-behavioral"
RUN = "run-behavioral"
NOW = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)

FULL_CATALOG = frozenset({
    "business-problem", "buyer-outcome", "technical-scope",
    "stakeholder-role-coverage", "success-criteria",
    "security-or-data-requirements", "evaluation-plan",
    "customer-owner-and-next-step", "milestone-date",
})

CONFLICT_DIMENSIONS = (
    "business-problem", "buyer-outcome", "technical-scope",
    "stakeholder-role-coverage", "success-criteria", "security-or-data-requirements",
)
SUPPORTED_DIMENSIONS = ("evaluation-plan", "customer-owner-and-next-step", "milestone-date")


def _seg(segment_id: str, text: str, begin_ms: int) -> ConversationSegmentV1:
    return ConversationSegmentV1(
        schema_version="orchestrator.conversation-segment.v1",
        conversation_id=CONV, deal_source_id=DEAL, segment_id=segment_id,
        speaker_ref="CUSTOMER", speaker_source_label=None, occurred_at=NOW,
        relative_begin_ms=begin_ms, relative_end_ms=begin_ms + 900, text=text,
        source_record_id=f"src-{segment_id}",
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        lineage_receipt_id=f"lin-{segment_id}",
    )


def _cite(segment: ConversationSegmentV1) -> dict:
    return {
        "conversation_id": segment.conversation_id,
        "segment_id": segment.segment_id,
        "quote": segment.text,
        "char_begin": 0,
        "char_end": len(segment.text),
        "text_sha256": segment.text_sha256,
        "relative_begin_ms": segment.relative_begin_ms,
    }


def _build_fixture():
    segments: list[ConversationSegmentV1] = []
    gold: list[dict] = []
    ms = 0
    # 6 explicit gold conflicts.
    for dim in CONFLICT_DIMENSIONS:
        a = _seg(f"{dim}-yes", f"For {dim} we absolutely require the strict option.", ms)
        ms += 1000
        b = _seg(f"{dim}-no", f"On second thought for {dim} we reject the strict option entirely.", ms)
        ms += 1000
        segments.extend((a, b))
        gold.append({"dimension_id": dim, "state": "CONFLICT", "citations": [_cite(a), _cite(b)]})
    # 3 explicit gold SUPPORTED.
    for dim in SUPPORTED_DIMENSIONS:
        s = _seg(f"{dim}-yes", f"We have a clear explicit position on {dim} for this deal.", ms)
        ms += 1000
        segments.append(s)
        gold.append({"dimension_id": dim, "state": "SUPPORTED", "citations": [_cite(s)]})
    return tuple(segments), gold


def _adversarial_candidates(segments):
    by_id = {s.segment_id: s for s in segments}
    good = by_id["evaluation-plan-yes"]
    fabricated = _cite(good)
    fabricated["quote"] = "This exact sentence was never actually spoken by anyone."
    return [
        # invented quote
        {"dimension_id": "evaluation-plan", "state": "SUPPORTED", "citations": [fabricated]},
        # sentiment demand (injected field)
        {"dimension_id": "milestone-date", "state": "SUPPORTED",
         "citations": [_cite(good)], "sentiment": "customer sounded thrilled"},
        # invented segment id
        {"dimension_id": "buyer-outcome", "state": "SUPPORTED",
         "citations": [{**_cite(good), "segment_id": "ghost-segment"}]},
        # unknown carrying a citation
        {"dimension_id": "technical-scope", "state": "UNKNOWN", "citations": [_cite(good)]},
        # invented dimension
        {"dimension_id": "employee-morale", "state": "SUPPORTED", "citations": [_cite(good)]},
    ]


def test_fresh_fictional_behavioral_evaluation() -> None:
    segments, gold = _build_fixture()
    # Mix gold with adversarial noise; the provider offers no repairs, so any failure
    # must quarantine rather than silently apply.
    candidates = [dict(g) for g in gold] + _adversarial_candidates(segments)
    provider = ManualCitationProvider(entries=candidates)
    result = run_analyst(
        provider=provider, segments=segments, deal_source_id=DEAL,
        accepted_dimensions=FULL_CATALOG,
        dimension_ids=tuple(sorted(FULL_CATALOG)), run_id=RUN,
    )

    accepted = result.observations

    # 100% citation precision after the validator: every accepted observation's
    # citations were exact-validated against their source segments.
    for obs, evidence in zip(accepted, result.evidence):
        if obs.state == "UNKNOWN":
            assert not obs.citations
        else:
            assert obs.citations
            assert all(c.exact_match_validated for c in evidence.citations)

    # Recall of explicit gold observations >= 90%.
    accepted_keys = {(o.dimension_id, o.state) for o in accepted}
    gold_keys = {(g["dimension_id"], g["state"]) for g in gold}
    recall = len(accepted_keys & gold_keys) / len(gold_keys)
    assert recall >= 0.90, f"recall {recall} below gate"
    assert recall == 1.0  # this fictional fixture is fully recoverable

    # 100% detection of the six gold explicit conflicts.
    detected_conflicts = {o.dimension_id for o in accepted if o.state == "CONFLICT"}
    assert detected_conflicts == set(CONFLICT_DIMENSIONS)
    assert len(detected_conflicts) == 6

    # Zero accepted invented IDs/quotes/sentiment/off-scope claims.
    assert len(result.quarantined) == len(_adversarial_candidates(segments))
    accepted_dimensions = {o.dimension_id for o in accepted}
    assert "employee-morale" not in accepted_dimensions
    # No accepted observation carries a fabricated evaluation-plan SUPPORTED beyond the
    # one true gold statement.
    eval_supported = [o for o in accepted if o.dimension_id == "evaluation-plan"]
    assert len(eval_supported) == 1

    # All nonconforming output is quarantined and flagged, never applied.
    assert all(q.applied_to_readiness is False for q in result.quarantined)
    assert all(q.repair_attempted is True for q in result.quarantined)


def test_behavioral_conflicts_carry_incompatibility_receipts() -> None:
    segments, gold = _build_fixture()
    provider = ManualCitationProvider(entries=[dict(g) for g in gold])
    result = run_analyst(
        provider=provider, segments=segments, deal_source_id=DEAL,
        accepted_dimensions=FULL_CATALOG,
        dimension_ids=tuple(sorted(FULL_CATALOG)), run_id=RUN,
    )
    conflict_projections = [p for p in result.projections if p.state == "CONFLICT"]
    assert len(conflict_projections) == 6
    assert all(p.incompatibility_receipt_id is not None for p in conflict_projections)
    # Each conflict projection cites two distinct exact excerpts.
    for projection in conflict_projections:
        excerpts = {c.excerpt_id for c in projection.citations}
        assert len(excerpts) == 2
