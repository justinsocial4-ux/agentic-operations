from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_CEILING
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .base import Identifier, Sha256, StrictContract, require_offset_aware
from .domain import (
    ConsultantFitReceiptV2,
    EligibilityCheckV2,
    EligibilityReceiptV2,
    MatchComponentV2,
    PriorityReceiptV2,
    ReceiptContextV2,
    WeeklyCapacityReceiptV1,
)

SolverStatusV1 = Literal[
    "OPTIMAL", "FEASIBLE", "INFEASIBLE", "MODEL_INVALID", "UNKNOWN",
    "NO_FEASIBLE_ASSIGNMENT",
]


class PortfolioDealV1(StrictContract):
    """Frozen optimizer deal input. It deliberately has no transcript/evidence text."""

    priority: PriorityReceiptV2
    effort_units: int = Field(gt=0)


class PortfolioPairV1(StrictContract):
    """Pair input derived only from deterministic eligibility and manager-approved fit."""

    eligibility: EligibilityReceiptV2
    fit: ConsultantFitReceiptV2 | None = None

    @model_validator(mode="after")
    def fit_exists_only_for_eligible_pair(self) -> "PortfolioPairV1":
        if self.eligibility.eligible != (self.fit is not None):
            raise ValueError("exactly eligible pairs must carry consultant fit")
        if self.fit is not None and (
            self.fit.eligibility_receipt_id != self.eligibility.eligibility_receipt_id
            or self.fit.deal_source_id != self.eligibility.deal_source_id
            or self.fit.consultant_source_id != self.eligibility.consultant_source_id
            or self.fit.priority_receipt_id != self.eligibility.priority_receipt_id
        ):
            raise ValueError("fit receipt does not match its eligibility receipt")
        return self


class PortfolioProblemV1(StrictContract):
    schema_version: Literal["orchestrator.portfolio-problem.v1"]
    run_id: Identifier
    policy_sha256: Sha256
    deals: tuple[PortfolioDealV1, ...] = Field(min_length=1)
    pairs: tuple[PortfolioPairV1, ...]
    capacities: tuple[WeeklyCapacityReceiptV1, ...]

    @model_validator(mode="after")
    def frozen_receipts_reconcile(self) -> "PortfolioProblemV1":
        deal_ids = tuple(item.priority.deal_source_id for item in self.deals)
        if len(deal_ids) != len(set(deal_ids)):
            raise ValueError("portfolio deals must be unique")
        capacity_ids = tuple(item.consultant_source_id for item in self.capacities)
        if len(capacity_ids) != len(set(capacity_ids)):
            raise ValueError("portfolio consultant capacities must be unique")
        pair_ids = tuple(
            (item.eligibility.deal_source_id, item.eligibility.consultant_source_id)
            for item in self.pairs
        )
        if len(pair_ids) != len(set(pair_ids)):
            raise ValueError("portfolio pairs must be unique")
        priorities = {item.priority.priority_receipt_id: item.priority for item in self.deals}
        deal_set = set(deal_ids)
        capacity_set = set(capacity_ids)
        for deal in self.deals:
            if deal.priority.run_id != self.run_id or deal.priority.policy_sha256 != self.policy_sha256:
                raise ValueError("priority receipt is outside the frozen optimizer run")
        for capacity in self.capacities:
            if capacity.run_id != self.run_id or capacity.policy_sha256 != self.policy_sha256:
                raise ValueError("capacity receipt is outside the frozen optimizer run")
        for pair in self.pairs:
            eligibility = pair.eligibility
            if (
                eligibility.run_id != self.run_id
                or eligibility.policy_sha256 != self.policy_sha256
                or eligibility.deal_source_id not in deal_set
                or eligibility.consultant_source_id not in capacity_set
                or eligibility.priority_receipt_id not in priorities
                or priorities[eligibility.priority_receipt_id].deal_source_id != eligibility.deal_source_id
            ):
                raise ValueError("eligibility receipt is outside the frozen optimizer run")
        return self


class SolverPhaseReceiptV1(StrictContract):
    phase: Literal[
        "MAXIMIZE_SERVICED_PRIORITY", "MAXIMIZE_PORTFOLIO_MATCH",
        "MINIMIZE_PEAK_UTILIZATION", "STABLE_ID_TIE_BREAK",
    ]
    status: SolverStatusV1
    objective_value: int | None = None


class AssignmentChoiceV2(StrictContract):
    deal_source_id: Identifier
    consultant_source_id: Identifier
    priority_receipt_id: Identifier
    eligibility_receipt_id: Identifier
    fit_receipt_id: Identifier
    due_week_bucket: Literal[1, 2, 3, 4]
    effort_units: int = Field(gt=0)
    priority_bp: int = Field(ge=0, le=10_000)
    fit_bp: int = Field(ge=0, le=10_000)


class SolverReceiptV1(ReceiptContextV2):
    schema_version: Literal["orchestrator.solver-receipt.v1"]
    solver_receipt_id: Identifier
    engine: Literal["OR_TOOLS_CP_SAT"]
    engine_version: str = Field(min_length=1, max_length=40)
    worker_count: Literal[1]
    random_seed: int = Field(ge=0)
    phase_limit_seconds: int = Field(ge=1, le=30)
    status: SolverStatusV1
    recommendation_status: Literal[
        "RECOMMENDATION_AVAILABLE", "NO_FEASIBLE_ASSIGNMENT", "SOLVER_FAILURE",
    ]
    phases: tuple[SolverPhaseReceiptV1, ...]
    serviced_priority_total: int | None = Field(default=None, ge=0)
    portfolio_match_total: int | None = Field(default=None, ge=0)
    peak_projected_utilization_bp: int | None = Field(default=None, ge=0)
    assignments: tuple[AssignmentChoiceV2, ...]
    forced_pair_ids: tuple[str, ...]
    constraints_verified: bool
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def solver_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def outcome_is_honest(self) -> "SolverReceiptV1":
        objective_values = (
            self.serviced_priority_total,
            self.portfolio_match_total,
            self.peak_projected_utilization_bp,
        )
        if self.status == "OPTIMAL":
            if self.recommendation_status != "RECOMMENDATION_AVAILABLE":
                raise ValueError("OPTIMAL portfolio must expose a recommendation")
            if any(value is None for value in objective_values) or not self.constraints_verified:
                raise ValueError("OPTIMAL receipt requires verified objective values")
        elif self.status == "NO_FEASIBLE_ASSIGNMENT":
            if self.recommendation_status != "NO_FEASIBLE_ASSIGNMENT" or self.assignments:
                raise ValueError("no-feasible status cannot carry an assignment")
            if any(value is not None for value in objective_values):
                raise ValueError("no-feasible status cannot fabricate objectives")
        else:
            if self.recommendation_status != "SOLVER_FAILURE" or self.assignments:
                raise ValueError("solver failure cannot carry a recommendation")
            if any(value is not None for value in objective_values) or self.constraints_verified:
                raise ValueError("solver failure cannot claim verified objectives")
        assignment_keys = tuple(
            (item.deal_source_id, item.consultant_source_id) for item in self.assignments
        )
        if assignment_keys != tuple(sorted(assignment_keys)):
            raise ValueError("solver assignments must use stable ID order")
        if len({item.deal_source_id for item in self.assignments}) != len(self.assignments):
            raise ValueError("a deal may be assigned at most once")
        if self.status == "OPTIMAL":
            expected_phases = (
                "MAXIMIZE_SERVICED_PRIORITY", "MAXIMIZE_PORTFOLIO_MATCH",
                "MINIMIZE_PEAK_UTILIZATION", "STABLE_ID_TIE_BREAK",
            )
            if tuple(item.phase for item in self.phases) != expected_phases:
                raise ValueError("optimal solver receipt requires all sequential phases")
            if any(item.status != "OPTIMAL" for item in self.phases):
                raise ValueError("optimal solver receipt cannot hide a non-optimal phase")
        return self


class OracleResultV1(StrictContract):
    schema_version: Literal["orchestrator.brute-force-oracle.v1"]
    status: Literal["OPTIMAL", "INFEASIBLE", "NO_FEASIBLE_ASSIGNMENT"]
    serviced_priority_total: int | None = Field(default=None, ge=0)
    portfolio_match_total: int | None = Field(default=None, ge=0)
    peak_projected_utilization_bp: int | None = Field(default=None, ge=0)
    assignments: tuple[tuple[Identifier, Identifier], ...]
    combinations_evaluated: int = Field(ge=0)


class HardConstraintProofV1(StrictContract):
    eligibility_receipt_id: Identifier
    eligible: bool
    checks: tuple[EligibilityCheckV2, ...]
    reason_codes: tuple[Identifier, ...]


class MatchContributionProofV1(StrictContract):
    fit_receipt_id: Identifier
    fit_bp: int = Field(ge=0, le=10_000)
    components: tuple[MatchComponentV2, ...]


class AlternativeCandidateV2(StrictContract):
    consultant_source_id: Identifier
    disposition: Literal["REJECTED_ELIGIBLE", "INELIGIBLE", "EQUIVALENT_OPTIMUM"]
    hard_constraint_proof: HardConstraintProofV1
    match_contributions: MatchContributionProofV1 | None = None
    counterfactual_status: SolverStatusV1 | None = None
    serviced_priority_delta: int | None = None
    portfolio_match_delta: int | None = None
    peak_utilization_delta_bp: int | None = None


class DealAlternativesV2(StrictContract):
    deal_source_id: Identifier
    recommended_consultant_source_id: Identifier | None = None
    recommended_hard_constraint_proof: HardConstraintProofV1 | None = None
    recommended_match_contributions: MatchContributionProofV1 | None = None
    rejected_eligible_alternatives: tuple[AlternativeCandidateV2, ...] = Field(max_length=2)
    ineligible_alternatives: tuple[AlternativeCandidateV2, ...]


class AssignmentRecommendationV2(ReceiptContextV2):
    schema_version: Literal["orchestrator.assignment-recommendation.v2"]
    recommendation_id: Identifier
    solver_receipt_id: Identifier
    assignment_status: Literal["RECOMMENDATION_ONLY"]
    solver_status: SolverStatusV1
    deals: tuple[DealAlternativesV2, ...]
    external_writes_attempted: Literal[False]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def recommendation_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)


class CapacityDemandV1(StrictContract):
    deal_source_id: Identifier
    region_id: Identifier
    required_skill_ids: tuple[Identifier, ...] = Field(min_length=1)
    due_week_bucket: Literal[1, 2, 3, 4]
    effort_units: int = Field(ge=0)


class CapacityCellV2(ReceiptContextV2):
    schema_version: Literal["orchestrator.capacity-cell.v2"]
    capacity_cell_id: Identifier
    region_id: Identifier
    skill_id: Identifier
    week_bucket: Literal[1, 2, 3, 4]
    demand_units: int = Field(ge=0)
    eligible_supply_units: int = Field(ge=0)
    committed_workload_units: int = Field(ge=0)
    free_units: int = Field(ge=0)
    projected_utilization_bp: int | None = Field(default=None, ge=0)
    surplus_deficit_units: int
    excluded_incomplete_consultant_ids: tuple[Identifier, ...]
    supply_state: Literal["COMPLETE", "PARTIAL_SUPPLY_EXCLUDED"]
    skill_rows_additive: Literal[False]

    @model_validator(mode="after")
    def capacity_arithmetic_reconciles(self) -> "CapacityCellV2":
        if self.free_units != self.eligible_supply_units - self.committed_workload_units:
            raise ValueError("capacity cell free-unit arithmetic does not reconcile")
        if self.surplus_deficit_units != self.free_units - self.demand_units:
            raise ValueError("capacity cell surplus/deficit arithmetic does not reconcile")
        expected_utilization = (
            None if self.eligible_supply_units == 0
            else (
                (self.committed_workload_units + self.demand_units) * 10_000
                + self.eligible_supply_units - 1
            ) // self.eligible_supply_units
        )
        if self.projected_utilization_bp != expected_utilization:
            raise ValueError("capacity cell utilization does not reconcile")
        expected_state = (
            "PARTIAL_SUPPLY_EXCLUDED"
            if self.excluded_incomplete_consultant_ids else "COMPLETE"
        )
        if self.supply_state != expected_state:
            raise ValueError("capacity cell supply state does not reconcile")
        return self


class ScenarioEffortChangeV2(StrictContract):
    deal_source_id: Identifier
    region_id: Literal["EMEA"]
    base_effort_units: int = Field(ge=0)
    scenario_effort_units: int = Field(ge=0)
    changed_field: Literal["effort_units"]
    multiplier: Literal["1.25"]
    rounding: Literal["CEILING_TO_CAPACITY_UNIT"]

    @model_validator(mode="after")
    def exact_scenario_math(self) -> "ScenarioEffortChangeV2":
        expected = int(
            (Decimal(self.base_effort_units) * Decimal("1.25")).quantize(
                Decimal("1"), rounding=ROUND_CEILING
            )
        )
        if self.scenario_effort_units != expected:
            raise ValueError("scenario effort must be the exact bounded ceiling result")
        return self


class ScenarioComparisonV2(ReceiptContextV2):
    schema_version: Literal["orchestrator.scenario-comparison.v2"]
    scenario_comparison_id: Identifier
    scenario_id: Literal["EMEA_EFFORT_PLUS_25_PERCENT"]
    label: Literal["USER_SELECTED_ASSUMPTION_NOT_A_FORECAST"]
    advanced_policy_confirmation_id: Identifier
    changes: tuple[ScenarioEffortChangeV2, ...]
    base_cells: tuple[CapacityCellV2, ...]
    scenario_cells: tuple[CapacityCellV2, ...]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def scenario_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def scenario_changes_only_demand_math(self) -> "ScenarioComparisonV2":
        def keyed(cells: tuple[CapacityCellV2, ...]) -> dict[tuple[str, str, int], CapacityCellV2]:
            result = {(cell.region_id, cell.skill_id, cell.week_bucket): cell for cell in cells}
            if len(result) != len(cells):
                raise ValueError("scenario capacity cells must be unique")
            return result

        base = keyed(self.base_cells)
        scenario = keyed(self.scenario_cells)
        if set(base) != set(scenario):
            raise ValueError("scenario cannot add or remove capacity groups")
        for key in base:
            before = base[key]
            after = scenario[key]
            unchanged = (
                "eligible_supply_units", "committed_workload_units", "free_units",
                "excluded_incomplete_consultant_ids", "supply_state", "skill_rows_additive",
            )
            if any(getattr(before, field) != getattr(after, field) for field in unchanged):
                raise ValueError("scenario changed a field outside EMEA effort demand")
            if before.region_id != "EMEA" and before != after:
                raise ValueError("scenario changed a non-EMEA cell")
        return self


class DigestFactV2(StrictContract):
    fact_id: Identifier
    source_artifact_id: Identifier
    statement: str = Field(min_length=1, max_length=500)


class LeadershipDigestV2(ReceiptContextV2):
    schema_version: Literal["orchestrator.leadership-digest.v2"]
    digest_id: Identifier
    generation_mode: Literal["DETERMINISTIC_FACT_BOUND"]
    facts: tuple[DigestFactV2, ...]
    recommendation_only: Literal[True]
    production_readiness: Literal["NOT_ASSESSED"]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def digest_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)
