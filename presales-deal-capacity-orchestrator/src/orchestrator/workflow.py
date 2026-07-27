from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator

from .canonical import canonical_json_bytes, canonical_sha256
from .contracts.base import Identifier, Sha256, StrictContract, require_offset_aware
from .contracts.domain import (
    ConsultantFitReceiptV2,
    EligibilityReceiptV2,
    PriorityBlockedReceiptV2,
    PriorityReceiptV2,
    ReadinessReceiptV2,
    WeeklyCapacityReceiptV1,
)
from .contracts.enums import LaneV1, SourceModeV1


class WorkflowStateV1(StrEnum):
    NEW = "NEW"
    AUTHORITY_ATTESTED = "AUTHORITY_ATTESTED"
    SOURCE_CONFIGURED = "SOURCE_CONFIGURED"
    SOURCE_PREFLIGHTED = "SOURCE_PREFLIGHTED"
    SAMPLE_PREVIEWED = "SAMPLE_PREVIEWED"
    MAPPING_REVIEW_REQUIRED = "MAPPING_REVIEW_REQUIRED"
    MAPPING_ACCEPTED = "MAPPING_ACCEPTED"
    INGESTING = "INGESTING"
    INGESTED = "INGESTED"
    INGESTED_PARTIAL = "INGESTED_PARTIAL"
    DATA_HEALTH_REVIEW = "DATA_HEALTH_REVIEW"
    INPUT_VALIDATED = "INPUT_VALIDATED"
    EVIDENCE_READY = "EVIDENCE_READY"
    READINESS_COMPUTED = "READINESS_COMPUTED"
    QUEUE_SCORED = "QUEUE_SCORED"
    ASSIGNMENT_SOLVED = "ASSIGNMENT_SOLVED"
    CAPACITY_COMPUTED = "CAPACITY_COMPUTED"
    SCENARIO_COMPUTED = "SCENARIO_COMPUTED"
    DIGEST_VALIDATED = "DIGEST_VALIDATED"
    DIGEST_FALLBACK = "DIGEST_FALLBACK"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    EXPORT_READY = "EXPORT_READY"
    CLOSED = "CLOSED"


class SourceRunStateV1(StrEnum):
    PENDING = "PENDING"
    PREFLIGHTED = "PREFLIGHTED"
    MAPPING_REQUIRED = "MAPPING_REQUIRED"
    READY = "READY"
    READING = "READING"
    RATE_LIMITED = "RATE_LIMITED"
    RETRY_WAIT = "RETRY_WAIT"
    COMPLETE = "COMPLETE"
    BOUNDED_PARTIAL = "BOUNDED_PARTIAL"
    AUTH_FAILED = "AUTH_FAILED"
    SOURCE_FAILED = "SOURCE_FAILED"
    CANCELLED = "CANCELLED"


_COMMON_TRANSITIONS = {
    (WorkflowStateV1.NEW, WorkflowStateV1.AUTHORITY_ATTESTED),
    (WorkflowStateV1.AUTHORITY_ATTESTED, WorkflowStateV1.SOURCE_CONFIGURED),
    (WorkflowStateV1.SOURCE_CONFIGURED, WorkflowStateV1.SOURCE_PREFLIGHTED),
    (WorkflowStateV1.SOURCE_PREFLIGHTED, WorkflowStateV1.SAMPLE_PREVIEWED),
    (WorkflowStateV1.SAMPLE_PREVIEWED, WorkflowStateV1.MAPPING_REVIEW_REQUIRED),
    (WorkflowStateV1.MAPPING_REVIEW_REQUIRED, WorkflowStateV1.MAPPING_ACCEPTED),
    (WorkflowStateV1.MAPPING_ACCEPTED, WorkflowStateV1.INGESTING),
    (WorkflowStateV1.INGESTING, WorkflowStateV1.INGESTED),
    (WorkflowStateV1.INGESTING, WorkflowStateV1.INGESTED_PARTIAL),
    (WorkflowStateV1.INGESTED, WorkflowStateV1.DATA_HEALTH_REVIEW),
    (WorkflowStateV1.INGESTED_PARTIAL, WorkflowStateV1.DATA_HEALTH_REVIEW),
    (WorkflowStateV1.DATA_HEALTH_REVIEW, WorkflowStateV1.INPUT_VALIDATED),
    (WorkflowStateV1.DIGEST_VALIDATED, WorkflowStateV1.REVIEW_REQUIRED),
    (WorkflowStateV1.DIGEST_FALLBACK, WorkflowStateV1.REVIEW_REQUIRED),
    (WorkflowStateV1.REVIEW_REQUIRED, WorkflowStateV1.EXPORT_READY),
    (WorkflowStateV1.EXPORT_READY, WorkflowStateV1.CLOSED),
}
_DEAL_TRANSITIONS = {
    (WorkflowStateV1.INPUT_VALIDATED, WorkflowStateV1.EVIDENCE_READY),
    (WorkflowStateV1.EVIDENCE_READY, WorkflowStateV1.READINESS_COMPUTED),
    (WorkflowStateV1.READINESS_COMPUTED, WorkflowStateV1.QUEUE_SCORED),
    (WorkflowStateV1.QUEUE_SCORED, WorkflowStateV1.DIGEST_VALIDATED),
    (WorkflowStateV1.QUEUE_SCORED, WorkflowStateV1.DIGEST_FALLBACK),
}
_ASSIGNMENT_TRANSITIONS = {
    (WorkflowStateV1.INPUT_VALIDATED, WorkflowStateV1.EVIDENCE_READY),
    (WorkflowStateV1.EVIDENCE_READY, WorkflowStateV1.READINESS_COMPUTED),
    (WorkflowStateV1.READINESS_COMPUTED, WorkflowStateV1.QUEUE_SCORED),
    (WorkflowStateV1.QUEUE_SCORED, WorkflowStateV1.ASSIGNMENT_SOLVED),
    (WorkflowStateV1.ASSIGNMENT_SOLVED, WorkflowStateV1.DIGEST_VALIDATED),
    (WorkflowStateV1.ASSIGNMENT_SOLVED, WorkflowStateV1.DIGEST_FALLBACK),
}
_CAPACITY_TRANSITIONS = {
    (WorkflowStateV1.INPUT_VALIDATED, WorkflowStateV1.CAPACITY_COMPUTED),
    (WorkflowStateV1.CAPACITY_COMPUTED, WorkflowStateV1.SCENARIO_COMPUTED),
    (WorkflowStateV1.SCENARIO_COMPUTED, WorkflowStateV1.DIGEST_VALIDATED),
    (WorkflowStateV1.SCENARIO_COMPUTED, WorkflowStateV1.DIGEST_FALLBACK),
}


def allowed_transitions(lane: LaneV1) -> frozenset[tuple[WorkflowStateV1, WorkflowStateV1]]:
    branch = {
        LaneV1.DEAL_PRIORITIZATION: _DEAL_TRANSITIONS,
        LaneV1.ASSIGNMENT_RECOMMENDATION: _ASSIGNMENT_TRANSITIONS,
        LaneV1.CAPACITY_HEATMAP: _CAPACITY_TRANSITIONS,
    }[lane]
    return frozenset(_COMMON_TRANSITIONS | branch)


_SOURCE_TRANSITIONS = frozenset({
    (SourceRunStateV1.PENDING, SourceRunStateV1.PREFLIGHTED),
    (SourceRunStateV1.PENDING, SourceRunStateV1.AUTH_FAILED),
    (SourceRunStateV1.PENDING, SourceRunStateV1.CANCELLED),
    (SourceRunStateV1.PREFLIGHTED, SourceRunStateV1.MAPPING_REQUIRED),
    (SourceRunStateV1.PREFLIGHTED, SourceRunStateV1.READY),
    (SourceRunStateV1.MAPPING_REQUIRED, SourceRunStateV1.READY),
    (SourceRunStateV1.READY, SourceRunStateV1.READING),
    (SourceRunStateV1.READING, SourceRunStateV1.RATE_LIMITED),
    (SourceRunStateV1.READING, SourceRunStateV1.RETRY_WAIT),
    (SourceRunStateV1.READING, SourceRunStateV1.COMPLETE),
    (SourceRunStateV1.READING, SourceRunStateV1.BOUNDED_PARTIAL),
    (SourceRunStateV1.READING, SourceRunStateV1.AUTH_FAILED),
    (SourceRunStateV1.READING, SourceRunStateV1.SOURCE_FAILED),
    (SourceRunStateV1.READING, SourceRunStateV1.CANCELLED),
    (SourceRunStateV1.RATE_LIMITED, SourceRunStateV1.RETRY_WAIT),
    (SourceRunStateV1.RATE_LIMITED, SourceRunStateV1.SOURCE_FAILED),
    (SourceRunStateV1.RATE_LIMITED, SourceRunStateV1.CANCELLED),
    (SourceRunStateV1.RETRY_WAIT, SourceRunStateV1.READING),
    (SourceRunStateV1.RETRY_WAIT, SourceRunStateV1.SOURCE_FAILED),
    (SourceRunStateV1.RETRY_WAIT, SourceRunStateV1.CANCELLED),
    (SourceRunStateV1.BOUNDED_PARTIAL, SourceRunStateV1.READING),
    (SourceRunStateV1.AUTH_FAILED, SourceRunStateV1.PENDING),
})


class ResumePlanV1(StrictContract):
    source_run_id: Identifier
    source_mode: SourceModeV1
    credential_reentry_required: bool
    restart_high_water: datetime | None
    local_file_offset: int | None = Field(default=None, ge=0)
    committed_page_number: int = Field(ge=0)
    durable_cursor_present: Literal[False]

    @field_validator("restart_high_water")
    @classmethod
    def aware_restart(cls, value: datetime | None) -> datetime | None:
        return require_offset_aware(value) if value is not None else None


DomainReceipt = (
    ReadinessReceiptV2
    | PriorityReceiptV2
    | PriorityBlockedReceiptV2
    | WeeklyCapacityReceiptV1
    | EligibilityReceiptV2
    | ConsultantFitReceiptV2
)
_RECEIPT_KIND = {
    ReadinessReceiptV2: ("READINESS", "readiness_receipt_id"),
    PriorityReceiptV2: ("PRIORITY", "priority_receipt_id"),
    PriorityBlockedReceiptV2: ("PRIORITY_BLOCKED", None),
    WeeklyCapacityReceiptV1: ("WEEKLY_CAPACITY", "capacity_receipt_id"),
    EligibilityReceiptV2: ("ELIGIBILITY", "eligibility_receipt_id"),
    ConsultantFitReceiptV2: ("CONSULTANT_FIT", "fit_receipt_id"),
}


class WorkflowStore:
    """SQLite-checkpointed workflow with additive hash-chained events."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_run(self, *, run_id: str, lane: LaneV1, synthetic: bool, created_at: datetime) -> None:
        self.connection.execute(
            "INSERT INTO runs(run_id, lane, state, synthetic, created_at) VALUES (?, ?, 'NEW', ?, ?)",
            (run_id, lane, int(synthetic), created_at.isoformat()),
        )
        self.connection.commit()

    def persist_domain_receipt(self, receipt: DomainReceipt, *, created_at: datetime) -> str:
        receipt_type = type(receipt)
        if receipt_type not in _RECEIPT_KIND:
            raise TypeError("only minimized typed Phase 2 receipts can be persisted")
        kind, id_field = _RECEIPT_KIND[receipt_type]
        digest = canonical_sha256(receipt)
        receipt_id = getattr(receipt, id_field) if id_field is not None else f"priority-blocked-{digest[:32]}"
        payload = canonical_json_bytes(receipt).decode()
        self.connection.execute(
            "INSERT INTO domain_receipts(receipt_id, run_id, receipt_kind, receipt_json, receipt_sha256, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (receipt_id, receipt.run_id, kind, payload, digest, created_at.isoformat()),
        )
        self.connection.commit()
        return digest

    def _artifact_exists(self, digest: str) -> bool:
        queries = (
            ("canonical_artifacts", "artifact_sha256"),
            ("data_health_receipts", "receipt_sha256"),
            ("analyst_receipts", "receipt_sha256"),
            ("solver_receipts", "receipt_sha256"),
            ("domain_receipts", "receipt_sha256"),
        )
        return any(self.connection.execute(
            f'SELECT 1 FROM "{table}" WHERE "{column}" = ? LIMIT 1', (digest,)
        ).fetchone() for table, column in queries)

    def _append_event(
        self,
        *,
        run_id: str,
        prior_state: str,
        new_state: str,
        source_run_id: str | None,
        artifact_sha256: str | None,
        actor_type: str,
        reason_code: str,
        created_at: datetime,
    ) -> str:
        latest = self.connection.execute(
            "SELECT sequence_number, event_sha256 FROM events WHERE run_id = ? ORDER BY sequence_number DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        sequence = 1 if latest is None else latest[0] + 1
        prior_event_sha256 = None if latest is None else latest[1]
        content = {
            "run_id": run_id,
            "sequence_number": sequence,
            "prior_event_sha256": prior_event_sha256,
            "prior_state": prior_state,
            "new_state": new_state,
            "source_run_id": source_run_id,
            "artifact_sha256": artifact_sha256,
            "actor_type": actor_type,
            "reason_code": reason_code,
            "created_at": created_at.isoformat(),
        }
        event_sha256 = canonical_sha256(content)
        self.connection.execute(
            "INSERT INTO events(event_id, run_id, sequence_number, prior_event_sha256, artifact_sha256, actor_type, "
            "reason_code, created_at, prior_state, new_state, event_sha256, source_run_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (f"event-{event_sha256[:32]}", run_id, sequence, prior_event_sha256, artifact_sha256,
             actor_type, reason_code, created_at.isoformat(), prior_state, new_state, event_sha256, source_run_id),
        )
        return event_sha256

    def transition(
        self,
        *,
        run_id: str,
        new_state: WorkflowStateV1,
        actor_type: str,
        reason_code: str,
        created_at: datetime,
        committed_artifact_sha256: str | None = None,
    ) -> str:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute("SELECT lane, state FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            if row is None:
                raise KeyError("unknown run")
            lane, prior_value = LaneV1(row[0]), WorkflowStateV1(row[1])
            if (prior_value, new_state) not in allowed_transitions(lane):
                raise ValueError(f"transition {prior_value}->{new_state} is not valid for {lane}")
            if committed_artifact_sha256 is not None and not self._artifact_exists(committed_artifact_sha256):
                raise ValueError("transition artifact is not committed or its hash no longer matches")
            event_hash = self._append_event(
                run_id=run_id, prior_state=prior_value, new_state=new_state, source_run_id=None,
                artifact_sha256=committed_artifact_sha256, actor_type=actor_type,
                reason_code=reason_code, created_at=created_at,
            )
            self.connection.execute("UPDATE runs SET state = ? WHERE run_id = ?", (new_state, run_id))
            self.connection.commit()
            return event_hash
        except Exception:
            self.connection.rollback()
            raise

    def resume_run(self, run_id: str) -> WorkflowStateV1:
        row = self.connection.execute("SELECT state FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError("unknown run")
        events = list(self.connection.execute(
            "SELECT sequence_number, prior_event_sha256, artifact_sha256, actor_type, reason_code, created_at, "
            "prior_state, new_state, event_sha256, source_run_id FROM events WHERE run_id = ? ORDER BY sequence_number",
            (run_id,),
        ))
        expected_prior = None
        expected_sequence = 1
        last_state: str | None = None
        for event in events:
            (sequence, prior_hash, artifact_hash, actor, reason, created, prior_state,
             new_state, event_hash, source_run_id) = event
            if sequence != expected_sequence or prior_hash != expected_prior:
                raise ValueError("workflow event sequence/hash chain is invalid")
            content = {
                "run_id": run_id, "sequence_number": sequence, "prior_event_sha256": prior_hash,
                "prior_state": prior_state, "new_state": new_state, "source_run_id": source_run_id,
                "artifact_sha256": artifact_hash, "actor_type": actor, "reason_code": reason,
                "created_at": created,
            }
            if canonical_sha256(content) != event_hash:
                raise ValueError("workflow event content hash mismatch")
            if artifact_hash is not None and not self._artifact_exists(artifact_hash):
                raise ValueError("workflow event references a missing or changed committed artifact")
            expected_prior = event_hash
            expected_sequence += 1
            if source_run_id is None:
                last_state = new_state
        if last_state is None:
            if events:
                # Source-only events do not advance the top-level state.
                last_state = events[-1][6]
            else:
                last_state = WorkflowStateV1.NEW
        if row[0] != last_state:
            raise ValueError("run state does not match committed event high-water")
        return WorkflowStateV1(row[0])

    def start_source_run(
        self,
        *,
        source_run_id: str,
        run_id: str,
        source_manifest_id: str,
        source_mode: SourceModeV1,
        overlap_seconds: int,
        created_at: datetime,
    ) -> None:
        if source_mode is SourceModeV1.DIRECT_CONNECTOR and overlap_seconds <= 0:
            raise ValueError("direct connector resume requires an explicit source-specific overlap")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            manifest = self.connection.execute(
                "SELECT run_id, source_mode FROM source_manifests WHERE source_manifest_id = ?",
                (source_manifest_id,),
            ).fetchone()
            if manifest is None or manifest[0] != run_id or manifest[1] != source_mode:
                raise ValueError("source run is not bound to the run/manifest/mode")
            self.connection.execute(
                "INSERT INTO source_runs(source_run_id, run_id, source_manifest_id, state, completeness, source_mode, overlap_seconds) "
                "VALUES (?, ?, ?, 'PENDING', 'UNKNOWN', ?, ?)",
                (source_run_id, run_id, source_manifest_id, source_mode, overlap_seconds),
            )
            top_state = self.connection.execute("SELECT state FROM runs WHERE run_id = ?", (run_id,)).fetchone()[0]
            self._append_event(
                run_id=run_id, prior_state=top_state, new_state=top_state, source_run_id=source_run_id,
                artifact_sha256=None, actor_type="SYSTEM", reason_code="SOURCE_RUN_CREATED", created_at=created_at,
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def transition_source(
        self,
        *,
        source_run_id: str,
        new_state: SourceRunStateV1,
        actor_type: str,
        reason_code: str,
        created_at: datetime,
    ) -> None:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute(
                "SELECT run_id, state FROM source_runs WHERE source_run_id = ?", (source_run_id,)
            ).fetchone()
            if row is None:
                raise KeyError("unknown source run")
            run_id, prior = row[0], SourceRunStateV1(row[1])
            if (prior, new_state) not in _SOURCE_TRANSITIONS:
                raise ValueError(f"invalid source transition {prior}->{new_state}")
            completeness = "COMPLETE" if new_state is SourceRunStateV1.COMPLETE else (
                "BOUNDED_PARTIAL" if new_state is SourceRunStateV1.BOUNDED_PARTIAL else "UNKNOWN"
            )
            self.connection.execute(
                "UPDATE source_runs SET state = ?, completeness = ? WHERE source_run_id = ?",
                (new_state, completeness, source_run_id),
            )
            top_state = self.connection.execute("SELECT state FROM runs WHERE run_id = ?", (run_id,)).fetchone()[0]
            self._append_event(
                run_id=run_id, prior_state=top_state, new_state=top_state, source_run_id=source_run_id,
                artifact_sha256=None, actor_type=actor_type, reason_code=reason_code, created_at=created_at,
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def commit_source_checkpoint(
        self,
        *,
        checkpoint_id: str,
        source_run_id: str,
        page_number: int,
        cursor_sha256: str | None,
        high_water_mark: datetime | None,
        local_file_offset: int | None,
        staged_record_versions: tuple[tuple[str, str], ...],
        committed_at: datetime,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Commit page high-water and stable-ID/version dedup in one transaction."""
        if cursor_sha256 is not None and (len(cursor_sha256) != 64 or any(c not in "0123456789abcdef" for c in cursor_sha256)):
            raise ValueError("only a SHA-256 cursor digest may be checkpointed")
        if len(staged_record_versions) != len(set(staged_record_versions)):
            raise ValueError("a staged page contains duplicate stable ID/version pairs")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute(
                "SELECT state FROM source_runs WHERE source_run_id = ?", (source_run_id,)
            ).fetchone()
            if row is None or row[0] != SourceRunStateV1.READING:
                raise ValueError("checkpoint requires a source in READING state")
            accepted: list[str] = []
            duplicates: list[str] = []
            for source_record_id, source_version in staged_record_versions:
                inserted = self.connection.execute(
                    "INSERT OR IGNORE INTO source_checkpoint_records(source_run_id, source_record_id, source_version, page_number) "
                    "VALUES (?, ?, ?, ?)",
                    (source_run_id, source_record_id, source_version, page_number),
                ).rowcount
                (accepted if inserted else duplicates).append(source_record_id)
            self.connection.execute(
                "INSERT INTO source_checkpoints(checkpoint_id, source_run_id, page_number, cursor_sha256, high_water_mark, "
                "local_file_offset, committed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (checkpoint_id, source_run_id, page_number, cursor_sha256,
                 high_water_mark.isoformat() if high_water_mark is not None else None,
                 local_file_offset, committed_at.isoformat()),
            )
            self.connection.commit()
            return tuple(accepted), tuple(duplicates)
        except Exception:
            self.connection.rollback()
            raise

    def source_resume_plan(self, source_run_id: str) -> ResumePlanV1:
        row = self.connection.execute(
            "SELECT sr.source_mode, sr.overlap_seconds, sm.manifest_json, sm.manifest_sha256 "
            "FROM source_runs sr JOIN source_manifests sm ON sm.source_manifest_id = sr.source_manifest_id "
            "WHERE sr.source_run_id = ?",
            (source_run_id,),
        ).fetchone()
        if row is None:
            raise KeyError("unknown source run")
        source_mode, overlap_seconds, manifest_json, manifest_sha256 = row
        if canonical_sha256(json.loads(manifest_json)) != manifest_sha256:
            raise ValueError("source manifest hash changed; resume denied")
        checkpoint = self.connection.execute(
            "SELECT page_number, high_water_mark, local_file_offset FROM source_checkpoints "
            "WHERE source_run_id = ? ORDER BY page_number DESC LIMIT 1",
            (source_run_id,),
        ).fetchone()
        page, high_water, file_offset = (0, None, None) if checkpoint is None else checkpoint
        mode = SourceModeV1(source_mode)
        high_water_time = datetime.fromisoformat(high_water) if high_water is not None else None
        restart = high_water_time
        credential_required = mode is SourceModeV1.DIRECT_CONNECTOR
        if credential_required and restart is not None:
            restart = restart - timedelta(seconds=overlap_seconds)
        return ResumePlanV1(
            source_run_id=source_run_id,
            source_mode=mode,
            credential_reentry_required=credential_required,
            restart_high_water=restart,
            local_file_offset=file_offset if mode is SourceModeV1.FILE_IMPORT else None,
            committed_page_number=page,
            durable_cursor_present=False,
        )
