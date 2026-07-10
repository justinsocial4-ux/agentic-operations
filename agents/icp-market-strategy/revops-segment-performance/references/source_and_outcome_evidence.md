# Source and Outcome Evidence

Read this file before using CRM fields, stages, close dates, amounts, or revisions.

- Register source ID, version, property-schema version, as-of time, extraction time, access scope, and policy ID.
- Treat source-system field names as identifiers, not universal business meanings. Customer-defined properties and stage mappings require exact versioned definitions.
- Require an approved occurrence-time rule for `WON` and `LOST`. A forecast close date or current stage alone is not an outcome-history receipt.
- Require stable opportunity ID and revision ID. Duplicate, reopened, reclosed, deleted, merged, future, or conflicting records stay explicit.
- Count only approved `WON` and `LOST` outcomes. Do not convert unknown, active, omitted, or missing states into losses or zeros.
- Do not fetch contact, rep, message, note, or activity data unless a separate approved purpose and privacy contract requires it.
