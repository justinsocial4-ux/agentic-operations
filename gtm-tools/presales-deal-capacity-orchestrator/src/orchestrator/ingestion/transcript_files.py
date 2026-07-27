from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Literal

from orchestrator.canonical import canonical_json_bytes
from orchestrator.contracts.enums import LaneV1
from orchestrator.contracts.manifest import SourceManifestV1
from orchestrator.contracts.mapping import MappingProfileV1
from orchestrator.contracts.records import ConversationSegmentV1
from orchestrator.ingestion.file_readers import FileReadBounds, read_csv_file, read_json_file
from orchestrator.ingestion.manifests import stable_source_record_id
from orchestrator.ingestion.transcripts import TranscriptRoute, TranscriptStageError, TranscriptStageResult, stage_transcripts_in_memory
from orchestrator.mapping.profiles import apply_mapping_profile


class TranscriptFileError(ValueError):
    pass


def read_transcript_file_ephemeral(
    *,
    path: Path,
    source_format: Literal["CSV", "JSON"],
    manifest: SourceManifestV1,
    profile: MappingProfileV1,
    route_id: str,
    origin_family: Literal["FILE_IMPORT", "FATHOM", "GONG"],
    native_call_or_meeting_id: str,
    exact_deal_source_id: str,
    started_at: datetime,
    ended_at: datetime,
) -> TranscriptRoute:
    if profile.source_instance_id != manifest.source_instance_id or manifest.mapping_profile_hash != profile.canonical_profile_sha256:
        raise TranscriptFileError("transcript profile does not match its source manifest")
    bounds = FileReadBounds(
        max_rows=manifest.hard_bounds.max_rows,
        max_bytes=manifest.hard_bounds.max_bytes,
        max_cell_bytes=min(1_048_576, manifest.hard_bounds.max_bytes),
        transcript=True,
    )
    reader = read_csv_file if source_format == "CSV" else read_json_file
    result = reader(
        path,
        authorization_attestation_id=manifest.authorization_attestation_id,
        bounds=bounds,
        selected_field_ids=manifest.selected_field_ids,
    )
    mapped = apply_mapping_profile(result.rows, profile, available_field_ids=result.field_ids)
    if mapped.quarantined_row_numbers or not mapped.accepted:
        raise TranscriptFileError("transcript segment mapping failed")
    segments: list[ConversationSegmentV1] = []
    for payload in mapped.accepted:
        if payload.get("deal_source_id") != exact_deal_source_id:
            raise TranscriptFileError("transcript file deal crosswalk is not exact")
        text = payload.get("text")
        segment_id = payload.get("segment_id")
        if not isinstance(text, str) or not isinstance(segment_id, str):
            raise TranscriptFileError("mapped transcript requires text and segment ID")
        payload = dict(payload)
        for offset_field in ("relative_begin_ms", "relative_end_ms"):
            raw_offset = payload.get(offset_field)
            if isinstance(raw_offset, str) and raw_offset.isascii() and raw_offset.isdigit():
                payload[offset_field] = int(raw_offset)
        payload.setdefault("schema_version", "orchestrator.conversation-segment.v1")
        payload["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        payload.setdefault("source_record_id", stable_source_record_id(
            adapter_id=manifest.adapter_id,
            source_instance_id=manifest.source_instance_id,
            object_kind=profile.object_kind,
            native_id=segment_id,
        ))
        segments.append(ConversationSegmentV1.model_validate_json(canonical_json_bytes(payload)))
    return TranscriptRoute(
        route_id=route_id,
        route_kind="FILE_IMPORT",
        source_manifest_id=manifest.source_manifest_id,
        origin_family=origin_family,
        native_call_or_meeting_id=native_call_or_meeting_id,
        deal_source_id=exact_deal_source_id,
        started_at=started_at,
        ended_at=ended_at,
        segments=tuple(segments),
    )


def stage_transcript_file(
    *,
    lane: LaneV1,
    exact_deal_source_ids: frozenset[str],
    **reader_kwargs: object,
) -> TranscriptStageResult:
    if lane is LaneV1.CAPACITY_HEATMAP:
        raise TranscriptStageError("conversation evidence is not consumed by Capacity/heatmap")
    route = read_transcript_file_ephemeral(**reader_kwargs)  # type: ignore[arg-type]
    return stage_transcripts_in_memory(
        lane=lane,
        routes=(route,),
        exact_deal_source_ids=exact_deal_source_ids,
    )
