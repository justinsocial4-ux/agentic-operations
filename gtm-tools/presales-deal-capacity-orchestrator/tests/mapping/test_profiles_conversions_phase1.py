from __future__ import annotations

from datetime import datetime, timezone

import pytest

from orchestrator.contracts.mapping import CrosswalkEntryV1, MappingProfileV1, MappingRuleV1
from orchestrator.mapping.conversions import ConversionError, convert_value
from orchestrator.mapping.profiles import MappingError, apply_mapping_profile, mapping_profile_payload_hash, scan_mapping_profile


def make_profile(**updates: object) -> MappingProfileV1:
    payload: dict[str, object] = {
        "schema_version": "orchestrator.mapping-profile.v1",
        "profile_id": "profile-1",
        "adapter_source_format_id": "csv-v1",
        "adapter_source_format_version": "1",
        "source_instance_id": "source-1",
        "object_kind": "DEAL_WORK_REQUEST",
        "rules": (
            MappingRuleV1(rule_id="id", source_field_id="deal", canonical_target_field="deal_source_id", conversion_id="IDENTITY", required=True),
        ),
        "null_tokens": ("", "NULL"),
        "timezone": "America/New_York",
        "currency": "USD",
        "effort_unit": "MINUTES",
        "source_population_predicate_sha256": "b" * 64,
        "owner_role": "data-owner",
        "reviewer_role": "manager",
        "accepted_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    payload.update(updates)
    payload["canonical_profile_sha256"] = mapping_profile_payload_hash(payload)
    return MappingProfileV1.model_validate(payload)


def test_scenario_f_unknown_custom_schema_remains_unmapped() -> None:
    profile = make_profile()
    result = apply_mapping_profile(
        ({"deal": "deal-1", "SE Need": "security", "Bench": "maybe", "Hero": "someone"},),
        profile,
        available_field_ids=("deal", "SE Need", "Bench", "Hero"),
    )
    assert result.accepted == ({"deal_source_id": "deal-1"},)
    assert result.unmapped_source_field_ids == ("Bench", "Hero", "SE Need")


def test_mapping_profile_no_value_no_secret_scan() -> None:
    scan_mapping_profile(make_profile())
    with pytest.raises(MappingError, match="private"):
        scan_mapping_profile(make_profile(owner_role="person@example.test"))
    with pytest.raises(MappingError, match="hash"):
        bad = make_profile().model_copy(update={"canonical_profile_sha256": "c" * 64})
        scan_mapping_profile(bad)


def test_closed_conversions_and_no_silent_rounding() -> None:
    crosswalk = MappingRuleV1(
        rule_id="region", source_field_id="region", canonical_target_field="region_id",
        conversion_id="ENUM_CROSSWALK", required=True,
        crosswalk=(CrosswalkEntryV1(source_value="Europe", canonical_value="EMEA"),),
    )
    assert convert_value("Europe", crosswalk) == "EMEA"
    with pytest.raises(ConversionError, match="crosswalk"):
        convert_value("Unknown", crosswalk)
    effort = MappingRuleV1(
        rule_id="effort", source_field_id="minutes", canonical_target_field="effort_units",
        conversion_id="EFFORT_MINUTES_TO_UNITS", required=True,
    )
    assert convert_value("90", effort) == 3
    with pytest.raises(ConversionError, match="30-minute"):
        convert_value("45", effort)
    timestamp = MappingRuleV1(
        rule_id="time", source_field_id="time", canonical_target_field="time",
        conversion_id="ISO_TIMESTAMP", required=True,
    )
    with pytest.raises(ConversionError, match="offset"):
        convert_value("2026-01-01T12:00:00", timestamp)
