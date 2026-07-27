import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestrator.contracts.enums import LaneV1, SourceModeV1
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.setup import ConfirmationActionV1, RunSetupAcceptanceV1, SourceSlotSelectionV1
from orchestrator.setup_gate import build_run_setup_acceptance

ROOT = Path(__file__).resolve().parents[2]


def acceptance() -> RunSetupAcceptanceV1:
    policy = PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())
    slots = (
        SourceSlotSelectionV1(source_slot_id="slot-deals", authority_role="DEALS_PRIMARY", adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT),
        SourceSlotSelectionV1(source_slot_id="slot-roster", authority_role="ROSTER_PRIMARY", adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT),
        SourceSlotSelectionV1(source_slot_id="slot-capacity", authority_role="CAPACITY_PRIMARY", adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT),
        SourceSlotSelectionV1(source_slot_id="slot-workload", authority_role="WORKLOAD_PRIMARY", adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT),
    )
    return build_run_setup_acceptance(
        run_id="run-1", lane=LaneV1.ASSIGNMENT_RECOMMENDATION, actor="manager",
        accepted_at=datetime(2026, 1, 1, tzinfo=timezone.utc), policy=policy,
        source_slots=slots, authority_and_core_confirmed=True, advanced_confirmed=True,
    )


def test_authority_is_folded_into_two_action_setup_budget() -> None:
    receipt = acceptance()
    assert len(receipt.actions) == 2
    assert receipt.actions[0].action_kind == "AUTHORITY_AND_CORE"
    assert len(receipt.core_field_acceptances) == 11
    assert len(receipt.advanced_field_acceptances) == 8


def test_separate_authority_or_third_confirmation_action_is_impossible() -> None:
    with pytest.raises(ValidationError):
        RunSetupAcceptanceV1.model_validate({
            **acceptance().model_dump(),
            "actions": [
                {"action_number": 1, "action_kind": "AUTHORITY_AND_CORE"},
                {"action_number": 2, "action_kind": "ADVANCED_REVIEWED_DEFAULTS"},
                {"action_number": 2, "action_kind": "ADVANCED_REVIEWED_DEFAULTS"},
            ],
        })


def test_incomplete_policy_inventory_is_rejected() -> None:
    payload = acceptance().model_dump()
    payload["core_field_acceptances"] = payload["core_field_acceptances"][:-1]
    with pytest.raises(ValidationError, match="inventory"):
        RunSetupAcceptanceV1.model_validate(payload)
