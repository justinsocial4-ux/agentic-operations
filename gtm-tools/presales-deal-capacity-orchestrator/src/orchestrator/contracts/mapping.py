from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from .base import Identifier, Sha256, StrictContract, require_offset_aware


class CrosswalkEntryV1(StrictContract):
    source_value: str = Field(min_length=1, max_length=256)
    canonical_value: str = Field(min_length=1, max_length=256)


class MappingRuleV1(StrictContract):
    rule_id: Identifier
    source_field_id: str = Field(min_length=1, max_length=256)
    canonical_target_field: str = Field(min_length=1, max_length=256)
    conversion_id: Literal[
        "IDENTITY", "TRIM", "ENUM_CROSSWALK", "ISO_TIMESTAMP",
        "EPOCH_MS_TIMESTAMP", "DECIMAL_CURRENCY", "EFFORT_MINUTES_TO_UNITS",
        "BOOLEAN", "LIST_SPLIT", "EXACT_ID_CROSSWALK",
    ]
    required: bool
    crosswalk: tuple[CrosswalkEntryV1, ...] = ()
    list_delimiter: str | None = Field(default=None, min_length=1, max_length=8)

    @field_validator("crosswalk")
    @classmethod
    def unique_crosswalk(cls, value: tuple[CrosswalkEntryV1, ...]) -> tuple[CrosswalkEntryV1, ...]:
        keys = [entry.source_value for entry in value]
        if len(keys) != len(set(keys)):
            raise ValueError("crosswalk source values must be unique")
        return value


class MappingProfileV1(StrictContract):
    schema_version: Literal["orchestrator.mapping-profile.v1"]
    profile_id: Identifier
    adapter_source_format_id: Identifier
    adapter_source_format_version: str
    source_instance_id: Identifier
    object_kind: Identifier
    rules: tuple[MappingRuleV1, ...]
    null_tokens: tuple[str, ...]
    timezone: str | None
    currency: str | None
    effort_unit: Literal["MINUTES", "THIRTY_MINUTE_UNITS"] | None
    source_population_predicate_sha256: Sha256
    owner_role: str = Field(min_length=1, max_length=80)
    reviewer_role: str = Field(min_length=1, max_length=80)
    accepted_at: datetime
    canonical_profile_sha256: Sha256

    @field_validator("accepted_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @field_validator("rules")
    @classmethod
    def unique_rules(cls, value: tuple[MappingRuleV1, ...]) -> tuple[MappingRuleV1, ...]:
        source_ids = [rule.source_field_id for rule in value]
        targets = [rule.canonical_target_field for rule in value]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source fields may be mapped only once per object profile")
        if len(targets) != len(set(targets)):
            raise ValueError("canonical target fields may be mapped only once")
        return value
