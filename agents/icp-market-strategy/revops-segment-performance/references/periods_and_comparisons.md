# Periods and Comparisons

Read this file before quarterly, weekly, prior-period, or year-over-year analysis.

- Require half-open UTC intervals `[begin, end)` plus the customer-owned display timezone.
- Assign records by the approved outcome occurrence timestamp, not extraction time or an editable forecast date.
- Comparison periods must be non-overlapping and equal in duration under the approved policy.
- Require identical source schema, outcome mapping, segment definition/version, membership mode, currency/amount basis, duration semantics, and extraction rule.
- Late-arriving or corrected records create a new frozen review; do not blend snapshots silently.
- Return exact count, percentage-point, money, and duration deltas only when their underlying lanes are calculated. Do not call a delta drift, trend, significance, acceleration, or cause.
