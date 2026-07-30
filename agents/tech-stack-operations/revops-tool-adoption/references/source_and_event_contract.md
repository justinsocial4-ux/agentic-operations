# Source And Event Contract

## Evidence record

Each source needs `evidence_id`, source/product, version/snapshot, extraction time, permission scope, observation window, lag, coverage, event-taxonomy version, transformation, and limits.

## Meaningful-event policy

Define included and excluded event types for each tool and role. State whether an event is user-initiated, administrative, automated, background, API/service, test, or unknown. Define deduplication and sessionization without assuming platform equivalence.

Audit/security events show that an event occurred; they do not automatically show useful product adoption. Vendor usage reports may supply product-defined active-user measures; preserve their definition and never rename them as a universal metric.

## Actor identity

Use an approved directory or platform account-type field. Heuristics can create a review candidate but cannot establish human, bot, shared, contractor, test, or service-account status.

## Coverage

Report expected sources/periods, received sources/periods, API/report lag, missing dates, schema changes, rejected rows, duplicates, and unknown events. Do not issue a portfolio-wide conclusion from a subset without naming the subset.
