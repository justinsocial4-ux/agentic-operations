# Weekly Revenue Data Contract

Read this before retrieving CRM data or accepting an export.

## Required record fields

| Field | Purpose | Missing behavior |
|---|---|---|
| `id` | Trace every claim to a record | Exclude unnamed record and count it as invalid |
| `name` | Human-readable narrative | Use safe ID if absent |
| `amount` and `currency` | Pipeline totals | Disable combined amount metric if invalid or mixed |
| `stage` and `pipeline_id` | Stage breakdown and comparison scope | Disable stage metric |
| `close_date` | Weekly outcomes and upcoming closes | Disable date-window metric |
| `created_date` | New-deal metric | Disable new-deal metric |
| `owner_id` | Owner breakdown | Disable owner breakdown |
| `is_closed`, `is_won` | Outcome classification | Do not infer solely from stage label |
| `stage_entered_at` | Days-in-stage evidence | Stall risk is unknown |
| `last_activity_at` | Buyer/seller activity evidence | Silence risk is unknown |
| `prior_close_date` | Close-date slip evidence | Slip is unknown |

Use ISO 8601 timestamps. Record the source timezone and convert boundaries deliberately.

## Snapshot requirements

Week-over-week reporting requires two comparable saved states:

1. current snapshot with extraction timestamp;
2. prior snapshot from the same weekday/time, pipeline scope, filters, currency treatment, and field semantics.

Current CRM values cannot reconstruct a prior snapshot. Property history may establish a specific prior field value, but it is not a complete prior pipeline snapshot unless every compared field is historical.

## Platform notes

- HubSpot's deals API supports current and historical property retrieval with `propertiesWithHistory`; inspect the account's property definitions and internal pipeline/stage IDs: https://developers.hubspot.com/docs/api-reference/legacy/crm/objects/deals/guide
- HubSpot property types and UTC date/datetime formats are documented here: https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide
- Salesforce object reads should use the platform REST/SOQL APIs and pagination. Salesforce explains object-data access and query pagination here: https://developer.salesforce.com/blogs/2024/04/accessing-object-data-with-salesforce-platform-apis
- Salesforce API limits vary by org and should be read from the Limits resource/headers rather than hard-coded: https://developer.salesforce.com/blogs/2024/11/api-limits-and-monitoring-your-api-usage

## Evidence states

Represent each metric as:

- `AVAILABLE`: all required source fields are present and valid;
- `DEGRADED`: metric is calculable but important coverage is below its target;
- `UNKNOWN`: required evidence is absent or scopes are not comparable;
- `NOT_APPLICABLE`: the approved scope intentionally excludes it.

Never encode `UNKNOWN` as zero.
