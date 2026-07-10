# Scoring and Drift Evidence

Read this file before saying a scoring model drifted or a feature stopped working.

## Evidence labels

- `ASSOCIATION_ONLY`: score tiers have different observed mature-cohort outcomes.
- `DRIFT_SIGNAL`: comparable periods show a material, review-worthy change under a preapproved rule.
- `DRIFT_SUPPORTED`: validation confirms the data pipeline and policy stayed stable, comparable cohorts exist, and an approved statistical or monitoring test crosses its threshold.
- `INSUFFICIENT_EVIDENCE`: score-at-MQL, history, sample, or comparison data is missing.

## Required checks

Before `DRIFT_SUPPORTED`, verify:

1. Score was captured at MQL entry, not overwritten later.
2. Model version, threshold, MQL definition, SQL definition, and conversion window are known.
3. Source, segment, seasonality, routing, and sales-capacity mix are reviewed.
4. History coverage and rejection capture are comparable.
5. The monitoring statistic, threshold, and multiple-testing treatment were approved before inspection.

Score-tier conversion is calibration evidence, not “accuracy.” A 70 score does not imply a 70% conversion probability unless the model was explicitly calibrated that way.

Do not claim causation or auto-deploy new weights. Prepare a review plan or controlled validation instead.
