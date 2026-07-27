from __future__ import annotations

import hashlib
from datetime import datetime
from urllib.parse import quote

from orchestrator.canonical import canonical_json_bytes
from orchestrator.contracts.enums import DataClassificationV1, SnapshotSemanticsV1, SourceModeV1
from orchestrator.contracts.manifest import HardBoundsV1, SourceAuthorityBindingV1, SourceManifestV1
from orchestrator.contracts.setup import SourceSlotSelectionV1


def source_identity_fingerprint(*, adapter_id: str, non_secret_source_identity: str) -> str:
    if not non_secret_source_identity:
        raise ValueError("source identity cannot be empty")
    return hashlib.sha256(canonical_json_bytes({
        "adapter_id": adapter_id,
        "identity": non_secret_source_identity,
    })).hexdigest()


def opaque_source_instance_id(*, adapter_id: str, identity_fingerprint: str) -> str:
    digest = hashlib.sha256(f"{adapter_id}\0{identity_fingerprint}".encode()).hexdigest()
    return f"src-{digest[:32]}"


def stable_source_record_id(
    *, adapter_id: str, source_instance_id: str, object_kind: str, native_id: str,
) -> str:
    if not native_id:
        raise ValueError("native IDs must remain non-empty strings")
    encoded = quote(native_id, safe="")
    return f"urn:orchestrator:{adapter_id}:{source_instance_id}:{object_kind}:{encoded}"


def build_file_source_manifest(
    *,
    run_id: str,
    slot: SourceSlotSelectionV1,
    authorization_attestation_id: str,
    actual_identity_fingerprint: str,
    requested_objects: tuple[str, ...],
    selected_field_ids: tuple[str, ...],
    snapshot_semantics: SnapshotSemanticsV1,
    hard_bounds: HardBoundsV1,
    mapping_profile_hash: str | None,
    retention_policy_id: str,
    data_classification: DataClassificationV1 = DataClassificationV1.AUTHORIZED_INTERNAL,
    window_begin: datetime | None = None,
    window_end: datetime | None = None,
) -> SourceManifestV1:
    if slot.source_mode is not SourceModeV1.FILE_IMPORT:
        raise ValueError("file manifest requires a FILE_IMPORT source slot")
    if (
        slot.expected_non_secret_identity_fingerprint is not None
        and slot.expected_non_secret_identity_fingerprint != actual_identity_fingerprint
    ):
        raise ValueError("SOURCE_SLOT_IDENTITY_MISMATCH")
    source_instance_id = opaque_source_instance_id(
        adapter_id=slot.adapter_id,
        identity_fingerprint=actual_identity_fingerprint,
    )
    manifest_digest = hashlib.sha256(canonical_json_bytes({
        "run_id": run_id,
        "slot": slot,
        "source_instance_id": source_instance_id,
        "objects": requested_objects,
        "fields": selected_field_ids,
    })).hexdigest()
    return SourceManifestV1(
        schema_version="orchestrator.source-manifest.v1",
        source_manifest_id=f"sm-{manifest_digest[:32]}",
        run_id=run_id,
        adapter_id=slot.adapter_id,
        source_mode=slot.source_mode,
        source_instance_id=source_instance_id,
        authorization_attestation_id=authorization_attestation_id,
        data_classification=data_classification,
        snapshot_semantics=snapshot_semantics,
        authority_bindings=(SourceAuthorityBindingV1(
            source_slot_id=slot.source_slot_id,
            authority_role=slot.authority_role,
            expected_non_secret_identity_fingerprint=slot.expected_non_secret_identity_fingerprint,
        ),),
        requested_objects=requested_objects,
        selected_field_ids=selected_field_ids,
        window_begin=window_begin,
        window_end=window_end,
        hard_bounds=hard_bounds,
        mapping_profile_hash=mapping_profile_hash,
        retention_policy_id=retention_policy_id,
        synthetic=data_classification is DataClassificationV1.FICTIONAL,
    )
