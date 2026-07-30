# Policy And Scope

Require a stable review ID/version, tool ID, legal service/product, license model, portfolio scope, review purpose, intended audience, equal observation windows, cutoff, timezone, source/evidence IDs, and policy owners.

Lock these customer-approved policies before calculation:

- entitlement and assignment policy;
- eligible-population and identity policy;
- source-specific meaningful-event and actor-type policy;
- deduplication, lag, coverage, and missingness policy;
- privacy, workforce-use, access, suppression, retention, and correction policy;
- comparison, maturity, and cohort policy;
- contract/cost/currency policy;
- downstream-use and decision policy.

Record the named reviewer/approver and prohibited uses. If the user requests a license, renewal, vendor, security, or workforce decision without an approved rule, return `RULE_REQUIRED`.

Every rerun receives a new receipt version. Preserve the previous cutoff, policies, sources, and output; never backfill it silently.
