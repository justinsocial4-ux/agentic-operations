from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .base import ExactDecimalString, Identifier, Sha256, StrictContract, require_offset_aware
from .policy import BasisPoints, DimensionId


class ReceiptContextV2(StrictContract):
    run_id: Identifier
    policy_sha256: Sha256
    source_manifest_ids: tuple[Identifier, ...] = Field(min_length=1)
    mapping_profile_sha256s: tuple[Sha256, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def frozen_context_is_unique(self) -> "ReceiptContextV2":
        if len(self.source_manifest_ids) != len(set(self.source_manifest_ids)):
            raise ValueError("receipt source manifests must be unique")
        if len(self.mapping_profile_sha256s) != len(set(self.mapping_profile_sha256s)):
            raise ValueError("receipt mapping hashes must be unique")
        return self


class ExactEvidenceCitationV2(StrictContract):
    """Validated citation metadata only; quote text is intentionally absent."""

    citation_id: Identifier
    source_record_id: Identifier
    conversation_id: Identifier | None = None
    segment_id: Identifier | None = None
    excerpt_sha256: Sha256
    char_begin: int = Field(ge=0)
    char_end: int = Field(gt=0)
    relative_begin_ms: int | None = Field(default=None, ge=0)
    exact_match_validated: Literal[True]

    @model_validator(mode="after")
    def ordered_offsets(self) -> "ExactEvidenceCitationV2":
        if self.char_begin >= self.char_end:
            raise ValueError("citation offsets must select non-empty exact evidence")
        return self


class ReadinessEvidenceV2(StrictContract):
    """Input to deterministic readiness after source/quote validation."""

    dimension_id: DimensionId
    state: Literal["SUPPORTED", "UNKNOWN", "CONFLICT"]
    provenance: Literal["STRUCTURED", "TRANSCRIPT"]
    citations: tuple[ExactEvidenceCitationV2, ...]
    incompatibility_receipt_id: Identifier | None = None

    @model_validator(mode="after")
    def enforce_state_evidence(self) -> "ReadinessEvidenceV2":
        if self.state == "SUPPORTED" and len(self.citations) < 1:
            raise ValueError("SUPPORTED requires at least one exact validated citation")
        if self.state == "CONFLICT":
            if len(self.citations) < 2 or len({item.citation_id for item in self.citations}) < 2:
                raise ValueError("CONFLICT requires at least two distinct exact validated citations")
            if self.incompatibility_receipt_id is None:
                raise ValueError("CONFLICT requires an incompatibility receipt")
        if self.state == "UNKNOWN" and (self.citations or self.incompatibility_receipt_id is not None):
            raise ValueError("UNKNOWN has no citation and is not an absence assertion")
        return self


class ReadinessDimensionReceiptV2(StrictContract):
    dimension_id: DimensionId
    state: Literal["SUPPORTED", "UNKNOWN", "CONFLICT"]
    citation_ids: tuple[Identifier, ...]
    citation_sha256s: tuple[Sha256, ...]
    provenance: tuple[Literal["STRUCTURED", "TRANSCRIPT"], ...]
    incompatibility_receipt_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def receipt_cardinality(self) -> "ReadinessDimensionReceiptV2":
        if len(self.citation_ids) != len(self.citation_sha256s):
            raise ValueError("citation IDs and hashes must reconcile")
        if self.state == "SUPPORTED" and not self.citation_ids:
            raise ValueError("SUPPORTED receipt requires an exact citation")
        if self.state == "CONFLICT" and (len(self.citation_ids) < 2 or not self.incompatibility_receipt_ids):
            raise ValueError("CONFLICT receipt requires incompatible exact citations")
        if self.state == "UNKNOWN" and (
            self.citation_ids or self.citation_sha256s or self.provenance or self.incompatibility_receipt_ids
        ):
            raise ValueError("UNKNOWN receipt must contain no evidence")
        return self


class ReadinessReceiptV2(ReceiptContextV2):
    schema_version: Literal["orchestrator.readiness-receipt.v2"]
    readiness_receipt_id: Identifier
    deal_source_id: Identifier
    request_type: Identifier
    dimensions: tuple[ReadinessDimensionReceiptV2, ...] = Field(min_length=1)
    required_dimension_ids: tuple[DimensionId, ...]
    queue_lane: Literal[
        "ASSIGNMENT_ELIGIBLE", "DEAL_INSPECTION", "ANALYSIS_BLOCKED",
        "OUT_OF_HORIZON", "INPUT_BLOCKED", "SOURCE_PARTIAL",
    ]
    reason_codes: tuple[Identifier, ...]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def dimensions_reconcile(self) -> "ReadinessReceiptV2":
        dimension_ids = tuple(item.dimension_id for item in self.dimensions)
        if len(dimension_ids) != len(set(dimension_ids)):
            raise ValueError("readiness dimensions must be unique")
        if not set(self.required_dimension_ids).issubset(dimension_ids):
            raise ValueError("required readiness dimensions must be present")
        return self


class PriorityFeatureV2(StrictContract):
    feature_id: Literal["MILESTONE_URGENCY", "READINESS_EVIDENCE", "COMMERCIAL_VALUE"]
    feature_bp: BasisPoints
    weight_bp: BasisPoints
    weighted_numerator: int = Field(ge=0, le=100_000_000)


class PriorityReceiptV2(ReceiptContextV2):
    schema_version: Literal["orchestrator.priority-receipt.v2"]
    priority_receipt_id: Identifier
    deal_source_id: Identifier
    readiness_receipt_id: Identifier
    due_week_bucket: Literal[1, 2, 3, 4]
    commercial_amount_used: ExactDecimalString
    commercial_currency: str = Field(pattern=r"^[A-Z]{3}$")
    commercial_basis_id: Identifier
    normalization_approval_receipt_id: Identifier | None = None
    features: tuple[PriorityFeatureV2, PriorityFeatureV2, PriorityFeatureV2]
    priority_bp: BasisPoints
    rounding: Literal["ROUND_HALF_EVEN"]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def priority_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def exact_feature_set(self) -> "PriorityReceiptV2":
        expected = ("MILESTONE_URGENCY", "READINESS_EVIDENCE", "COMMERCIAL_VALUE")
        if tuple(item.feature_id for item in self.features) != expected:
            raise ValueError("priority receipt must carry the three ordered policy features exactly once")
        return self


class PriorityBlockedReceiptV2(StrictContract):
    schema_version: Literal["orchestrator.priority-blocked-receipt.v2"]
    run_id: Identifier
    deal_source_id: Identifier
    queue_lane: Literal["INPUT_BLOCKED"]
    reason_code: Literal["CURRENCY_BASIS_MISMATCH"]
    priority_receipt_issued: Literal[False]


class WeeklyCapacityBucketV1(StrictContract):
    week_bucket: Literal[1, 2, 3, 4]
    scheduled_units: int = Field(ge=0)
    time_off_units: int = Field(ge=0)
    active_workload_units: int = Field(ge=0)
    free_units: int | None = Field(default=None, ge=0)
    completeness_state: Literal["COMPLETE", "INCOMPLETE", "CONFLICT"]

    @model_validator(mode="after")
    def complete_arithmetic(self) -> "WeeklyCapacityBucketV1":
        expected = self.scheduled_units - self.time_off_units - self.active_workload_units
        if self.completeness_state == "COMPLETE" and (expected < 0 or self.free_units != expected):
            raise ValueError("complete capacity bucket arithmetic does not reconcile")
        if self.completeness_state != "COMPLETE" and self.free_units is not None:
            raise ValueError("incomplete/conflicting capacity cannot expose free units")
        return self


class WeeklyCapacityReceiptV1(ReceiptContextV2):
    schema_version: Literal["orchestrator.weekly-capacity-receipt.v1"]
    capacity_receipt_id: Identifier
    consultant_source_id: Identifier
    capacity_unit_minutes: Literal[30]
    horizon_weeks: Literal[4]
    buckets: tuple[
        WeeklyCapacityBucketV1, WeeklyCapacityBucketV1,
        WeeklyCapacityBucketV1, WeeklyCapacityBucketV1,
    ]
    complete_through_bucket: int = Field(ge=0, le=4)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def capacity_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def literal_bucket_set(self) -> "WeeklyCapacityReceiptV1":
        if tuple(item.week_bucket for item in self.buckets) != (1, 2, 3, 4):
            raise ValueError("capacity horizon must contain ordered buckets 1..4 exactly once")
        return self


class EligibilityCheckV2(StrictContract):
    check_id: Literal[
        "DEAL_LANE", "ACTIVE_STATUS", "REGION", "SKILLS", "LANGUAGE", "TIME_ZONE",
        "WORKING_WINDOW", "CAPACITY_COMPLETE", "CUMULATIVE_CAPACITY", "UTILIZATION",
        "FROZEN_RECEIPTS",
    ]
    passed: bool
    reason_code: Identifier | None = None


class EligibilityReceiptV2(ReceiptContextV2):
    schema_version: Literal["orchestrator.eligibility-receipt.v2"]
    eligibility_receipt_id: Identifier
    deal_source_id: Identifier
    consultant_source_id: Identifier
    priority_receipt_id: Identifier
    capacity_receipt_id: Identifier
    due_week_bucket: Literal[1, 2, 3, 4]
    checks: tuple[EligibilityCheckV2, ...]
    eligible: bool
    reason_codes: tuple[Identifier, ...]
    actual_working_window_minutes: int = Field(ge=0, le=1440)
    projected_utilization_bp: int | None = Field(default=None, ge=0)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def eligibility_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def checks_reconcile(self) -> "EligibilityReceiptV2":
        expected = (
            "DEAL_LANE", "ACTIVE_STATUS", "REGION", "SKILLS", "LANGUAGE", "TIME_ZONE",
            "WORKING_WINDOW", "CAPACITY_COMPLETE", "CUMULATIVE_CAPACITY", "UTILIZATION",
            "FROZEN_RECEIPTS",
        )
        if tuple(item.check_id for item in self.checks) != expected:
            raise ValueError("eligibility receipt must carry every ordered hard check exactly once")
        if self.eligible != all(item.passed for item in self.checks):
            raise ValueError("eligibility must equal the conjunction of hard checks")
        failed = tuple(item.reason_code for item in self.checks if not item.passed)
        if self.reason_codes != tuple(code for code in failed if code is not None):
            raise ValueError("eligibility reason codes do not reconcile")
        return self


class MatchComponentV2(StrictContract):
    component_id: Literal["SKILL_SURPLUS", "CONTINUITY", "OVERLAP_SURPLUS", "CAPACITY_HEADROOM"]
    component_bp: BasisPoints
    weight_bp: BasisPoints
    weighted_numerator: int = Field(ge=0, le=100_000_000)


class ConsultantFitReceiptV2(ReceiptContextV2):
    schema_version: Literal["orchestrator.consultant-fit-receipt.v2"]
    fit_receipt_id: Identifier
    deal_source_id: Identifier
    consultant_source_id: Identifier
    eligibility_receipt_id: Identifier
    priority_receipt_id: Identifier
    components: tuple[MatchComponentV2, MatchComponentV2, MatchComponentV2, MatchComponentV2]
    fit_bp: BasisPoints
    rounding: Literal["ROUND_HALF_EVEN"]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def fit_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def exact_component_set(self) -> "ConsultantFitReceiptV2":
        expected = ("SKILL_SURPLUS", "CONTINUITY", "OVERLAP_SURPLUS", "CAPACITY_HEADROOM")
        if tuple(item.component_id for item in self.components) != expected:
            raise ValueError("fit receipt must carry the four ordered match components exactly once")
        return self
