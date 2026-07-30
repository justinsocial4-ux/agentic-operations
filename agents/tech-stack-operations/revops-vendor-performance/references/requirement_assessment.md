# Requirement Assessment

## Requirement record

Capture the exact requirement text plus:

- `requirement_id`, contract/policy ID and version, owner, effective dates;
- lane, service/region/tier/severity, comparator, target, unit;
- observation clock, business calendar/timezone, pause/stop rules;
- exclusions, grace periods, rounding rule, aggregation rule, and applicability;
- evidence IDs and approved source-precedence rule.

Do not parse ambiguous natural-language terms into numbers without owner confirmation.

## Allowed states

- `MET`: complete, applicable, non-conflicting evidence satisfies the exact named rule.
- `NOT_MET`: complete, applicable, non-conflicting evidence fails the exact named rule.
- `INDETERMINATE`: missing/immature evidence, zero denominator, unresolved identity, or incomplete rule prevents assessment.
- `NOT_APPLICABLE`: the approved applicability rule excludes this requirement for the service/period.
- `CONFLICTING`: material terms or evidence disagree and the approved precedence rule does not resolve them.

## Exactness rules

Expose numerator, denominator, unit, unrounded value, and approved rounding. Apply the comparator to the unrounded value unless the requirement explicitly says otherwise. Decimal display is not proof of measurement precision.

## Missingness

Never treat missing as zero, passing, failing, average, neutral, or low confidence. Do not redistribute weights because this review has no composite weighting.

## Comparison

Cross-vendor or trend comparison requires identical requirement version, service scope, clock, exclusion rules, source policy, window maturity, and unit/currency. Otherwise return `INCOMPARABLE` and list the mismatches.
