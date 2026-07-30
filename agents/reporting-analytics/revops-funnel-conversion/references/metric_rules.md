# Metric Rules

Read this file before calculating conversion, dwell, trends, or segment comparisons.

## Transition conversion

```text
transition_rate = advanced_within_window / mature_entries_to_prior_stage
pending = entered_prior_stage - mature_entries_to_prior_stage
not_advanced = mature_entries_to_prior_stage - advanced_within_window
```

Pending records are excluded, not failures. Report a Wilson interval for decision-bearing rates.

## Funnel reach

Ordered reach counts answer “how many anchored episodes ever reached each stage under the policy?” They are not the same as transition denominators because later transitions can have different maturity windows.

## End-to-end conversion

Define the anchor and end-to-end observation window. Use only anchored episodes whose end-to-end deadline is at or before the cutoff. Do not divide final-stage records by all recent first-stage records.

## Dwell and current age

- Completed dwell: exit timestamp minus entry timestamp for completed visits.
- Current age: cutoff minus latest valid entry timestamp for records still in stage.
- Never mix these distributions.
- Report count, median, p75, and p90; show the repeated-visit rule.

## Comparisons

Require identical policy, anchor, windows, filters, coverage, and dimension definitions. Report absolute percentage-point and relative changes separately. A zero baseline makes relative change undefined.

A p-value is not the probability that a hypothesis is true. Without a preapproved rule, report intervals and p-values descriptively and do not convert them to significant/weak/strong/noise verdicts. Once results have been seen, any new rule is prospective and must be evaluated on an independent future cohort.

Do not compare interval overlap or statistical distinguishability across different transitions as evidence that one transition is or is not a bottleneck. The transitions have different populations, windows, and business questions. Report each interval independently.

Show sample counts and interval widths. Terms such as small, large, adequate, reliable, or enough require a decision-specific requirement approved before inspection; do not invent one after seeing the counts.

## Missing dimensions

Freeze dimensions at the approved point. Put missing values in `UNKNOWN`. Never drop unknowns from the denominator without showing the exclusion and its effect.
