# Scenario Math

The helper performs only these identities:

1. `candidate_plan_total = sum(candidate_quota for every declared anonymous territory)`
2. `target_difference = candidate_plan_total - corporate_target`
3. `prior_quota_delta = candidate_quota - prior_quota`
4. When coverage state is `accepted`, `coverage_ratio = coverage_amount / candidate_quota`; otherwise the ratio is null.

Use Python `Decimal` from strings. Quantize only derived values to the policy's scale and rounding mode. Preserve signed differences. A positive or negative result is not advice. A ratio is not a fairness, sufficiency, achievability, performance, or forecast label.
