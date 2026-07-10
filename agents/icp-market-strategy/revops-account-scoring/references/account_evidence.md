# Account Evidence Contract

Use stable account/legal-entity IDs. Record source system, field, observed value, observed/effective time, extraction cutoff, provenance, validity, freshness, and transformation. Keep CRM, enrichment, warehouse, and analyst evidence separate.

Industry, employee count, annual revenue, geography, domain, product use, and technology fields are observations with definitions—not universal fit signals. Confirm units, currency, fiscal period, employee basis, taxonomy version, country mapping, and whether the value describes a parent or child entity.

Do not use title, domain, company name, website text, or a guessed industry to fill missing evidence. Do not prefer enrichment merely because it is newer; apply an approved source-precedence rule. Conflicts remain `CONFLICT` until resolved.

Preserve duplicates, mergers, subsidiaries, branches, parent accounts, customer/prospect status, exclusions, and unknowns. Do not collapse them silently.
