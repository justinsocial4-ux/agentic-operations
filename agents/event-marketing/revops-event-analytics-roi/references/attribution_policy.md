# Attribution Policy

Separate:

1. **Recorded association** — a platform links an event/campaign, person, and opportunity.
2. **Model attribution** — a configured model assigns credit under stated rules.
3. **Causal incrementality** — a counterfactual design estimates what the event changed.

For model attribution, record platform, model ID/version, first/last/even/custom rule, credit weight, eligible interactions, contact-role rules, lookback/window, model settings, processing/sampling, opportunity state, and extraction cutoff.

Individual row credit weights are outputs of the model, not its credit-rule definition. If credit records exist but any required setting is missing, calculate them only as `MODEL_CREDIT_RECORDS`. Return `ATTRIBUTION_POLICY_INCOMPLETE`, name each missing field, and withhold the claim that the model rollup is fully auditable.

Time proximity is not sourcing. Include pre-existing, active-pipeline, won, lost, other, immature, duplicate, and unattributed records according to policy. The same opportunity must not be double counted within one event rollup.
