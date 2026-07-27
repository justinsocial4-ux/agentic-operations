from __future__ import annotations

import json
import socket
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.canonical import canonical_sha256
from orchestrator.contracts.enums import DataClassificationV1, LaneV1, SnapshotSemanticsV1, SourceModeV1
from orchestrator.contracts.manifest import HardBoundsV1
from orchestrator.contracts.mapping import CrosswalkEntryV1, MappingProfileV1, MappingRuleV1
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.setup import SourceSlotSelectionV1
from orchestrator.ingestion.file_readers import contract_tested_file_import_proof
from orchestrator.ingestion.import_pipeline import import_operational_file
from orchestrator.ingestion.manifests import build_file_source_manifest, opaque_source_instance_id
from orchestrator.mapping.health import assess_data_health
from orchestrator.mapping.profiles import mapping_profile_payload_hash
from orchestrator.setup_gate import (
    PostPreflightIdentityV1, bind_post_preflight_manifest, build_authorization_attestation,
    build_run_setup_acceptance,
)
from orchestrator.store import Phase1Store, apply_migrations, connect_database

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def make_deal_profile(source_instance_id: str) -> MappingProfileV1:
    target_conversions: tuple[tuple[str, str, str], ...] = (
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
    rules = []
    for source, target, conversion in target_conversions:
        kwargs: dict[str, object] = {}
        if conversion == "EXACT_ID_CROSSWALK":
            kwargs["crosswalk"] = (CrosswalkEntryV1(
                source_value="deal-1",
                canonical_value=f"urn:orchestrator:csv-operational-v1:{source_instance_id}:DEAL:deal-1",
            ),)
        if conversion == "LIST_SPLIT":
            kwargs["list_delimiter"] = ";"
        rules.append(MappingRuleV1(
            rule_id=f"rule-{target.replace('_', '-')}", source_field_id=source,
            canonical_target_field=target, conversion_id=conversion, required=True, **kwargs,
        ))
    payload: dict[str, object] = {
        "schema_version": "orchestrator.mapping-profile.v1", "profile_id": "profile-deal-priority-v1",
        "adapter_source_format_id": "csv-operational-v1", "adapter_source_format_version": "1",
        "source_instance_id": source_instance_id, "object_kind": "DEAL_WORK_REQUEST", "rules": tuple(rules),
        "null_tokens": ("", "NULL"), "timezone": "UTC", "currency": "USD", "effort_unit": None,
        "source_population_predicate_sha256": "e" * 64, "owner_role": "data-owner", "reviewer_role": "manager",
        "accepted_at": NOW,
    }
    payload["canonical_profile_sha256"] = mapping_profile_payload_hash(payload)
    return MappingProfileV1.model_validate(payload)


def test_import_only_end_to_end_is_credential_free_network_denied_and_commits_health(tmp_path: Path, monkeypatch: object) -> None:
    def deny_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("file-import path attempted network access")

    monkeypatch.setattr(socket.socket, "connect", deny_network)  # type: ignore[attr-defined]
    policy = PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())
    slot = SourceSlotSelectionV1(
        source_slot_id="slot-deals", authority_role="DEALS_PRIMARY",
        adapter_id="csv-operational-v1", source_mode=SourceModeV1.FILE_IMPORT,
    )
    attestation = build_authorization_attestation(
        authorization_attestation_id="att-fictional-import", run_id="run-import-e2e",
        source_types=("CSV",), data_classification=DataClassificationV1.AUTHORIZED_INTERNAL,
        authorized_bounds={"max_rows": 100, "max_bytes": 100_000},
        retention_policy_id="retention-7-days", actor_role="manager", attested_at=NOW,
        transcript_warning_acknowledged=False,
    )
    setup = build_run_setup_acceptance(
        run_id="run-import-e2e", lane=LaneV1.DEAL_PRIORITIZATION, actor="manager",
        accepted_at=NOW, policy=policy, source_slots=(slot,),
        authority_and_core_confirmed=True, advanced_confirmed=True,
    )
    fingerprint = "f" * 64
    source_instance_id = opaque_source_instance_id(adapter_id=slot.adapter_id, identity_fingerprint=fingerprint)
    profile = make_deal_profile(source_instance_id)
    selected_fields = tuple(rule.source_field_id for rule in profile.rules)
    manifest = build_file_source_manifest(
        run_id="run-import-e2e", slot=slot, authorization_attestation_id="att-fictional-import",
        actual_identity_fingerprint=fingerprint, requested_objects=("DEAL_WORK_REQUEST",),
        selected_field_ids=selected_fields, snapshot_semantics=SnapshotSemanticsV1.FULL_SNAPSHOT,
        hard_bounds=HardBoundsV1(max_pages=1, max_rows=100, max_bytes=100_000, max_seconds=10),
        mapping_profile_hash=profile.canonical_profile_sha256, retention_policy_id="retention-7-days",
    )
    identity = PostPreflightIdentityV1(
        adapter_id=slot.adapter_id, source_mode=SourceModeV1.FILE_IMPORT,
        authority_role="DEALS_PRIMARY", actual_non_secret_identity_fingerprint=fingerprint,
    )
    bound = bind_post_preflight_manifest(
        receipt=setup, source_slot_id=slot.source_slot_id, manifest=manifest, identity=identity,
    )

    connection = connect_database(tmp_path / "import.sqlite")
    apply_migrations(connection)
    store = Phase1Store(connection)
    store.create_run(run_id=setup.run_id, lane=setup.lane, synthetic=False, created_at=NOW)
    store.persist_authorization_attestation(attestation)
    store.persist_setup_acceptance(setup, policy_sha256=canonical_sha256(policy))
    store.persist_manifest(manifest)
    store.persist_bound_authority(setup.run_id, bound, bound_at=NOW)
    store.persist_mapping_profile(profile)
    store.persist_mapping_acceptance(
        acceptance_id="mapping-accept-1", run_id=setup.run_id,
        mapping_profile_id=profile.profile_id, actor_role="manager", accepted_at=NOW,
    )

    imported = import_operational_file(
        store=store, run_id=setup.run_id, lane=setup.lane,
        path=ROOT / "data/examples/import/deal_priority_v1.csv", source_format="CSV",
        manifest=manifest, bound_authority=bound, profile=profile,
        artifact_kind="DEAL_WORK_REQUEST", native_id_target_field="work_request_id",
        page_receipt_id="page-import-1", staged_at=NOW,
    )
    assert imported.population.accepted == 1
    health = assess_data_health(
        receipt_id="health-import-e2e", run_id=setup.run_id, lane=setup.lane,
        source_manifest_ids=(manifest.source_manifest_id,),
        mapping_profile_sha256s=(profile.canonical_profile_sha256,),
        populations=(imported.population,), created_at=NOW,
    )
    assert health.accepted_for_operational_commit
    assert store.commit_operational(health) == 1

    stored = json.loads(connection.execute("SELECT artifact_json FROM canonical_artifacts").fetchone()[0])
    assert stored["work_request_id"] == "work-1"
    assert stored["deal_source_id"].startswith("urn:orchestrator:")
    assert "region_id" not in stored and "effort_units" not in stored and "account_source_id" not in stored
    assert connection.execute("SELECT COUNT(*) FROM lineage_edges").fetchone()[0] == len(profile.rules)
    proof = contract_tested_file_import_proof()
    assert proof.execution_mode == "FILE_IMPORT"
    assert proof.live_validation_proof == "NOT_LIVE_VALIDATED"
    store.reset_run(setup.run_id)
    assert connection.execute("SELECT COUNT(*) FROM runs").fetchone() == (0,)
    assert connection.execute("SELECT COUNT(*) FROM canonical_artifacts").fetchone() == (0,)
    assert connection.execute("SELECT COUNT(*) FROM mapping_profiles").fetchone() == (0,)
    connection.close()
