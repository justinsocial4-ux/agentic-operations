# Data Quality And CRM Hygiene

These agents help clean the CRM foundation: duplicates, stale contacts,
inconsistent fields, missing enrichment, weak account hierarchy, and overall CRM
health.

| Agent | What it does |
|---|---|
| [Deduplication Engine](revops-data-deduplication/SKILL.md) | Finds duplicate contacts, leads, and accounts. |
| [Field Normalization Engine](revops-data-field-normalization/SKILL.md) | Standardizes messy fields like job titles, industries, countries, and company names. |
| [Contact Decay Detection](revops-data-contact-decay/SKILL.md) | Finds stale contacts that need cleanup, re-engagement, or archival. |
| [CRM Health Score Agent](revops-data-crm-health-score/SKILL.md) | Scores six CRM-quality dimensions with tested arithmetic, evidence caveats, trends, and cleanup priorities. |
| [Enrichment Orchestration Engine](revops-data-enrichment-orchestration/SKILL.md) | Routes missing fields with tested scoring, explicit evidence caveats, and multi-source conflict handling. |
| [Account Hierarchy Engine](revops-data-account-hierarchy/SKILL.md) | Maps account families with tested confidence, cycle, and tree logic plus explicit evidence limits. |
