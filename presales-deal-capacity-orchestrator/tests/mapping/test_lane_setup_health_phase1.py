from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from orchestrator.contracts.enums import DataClassificationV1, LaneV1, SnapshotSemanticsV1, SourceModeV1
from orchestrator.contracts.manifest import HardBoundsV1
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.setup import SourceSlotSelectionV1
from orchestrator.ingestion.manifests import build_file_source_manifest
from orchestrator.mapping.health import (
    PopulationCountsV1,
    SourceConflictV1,
    assess_data_health,
    capacity_coverage,
)
from orchestrator.mapping.projections import project_consultant, project_deal, project_operational_record, serialized_projection
from orchestrator.setup_gate import (
    PostPreflightIdentityV1,
    SetupGateError,
    bind_post_preflight_manifest,
    build_authorization_attestation,
    build_run_setup_acceptance,
    validate_current_setup,
)

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def policy() -> PolicyV2:
    return PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())


def deal_payload() -> dict[str, object]:
    return {
        "work_request_id": "work-1", "deal_source_id": "deal-1",
        "region_source_value": "Europe", "region_id": "EMEA",
        "request_type": "DEMO_REQUEST", "milestone_type": "POC",
        "milestone_due_time": "2026-08-14T12:00:00Z", "effort_units": 8,
        "commercial_amount": "100000.00", "commercial_currency": "USD",
        "commercial_basis": "demo-corporate-bookings-v1",
        "required_skill_ids": ["security"], "required_languages": ["en"],
        "required_working_window_overlap_minutes": 120,
        "structured_evidence_references": [], "source_freshness": "2026-08-01T00:00:00Z",
        "lineage_receipt_ids": ["lin-1"],
        "account_source_id": "unconsumed-account", "pipeline_id": "unconsumed-pipeline",
        "stage_id": "unconsumed-stage",
    }


def test_all_three_exact_lane_projections_omit_unconsumed_fields() -> None:
    priority = serialized_projection(project_deal(deal_payload(), LaneV1.DEAL_PRIORITIZATION))
    assert "region_id" not in priority and "effort_units" not in priority and "account_source_id" not in priority

    assignment = serialized_projection(project_deal(deal_payload(), LaneV1.ASSIGNMENT_RECOMMENDATION))
    assert "pipeline_id" not in assignment and "stage_id" not in assignment and "account_source_id" not in assignment

    capacity = serialized_projection(project_deal(deal_payload(), LaneV1.CAPACITY_HEATMAP))
    assert "request_type" not in capacity and "commercial_amount" not in capacity
    assert "structured_evidence_references" not in capacity

    consultant_payload = {
        "consultant_source_id": "consultant-1", "active_eligibility": True,
        "supported_region_ids": ["EMEA"], "time_zone": "Europe/London",
        "working_windows": ["09:00-17:00"], "languages": ["en"],
        "manager_approved_skill_ids": ["security"], "policy_receipt_ids": ["policy-1"],
    }
    capacity_consultant = serialized_projection(project_consultant(consultant_payload, LaneV1.CAPACITY_HEATMAP))
    assert "time_zone" not in capacity_consultant and "working_windows" not in capacity_consultant
    with pytest.raises(ValueError, match="no consultant roster"):
        project_consultant(consultant_payload, LaneV1.DEAL_PRIORITIZATION)

    capacity_record = project_operational_record("CAPACITY_AVAILABILITY", {
        "consultant_source_id": "consultant-1", "week_bucket": 1, "scheduled_units": 40,
        "time_off_reduction_units": 0, "source_as_of": "2026-08-01T00:00:00Z",
        "completeness_state": "COMPLETE", "lineage_receipt_ids": ["lin-capacity"],
    }, LaneV1.CAPACITY_HEATMAP)
    workload_record = project_operational_record("WORKLOAD_COMMITMENT", {
        "consultant_source_id": "consultant-1", "source_work_id": "task-1", "week_bucket": 1,
        "committed_units": 4, "due_time": "2026-08-07T00:00:00Z", "status": "OPEN",
        "lineage_receipt_ids": ["lin-workload"],
    }, LaneV1.ASSIGNMENT_RECOMMENDATION)
    skill_record = project_operational_record("SKILL_ASSERTION", {
        "consultant_source_id": "consultant-1", "skill_id": "security", "level": 3,
        "policy_owner": "manager", "effective_begin": "2026-08-01T00:00:00Z",
        "source_receipt_id": "skill-receipt-1",
    }, LaneV1.CAPACITY_HEATMAP)
    assert capacity_record.week_bucket == workload_record.week_bucket == 1
    assert skill_record.level == 3
    for kind in ("CAPACITY_AVAILABILITY", "WORKLOAD_COMMITMENT", "SKILL_ASSERTION"):
        with pytest.raises(ValueError, match="does not consume"):
            project_operational_record(kind, {}, LaneV1.DEAL_PRIORITIZATION)


def test_private_transcript_attestation_requires_separate_warning() -> None:
    with pytest.raises(ValueError, match="warning"):
        build_authorization_attestation(
            authorization_attestation_id="att-private", run_id="run-private",
            source_types=("TRANSCRIPT_JSON",), data_classification=DataClassificationV1.AUTHORIZED_PRIVATE_TRANSCRIPT,
            authorized_bounds={"max_rows": 100}, retention_policy_id="retention-session",
            actor_role="manager", attested_at=NOW, transcript_warning_acknowledged=False,
        )


def test_lane_setup_has_no_roster_for_priority_and_no_conversation_lane() -> None:
    deal_slot = SourceSlotSelectionV1(
        source_slot_id="slot-deals", authority_role="DEALS_PRIMARY",
        adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT,
    )
    receipt = build_run_setup_acceptance(
        run_id="run-priority", lane=LaneV1.DEAL_PRIORITIZATION, actor="manager",
        accepted_at=NOW, policy=policy(), source_slots=(deal_slot,),
        authority_and_core_confirmed=True, advanced_confirmed=True,
    )
    assert {slot.authority_role for slot in receipt.source_slots} == {"DEALS_PRIMARY"}
    assert len(receipt.actions) == 2
    assert {item.field_name for item in receipt.core_field_acceptances} >= {"horizon_weeks", "commercial_currency_basis"}
    assert "skill_catalog" not in {item.field_name for item in receipt.advanced_field_acceptances}

    conversation = SourceSlotSelectionV1(
        source_slot_id="slot-conversation", authority_role="CONVERSATION_ADDITIVE",
        adapter_id="transcript-json-v1", source_mode=SourceModeV1.FILE_IMPORT,
    )
    supply_slots = (
        SourceSlotSelectionV1(source_slot_id="slot-roster", authority_role="ROSTER_PRIMARY", adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT),
        SourceSlotSelectionV1(source_slot_id="slot-capacity", authority_role="CAPACITY_PRIMARY", adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT),
        SourceSlotSelectionV1(source_slot_id="slot-workload", authority_role="WORKLOAD_PRIMARY", adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT),
    )
    with pytest.raises(ValueError, match="cannot attach"):
        build_run_setup_acceptance(
            run_id="run-capacity", lane=LaneV1.CAPACITY_HEATMAP, actor="manager",
            accepted_at=NOW, policy=policy(), source_slots=(deal_slot, *supply_slots, conversation),
            authority_and_core_confirmed=True, advanced_confirmed=True,
        )


def test_policy_changes_invalidate_acceptance_and_four_week_horizon_is_literal() -> None:
    slot = SourceSlotSelectionV1(
        source_slot_id="slot-deals", authority_role="DEALS_PRIMARY", adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT,
    )
    receipt = build_run_setup_acceptance(
        run_id="run-1", lane=LaneV1.DEAL_PRIORITIZATION, actor="manager", accepted_at=NOW,
        policy=policy(), source_slots=(slot,), authority_and_core_confirmed=True, advanced_confirmed=True,
    )
    validate_current_setup(receipt, policy=policy(), source_slots=(slot,))
    changed = policy().model_copy(update={"commercial_value_cap": "600000.00"})
    with pytest.raises(SetupGateError, match="invalidated"):
        validate_current_setup(receipt, policy=changed, source_slots=(slot,))
    with pytest.raises(SetupGateError, match="confirmation"):
        build_run_setup_acceptance(
            run_id="run-2", lane=LaneV1.DEAL_PRIORITIZATION, actor="manager", accepted_at=NOW,
            policy=policy(), source_slots=(slot,), authority_and_core_confirmed=True, advanced_confirmed=False,
        )


def test_source_slot_authority_binds_only_matching_post_preflight_manifest() -> None:
    slot = SourceSlotSelectionV1(
        source_slot_id="slot-deals", authority_role="DEALS_PRIMARY", adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT,
    )
    receipt = build_run_setup_acceptance(
        run_id="run-1", lane=LaneV1.DEAL_PRIORITIZATION, actor="manager", accepted_at=NOW,
        policy=policy(), source_slots=(slot,), authority_and_core_confirmed=True, advanced_confirmed=True,
    )
    manifest = build_file_source_manifest(
        run_id="run-1", slot=slot, authorization_attestation_id="att-1",
        actual_identity_fingerprint="d" * 64, requested_objects=("DEAL_WORK_REQUEST",), selected_field_ids=("id",),
        snapshot_semantics=SnapshotSemanticsV1.FULL_SNAPSHOT,
        hard_bounds=HardBoundsV1(max_pages=1, max_rows=10, max_bytes=1000, max_seconds=10),
        mapping_profile_hash=None, retention_policy_id="retention-1",
    )
    identity = PostPreflightIdentityV1(
        adapter_id="csv-v1", source_mode=SourceModeV1.FILE_IMPORT,
        authority_role="DEALS_PRIMARY", actual_non_secret_identity_fingerprint="d" * 64,
    )
    bound = bind_post_preflight_manifest(receipt=receipt, source_slot_id="slot-deals", manifest=manifest, identity=identity)
    assert bound.source_manifest_id == manifest.source_manifest_id
    mismatch = identity.model_copy(update={"adapter_id": "json-v1"})
    with pytest.raises(SetupGateError, match="SOURCE_SLOT_IDENTITY_MISMATCH"):
        bind_post_preflight_manifest(receipt=receipt, source_slot_id="slot-deals", manifest=manifest, identity=mismatch)


def test_scenario_partial_clickup_workload_is_source_local_and_scenario_i_conflict_visible() -> None:
    incomplete, complete_count = capacity_coverage(
        consultant_ids=frozenset({"consultant-1", "consultant-2"}),
        capacity_buckets_by_consultant={
            "consultant-1": frozenset({1, 2, 3, 4}),
            "consultant-2": frozenset({1, 2, 3}),
        },
        workload_covered_consultant_ids=frozenset({"consultant-1"}),
    )
    assert incomplete == ("consultant-2",) and complete_count == 1
    populations = tuple(
        PopulationCountsV1(
            population=name, declared=1, fetched=1, parsed=1, accepted=1,
            quarantined=0, excluded=0, duplicate=0, tombstoned=0, unmatched=0, read_complete=True,
        )
        for name in ("DEAL_WORK_REQUEST", "CONSULTANT", "CAPACITY_AVAILABILITY", "WORKLOAD_COMMITMENT", "SKILL_ASSERTION")
    )
    conflict = SourceConflictV1(
        canonical_record_id="deal-1", canonical_field_id="milestone_due_time",
        winning_source_manifest_id="sm-salesforce", losing_source_manifest_ids=("sm-import",), acknowledged=False,
    )
    blocked = assess_data_health(
        receipt_id="health-1", run_id="run-1", lane=LaneV1.ASSIGNMENT_RECOMMENDATION,
        source_manifest_ids=("sm-salesforce",), mapping_profile_sha256s=("a" * 64,), populations=populations,
        created_at=NOW, incomplete_consultant_ids=incomplete, complete_consultant_count=complete_count,
        source_conflicts=(conflict,),
    )
    assert not blocked.accepted_for_operational_commit
    acknowledged = conflict.model_copy(update={"acknowledged": True})
    passed = assess_data_health(
        receipt_id="health-2", run_id="run-1", lane=LaneV1.ASSIGNMENT_RECOMMENDATION,
        source_manifest_ids=("sm-salesforce",), mapping_profile_sha256s=("a" * 64,), populations=populations,
        created_at=NOW, incomplete_consultant_ids=incomplete, complete_consultant_count=complete_count,
        source_conflicts=(acknowledged,),
    )
    assert passed.accepted_for_operational_commit and passed.incomplete_consultant_ids == ("consultant-2",)
