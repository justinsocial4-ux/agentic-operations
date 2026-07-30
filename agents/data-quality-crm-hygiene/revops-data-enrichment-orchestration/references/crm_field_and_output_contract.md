# CRM Field And Output Contract

Read this before mapping fields or writing results back to Salesforce or HubSpot.

## Minimum Match Inputs

- Contact or lead: first name, last name, and at least one usable identifier or account/company link.
- Account/company: company name plus domain or another stable company identifier when available.
- Enrichment provider: at least one authenticated integration; two or more enable waterfall fallback.

## Write-Back Fields

Map the customer's actual schema to these logical fields:

| Logical field | Purpose |
|---|---|
| enriched email / phone / title / company data | Accepted provider result |
| enrichment source | Provider that supplied the accepted value |
| enrichment confidence | 0–100 field-level confidence |
| enrichment date | ISO 8601 timestamp |
| enrichment cost | Charged or allocated cost |
| prior value / change reason | Audit history when upgrading low-confidence data |

## Write Safety

- Fill empty fields or upgrade explicitly low-confidence data.
- Never overwrite a verified manual value.
- Preserve the old value and the reason for every approved change.
- Do not write “not found,” conflicted, over-budget, or below-threshold results.
- Filter consent and suppression lists upstream; this pilot does not manage consent.

## Required Report Sections

1. Records processed, enriched, partial, not found, and skipped.
2. Coverage before/after by field.
3. Spend by provider, total spend, and cost per accepted record.
4. Confidence distribution and conflicts.
5. Remaining data gaps and estimated next-pass cost.
6. Data limitations, assumptions, and provider evidence caveats.
7. Recommended validation and re-enrichment actions.
8. Source systems and timestamps.
