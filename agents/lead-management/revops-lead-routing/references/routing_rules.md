# LM-03 Routing Rules

Read this file before changing routing precedence, capacity thresholds, candidate eligibility, or round-robin behavior.

## Rule Precedence

1. Preserve a verified active existing-account owner when policy requires continuity.
2. Use the verified account territory, then primary and secondary territory roles.
3. Use fuzzy-account-plus-city, geographic, or configured industry rules only when stronger context is absent.
4. Use the approved general pool as the last route, never an invented pool.

Default rule-strength labels are 95, 90, 80, 70, 60, and 30. They are policy labels, not calibrated probabilities.

## Eligibility

An owner is eligible only when all are true:

- a stable CRM owner ID exists;
- the owner is active and not archived;
- the owner belongs to the approved pool or territory;
- the owner is not excluded;
- no territory conflict exists;
- capacity is below Critical when capacity-aware routing is active.

## Capacity

```text
score = min(active_opps / average_active_opps, 1) * 50
      + min(pipeline_amount / quota, 1) * 30
      + min(activities_7d / weekly_target, 1) * 20
```

| State | Boundary | Auto-routing posture |
|---|---|---|
| Green | `< 50` | Preferred inside valid route |
| Yellow | `>= 50 and < 85` | Acceptable |
| Red | `>= 85 and < 100` | Caution |
| Critical | `>= 100` | Never auto-route |
| Unknown | missing/stale inputs | Disclose; do not treat as zero |

## Stable Ranking Tuple

Sort by:

1. existing-account-owner flag;
2. territory role: primary, secondary, general;
3. capacity state: Green, Yellow, Red, Unknown;
4. exact vertical-specialist flag;
5. round-robin position;
6. owner ID.

Never use conversion rate to shift extra load to a lower-performing rep.

## Escalation

Any critical flag or two review flags means `MANUAL_REVIEW`. A Red-capacity warning alone is caution, not permission to bypass account or territory policy.
