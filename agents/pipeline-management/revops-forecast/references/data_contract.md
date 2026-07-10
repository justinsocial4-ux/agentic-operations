# Forecast Data Contract

Read before querying a CRM or accepting a snapshot.

Required fields: forecast-unit ID, pipeline, snapshot timestamp, forecast period, amount, currency, category ID, category label, close date, closed/won state, owner/territory, and policy version. Calculated expectation additionally requires probability, probability source, model version, and calibration target.

Submitted forecasts require submitter, submission timestamp, period, currency, scope, and value. Backtesting requires archived submission/calculated snapshots plus the closed-won actual under the identical approved amount basis for the exact period and scope.

Fail closed on duplicate units, mixed currency without dated FX, null amounts hidden as zero, negative amounts without policy, close dates outside the period, active/closed contradictions, and current values presented as historical snapshots.

Use Decimal-safe arithmetic. Record every exclusion and its amount.
