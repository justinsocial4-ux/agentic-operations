# Weekly Revenue Metric Rules

Read this for exact formulas, boundary behavior, and evidence requirements.

## Weekly windows

Use half-open intervals: `start <= timestamp < end`. A record at Monday 00:00 belongs to exactly one week.

## Outcome metrics

- Closed won: `is_closed is true` and `is_won is true`, with close date in the window.
- Closed lost: `is_closed is true` and `is_won is false`, with close date in the window.
- Win rate: won count divided by won plus lost count. When the denominator is zero, return `null`, not 0%.
- Closed-lost amount is not churn. Churn requires customer/contract evidence outside this skill's deal outcome contract.

## Pipeline and new-deal metrics

- Open pipeline: snapshot records where `is_closed is false`.
- New deals: records whose created date falls in the weekly window.
- Keep totals separated by currency unless approved dated conversion rates exist.

## Percentage deltas

| Prior | Current | Output |
|---:|---:|---|
| nonzero | any | `(current-prior)/prior × 100` |
| 0 | positive | `NEW` |
| 0 | 0 | `UNCHANGED_ZERO` |

Do not emit infinity. Treat negative monetary values only under an explicit data policy.

## Deal risk defaults

These are transparent operating defaults to backtest on customer outcomes.

1. `stage_multiplier = days_in_stage / historical_stage_median_days`.
2. `stall_score = clamp((stage_multiplier - 1) / 2, 0, 1)`.
3. `silence_score = 0` below 7 days; otherwise `clamp((days_since_activity - 6) / 14, 0, 1)`.
4. `composite = stall_score × 0.60 + silence_score × 0.40`.
5. High is at least 0.70; Medium is at least 0.40; Low is below 0.40.

Require a positive historical median and real stage-entry/activity timestamps. If either component is missing, composite risk is `UNKNOWN`; do not renormalize the remaining weight.

## Close-date slips

`slip_days = current_close_date - prior_close_date`. Positive values are later. More than 7 days is the default urgent threshold. Zero or negative means no later slip.

## Velocity signal

Compare the current closed-won count with at least eight completed prior weekly counts. Use the population mean and population standard deviation:

- Surge: current > mean + 2.0 standard deviations.
- Slowdown: current < mean - 1.5 standard deviations.
- If history is shorter than eight weeks or baseline variance is zero, return an explicit non-signal state.

These thresholds are heuristics, not predictions.

## Forecast accuracy

Do not call win rate or pipeline delta forecast accuracy. Forecast accuracy requires a saved forecast made before the outcome and the matching actual outcome. If using MAPE, lower is better; report `accuracy = 100% - MAPE` only when every denominator and aggregation choice is defined.
