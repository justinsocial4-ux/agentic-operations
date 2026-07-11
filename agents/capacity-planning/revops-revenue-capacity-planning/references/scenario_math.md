# Scenario Math

The helper performs only these identities:

1. `gap = target - retained_contribution - expansion_contribution`
2. If `gap > 0`, `modeled_units = gap / observed_output_per_capacity_unit`; otherwise modeled units are zero.
3. If requested by policy and scenario, `whole_unit_ceiling` is the mathematical ceiling of positive modeled units; otherwise it is omitted.
4. `unit_difference = modeled_units - current_capacity_units`.

These are scenario outputs, not forecasts or recommendations. A positive unit difference does not mean “hire”; a negative difference does not mean “fire.” It only describes the supplied equation.

Use Python `Decimal` from strings. Quantize derived decimal values only to the policy's declared scale and rounding mode. Preserve signed gap and difference. Do not clamp or reinterpret them. Whole-unit ceiling uses `ROUND_CEILING` only when explicitly enabled.

Do not calculate pipeline coverage, win rate, sales cycle, attrition, ramp, revenue attainment, NRR impact, budget, ROI, confidence, or probability.
