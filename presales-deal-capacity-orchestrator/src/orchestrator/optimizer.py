from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import product
from math import prod

import ortools
from ortools.sat.python import cp_model

from .canonical import canonical_sha256
from .contracts.phase3 import (
    AssignmentChoiceV2,
    OracleResultV1,
    PortfolioProblemV1,
    SolverPhaseReceiptV1,
    SolverReceiptV1,
)
from .contracts.policy import PolicyV2


_STATUS = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.MODEL_INVALID: "MODEL_INVALID",
    cp_model.UNKNOWN: "UNKNOWN",
}


@dataclass(frozen=True)
class _ModelArtifacts:
    model: cp_model.CpModel
    variables: dict[tuple[str, str], cp_model.IntVar]
    peak_utilization: cp_model.IntVar
    tie_expression: cp_model.LinearExpr


def portfolio_problem_sha256(problem: PortfolioProblemV1) -> str:
    """Order-insensitive digest of the frozen portfolio receipt set."""
    payload = {
        "schema_version": problem.schema_version,
        "run_id": problem.run_id,
        "policy_sha256": problem.policy_sha256,
        "deals": tuple(sorted(problem.deals, key=lambda item: item.priority.deal_source_id)),
        "pairs": tuple(sorted(
            problem.pairs,
            key=lambda item: (
                item.eligibility.deal_source_id,
                item.eligibility.consultant_source_id,
            ),
        )),
        "capacities": tuple(sorted(
            problem.capacities, key=lambda item: item.consultant_source_id
        )),
    }
    return canonical_sha256(payload)


def _eligible_pairs(problem: PortfolioProblemV1) -> dict[tuple[str, str], object]:
    return {
        (pair.eligibility.deal_source_id, pair.eligibility.consultant_source_id): pair
        for pair in problem.pairs
        if pair.eligibility.eligible
    }


def _contexts(problem: PortfolioProblemV1) -> tuple[tuple[str, ...], tuple[str, ...]]:
    sources: set[str] = set()
    mappings: set[str] = set()
    receipts = [item.priority for item in problem.deals]
    receipts.extend(problem.capacities)
    for pair in problem.pairs:
        receipts.append(pair.eligibility)
        if pair.fit is not None:
            receipts.append(pair.fit)
    for receipt in receipts:
        sources.update(receipt.source_manifest_ids)
        mappings.update(receipt.mapping_profile_sha256s)
    return tuple(sorted(sources)), tuple(sorted(mappings))


def _build_model(
    problem: PortfolioProblemV1,
    policy: PolicyV2,
    *,
    fixed_priority: int | None = None,
    fixed_match: int | None = None,
    fixed_peak: int | None = None,
    forced_pairs: tuple[tuple[str, str], ...] = (),
) -> _ModelArtifacts:
    model = cp_model.CpModel()
    deals = {item.priority.deal_source_id: item for item in problem.deals}
    capacities = {item.consultant_source_id: item for item in problem.capacities}
    eligible = _eligible_pairs(problem)
    variables = {
        key: model.new_bool_var(f"assign__{key[0]}__{key[1]}")
        for key in sorted(eligible)
    }

    for deal_id in sorted(deals):
        model.add(sum(var for (candidate_deal, _), var in variables.items() if candidate_deal == deal_id) <= 1)

    for forced in forced_pairs:
        variable = variables.get(forced)
        if variable is None:
            model.add(False)
        else:
            model.add(variable == 1)

    candidate_consultants = sorted({consultant_id for _, consultant_id in variables})
    utilization_variables: list[cp_model.IntVar] = []
    for consultant_id in candidate_consultants:
        capacity = capacities[consultant_id]
        for week in range(1, 5):
            buckets = capacity.buckets[:week]
            if any(bucket.free_units is None for bucket in buckets):
                # No eligible receipt should point through incomplete capacity, but
                # retain a hard contradiction instead of weakening the constraint.
                model.add(False)
                continue
            net_units = sum(bucket.scheduled_units - bucket.time_off_units for bucket in buckets)
            baseline_units = sum(bucket.active_workload_units for bucket in buckets)
            assigned = sum(
                deals[deal_id].effort_units * variable
                for (deal_id, candidate_id), variable in variables.items()
                if candidate_id == consultant_id and deals[deal_id].priority.due_week_bucket <= week
            )
            cumulative_free = sum(bucket.free_units or 0 for bucket in buckets)
            model.add(assigned <= cumulative_free)
            model.add((baseline_units + assigned) * 10_000 <= policy.utilization_ceiling * net_units)
            if net_units > 0:
                utilization = model.new_int_var(0, 10_000, f"util__{consultant_id}__{week}")
                # Ceiling division makes the displayed bound conservative and exact.
                model.add_division_equality(
                    utilization,
                    (baseline_units + assigned) * 10_000 + net_units - 1,
                    net_units,
                )
                utilization_variables.append(utilization)
            elif baseline_units != 0:
                model.add(False)

    peak = model.new_int_var(0, 10_000, "peak_projected_utilization_bp")
    if utilization_variables:
        model.add_max_equality(peak, utilization_variables)
    else:
        model.add(peak == 0)

    priority_expression = sum(
        deals[deal_id].priority.priority_bp * variable
        for (deal_id, _), variable in variables.items()
    )
    match_expression = sum(
        eligible[key].fit.fit_bp * variable  # type: ignore[union-attr]
        for key, variable in variables.items()
    )
    ranks = {key: rank for rank, key in enumerate(sorted(variables), start=1)}
    tie_expression = sum(ranks[key] * variable for key, variable in variables.items())

    if fixed_priority is not None:
        model.add(priority_expression == fixed_priority)
    if fixed_match is not None:
        model.add(match_expression == fixed_match)
    if fixed_peak is not None:
        model.add(peak == fixed_peak)

    return _ModelArtifacts(model=model, variables=variables, peak_utilization=peak, tie_expression=tie_expression)


def _configured_solver(policy: PolicyV2) -> cp_model.CpSolver:
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = policy.solver_config.random_seed
    solver.parameters.max_time_in_seconds = policy.solver_config.phase_limit_seconds
    solver.parameters.randomize_search = False
    return solver


def _solve_phase(
    artifacts: _ModelArtifacts,
    policy: PolicyV2,
    *,
    objective: cp_model.LinearExpr | cp_model.IntVar,
    maximize: bool,
) -> tuple[str, int | None, cp_model.CpSolver]:
    if maximize:
        artifacts.model.maximize(objective)
    else:
        artifacts.model.minimize(objective)
    solver = _configured_solver(policy)
    status_code = solver.solve(artifacts.model)
    status = _STATUS.get(status_code, "UNKNOWN")
    value = int(round(solver.objective_value)) if status in {"OPTIMAL", "FEASIBLE"} else None
    return status, value, solver


def _failure_receipt(
    *,
    problem: PortfolioProblemV1,
    policy: PolicyV2,
    status: str,
    phases: tuple[SolverPhaseReceiptV1, ...],
    forced_pairs: tuple[tuple[str, str], ...],
    created_at: datetime,
) -> SolverReceiptV1:
    sources, mappings = _contexts(problem)
    payload = {
        "problem": portfolio_problem_sha256(problem),
        "status": status,
        "phases": phases,
        "forced_pairs": forced_pairs,
    }
    return SolverReceiptV1(
        schema_version="orchestrator.solver-receipt.v1",
        solver_receipt_id=f"solver-{canonical_sha256(payload)[:32]}",
        run_id=problem.run_id,
        policy_sha256=problem.policy_sha256,
        source_manifest_ids=sources,
        mapping_profile_sha256s=mappings,
        engine="OR_TOOLS_CP_SAT",
        engine_version=ortools.__version__,
        worker_count=1,
        random_seed=policy.solver_config.random_seed,
        phase_limit_seconds=policy.solver_config.phase_limit_seconds,
        status=status,
        recommendation_status=("NO_FEASIBLE_ASSIGNMENT" if status == "NO_FEASIBLE_ASSIGNMENT" else "SOLVER_FAILURE"),
        phases=phases,
        serviced_priority_total=None,
        portfolio_match_total=None,
        peak_projected_utilization_bp=None,
        assignments=(),
        forced_pair_ids=tuple(f"{deal}:{consultant}" for deal, consultant in forced_pairs),
        constraints_verified=False,
        created_at=created_at,
    )


def _objective_values(
    problem: PortfolioProblemV1,
    assignments: tuple[tuple[str, str], ...],
) -> tuple[int, int, int]:
    deals = {item.priority.deal_source_id: item for item in problem.deals}
    pairs = _eligible_pairs(problem)
    capacities = {item.consultant_source_id: item for item in problem.capacities}
    priority = sum(deals[deal].priority.priority_bp for deal, _ in assignments)
    match = sum(pairs[(deal, consultant)].fit.fit_bp for deal, consultant in assignments)  # type: ignore[union-attr]
    peak = 0
    candidate_consultants = sorted({consultant for _, consultant in pairs})
    for consultant in candidate_consultants:
        capacity = capacities[consultant]
        for week in range(1, 5):
            buckets = capacity.buckets[:week]
            net = sum(bucket.scheduled_units - bucket.time_off_units for bucket in buckets)
            baseline = sum(bucket.active_workload_units for bucket in buckets)
            added = sum(
                deals[deal].effort_units
                for deal, assigned_consultant in assignments
                if assigned_consultant == consultant and deals[deal].priority.due_week_bucket <= week
            )
            utilization = 0 if net == 0 else ((baseline + added) * 10_000 + net - 1) // net
            peak = max(peak, utilization)
    return priority, match, peak


def _verify_constraints(
    problem: PortfolioProblemV1,
    policy: PolicyV2,
    assignments: tuple[tuple[str, str], ...],
    forced_pairs: tuple[tuple[str, str], ...],
) -> bool:
    deals = {item.priority.deal_source_id: item for item in problem.deals}
    capacities = {item.consultant_source_id: item for item in problem.capacities}
    eligible = _eligible_pairs(problem)
    if not set(forced_pairs).issubset(assignments):
        return False
    if any(pair not in eligible for pair in assignments):
        return False
    if len({deal for deal, _ in assignments}) != len(assignments):
        return False
    for consultant in {consultant for _, consultant in assignments}:
        capacity = capacities[consultant]
        for week in range(1, 5):
            buckets = capacity.buckets[:week]
            if any(bucket.free_units is None for bucket in buckets):
                return False
            assigned = sum(
                deals[deal].effort_units
                for deal, candidate in assignments
                if candidate == consultant and deals[deal].priority.due_week_bucket <= week
            )
            free = sum(bucket.free_units or 0 for bucket in buckets)
            net = sum(bucket.scheduled_units - bucket.time_off_units for bucket in buckets)
            baseline = sum(bucket.active_workload_units for bucket in buckets)
            if assigned > free or (baseline + assigned) * 10_000 > policy.utilization_ceiling * net:
                return False
    return True


def solve_portfolio(
    *,
    problem: PortfolioProblemV1,
    policy: PolicyV2,
    created_at: datetime,
    forced_pairs: tuple[tuple[str, str], ...] = (),
) -> SolverReceiptV1:
    """Solve the whole portfolio in deterministic sequential CP-SAT phases.

    Inputs are frozen deterministic receipts. There is intentionally no transcript,
    quote, observation, win-rate, source transport, or write/action parameter.
    """
    if canonical_sha256(policy) != problem.policy_sha256:
        raise ValueError("optimizer policy does not match the frozen problem")
    forced_pairs = tuple(sorted(forced_pairs))
    eligible = _eligible_pairs(problem)
    if not eligible and not forced_pairs:
        return _failure_receipt(
            problem=problem,
            policy=policy,
            status="NO_FEASIBLE_ASSIGNMENT",
            phases=(),
            forced_pairs=forced_pairs,
            created_at=created_at,
        )

    deals = {item.priority.deal_source_id: item for item in problem.deals}
    phases: list[SolverPhaseReceiptV1] = []

    phase1 = _build_model(problem, policy, forced_pairs=forced_pairs)
    priority_expression = sum(
        deals[deal].priority.priority_bp * variable
        for (deal, _), variable in phase1.variables.items()
    )
    status, priority_optimum, _ = _solve_phase(phase1, policy, objective=priority_expression, maximize=True)
    phases.append(SolverPhaseReceiptV1(
        phase="MAXIMIZE_SERVICED_PRIORITY", status=status, objective_value=priority_optimum
    ))
    if status != "OPTIMAL":
        return _failure_receipt(
            problem=problem, policy=policy, status=status, phases=tuple(phases),
            forced_pairs=forced_pairs, created_at=created_at,
        )
    assert priority_optimum is not None

    pairs = _eligible_pairs(problem)
    phase2 = _build_model(problem, policy, fixed_priority=priority_optimum, forced_pairs=forced_pairs)
    match_expression = sum(
        pairs[key].fit.fit_bp * variable  # type: ignore[union-attr]
        for key, variable in phase2.variables.items()
    )
    status, match_optimum, _ = _solve_phase(phase2, policy, objective=match_expression, maximize=True)
    phases.append(SolverPhaseReceiptV1(
        phase="MAXIMIZE_PORTFOLIO_MATCH", status=status, objective_value=match_optimum
    ))
    if status != "OPTIMAL":
        return _failure_receipt(
            problem=problem, policy=policy, status=status, phases=tuple(phases),
            forced_pairs=forced_pairs, created_at=created_at,
        )
    assert match_optimum is not None

    phase3 = _build_model(
        problem, policy, fixed_priority=priority_optimum, fixed_match=match_optimum,
        forced_pairs=forced_pairs,
    )
    status, peak_optimum, _ = _solve_phase(
        phase3, policy, objective=phase3.peak_utilization, maximize=False
    )
    phases.append(SolverPhaseReceiptV1(
        phase="MINIMIZE_PEAK_UTILIZATION", status=status, objective_value=peak_optimum
    ))
    if status != "OPTIMAL":
        return _failure_receipt(
            problem=problem, policy=policy, status=status, phases=tuple(phases),
            forced_pairs=forced_pairs, created_at=created_at,
        )
    assert peak_optimum is not None

    phase4 = _build_model(
        problem, policy, fixed_priority=priority_optimum, fixed_match=match_optimum,
        fixed_peak=peak_optimum, forced_pairs=forced_pairs,
    )
    status, tie_value, final_solver = _solve_phase(
        phase4, policy, objective=phase4.tie_expression, maximize=False
    )
    phases.append(SolverPhaseReceiptV1(
        phase="STABLE_ID_TIE_BREAK", status=status, objective_value=tie_value
    ))
    if status != "OPTIMAL":
        return _failure_receipt(
            problem=problem, policy=policy, status=status, phases=tuple(phases),
            forced_pairs=forced_pairs, created_at=created_at,
        )

    selected = tuple(sorted(
        key for key, variable in phase4.variables.items() if final_solver.value(variable) == 1
    ))
    verified = _verify_constraints(problem, policy, selected, forced_pairs)
    recomputed_priority, recomputed_match, recomputed_peak = _objective_values(problem, selected)
    if not verified or (recomputed_priority, recomputed_match, recomputed_peak) != (
        priority_optimum, match_optimum, peak_optimum
    ):
        return _failure_receipt(
            problem=problem, policy=policy, status="MODEL_INVALID", phases=tuple(phases),
            forced_pairs=forced_pairs, created_at=created_at,
        )

    choices = tuple(AssignmentChoiceV2(
        deal_source_id=deal_id,
        consultant_source_id=consultant_id,
        priority_receipt_id=deals[deal_id].priority.priority_receipt_id,
        eligibility_receipt_id=pairs[(deal_id, consultant_id)].eligibility.eligibility_receipt_id,
        fit_receipt_id=pairs[(deal_id, consultant_id)].fit.fit_receipt_id,  # type: ignore[union-attr]
        due_week_bucket=deals[deal_id].priority.due_week_bucket,
        effort_units=deals[deal_id].effort_units,
        priority_bp=deals[deal_id].priority.priority_bp,
        fit_bp=pairs[(deal_id, consultant_id)].fit.fit_bp,  # type: ignore[union-attr]
    ) for deal_id, consultant_id in selected)
    sources, mappings = _contexts(problem)
    identity = {
        "problem": portfolio_problem_sha256(problem),
        "phases": phases,
        "assignments": choices,
        "objectives": (priority_optimum, match_optimum, peak_optimum),
        "forced_pairs": forced_pairs,
    }
    return SolverReceiptV1(
        schema_version="orchestrator.solver-receipt.v1",
        solver_receipt_id=f"solver-{canonical_sha256(identity)[:32]}",
        run_id=problem.run_id,
        policy_sha256=problem.policy_sha256,
        source_manifest_ids=sources,
        mapping_profile_sha256s=mappings,
        engine="OR_TOOLS_CP_SAT",
        engine_version=ortools.__version__,
        worker_count=1,
        random_seed=policy.solver_config.random_seed,
        phase_limit_seconds=policy.solver_config.phase_limit_seconds,
        status="OPTIMAL",
        recommendation_status="RECOMMENDATION_AVAILABLE",
        phases=tuple(phases),
        serviced_priority_total=priority_optimum,
        portfolio_match_total=match_optimum,
        peak_projected_utilization_bp=peak_optimum,
        assignments=choices,
        forced_pair_ids=tuple(f"{deal}:{consultant}" for deal, consultant in forced_pairs),
        constraints_verified=True,
        created_at=created_at,
    )


def brute_force_oracle(
    *,
    problem: PortfolioProblemV1,
    policy: PolicyV2,
    forced_pairs: tuple[tuple[str, str], ...] = (),
    maximum_combinations: int = 1_000_000,
) -> OracleResultV1:
    """Exhaustive oracle for tiny fixtures; never used as a scale fallback."""
    if canonical_sha256(policy) != problem.policy_sha256:
        raise ValueError("oracle policy does not match the frozen problem")
    eligible = _eligible_pairs(problem)
    forced_pairs = tuple(sorted(forced_pairs))
    if not eligible and not forced_pairs:
        return OracleResultV1(
            schema_version="orchestrator.brute-force-oracle.v1",
            status="NO_FEASIBLE_ASSIGNMENT", assignments=(), combinations_evaluated=0,
        )
    deals = sorted(item.priority.deal_source_id for item in problem.deals)
    options = [
        (None,) + tuple(sorted(consultant for deal_id, consultant in eligible if deal_id == deal))
        for deal in deals
    ]
    combination_count = prod(len(items) for items in options)
    if combination_count > maximum_combinations:
        raise ValueError("brute-force oracle is limited to tiny fixtures")
    ranks = {key: rank for rank, key in enumerate(sorted(eligible), start=1)}
    best_key: tuple[int, int, int, int] | None = None
    best_assignments: tuple[tuple[str, str], ...] = ()
    evaluated = 0
    for selected_options in product(*options):
        selected = tuple(
            (deal, consultant) for deal, consultant in zip(deals, selected_options) if consultant is not None
        )
        evaluated += 1
        if not _verify_constraints(problem, policy, selected, forced_pairs):
            continue
        priority, match, peak = _objective_values(problem, selected)
        tie_cost = sum(ranks[pair] for pair in selected)
        key = (priority, match, -peak, -tie_cost)
        if best_key is None or key > best_key:
            best_key = key
            best_assignments = selected
    if best_key is None:
        return OracleResultV1(
            schema_version="orchestrator.brute-force-oracle.v1",
            status="INFEASIBLE", assignments=(), combinations_evaluated=evaluated,
        )
    priority, match, peak = _objective_values(problem, best_assignments)
    return OracleResultV1(
        schema_version="orchestrator.brute-force-oracle.v1",
        status="OPTIMAL",
        serviced_priority_total=priority,
        portfolio_match_total=match,
        peak_projected_utilization_bp=peak,
        assignments=best_assignments,
        combinations_evaluated=evaluated,
    )
