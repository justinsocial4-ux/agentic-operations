from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .canonical import canonical_sha256
from .contracts.domain import (
    ConsultantFitReceiptV2,
    EligibilityCheckV2,
    EligibilityReceiptV2,
    MatchComponentV2,
    PriorityReceiptV2,
    ReadinessReceiptV2,
    WeeklyCapacityReceiptV1,
)
from .contracts.enums import LaneV1
from .contracts.policy import PolicyV2
from .contracts.records import ConsultantV2, DealWorkRequestV2, SkillAssertionV1


def _round_half_even(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def _window_minutes(value: str) -> int:
    try:
        start, end = value.split("-", 1)
        start_hour, start_minute = (int(part) for part in start.split(":"))
        end_hour, end_minute = (int(part) for part in end.split(":"))
    except (ValueError, TypeError) as exc:
        raise ValueError("working windows must use HH:MM-HH:MM") from exc
    if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23 and 0 <= start_minute <= 59 and 0 <= end_minute <= 59):
        raise ValueError("working window time is invalid")
    begin = start_hour * 60 + start_minute
    finish = end_hour * 60 + end_minute
    return (finish - begin) % 1440 or 1440


def _working_window(consultant: ConsultantV2) -> tuple[bool, int]:
    if consultant.time_zone is None or consultant.working_windows is None:
        return False, 0
    try:
        ZoneInfo(consultant.time_zone)
        durations = tuple(_window_minutes(value) for value in consultant.working_windows)
    except (ZoneInfoNotFoundError, ValueError):
        return False, 0
    return bool(durations), max(durations, default=0)


def _current_skill_levels(
    consultant_id: str,
    assertions: tuple[SkillAssertionV1, ...],
    as_of: datetime,
) -> tuple[dict[str, int], set[str]]:
    levels: dict[str, set[int]] = defaultdict(set)
    for assertion in assertions:
        if assertion.consultant_source_id != consultant_id:
            raise ValueError("skill assertion belongs to a different consultant")
        if assertion.effective_begin <= as_of and (assertion.effective_end is None or as_of < assertion.effective_end):
            levels[assertion.skill_id].add(assertion.level)
    conflicts = {skill_id for skill_id, values in levels.items() if len(values) > 1}
    return ({skill_id: next(iter(values)) for skill_id, values in levels.items() if len(values) == 1}, conflicts)


def evaluate_eligibility(
    *,
    run_id: str,
    deal: DealWorkRequestV2,
    readiness: ReadinessReceiptV2,
    priority: PriorityReceiptV2,
    consultant: ConsultantV2,
    skill_assertions: tuple[SkillAssertionV1, ...],
    capacity: WeeklyCapacityReceiptV1,
    policy: PolicyV2,
    policy_sha256: str,
    source_manifest_ids: tuple[str, ...],
    mapping_profile_sha256s: tuple[str, ...],
    as_of: datetime,
    created_at: datetime,
) -> EligibilityReceiptV2:
    """Evaluate hard constraints using structured, manager-approved inputs only."""
    deal.validate_for_lane(LaneV1.ASSIGNMENT_RECOMMENDATION)
    consultant.validate_for_lane(LaneV1.ASSIGNMENT_RECOMMENDATION)
    source_manifest_ids = tuple(sorted(set(source_manifest_ids)))
    mapping_profile_sha256s = tuple(sorted(set(mapping_profile_sha256s)))
    if (
        priority.run_id != run_id
        or readiness.run_id != run_id
        or capacity.run_id != run_id
        or priority.policy_sha256 != policy_sha256
        or readiness.policy_sha256 != policy_sha256
        or capacity.policy_sha256 != policy_sha256
        or priority.deal_source_id != deal.deal_source_id
        or readiness.deal_source_id != deal.deal_source_id
        or priority.readiness_receipt_id != readiness.readiness_receipt_id
        or capacity.consultant_source_id != consultant.consultant_source_id
        or not set(priority.source_manifest_ids).issubset(source_manifest_ids)
        or not set(readiness.source_manifest_ids).issubset(source_manifest_ids)
        or not set(capacity.source_manifest_ids).issubset(source_manifest_ids)
        or not set(priority.mapping_profile_sha256s).issubset(mapping_profile_sha256s)
        or not set(readiness.mapping_profile_sha256s).issubset(mapping_profile_sha256s)
        or not set(capacity.mapping_profile_sha256s).issubset(mapping_profile_sha256s)
    ):
        raise ValueError("eligibility inputs do not match the frozen run receipts")

    checks: list[EligibilityCheckV2] = []

    def add(check_id: str, passed: bool, reason: str) -> None:
        checks.append(EligibilityCheckV2(
            check_id=check_id,
            passed=passed,
            reason_code=None if passed else reason,
        ))

    add("DEAL_LANE", readiness.queue_lane == "ASSIGNMENT_ELIGIBLE", "DEAL_NOT_ASSIGNMENT_ELIGIBLE")
    add("ACTIVE_STATUS", consultant.active_eligibility, "CONSULTANT_NOT_EXPLICITLY_ACTIVE")
    assert deal.region_id is not None
    add("REGION", deal.region_id in consultant.supported_region_ids, "REGION_NOT_SUPPORTED")

    levels, skill_conflicts = _current_skill_levels(consultant.consultant_source_id, skill_assertions, as_of)
    catalog = {item.skill_id: item.minimum_level for item in policy.skill_catalog}
    assert deal.required_skill_ids is not None
    skills_pass = all(
        skill_id in catalog
        and skill_id in consultant.manager_approved_skill_ids
        and skill_id not in skill_conflicts
        and levels.get(skill_id, -1) >= catalog[skill_id]
        for skill_id in deal.required_skill_ids
    )
    add("SKILLS", skills_pass, "REQUIRED_MANAGER_APPROVED_SKILL_MISSING")

    assert deal.required_languages is not None and consultant.languages is not None
    add("LANGUAGE", set(deal.required_languages).issubset(consultant.languages), "REQUIRED_LANGUAGE_MISSING")

    timezone_and_window_valid, actual_overlap = _working_window(consultant)
    add("TIME_ZONE", timezone_and_window_valid, "TIME_ZONE_OR_WINDOW_INVALID")
    assert deal.required_working_window_overlap_minutes is not None
    required_overlap = max(deal.required_working_window_overlap_minutes, policy.minimum_working_window_overlap)
    add("WORKING_WINDOW", timezone_and_window_valid and actual_overlap >= required_overlap, "WORKING_WINDOW_OVERLAP_INSUFFICIENT")

    due_bucket = priority.due_week_bucket
    complete = capacity.complete_through_bucket >= due_bucket
    add("CAPACITY_COMPLETE", complete, "CAPACITY_OR_WORKLOAD_INCOMPLETE_THROUGH_MILESTONE")
    relevant = capacity.buckets[:due_bucket]
    cumulative_free = sum(item.free_units or 0 for item in relevant) if complete else 0
    assert deal.effort_units is not None
    add("CUMULATIVE_CAPACITY", complete and cumulative_free >= deal.effort_units, "INSUFFICIENT_CUMULATIVE_FREE_CAPACITY")

    projected_utilization: int | None = None
    denominator = sum(item.scheduled_units - item.time_off_units for item in relevant) if complete else 0
    numerator = sum(item.active_workload_units for item in relevant) + deal.effort_units
    if denominator > 0:
        projected_utilization = _round_half_even(Decimal(numerator) * Decimal(10_000) / Decimal(denominator))
    utilization_pass = projected_utilization is not None and projected_utilization <= policy.utilization_ceiling
    add("UTILIZATION", utilization_pass, "PROJECTED_UTILIZATION_EXCEEDS_POLICY")
    add("FROZEN_RECEIPTS", True, "FROZEN_RECEIPT_MISMATCH")

    reasons = tuple(item.reason_code for item in checks if not item.passed and item.reason_code is not None)
    identity_payload = {
        "run_id": run_id,
        "deal": deal.deal_source_id,
        "consultant": consultant.consultant_source_id,
        "priority": priority.priority_receipt_id,
        "capacity": capacity.capacity_receipt_id,
        "checks": checks,
        "policy_sha256": policy_sha256,
    }
    return EligibilityReceiptV2(
        schema_version="orchestrator.eligibility-receipt.v2",
        eligibility_receipt_id=f"eligibility-{canonical_sha256(identity_payload)[:32]}",
        run_id=run_id,
        policy_sha256=policy_sha256,
        source_manifest_ids=source_manifest_ids,
        mapping_profile_sha256s=mapping_profile_sha256s,
        deal_source_id=deal.deal_source_id,
        consultant_source_id=consultant.consultant_source_id,
        priority_receipt_id=priority.priority_receipt_id,
        capacity_receipt_id=capacity.capacity_receipt_id,
        due_week_bucket=due_bucket,
        checks=tuple(checks),
        eligible=not reasons,
        reason_codes=reasons,
        actual_working_window_minutes=actual_overlap,
        projected_utilization_bp=projected_utilization,
        created_at=created_at,
    )


def compute_consultant_fit(
    *,
    deal: DealWorkRequestV2,
    consultant: ConsultantV2,
    priority: PriorityReceiptV2,
    eligibility: EligibilityReceiptV2,
    skill_assertions: tuple[SkillAssertionV1, ...],
    capacity: WeeklyCapacityReceiptV1,
    policy: PolicyV2,
    as_of: datetime,
    created_at: datetime,
) -> ConsultantFitReceiptV2:
    """Compute fit from receipt/roster data; this API has no evidence-text input."""
    if not eligibility.eligible:
        raise ValueError("consultant fit is defined only for an eligible pair")
    if (
        eligibility.priority_receipt_id != priority.priority_receipt_id
        or eligibility.capacity_receipt_id != capacity.capacity_receipt_id
        or eligibility.deal_source_id != deal.deal_source_id
        or eligibility.consultant_source_id != consultant.consultant_source_id
    ):
        raise ValueError("fit inputs do not match eligibility receipt")
    levels, conflicts = _current_skill_levels(consultant.consultant_source_id, skill_assertions, as_of)
    if conflicts:
        raise ValueError("conflicting manager-approved skill assertions cannot produce fit")
    minima = {item.skill_id: item.minimum_level for item in policy.skill_catalog}
    assert deal.required_skill_ids is not None
    skill_values = []
    for skill_id in deal.required_skill_ids:
        minimum = minima[skill_id]
        denominator = max(1, 4 - minimum)
        skill_values.append(max(0, levels[skill_id] - minimum) * 10_000 // denominator)
    skill_bp = _round_half_even(Decimal(sum(skill_values)) / Decimal(len(skill_values))) if skill_values else 10_000
    continuity_bp = 10_000 if deal.continuity_consultant_id == consultant.consultant_source_id else 0
    assert deal.required_working_window_overlap_minutes is not None
    overlap_floor = max(deal.required_working_window_overlap_minutes, policy.minimum_working_window_overlap)
    overlap_denominator = max(1, 1440 - overlap_floor)
    overlap_bp = min(10_000, max(0, eligibility.actual_working_window_minutes - overlap_floor) * 10_000 // overlap_denominator)

    relevant = capacity.buckets[:eligibility.due_week_bucket]
    cumulative_net = sum(item.scheduled_units - item.time_off_units for item in relevant)
    cumulative_free_after = sum(item.free_units or 0 for item in relevant) - (deal.effort_units or 0)
    headroom_bp = 0 if cumulative_net <= 0 else min(10_000, max(0, cumulative_free_after) * 10_000 // cumulative_net)

    weights = policy.match_component_weights_bp
    values = (
        ("SKILL_SURPLUS", skill_bp, weights.skill_surplus),
        ("CONTINUITY", continuity_bp, weights.continuity),
        ("OVERLAP_SURPLUS", overlap_bp, weights.overlap_surplus),
        ("CAPACITY_HEADROOM", headroom_bp, weights.capacity_headroom),
    )
    components = tuple(MatchComponentV2(
        component_id=component_id,
        component_bp=component_bp,
        weight_bp=weight_bp,
        weighted_numerator=component_bp * weight_bp,
    ) for component_id, component_bp, weight_bp in values)
    fit_bp = _round_half_even(Decimal(sum(item.weighted_numerator for item in components)) / Decimal(10_000))
    identity_payload = {
        "eligibility": eligibility.eligibility_receipt_id,
        "priority": priority.priority_receipt_id,
        "components": components,
        "fit_bp": fit_bp,
    }
    return ConsultantFitReceiptV2(
        schema_version="orchestrator.consultant-fit-receipt.v2",
        fit_receipt_id=f"fit-{canonical_sha256(identity_payload)[:32]}",
        run_id=eligibility.run_id,
        policy_sha256=eligibility.policy_sha256,
        source_manifest_ids=eligibility.source_manifest_ids,
        mapping_profile_sha256s=eligibility.mapping_profile_sha256s,
        deal_source_id=deal.deal_source_id,
        consultant_source_id=consultant.consultant_source_id,
        eligibility_receipt_id=eligibility.eligibility_receipt_id,
        priority_receipt_id=priority.priority_receipt_id,
        components=components,
        fit_bp=fit_bp,
        rounding="ROUND_HALF_EVEN",
        created_at=created_at,
    )
