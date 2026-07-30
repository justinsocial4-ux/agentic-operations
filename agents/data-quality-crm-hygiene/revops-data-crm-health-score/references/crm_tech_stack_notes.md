# CRM Tech-Stack Notes

Use this file during preflight and field mapping. DQH-04 v1 is read-only.

## Salesforce

- Read Contact, Account, Opportunity, Task, Event, and optional EmailMessage records.
- Read field metadata before assuming custom fields exist.
- Fetch in 2,000-record batches; on rate limits, use the pilot fallback of smaller 1,000-record batches plus 2s, 4s, and 8s backoff.
- `email_verified` and `phone_verified` are not standard Salesforce fields. Use them only if the customer confirms equivalent custom fields.
- Use an example-only org identifier in documentation; never publish a real org ID.

## HubSpot

- Read contacts, companies, deals, engagements, and property metadata.
- Map Company associations to the pilot Account linkage checks.
- Use last activity or last modified time for freshness only when the chosen field is disclosed.
- Do not assume verification properties exist; use the documented format-valid fallback when they do not.

## Offline CSV

If no CRM connection exists, ask for exported fields and treat the run as analysis-only. Do not imply that connection checks passed. Preserve record counts, missing-column warnings, and confidence degradation in the report.

## Optional Warehouse

Snowflake is optional and may supply engagement history. Its absence must not block a baseline score; disclose the missing history and use the workflow's degraded mode.
