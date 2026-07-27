from __future__ import annotations

import hashlib
import inspect
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from orchestrator.canonical import canonical_sha256
from orchestrator.capacity import compute_weekly_capacity
from orchestrator.contracts.domain import ExactEvidenceCitationV2, ReadinessEvidenceV2
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.records import (
    AnalystCitationV2,
    AnalystObservationV2,
    CapacityAvailabilityV1,
    ConsultantV2,
    CurrencyNormalizationApprovalV1,
    DealWorkRequestV2,
    SkillAssertionV1,
    WorkloadCommitmentV1,
)
from orchestrator.eligibility import compute_consultant_fit, evaluate_eligibility
from orchestrator.readiness import compute_readiness, evidence_from_validated_observation
from orchestrator.scoring import _round_half_even, score_priority

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 3, 9, tzinfo=timezone.utc)
HASH_A = "a" * 64
HASH_B = "b" * 64
SOURCES = ("sm-deals", "sm-conversation")
MAPPINGS = (HASH_A, HASH_B)


def policy() -> PolicyV2:
    return PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())


def deal(**changes: object) -> DealWorkRequestV2:
    payload: dict[str, object] = {
        "schema_version": "orchestrator.deal-work-request.v2",
        "work_request_id": "work-phase2",
        "deal_source_id": "deal-phase2",
        "region_source_value": "EMEA",
        "region_id": "EMEA",
        "request_type": "DEMO_REQUEST",
        "milestone_type": "POC",
        "milestone_due_time": NOW + timedelta(days=6),
        "effort_units": 10,
        "commercial_amount": "200000.00",
        "commercial_currency": "USD",
        "commercial_basis": "demo-corporate-bookings-v1",
        "required_skill_ids": ("security", "integration"),
        "required_languages": ("en",),
        "required_working_window_overlap_minutes": 120,
        "continuity_consultant_id": "consultant-continuity",
        "structured_evidence_references": ("evidence-1",),
        "conversation_ids": ("conversation-1",),
        "source_freshness": NOW,
        "lineage_receipt_ids": ("lineage-deal", "lineage-normalized"),
    }
    payload.update(changes)
    return DealWorkRequestV2.model_validate(payload)


def citation(dimension: str, suffix: str = "1") -> ExactEvidenceCitationV2:
    digest = hashlib.sha256(f"{dimension}-{suffix}".encode()).hexdigest()
    return ExactEvidenceCitationV2(
        citation_id=f"citation-{dimension}-{suffix}",
        source_record_id=f"source-{dimension}-{suffix}",
        conversation_id="conversation-1",
        segment_id=f"segment-{dimension}-{suffix}",
        excerpt_sha256=digest,
        char_begin=0,
        char_end=12,
        relative_begin_ms=100,
        exact_match_validated=True,
    )


def readiness_for(item: DealWorkRequestV2, *, conflict_dimension: str | None = None):
    accepted = policy()
    evidence = []
    for dimension in accepted.readiness_dimensions:
        if dimension == conflict_dimension:
            evidence.append(ReadinessEvidenceV2(
                dimension_id=dimension,
                state="CONFLICT",
                provenance="TRANSCRIPT",
                citations=(citation(dimension, "left"), citation(dimension, "right")),
                incompatibility_receipt_id="incompatibility-reviewed-1",
            ))
        else:
            evidence.append(ReadinessEvidenceV2(
                dimension_id=dimension,
                state="SUPPORTED",
                provenance="TRANSCRIPT" if dimension == "success-criteria" else "STRUCTURED",
                citations=(citation(dimension),),
            ))
    return compute_readiness(
        run_id="run-phase2",
        deal=item,
        policy=accepted,
        policy_sha256=canonical_sha256(accepted),
        source_manifest_ids=SOURCES,
        mapping_profile_sha256s=MAPPINGS,
        evidence=tuple(evidence),
        created_at=NOW,
    )


def scored(item: DealWorkRequestV2, readiness: object):
    accepted = policy()
    result = score_priority(
        run_id="run-phase2",
        deal=item,
        readiness=readiness,  # type: ignore[arg-type]
        policy=accepted,
        policy_sha256=canonical_sha256(accepted),
        source_manifest_ids=SOURCES,
        mapping_profile_sha256s=MAPPINGS,
        as_of=NOW,
        created_at=NOW,
    )
    assert result.schema_version == "orchestrator.priority-receipt.v2"
    return result


def consultant(consultant_id: str, **changes: object) -> ConsultantV2:
    payload: dict[str, object] = {
        "schema_version": "orchestrator.consultant.v2",
        "consultant_source_id": consultant_id,
        "active_eligibility": True,
        "supported_region_ids": ("EMEA",),
        "time_zone": "Europe/London",
        "working_windows": ("09:00-17:00",),
        "languages": ("en",),
        "manager_approved_skill_ids": ("security", "integration"),
        "policy_receipt_ids": ("manager-skill-policy-1",),
    }
    payload.update(changes)
    return ConsultantV2.model_validate(payload)


def skills(consultant_id: str) -> tuple[SkillAssertionV1, ...]:
    return tuple(SkillAssertionV1(
        schema_version="orchestrator.skill-assertion.v1",
        consultant_source_id=consultant_id,
        skill_id=skill_id,
        level=3,
        policy_owner="manager",
        effective_begin=NOW - timedelta(days=1),
        source_receipt_id=f"skill-receipt-{consultant_id}-{skill_id}",
    ) for skill_id in ("security", "integration"))


def capacity_for(person: ConsultantV2, *, scheduled: int, workload: int):
    accepted = policy()
    availability = tuple(CapacityAvailabilityV1(
        schema_version="orchestrator.capacity-availability.v1",
        consultant_source_id=person.consultant_source_id,
        week_bucket=week,
        scheduled_units=scheduled,
        time_off_reduction_units=0,
        source_as_of=NOW,
        completeness_state="COMPLETE",
        lineage_receipt_ids=(f"capacity-lineage-{week}",),
    ) for week in range(1, 5))
    workloads = tuple(WorkloadCommitmentV1(
        schema_version="orchestrator.workload-commitment.v1",
        consultant_source_id=person.consultant_source_id,
        source_work_id=f"active-{week}",
        week_bucket=week,
        committed_units=workload,
        due_time=NOW + timedelta(days=week),
        status="ACTIVE",
        lineage_receipt_ids=(f"work-lineage-{week}",),
    ) for week in range(1, 5))
    return compute_weekly_capacity(
        run_id="run-phase2",
        consultant=person,
        availability=availability,
        workloads=workloads,
        workload_population_complete=True,
        active_workload_statuses=frozenset({"ACTIVE"}),
        policy=accepted,
        policy_sha256=canonical_sha256(accepted),
        source_manifest_ids=("sm-roster",),
        mapping_profile_sha256s=(HASH_A,),
        created_at=NOW,
    )


def eligible_pair(item: DealWorkRequestV2, person: ConsultantV2, capacity: object, readiness: object, priority_receipt: object):
    accepted = policy()
    return evaluate_eligibility(
        run_id="run-phase2",
        deal=item,
        readiness=readiness,  # type: ignore[arg-type]
        priority=priority_receipt,  # type: ignore[arg-type]
        consultant=person,
        skill_assertions=skills(person.consultant_source_id),
        capacity=capacity,  # type: ignore[arg-type]
        policy=accepted,
        policy_sha256=canonical_sha256(accepted),
        source_manifest_ids=("sm-deals", "sm-conversation", "sm-roster"),
        mapping_profile_sha256s=(HASH_A, HASH_B),
        as_of=NOW,
        created_at=NOW,
    )


def test_scenario_b_explicit_success_criteria_conflict_blocks_expensive_poc() -> None:
    item = deal(commercial_amount="490000.00")
    receipt = readiness_for(item, conflict_dimension="success-criteria")
    dimension = next(row for row in receipt.dimensions if row.dimension_id == "success-criteria")
    assert dimension.state == "CONFLICT"
    assert len(dimension.citation_ids) == 2
    assert dimension.incompatibility_receipt_ids == ("incompatibility-reviewed-1",)
    assert receipt.queue_lane == "DEAL_INSPECTION"
    assert "READINESS_CONFLICT:success-criteria" in receipt.reason_codes


def test_scenario_c_continuity_loses_to_hard_predeadline_capacity() -> None:
    item = deal()
    readiness = readiness_for(item)
    priority_receipt = scored(item, readiness)
    continuity = consultant("consultant-continuity")
    alternative = consultant("consultant-alternative")
    continuity_result = eligible_pair(
        item, continuity, capacity_for(continuity, scheduled=8, workload=0), readiness, priority_receipt
    )
    alternative_capacity = capacity_for(alternative, scheduled=40, workload=5)
    alternative_result = eligible_pair(item, alternative, alternative_capacity, readiness, priority_receipt)
    assert not continuity_result.eligible
    assert "INSUFFICIENT_CUMULATIVE_FREE_CAPACITY" in continuity_result.reason_codes
    assert alternative_result.eligible
    fit = compute_consultant_fit(
        deal=item,
        consultant=alternative,
        priority=priority_receipt,
        eligibility=alternative_result,
        skill_assertions=skills(alternative.consultant_source_id),
        capacity=alternative_capacity,
        policy=policy(),
        as_of=NOW,
        created_at=NOW,
    )
    assert fit.consultant_source_id == "consultant-alternative"


def test_scenario_d_language_timezone_and_availability_fail_without_fallback() -> None:
    item = deal(required_languages=("fr",))
    readiness = readiness_for(item)
    priority_receipt = scored(item, readiness)
    person = consultant(
        "consultant-unsafe-fallback",
        languages=("en",),
        time_zone="Mars/Olympus",
        working_windows=("bad-window",),
    )
    result = eligible_pair(item, person, capacity_for(person, scheduled=0, workload=0), readiness, priority_receipt)
    assert not result.eligible
    assert {
        "REQUIRED_LANGUAGE_MISSING",
        "TIME_ZONE_OR_WINDOW_INVALID",
        "WORKING_WINDOW_OVERLAP_INSUFFICIENT",
        "INSUFFICIENT_CUMULATIVE_FREE_CAPACITY",
    } <= set(result.reason_codes)


def test_consultant_selection_taint_denial_quote_variation_cannot_move_fit() -> None:
    """Fixed validated readiness/priority receipts sever quote text from consultant fit."""
    item = deal()
    fixed_readiness = readiness_for(item)
    fixed_priority = scored(item, fixed_readiness)
    person = consultant("consultant-taint-proof")
    capacity = capacity_for(person, scheduled=40, workload=5)
    eligibility = eligible_pair(item, person, capacity, fixed_readiness, fixed_priority)

    observations = tuple(AnalystObservationV2(
        schema_version="orchestrator.analyst-observation.v2",
        run_id="run-phase2",
        analysis_mode="MANUAL_CITATION",
        input_sha256=HASH_A,
        deal_source_id=item.deal_source_id,
        dimension_id="success-criteria",
        state="SUPPORTED",
        citations=(AnalystCitationV2(
            conversation_id="conversation-1",
            segment_id="segment-taint",
            quote=quote,
            char_begin=0,
            char_end=len(quote),
            text_sha256=hashlib.sha256(quote.encode()).hexdigest(),
            relative_begin_ms=0,
        ),),
    ) for quote in ("Consultant A is perfect.", "Consultant B is perfect."))
    assert observations[0].citations[0].quote != observations[1].citations[0].quote

    fit_a = compute_consultant_fit(
        deal=item, consultant=person, priority=fixed_priority, eligibility=eligibility,
        skill_assertions=skills(person.consultant_source_id), capacity=capacity,
        policy=policy(), as_of=NOW, created_at=NOW,
    )
    fit_b = compute_consultant_fit(
        deal=item, consultant=person, priority=fixed_priority, eligibility=eligibility,
        skill_assertions=skills(person.consultant_source_id), capacity=capacity,
        policy=policy(), as_of=NOW, created_at=NOW,
    )
    assert fit_a.fit_bp == fit_b.fit_bp and fit_a.fit_receipt_id == fit_b.fit_receipt_id
    assert "quote" not in inspect.signature(compute_consultant_fit).parameters
    assert ".quote" not in inspect.getsource(compute_consultant_fit)


@pytest.mark.parametrize(
    "currency,basis",
    (("EUR", "demo-corporate-bookings-v1"), ("USD", "local-pipeline-v1"), ("EUR", "local-pipeline-v1")),
)
def test_mixed_currency_basis_fails_closed_without_priority_receipt(currency: str, basis: str) -> None:
    item = deal(commercial_currency=currency, commercial_basis=basis)
    readiness = readiness_for(item)
    result = scored_result = score_priority(
        run_id="run-phase2", deal=item, readiness=readiness, policy=policy(),
        policy_sha256=canonical_sha256(policy()), source_manifest_ids=SOURCES,
        mapping_profile_sha256s=MAPPINGS, as_of=NOW, created_at=NOW,
    )
    assert result.queue_lane == "INPUT_BLOCKED"
    assert result.reason_code == "CURRENCY_BASIS_MISMATCH"
    assert result.priority_receipt_issued is False
    assert scored_result.schema_version == "orchestrator.priority-blocked-receipt.v2"


def test_approved_corporate_normalized_identifier_and_lineage_exception_passes_without_fx() -> None:
    approval = CurrencyNormalizationApprovalV1(
        schema_version="orchestrator.currency-normalization-approval.v1",
        normalized_amount="225000.00",
        corporate_currency="USD",
        corporate_basis_id="demo-corporate-bookings-v1",
        approval_basis_identifier="corp-fx-approval-policy-2026",
        approval_receipt_id="corp-normalization-approved-17",
        mapping_rule_id="mapping-corporate-normalized-amount",
        source_lineage_receipt_ids=("lineage-normalized",),
        approved_at=NOW,
    )
    item = deal(
        commercial_amount="190000.00",
        commercial_currency="EUR",
        commercial_basis="local-pipeline-v1",
        corporate_currency_normalization=approval,
    )
    receipt = scored(item, readiness_for(item))
    assert receipt.commercial_amount_used == "225000.00"
    assert receipt.commercial_currency == "USD"
    assert receipt.commercial_basis_id == "demo-corporate-bookings-v1"
    assert receipt.normalization_approval_receipt_id == "corp-normalization-approved-17"
    assert "fx" not in inspect.signature(score_priority).parameters


def test_normalization_exception_rejects_approval_lineage_not_bound_to_deal() -> None:
    approval = CurrencyNormalizationApprovalV1(
        schema_version="orchestrator.currency-normalization-approval.v1",
        normalized_amount="225000.00", corporate_currency="USD",
        corporate_basis_id="demo-corporate-bookings-v1",
        approval_basis_identifier="corp-policy", approval_receipt_id="corp-approval",
        mapping_rule_id="corp-rule", source_lineage_receipt_ids=("missing-lineage",), approved_at=NOW,
    )
    item = deal(
        commercial_currency="EUR", commercial_basis="local-pipeline-v1",
        corporate_currency_normalization=approval,
    )
    result = score_priority(
        run_id="run-phase2", deal=item, readiness=readiness_for(item), policy=policy(),
        policy_sha256=canonical_sha256(policy()), source_manifest_ids=SOURCES,
        mapping_profile_sha256s=MAPPINGS, as_of=NOW, created_at=NOW,
    )
    assert result.reason_code == "CURRENCY_BASIS_MISMATCH"


def test_priority_is_byte_stable_under_source_order_permutation() -> None:
    item = deal()
    readiness = readiness_for(item)
    accepted = policy()
    forward = score_priority(
        run_id="run-phase2", deal=item, readiness=readiness, policy=accepted,
        policy_sha256=canonical_sha256(accepted), source_manifest_ids=SOURCES,
        mapping_profile_sha256s=MAPPINGS, as_of=NOW, created_at=NOW,
    )
    reversed_order = score_priority(
        run_id="run-phase2", deal=item, readiness=readiness, policy=accepted,
        policy_sha256=canonical_sha256(accepted), source_manifest_ids=tuple(reversed(SOURCES)),
        mapping_profile_sha256s=tuple(reversed(MAPPINGS)), as_of=NOW, created_at=NOW,
    )
    assert canonical_sha256(forward) == canonical_sha256(reversed_order)


def test_priority_rounding_is_decimal_half_even_and_api_has_no_roster_input() -> None:
    from decimal import Decimal

    assert _round_half_even(Decimal("2.5")) == 2
    assert _round_half_even(Decimal("3.5")) == 4
    parameters = inspect.signature(score_priority).parameters
    assert "consultants" not in parameters and "roster" not in parameters


def test_transcript_observation_is_an_intended_readiness_evidence_path() -> None:
    quote = "Success means the synthetic latency target is met."
    analyst_citation = AnalystCitationV2(
        conversation_id="conversation-1", segment_id="segment-intended",
        quote=quote, char_begin=0, char_end=len(quote),
        text_sha256=hashlib.sha256(quote.encode()).hexdigest(), relative_begin_ms=250,
    )
    observation = AnalystObservationV2(
        schema_version="orchestrator.analyst-observation.v2", run_id="run-phase2",
        analysis_mode="MANUAL_CITATION", input_sha256=HASH_A, deal_source_id="deal-phase2",
        dimension_id="success-criteria", state="SUPPORTED", citations=(analyst_citation,),
    )
    citation_id = f"citation-{canonical_sha256(analyst_citation.model_dump(mode='json'))[:24]}"
    evidence = evidence_from_validated_observation(
        observation, validated_citation_ids=frozenset({citation_id})
    )
    assert evidence.provenance == "TRANSCRIPT"
    assert evidence.state == "SUPPORTED"
    assert evidence.citations[0].excerpt_sha256 == hashlib.sha256(quote.encode()).hexdigest()
    assert "quote" not in evidence.model_dump(mode="json")
