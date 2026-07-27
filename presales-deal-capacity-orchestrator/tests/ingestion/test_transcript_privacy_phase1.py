from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from orchestrator.contracts.enums import LaneV1
from orchestrator.contracts.records import ConversationSegmentV1
from orchestrator.ingestion.transcripts import TranscriptRoute, stage_transcripts_in_memory
from orchestrator.retention import RetainedCitedExcerptV1, scan_artifacts_for_sentinel, write_metadata_only_crash_artifact
from orchestrator.store import Phase1Store, apply_migrations, connect_database

NOW = datetime(2026, 8, 3, 9, tzinfo=timezone.utc)
SENTINEL = "PHASE1_SENTINEL full private transcript residency delighted 91d6d2"


def segment(*, route: str, text: str = SENTINEL) -> ConversationSegmentV1:
    return ConversationSegmentV1(
        schema_version="orchestrator.conversation-segment.v1",
        conversation_id=f"conv-{route}", deal_source_id="deal-1", segment_id=f"seg-{route}",
        speaker_ref="CUSTOMER", speaker_source_label="fictional-customer",
        occurred_at=NOW, relative_begin_ms=10, relative_end_ms=20, text=text,
        source_record_id=f"source-{route}", text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        lineage_receipt_id=f"lineage-{route}",
    )


def test_scenario_j_cross_route_duplicate_analyzes_once_and_conflict_blocks() -> None:
    direct = TranscriptRoute(
        route_id="direct-gong", route_kind="DIRECT_REPLAY", source_manifest_id="sm-direct",
        origin_family="GONG", native_call_or_meeting_id="gong-call-1", deal_source_id="deal-1",
        started_at=NOW, ended_at=NOW, segments=(segment(route="direct"),),
    )
    imported = TranscriptRoute(
        route_id="gong-file", route_kind="FILE_IMPORT", source_manifest_id="sm-file",
        origin_family="GONG", native_call_or_meeting_id="gong-call-1", deal_source_id="deal-1",
        started_at=NOW, ended_at=NOW, segments=(segment(route="file"),),
    )
    result = stage_transcripts_in_memory(
        lane=LaneV1.DEAL_PRIORITIZATION, routes=(imported, direct),
        exact_deal_source_ids=frozenset({"deal-1"}),
    )
    assert len(result.metadata) == len(result.analyzed_origin_ids) == 1
    assert result.authoritative_source_manifest_ids == ("sm-direct",)
    assert result.duplicate_edges[0].reason == "SAME_NATIVE_ID_AND_CONTENT_HASH"
    assert result.conflicts == ()
    assert "text" not in result.metadata[0].model_dump()

    conflicting_file = TranscriptRoute(
        **{**imported.__dict__, "segments": (segment(route="conflict", text="different fictional content"),)}
    )
    conflict = stage_transcripts_in_memory(
        lane=LaneV1.ASSIGNMENT_RECOMMENDATION, routes=(direct, conflicting_file),
        exact_deal_source_ids=frozenset({"deal-1"}),
    )
    assert conflict.metadata == ()
    assert conflict.conflicts[0].reason == "CONVERSATION_ORIGIN_CONFLICT"


def test_db_wal_backup_crash_artifact_transcript_sentinel_scan(tmp_path: Path) -> None:
    app_dir = tmp_path / "app-artifacts"
    app_dir.mkdir()
    database = app_dir / "state.sqlite"
    connection = connect_database(database)
    apply_migrations(connection)
    connection.execute("PRAGMA journal_mode = WAL")
    store = Phase1Store(connection)
    store.create_run(run_id="run-privacy", lane=LaneV1.DEAL_PRIORITIZATION, synthetic=False, created_at=NOW)
    for manifest_id in ("sm-direct", "sm-file"):
        connection.execute(
            "INSERT INTO source_manifests(source_manifest_id, run_id, source_instance_id, adapter_id, source_mode, manifest_json, manifest_sha256) "
            "VALUES (?, 'run-privacy', ?, 'gong-file-v1', 'FILE_IMPORT', '{}', ?)",
            (manifest_id, f"src-{manifest_id}", "a" * 64),
        )
    connection.commit()

    route = TranscriptRoute(
        route_id="gong-file", route_kind="FILE_IMPORT", source_manifest_id="sm-file",
        origin_family="GONG", native_call_or_meeting_id="gong-call-private", deal_source_id="deal-1",
        started_at=NOW, ended_at=NOW, segments=(segment(route="privacy"),),
    )
    cancelled = stage_transcripts_in_memory(
        lane=LaneV1.ASSIGNMENT_RECOMMENDATION, routes=(route,),
        exact_deal_source_ids=frozenset({"deal-1"}), cancel_requested=True,
    )
    assert cancelled.metadata == ()
    result = stage_transcripts_in_memory(
        lane=LaneV1.ASSIGNMENT_RECOMMENDATION, routes=(route,),
        exact_deal_source_ids=frozenset({"deal-1"}),
    )
    store.persist_conversation_metadata(
        run_id="run-privacy", source_manifest_id="sm-file", metadata=result.metadata[0]
    )
    expected_hash = hashlib.sha256(SENTINEL.encode()).hexdigest()
    assert connection.execute(
        "SELECT content_sha256 FROM conversation_evidence_metadata"
    ).fetchone() == (expected_hash,)
    approved_excerpt = "private transcript"
    excerpt_begin = SENTINEL.index(approved_excerpt)
    store.persist_retention_approved_excerpt(RetainedCitedExcerptV1(
        schema_version="orchestrator.retained-cited-excerpt.v1", excerpt_id="excerpt-1",
        conversation_origin_id=result.metadata[0].conversation_origin_id,
        excerpt=approved_excerpt, quote_sha256=hashlib.sha256(approved_excerpt.encode()).hexdigest(),
        char_begin=excerpt_begin, char_end=excerpt_begin + len(approved_excerpt),
        expires_at=NOW + timedelta(days=1), retention_approved_at=NOW,
    ))
    assert connection.execute("SELECT excerpt_utf8 FROM cited_excerpts").fetchone() == (approved_excerpt,)

    store.create_backup(app_dir / "state.backup.sqlite")
    write_metadata_only_crash_artifact(
        app_dir / "crash.json", occurred_at=NOW, reason_code="TRANSCRIPT_STAGE_ABORTED", run_id="run-privacy"
    )
    (app_dir / "app.log").write_text("transcript stage aborted; metadata only\n", encoding="utf-8")
    (app_dir / "export.json").write_text('{"transcript_content_sha256":"' + expected_hash + '"}', encoding="utf-8")

    assert scan_artifacts_for_sentinel((app_dir,), SENTINEL) == ()
    connection.close()
