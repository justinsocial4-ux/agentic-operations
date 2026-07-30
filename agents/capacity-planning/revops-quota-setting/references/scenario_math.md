# Scenario Math

The helper performs only these identities:

1. `candidate_plan_total = sum(candidate_quota for every declared anonymous territory)`
2. `target_difference = candidate_plan_total - corporate_target`
3. `prior_quota_delta = candidate_quota - prior_quota`
4. When coverage state is `accepted`, `coverage_ratio = coverage_amount / candidate_quota`; otherwise the ratio is null.

Use Python `Decimal` from strings. Each input is bounded to 28 total digits and scale 0–6. The helper sizes a local calculation context from that limit, the approved scales, and the declared territory count so accepted sums, differences, and quantization do not depend on the process-global Decimal context. Coverage ratios use exact integer numerator/denominator remainders for `down` or `half_even` rounding, avoiding intermediate or double rounding. Derived totals may contain more digits than one accepted input. Quantize only derived values to the policy's scale and rounding mode. Preserve signed differences. A positive or negative result is not advice. A ratio is not a fairness, sufficiency, achievability, performance, or forecast label.
