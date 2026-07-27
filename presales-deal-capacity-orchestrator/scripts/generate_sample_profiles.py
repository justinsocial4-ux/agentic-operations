"""Generate credential-free sample mapping profiles for the import path.

These profiles are ready-to-adapt examples that map the checked-in fictional
CSV/JSON import samples (``data/examples/import/``) to canonical fields. They are
hash-bound and contain no values, secrets, or private data: only field names,
conversions, and explicit ID crosswalks. Regenerate with:

    uv run --frozen python scripts/generate_sample_profiles.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.contracts.mapping import CrosswalkEntryV1, MappingProfileV1, MappingRuleV1
from orchestrator.mapping.profiles import mapping_profile_payload_hash, scan_mapping_profile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config" / "mapping_profiles"
ACCEPTED_AT = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
SOURCE_INSTANCE_ID = "src-example-deal-csv"

# Mirrors data/examples/import/deal_priority_v1.csv. The deliberately unknown
# headers (SE Need, Bench, Hero) are intentionally NOT mapped: unknown fields
# are never invented or silently mapped.
DEAL_RULES: tuple[tuple[str, str, str], ...] = (
    ("work_id", "work_request_id", "IDENTITY"),
    ("deal_id", "deal_source_id", "EXACT_ID_CROSSWALK"),
    ("request_type", "request_type", "IDENTITY"),
    ("milestone_type", "milestone_type", "IDENTITY"),
    ("due_at", "milestone_due_time", "ISO_TIMESTAMP"),
    ("amount", "commercial_amount", "DECIMAL_CURRENCY"),
    ("currency", "commercial_currency", "IDENTITY"),
    ("basis", "commercial_basis", "IDENTITY"),
    ("evidence_refs", "structured_evidence_references", "LIST_SPLIT"),
    ("fresh_at", "source_freshness", "ISO_TIMESTAMP"),
    ("lineage_refs", "lineage_receipt_ids", "LIST_SPLIT"),
)


def build_deal_profile() -> MappingProfileV1:
    rules = []
    for source, target, conversion in DEAL_RULES:
        kwargs: dict[str, object] = {}
        if conversion == "EXACT_ID_CROSSWALK":
            kwargs["crosswalk"] = (
                CrosswalkEntryV1(
                    source_value="deal-1",
                    canonical_value=f"urn:orchestrator:csv-operational-v1:{SOURCE_INSTANCE_ID}:DEAL:deal-1",
                ),
            )
        if conversion == "LIST_SPLIT":
            kwargs["list_delimiter"] = ";"
        rules.append(
            MappingRuleV1(
                rule_id=f"rule-{target.replace('_', '-')}",
                source_field_id=source,
                canonical_target_field=target,
                conversion_id=conversion,
                required=True,
                **kwargs,
            )
        )
    payload: dict[str, object] = {
        "schema_version": "orchestrator.mapping-profile.v1",
        "profile_id": "profile-example-deal-priority-v1",
        "adapter_source_format_id": "csv-operational-v1",
        "adapter_source_format_version": "1",
        "source_instance_id": SOURCE_INSTANCE_ID,
        "object_kind": "DEAL_WORK_REQUEST",
        "rules": tuple(rules),
        "null_tokens": ("", "NULL"),
        "timezone": "UTC",
        "currency": "USD",
        "effort_unit": None,
        "source_population_predicate_sha256": "e" * 64,
        "owner_role": "data-owner",
        "reviewer_role": "manager",
        "accepted_at": ACCEPTED_AT,
    }
    payload["canonical_profile_sha256"] = mapping_profile_payload_hash(payload)
    return MappingProfileV1.model_validate(payload)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    profile = build_deal_profile()
    scan_mapping_profile(profile)  # fail closed if any value/secret slipped in
    target = OUT / "example_deal_priority_csv_v1.json"
    target.write_text(
        json.dumps(profile.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
