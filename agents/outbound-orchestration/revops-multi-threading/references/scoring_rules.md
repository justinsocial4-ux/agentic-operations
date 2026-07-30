# Coverage and Candidate Scoring Rules

Read this for exact deterministic rules.

## Engagement defaults

- Active: 0–30 days since meaningful activity.
- Cold: 31–90 days.
- Dormant: more than 90 days.
- Uncontacted: no meaningful activity recorded.
- Unknown: activity coverage unavailable.

These are tuneable operating bands.

## Coverage

For required roles, report verified active, inferred-only active, cold/dormant verified, and missing. A single point of failure exists when exactly one distinct stakeholder is active. Do not calculate it when engagement coverage is unknown.

## Candidate priority

| Component | Weight |
|---|---:|
| Role/title fit | 0.30 |
| Department/function fit | 0.20 |
| Seniority fit | 0.15 |
| Relationship/hierarchy evidence | 0.20 |
| Prior meaningful engagement | 0.15 |

Every component must be an explicit 0–1 value. Missing evidence yields an incomplete score, not a neutral default. The weighted total is a sorting aid, not confidence or role probability.

Break ties by stronger relationship evidence, then meaningful engagement, then stable contact ID.
