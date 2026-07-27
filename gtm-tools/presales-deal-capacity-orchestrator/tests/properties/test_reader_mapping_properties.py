from __future__ import annotations

import csv
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from hypothesis import given, strategies as st

from orchestrator.contracts.mapping import MappingProfileV1, MappingRuleV1
from orchestrator.ingestion.file_readers import read_csv_file, read_json_file
from orchestrator.mapping.profiles import apply_mapping_profile, mapping_profile_payload_hash

SAFE_TEXT = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=0,
    max_size=30,
)


def profile(source_instance_id: str = "source-1") -> MappingProfileV1:
    payload = {
        "schema_version": "orchestrator.mapping-profile.v1",
        "profile_id": "profile-1",
        "adapter_source_format_id": "csv-v1",
        "adapter_source_format_version": "1",
        "source_instance_id": source_instance_id,
        "object_kind": "TEST_RECORD",
        "rules": (
            MappingRuleV1(rule_id="rule-id", source_field_id="id", canonical_target_field="record_id", conversion_id="TRIM", required=True),
            MappingRuleV1(rule_id="rule-value", source_field_id="value", canonical_target_field="value", conversion_id="IDENTITY", required=False),
        ),
        "null_tokens": ("NULL",),
        "timezone": "UTC",
        "currency": None,
        "effort_unit": None,
        "source_population_predicate_sha256": "a" * 64,
        "owner_role": "data-owner",
        "reviewer_role": "manager",
        "accepted_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    payload["canonical_profile_sha256"] = mapping_profile_payload_hash(payload)
    return MappingProfileV1.model_validate(payload)


@given(st.lists(st.tuples(st.integers(min_value=0, max_value=1_000_000), SAFE_TEXT), min_size=1, max_size=30))
def test_csv_and_json_readers_preserve_same_bounded_rows(rows: list[tuple[int, str]]) -> None:
    objects = [{"id": str(identifier), "value": value} for identifier, value in rows]
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = Path(directory)
        csv_path = tmp_path / "property.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("id", "value"))
            writer.writeheader()
            writer.writerows(objects)
        json_path = tmp_path / "property.json"
        json_path.write_text(json.dumps(objects, ensure_ascii=False), encoding="utf-8")
        csv_result = read_csv_file(csv_path, authorization_attestation_id="att-property")
        json_result = read_json_file(json_path, authorization_attestation_id="att-property")
    assert csv_result.rows == json_result.rows
    assert apply_mapping_profile(csv_result.rows, profile(), available_field_ids=csv_result.field_ids) == apply_mapping_profile(
        json_result.rows, profile(), available_field_ids=json_result.field_ids
    )


@given(st.integers(min_value=0, max_value=1_000_000), SAFE_TEXT)
def test_mapping_is_deterministic_and_never_maps_unknown_headers(identifier: int, value: str) -> None:
    rows = ({"id": f" {identifier} ", "value": value, "SE Need": "x", "Bench": "y", "Hero": "z"},)
    mapped = apply_mapping_profile(rows, profile(), available_field_ids=tuple(rows[0]))
    assert mapped.accepted == ({"record_id": str(identifier), "value": value},)
    assert mapped.unmapped_source_field_ids == ("Bench", "Hero", "SE Need")
