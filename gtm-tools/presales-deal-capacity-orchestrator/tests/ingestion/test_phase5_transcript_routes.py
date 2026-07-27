from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from orchestrator.contracts.enums import LaneV1
from orchestrator.contracts.records import ConversationOriginV1, ConversationSegmentV1
from orchestrator.ingestion.gong import GongAdapter, GongProactiveLimiter
from orchestrator.ingestion.registry import load_gong_capability
from orchestrator.ingestion.transcripts import (
    TranscriptRoute,
    TranscriptStageError,
    conversation_origin_for_route,
    normalized_content_hash,
    stage_transcripts_in_memory,
)
from orchestrator.ingestion.transport import LockedHttpClient, build_httpx_client
from orchestrator.retention import scan_artifacts_for_sentinel, write_metadata_only_crash_artifact
from orchestrator.store import Phase1Store, apply_migrations, connect_database

ROOT = Path(__file__).resolve().parents[2]
FX = ROOT / "data" / "replay" / "gong"
NOW = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 8, 3, 10, 0, tzinfo=timezone.utc)
ALL_SCOPES = frozenset({
    "api:calls:read:basic", "api:calls:read:extensive", "api:calls:read:transcript", "api:users:read",
})
# A unique full-transcript phrase that must appear NOWHERE durable.
SENTINEL = "PHASE5_SENTINEL EU residency delighted really excited 5f1a2c"


def _extensive() -> dict:
    return json.loads((FX / "calls-extensive.json").read_text(encoding="utf-8"))


def _transcript_with(text: str) -> dict:
    return {
        "callTranscripts": [
            {
                "callId": "gong-call-1",
                "transcript": [
                    {"speakerId": "spk-external", "sentences": [{"start": 0, "end": 3000, "text": text}]},
                    {"speakerId": "spk-internal", "sentences": [{"start": 3000, "end": 6000, "text": "We can meet that."}]},
                ],
            }
        ],
        "records": {},
    }


def _gong_adapter(transcript_text: str) -> GongAdapter:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/calls/extensive":
            return httpx.Response(200, json=_extensive())
        if request.url.path == "/v2/calls/transcript":
            return httpx.Response(200, json=_transcript_with(transcript_text))
        return httpx.Response(404, json={})

    cap = load_gong_capability(ROOT)
    endpoints = GongAdapter._build_endpoints(cap)
    raw = build_httpx_client(transport=httpx.MockTransport(handler))
    locked = LockedHttpClient(endpoints, client=raw, sleeper=lambda _: None, now=lambda: 0)
    return GongAdapter(
        package_root=ROOT, auth_mode="SESSION_PASTED_BEARER", bearer_token="fake-bearer",
        available_scopes=ALL_SCOPES, capability=cap, client=locked,
        limiter=GongProactiveLimiter(monotonic=lambda: 0.0, wallclock=lambda: 0.0),
    )


def _direct_route(text: str, *, route_id: str = "direct-gong") -> TranscriptRoute:
    adapter = _gong_adapter(text)
    route = adapter.read_transcript_route(
        source_instance_id="sm-direct", call_id="gong-call-1", from_dt=NOW, to_dt=END,
        exact_deal_source_id="deal-1", started_at=NOW, ended_at=END, route_id=route_id,
    )
    adapter.close()
    return route


def _file_route(texts: list[str], *, route_id: str = "gong-file") -> TranscriptRoute:
    segments = []
    for index, text in enumerate(texts):
        segments.append(ConversationSegmentV1(
            schema_version="orchestrator.conversation-segment.v1",
            conversation_id="gong-call-1", deal_source_id="deal-1", segment_id=f"file-seg-{index}",
            speaker_ref="UNKNOWN", speaker_source_label=None, occurred_at=NOW,
            relative_begin_ms=index * 1000, relative_end_ms=index * 1000 + 500, text=text,
            source_record_id=f"file-src-{index}", text_sha256=hashlib.sha256(text.encode()).hexdigest(),
            lineage_receipt_id=f"lin-file-{index}",
        ))
    return TranscriptRoute(
        route_id=route_id, route_kind="FILE_IMPORT", source_manifest_id="sm-file",
        origin_family="GONG", native_call_or_meeting_id="gong-call-1", deal_source_id="deal-1",
        started_at=NOW, ended_at=END, segments=tuple(segments),
    )


# -- Scenario J: cross-route dedup via direct Gong + file import --------------------


def test_scenario_j_direct_gong_plus_file_resolve_to_one_origin() -> None:
    direct = _direct_route(SENTINEL)
    # Same call, same content -> file route must match the direct content hash.
    direct_texts = [seg.text for seg in direct.segments]
    imported = _file_route(direct_texts)
    assert normalized_content_hash(direct.segments) == normalized_content_hash(imported.segments)

    result = stage_transcripts_in_memory(
        lane=LaneV1.ASSIGNMENT_RECOMMENDATION, routes=(imported, direct),
        exact_deal_source_ids=frozenset({"deal-1"}),
    )
    assert len(result.metadata) == len(result.analyzed_origin_ids) == 1
    # Direct Gong metadata is authoritative; the file route is a duplicate lineage edge.
    assert result.authoritative_source_manifest_ids == ("sm-direct",)
    assert result.duplicate_edges[0].reason == "SAME_NATIVE_ID_AND_CONTENT_HASH"
    assert result.conflicts == ()
    assert "text" not in result.metadata[0].model_dump()


def test_scenario_j_same_id_different_hash_blocks() -> None:
    direct = _direct_route(SENTINEL)
    conflicting = _file_route(["completely different fictional content"])
    result = stage_transcripts_in_memory(
        lane=LaneV1.DEAL_PRIORITIZATION, routes=(direct, conflicting),
        exact_deal_source_ids=frozenset({"deal-1"}),
    )
    assert result.metadata == ()  # neither is analyzed until Kevin chooses
    assert result.conflicts[0].reason == "CONVERSATION_ORIGIN_CONFLICT"


def test_conversation_origin_v1_crosswalk_key_matches_across_routes() -> None:
    direct = _direct_route(SENTINEL)
    imported = _file_route([seg.text for seg in direct.segments])
    origin_direct = conversation_origin_for_route(direct)
    origin_file = conversation_origin_for_route(imported)
    assert isinstance(origin_direct, ConversationOriginV1)
    assert origin_direct.crosswalk_key() == origin_file.crosswalk_key()
    assert origin_direct.source_family == "GONG"
    # ConversationOriginV1 has no text field; it is an ephemeral key only.
    assert "text" not in origin_direct.model_dump()


# -- Scenario H: additive transcript privacy/evidence ------------------------------


def test_scenario_h_additive_evidence_attaches_only_by_exact_crosswalk() -> None:
    direct = _direct_route(SENTINEL)
    # exact crosswalk required
    with pytest.raises(TranscriptStageError, match="exact approved deal crosswalk"):
        stage_transcripts_in_memory(
            lane=LaneV1.DEAL_PRIORITIZATION, routes=(direct,),
            exact_deal_source_ids=frozenset({"some-other-deal"}),
        )
    result = stage_transcripts_in_memory(
        lane=LaneV1.DEAL_PRIORITIZATION, routes=(direct,),
        exact_deal_source_ids=frozenset({"deal-1"}),
    )
    metadata = result.metadata[0]
    assert metadata.deal_source_id == "deal-1"
    # No standalone conversation deliverable: only metadata + roles survive.
    dumped = metadata.model_dump()
    assert "text" not in dumped
    assert metadata.speaker_role_counts == {"CUSTOMER": 1, "INTERNAL": 1, "UNKNOWN": 0}
    # No employee/candidate/sentiment output field exists on the durable record.
    assert set(dumped) == {
        "schema_version", "conversation_origin_id", "source_family", "native_call_or_meeting_id",
        "deal_source_id", "transcript_content_sha256", "started_at", "ended_at",
        "speaker_role_counts", "cited_excerpt_ids",
    }
    # Sentiment-like language never becomes a durable field.
    assert "excited" not in json.dumps(dumped, default=str)


def test_scenario_h_conversation_not_consumed_by_capacity_lane() -> None:
    direct = _direct_route(SENTINEL)
    with pytest.raises(TranscriptStageError, match="not consumed by Capacity"):
        stage_transcripts_in_memory(
            lane=LaneV1.CAPACITY_HEATMAP, routes=(direct,),
            exact_deal_source_ids=frozenset({"deal-1"}),
        )


# -- Sentinel scan: both routes leave no full transcript text durable --------------


def _persist_and_scan(tmp_path: Path, route: TranscriptRoute, *, run_id: str) -> tuple:
    app_dir = tmp_path / f"artifacts-{run_id}"
    app_dir.mkdir()
    database = app_dir / "state.sqlite"
    connection = connect_database(database)
    apply_migrations(connection)
    connection.execute("PRAGMA journal_mode = WAL")
    store = Phase1Store(connection)
    store.create_run(run_id=run_id, lane=LaneV1.ASSIGNMENT_RECOMMENDATION, synthetic=False, created_at=NOW)
    connection.execute(
        "INSERT INTO source_manifests(source_manifest_id, run_id, source_instance_id, adapter_id, source_mode, manifest_json, manifest_sha256) "
        "VALUES (?, ?, ?, 'gong-api-v2', 'DIRECT_CONNECTOR', '{}', ?)",
        (route.source_manifest_id, run_id, f"src-{route.source_manifest_id}", "a" * 64),
    )
    connection.commit()
    result = stage_transcripts_in_memory(
        lane=LaneV1.ASSIGNMENT_RECOMMENDATION, routes=(route,),
        exact_deal_source_ids=frozenset({"deal-1"}),
    )
    store.persist_conversation_metadata(
        run_id=run_id, source_manifest_id=route.source_manifest_id, metadata=result.metadata[0],
    )
    store.create_backup(app_dir / "state.backup.sqlite")
    write_metadata_only_crash_artifact(
        app_dir / "crash.json", occurred_at=NOW, reason_code="TRANSCRIPT_STAGE_ABORTED", run_id=run_id,
    )
    (app_dir / "app.log").write_text("gong transcript stage complete; metadata only\n", encoding="utf-8")
    matches = scan_artifacts_for_sentinel((app_dir,), SENTINEL)
    connection.close()
    return matches, result


def test_both_transcript_routes_leave_no_full_text_in_db_wal_backup_crash(tmp_path: Path) -> None:
    # Direct Gong route
    direct = _direct_route(SENTINEL)
    direct_matches, direct_result = _persist_and_scan(tmp_path, direct, run_id="run-direct")
    assert direct_matches == ()
    assert direct_result.metadata[0].transcript_content_sha256 != ""

    # File-import route with identical content (same origin family GONG)
    imported = _file_route([seg.text for seg in direct.segments], route_id="gong-file")
    file_matches, _ = _persist_and_scan(tmp_path, imported, run_id="run-file")
    assert file_matches == ()
