from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestrator.contracts.enums import LaneV1
from orchestrator.contracts.manifest import SourceManifestV1
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.records import CurrencyNormalizationApprovalV1, DealWorkRequestV2

ROOT = Path(__file__).resolve().parents[2]


def test_demo_policy_is_strict_and_uses_literal_units() -> None:
    policy = PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())
    assert policy.horizon_weeks == 4
    assert policy.capacity_unit_minutes == 30
    assert "individual_win_rate" in policy.prohibited_inputs


@pytest.mark.parametrize("field,invalid", [("horizon_weeks", 5), ("capacity_unit_minutes", 60)])
def test_policy_confirm_only_literals_reject_other_values(field: str, invalid: int) -> None:
    payload = json.loads((ROOT / "config/demo_policy_v2.json").read_text())
    payload[field] = invalid
    with pytest.raises(ValidationError):
        PolicyV2.model_validate(payload)


def test_policy_cannot_loosen_no_win_rate_transcript_fit_or_write_boundaries() -> None:
    payload = json.loads((ROOT / "config/demo_policy_v2.json").read_text())
    payload["prohibited_inputs"].remove("individual_win_rate")
    with pytest.raises(ValidationError, match="cannot loosen"):
        PolicyV2.model_validate_json(json.dumps(payload))


def test_duplicate_json_keys_rejected_before_model_validation() -> None:
    duplicate = '{"schema_version":"orchestrator.policy.v2","horizon_weeks":4,"horizon_weeks":4}'
    with pytest.raises(ValueError, match="duplicate JSON key"):
        PolicyV2.model_validate_json(duplicate)


def test_extra_fields_and_numeric_decimal_are_rejected() -> None:
    payload = json.loads((ROOT / "config/demo_policy_v2.json").read_text())
    payload["invented"] = True
    with pytest.raises(ValidationError, match="Extra inputs"):
        PolicyV2.model_validate(payload)
    payload.pop("invented")
    payload["commercial_value_floor"] = 10000.0
    with pytest.raises(ValidationError):
        PolicyV2.model_validate(payload)


def test_offset_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValidationError, match="UTC offset"):
        CurrencyNormalizationApprovalV1(
            schema_version="orchestrator.currency-normalization-approval.v1",
            normalized_amount="100.00",
            corporate_currency="USD",
            corporate_basis_id="bookings-v1",
            approval_basis_identifier="approval-basis-1",
            approval_receipt_id="approval-1",
            mapping_rule_id="rule-1",
            source_lineage_receipt_ids=("lineage-1",),
            approved_at=datetime(2026, 1, 1),
        )


def test_currency_normalization_receipt_is_typed_and_lineage_complete() -> None:
    approval = CurrencyNormalizationApprovalV1(
        schema_version="orchestrator.currency-normalization-approval.v1",
        normalized_amount="100.00",
        corporate_currency="USD",
        corporate_basis_id="bookings-v1",
        approval_basis_identifier="approval-basis-1",
        approval_receipt_id="approval-1",
        mapping_rule_id="rule-1",
        source_lineage_receipt_ids=("lineage-1",),
        approved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    deal = DealWorkRequestV2(
        schema_version="orchestrator.deal-work-request.v2",
        work_request_id="work-1",
        deal_source_id="deal-1",
        corporate_currency_normalization=approval,
    )
    assert deal.corporate_currency_normalization.approval_basis_identifier == "approval-basis-1"
    with pytest.raises(ValidationError):
        CurrencyNormalizationApprovalV1(
            **{**approval.model_dump(), "source_lineage_receipt_ids": ()}
        )


def test_deal_lane_projection_rejects_missing_consumed_fields() -> None:
    deal = DealWorkRequestV2(
        schema_version="orchestrator.deal-work-request.v2",
        work_request_id="work-1",
        deal_source_id="deal-1",
    )
    with pytest.raises(ValueError, match="commercial_amount"):
        deal.validate_for_lane(LaneV1.DEAL_PRIORITIZATION)


def test_source_manifest_supports_one_source_in_multiple_authority_roles() -> None:
    payload = {
        "schema_version": "orchestrator.source-manifest.v1",
        "source_manifest_id": "sm-1", "run_id": "run-1", "adapter_id": "clickup-v1",
        "source_mode": "FILE_IMPORT", "source_instance_id": "source-1",
        "authorization_attestation_id": "att-1", "data_classification": "AUTHORIZED_INTERNAL",
        "snapshot_semantics": "FULL_SNAPSHOT",
        "authority_bindings": [
            {"source_slot_id": "slot-roster", "authority_role": "ROSTER_PRIMARY", "expected_non_secret_identity_fingerprint": None},
            {"source_slot_id": "slot-capacity", "authority_role": "CAPACITY_PRIMARY", "expected_non_secret_identity_fingerprint": None}
        ],
        "requested_objects": ["TASK"], "selected_field_ids": ["id"],
        "window_begin": "2026-01-01T00:00:00Z", "window_end": "2026-01-02T00:00:00Z",
        "hard_bounds": {"max_pages": 20, "max_rows": 2000, "max_bytes": 52428800, "max_seconds": 120},
        "mapping_profile_hash": None, "retention_policy_id": "retention-1", "synthetic": False
    }
    manifest = SourceManifestV1.model_validate_json_strict(json.dumps(payload))
    assert {binding.authority_role for binding in manifest.authority_bindings} == {"ROSTER_PRIMARY", "CAPACITY_PRIMARY"}
