PRAGMA foreign_keys = ON;

CREATE TABLE deletion_receipts (
    deletion_receipt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_manifest_id TEXT NOT NULL REFERENCES source_manifests(source_manifest_id),
    deletion_state TEXT NOT NULL CHECK (deletion_state IN ('DELETIONS_CONFIRMED', 'DELETION_UNKNOWN')),
    receipt_json TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
) STRICT;

CREATE TABLE source_tombstones (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_manifest_id TEXT NOT NULL REFERENCES source_manifests(source_manifest_id),
    source_record_id TEXT NOT NULL,
    deletion_receipt_id TEXT NOT NULL REFERENCES deletion_receipts(deletion_receipt_id),
    run_policy_id TEXT NOT NULL,
    tombstoned_at TEXT NOT NULL,
    PRIMARY KEY (run_id, source_manifest_id, source_record_id)
) STRICT;
