from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .base import Identifier, Sha256, StrictContract, require_offset_aware


class ConnectorPreflightReceiptV1(StrictContract):
    schema_version: Literal["orchestrator.connector-preflight.v1"]
    adapter_id: Identifier
    source_instance_id: Identifier
    source_identity_fingerprint: Sha256
    auth_mode: str
    permitted_operation_ids: tuple[Identifier, ...]
    credential_persisted: Literal[False] = False
    external_write_attempted: Literal[False] = False


class SourceFieldMetadataV1(StrictContract):
    field_id: str = Field(min_length=1)
    label: str | None = None
    source_type: str
    custom: bool


class SourceSchemaMetadataV1(StrictContract):
    schema_version: Literal["orchestrator.source-schema-metadata.v1"]
    adapter_id: Identifier
    object_kind: str
    fields: tuple[SourceFieldMetadataV1, ...]
    schema_sha256: Sha256
    mapping_accepted: Literal[False] = False


class RateLimitObservationV1(StrictContract):
    limit: int | None = Field(default=None, ge=0)
    remaining: int | None = Field(default=None, ge=0)
    reset: int | None = Field(default=None, ge=0)
    raw_sforce_limit_info: str | None = None


class ConnectorPageV1(StrictContract):
    schema_version: Literal["orchestrator.connector-page.v1"]
    adapter_id: Identifier
    object_kind: str
    records: tuple[dict[str, Any], ...]
    page_number: int = Field(ge=0)
    next_cursor: str | None = None
    cursor_sha256: Sha256 | None = None
    response_sha256: Sha256
    high_water_mark: datetime | None = None
    complete: bool
    completeness: Literal["COMPLETE", "BOUNDED_PARTIAL"]
    warnings: tuple[str, ...] = ()
    rate_limit: RateLimitObservationV1 | None = None

    @field_validator("high_water_mark")
    @classmethod
    def high_water_is_aware(cls, value: datetime | None) -> datetime | None:
        return require_offset_aware(value) if value is not None else None

    @model_validator(mode="after")
    def cursor_is_hash_bound(self) -> "ConnectorPageV1":
        if (self.next_cursor is None) != (self.cursor_sha256 is None):
            raise ValueError("an in-memory cursor must have a receipt hash")
        if self.complete != (self.completeness == "COMPLETE"):
            raise ValueError("complete and completeness disagree")
        return self

    def durable_checkpoint_projection(self) -> dict[str, Any]:
        """Deliberately excludes the opaque vendor cursor value."""
        return {
            "page_number": self.page_number,
            "cursor_sha256": self.cursor_sha256,
            "high_water_mark": self.high_water_mark,
            "completeness": self.completeness,
        }


class DeletionReceiptV1(StrictContract):
    schema_version: Literal["orchestrator.deletion-receipt.v1"]
    deletion_receipt_id: Identifier
    adapter_id: Identifier
    source_instance_id: Identifier
    object_kind: str
    window_begin: datetime
    window_end: datetime
    deleted_source_record_ids: tuple[str, ...]
    feed_complete: bool
    deletion_state: Literal["DELETIONS_CONFIRMED", "DELETION_UNKNOWN"]
    response_sha256: Sha256
    historical_receipt_preserved: Literal[True] = True

    @field_validator("window_begin", "window_end")
    @classmethod
    def deletion_times_are_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def validate_deletion_state(self) -> "DeletionReceiptV1":
        if self.window_begin >= self.window_end:
            raise ValueError("deletion window must be increasing")
        expected = "DELETIONS_CONFIRMED" if self.feed_complete else "DELETION_UNKNOWN"
        if self.deletion_state != expected:
            raise ValueError("deletion state must reflect feed completeness")
        return self
