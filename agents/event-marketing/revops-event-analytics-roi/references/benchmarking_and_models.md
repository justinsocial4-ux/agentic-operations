# Benchmarking And Models

Freeze peer eligibility before viewing results: event type/tier, audience/population, geography, period, cost basis, currency/FX, attribution model, outcome maturity, and metric definition.

Report peer count, missingness, median, tie convention, and direction. The helper's performance percentile is the share of peers at or worse than the event: peers greater than or equal for lower-is-better costs; peers less than or equal for higher-is-better benefits. It is descriptive, not statistical confidence.

Do not label peer counts small/adequate or performance good/poor without an approved decision rule.

A prediction requires a model card, training cutoff, cohort, features, target, preprocessing, leakage checks, holdout/backtest, baseline comparison, calibration, uncertainty method, drift/retraining rule, and owner. Residual error alone is not a universal prediction interval.
