from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from orchestrator.canonical import canonical_json_bytes, canonical_sha256
from orchestrator.contracts.enums import LaneV1
from orchestrator.contracts.manifest import SourceManifestV1
from orchestrator.contracts.mapping import MappingProfileV1
from orchestrator.ingestion.file_readers import FileReadBounds, read_csv_file, read_json_file
from orchestrator.ingestion.manifests import stable_source_record_id
from orchestrator.lineage import build_lineage_edges
from orchestrator.mapping.health import PopulationCountsV1
from orchestrator.mapping.profiles import MappingIssue, apply_mapping_profile
from orchestrator.mapping.projections import project_operational_record
from orchestrator.setup_gate import BoundSourceAuthorityV1
from orchestrator.store import Phase1Store


class ImportPipelineError(ValueError):
    pass


@dataclass(frozen=True)
class ImportedPopulation:
    population: PopulationCountsV1
    canonical_artifact_ids: tuple[str, ...]
    issues: tuple[MappingIssue, ...]
    unmapped_source_field_ids: tuple[str, ...]


def import_operational_file(
    *,
    store: Phase1Store,
    run_id: str,
    lane: LaneV1,
    path: Path,
    source_format: Literal["CSV", "JSON"],
    manifest: SourceManifestV1,
    bound_authority: BoundSourceAuthorityV1,
    profile: MappingProfileV1,
    artifact_kind: str,
    native_id_target_field: str,
    page_receipt_id: str,
    staged_at: datetime,
) -> ImportedPopulation:
    """Credential-free file read -> map -> lane project -> operational staging."""
    if (
        manifest.run_id != run_id
        or bound_authority.source_manifest_id != manifest.source_manifest_id
        or bound_authority.source_instance_id != manifest.source_instance_id
        or profile.source_instance_id != manifest.source_instance_id
        or manifest.mapping_profile_hash != profile.canonical_profile_sha256
    ):
        raise ImportPipelineError("unbound manifest/profile authority cannot enter canonical staging")
    bounds = FileReadBounds(
        max_rows=manifest.hard_bounds.max_rows,
        max_bytes=manifest.hard_bounds.max_bytes,
        max_cell_bytes=min(1_048_576, manifest.hard_bounds.max_bytes),
    )
    reader = read_csv_file if source_format == "CSV" else read_json_file
    result = reader(
        path,
        authorization_attestation_id=manifest.authorization_attestation_id,
        bounds=bounds,
        selected_field_ids=manifest.selected_field_ids,
    )
    mapped = apply_mapping_profile(result.rows, profile, available_field_ids=result.field_ids)
    artifact_ids: list[str] = []
    projection_issues: list[MappingIssue] = []
    seen_native_ids: dict[str, str] = {}
    duplicate_count = 0
    for mapped_payload, row_number in zip(mapped.accepted, mapped.accepted_row_numbers, strict=True):
        try:
            record = project_operational_record(artifact_kind, mapped_payload, lane)
        except (ValidationError, ValueError):
            projection_issues.append(MappingIssue(row_number, artifact_kind, "LANE_PROJECTION_REJECTED"))
            continue
        serialized = record.model_dump(mode="json", exclude_unset=True)
        artifact_digest = canonical_sha256(serialized)
        artifact_id = f"ca-{artifact_digest[:32]}"
        native_id = serialized.get(native_id_target_field)
        if not isinstance(native_id, str) or not native_id:
            projection_issues.append(MappingIssue(row_number, native_id_target_field, "NATIVE_ID_MISSING"))
            continue
        if native_id in seen_native_ids:
            duplicate_count += 1
            if seen_native_ids[native_id] != artifact_digest:
                projection_issues.append(MappingIssue(row_number, native_id_target_field, "CONFLICTING_DUPLICATE_NATIVE_ID"))
            continue
        seen_native_ids[native_id] = artifact_digest
        source_record_id = stable_source_record_id(
            adapter_id=manifest.adapter_id,
            source_instance_id=manifest.source_instance_id,
            object_kind=profile.object_kind,
            native_id=native_id,
        )
        source_row = result.rows[row_number - 1]
        edges = build_lineage_edges(
            run_id=run_id,
            source_manifest_id=manifest.source_manifest_id,
            page_receipt_id=page_receipt_id,
            source_record_id=source_record_id,
            source_row=source_row,
            profile=profile,
            canonical_artifact_id=artifact_id,
            source_format=source_format,
        )
        staging_digest = hashlib.sha256(f"{run_id}\0{artifact_id}".encode()).hexdigest()
        store.stage_operational_artifact(
            staging_id=f"stage-{staging_digest[:32]}",
            run_id=run_id,
            source_manifest_id=manifest.source_manifest_id,
            canonical_artifact_id=artifact_id,
            artifact_kind=artifact_kind,
            artifact=record,
            lineage_edges=edges,
            staged_at=staged_at,
        )
        artifact_ids.append(artifact_id)
    conflict_issue_count = sum(issue.reason_code == "CONFLICTING_DUPLICATE_NATIVE_ID" for issue in projection_issues)
    total_quarantined = len(mapped.quarantined_row_numbers) + len(projection_issues) - conflict_issue_count
    return ImportedPopulation(
        population=PopulationCountsV1(
            population=artifact_kind,
            declared=len(result.rows),
            fetched=len(result.rows),
            parsed=len(result.rows),
            accepted=len(artifact_ids),
            quarantined=total_quarantined,
            excluded=0,
            duplicate=duplicate_count,
            tombstoned=0,
            unmatched=0,
            read_complete=result.complete,
        ),
        canonical_artifact_ids=tuple(artifact_ids),
        issues=(*mapped.issues, *projection_issues),
        unmapped_source_field_ids=mapped.unmapped_source_field_ids,
    )
