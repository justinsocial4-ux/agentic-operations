from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from orchestrator.canonical import canonical_json_bytes, canonical_sha256
from orchestrator.capacity import compute_capacity_heatmap
from orchestrator.contracts.domain import WeeklyCapacityBucketV1, WeeklyCapacityReceiptV1
from orchestrator.contracts.phase3 import (
    CapacityDemandV1,
    SolverPhaseReceiptV1,
    SolverReceiptV1,
)
from orchestrator.contracts.enums import LaneV1, SourceModeV1
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.records import ConsultantV2
from orchestrator.contracts.setup import SourceSlotSelectionV1
from orchestrator.digest import build_leadership_digest
from orchestrator.scenario import apply_emea_effort_assumption, run_emea_capacity_scenario
from orchestrator.setup_gate import build_run_setup_acceptance
from orchestrator.store import Phase1Store, apply_migrations, connect_database

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 3, 9, tzinfo=timezone.utc)
HASH = "a" * 64


def policy() -> PolicyV2:
    return PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())


def consultant() -> ConsultantV2:
    return ConsultantV2(
        schema_version="orchestrator.consultant.v2",
        consultant_source_id="consultant-emea-security",
        active_eligibility=True,
        supported_region_ids=("EMEA",),
        manager_approved_skill_ids=("security",),
        policy_receipt_ids=("manager-approved-skill-policy",),
    )


def capacity() -> WeeklyCapacityReceiptV1:
    return WeeklyCapacityReceiptV1(
        schema_version="orchestrator.weekly-capacity-receipt.v1",
        capacity_receipt_id="capacity-emea-security",
        run_id="run-scenario-e",
        policy_sha256=canonical_sha256(policy()),
        source_manifest_ids=("sm-capacity",),
        mapping_profile_sha256s=(HASH,),
        consultant_source_id="consultant-emea-security",
        capacity_unit_minutes=30,
        horizon_weeks=4,
        buckets=tuple(WeeklyCapacityBucketV1(
            week_bucket=week,
            scheduled_units=56 if week == 1 else 0,
            time_off_units=0,
            active_workload_units=0,
            free_units=56 if week == 1 else 0,
            completeness_state="COMPLETE",
        ) for week in range(1, 5)),
        complete_through_bucket=4,
        created_at=NOW,
    )


def demand() -> CapacityDemandV1:
    return CapacityDemandV1(
        deal_source_id="deal-emea-security",
        region_id="EMEA",
        required_skill_ids=("security",),
        due_week_bucket=1,
        effort_units=48,
    )


def setup_acceptance():
    slots = tuple(SourceSlotSelectionV1(
        source_slot_id=f"slot-{role.lower()}",
        authority_role=role,
        adapter_id="fictional-adapter",
        source_mode=SourceModeV1.FICTIONAL,
    ) for role in ("DEALS_PRIMARY", "ROSTER_PRIMARY", "CAPACITY_PRIMARY", "WORKLOAD_PRIMARY"))
    return build_run_setup_acceptance(
        run_id="run-scenario-e",
        lane=LaneV1.CAPACITY_HEATMAP,
        actor="synthetic-manager",
        accepted_at=NOW,
        policy=policy(),
        source_slots=slots,
        authority_and_core_confirmed=True,
        advanced_confirmed=True,
    )


def scenario():
    return run_emea_capacity_scenario(
        run_id="run-scenario-e",
        demands=(demand(),),
        consultants=(consultant(),),
        capacities=(capacity(),),
        policy=policy(),
        policy_sha256=canonical_sha256(policy()),
        source_manifest_ids=("sm-deals", "sm-capacity", "sm-roster"),
        mapping_profile_sha256s=(HASH,),
        setup_acceptance=setup_acceptance(),
        created_at=NOW,
    )


def test_scenario_e_emea_25_percent_flips_24h_demand_to_deficit() -> None:
    result = scenario()
    base = next(
        cell for cell in result.base_cells
        if cell.region_id == "EMEA" and cell.skill_id == "security" and cell.week_bucket == 1
    )
    changed = next(
        cell for cell in result.scenario_cells
        if cell.region_id == "EMEA" and cell.skill_id == "security" and cell.week_bucket == 1
    )
    assert base.demand_units == 48  # 24 hours in 30-minute units
    assert result.changes[0].scenario_effort_units == 60  # 30 hours
    assert base.eligible_supply_units == changed.eligible_supply_units == 56  # 28 hours
    assert base.surplus_deficit_units == 8
    assert changed.demand_units == 60
    assert changed.surplus_deficit_units == -4
    assert result.label == "USER_SELECTED_ASSUMPTION_NOT_A_FORECAST"


def test_scenario_changes_only_emea_effort_and_requires_advanced_confirmation() -> None:
    original = demand()
    changed = apply_emea_effort_assumption((original,), policy=policy())[0]
    before = original.model_dump()
    after = changed.model_dump()
    assert {key for key in before if before[key] != after[key]} == {"effort_units"}
    with pytest.raises(ValueError, match="Advanced confirmation"):
        run_emea_capacity_scenario(
            run_id="run-scenario-e",
            demands=(original,),
            consultants=(consultant(),),
            capacities=(capacity(),),
            policy=policy(),
            policy_sha256=canonical_sha256(policy()),
            source_manifest_ids=("sm-deals", "sm-capacity", "sm-roster"),
            mapping_profile_sha256s=(HASH,),
            setup_acceptance=None,  # type: ignore[arg-type]
            created_at=NOW,
        )


def test_standalone_heatmap_reconciles_demand_supply_workload_free_and_is_non_additive() -> None:
    cells = compute_capacity_heatmap(
        run_id="run-scenario-e",
        demands=(demand(),),
        consultants=(consultant(),),
        capacities=(capacity(),),
        policy=policy(),
        policy_sha256=canonical_sha256(policy()),
        source_manifest_ids=("sm-deals", "sm-capacity", "sm-roster"),
        mapping_profile_sha256s=(HASH,),
    )
    first = next(cell for cell in cells if cell.week_bucket == 1)
    assert first.demand_units == 48
    assert first.eligible_supply_units == 56
    assert first.committed_workload_units == 0
    assert first.free_units == 56
    assert first.surplus_deficit_units == first.free_units - first.demand_units
    assert first.projected_utilization_bp == 8572
    assert first.skill_rows_additive is False


def solver_receipt() -> SolverReceiptV1:
    return SolverReceiptV1(
        schema_version="orchestrator.solver-receipt.v1",
        solver_receipt_id="solver-digest-fixture",
        run_id="run-scenario-e",
        policy_sha256=canonical_sha256(policy()),
        source_manifest_ids=("sm-capacity", "sm-deals", "sm-roster"),
        mapping_profile_sha256s=(HASH,),
        engine="OR_TOOLS_CP_SAT",
        engine_version="9.15.6755",
        worker_count=1,
        random_seed=1729,
        phase_limit_seconds=5,
        status="OPTIMAL",
        recommendation_status="RECOMMENDATION_AVAILABLE",
        phases=(
            SolverPhaseReceiptV1(phase="MAXIMIZE_SERVICED_PRIORITY", status="OPTIMAL", objective_value=0),
            SolverPhaseReceiptV1(phase="MAXIMIZE_PORTFOLIO_MATCH", status="OPTIMAL", objective_value=0),
            SolverPhaseReceiptV1(phase="MINIMIZE_PEAK_UTILIZATION", status="OPTIMAL", objective_value=0),
            SolverPhaseReceiptV1(phase="STABLE_ID_TIE_BREAK", status="OPTIMAL", objective_value=0),
        ),
        serviced_priority_total=0,
        portfolio_match_total=0,
        peak_projected_utilization_bp=0,
        assignments=(),
        forced_pair_ids=(),
        constraints_verified=True,
        created_at=NOW,
    )


def test_solver_receipt_persists_as_canonical_recommendation_only_artifact(tmp_path: Path) -> None:
    connection = connect_database(tmp_path / "phase3.sqlite")
    apply_migrations(connection)
    store = Phase1Store(connection)
    store.create_run(
        run_id="run-scenario-e", lane="ASSIGNMENT_RECOMMENDATION", synthetic=True, created_at=NOW
    )
    receipt = solver_receipt()
    store.persist_solver_receipt(receipt)
    row = connection.execute(
        "SELECT status, receipt_json, receipt_sha256 FROM solver_receipts WHERE solver_receipt_id = ?",
        (receipt.solver_receipt_id,),
    ).fetchone()
    assert row == (
        "OPTIMAL",
        canonical_json_bytes(receipt).decode(),
        canonical_sha256(receipt),
    )
    connection.close()


def test_deterministic_leadership_digest_is_fact_bound_and_byte_stable() -> None:
    comparison = scenario()
    first = build_leadership_digest(
        solver_receipt=solver_receipt(), scenario_comparison=comparison, created_at=NOW
    )
    second = build_leadership_digest(
        solver_receipt=solver_receipt(), scenario_comparison=comparison, created_at=NOW
    )
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    statements = " ".join(fact.statement for fact in first.facts)
    assert "proved all portfolio objective phases OPTIMAL" in statements
    assert "user-selected EMEA +25% effort assumption" in statements
    assert "not a forecast" in statements
    assert first.recommendation_only is True
    assert first.production_readiness == "NOT_ASSESSED"
