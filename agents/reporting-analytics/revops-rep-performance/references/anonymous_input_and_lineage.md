# Anonymous Input and Lineage

## Allowed shape

Accept only structured aggregate evidence with no person-level row. The document must declare complete populations for sources, cohorts, periods, cells, and comparisons. Every declared ID must appear exactly once and no undeclared member may appear.

Each source receipt binds a system label, schema version, authorization ID, population receipt ID, observation time, and capture time. The source observation must occur after every bound period ends. Each cohort binds only an opaque cohort ID, the one policy-approved dimension, a customer-supplied member count, a population receipt, and an anonymity receipt. Each period binds UTC beginning and ending timestamps. Each cell binds one source, cohort, period, metric, approved aggregation rule, unit, and value.

## Forbidden content

Reject direct identifiers, pseudonyms, names, worker or customer IDs, emails, phones, addresses, domains, URLs, notes, titles, free text, recordings, transcripts, protected traits, health, leave, compensation, quota, attainment, ranking, scores, and individual activity. Reject suspicious identifier-like or contact-like strings even under an unexpected key.

## Population proof

Do not treat the latest timestamp or a successful API response as population completeness. Require exact declared/observed ID equality at every level. Partial pages, first-N results, omitted nulls, deduplicated rows without receipts, and silent exclusions fail closed.
