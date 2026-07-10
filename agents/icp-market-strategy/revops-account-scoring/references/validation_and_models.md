# Validation And Model Boundary

## Rule-policy validation

Freeze the policy before the outcome window. Define population, score purpose, exact outcome, maturity window, exclusions, missingness, and decision rule prospectively. Preserve won, lost, unresolved, no-opportunity, excluded, and missing outcomes. Report score distribution and outcomes by frozen bucket without tuning on the same cohort.

Association does not prove the score or subsequent treatment caused outcomes. Selection, treatment, leakage, sales effort, territory, campaign exposure, and maturity can confound comparisons.

## Predictive claims

Before calling a score predictive/probabilistic, require a model card: target, population, features, training cutoff, leakage controls, train/holdout split, baseline, discrimination and calibration, subgroup/error analysis, uncertainty, data/version, owner, monitoring, and retirement rule. Otherwise return `MODEL_UNAVAILABLE`.

Construct validity matters: demonstrate that the score measures the named concept. A rule score can be reproducible and still fail to measure fit, intent, or likelihood.
