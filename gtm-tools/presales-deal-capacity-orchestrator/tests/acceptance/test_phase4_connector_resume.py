from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from orchestrator.canonical import canonical_sha256
from orchestrator.contracts.enums import LaneV1, SourceModeV1
from orchestrator.store import apply_migrations, connect_database
from orchestrator.workflow import SourceRunStateV1, WorkflowStore

NOW = datetime(2026, 8, 2, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("adapter_id", "source_run_id", "overlap_seconds", "fake_token", "raw_cursor"),
    [
        ("salesforce-rest-v1", "sr-salesforce", 300, "fake-salesforce-resume-token", "/query/vendor-secret-cursor"),
        ("clickup-api-v2", "sr-clickup", 120, "fake-clickup-resume-token", "vendor-page-17"),
    ],
)
def test_each_connector_cross_process_resume_reenters_credentials_overlaps_and_deduplicates(
    tmp_path: Path,
    adapter_id: str,
    source_run_id: str,
    overlap_seconds: int,
    fake_token: str,
    raw_cursor: str,
) -> None:
    database = tmp_path / f"{adapter_id}.sqlite"
    connection = connect_database(database)
    apply_migrations(connection)
    workflow = WorkflowStore(connection)
    run_id = f"run-{adapter_id}"
    manifest_id = f"sm-{adapter_id}"
    workflow.create_run(run_id=run_id, lane=LaneV1.ASSIGNMENT_RECOMMENDATION, synthetic=True, created_at=NOW)
    manifest = {
        "run_id": run_id,
        "source_manifest_id": manifest_id,
        "adapter_id": adapter_id,
        "source_mode": "DIRECT_CONNECTOR",
    }
    connection.execute(
        "INSERT INTO source_manifests(source_manifest_id,run_id,source_instance_id,adapter_id,source_mode,manifest_json,manifest_sha256) VALUES (?,?,?,?,?,?,?)",
        (manifest_id, run_id, f"src-{adapter_id}", adapter_id, SourceModeV1.DIRECT_CONNECTOR,
         json.dumps(manifest, sort_keys=True), canonical_sha256(manifest)),
    )
    connection.commit()
    workflow.start_source_run(
        source_run_id=source_run_id,
        run_id=run_id,
        source_manifest_id=manifest_id,
        source_mode=SourceModeV1.DIRECT_CONNECTOR,
        overlap_seconds=overlap_seconds,
        created_at=NOW,
    )
    for state in (SourceRunStateV1.PREFLIGHTED, SourceRunStateV1.READY, SourceRunStateV1.READING):
        workflow.transition_source(
            source_run_id=source_run_id,
            new_state=state,
            actor_type="SYSTEM",
            reason_code=f"ENTER-{state}",
            created_at=NOW,
        )
    cursor_hash = hashlib.sha256(raw_cursor.encode()).hexdigest()
    workflow.commit_source_checkpoint(
        checkpoint_id=f"cp-{adapter_id}-1",
        source_run_id=source_run_id,
        page_number=1,
        cursor_sha256=cursor_hash,
        high_water_mark=NOW,
        local_file_offset=None,
        staged_record_versions=((f"urn:{adapter_id}:record-1", "version-1"),),
        committed_at=NOW,
    )
    connection.close()

    raw_database = database.read_bytes()
    assert raw_cursor.encode() not in raw_database
    assert fake_token.encode() not in raw_database
    assert cursor_hash.encode() in raw_database

    resumed_connection = connect_database(database)
    resumed = WorkflowStore(resumed_connection)
    plan = resumed.source_resume_plan(source_run_id)
    assert plan.credential_reentry_required is True
    assert plan.restart_high_water == NOW - timedelta(seconds=overlap_seconds)
    assert plan.durable_cursor_present is False
    accepted, duplicates = resumed.commit_source_checkpoint(
        checkpoint_id=f"cp-{adapter_id}-2",
        source_run_id=source_run_id,
        page_number=2,
        cursor_sha256=hashlib.sha256(b"new-memory-only-cursor").hexdigest(),
        high_water_mark=NOW + timedelta(minutes=1),
        local_file_offset=None,
        staged_record_versions=(
            (f"urn:{adapter_id}:record-1", "version-1"),
            (f"urn:{adapter_id}:record-1", "version-2"),
            (f"urn:{adapter_id}:record-2", "version-1"),
        ),
        committed_at=NOW + timedelta(minutes=1),
    )
    assert duplicates == (f"urn:{adapter_id}:record-1",)
    assert accepted == (f"urn:{adapter_id}:record-1", f"urn:{adapter_id}:record-2")
    resumed_connection.close()
