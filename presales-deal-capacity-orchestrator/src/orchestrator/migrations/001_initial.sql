PRAGMA foreign_keys = ON;

CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
) STRICT;

CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    lane TEXT NOT NULL,
    state TEXT NOT NULL,
    synthetic INTEGER NOT NULL CHECK (synthetic IN (0, 1)),
    created_at TEXT NOT NULL
) STRICT;

CREATE TABLE source_manifests (
    source_manifest_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_instance_id TEXT NOT NULL,
    adapter_id TEXT NOT NULL,
    source_mode TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL
) STRICT;

CREATE TABLE source_runs (
    source_run_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_manifest_id TEXT NOT NULL REFERENCES source_manifests(source_manifest_id),
    state TEXT NOT NULL,
    completeness TEXT NOT NULL
) STRICT;

CREATE TABLE source_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    source_run_id TEXT NOT NULL REFERENCES source_runs(source_run_id),
    page_number INTEGER NOT NULL CHECK (page_number >= 0),
    cursor_sha256 TEXT,
    high_water_mark TEXT,
    local_file_offset INTEGER CHECK (local_file_offset IS NULL OR local_file_offset >= 0),
    committed_at TEXT NOT NULL
) STRICT;

CREATE TABLE mapping_profiles (
    mapping_profile_id TEXT PRIMARY KEY,
    source_instance_id TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    profile_sha256 TEXT NOT NULL,
    accepted_at TEXT NOT NULL
) STRICT;

CREATE TABLE mapping_acceptances (
    acceptance_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    mapping_profile_id TEXT NOT NULL REFERENCES mapping_profiles(mapping_profile_id),
    actor_role TEXT NOT NULL,
    accepted_at TEXT NOT NULL
) STRICT;

CREATE TABLE policy_acceptances (
    acceptance_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    lane TEXT NOT NULL,
    policy_sha256 TEXT NOT NULL,
    acceptance_json TEXT NOT NULL,
    accepted_at TEXT NOT NULL
) STRICT;

CREATE TABLE lineage_edges (
    lineage_edge_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_manifest_id TEXT NOT NULL REFERENCES source_manifests(source_manifest_id),
    source_record_id TEXT NOT NULL,
    source_field_id TEXT NOT NULL,
    raw_value_sha256 TEXT NOT NULL,
    canonical_artifact_id TEXT NOT NULL,
    canonical_field_id TEXT NOT NULL,
    conversion_id TEXT NOT NULL,
    validation_state TEXT NOT NULL
) STRICT;

CREATE TABLE canonical_artifacts (
    canonical_artifact_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    artifact_kind TEXT NOT NULL CHECK (artifact_kind <> 'CONVERSATION_SEGMENT'),
    artifact_json TEXT NOT NULL,
    artifact_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
) STRICT;

CREATE TABLE conversation_evidence_metadata (
    conversation_origin_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_manifest_id TEXT NOT NULL REFERENCES source_manifests(source_manifest_id),
    native_call_or_meeting_id TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    role_counts_json TEXT,
    deal_source_id TEXT NOT NULL
) STRICT;

CREATE TABLE cited_excerpts (
    excerpt_id TEXT PRIMARY KEY,
    conversation_origin_id TEXT NOT NULL REFERENCES conversation_evidence_metadata(conversation_origin_id),
    quote_sha256 TEXT NOT NULL,
    char_begin INTEGER NOT NULL CHECK (char_begin >= 0),
    char_end INTEGER NOT NULL CHECK (char_end > char_begin),
    expires_at TEXT NOT NULL,
    retention_approved_at TEXT NOT NULL
) STRICT;

CREATE TABLE data_health_receipts (
    receipt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    receipt_json TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
) STRICT;

CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    sequence_number INTEGER NOT NULL CHECK (sequence_number >= 0),
    prior_event_sha256 TEXT,
    artifact_sha256 TEXT,
    actor_type TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (run_id, sequence_number)
) STRICT;

CREATE TABLE analyst_receipts (
    analyst_receipt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    deal_source_id TEXT NOT NULL,
    dimension_id TEXT NOT NULL,
    evidence_state TEXT NOT NULL,
    citation_metadata_json TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL
) STRICT;

CREATE TABLE solver_receipts (
    solver_receipt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    status TEXT NOT NULL,
    receipt_json TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL
) STRICT;

CREATE TABLE manager_dispositions (
    disposition_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    recommendation_id TEXT NOT NULL,
    disposition TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    created_at TEXT NOT NULL
) STRICT;

CREATE TABLE exports (
    export_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    bundle_sha256 TEXT NOT NULL,
    destination_receipt TEXT NOT NULL,
    created_at TEXT NOT NULL
) STRICT;

CREATE TABLE retention_items (
    retention_item_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    category TEXT NOT NULL,
    local_path TEXT,
    expires_at TEXT NOT NULL,
    deletion_state TEXT NOT NULL
) STRICT;
