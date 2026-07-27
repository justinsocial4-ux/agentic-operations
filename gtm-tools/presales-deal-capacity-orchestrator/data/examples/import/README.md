# Synthetic import examples

All rows are fictional and credential-free.

- `deal_priority_v1.csv` exercises the Phase 1 Deal-prioritization import. The deliberately unknown headers `SE Need`, `Bench`, and `Hero` are not selected or silently mapped.
- `conversation_segments_v1.json` is a fictional transcript-segment shape for the ephemeral import adapter. Full segment text is read into process memory only; durable output is hash/metadata and retention-approved cited excerpts only.

Import requires authorization attestation even for these samples, explicit selected fields, a hash-bound mapping profile, matching post-preflight source-slot authority, and data-health acceptance. No network path is used.
