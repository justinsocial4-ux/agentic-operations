from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .canonical import canonical_sha256
from .contracts.domain import WeeklyCapacityBucketV1, WeeklyCapacityReceiptV1
from .contracts.phase3 import CapacityCellV2, CapacityDemandV1
from .contracts.policy import PolicyV2
from .contracts.records import CapacityAvailabilityV1, ConsultantV2, WorkloadCommitmentV1


def compute_weekly_capacity(
    *,
    run_id: str,
    consultant: ConsultantV2,
    availability: tuple[CapacityAvailabilityV1, ...],
    workloads: tuple[WorkloadCommitmentV1, ...],
    workload_population_complete: bool,
    active_workload_statuses: frozenset[str],
    policy: PolicyV2,
    policy_sha256: str,
    source_manifest_ids: tuple[str, ...],
    mapping_profile_sha256s: tuple[str, ...],
    created_at: datetime,
) -> WeeklyCapacityReceiptV1:
    """Reconcile 30-minute capacity in the four literal weekly buckets."""
    source_manifest_ids = tuple(sorted(set(source_manifest_ids)))
    mapping_profile_sha256s = tuple(sorted(set(mapping_profile_sha256s)))
    if policy.horizon_weeks != 4 or policy.capacity_unit_minutes != 30:
        raise ValueError("v1 capacity requires four buckets of 30-minute units")
    if not active_workload_statuses:
        raise ValueError("active workload statuses must be explicitly supplied")
    if any(item.consultant_source_id != consultant.consultant_source_id for item in availability):
        raise ValueError("capacity row belongs to a different consultant")
    if any(item.consultant_source_id != consultant.consultant_source_id for item in workloads):
        raise ValueError("workload row belongs to a different consultant")

    availability_by_bucket: dict[int, CapacityAvailabilityV1] = {}
    for item in availability:
        if item.week_bucket in availability_by_bucket:
            raise ValueError("duplicate consultant capacity bucket")
        availability_by_bucket[item.week_bucket] = item

    seen_work_ids: set[str] = set()
    active_by_bucket: dict[int, int] = defaultdict(int)
    workload_conflict_buckets: set[int] = set()
    for item in workloads:
        identity = f"{item.source_work_id}:{item.week_bucket}"
        if identity in seen_work_ids:
            workload_conflict_buckets.add(item.week_bucket)
            continue
        seen_work_ids.add(identity)
        if item.status in active_workload_statuses:
            active_by_bucket[item.week_bucket] += item.committed_units

    buckets: list[WeeklyCapacityBucketV1] = []
    for week in range(1, 5):
        row = availability_by_bucket.get(week)
        if row is None:
            buckets.append(WeeklyCapacityBucketV1(
                week_bucket=week,
                scheduled_units=0,
                time_off_units=0,
                active_workload_units=active_by_bucket[week],
                free_units=None,
                completeness_state="INCOMPLETE",
            ))
            continue
        scheduled = row.scheduled_units
        time_off = row.time_off_reduction_units
        workload = active_by_bucket[week]
        free = scheduled - time_off - workload
        if row.completeness_state == "CONFLICT" or week in workload_conflict_buckets or free < 0:
            state = "CONFLICT"
            complete_free = None
        elif row.completeness_state != "COMPLETE" or not workload_population_complete:
            state = "INCOMPLETE"
            complete_free = None
        else:
            state = "COMPLETE"
            complete_free = free
        buckets.append(WeeklyCapacityBucketV1(
            week_bucket=week,
            scheduled_units=scheduled,
            time_off_units=time_off,
            active_workload_units=workload,
            free_units=complete_free,
            completeness_state=state,
        ))

    complete_through = 0
    for item in buckets:
        if item.completeness_state != "COMPLETE":
            break
        complete_through = item.week_bucket
    identity_payload = {
        "run_id": run_id,
        "consultant": consultant.consultant_source_id,
        "buckets": buckets,
        "policy_sha256": policy_sha256,
        "sources": source_manifest_ids,
        "mappings": mapping_profile_sha256s,
    }
    return WeeklyCapacityReceiptV1(
        schema_version="orchestrator.weekly-capacity-receipt.v1",
        capacity_receipt_id=f"capacity-{canonical_sha256(identity_payload)[:32]}",
        run_id=run_id,
        policy_sha256=policy_sha256,
        source_manifest_ids=source_manifest_ids,
        mapping_profile_sha256s=mapping_profile_sha256s,
        consultant_source_id=consultant.consultant_source_id,
        capacity_unit_minutes=30,
        horizon_weeks=4,
        buckets=tuple(buckets),
        complete_through_bucket=complete_through,
        created_at=created_at,
    )


def compute_capacity_heatmap(
    *,
    run_id: str,
    demands: tuple[CapacityDemandV1, ...],
    consultants: tuple[ConsultantV2, ...],
    capacities: tuple[WeeklyCapacityReceiptV1, ...],
    policy: PolicyV2,
    policy_sha256: str,
    source_manifest_ids: tuple[str, ...],
    mapping_profile_sha256s: tuple[str, ...],
) -> tuple[CapacityCellV2, ...]:
    """Build non-additive region/skill/week cells without assignment inputs."""
    if canonical_sha256(policy) != policy_sha256:
        raise ValueError("capacity view policy does not match the accepted policy")
    if policy.horizon_weeks != 4 or policy.capacity_unit_minutes != 30:
        raise ValueError("v1 heatmap requires four 30-minute buckets")
    source_manifest_ids = tuple(sorted(set(source_manifest_ids)))
    mapping_profile_sha256s = tuple(sorted(set(mapping_profile_sha256s)))
    if len({item.deal_source_id for item in demands}) != len(demands):
        raise ValueError("capacity demand deals must be unique")
    if len({item.consultant_source_id for item in consultants}) != len(consultants):
        raise ValueError("capacity consultants must be unique")
    capacity_by_consultant = {item.consultant_source_id: item for item in capacities}
    if len(capacity_by_consultant) != len(capacities):
        raise ValueError("capacity receipts must be unique per consultant")
    for capacity in capacities:
        if capacity.run_id != run_id or capacity.policy_sha256 != policy_sha256:
            raise ValueError("capacity receipt is outside the frozen heatmap run")

    groups: set[tuple[str, str]] = set()
    for demand in demands:
        groups.update((demand.region_id, skill_id) for skill_id in demand.required_skill_ids)
    for consultant in consultants:
        if consultant.active_eligibility:
            groups.update(
                (region_id, skill_id)
                for region_id in consultant.supported_region_ids
                for skill_id in consultant.manager_approved_skill_ids
            )

    cells: list[CapacityCellV2] = []
    for region_id, skill_id in sorted(groups):
        matching = tuple(sorted(
            (
                consultant for consultant in consultants
                if consultant.active_eligibility
                and region_id in consultant.supported_region_ids
                and skill_id in consultant.manager_approved_skill_ids
            ),
            key=lambda item: item.consultant_source_id,
        ))
        complete = tuple(
            consultant for consultant in matching
            if consultant.consultant_source_id in capacity_by_consultant
            and capacity_by_consultant[consultant.consultant_source_id].complete_through_bucket == 4
        )
        complete_ids = {item.consultant_source_id for item in complete}
        excluded = tuple(
            item.consultant_source_id for item in matching
            if item.consultant_source_id not in complete_ids
        )
        for week in range(1, 5):
            demand_units = sum(
                item.effort_units for item in demands
                if item.region_id == region_id
                and skill_id in item.required_skill_ids
                and item.due_week_bucket == week
            )
            buckets = tuple(
                capacity_by_consultant[item.consultant_source_id].buckets[week - 1]
                for item in complete
            )
            supply = sum(item.scheduled_units - item.time_off_units for item in buckets)
            workload = sum(item.active_workload_units for item in buckets)
            free = sum(item.free_units or 0 for item in buckets)
            utilization = (
                None if supply == 0
                else ((workload + demand_units) * 10_000 + supply - 1) // supply
            )
            identity = {
                "run_id": run_id,
                "region_id": region_id,
                "skill_id": skill_id,
                "week": week,
                "demand": demand_units,
                "supply": supply,
                "workload": workload,
                "free": free,
                "excluded": excluded,
                "policy_sha256": policy_sha256,
            }
            cells.append(CapacityCellV2(
                schema_version="orchestrator.capacity-cell.v2",
                capacity_cell_id=f"capacity-cell-{canonical_sha256(identity)[:32]}",
                run_id=run_id,
                policy_sha256=policy_sha256,
                source_manifest_ids=source_manifest_ids,
                mapping_profile_sha256s=mapping_profile_sha256s,
                region_id=region_id,
                skill_id=skill_id,
                week_bucket=week,
                demand_units=demand_units,
                eligible_supply_units=supply,
                committed_workload_units=workload,
                free_units=free,
                projected_utilization_bp=utilization,
                surplus_deficit_units=free - demand_units,
                excluded_incomplete_consultant_ids=excluded,
                supply_state="PARTIAL_SUPPLY_EXCLUDED" if excluded else "COMPLETE",
                skill_rows_additive=False,
            ))
    return tuple(cells)
