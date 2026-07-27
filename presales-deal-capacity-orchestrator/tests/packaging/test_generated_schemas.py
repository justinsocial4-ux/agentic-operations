import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "source_manifest_v1.schema.json", "mapping_profile_v1.schema.json",
    "conversation_segment_v1.schema.json", "analyst_observation_v2.schema.json",
    "export_bundle_v2.schema.json", "adapter_capability_v1.schema.json",
    "connector_page_v1.schema.json", "connector_preflight_v1.schema.json",
    "deletion_receipt_v1.schema.json", "source_schema_metadata_v1.schema.json",
    "deal_work_request_v2.schema.json", "policy_v2.schema.json",
    "run_setup_acceptance_v1.schema.json", "authorization_attestation_v1.schema.json",
    "consultant_v2.schema.json",
    "capacity_availability_v1.schema.json", "workload_commitment_v1.schema.json",
    "skill_assertion_v1.schema.json", "conversation_evidence_metadata_v1.schema.json",
    "data_health_receipt_v1.schema.json",
    "solver_receipt_v1.schema.json", "assignment_recommendation_v2.schema.json",
    "capacity_cell_v2.schema.json", "scenario_comparison_v2.schema.json",
    "leadership_digest_v2.schema.json",
}


def test_required_public_schemas_are_checked_in_and_forbid_extra_fields() -> None:
    assert EXPECTED <= {path.name for path in (ROOT / "schemas").glob("*.json")}
    for name in EXPECTED:
        schema = json.loads((ROOT / "schemas" / name).read_text())
        assert schema.get("additionalProperties") is False
