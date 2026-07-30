# Scope and Policy

## Allowed purpose

The only allowed purpose is `revenue_capacity_scenario_review`: calculate transparent arithmetic over a complete, anonymous, customer-supplied scenario. The skill does not decide whether the scenario is sensible or what anyone should do.

Require a stable policy ID and version, owner role, human reviewer role, UTC effective and cutoff times, optional UTC expiry, IANA timezone, correction path, calculation policy, source bindings, and all prohibited uses required by the helper.

## Fail-closed authority

Reject an absent, expired, not-yet-effective, or mismatched policy. Reject a source whose authorization does not cover the cutoff. Do not interpret silence as permission. A correction produces a new policy/scenario version; it never overwrites the frozen receipt.

## Prohibited-use floor

The policy must prohibit employment decisions, compensation decisions, worker ranking, worker monitoring, quota changes, territory changes, recruiting action, budget approval, CRM writes, alerts, forecasts, confidence scores, benchmark substitution, and customer action. Customers may add stricter prohibitions.
