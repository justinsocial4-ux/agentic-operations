from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from orchestrator.canonical import canonical_sha256
from orchestrator.contracts.mapping import MappingProfileV1, MappingRuleV1

from .conversions import ConversionError, convert_value

_SECRET_KEY = re.compile(r"(?:password|secret|token|authorization|cookie|api[_-]?key|credential)", re.I)
_PRIVATE_VALUE = re.compile(r"(?:[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|-----BEGIN [A-Z ]+PRIVATE KEY-----|\bBearer\s+\S+|\bsk-[A-Za-z0-9]{12,})", re.I)
_FORBIDDEN_VALUE_KEYS = frozenset({"sample", "sample_value", "example", "transcript", "text", "quote", "name", "email"})


class MappingError(ValueError):
    pass


@dataclass(frozen=True)
class MappingIssue:
    row_number: int
    target_field: str
    reason_code: str


@dataclass(frozen=True)
class MappedRows:
    accepted: tuple[dict[str, Any], ...]
    accepted_row_numbers: tuple[int, ...]
    quarantined_row_numbers: tuple[int, ...]
    issues: tuple[MappingIssue, ...]
    unmapped_source_field_ids: tuple[str, ...]


def mapping_profile_payload_hash(profile: MappingProfileV1 | Mapping[str, Any]) -> str:
    if isinstance(profile, MappingProfileV1):
        payload = profile.model_dump(mode="json", exclude={"canonical_profile_sha256"})
    else:
        candidate = dict(profile)
        candidate["canonical_profile_sha256"] = "0" * 64
        normalized = MappingProfileV1.model_validate(candidate)
        payload = normalized.model_dump(mode="json", exclude={"canonical_profile_sha256"})
    return canonical_sha256(payload)


def scan_mapping_profile(profile: MappingProfileV1) -> None:
    """Reject value-bearing/private/secret material while allowing explicit ID crosswalks."""
    payload = profile.model_dump(mode="json")

    def walk(value: Any, key: str = "") -> None:
        lowered = key.lower()
        if (lowered != "null_tokens" and _SECRET_KEY.search(lowered)) or lowered in _FORBIDDEN_VALUE_KEYS:
            raise MappingError("mapping profile contains a forbidden value/secret field")
        if isinstance(value, str) and _PRIVATE_VALUE.search(value):
            raise MappingError("mapping profile contains private or secret-looking content")
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(child, str(child_key))
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child, key)

    walk(payload)
    if profile.canonical_profile_sha256 != mapping_profile_payload_hash(profile):
        raise MappingError("mapping profile hash does not match its credential-free payload")


def apply_mapping_profile(
    rows: tuple[dict[str, Any], ...],
    profile: MappingProfileV1,
    *,
    available_field_ids: tuple[str, ...],
) -> MappedRows:
    scan_mapping_profile(profile)
    available = set(available_field_ids)
    missing_required_mappings = sorted(
        rule.source_field_id for rule in profile.rules if rule.required and rule.source_field_id not in available
    )
    if missing_required_mappings:
        raise MappingError("required source field mapping is absent")

    null_tokens = set(profile.null_tokens)
    accepted: list[dict[str, Any]] = []
    accepted_row_numbers: list[int] = []
    quarantined: list[int] = []
    issues: list[MappingIssue] = []
    mapped_sources = {rule.source_field_id for rule in profile.rules}
    for row_number, row in enumerate(rows, start=1):
        output: dict[str, Any] = {}
        row_failed = False
        for rule in profile.rules:
            if rule.source_field_id not in row or (
                isinstance(row.get(rule.source_field_id), str) and row.get(rule.source_field_id) in null_tokens
            ) or row.get(rule.source_field_id) is None:
                if rule.required:
                    issues.append(MappingIssue(row_number, rule.canonical_target_field, "REQUIRED_VALUE_MISSING"))
                    row_failed = True
                continue
            try:
                output[rule.canonical_target_field] = convert_value(row[rule.source_field_id], rule)
            except ConversionError:
                issues.append(MappingIssue(row_number, rule.canonical_target_field, "CONVERSION_REJECTED"))
                row_failed = True
        if row_failed:
            quarantined.append(row_number)
        else:
            accepted.append(output)
            accepted_row_numbers.append(row_number)
    return MappedRows(
        accepted=tuple(accepted),
        accepted_row_numbers=tuple(accepted_row_numbers),
        quarantined_row_numbers=tuple(quarantined),
        issues=tuple(issues),
        unmapped_source_field_ids=tuple(sorted(available - mapped_sources)),
    )


def rule_by_target(profile: MappingProfileV1) -> dict[str, MappingRuleV1]:
    return {rule.canonical_target_field: rule for rule in profile.rules}
