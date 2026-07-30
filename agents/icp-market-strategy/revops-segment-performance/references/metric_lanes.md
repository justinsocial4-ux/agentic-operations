# Metric Lanes

Read this file before calculating win rate, amounts, duration, velocity, ACV, ARR, or forecast accuracy.

- Population lane: total closed outcomes, won count, lost count, and exact approved win-rate rounding. Preserve the denominator.
- Money lane: calculate won-amount total and median only from supplied compatible non-negative Decimal strings. Missing won amounts make this lane unresolved; never impute.
- Duration lane: calculate median elapsed seconds only from supplied approved begin/stop occurrence timestamps. Missing or negative duration makes this lane unresolved.
- Keep lanes independent. Missing money or duration does not erase a valid population lane.
- Opportunity Amount is not automatically ACV, ARR, bookings, revenue, margin, or price. Use the policy’s exact business basis label.
- Forecast accuracy requires timestamped forecast snapshots, a target event, horizon, scoring rule, and validation contract. It is outside this helper.
