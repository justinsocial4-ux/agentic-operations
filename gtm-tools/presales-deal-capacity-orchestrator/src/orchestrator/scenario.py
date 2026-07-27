from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_CEILING

from .canonical import canonical_sha256
from .capacity import compute_capacity_heatmap
from .contracts.domain import WeeklyCapacityReceiptV1
from .contracts.enums import LaneV1
from .contracts.phase3 import (
    CapacityDemandV1,
    ScenarioComparisonV2,
    ScenarioEffortChangeV2,
)
from .contracts.policy import PolicyV2
from .contracts.records import ConsultantV2
from .contracts.setup import RunSetupAcceptanceV1
from .setup_gate import validate_current_setup


def apply_emea_effort_assumption(
    demands: tuple[CapacityDemandV1, ...],
    *,
    policy: PolicyV2,
) -> tuple[CapacityDemandV1, ...]:
    """Change only EMEA effort, multiplying by 1.25 and ceiling to one unit."""
    boundaries = policy.scenario_boundaries
    if (
        boundaries.region_id != "EMEA"
        or boundaries.effort_multiplier != "1.25"
        or boundaries.rounding != "CEILING_TO_CAPACITY_UNIT"
    ):
        raise ValueError("only the bounded EMEA +25% scenario exists in v1")
    multiplier = Decimal(boundaries.effort_multiplier)
    return tuple(
        item.model_copy(update={
            "effort_units": int(
                (Decimal(item.effort_units) * multiplier).quantize(
                    Decimal("1"), rounding=ROUND_CEILING
                )
            )
        }) if item.region_id == "EMEA" else item
        for item in demands
    )


def run_emea_capacity_scenario(
    *,
    run_id: str,
    demands: tuple[CapacityDemandV1, ...],
    consultants: tuple[ConsultantV2, ...],
    capacities: tuple[WeeklyCapacityReceiptV1, ...],
    policy: PolicyV2,
    policy_sha256: str,
    source_manifest_ids: tuple[str, ...],
    mapping_profile_sha256s: tuple[str, ...],
    setup_acceptance: RunSetupAcceptanceV1,
    created_at: datetime,
) -> ScenarioComparisonV2:
    """Rerun deterministic capacity under a confirmed user-selected assumption."""
    if not isinstance(setup_acceptance, RunSetupAcceptanceV1):
        raise ValueError("Capacity/heatmap Advanced confirmation is required")
    if setup_acceptance.run_id != run_id or setup_acceptance.lane is not LaneV1.CAPACITY_HEATMAP:
        raise ValueError("Capacity/heatmap Advanced confirmation is required")
    validate_current_setup(
        setup_acceptance, policy=policy, source_slots=setup_acceptance.source_slots
    )
    advanced_policy_confirmation_id = f"setup-{canonical_sha256(setup_acceptance)[:32]}"
    base_cells = compute_capacity_heatmap(
        run_id=run_id,
        demands=demands,
        consultants=consultants,
        capacities=capacities,
        policy=policy,
        policy_sha256=policy_sha256,
        source_manifest_ids=source_manifest_ids,
        mapping_profile_sha256s=mapping_profile_sha256s,
    )
    scenario_demands = apply_emea_effort_assumption(demands, policy=policy)
    scenario_cells = compute_capacity_heatmap(
        run_id=run_id,
        demands=scenario_demands,
        consultants=consultants,
        capacities=capacities,
        policy=policy,
        policy_sha256=policy_sha256,
        source_manifest_ids=source_manifest_ids,
        mapping_profile_sha256s=mapping_profile_sha256s,
    )
    changes = tuple(
        ScenarioEffortChangeV2(
            deal_source_id=before.deal_source_id,
            region_id="EMEA",
            base_effort_units=before.effort_units,
            scenario_effort_units=after.effort_units,
            changed_field="effort_units",
            multiplier="1.25",
            rounding="CEILING_TO_CAPACITY_UNIT",
        )
        for before, after in zip(demands, scenario_demands)
        if before.region_id == "EMEA"
    )
    source_manifest_ids = tuple(sorted(set(source_manifest_ids)))
    mapping_profile_sha256s = tuple(sorted(set(mapping_profile_sha256s)))
    identity = {
        "run_id": run_id,
        "base_cells": base_cells,
        "scenario_cells": scenario_cells,
        "changes": changes,
        "advanced_policy_confirmation_id": advanced_policy_confirmation_id,
    }
    return ScenarioComparisonV2(
        schema_version="orchestrator.scenario-comparison.v2",
        scenario_comparison_id=f"scenario-{canonical_sha256(identity)[:32]}",
        run_id=run_id,
        policy_sha256=policy_sha256,
        source_manifest_ids=source_manifest_ids,
        mapping_profile_sha256s=mapping_profile_sha256s,
        scenario_id="EMEA_EFFORT_PLUS_25_PERCENT",
        label="USER_SELECTED_ASSUMPTION_NOT_A_FORECAST",
        advanced_policy_confirmation_id=advanced_policy_confirmation_id,
        changes=changes,
        base_cells=base_cells,
        scenario_cells=scenario_cells,
        created_at=created_at,
    )
