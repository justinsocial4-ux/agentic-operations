# Data Quality And CRM Hygiene

These agents help clean the CRM foundation: duplicates, stale contacts,
inconsistent fields, missing enrichment, weak account hierarchy, and overall CRM
health.

| Agent | What it does |
|---|---|
| [Deduplication Engine](revops-data-deduplication/SKILL.md) | Finds duplicate contacts, leads, and accounts. |
| [Field Normalization Engine](revops-data-field-normalization/SKILL.md) | Standardizes messy fields like job titles, industries, countries, and company names. |
| [Contact Decay Detection](revops-data-contact-decay/SKILL.md) | Scores stale contacts with tested five-signal arithmetic and routes them to monitoring, re-engagement, enrichment, or approval-gated archival review. |
| [CRM Health Score Agent](revops-data-crm-health-score/SKILL.md) | Scores six CRM-quality dimensions with tested arithmetic, evidence caveats, trends, and cleanup priorities. |
| [Enrichment Orchestration Engine](revops-data-enrichment-orchestration/SKILL.md) | Routes missing fields with tested scoring, explicit evidence caveats, and multi-source conflict handling. |
| [Enrichment Route Plan Review](revops-enrichment-orchestration/SKILL.md) | Reviews supplied pseudonymous route assignments against exact governance, suppression, field, provider-contract, geography, and charge evidence without choosing providers or enriching records. |
| [Account Hierarchy Engine](revops-data-account-hierarchy/SKILL.md) | Maps account families with tested confidence, cycle, and tree logic plus explicit evidence limits. |
