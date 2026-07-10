# Utilization Metrics

## Named-seat metrics

- Assignment rate: `assigned entitlements / paid entitlements`.
- Observed active-assigned rate: `active eligible humans / eligible assigned humans`.
- Observed active-entitlement rate: `active eligible humans / paid entitlements`, only when the approved license model makes this meaningful.
- Unassigned count: `paid - assigned`.

Return `ZERO_DENOMINATOR` rather than zero when a denominator is zero.

## Event/feature reach

For an approved event, report `eligible active identities with event / approved eligible population`. Preserve event ID/taxonomy, actor type, window, source, coverage, and exclusions. Feature reach is not feature value or user proficiency.

## Cost context

Cost per observed active identity may be calculated only from one exact approved cost basis, currency, and period divided by the matching active population. Label it descriptive. It cannot prove avoidable cost, value, savings, or a removable seat count.

## Prohibited derived measures

Do not generate composite adoption scores, engagement velocity, productivity, intent, risk, confidence, value, waste, utilization “health,” or person/tool tiers.
