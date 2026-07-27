from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from orchestrator.contracts.enums import LaneV1, SnapshotSemanticsV1, SourceModeV1
from orchestrator.contracts.manifest import HardBoundsV1
from orchestrator.contracts.mapping import MappingProfileV1, MappingRuleV1
from orchestrator.contracts.setup import SourceSlotSelectionV1
from orchestrator.ingestion.manifests import build_file_source_manifest, opaque_source_instance_id
from orchestrator.ingestion.transcript_files import stage_transcript_file
from orchestrator.ingestion.transcripts import TranscriptStageError
from orchestrator.mapping.profiles import mapping_profile_payload_hash

NOW = datetime(2026, 8, 3, 9, tzinfo=timezone.utc)


def make_profile(source_instance_id: str, source_format: str) -> MappingProfileV1:
    fields = {
        "conversation_id": "IDENTITY", "deal_source_id": "IDENTITY", "segment_id": "IDENTITY",
        "speaker_ref": "IDENTITY", "occurred_at": "ISO_TIMESTAMP",
        "relative_begin_ms": "IDENTITY", "relative_end_ms": "IDENTITY",
        "text": "IDENTITY", "lineage_receipt_id": "IDENTITY",
    }
    rules = tuple(
        MappingRuleV1(
            rule_id=f"rule-{target.replace('_', '-')}", source_field_id=target,
            canonical_target_field=target, conversion_id=conversion, required=True,
        )
        for target, conversion in fields.items()
    )
    payload: dict[str, object] = {
        "schema_version": "orchestrator.mapping-profile.v1", "profile_id": f"profile-{source_format.lower()}",
        "adapter_source_format_id": f"transcript-{source_format.lower()}-v1", "adapter_source_format_version": "1",
        "source_instance_id": source_instance_id, "object_kind": "CONVERSATION_SEGMENT", "rules": rules,
        "null_tokens": ("",), "timezone": "UTC", "currency": None, "effort_unit": None,
        "source_population_predicate_sha256": "b" * 64, "owner_role": "data-owner", "reviewer_role": "manager",
        "accepted_at": NOW,
    }
    payload["canonical_profile_sha256"] = mapping_profile_payload_hash(payload)
    return MappingProfileV1.model_validate(payload)


@pytest.mark.parametrize("source_format", ["CSV", "JSON"])
def test_csv_and_json_transcript_importers_are_ephemeral_and_exact_crosswalked(tmp_path: Path, source_format: str) -> None:
    row = {
        "conversation_id": "conv-1", "deal_source_id": "deal-1", "segment_id": "seg-1",
        "speaker_ref": "CUSTOMER", "occurred_at": "2026-08-03T09:00:00Z",
        "relative_begin_ms": 0, "relative_end_ms": 1000,
        "text": "Fictional customer explicitly requires EU data residency.",
        "lineage_receipt_id": "lineage-1",
    }
    path = tmp_path / f"transcript.{source_format.lower()}"
    if source_format == "CSV":
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=tuple(row))
            writer.writeheader()
            writer.writerow(row)
    else:
        path.write_text(json.dumps([row]), encoding="utf-8")
    slot = SourceSlotSelectionV1(
        source_slot_id="slot-conversation", authority_role="CONVERSATION_ADDITIVE",
        adapter_id=f"transcript-{source_format.lower()}-v1", source_mode=SourceModeV1.FILE_IMPORT,
    )
    fingerprint = "c" * 64
    source_instance_id = opaque_source_instance_id(adapter_id=slot.adapter_id, identity_fingerprint=fingerprint)
    profile = make_profile(source_instance_id, source_format)
    manifest = build_file_source_manifest(
        run_id="run-1", slot=slot, authorization_attestation_id="att-1",
        actual_identity_fingerprint=fingerprint, requested_objects=("CONVERSATION_SEGMENT",),
        selected_field_ids=tuple(row), snapshot_semantics=SnapshotSemanticsV1.FULL_SNAPSHOT,
        hard_bounds=HardBoundsV1(max_pages=1, max_rows=100, max_bytes=100_000, max_seconds=10),
        mapping_profile_hash=profile.canonical_profile_sha256, retention_policy_id="retention-1",
    )
    kwargs = dict(
        path=path, source_format=source_format, manifest=manifest, profile=profile,
        route_id="file-route", origin_family="GONG", native_call_or_meeting_id="gong-call-1",
        exact_deal_source_id="deal-1", started_at=NOW, ended_at=NOW,
    )
    result = stage_transcript_file(
        lane=LaneV1.DEAL_PRIORITIZATION,
        exact_deal_source_ids=frozenset({"deal-1"}),
        **kwargs,
    )
    assert len(result.metadata) == 1
    assert result.metadata[0].cited_excerpt_ids == ()
    with pytest.raises(TranscriptStageError, match="not consumed"):
        stage_transcript_file(
            lane=LaneV1.CAPACITY_HEATMAP,
            exact_deal_source_ids=frozenset({"deal-1"}),
            **kwargs,
        )
