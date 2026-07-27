from __future__ import annotations

import sqlite3
from pathlib import Path

from orchestrator.store import apply_migrations, connect_database

REQUIRED_TABLES = {
    "runs", "source_manifests", "source_runs", "source_checkpoints",
    "mapping_profiles", "mapping_acceptances", "policy_acceptances", "lineage_edges",
    "canonical_artifacts", "conversation_evidence_metadata", "cited_excerpts",
    "data_health_receipts", "events", "analyst_receipts", "solver_receipts",
    "manager_dispositions", "exports", "retention_items", "authorization_attestations",
    "source_authority_bindings", "operational_staging", "source_checkpoint_records",
    "domain_receipts",
}
FORBIDDEN_COLUMN_TERMS = {
    "credential", "password", "client_secret", "refresh_token", "access_token",
    "api_key", "authorization_header", "transcript_text", "segment_text",
    "quote_text", "uncited_text", "vendor_cursor",
}


def test_migration_builds_minimized_schema_without_secret_or_transcript_text_columns(tmp_path: Path) -> None:
    database = tmp_path / "phase0.sqlite"
    connection = connect_database(database)
    apply_migrations(connection)
    apply_migrations(connection)
    assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone() == (4,)
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert REQUIRED_TABLES <= tables
    for table in tables:
        for row in connection.execute(f'PRAGMA table_info("{table}")'):
            column = row[1].lower()
            assert all(term not in column for term in FORBIDDEN_COLUMN_TERMS), (table, column)
    trigger_or_fts = list(connection.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' OR name LIKE '%fts%'"
    ))
    assert trigger_or_fts == []
    connection.close()


def test_foreign_keys_are_enabled(tmp_path: Path) -> None:
    connection = connect_database(tmp_path / "foreign.sqlite")
    assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
    connection.close()
