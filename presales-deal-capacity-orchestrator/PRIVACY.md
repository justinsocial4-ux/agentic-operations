# Privacy

This package uses only synthetic fixtures, official-shape replay fixtures, and public documentation. No credentials, accounts, customer records, employee records, or private transcripts are included in the source, history, fixtures, logs, database, exports, screenshots, or release archive.

Future authorized-data modes must attest authority before any file-content read, schema preview, preflight, or connector call. Credentials and vendor cursors are process-memory-only. Full transcript text and uncited segments must never enter SQLite, logs, exports, temporary files, backups, or crash artifacts. Exact cited excerpts default to session-only retention.

Authorized real-data state must live outside this repository and outside the import directory, in an owner-only directory (`0700`) with owner-only files (`0600`) on POSIX. The implementation fails closed if it cannot establish those permissions. Synced folders and external backups can create copies beyond app control; reset cannot promise deletion from them.

No telemetry, analytics, crash upload, external logging, remote fonts, CDN assets, or remote LLM route is enabled. A future private-transcript model route is limited to loopback `LIVE_LOCAL`; the local model's own storage/logging behavior is the user's responsibility.
