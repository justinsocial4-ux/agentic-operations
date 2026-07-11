# Comparability and Calculation

## Comparison gate

Two cells are comparable only when all of these match exactly:

- cohort ID;
- metric code;
- source ID, schema version, and authorization ID;
- unit;
- currency and amount basis for money;
- period duration.

The periods must be non-overlapping, the prior period must end no later than the current period begins, and both must end on or before the policy cutoff.

## Exact math

Parse values from decimal strings. Reject binary floats, booleans, non-finite values, negatives, fractional counts, and money without currency or amount basis. Calculate only:

`signed_delta = current_value - previous_value`

Do not calculate percentages, rates, ranks, normalized scores, confidence, forecasts, or causal effects. Do not round an input. Render normalized Decimal strings without exponent notation.

## Suppression first

If the cohort member count is below the approved minimum, suppress every cell for that cohort before calculation. A comparison referencing a suppressed cell returns a suppressed receipt without values or a delta.
