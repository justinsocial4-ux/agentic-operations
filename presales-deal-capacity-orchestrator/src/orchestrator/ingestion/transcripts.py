from __future__ import annotations

import gc
import hashlib
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from orchestrator.contracts.enums import LaneV1
from orchestrator.contracts.records import (
    ConversationEvidenceMetadataV1,
    ConversationOriginV1,
    ConversationSegmentV1,
)


class TranscriptStageError(ValueError):
    """Transcript failures intentionally never include source text."""


@dataclass(frozen=True)
class TranscriptRoute:
    route_id: str
    route_kind: Literal["FILE_IMPORT", "DIRECT_REPLAY", "DIRECT_CONNECTOR"]
    source_manifest_id: str
    origin_family: Literal["FILE_IMPORT", "FATHOM", "GONG"]
    native_call_or_meeting_id: str
    deal_source_id: str
    started_at: datetime
    ended_at: datetime
    segments: tuple[ConversationSegmentV1, ...]


@dataclass(frozen=True)
class ConversationDuplicateEdge:
    duplicate_route_id: str
    authoritative_route_id: str
    reason: Literal["SAME_NATIVE_ID_AND_CONTENT_HASH", "CONFIRMED_HASH_MATCH"]


@dataclass(frozen=True)
class ConversationConflict:
    route_ids: tuple[str, str]
    reason: Literal["CONVERSATION_ORIGIN_CONFLICT", "DUPLICATE_CONFIRMATION_REQUIRED"]


@dataclass(frozen=True)
class TranscriptStageResult:
    metadata: tuple[ConversationEvidenceMetadataV1, ...]
    authoritative_source_manifest_ids: tuple[str, ...]
    duplicate_edges: tuple[ConversationDuplicateEdge, ...]
    conflicts: tuple[ConversationConflict, ...]
    analyzed_origin_ids: tuple[str, ...]


def establish_no_core_dump_policy() -> bool:
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        return resource.getrlimit(resource.RLIMIT_CORE)[0] == 0
    except (ImportError, OSError, ValueError):
        return False


def _normalized_content_hash(segments: tuple[ConversationSegmentV1, ...]) -> str:
    digest = hashlib.sha256()
    for index, segment in enumerate(segments):
        normalized = unicodedata.normalize("NFC", segment.text.replace("\r\n", "\n").replace("\r", "\n"))
        if index:
            digest.update(b"\n")
        digest.update(normalized.encode("utf-8"))
    return digest.hexdigest()


def normalized_content_hash(segments: tuple[ConversationSegmentV1, ...]) -> str:
    """Public wrapper: the exact normalized full-content hash used for cross-route dedup."""
    return _normalized_content_hash(segments)


def conversation_origin_for_route(route: TranscriptRoute) -> ConversationOriginV1:
    """Build the ephemeral cross-route origin key. It is never persisted."""
    return ConversationOriginV1(
        schema_version="orchestrator.conversation-origin.v1",
        source_family=route.origin_family,
        opaque_source_instance=route.source_manifest_id,
        native_call_or_meeting_id=route.native_call_or_meeting_id or None,
        transcript_content_sha256=_normalized_content_hash(route.segments),
        deal_source_id=route.deal_source_id,
        started_at=route.started_at,
        ended_at=route.ended_at,
    )


def _authoritative(routes: list[tuple[TranscriptRoute, str]]) -> tuple[TranscriptRoute, str]:
    return sorted(routes, key=lambda item: (item[0].route_kind == "FILE_IMPORT", item[0].route_id))[0]


def stage_transcripts_in_memory(
    *,
    lane: LaneV1,
    routes: tuple[TranscriptRoute, ...],
    exact_deal_source_ids: frozenset[str],
    confirmed_hash_merge_route_pairs: frozenset[frozenset[str]] = frozenset(),
    require_no_core_dump: bool = True,
    cancel_requested: bool = False,
) -> TranscriptStageResult:
    if lane is LaneV1.CAPACITY_HEATMAP:
        raise TranscriptStageError("conversation evidence is not consumed by Capacity/heatmap")
    if require_no_core_dump and not establish_no_core_dump_policy():
        raise TranscriptStageError("transcript ingestion disabled because no-core-dump policy could not be established")
    if cancel_requested:
        gc.collect()
        return TranscriptStageResult((), (), (), (), ())

    hashed: list[tuple[TranscriptRoute, str]] = []
    for route in routes:
        if route.deal_source_id not in exact_deal_source_ids:
            raise TranscriptStageError("conversation requires an exact approved deal crosswalk")
        if not route.segments:
            raise TranscriptStageError("conversation route contains no segments")
        if route.started_at > route.ended_at:
            raise TranscriptStageError("conversation route has an invalid time interval")
        if any(segment.deal_source_id != route.deal_source_id for segment in route.segments):
            raise TranscriptStageError("cross-deal transcript segment denied")
        hashed.append((route, _normalized_content_hash(route.segments)))

    by_native: dict[tuple[str, str], list[tuple[TranscriptRoute, str]]] = {}
    for item in hashed:
        route, _ = item
        by_native.setdefault((route.origin_family, route.native_call_or_meeting_id), []).append(item)

    selected: list[tuple[TranscriptRoute, str]] = []
    duplicates: list[ConversationDuplicateEdge] = []
    conflicts: list[ConversationConflict] = []
    consumed_route_ids: set[str] = set()
    for group in by_native.values():
        hashes = {content_hash for _, content_hash in group}
        if len(hashes) > 1:
            ordered = sorted(route.route_id for route, _ in group)
            for left, right in zip(ordered, ordered[1:]):
                conflicts.append(ConversationConflict((left, right), "CONVERSATION_ORIGIN_CONFLICT"))
            consumed_route_ids.update(ordered)
            continue
        winner = _authoritative(group)
        selected.append(winner)
        consumed_route_ids.update(route.route_id for route, _ in group)
        for route, _ in group:
            if route.route_id != winner[0].route_id:
                duplicates.append(ConversationDuplicateEdge(
                    duplicate_route_id=route.route_id,
                    authoritative_route_id=winner[0].route_id,
                    reason="SAME_NATIVE_ID_AND_CONTENT_HASH",
                ))

    # Hash-only candidates never silently merge. Compatible deal/time metadata plus an
    # explicit manager confirmation is required.
    by_hash: dict[str, list[TranscriptRoute]] = {}
    for route, content_hash in selected:
        by_hash.setdefault(content_hash, []).append(route)
    retained: list[tuple[TranscriptRoute, str]] = []
    for content_hash, group in by_hash.items():
        if len(group) == 1:
            retained.append((group[0], content_hash))
            continue
        winner = sorted(group, key=lambda route: (route.route_kind == "FILE_IMPORT", route.route_id))[0]
        retained.append((winner, content_hash))
        for route in group:
            if route.route_id == winner.route_id:
                continue
            pair = frozenset({winner.route_id, route.route_id})
            compatible = (
                route.deal_source_id == winner.deal_source_id
                and route.started_at == winner.started_at
                and route.ended_at == winner.ended_at
            )
            if compatible and pair in confirmed_hash_merge_route_pairs:
                duplicates.append(ConversationDuplicateEdge(route.route_id, winner.route_id, "CONFIRMED_HASH_MATCH"))
            else:
                conflicts.append(ConversationConflict(tuple(sorted(pair)), "DUPLICATE_CONFIRMATION_REQUIRED"))
                retained = [item for item in retained if item[0].route_id != winner.route_id]

    metadata: list[ConversationEvidenceMetadataV1] = []
    manifest_ids: list[str] = []
    for route, content_hash in retained:
        role_counts = Counter(segment.speaker_ref for segment in route.segments)
        origin_digest = hashlib.sha256(
            f"{route.origin_family}\0{route.native_call_or_meeting_id}\0{content_hash}".encode()
        ).hexdigest()
        metadata.append(ConversationEvidenceMetadataV1(
            schema_version="orchestrator.conversation-evidence-metadata.v1",
            conversation_origin_id=f"origin-{origin_digest[:32]}",
            source_family=route.origin_family,
            native_call_or_meeting_id=route.native_call_or_meeting_id,
            deal_source_id=route.deal_source_id,
            transcript_content_sha256=content_hash,
            started_at=route.started_at,
            ended_at=route.ended_at,
            speaker_role_counts={key: role_counts.get(key, 0) for key in ("CUSTOMER", "INTERNAL", "UNKNOWN")},
            cited_excerpt_ids=(),
        ))
        manifest_ids.append(route.source_manifest_id)

    result = TranscriptStageResult(
        metadata=tuple(metadata),
        authoritative_source_manifest_ids=tuple(manifest_ids),
        duplicate_edges=tuple(duplicates),
        conflicts=tuple(conflicts),
        analyzed_origin_ids=tuple(item.conversation_origin_id for item in metadata),
    )
    # No route, segment, or text reference is retained by the result.
    hashed.clear()
    gc.collect()
    return result
