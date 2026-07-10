# Metrics and Scoring

## Ratios

```text
seat_utilization = active_entitled_users / licensed_seats
feature_adoption = adopted_eligible_features / eligible_features
evidence_coverage = known_records / eligible_records
```

Define every numerator, denominator, window, and exclusion in the approved policy. A zero denominator returns unknown. Utilization above 1 may reflect overage, identity defects, shared credentials, test traffic, contract mismatch, or genuine pressure; it is not automatically an expansion conclusion.

Unused entitlement and unpurchased whitespace are different:

- unused entitlement: purchased capacity or product access not observed in use
- unpurchased whitespace: product/SKU not present in the approved contract/catalog mapping

## Policy scores

Use a weighted score only when components are on approved 0–1 scales, every required component is present, weights are non-negative, the component and weight keys match, and weights total exactly 1.

```text
policy_score = sum(component_value × approved_weight)
```

Do not impute missing components, renormalize weights, or call the result probability/confidence. Calibration requires a defined outcome, archived predictions made before outcomes, representative evaluation data, and reported validation.

## Eligibility

Eligibility is a rule evaluation, not a score. Report each rule as pass, fail, or unknown. Required unknown evidence yields `ELIGIBILITY_UNKNOWN`; any approved blocker yields `NOT_ELIGIBLE`.

## Value

```text
value_preview = approved_quantity × verified_unit_price
```

Name the amount basis, price source/version, currency, effective date, discount treatment, and tax treatment. Do not estimate value as a percentage of ARR unless a named customer policy explicitly requires that method.
