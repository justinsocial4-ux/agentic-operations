from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestrator.canonical import canonical_sha256
from orchestrator.capacity import compute_weekly_capacity
from orchestrator.contracts.domain import (
    ConsultantFitReceiptV2,
    EligibilityReceiptV2,
    ExactEvidenceCitationV2,
    PriorityReceiptV2,
    ReadinessEvidenceV2,
    ReadinessReceiptV2,
    WeeklyCapacityReceiptV1,
)
from orchestrator.contracts.enums import LaneV1
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.records import CapacityAvailabilityV1, ConsultantV2, WorkloadCommitmentV1
from orchestrator.mapping.health import PopulationCountsV1
from orchestrator.partial_sources import SourcePopulationStatusV1, evaluate_partial_source_policy

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)
HASH = "a" * 64


def _citation() -> ExactEvidenceCitationV2:
    return ExactEvidenceCitationV2(
        citation_id="citation-1", source_record_id="source-1",
        excerpt_sha256=hashlib.sha256(b"synthetic quote").hexdigest(),
        char_begin=0, char_end=15, exact_match_validated=True,
    )


def test_readiness_three_state_evidence_cardinality_fails_closed() -> None:
    with pytest.raises(ValidationError, match="SUPPORTED requires"):
        ReadinessEvidenceV2(
            dimension_id="business-problem", state="SUPPORTED",
            provenance="STRUCTURED", citations=(),
        )
    second = _citation().model_copy(update={"citation_id": "citation-2", "source_record_id": "source-2"})
    with pytest.raises(ValidationError, match="incompatibility receipt"):
        ReadinessEvidenceV2(
            dimension_id="business-problem", state="CONFLICT",
            provenance="TRANSCRIPT", citations=(_citation(), second),
        )
    with pytest.raises(ValidationError, match="UNKNOWN has no citation"):
        ReadinessEvidenceV2(
            dimension_id="business-problem", state="UNKNOWN",
            provenance="STRUCTURED", citations=(_citation(),),
        )
    unknown = ReadinessEvidenceV2(
        dimension_id="business-problem", state="UNKNOWN",
        provenance="STRUCTURED", citations=(),
    )
    assert unknown.state == "UNKNOWN" and unknown.citations == ()


def _consultant() -> ConsultantV2:
    return ConsultantV2(
        schema_version="orchestrator.consultant.v2",
        consultant_source_id="consultant-capacity", active_eligibility=True,
        supported_region_ids=("EMEA",), manager_approved_skill_ids=("security",),
        policy_receipt_ids=("policy-receipt",),
    )


def _availability() -> tuple[CapacityAvailabilityV1, ...]:
    return tuple(CapacityAvailabilityV1(
        schema_version="orchestrator.capacity-availability.v1",
        consultant_source_id="consultant-capacity", week_bucket=week,
        scheduled_units=20, time_off_reduction_units=2, source_as_of=NOW,
        completeness_state="COMPLETE", lineage_receipt_ids=(f"lineage-{week}",),
    ) for week in range(1, 5))


def _capacity(workload_units: int, availability: tuple[CapacityAvailabilityV1, ...] | None = None):
    accepted = PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())
    workloads = tuple(WorkloadCommitmentV1(
        schema_version="orchestrator.workload-commitment.v1",
        consultant_source_id="consultant-capacity", source_work_id=f"work-{week}",
        week_bucket=week, committed_units=workload_units, due_time=NOW,
        status="ACTIVE", lineage_receipt_ids=(f"work-lineage-{week}",),
    ) for week in range(1, 5))
    return compute_weekly_capacity(
        run_id="run-capacity", consultant=_consultant(),
        availability=_availability() if availability is None else availability,
        workloads=workloads, workload_population_complete=True,
        active_workload_statuses=frozenset({"ACTIVE"}), policy=accepted,
        policy_sha256=canonical_sha256(accepted), source_manifest_ids=("sm-capacity",),
        mapping_profile_sha256s=(HASH,), created_at=NOW,
    )


def test_weekly_capacity_is_exactly_four_30_minute_buckets_and_reconciles() -> None:
    receipt = _capacity(3)
    assert receipt.horizon_weeks == 4
    assert receipt.capacity_unit_minutes == 30
    assert tuple(bucket.week_bucket for bucket in receipt.buckets) == (1, 2, 3, 4)
    assert tuple(bucket.free_units for bucket in receipt.buckets) == (15, 15, 15, 15)
    assert receipt.complete_through_bucket == 4


def test_missing_bucket_is_unknown_not_zero_capacity_and_workload_monotonicity() -> None:
    missing = _capacity(0, _availability()[:3])
    assert missing.buckets[3].completeness_state == "INCOMPLETE"
    assert missing.buckets[3].free_units is None
    assert missing.complete_through_bucket == 3
    assert sum(bucket.free_units or 0 for bucket in _capacity(5).buckets) < sum(
        bucket.free_units or 0 for bucket in _capacity(1).buckets
    )


def test_exact_population_reconciliation_rejects_arithmetic_mismatch() -> None:
    with pytest.raises(ValidationError, match="reconciliation failed"):
        PopulationCountsV1(
            population="DEAL_WORK_REQUEST", declared=2, fetched=2, parsed=2,
            accepted=1, quarantined=0, excluded=0, duplicate=0,
            tombstoned=0, unmatched=0, read_complete=True,
        )


def test_partial_conversation_defaults_unknown_but_does_not_block_priority() -> None:
    decision = evaluate_partial_source_policy(
        lane=LaneV1.DEAL_PRIORITIZATION,
        statuses=(
            SourcePopulationStatusV1(
                source_manifest_id="sm-deals", population="DEAL_WORK_REQUEST", state="COMPLETE"
            ),
            SourcePopulationStatusV1(
                source_manifest_id="sm-policy", population="POLICY", state="COMPLETE"
            ),
            SourcePopulationStatusV1(
                source_manifest_id="sm-conversation", population="CONVERSATION_EVIDENCE", state="SOURCE_FAILED"
            ),
        ),
    )
    assert decision.ingested_state == "INGESTED_PARTIAL"
    assert decision.downstream_allowed
    assert decision.conversation_dimensions_default_unknown


def test_partial_capacity_is_consultant_local_while_roster_failure_blocks_assignment() -> None:
    statuses = (
        SourcePopulationStatusV1(source_manifest_id="sm-deals", population="DEAL_WORK_REQUEST", state="COMPLETE"),
        SourcePopulationStatusV1(source_manifest_id="sm-roster", population="CONSULTANT", state="COMPLETE"),
        SourcePopulationStatusV1(
            source_manifest_id="sm-capacity", population="CAPACITY_AVAILABILITY",
            state="BOUNDED_PARTIAL", affected_consultant_ids=("consultant-incomplete",),
        ),
        SourcePopulationStatusV1(source_manifest_id="sm-work", population="WORKLOAD_COMMITMENT", state="COMPLETE"),
        SourcePopulationStatusV1(source_manifest_id="sm-skills", population="SKILL_ASSERTION", state="COMPLETE"),
        SourcePopulationStatusV1(source_manifest_id="sm-policy", population="POLICY", state="COMPLETE"),
    )
    local = evaluate_partial_source_policy(lane=LaneV1.ASSIGNMENT_RECOMMENDATION, statuses=statuses)
    assert local.downstream_allowed
    assert local.incomplete_consultant_ids == ("consultant-incomplete",)

    blocked_statuses = tuple(
        row.model_copy(update={"state": "SOURCE_FAILED"}) if row.population == "CONSULTANT" else row
        for row in statuses
    )
    blocked = evaluate_partial_source_policy(lane=LaneV1.ASSIGNMENT_RECOMMENDATION, statuses=blocked_statuses)
    assert not blocked.downstream_allowed
    assert "CONSULTANT" in blocked.missing_required_populations


def test_domain_receipt_models_have_no_individual_win_rate_field() -> None:
    models = (
        ReadinessReceiptV2, PriorityReceiptV2, WeeklyCapacityReceiptV1,
        EligibilityReceiptV2, ConsultantFitReceiptV2,
    )
    assert all("win_rate" not in model.model_fields for model in models)
