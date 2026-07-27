from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .base import CurrencyCode, ExactDecimalString, Identifier, Sha256, StrictContract, require_offset_aware
from .enums import LaneV1


class CurrencyNormalizationApprovalV1(StrictContract):
    """Source-supplied approval receipt; this app performs no FX conversion."""

    schema_version: Literal["orchestrator.currency-normalization-approval.v1"]
    normalized_amount: ExactDecimalString
    corporate_currency: CurrencyCode
    corporate_basis_id: Identifier
    approval_basis_identifier: Identifier
    approval_receipt_id: Identifier
    mapping_rule_id: Identifier
    source_lineage_receipt_ids: tuple[Identifier, ...] = Field(min_length=1)
    approved_at: datetime

    @field_validator("approved_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        return require_offset_aware(value)


class DealWorkRequestV2(StrictContract):
    schema_version: Literal["orchestrator.deal-work-request.v2"]
    work_request_id: Identifier
    deal_source_id: Identifier
    account_source_id: Identifier | None = None
    region_source_value: str | None = None
    region_id: Identifier | None = None
    pipeline_source_value: str | None = None
    pipeline_id: Identifier | None = None
    stage_source_value: str | None = None
    stage_id: Identifier | None = None
    request_type: Identifier | None = None
    milestone_type: Identifier | None = None
    milestone_due_time: datetime | None = None
    effort_units: int | None = Field(default=None, ge=0)
    commercial_amount: ExactDecimalString | None = None
    commercial_currency: CurrencyCode | None = None
    commercial_basis: Identifier | None = None
    corporate_currency_normalization: CurrencyNormalizationApprovalV1 | None = None
    required_skill_ids: tuple[Identifier, ...] | None = None
    required_languages: tuple[str, ...] | None = None
    required_working_window_overlap_minutes: int | None = Field(default=None, ge=0, le=1440)
    continuity_consultant_id: Identifier | None = None
    structured_evidence_references: tuple[Identifier, ...] | None = None
    conversation_ids: tuple[Identifier, ...] | None = None
    source_freshness: datetime | None = None
    lineage_receipt_ids: tuple[Identifier, ...] | None = None

    @field_validator("milestone_due_time", "source_freshness")
    @classmethod
    def aware_times(cls, value: datetime | None) -> datetime | None:
        return require_offset_aware(value) if value is not None else None

    def validate_for_lane(self, lane: LaneV1) -> "DealWorkRequestV2":
        common = {"milestone_due_time", "source_freshness", "lineage_receipt_ids"}
        priority = common | {
            "request_type",
            "milestone_type",
            "commercial_amount",
            "commercial_currency",
            "commercial_basis",
            "structured_evidence_references",
        }
        assignment = priority | {
            "region_source_value",
            "region_id",
            "effort_units",
            "required_skill_ids",
            "required_languages",
            "required_working_window_overlap_minutes",
        }
        capacity = common | {"region_source_value", "region_id", "effort_units", "required_skill_ids"}
        required = {
            LaneV1.DEAL_PRIORITIZATION: priority,
            LaneV1.ASSIGNMENT_RECOMMENDATION: assignment,
            LaneV1.CAPACITY_HEATMAP: capacity,
        }[lane]
        missing = sorted(field for field in required if getattr(self, field) is None)
        if missing:
            raise ValueError(f"missing required fields for {lane}: {', '.join(missing)}")
        return self


class ConsultantV2(StrictContract):
    schema_version: Literal["orchestrator.consultant.v2"]
    consultant_source_id: Identifier
    active_eligibility: bool
    supported_region_ids: tuple[Identifier, ...]
    time_zone: str | None = None
    working_windows: tuple[str, ...] | None = None
    languages: tuple[str, ...] | None = None
    manager_approved_skill_ids: tuple[Identifier, ...]
    policy_receipt_ids: tuple[Identifier, ...] = Field(min_length=1)

    def validate_for_lane(self, lane: LaneV1) -> "ConsultantV2":
        if lane is LaneV1.DEAL_PRIORITIZATION:
            raise ValueError("consultant population is not consumed by Deal prioritization")
        if lane is LaneV1.ASSIGNMENT_RECOMMENDATION:
            missing = [name for name in ("time_zone", "working_windows", "languages") if getattr(self, name) is None]
            if missing:
                raise ValueError(f"missing Assignment consultant fields: {', '.join(missing)}")
        return self


class CapacityAvailabilityV1(StrictContract):
    schema_version: Literal["orchestrator.capacity-availability.v1"]
    consultant_source_id: Identifier
    week_bucket: int = Field(ge=1, le=4)
    scheduled_units: int = Field(ge=0)
    time_off_reduction_units: int = Field(ge=0)
    source_as_of: datetime
    completeness_state: Literal["COMPLETE", "INCOMPLETE", "CONFLICT"]
    lineage_receipt_ids: tuple[Identifier, ...] = Field(min_length=1)

    @field_validator("source_as_of")
    @classmethod
    def source_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)


class WorkloadCommitmentV1(StrictContract):
    schema_version: Literal["orchestrator.workload-commitment.v1"]
    consultant_source_id: Identifier
    source_work_id: Identifier
    week_bucket: int = Field(ge=1, le=4)
    committed_units: int = Field(ge=0)
    due_time: datetime
    status: Identifier
    lineage_receipt_ids: tuple[Identifier, ...] = Field(min_length=1)

    @field_validator("due_time")
    @classmethod
    def due_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)


class SkillAssertionV1(StrictContract):
    schema_version: Literal["orchestrator.skill-assertion.v1"]
    consultant_source_id: Identifier
    skill_id: Identifier
    level: int = Field(ge=0, le=4)
    policy_owner: str = Field(min_length=1, max_length=80)
    effective_begin: datetime
    effective_end: datetime | None = None
    source_receipt_id: Identifier

    @field_validator("effective_begin", "effective_end")
    @classmethod
    def effective_times_are_aware(cls, value: datetime | None) -> datetime | None:
        return require_offset_aware(value) if value is not None else None

    @model_validator(mode="after")
    def effective_interval_is_ordered(self) -> "SkillAssertionV1":
        if self.effective_end is not None and self.effective_begin >= self.effective_end:
            raise ValueError("skill effective interval is inverted")
        return self


class ConversationOriginV1(StrictContract):
    """Ephemeral cross-route origin key. It exists only in the in-memory transcript
    stage and is never serialized to SQLite, temporary files, logs, backups, exports,
    or crash artifacts. The normalized full-content hash plus source family and native
    call/meeting ID form the exact cross-route deduplication key in section 4.3."""

    schema_version: Literal["orchestrator.conversation-origin.v1"]
    source_family: Literal["FILE_IMPORT", "FATHOM", "GONG"]
    opaque_source_instance: Identifier
    native_call_or_meeting_id: str | None = Field(default=None, max_length=256)
    transcript_content_sha256: Sha256
    deal_source_id: Identifier
    started_at: datetime
    ended_at: datetime

    @field_validator("started_at", "ended_at")
    @classmethod
    def origin_times_are_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def origin_interval_is_ordered(self) -> "ConversationOriginV1":
        if self.started_at > self.ended_at:
            raise ValueError("conversation origin interval is inverted")
        return self

    def crosswalk_key(self) -> tuple[str, str | None, str]:
        return (self.source_family, self.native_call_or_meeting_id, self.transcript_content_sha256)


class ConversationEvidenceMetadataV1(StrictContract):
    schema_version: Literal["orchestrator.conversation-evidence-metadata.v1"]
    conversation_origin_id: Identifier
    source_family: Literal["FILE_IMPORT", "FATHOM", "GONG"]
    native_call_or_meeting_id: str = Field(min_length=1, max_length=256)
    deal_source_id: Identifier
    transcript_content_sha256: Sha256
    started_at: datetime
    ended_at: datetime
    speaker_role_counts: dict[Literal["CUSTOMER", "INTERNAL", "UNKNOWN"], int] | None = None
    cited_excerpt_ids: tuple[Identifier, ...] = ()

    @field_validator("started_at", "ended_at")
    @classmethod
    def metadata_times_are_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def metadata_is_bounded(self) -> "ConversationEvidenceMetadataV1":
        if self.started_at > self.ended_at:
            raise ValueError("conversation interval is inverted")
        if self.speaker_role_counts is not None and any(value < 0 for value in self.speaker_role_counts.values()):
            raise ValueError("speaker role counts cannot be negative")
        return self


class ConversationSegmentV1(StrictContract):
    """Ephemeral only. Persistence code must never accept this model."""

    schema_version: Literal["orchestrator.conversation-segment.v1"]
    conversation_id: Identifier
    deal_source_id: Identifier
    segment_id: Identifier
    speaker_ref: Literal["CUSTOMER", "INTERNAL", "UNKNOWN"]
    speaker_source_label: str | None = Field(default=None, max_length=200)
    occurred_at: datetime
    relative_begin_ms: int = Field(ge=0)
    relative_end_ms: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=262_144)
    source_record_id: Identifier
    text_sha256: Sha256
    lineage_receipt_id: Identifier

    @field_validator("occurred_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def offsets_ordered(self) -> "ConversationSegmentV1":
        if self.relative_begin_ms > self.relative_end_ms:
            raise ValueError("relative segment offsets are inverted")
        if hashlib.sha256(self.text.encode("utf-8")).hexdigest() != self.text_sha256:
            raise ValueError("segment text hash does not match text")
        return self


class AnalystCitationV2(StrictContract):
    conversation_id: Identifier
    segment_id: Identifier
    quote: str = Field(min_length=1, max_length=4096)
    char_begin: int = Field(ge=0)
    char_end: int = Field(ge=0)
    text_sha256: Sha256
    relative_begin_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def offsets_ordered(self) -> "AnalystCitationV2":
        if self.char_begin >= self.char_end:
            raise ValueError("citation offsets must select non-empty text")
        return self


class AnalystObservationV2(StrictContract):
    schema_version: Literal["orchestrator.analyst-observation.v2"]
    run_id: Identifier
    analysis_mode: Literal["LIVE_LOCAL", "RECORDED_ANALYST_REPLAY", "MANUAL_CITATION"]
    input_sha256: Sha256
    deal_source_id: Identifier
    dimension_id: Literal[
        "business-problem", "buyer-outcome", "technical-scope",
        "stakeholder-role-coverage", "success-criteria",
        "security-or-data-requirements", "evaluation-plan",
        "customer-owner-and-next-step", "milestone-date",
    ]
    state: Literal["SUPPORTED", "UNKNOWN", "CONFLICT"]
    citations: tuple[AnalystCitationV2, ...]

    @model_validator(mode="after")
    def citation_cardinality(self) -> "AnalystObservationV2":
        if self.state == "SUPPORTED" and len(self.citations) < 1:
            raise ValueError("SUPPORTED requires a citation")
        if self.state == "CONFLICT" and len(self.citations) < 2:
            raise ValueError("CONFLICT requires at least two citations")
        if self.state == "UNKNOWN" and self.citations:
            raise ValueError("UNKNOWN must not carry citations")
        return self
