from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from orchestrator.canonical import canonical_sha256
from orchestrator.contracts.enums import LaneV1, SourceModeV1
from orchestrator.store import apply_migrations, connect_database
from orchestrator.workflow import (
    WorkflowStateV1,
    WorkflowStore,
    allowed_transitions,
)

NOW = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)


def test_all_23_enumerated_states_and_every_lane_transition_are_exercised(tmp_path: Path) -> None:
    assert len(WorkflowStateV1) == 23
    all_edges: set[tuple[WorkflowStateV1, WorkflowStateV1]] = set()
    touched: set[WorkflowStateV1] = set()
    connection = connect_database(tmp_path / "all-transitions.sqlite")
    apply_migrations(connection)
    workflow = WorkflowStore(connection)
    counter = 0
    for lane in LaneV1:
        for prior, new in sorted(allowed_transitions(lane), key=lambda edge: (edge[0].value, edge[1].value)):
            counter += 1
            run_id = f"run-transition-{counter}"
            workflow.create_run(run_id=run_id, lane=lane, synthetic=True, created_at=NOW)
            connection.execute("UPDATE runs SET state = ? WHERE run_id = ?", (prior, run_id))
            connection.commit()
            workflow.transition(
                run_id=run_id, new_state=new, actor_type="TEST",
                reason_code=f"COVER-{prior}-{new}", created_at=NOW,
            )
            assert connection.execute("SELECT state FROM runs WHERE run_id = ?", (run_id,)).fetchone()[0] == new
            all_edges.add((prior, new))
            touched.update((prior, new))
    assert touched == set(WorkflowStateV1)
    assert all_edges == set().union(*(allowed_transitions(lane) for lane in LaneV1))
    assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == counter
    connection.close()


def test_top_level_restart_reentry_resumes_committed_event_high_water(tmp_path: Path) -> None:
    database = tmp_path / "workflow-restart.sqlite"
    connection = connect_database(database)
    apply_migrations(connection)
    workflow = WorkflowStore(connection)
    workflow.create_run(run_id="run-restart", lane=LaneV1.DEAL_PRIORITIZATION, synthetic=True, created_at=NOW)
    path = (
        WorkflowStateV1.AUTHORITY_ATTESTED,
        WorkflowStateV1.SOURCE_CONFIGURED,
        WorkflowStateV1.SOURCE_PREFLIGHTED,
        WorkflowStateV1.SAMPLE_PREVIEWED,
        WorkflowStateV1.MAPPING_REVIEW_REQUIRED,
        WorkflowStateV1.MAPPING_ACCEPTED,
        WorkflowStateV1.INGESTING,
        WorkflowStateV1.INGESTED_PARTIAL,
        WorkflowStateV1.DATA_HEALTH_REVIEW,
        WorkflowStateV1.INPUT_VALIDATED,
    )
    for state in path:
        workflow.transition(
            run_id="run-restart", new_state=state, actor_type="SYSTEM",
            reason_code=f"ENTER-{state}", created_at=NOW,
        )
    connection.close()

    resumed_connection = connect_database(database)
    apply_migrations(resumed_connection)
    resumed = WorkflowStore(resumed_connection)
    assert resumed.resume_run("run-restart") is WorkflowStateV1.INPUT_VALIDATED
    resumed.transition(
        run_id="run-restart", new_state=WorkflowStateV1.EVIDENCE_READY,
        actor_type="MANAGER", reason_code="REENTRY-CONTINUE", created_at=NOW + timedelta(seconds=1),
    )
    assert resumed.resume_run("run-restart") is WorkflowStateV1.EVIDENCE_READY
    rows = list(resumed_connection.execute(
        "SELECT sequence_number, prior_event_sha256, event_sha256 FROM events WHERE run_id = ? ORDER BY sequence_number",
        ("run-restart",),
    ))
    assert [row[0] for row in rows] == list(range(1, len(rows) + 1))
    assert all(rows[index][1] == rows[index - 1][2] for index in range(1, len(rows)))
    resumed_connection.close()


def _insert_manifest(connection: object, *, run_id: str, manifest_id: str, mode: SourceModeV1) -> None:
    payload = {
        "schema_version": "synthetic-test-manifest",
        "source_manifest_id": manifest_id,
        "run_id": run_id,
        "source_mode": mode,
    }
    connection.execute(  # type: ignore[attr-defined]
        "INSERT INTO source_manifests(source_manifest_id, run_id, source_instance_id, adapter_id, source_mode, "
        "manifest_json, manifest_sha256) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (manifest_id, run_id, f"source-{manifest_id}", "synthetic-adapter", mode,
         json.dumps(payload, sort_keys=True), canonical_sha256(payload)),
    )
    connection.commit()  # type: ignore[attr-defined]


def _advance_source_to_reading(workflow: WorkflowStore, source_run_id: str) -> None:
    from orchestrator.workflow import SourceRunStateV1

    for state in (SourceRunStateV1.PREFLIGHTED, SourceRunStateV1.READY, SourceRunStateV1.READING):
        workflow.transition_source(
            source_run_id=source_run_id, new_state=state,
            actor_type="SYSTEM", reason_code=f"SOURCE-{state}", created_at=NOW,
        )


def test_cross_process_direct_resume_uses_overlap_requires_reentry_and_deduplicates(tmp_path: Path) -> None:
    database = tmp_path / "source-restart.sqlite"
    connection = connect_database(database)
    apply_migrations(connection)
    workflow = WorkflowStore(connection)
    workflow.create_run(run_id="run-source", lane=LaneV1.DEAL_PRIORITIZATION, synthetic=True, created_at=NOW)
    _insert_manifest(connection, run_id="run-source", manifest_id="sm-direct", mode=SourceModeV1.DIRECT_CONNECTOR)
    workflow.start_source_run(
        source_run_id="source-run-direct", run_id="run-source", source_manifest_id="sm-direct",
        source_mode=SourceModeV1.DIRECT_CONNECTOR, overlap_seconds=300, created_at=NOW,
    )
    _advance_source_to_reading(workflow, "source-run-direct")
    accepted, duplicates = workflow.commit_source_checkpoint(
        checkpoint_id="checkpoint-1", source_run_id="source-run-direct", page_number=1,
        cursor_sha256="c" * 64, high_water_mark=NOW, local_file_offset=None,
        staged_record_versions=(("urn:record:1", "version-1"),), committed_at=NOW,
    )
    assert accepted == ("urn:record:1",) and duplicates == ()
    connection.close()

    resumed_connection = connect_database(database)
    resumed = WorkflowStore(resumed_connection)
    plan = resumed.source_resume_plan("source-run-direct")
    assert plan.credential_reentry_required
    assert plan.restart_high_water == NOW - timedelta(seconds=300)
    assert plan.committed_page_number == 1
    assert plan.durable_cursor_present is False
    accepted, duplicates = resumed.commit_source_checkpoint(
        checkpoint_id="checkpoint-2", source_run_id="source-run-direct", page_number=2,
        cursor_sha256="d" * 64, high_water_mark=NOW + timedelta(minutes=1), local_file_offset=None,
        staged_record_versions=(
            ("urn:record:1", "version-1"),
            ("urn:record:1", "version-2"),
            ("urn:record:2", "version-1"),
        ),
        committed_at=NOW + timedelta(minutes=1),
    )
    assert duplicates == ("urn:record:1",)
    assert accepted == ("urn:record:1", "urn:record:2")
    assert resumed.resume_run("run-source") is WorkflowStateV1.NEW
    resumed_connection.close()


def test_file_resume_uses_committed_offset_without_credentials(tmp_path: Path) -> None:
    connection = connect_database(tmp_path / "file-restart.sqlite")
    apply_migrations(connection)
    workflow = WorkflowStore(connection)
    workflow.create_run(run_id="run-file", lane=LaneV1.DEAL_PRIORITIZATION, synthetic=True, created_at=NOW)
    _insert_manifest(connection, run_id="run-file", manifest_id="sm-file", mode=SourceModeV1.FILE_IMPORT)
    workflow.start_source_run(
        source_run_id="source-run-file", run_id="run-file", source_manifest_id="sm-file",
        source_mode=SourceModeV1.FILE_IMPORT, overlap_seconds=0, created_at=NOW,
    )
    _advance_source_to_reading(workflow, "source-run-file")
    workflow.commit_source_checkpoint(
        checkpoint_id="file-checkpoint", source_run_id="source-run-file", page_number=1,
        cursor_sha256=None, high_water_mark=None, local_file_offset=4096,
        staged_record_versions=(("urn:file:row:1", "hash-1"),), committed_at=NOW,
    )
    plan = workflow.source_resume_plan("source-run-file")
    assert not plan.credential_reentry_required
    assert plan.local_file_offset == 4096
    connection.close()


def test_resume_detects_event_tampering_and_transition_rejects_uncommitted_artifact(tmp_path: Path) -> None:
    connection = connect_database(tmp_path / "tamper.sqlite")
    apply_migrations(connection)
    workflow = WorkflowStore(connection)
    workflow.create_run(run_id="run-tamper", lane=LaneV1.DEAL_PRIORITIZATION, synthetic=True, created_at=NOW)
    with pytest.raises(ValueError, match="not committed"):
        workflow.transition(
            run_id="run-tamper", new_state=WorkflowStateV1.AUTHORITY_ATTESTED,
            actor_type="SYSTEM", reason_code="BAD-ARTIFACT", created_at=NOW,
            committed_artifact_sha256="e" * 64,
        )
    workflow.transition(
        run_id="run-tamper", new_state=WorkflowStateV1.AUTHORITY_ATTESTED,
        actor_type="SYSTEM", reason_code="VALID", created_at=NOW,
    )
    connection.execute("UPDATE events SET reason_code = 'TAMPERED' WHERE run_id = 'run-tamper'")
    connection.commit()
    with pytest.raises(ValueError, match="content hash mismatch"):
        workflow.resume_run("run-tamper")
    connection.close()
