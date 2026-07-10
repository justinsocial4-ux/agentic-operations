# Data Contract

Read this file before a CRM query, event-warehouse query, or export analysis.

## Required episode fields

| Field | Meaning |
|---|---|
| `episode_id` | Stable, unique identifier for the approved MQL episode |
| `person_id` | Stable CRM or warehouse record identifier |
| `mql_entered_at` | Timestamp of MQL entry |
| `sql_entered_at` | Timestamp of SQL entry, nullable |
| `terminal_disposition` | Customer-approved rejected/recycled/other code, nullable |
| `terminal_at` | Timestamp of terminal disposition, nullable |
| `source_at_mql` | Lead source frozen at MQL entry, nullable |
| `segment_at_mql` | Segment frozen at MQL entry, nullable |
| `score_at_mql` | Lead score frozen at MQL entry, nullable |

Also record the UTC cutoff, timezone conversion, conversion-window length, history-start date, pipeline/process, filters, and extraction timestamp.

## Salesforce

Use Lead or custom-object field history only when status tracking was enabled during the cohort period. Field history begins when tracking is turned on; it does not reconstruct earlier changes. Preserve old value, new value, timestamp, and record ID. Lead `Status` values are org-configured; map them through the customer's approved policy.

## HubSpot

Use Lifecycle stage history, `propertiesWithHistory`, or the calculated `Date entered [stage]` properties when available. HubSpot default lifecycle stages include Marketing Qualified Lead and Sales Qualified Lead, but customers may customize stages. Lead Status is a sub-stage within SQL, not a substitute for the lifecycle contract.

## Fail-closed checks

- Do not use current status to infer when MQL or SQL occurred.
- Do not use `LastModifiedDate` as a lifecycle timestamp.
- Do not join by email when a stable ID is available.
- Quarantine SQL-before-MQL, negative durations, duplicate episode IDs, and conflicting terminal events.
- Report the percentage of records with complete transition evidence.
- Keep deleted, merged, and converted Salesforce leads traceable through an approved identity map.
