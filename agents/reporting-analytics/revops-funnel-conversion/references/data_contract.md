# Data Contract

Read this file before querying a CRM or accepting an export.

## Episode-level fields

| Field | Meaning |
|---|---|
| `episode_id` | Stable unique funnel episode |
| `record_id` | Stable CRM/warehouse identity |
| `pipeline_id` | Pipeline/process identifier |
| `stage_events` | Ordered stage, entered-at, exited-at, source event IDs |
| `terminal_outcome` | Approved terminal state, nullable |
| `anchor_dimensions` | Source, segment, owner, or other values frozen at the approved point |
| `amount_at_anchor` | Optional amount with currency and timestamp |

Also record extraction time, cutoff, timezone, earliest covered history date, pipeline-policy version, filters, exclusions, and identity/merge rules.

## Salesforce

Opportunity Stage History records changes to Stage, Amount, Probability, and Close Date. Field-history availability and retention differ by feature and configuration. Lead/lifecycle stages outside Opportunity require verified tracked fields or another event source.

Do not assume Salesforce Lead conversion always creates an Opportunity. Preserve the identity mapping between Lead, Contact, Account, and Opportunity when the customer uses that path.

## HubSpot

Use lifecycle/deal stage history or automatically maintained `Date entered [stage]` properties. Funnel semantics depend on whether all selected stages are required or any selected stage is allowed. Record which logic is used.

## Fail-closed checks

- No current-status reconstruction of earlier stages.
- No `LastModifiedDate` as stage entry or exit.
- No email-only identity join when stable IDs exist.
- No cross-pipeline stage mixing.
- Quarantine SQL-before-MQL, Closed-Won-before-Opportunity, negative duration, duplicate event IDs, and conflicting terminal outcomes.
- Preserve missing anchor dimensions as `UNKNOWN`, not inferred from current values.
