# Enrichment Vendor Guide

Use this reference before selecting or invoking an enrichment source for Stale contacts. The pilot names ZoomInfo, Clay, and Apollo as examples; it does not establish that any one provider is best.

## Selection questions

- Which fields must be verified: phone, email, title, employer, or company status?
- What geography and market segment must the provider cover?
- What source timestamp, confidence, and provenance does it return?
- Can it process the approved batch size within rate limits?
- What contract, credit, privacy, retention, and deletion terms apply?
- Can results be reviewed before CRM writes?

## Minimum returned evidence

For each proposed update, retain:

- contact ID and field name;
- prior value and proposed value;
- provider and retrieval timestamp;
- provider confidence or verification status, when available;
- match key used;
- accepted, rejected, or unresolved decision.

## Operating guardrails

- Enrich only the approved scope.
- Do not overwrite a stronger, newer value without review.
- Do not treat a provider's missing result as proof of departure.
- Recompute all five decay signals after accepted enrichment.
- Keep vendor cost and turnaround estimates as current quotes, not hard-coded promises.
- Follow the customer's privacy, consent, and data-processing requirements.

If no provider is connected, export an approved CSV or return an analysis-only plan. Never fabricate enriched values.
