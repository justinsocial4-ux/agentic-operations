from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from orchestrator.canonical import canonical_sha256
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.records import ConversationSegmentV1, DealWorkRequestV2
from orchestrator.llm.analyst import run_analyst
from orchestrator.llm.provider import ManualCitationProvider
from orchestrator.readiness import compute_readiness

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)
DEAL = "deal-phase6"
RUN = "run-phase6-int"


def _policy() -> PolicyV2:
    return PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())


def _deal() -> DealWorkRequestV2:
    return DealWorkRequestV2.model_validate({
        "schema_version": "orchestrator.deal-work-request.v2",
        "work_request_id": "work-phase6",
        "deal_source_id": DEAL,
        "region_source_value": "EMEA",
        "region_id": "EMEA",
        "request_type": "DEMO_REQUEST",
        "milestone_type": "POC",
        "milestone_due_time": NOW + timedelta(days=6),
        "effort_units": 10,
        "commercial_amount": "200000.00",
        "commercial_currency": "USD",
        "commercial_basis": "demo-corporate-bookings-v1",
        "required_skill_ids": ("security",),
        "required_languages": ("en",),
        "required_working_window_overlap_minutes": 120,
        "continuity_consultant_id": "consultant-continuity",
        "structured_evidence_references": ("evidence-1",),
        "conversation_ids": ("conv-p6",),
        "source_freshness": NOW,
        "lineage_receipt_ids": ("lineage-deal", "lineage-normalized"),
    })


def _seg(segment_id: str, text: str, begin_ms: int) -> ConversationSegmentV1:
    return ConversationSegmentV1(
        schema_version="orchestrator.conversation-segment.v1",
        conversation_id="conv-p6", deal_source_id=DEAL, segment_id=segment_id,
        speaker_ref="CUSTOMER", speaker_source_label=None, occurred_at=NOW,
        relative_begin_ms=begin_ms, relative_end_ms=begin_ms + 900, text=text,
        source_record_id=f"src-{segment_id}",
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        lineage_receipt_id=f"lin-{segment_id}",
    )


def _cite(seg: ConversationSegmentV1) -> dict:
    return {
        "conversation_id": seg.conversation_id, "segment_id": seg.segment_id,
        "quote": seg.text, "char_begin": 0, "char_end": len(seg.text),
        "text_sha256": seg.text_sha256, "relative_begin_ms": seg.relative_begin_ms,
    }


def test_transcript_analyst_evidence_satisfies_versioned_readiness_dimension() -> None:
    # A transcript observation satisfies exactly one versioned PolicyV2 dimension.
    seg = _seg("seg-sc", "Success means a signed pilot by the 30th.", 0)
    provider = ManualCitationProvider(entries=[{
        "dimension_id": "success-criteria", "state": "SUPPORTED", "citations": [_cite(seg)],
    }])
    result = run_analyst(
        provider=provider, segments=(seg,), deal_source_id=DEAL,
        accepted_dimensions=frozenset(_policy().readiness_dimensions),
        dimension_ids=("success-criteria",), run_id=RUN,
    )
    assert len(result.evidence) == 1
    evidence = result.evidence[0]
    assert evidence.dimension_id == "success-criteria"
    assert evidence.provenance == "TRANSCRIPT"

    policy = _policy()
    receipt = compute_readiness(
        run_id=RUN, deal=_deal(), policy=policy, policy_sha256=canonical_sha256(policy),
        source_manifest_ids=("sm-transcript",), mapping_profile_sha256s=("e" * 64,),
        evidence=result.evidence, created_at=NOW,
    )
    by_dimension = {d.dimension_id: d for d in receipt.dimensions}
    assert by_dimension["success-criteria"].state == "SUPPORTED"
    assert "TRANSCRIPT" in by_dimension["success-criteria"].provenance
    # The receipt records exact citation IDs/hashes — no quote text.
    assert by_dimension["success-criteria"].citation_ids
    assert "quote" not in receipt.model_dump(mode="json")


def test_quarantined_observation_never_reaches_readiness_receipt() -> None:
    seg = _seg("seg-sc", "Success means a signed pilot by the 30th.", 0)
    fabricated = _cite(seg)
    fabricated["quote"] = "Success means nothing was ever agreed."  # not in segment
    provider = ManualCitationProvider(entries=[{
        "dimension_id": "success-criteria", "state": "SUPPORTED", "citations": [fabricated],
    }])
    result = run_analyst(
        provider=provider, segments=(seg,), deal_source_id=DEAL,
        accepted_dimensions=frozenset(_policy().readiness_dimensions),
        dimension_ids=("success-criteria",), run_id=RUN,
    )
    assert result.evidence == ()
    assert len(result.quarantined) == 1

    policy = _policy()
    receipt = compute_readiness(
        run_id=RUN, deal=_deal(), policy=policy, policy_sha256=canonical_sha256(policy),
        source_manifest_ids=("sm-transcript",), mapping_profile_sha256s=("e" * 64,),
        evidence=result.evidence, created_at=NOW,
    )
    by_dimension = {d.dimension_id: d for d in receipt.dimensions}
    # The quarantined observation did not silently mark the dimension SUPPORTED.
    assert by_dimension["success-criteria"].state == "UNKNOWN"
    # And UNKNOWN is not treated as absence: the deal simply lands in inspection.
    assert receipt.queue_lane == "DEAL_INSPECTION"
