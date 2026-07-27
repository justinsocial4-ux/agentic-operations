from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .base import Identifier, Sha256, StrictContract, require_offset_aware
from .policy import DimensionId

AnalysisModeV2 = Literal["LIVE_LOCAL", "RECORDED_ANALYST_REPLAY", "MANUAL_CITATION"]


class AnalystProjectionCitationV2(StrictContract):
    """Durable projection of a validated citation. Quote text is intentionally absent;
    only excerpt ID, quote hash, offsets, and timestamps survive under session-only
    retention. No quote text enters this model or any table built from it."""

    excerpt_id: Identifier
    conversation_id: Identifier
    segment_id: Identifier
    quote_sha256: Sha256
    segment_text_sha256: Sha256
    char_begin: int = Field(ge=0)
    char_end: int = Field(gt=0)
    relative_begin_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def ordered_offsets(self) -> "AnalystProjectionCitationV2":
        if self.char_begin >= self.char_end:
            raise ValueError("projection citation offsets must select non-empty evidence")
        return self


class AnalystObservationProjectionV2(StrictContract):
    """Durable, text-free projection of a validator-proven AnalystObservationV2.

    It carries no consultant ID, employee ID, sentiment, emotion, intent, authority,
    confidence, probability, severity, score, candidate, assignment, performance,
    coaching, action, or authorization field. `extra="forbid"` rejects any such key."""

    schema_version: Literal["orchestrator.analyst-observation-projection.v2"]
    run_id: Identifier
    analysis_mode: AnalysisModeV2
    input_sha256: Sha256
    deal_source_id: Identifier
    dimension_id: DimensionId
    state: Literal["SUPPORTED", "UNKNOWN", "CONFLICT"]
    provenance: Literal["TRANSCRIPT"]
    citations: tuple[AnalystProjectionCitationV2, ...]
    incompatibility_receipt_id: Identifier | None = None
    validated: Literal[True]

    @model_validator(mode="after")
    def projection_cardinality(self) -> "AnalystObservationProjectionV2":
        if self.state == "SUPPORTED" and len(self.citations) < 1:
            raise ValueError("SUPPORTED projection requires a validated citation")
        if self.state == "CONFLICT":
            if len(self.citations) < 2:
                raise ValueError("CONFLICT projection requires at least two validated citations")
            if self.incompatibility_receipt_id is None:
                raise ValueError("CONFLICT projection requires an incompatibility receipt")
        if self.state == "UNKNOWN" and (self.citations or self.incompatibility_receipt_id is not None):
            raise ValueError("UNKNOWN projection carries no citation and is not an absence assertion")
        return self


QuarantineReasonCodeV2 = Literal[
    "MALFORMED_PAYLOAD",
    "UNKNOWN_FIELD",
    "OFF_SCOPE_DIMENSION",
    "DEAL_SCOPE_MISMATCH",
    "CROSS_DEAL_CITATION",
    "UNKNOWN_SEGMENT",
    "QUOTE_OFFSET_MISMATCH",
    "QUOTE_TEXT_MISMATCH",
    "SEGMENT_HASH_MISMATCH",
    "TIMESTAMP_OUT_OF_BOUNDS",
    "MISSING_CITATION",
    "INSUFFICIENT_CONFLICT_CITATIONS",
    "UNKNOWN_WITH_CITATION",
    "DUPLICATE_CITATION",
    "REPAIR_UNAVAILABLE",
]


class QuarantineRecordV2(StrictContract):
    """An isolated failed/invalid observation. It is flagged for manager attention and
    NEVER silently affects readiness or decision outputs. It carries no quote text."""

    schema_version: Literal["orchestrator.analyst-quarantine.v2"]
    run_id: Identifier
    analysis_mode: AnalysisModeV2
    input_sha256: Sha256
    deal_source_id: Identifier
    dimension_id: DimensionId | None = None
    initial_reason_code: QuarantineReasonCodeV2
    repair_attempted: Literal[True]
    repair_reason_code: QuarantineReasonCodeV2
    applied_to_readiness: Literal[False]


class AnalystDigestFactV2(StrictContract):
    """A single validator-proven fact. It states only the dimension state and exact
    citation references. It cannot carry sentiment, intent, authority, performance,
    employee score, or action fields (`extra="forbid"`)."""

    dimension_id: DimensionId
    state: Literal["SUPPORTED", "UNKNOWN", "CONFLICT"]
    provenance: Literal["TRANSCRIPT"]
    citation_excerpt_ids: tuple[Identifier, ...]
    citation_sha256s: tuple[Sha256, ...]
    statement: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def facts_reconcile(self) -> "AnalystDigestFactV2":
        if len(self.citation_excerpt_ids) != len(self.citation_sha256s):
            raise ValueError("citation IDs and hashes must reconcile")
        if self.state == "SUPPORTED" and not self.citation_excerpt_ids:
            raise ValueError("SUPPORTED fact requires a citation reference")
        if self.state == "UNKNOWN" and (self.citation_excerpt_ids or self.citation_sha256s):
            raise ValueError("UNKNOWN fact carries no citation reference")
        return self


class AnalystDigestV2(StrictContract):
    """A fact-bound analyst digest. It states ONLY what the validator proved: exact
    dimension state, citation IDs/hashes, and provenance. It cannot invent context,
    infer sentiment/intent/authority/performance, score employees, or create actions."""

    schema_version: Literal["orchestrator.analyst-digest.v2"]
    digest_id: Identifier
    run_id: Identifier
    deal_source_id: Identifier
    policy_sha256: Sha256
    analysis_mode: AnalysisModeV2
    generation_mode: Literal["VALIDATOR_FACT_BOUND"]
    facts: tuple[AnalystDigestFactV2, ...]
    quarantined_count: int = Field(ge=0)
    recommendation_only: Literal[True]
    production_readiness: Literal["NOT_ASSESSED"]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def digest_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)
