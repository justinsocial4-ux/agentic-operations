from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from .base import CurrencyCode, ExactDecimalString, Identifier, StrictContract

DimensionId = Literal[
    "business-problem",
    "buyer-outcome",
    "technical-scope",
    "stakeholder-role-coverage",
    "success-criteria",
    "security-or-data-requirements",
    "evaluation-plan",
    "customer-owner-and-next-step",
    "milestone-date",
]
BasisPoints = Annotated[int, Field(ge=0, le=10_000)]
IanaTimezone = Annotated[str, StringConstraints(min_length=3, max_length=64, pattern=r"^[A-Za-z_]+(?:/[A-Za-z0-9_+.-]+)+$")]


class PriorityWeightsV1(StrictContract):
    milestone_urgency: BasisPoints
    readiness_evidence: BasisPoints
    commercial_value: BasisPoints

    @model_validator(mode="after")
    def sum_to_one(self) -> "PriorityWeightsV1":
        if self.milestone_urgency + self.readiness_evidence + self.commercial_value != 10_000:
            raise ValueError("priority weights must sum to 10000 basis points")
        return self


class WeightRangeV1(StrictContract):
    minimum_bp: BasisPoints
    maximum_bp: BasisPoints

    @model_validator(mode="after")
    def ordered(self) -> "WeightRangeV1":
        if self.minimum_bp > self.maximum_bp:
            raise ValueError("weight minimum must not exceed maximum")
        return self


class PriorityWeightBoundsV1(StrictContract):
    milestone_urgency: WeightRangeV1
    readiness_evidence: WeightRangeV1
    commercial_value: WeightRangeV1


class UrgencyBreakpointV1(StrictContract):
    latest_days_until_due: int = Field(ge=0, le=28)
    feature_bp: BasisPoints


class CommercialCurrencyBasisV1(StrictContract):
    currency: CurrencyCode
    basis_id: Identifier


class SkillCatalogEntryV1(StrictContract):
    skill_id: Identifier
    label: str = Field(min_length=1, max_length=80)
    minimum_level: int = Field(ge=0, le=4)


class MatchComponentWeightsV1(StrictContract):
    skill_surplus: BasisPoints
    continuity: BasisPoints
    overlap_surplus: BasisPoints
    capacity_headroom: BasisPoints

    @model_validator(mode="after")
    def sum_to_one(self) -> "MatchComponentWeightsV1":
        if sum((self.skill_surplus, self.continuity, self.overlap_surplus, self.capacity_headroom)) != 10_000:
            raise ValueError("match component weights must sum to 10000 basis points")
        return self


class SolverConfigV1(StrictContract):
    worker_count: Literal[1]
    random_seed: int = Field(ge=0)
    phase_limit_seconds: int = Field(ge=1, le=30)
    release_requires_optimal: Literal[True]


class ScenarioBoundariesV1(StrictContract):
    region_id: Literal["EMEA"]
    effort_multiplier: Literal["1.25"]
    rounding: Literal["CEILING_TO_CAPACITY_UNIT"]


class PolicyV2(StrictContract):
    schema_version: Literal["orchestrator.policy.v2"]
    horizon_weeks: Literal[4]
    readiness_dimensions: tuple[DimensionId, ...]
    required_readiness_subsets_by_request_type: dict[str, tuple[DimensionId, ...]]
    priority_weights_bp: PriorityWeightsV1
    priority_weight_bounds: PriorityWeightBoundsV1
    urgency_breakpoints: tuple[UrgencyBreakpointV1, ...]
    commercial_value_floor: ExactDecimalString
    commercial_value_cap: ExactDecimalString
    commercial_currency_basis: CommercialCurrencyBasisV1
    skill_catalog: tuple[SkillCatalogEntryV1, ...]
    capacity_unit_minutes: Literal[30]
    capacity_completeness_window: Literal["THROUGH_MILESTONE", "FOUR_WEEK_HORIZON"]
    utilization_ceiling: BasisPoints
    minimum_working_window_overlap: int = Field(ge=0, le=1440)
    match_component_weights_bp: MatchComponentWeightsV1
    solver_config: SolverConfigV1
    scenario_boundaries: ScenarioBoundariesV1
    prohibited_inputs: tuple[str, ...]
    prohibited_outputs: tuple[str, ...]
    export_boundary: Literal["INERT_RECOMMENDATION_ONLY"]

    @model_validator(mode="after")
    def validate_policy_bounds(self) -> "PolicyV2":
        from decimal import Decimal

        if Decimal(self.commercial_value_floor) >= Decimal(self.commercial_value_cap):
            raise ValueError("commercial value floor must be below cap")
        if len(self.readiness_dimensions) != len(set(self.readiness_dimensions)):
            raise ValueError("readiness dimensions must be unique")
        allowed = set(self.readiness_dimensions)
        if any(not set(required).issubset(allowed) for required in self.required_readiness_subsets_by_request_type.values()):
            raise ValueError("required readiness subsets must be selected dimensions")
        weight_values = self.priority_weights_bp
        ranges = self.priority_weight_bounds
        for value, bounds in (
            (weight_values.milestone_urgency, ranges.milestone_urgency),
            (weight_values.readiness_evidence, ranges.readiness_evidence),
            (weight_values.commercial_value, ranges.commercial_value),
        ):
            if not bounds.minimum_bp <= value <= bounds.maximum_bp:
                raise ValueError("priority weight is outside approved bounds")
        required_prohibited_inputs = {
            "individual_win_rate", "protected_traits", "transcript_text_for_consultant_fit",
            "transcript_derived_manager_tags",
        }
        required_prohibited_outputs = {
            "automatic_assignment", "employment_decision", "source_system_write",
            "sentiment_or_performance_inference",
        }
        if not required_prohibited_inputs.issubset(self.prohibited_inputs):
            raise ValueError("policy cannot loosen non-negotiable prohibited inputs")
        if not required_prohibited_outputs.issubset(self.prohibited_outputs):
            raise ValueError("policy cannot loosen non-negotiable prohibited outputs")
        return self
