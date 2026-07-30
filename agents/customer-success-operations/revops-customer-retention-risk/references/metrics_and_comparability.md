# Metrics And Comparability

Treat source, schema, metric ID/version, account-group semantics, population receipt, unit, basis, currency, timezone, and window as part of the fact. A matching display name does not make two metrics equivalent.

Use plain Decimal strings for supplied numeric evidence. Do not convert currency, invent denominators, round into categories, impute missing values, or normalize unlike measures. A current/prior comparison is permitted only when its approved semantics match and the windows are valid and non-overlapping. Otherwise return `NOT_COMPARABLE` or `METRIC_CONFLICT`.

Rules reference facts and one policy-owned threshold receipt. Results do not repeat the values. This prevents model arithmetic and preserves standing R2.
