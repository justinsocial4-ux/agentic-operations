# Cohort and Denominator Rules

Read this file before calculating a rate or comparing periods.

## Cohort definition

Anchor cohorts on `mql_entered_at`, not current status or SQL date. Use the same conversion window for every episode. At cutoff, split episodes into:

- `PENDING_NOT_MATURE`: deadline is after cutoff; exclude from outcome rates.
- `MATURE_CONVERTED`: SQL occurred on or before deadline.
- `MATURE_REJECTED`: approved rejection occurred on or before deadline and precedence assigns rejection.
- `MATURE_RECYCLED_OR_OTHER`: approved non-rejection terminal outcome.
- `MATURE_UNRESOLVED`: no qualifying terminal event by deadline.

Outcome precedence must be customer-approved. If conflicting events cannot be resolved, use `DATA_CONFLICT` rather than choosing the favorable outcome.

## Rates

Every rate must name its numerator and denominator. Use mature MQL episodes as the denominator for within-window conversion, rejection, and unresolved rates.

Never add pending episodes to the denominator. Never remove unresolved mature episodes merely because they lack a tidy status.

## Comparisons

Compare only when both cohorts share:

- lifecycle mapping and episode rule
- conversion window and cutoff logic
- history availability
- filters and deduplication
- source/segment definitions

Report percentage-point change and relative percent change separately. A zero baseline makes relative change undefined.

Use uncertainty intervals and a proportion test as descriptive evidence. A p-value is not the probability that a hypothesis or recommendation is correct. Unless an alpha or other decision rule was approved before inspection, do not translate the p-value into significant/not significant, weak/strong, distinguishable/indistinguishable, noise, confirmed, or insufficient-evidence language. State only the observed effect, interval, p-value, and absence of an approved verdict rule. Multiple comparisons need an approved correction. Observational cohorts do not prove that source, score, owner, or campaign caused the difference.

## Small samples

There is no universal record-count boundary that makes a cohort reliable. Show the actual counts and interval width. Suppress rankings when intervals are too wide for the user's decision or when a customer-approved minimum is not met.
