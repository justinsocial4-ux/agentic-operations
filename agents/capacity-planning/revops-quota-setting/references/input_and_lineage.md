# Input and Lineage

Accept only `customer-supplied-anonymous-quota-plan` evidence. Bind each source ID/version to one schema, authorization, currency, amount basis, period, anonymous territory basis, and coverage basis. Every binding needs exactly one complete source population.

The declared scenario population must equal the observed scenario population. Within each scenario, the declared opaque territory IDs must equal the row IDs and the approved pseudonymization-receipt population exactly once. Reject missing, duplicate, extra, unapproved, malformed, or cross-source records.

All amounts are plain decimal strings. Core quota and target values are mandatory. Coverage is explicitly `accepted`, `missing`, `conflicting`, or `suppressed`; only `accepted` may carry an amount. Do not merge sources, fill gaps, or substitute a benchmark.
