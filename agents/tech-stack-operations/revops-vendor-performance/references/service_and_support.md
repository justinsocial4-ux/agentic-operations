# Service And Support Evidence

## Availability

Use the contract-defined service clock:

`eligible_minutes = total_clock_minutes - approved_excluded_minutes`

`availability_pct = (eligible_minutes - in_scope_downtime_minutes) / eligible_minutes × 100`

Require service, region, customer impact, incident start/end, timezone, overlap handling, exclusions, maintenance classification, and source. If eligible minutes are zero, return `INDETERMINATE`.

Do not use a vendor's global status percentage for a customer-specific service unless the contract/policy explicitly permits it. Do not infer downtime from support resolution time.

## Support clocks

Response, restoration, resolution, workaround, and update cadence are different measures. Preserve severity, entitlement tier, business-hours calendar, pauses, customer-wait time, reopenings, merges, and matured-case rule.

The denominator is all eligible mature cases under the named rule—not only closed cases. An open case can be assessed only if the approved clock has matured or breached; otherwise it remains immature.

Report counts of met, not met, immature, excluded, conflicting, and indeterminate cases. Never use an average alone to prove a percentile or per-case SLA.

## Source conflict

Keep vendor status, customer telemetry, incident tickets, and independent monitoring as distinct evidence. Record overlapping incident IDs and disagreement. A conflict is a review item, not a reason to average observations.

## Customer impact

Observed affected users, workflows, or duration can be reported when sourced. Do not convert operational impact into revenue loss, causality, or damages without an approved method and evidence.
