# Comparisons And Maturity

Compare windows only when they are equal duration, non-overlapping, complete, and governed by the same source, event, population, identity, exclusion, lag, and cohort policies.

Report:

- current and prior numerators/denominators/rates;
- percentage-point change;
- denominator and population changes;
- relative change only when the prior rate is nonzero;
- source coverage and policy versions for both windows.

If the prior rate is zero, return `RELATIVE_CHANGE_UNAVAILABLE`. If any definition or coverage is not comparable, return `INCOMPARABLE`. If either window is incomplete, return `IMMATURE_WINDOW`.

Do not compare cumulative 30-day and 90-day distinct-user counts as matched periods. Do not infer seasonality, displacement, training need, satisfaction, causality, or future behavior from a trend.

Cross-tool comparisons additionally require equivalent business questions and metrics. Raw events from different platforms are usually not comparable.
