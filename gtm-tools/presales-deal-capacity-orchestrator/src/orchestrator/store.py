from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from .canonical import canonical_json_bytes, canonical_sha256
from .contracts.connectors import DeletionReceiptV1
from .contracts.manifest import SourceManifestV1
from .contracts.mapping import MappingProfileV1
from .contracts.phase3 import SolverReceiptV1
from .contracts.records import ConversationEvidenceMetadataV1, ConversationSegmentV1
from .contracts.setup import AuthorizationAttestationV1, RunSetupAcceptanceV1
from .lineage import LineageEdgeV1
from .mapping.health import DataHealthReceiptV1
from .mapping.profiles import scan_mapping_profile
from .retention import RetainedCitedExcerptV1
from .setup_gate import BoundSourceAuthorityV1

MIGRATIONS_DIRECTORY = Path(__file__).with_name("migrations")


def connect_database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA trusted_schema = OFF")
    connection.execute("PRAGMA temp_store = MEMORY")
    return connection


def apply_migrations(connection: sqlite3.Connection) -> None:
    migration_files = sorted(MIGRATIONS_DIRECTORY.glob("[0-9][0-9][0-9]_*.sql"))
    if not migration_files:
        raise RuntimeError("no SQLite migrations found")
    existing = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        )
    }
    applied: set[str] = set()
    if "schema_migrations" in existing:
        applied = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
    for migration_path in migration_files:
        if migration_path.name in applied:
            continue
        connection.executescript(migration_path.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (migration_path.name, datetime.now(timezone.utc).isoformat()),
        )
        connection.commit()


class Phase1Store:
    """Operational import store. Its public API has no full-transcript write path."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_run(self, *, run_id: str, lane: str, synthetic: bool, created_at: datetime) -> None:
        self.connection.execute(
            "INSERT INTO runs(run_id, lane, state, synthetic, created_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, lane, "AUTHORITY_ATTESTED", int(synthetic), created_at.isoformat()),
        )
        self.connection.commit()

    def persist_authorization_attestation(self, receipt: AuthorizationAttestationV1) -> None:
        payload = canonical_json_bytes(receipt).decode()
        self.connection.execute(
            "INSERT INTO authorization_attestations(authorization_attestation_id, run_id, attestation_json, "
            "attestation_sha256, attested_at) VALUES (?, ?, ?, ?, ?)",
            (receipt.authorization_attestation_id, receipt.run_id, payload, canonical_sha256(receipt), receipt.attested_at.isoformat()),
        )
        self.connection.commit()

    def persist_setup_acceptance(self, receipt: RunSetupAcceptanceV1, *, policy_sha256: str) -> None:
        payload = canonical_json_bytes(receipt).decode()
        self.connection.execute(
            "INSERT INTO policy_acceptances(acceptance_id, run_id, lane, policy_sha256, acceptance_json, accepted_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (f"setup-{canonical_sha256(receipt)[:32]}", receipt.run_id, receipt.lane, policy_sha256, payload, receipt.accepted_at.isoformat()),
        )
        self.connection.commit()

    def persist_manifest(self, manifest: SourceManifestV1) -> None:
        payload = canonical_json_bytes(manifest).decode()
        self.connection.execute(
            "INSERT INTO source_manifests(source_manifest_id, run_id, source_instance_id, adapter_id, source_mode, manifest_json, manifest_sha256) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (manifest.source_manifest_id, manifest.run_id, manifest.source_instance_id, manifest.adapter_id,
             manifest.source_mode, payload, canonical_sha256(manifest)),
        )
        self.connection.commit()

    def persist_bound_authority(self, run_id: str, binding: BoundSourceAuthorityV1, *, bound_at: datetime) -> None:
        self.connection.execute(
            "INSERT INTO source_authority_bindings(binding_sha256, run_id, source_slot_id, authority_role, "
            "source_manifest_id, source_instance_id, bound_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (binding.binding_sha256, run_id, binding.source_slot_id, binding.authority_role,
             binding.source_manifest_id, binding.source_instance_id, bound_at.isoformat()),
        )
        self.connection.commit()

    def persist_mapping_profile(self, profile: MappingProfileV1) -> None:
        scan_mapping_profile(profile)
        payload = canonical_json_bytes(profile).decode()
        self.connection.execute(
            "INSERT INTO mapping_profiles(mapping_profile_id, source_instance_id, profile_json, profile_sha256, accepted_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (profile.profile_id, profile.source_instance_id, payload, profile.canonical_profile_sha256, profile.accepted_at.isoformat()),
        )
        self.connection.commit()

    def persist_mapping_acceptance(
        self,
        *,
        acceptance_id: str,
        run_id: str,
        mapping_profile_id: str,
        actor_role: str,
        accepted_at: datetime,
    ) -> None:
        self.connection.execute(
            "INSERT INTO mapping_acceptances(acceptance_id, run_id, mapping_profile_id, actor_role, accepted_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (acceptance_id, run_id, mapping_profile_id, actor_role, accepted_at.isoformat()),
        )
        self.connection.commit()

    def stage_operational_artifact(
        self,
        *,
        staging_id: str,
        run_id: str,
        source_manifest_id: str,
        canonical_artifact_id: str,
        artifact_kind: str,
        artifact: BaseModel,
        lineage_edges: tuple[LineageEdgeV1, ...],
        staged_at: datetime,
    ) -> None:
        if isinstance(artifact, ConversationSegmentV1) or artifact_kind == "CONVERSATION_SEGMENT":
            raise TypeError("ephemeral conversation segments cannot enter operational staging")
        if "transcript" in artifact_kind.lower():
            raise TypeError("transcript-shaped operational artifact kinds are forbidden")
        payload = canonical_json_bytes(artifact.model_dump(mode="json", exclude_unset=True)).decode()
        lineage_payload = canonical_json_bytes(lineage_edges).decode()
        with self.connection:
            self.connection.execute(
                "INSERT INTO operational_staging(staging_id, run_id, source_manifest_id, canonical_artifact_id, "
                "artifact_kind, artifact_json, artifact_sha256, lineage_json, staged_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (staging_id, run_id, source_manifest_id, canonical_artifact_id, artifact_kind,
                 payload, canonical_sha256(artifact.model_dump(mode="json", exclude_unset=True)), lineage_payload,
                 staged_at.isoformat()),
            )

    def commit_operational(self, receipt: DataHealthReceiptV1) -> int:
        if not receipt.accepted_for_operational_commit:
            raise ValueError("data health is not accepted; operational commit denied")
        rows = list(self.connection.execute(
            "SELECT canonical_artifact_id, artifact_kind, artifact_json, artifact_sha256, lineage_json, staged_at "
            "FROM operational_staging WHERE run_id = ? ORDER BY staging_id",
            (receipt.run_id,),
        ))
        receipt_payload = canonical_json_bytes(receipt).decode()
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(
                "INSERT INTO data_health_receipts(receipt_id, run_id, receipt_json, receipt_sha256, created_at) VALUES (?, ?, ?, ?, ?)",
                (receipt.receipt_id, receipt.run_id, receipt_payload, canonical_sha256(receipt), receipt.created_at.isoformat()),
            )
            for artifact_id, kind, payload, payload_hash, lineage_payload, created_at in rows:
                self.connection.execute(
                    "INSERT INTO canonical_artifacts(canonical_artifact_id, run_id, artifact_kind, artifact_json, artifact_sha256, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (artifact_id, receipt.run_id, kind, payload, payload_hash, created_at),
                )
                for edge_payload in json.loads(lineage_payload):
                    edge = LineageEdgeV1.model_validate(edge_payload)
                    self.connection.execute(
                        "INSERT INTO lineage_edges(lineage_edge_id, run_id, source_manifest_id, source_record_id, "
                        "source_field_id, raw_value_sha256, canonical_artifact_id, canonical_field_id, conversion_id, "
                        "validation_state, page_receipt_id, source_pointer, mapping_profile_id, mapping_rule_id, quarantine_reason) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (edge.lineage_edge_id, edge.run_id, edge.source_manifest_id, edge.source_record_id,
                         edge.source_field_id, edge.raw_selected_value_sha256, edge.canonical_artifact_id,
                         edge.canonical_field_id, edge.conversion_id, edge.validation_state, edge.page_receipt_id,
                         edge.source_pointer, edge.mapping_profile_id, edge.mapping_rule_id, edge.quarantine_reason),
                    )
            self.connection.execute("DELETE FROM operational_staging WHERE run_id = ?", (receipt.run_id,))
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return len(rows)

    def persist_deletion_receipt(
        self,
        *,
        run_id: str,
        source_manifest_id: str,
        receipt: DeletionReceiptV1,
        run_policy_id: str,
        created_at: datetime,
    ) -> tuple[str, ...]:
        """Append the receipt and tombstone explicit IDs; incompleteness only forbids absence inference."""
        payload = canonical_json_bytes(receipt).decode()
        tombstones = receipt.deleted_source_record_ids
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(
                "INSERT INTO deletion_receipts(deletion_receipt_id, run_id, source_manifest_id, deletion_state, "
                "receipt_json, receipt_sha256, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (receipt.deletion_receipt_id, run_id, source_manifest_id, receipt.deletion_state,
                 payload, canonical_sha256(receipt), created_at.isoformat()),
            )
            for source_record_id in tombstones:
                self.connection.execute(
                    "INSERT OR IGNORE INTO source_tombstones(run_id, source_manifest_id, source_record_id, deletion_receipt_id, "
                    "run_policy_id, tombstoned_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (run_id, source_manifest_id, source_record_id, receipt.deletion_receipt_id,
                     run_policy_id, created_at.isoformat()),
                )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return tombstones

    def persist_solver_receipt(self, receipt: SolverReceiptV1) -> None:
        """Persist only the deterministic recommendation receipt; this performs no assignment."""
        payload = canonical_json_bytes(receipt).decode()
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(
                "INSERT INTO solver_receipts(solver_receipt_id, run_id, status, receipt_json, receipt_sha256) "
                "VALUES (?, ?, ?, ?, ?)",
                (receipt.solver_receipt_id, receipt.run_id, receipt.status, payload, canonical_sha256(receipt)),
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def persist_conversation_metadata(
        self,
        *,
        run_id: str,
        source_manifest_id: str,
        metadata: ConversationEvidenceMetadataV1,
    ) -> None:
        # This typed projection has no text field. Never broaden this API to accept a
        # segment, generic dict, exception, or transcript buffer.
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(
                "INSERT INTO conversation_evidence_metadata(conversation_origin_id, run_id, source_manifest_id, "
                "native_call_or_meeting_id, content_sha256, started_at, ended_at, role_counts_json, deal_source_id, "
                "source_family, cited_excerpt_ids_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (metadata.conversation_origin_id, run_id, source_manifest_id,
                 metadata.native_call_or_meeting_id, metadata.transcript_content_sha256,
                 metadata.started_at.isoformat(), metadata.ended_at.isoformat(),
                 canonical_json_bytes(metadata.speaker_role_counts).decode() if metadata.speaker_role_counts is not None else None,
                 metadata.deal_source_id, metadata.source_family,
                 canonical_json_bytes(metadata.cited_excerpt_ids).decode()),
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def persist_retention_approved_excerpt(self, excerpt: RetainedCitedExcerptV1) -> None:
        row = self.connection.execute(
            "SELECT content_sha256, cited_excerpt_ids_json FROM conversation_evidence_metadata WHERE conversation_origin_id = ?",
            (excerpt.conversation_origin_id,),
        ).fetchone()
        if row is None:
            raise ValueError("retained excerpt requires existing conversation metadata")
        if excerpt.quote_sha256 == row[0]:
            raise ValueError("a full-content transcript cannot be persisted as a cited excerpt")
        cited_ids = list(json.loads(row[1] or "[]"))
        cited_ids.append(excerpt.excerpt_id)
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(
                "INSERT INTO cited_excerpts(excerpt_id, conversation_origin_id, quote_sha256, char_begin, char_end, "
                "expires_at, retention_approved_at, excerpt_utf8) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (excerpt.excerpt_id, excerpt.conversation_origin_id, excerpt.quote_sha256,
                 excerpt.char_begin, excerpt.char_end, excerpt.expires_at.isoformat(),
                 excerpt.retention_approved_at.isoformat(), excerpt.excerpt),
            )
            self.connection.execute(
                "UPDATE conversation_evidence_metadata SET cited_excerpt_ids_json = ? WHERE conversation_origin_id = ?",
                (canonical_json_bytes(tuple(cited_ids)).decode(), excerpt.conversation_origin_id),
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def create_backup(self, destination: Path) -> None:
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("backup destination must be a new regular file")
        descriptor = os.open(
            destination,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        os.close(descriptor)
        backup = sqlite3.connect(destination)
        try:
            self.connection.backup(backup)
        finally:
            backup.close()

    def reset_run(self, run_id: str) -> None:
        """Purge app-controlled rows only; this never touches imports, exports, or vendors."""
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            manifest_ids = [row[0] for row in self.connection.execute(
                "SELECT source_manifest_id FROM source_manifests WHERE run_id = ?", (run_id,)
            )]
            profile_ids = [row[0] for row in self.connection.execute(
                "SELECT mapping_profile_id FROM mapping_acceptances WHERE run_id = ?", (run_id,)
            )]
            source_run_ids = [row[0] for row in self.connection.execute(
                "SELECT source_run_id FROM source_runs WHERE run_id = ?", (run_id,)
            )]
            for source_run_id in source_run_ids:
                self.connection.execute("DELETE FROM source_checkpoint_records WHERE source_run_id = ?", (source_run_id,))
                self.connection.execute("DELETE FROM source_checkpoints WHERE source_run_id = ?", (source_run_id,))
            self.connection.execute("DELETE FROM source_runs WHERE run_id = ?", (run_id,))
            for manifest_id in manifest_ids:
                origin_ids = [row[0] for row in self.connection.execute(
                    "SELECT conversation_origin_id FROM conversation_evidence_metadata WHERE source_manifest_id = ?",
                    (manifest_id,),
                )]
                for origin_id in origin_ids:
                    self.connection.execute("DELETE FROM cited_excerpts WHERE conversation_origin_id = ?", (origin_id,))
                self.connection.execute("DELETE FROM conversation_evidence_metadata WHERE source_manifest_id = ?", (manifest_id,))
            for table in (
                "source_tombstones", "deletion_receipts",
                "source_authority_bindings", "operational_staging", "lineage_edges",
                "canonical_artifacts", "data_health_receipts", "events", "analyst_receipts",
                "domain_receipts", "solver_receipts", "manager_dispositions", "exports", "retention_items",
                "mapping_acceptances", "policy_acceptances", "authorization_attestations",
            ):
                self.connection.execute(f'DELETE FROM "{table}" WHERE run_id = ?', (run_id,))
            for profile_id in profile_ids:
                self.connection.execute("DELETE FROM mapping_profiles WHERE mapping_profile_id = ?", (profile_id,))
            self.connection.execute("DELETE FROM source_manifests WHERE run_id = ?", (run_id,))
            self.connection.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
