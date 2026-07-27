PRAGMA foreign_keys = ON;

ALTER TABLE events ADD COLUMN prior_state TEXT;
ALTER TABLE events ADD COLUMN new_state TEXT;
ALTER TABLE events ADD COLUMN event_sha256 TEXT;
ALTER TABLE events ADD COLUMN source_run_id TEXT;

ALTER TABLE source_runs ADD COLUMN source_mode TEXT NOT NULL DEFAULT 'FILE_IMPORT';
ALTER TABLE source_runs ADD COLUMN overlap_seconds INTEGER NOT NULL DEFAULT 0 CHECK (overlap_seconds >= 0);

CREATE TABLE source_checkpoint_records (
    source_run_id TEXT NOT NULL REFERENCES source_runs(source_run_id),
    source_record_id TEXT NOT NULL,
    source_version TEXT NOT NULL,
    page_number INTEGER NOT NULL CHECK (page_number >= 0),
    PRIMARY KEY (source_run_id, source_record_id, source_version)
) STRICT;

CREATE UNIQUE INDEX source_checkpoint_page_once
    ON source_checkpoints(source_run_id, page_number);

CREATE TABLE domain_receipts (
    receipt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    receipt_kind TEXT NOT NULL CHECK (receipt_kind IN (
        'READINESS', 'PRIORITY', 'PRIORITY_BLOCKED', 'WEEKLY_CAPACITY',
        'ELIGIBILITY', 'CONSULTANT_FIT'
    )),
    receipt_json TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
) STRICT;
