# International Subsidiaries

Use this file for cross-border, regional, and legal-entity cases.

## Common Indicators

- regions: EMEA, APAC, LATAM, NA, Europe, Asia Pacific
- countries or cities appended to a parent name
- business-unit terms: Division, Holdings, Group, Services, Digital, Aviation
- legal forms: GmbH, BV, SA, SAS, PLC, Pty Ltd, KK

These indicators create a subsidiary-pattern signal only. They do not establish legal ownership or the correct direction by themselves.

## Review Checklist

1. Confirm that Parent and Child are separate CRM Account records.
2. Confirm Parent/Child direction with D-U-N-S hierarchy data, an existing CRM link, verified corporate documentation, or an explicit customer mapping.
3. Compare website and Contact email domains, but treat a shared domain as corroboration rather than proof of direction.
4. Check country, industry, and employee-count coherence.
5. Flag joint ventures, franchise structures, private-equity portfolios, and matrix organizations for manual review because v1 assumes one parent.
6. Preserve existing approved links unless the user explicitly approves a replacement.

## Missing Parent

If the legal or commercial parent is not in the CRM, do not create a guessed link. Add the account to the orphan checklist with one of two recommendations:

- create the missing parent record after verification, or
- accept the account as a root and record the limitation.

## Refresh

Recheck hierarchies quarterly for mergers, acquisitions, rebrands, and restructures. The pilot does not include a real-time M&A feed.
