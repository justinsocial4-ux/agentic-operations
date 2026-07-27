from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .base import Identifier, Sha256, StrictContract, require_offset_aware
from .enums import DataClassificationV1, SnapshotSemanticsV1, SourceModeV1


class HardBoundsV1(StrictContract):
    max_pages: int = Field(ge=1, le=100)
    max_rows: int = Field(ge=1, le=10_000)
    max_bytes: int = Field(ge=1, le=262_144_000)
    max_seconds: int = Field(ge=1, le=600)


class SourceAuthorityBindingV1(StrictContract):
    source_slot_id: Identifier
    authority_role: Literal[
        "DEALS_PRIMARY",
        "ROSTER_PRIMARY",
        "CAPACITY_PRIMARY",
        "WORKLOAD_PRIMARY",
        "CONVERSATION_ADDITIVE",
    ]
    expected_non_secret_identity_fingerprint: Sha256 | None = None


class SourceManifestV1(StrictContract):
    schema_version: Literal["orchestrator.source-manifest.v1"]
    source_manifest_id: Identifier
    run_id: Identifier
    adapter_id: Identifier
    source_mode: SourceModeV1
    source_instance_id: Identifier
    authorization_attestation_id: Identifier
    data_classification: DataClassificationV1
    snapshot_semantics: SnapshotSemanticsV1
    authority_bindings: tuple[SourceAuthorityBindingV1, ...] = Field(min_length=1)
    requested_objects: tuple[str, ...]
    selected_field_ids: tuple[str, ...]
    window_begin: datetime | None
    window_end: datetime | None
    hard_bounds: HardBoundsV1
    mapping_profile_hash: Sha256 | None
    retention_policy_id: Identifier
    synthetic: bool

    @field_validator("window_begin", "window_end")
    @classmethod
    def timestamps_are_offset_aware(cls, value: datetime | None) -> datetime | None:
        return require_offset_aware(value) if value is not None else None

    @model_validator(mode="after")
    def validate_manifest(self) -> "SourceManifestV1":
        bindings = [(item.source_slot_id, item.authority_role) for item in self.authority_bindings]
        if len(bindings) != len(set(bindings)):
            raise ValueError("duplicate slot/authority binding")
        if self.window_begin and self.window_end and self.window_begin >= self.window_end:
            raise ValueError("window_begin must precede window_end")
        if self.synthetic != (self.data_classification is DataClassificationV1.FICTIONAL):
            raise ValueError("synthetic must match FICTIONAL data classification exactly")
        return self
