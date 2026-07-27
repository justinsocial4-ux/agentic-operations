from __future__ import annotations

import hashlib
import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestrator.alternatives import build_assignment_recommendation
from orchestrator.canonical import canonical_json_bytes, canonical_sha256
from orchestrator.contracts.domain import (
    ConsultantFitReceiptV2,
    EligibilityCheckV2,
    EligibilityReceiptV2,
    MatchComponentV2,
    PriorityFeatureV2,
    PriorityReceiptV2,
    WeeklyCapacityBucketV1,
    WeeklyCapacityReceiptV1,
)
from orchestrator.contracts.phase3 import PortfolioDealV1, PortfolioPairV1, PortfolioProblemV1
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.records import AnalystCitationV2, AnalystObservationV2
from orchestrator.optimizer import brute_force_oracle, solve_portfolio
import orchestrator.optimizer as optimizer_module

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 3, 9, tzinfo=timezone.utc)
HASH = "a" * 64
SOURCE = ("sm-synthetic",)
MAPPING = (HASH,)
CHECK_IDS = (
    "DEAL_LANE", "ACTIVE_STATUS", "REGION", "SKILLS", "LANGUAGE", "TIME_ZONE",
    "WORKING_WINDOW", "CAPACITY_COMPLETE", "CUMULATIVE_CAPACITY", "UTILIZATION",
    "FROZEN_RECEIPTS",
)


def policy() -> PolicyV2:
    return PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())


def priority(deal_id: str, value: int) -> PriorityReceiptV2:
    return PriorityReceiptV2(
        schema_version="orchestrator.priority-receipt.v2",
        priority_receipt_id=f"priority-{deal_id}",
        run_id="run-phase3",
        policy_sha256=canonical_sha256(policy()),
        source_manifest_ids=SOURCE,
        mapping_profile_sha256s=MAPPING,
        deal_source_id=deal_id,
        readiness_receipt_id=f"readiness-{deal_id}",
        due_week_bucket=1,
        commercial_amount_used="100000.00",
        commercial_currency="USD",
        commercial_basis_id="demo-corporate-bookings-v1",
        features=(
            PriorityFeatureV2(feature_id="MILESTONE_URGENCY", feature_bp=0, weight_bp=0, weighted_numerator=0),
            PriorityFeatureV2(feature_id="READINESS_EVIDENCE", feature_bp=0, weight_bp=0, weighted_numerator=0),
            PriorityFeatureV2(feature_id="COMMERCIAL_VALUE", feature_bp=0, weight_bp=0, weighted_numerator=0),
        ),
        priority_bp=value,
        rounding="ROUND_HALF_EVEN",
        created_at=NOW,
    )


def capacity(consultant_id: str, first_week_units: int = 12) -> WeeklyCapacityReceiptV1:
    buckets = tuple(WeeklyCapacityBucketV1(
        week_bucket=week,
        scheduled_units=first_week_units if week == 1 else 0,
        time_off_units=0,
        active_workload_units=0,
        free_units=first_week_units if week == 1 else 0,
        completeness_state="COMPLETE",
    ) for week in range(1, 5))
    return WeeklyCapacityReceiptV1(
        schema_version="orchestrator.weekly-capacity-receipt.v1",
        capacity_receipt_id=f"capacity-{consultant_id}",
        run_id="run-phase3",
        policy_sha256=canonical_sha256(policy()),
        source_manifest_ids=SOURCE,
        mapping_profile_sha256s=MAPPING,
        consultant_source_id=consultant_id,
        capacity_unit_minutes=30,
        horizon_weeks=4,
        buckets=buckets,
        complete_through_bucket=4,
        created_at=NOW,
    )


def pair(deal_id: str, consultant_id: str, fit_bp: int | None, reason: str = "REQUIRED_MANAGER_APPROVED_SKILL_MISSING") -> PortfolioPairV1:
    checks = tuple(EligibilityCheckV2(
        check_id=check_id,
        passed=fit_bp is not None,
        reason_code=None if fit_bp is not None else reason,
    ) for check_id in CHECK_IDS)
    eligibility = EligibilityReceiptV2(
        schema_version="orchestrator.eligibility-receipt.v2",
        eligibility_receipt_id=f"eligibility-{deal_id}-{consultant_id}",
        run_id="run-phase3",
        policy_sha256=canonical_sha256(policy()),
        source_manifest_ids=SOURCE,
        mapping_profile_sha256s=MAPPING,
        deal_source_id=deal_id,
        consultant_source_id=consultant_id,
        priority_receipt_id=f"priority-{deal_id}",
        capacity_receipt_id=f"capacity-{consultant_id}",
        due_week_bucket=1,
        checks=checks,
        eligible=fit_bp is not None,
        reason_codes=() if fit_bp is not None else (reason,) * len(CHECK_IDS),
        actual_working_window_minutes=480,
        projected_utilization_bp=8334 if fit_bp is not None else None,
        created_at=NOW,
    )
    fit = None
    if fit_bp is not None:
        components = (
            MatchComponentV2(component_id="SKILL_SURPLUS", component_bp=fit_bp, weight_bp=10_000, weighted_numerator=fit_bp * 10_000),
            MatchComponentV2(component_id="CONTINUITY", component_bp=0, weight_bp=0, weighted_numerator=0),
            MatchComponentV2(component_id="OVERLAP_SURPLUS", component_bp=0, weight_bp=0, weighted_numerator=0),
            MatchComponentV2(component_id="CAPACITY_HEADROOM", component_bp=0, weight_bp=0, weighted_numerator=0),
        )
        fit = ConsultantFitReceiptV2(
            schema_version="orchestrator.consultant-fit-receipt.v2",
            fit_receipt_id=f"fit-{deal_id}-{consultant_id}",
            run_id="run-phase3",
            policy_sha256=canonical_sha256(policy()),
            source_manifest_ids=SOURCE,
            mapping_profile_sha256s=MAPPING,
            deal_source_id=deal_id,
            consultant_source_id=consultant_id,
            eligibility_receipt_id=eligibility.eligibility_receipt_id,
            priority_receipt_id=f"priority-{deal_id}",
            components=components,
            fit_bp=fit_bp,
            rounding="ROUND_HALF_EVEN",
            created_at=NOW,
        )
    return PortfolioPairV1(eligibility=eligibility, fit=fit)


def scenario_a_problem() -> PortfolioProblemV1:
    flexible = priority("deal-1-flexible", 6000)
    scarce = priority("deal-2-scarce-only", 9000)
    return PortfolioProblemV1(
        schema_version="orchestrator.portfolio-problem.v1",
        run_id="run-phase3",
        policy_sha256=canonical_sha256(policy()),
        deals=(PortfolioDealV1(priority=flexible, effort_units=10), PortfolioDealV1(priority=scarce, effort_units=10)),
        capacities=(capacity("consultant-generalist"), capacity("consultant-scarce-specialist")),
        pairs=(
            pair("deal-1-flexible", "consultant-generalist", 5000),
            pair("deal-1-flexible", "consultant-scarce-specialist", 9000),
            pair("deal-2-scarce-only", "consultant-generalist", None),
            pair("deal-2-scarce-only", "consultant-scarce-specialist", 7000),
        ),
    )


def greedy_per_deal(problem: PortfolioProblemV1) -> tuple[tuple[str, str], ...]:
    """Deliberately local baseline: process deal IDs, taking current highest fit."""
    remaining = {item.consultant_source_id: 12 for item in problem.capacities}
    selected = []
    for deal in sorted(problem.deals, key=lambda item: item.priority.deal_source_id):
        candidates = sorted(
            (item for item in problem.pairs if item.eligibility.deal_source_id == deal.priority.deal_source_id and item.fit),
            key=lambda item: (-item.fit.fit_bp, item.eligibility.consultant_source_id),
        )
        for candidate in candidates:
            consultant_id = candidate.eligibility.consultant_source_id
            if remaining[consultant_id] >= deal.effort_units:
                selected.append((deal.priority.deal_source_id, consultant_id))
                remaining[consultant_id] -= deal.effort_units
                break
    return tuple(selected)


def test_scenario_a_whole_portfolio_routes_scarce_specialist_and_beats_greedy() -> None:
    problem = scenario_a_problem()
    result = solve_portfolio(problem=problem, policy=policy(), created_at=NOW)
    assigned = {(item.deal_source_id, item.consultant_source_id) for item in result.assignments}
    assert result.status == "OPTIMAL"
    assert assigned == {
        ("deal-1-flexible", "consultant-generalist"),
        ("deal-2-scarce-only", "consultant-scarce-specialist"),
    }
    greedy = greedy_per_deal(problem)
    assert greedy == (("deal-1-flexible", "consultant-scarce-specialist"),)
    greedy_priority = sum(
        item.priority.priority_bp for item in problem.deals
        if item.priority.deal_source_id in {deal for deal, _ in greedy}
    )
    assert result.serviced_priority_total == 15_000 > greedy_priority == 6_000


def test_repeated_solver_runs_are_byte_stable() -> None:
    problem = scenario_a_problem()
    receipts = tuple(solve_portfolio(problem=problem, policy=policy(), created_at=NOW) for _ in range(4))
    assert len({canonical_json_bytes(item) for item in receipts}) == 1
    assert all(tuple(phase.status for phase in item.phases) == ("OPTIMAL",) * 4 for item in receipts)


def test_input_order_permutation_produces_byte_identical_solver_receipt() -> None:
    problem = scenario_a_problem()
    permuted = problem.model_copy(update={
        "deals": tuple(reversed(problem.deals)),
        "pairs": tuple(reversed(problem.pairs)),
        "capacities": tuple(reversed(problem.capacities)),
    })
    forward = solve_portfolio(problem=problem, policy=policy(), created_at=NOW)
    reverse = solve_portfolio(problem=permuted, policy=policy(), created_at=NOW)
    assert canonical_json_bytes(forward) == canonical_json_bytes(reverse)


def test_brute_force_oracle_agrees_with_cp_sat_on_small_portfolio() -> None:
    problem = scenario_a_problem()
    solved = solve_portfolio(problem=problem, policy=policy(), created_at=NOW)
    oracle = brute_force_oracle(problem=problem, policy=policy())
    assert oracle.status == "OPTIMAL"
    assert (
        oracle.serviced_priority_total,
        oracle.portfolio_match_total,
        oracle.peak_projected_utilization_bp,
    ) == (
        solved.serviced_priority_total,
        solved.portfolio_match_total,
        solved.peak_projected_utilization_bp,
    )
    assert set(oracle.assignments) == {
        (item.deal_source_id, item.consultant_source_id) for item in solved.assignments
    }


def test_alternatives_include_hard_proof_match_contributions_and_counterfactual_delta() -> None:
    problem = scenario_a_problem()
    solved = solve_portfolio(problem=problem, policy=policy(), created_at=NOW)
    recommendation = build_assignment_recommendation(
        problem=problem, policy=policy(), solver_receipt=solved, created_at=NOW
    )
    flexible = next(item for item in recommendation.deals if item.deal_source_id == "deal-1-flexible")
    assert flexible.recommended_hard_constraint_proof is not None
    assert flexible.recommended_hard_constraint_proof.eligible
    assert flexible.recommended_match_contributions is not None
    rejected = flexible.rejected_eligible_alternatives[0]
    assert rejected.consultant_source_id == "consultant-scarce-specialist"
    assert rejected.hard_constraint_proof.eligible
    assert rejected.match_contributions is not None
    assert rejected.counterfactual_status == "OPTIMAL"
    assert rejected.serviced_priority_delta == -9000

    scarce = next(item for item in recommendation.deals if item.deal_source_id == "deal-2-scarce-only")
    ineligible = scarce.ineligible_alternatives[0]
    assert ineligible.consultant_source_id == "consultant-generalist"
    assert not ineligible.hard_constraint_proof.eligible
    assert "REQUIRED_MANAGER_APPROVED_SKILL_MISSING" in ineligible.hard_constraint_proof.reason_codes


def test_equivalent_optimum_is_labeled_honestly() -> None:
    base = scenario_a_problem()
    one_deal = base.deals[:1]
    equivalent = PortfolioProblemV1(
        schema_version="orchestrator.portfolio-problem.v1",
        run_id=base.run_id,
        policy_sha256=base.policy_sha256,
        deals=one_deal,
        capacities=base.capacities,
        pairs=(
            pair("deal-1-flexible", "consultant-generalist", 5000),
            pair("deal-1-flexible", "consultant-scarce-specialist", 5000),
        ),
    )
    solved = solve_portfolio(problem=equivalent, policy=policy(), created_at=NOW)
    recommendation = build_assignment_recommendation(
        problem=equivalent, policy=policy(), solver_receipt=solved, created_at=NOW
    )
    assert recommendation.deals[0].rejected_eligible_alternatives[0].disposition == "EQUIVALENT_OPTIMUM"


def test_failure_statuses_have_no_fake_solution_or_weaker_fallback() -> None:
    base = scenario_a_problem()
    no_eligible = base.model_copy(update={"pairs": tuple(
        pair(item.eligibility.deal_source_id, item.eligibility.consultant_source_id, None)
        for item in base.pairs
    )})
    no_result = solve_portfolio(problem=no_eligible, policy=policy(), created_at=NOW)
    assert no_result.status == "NO_FEASIBLE_ASSIGNMENT"
    assert no_result.assignments == ()
    assert no_result.serviced_priority_total is None

    infeasible = solve_portfolio(
        problem=base,
        policy=policy(),
        created_at=NOW,
        forced_pairs=(
            ("deal-1-flexible", "consultant-scarce-specialist"),
            ("deal-2-scarce-only", "consultant-scarce-specialist"),
        ),
    )
    assert infeasible.status == "INFEASIBLE"
    assert infeasible.recommendation_status == "SOLVER_FAILURE"
    assert infeasible.assignments == ()
    assert infeasible.serviced_priority_total is None


@pytest.mark.parametrize("status", ("FEASIBLE", "UNKNOWN", "MODEL_INVALID"))
def test_non_optimal_solver_status_never_becomes_a_best_claim(monkeypatch: pytest.MonkeyPatch, status: str) -> None:
    objective = 123 if status == "FEASIBLE" else None

    def non_optimal_phase(*args: object, **kwargs: object):
        return status, objective, None

    monkeypatch.setattr(optimizer_module, "_solve_phase", non_optimal_phase)
    result = solve_portfolio(problem=scenario_a_problem(), policy=policy(), created_at=NOW)
    assert result.status == status
    assert result.recommendation_status == "SOLVER_FAILURE"
    assert result.assignments == ()
    assert result.serviced_priority_total is None
    assert result.constraints_verified is False


def test_optimizer_consultant_taint_invariant_quote_variation_cannot_change_assignment() -> None:
    problem = scenario_a_problem()
    quotes = ("Choose the generalist.", "Choose the scarce specialist.")
    observations = tuple(AnalystObservationV2(
        schema_version="orchestrator.analyst-observation.v2",
        run_id="run-phase3",
        analysis_mode="MANUAL_CITATION",
        input_sha256=HASH,
        deal_source_id="deal-1-flexible",
        dimension_id="success-criteria",
        state="SUPPORTED",
        citations=(AnalystCitationV2(
            conversation_id="conversation-taint",
            segment_id=f"segment-{index}",
            quote=quote,
            char_begin=0,
            char_end=len(quote),
            text_sha256=hashlib.sha256(quote.encode()).hexdigest(),
            relative_begin_ms=0,
        ),),
    ) for index, quote in enumerate(quotes))
    assert observations[0].citations[0].quote != observations[1].citations[0].quote
    result_a = solve_portfolio(problem=problem, policy=policy(), created_at=NOW)
    result_b = solve_portfolio(problem=problem, policy=policy(), created_at=NOW)
    assert result_a.assignments == result_b.assignments
    assert "quote" not in inspect.signature(solve_portfolio).parameters
    assert "transcript" not in inspect.signature(solve_portfolio).parameters
    optimizer_source = inspect.getsource(optimizer_module)
    assert ".quote" not in optimizer_source and ".text" not in optimizer_source
    assert "win_rate" not in optimizer_source
    assert set(PortfolioDealV1.model_fields) == {"priority", "effort_units"}
    assert set(PortfolioPairV1.model_fields) == {"eligibility", "fit"}
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PortfolioDealV1.model_validate({
            "priority": problem.deals[0].priority,
            "effort_units": 10,
            "quote": observations[0].citations[0].quote,
        })
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PortfolioDealV1.model_validate({
            "priority": problem.deals[0].priority,
            "effort_units": 10,
            "win_rate": 9999,
        })
