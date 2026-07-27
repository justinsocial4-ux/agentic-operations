PRAGMA foreign_keys = ON;

CREATE TABLE authorization_attestations (
    authorization_attestation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    attestation_json TEXT NOT NULL,
    attestation_sha256 TEXT NOT NULL,
    attested_at TEXT NOT NULL
) STRICT;

CREATE TABLE source_authority_bindings (
    binding_sha256 TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_slot_id TEXT NOT NULL,
    authority_role TEXT NOT NULL,
    source_manifest_id TEXT NOT NULL REFERENCES source_manifests(source_manifest_id),
    source_instance_id TEXT NOT NULL,
    bound_at TEXT NOT NULL,
    UNIQUE (run_id, source_slot_id)
) STRICT;

CREATE TABLE operational_staging (
    staging_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_manifest_id TEXT NOT NULL REFERENCES source_manifests(source_manifest_id),
    canonical_artifact_id TEXT NOT NULL,
    artifact_kind TEXT NOT NULL CHECK (artifact_kind <> 'CONVERSATION_SEGMENT'),
    artifact_json TEXT NOT NULL,
    artifact_sha256 TEXT NOT NULL,
    lineage_json TEXT NOT NULL,
    staged_at TEXT NOT NULL,
    UNIQUE (canonical_artifact_id)
) STRICT;

ALTER TABLE lineage_edges ADD COLUMN page_receipt_id TEXT;
ALTER TABLE lineage_edges ADD COLUMN source_pointer TEXT;
ALTER TABLE lineage_edges ADD COLUMN mapping_profile_id TEXT;
ALTER TABLE lineage_edges ADD COLUMN mapping_rule_id TEXT;
ALTER TABLE lineage_edges ADD COLUMN quarantine_reason TEXT;

ALTER TABLE conversation_evidence_metadata ADD COLUMN source_family TEXT;
ALTER TABLE conversation_evidence_metadata ADD COLUMN cited_excerpt_ids_json TEXT;
ALTER TABLE cited_excerpts ADD COLUMN excerpt_utf8 TEXT;
