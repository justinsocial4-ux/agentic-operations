# Source and Population

Read before using snapshots or producing any comparison.

- Register evidence ID, source/version, schema ID/version, as-of and extraction times, access scope, and source policy ID.
- Require exact declared totals for account rows, assignment records, and entitlement occurrences. Reconcile all three before per-account conclusions.
- Reject duplicate account IDs, duplicate evidence IDs, unregistered evidence, future snapshots, stale-by-policy snapshots, unknown schemas, and negative control totals.
- Do not use cached or partial data as a fallback. An incomplete population is `POPULATION_INCOMPLETE`.
- The helper reviews supplied rows only; it does not claim the source exported every access path unless the customer receipt explicitly proves that scope.
