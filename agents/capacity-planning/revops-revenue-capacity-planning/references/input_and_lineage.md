# Input and Lineage

## Accepted evidence

Accept only `customer-supplied-anonymous-aggregate` structured evidence supplied before the run. Each source binding and population receipt must identify its source, version, source kind, schema, authorization, observation time, capture time, and exact scenario IDs. Every bound source must have exactly one complete population.

The declared scenario population and source population must be complete and identical. Reject missing, duplicate, extra, or cross-source scenario IDs. One scenario uses one source receipt; do not merge sources or fill one source from another.

## Required scenario values

Each scenario supplies stable IDs plus currency, amount basis, period ID, anonymous capacity-unit basis, target amount, retained contribution, expansion contribution, current capacity units, observed output per capacity unit, and whether the approved whole-unit ceiling is requested.

All numeric inputs are JSON strings. Floats are rejected because their binary representation can silently change decimal facts. Values must share the declared currency, amount basis, period, and capacity-unit basis.

## No substitutions

Never derive missing values from industry reports, vendor blogs, CRM defaults, account ratios, job titles, quotas, compensation, or another scenario. `SOURCE_REQUIRED` is safer than plausible-looking arithmetic without lineage.
