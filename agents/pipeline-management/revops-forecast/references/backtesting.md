# Backtesting and Bias

Read before discussing forecast accuracy, confidence, stability, calibration, or rep performance.

Use frozen forecasts and the closed-won actual under the identical approved amount basis for matching periods, scope, currency, and policy. Do not change the basis between forecast and actual.

```text
error = forecast - actual
MAE = mean(abs(error))
WAPE = sum(abs(error)) / sum(actual)
aggregate_bias = sum(error) / sum(actual)
```

Positive bias means overforecast; negative bias means underforecast. WAPE and bias are undefined when total actual is zero. Keep such periods and report currency errors; do not discard them.

Do not exclude lost deals or large misses merely because they exceed a threshold. Exclusions require a preapproved data-error rule and an exclusion receipt.

Rep review requires repeated submitted forecasts across periods. Report period count, actuals, errors, and policy changes. Do not turn limited history into an accuracy or coaching label.

Backtests are historical evidence, not a guarantee of future accuracy. Any threshold chosen after seeing results applies only to future independent periods.
