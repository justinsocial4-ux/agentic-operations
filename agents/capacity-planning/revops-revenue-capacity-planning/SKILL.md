---
name: revops-revenue-capacity-planning
description: "Calculates exact anonymous revenue-capacity scenario arithmetic from complete customer-supplied inputs without recommending staffing action. Make sure to use this skill whenever the user asks how many reps or CSMs they need, requests a revenue capacity or headcount plan, wants hiring timing or budget impact, asks for pipeline-to-capacity math, wants a what-if model, or asks to rank, hire, replace, allocate, or evaluate workers—even when the request assumes CRM history or industry benchmarks are enough."
metadata:
  category: "Capacity Planning"
  phase: "2"
  data_readiness: "approved_policy_complete_anonymous_inputs_and_source_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved purpose, source, scenario, calculation, privacy, workforce, and correction policies"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable policy, scenario, source, schema, authorization, population, calculation, and receipt IDs"
---

# Revenue Capacity Scenario Review

Show only what a complete anonymous scenario proves arithmetically. Do not turn modeled capacity units into a hiring, firing, quota, territory, budget, recruiting, performance, or forecast decision.

## Exact Response Rule

Build the input document, run `scripts/capacity_scenario.py`, and return `render_review_output(review_capacity_scenarios(document))` byte for byte. The first response byte must be `{`; the final response byte must be the helper's newline after `}`. Do not use Markdown fences or add model prose. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, dates, prohibited uses, or correction paths.
- Read `references/input_and_lineage.md` before accepting scenario values, sources, schemas, authorization, or population evidence.
- Read `references/scenario_math.md` before calculating gaps, modeled units, ceilings, or differences.
- Read `references/privacy_and_workforce.md` before accepting role, customer, owner, worker, quota, activity, ramp, attrition, or performance data.
- Read `references/current_platform_limits.md` before mapping Salesforce, HubSpot, spreadsheet, finance, or HR evidence.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_boundaries.md` before discussing headcount, recruiting, budget, quota, territory, customer, or worker action.
- Read `references/verification_sources.md` for the current official sources supporting platform, arithmetic, and governance boundaries.
- Use `scripts/capacity_scenario.py` for strict validation, population reconciliation, Decimal arithmetic, and exact rendering.

## Operating Rules

1. Work offline and read-only. Do not query, export, cache, schedule, message, alert, write CRM, change a budget, or modify any customer or worker record.
2. Require an effective customer policy with stable ID/version, owner, human reviewer, approved purpose, prohibited uses, UTC cutoff, timezone, calculation policy, and correction path.
3. Accept only pre-supplied structured anonymous aggregates. Reject names, emails, phones, addresses, domains, URLs, notes, free text, job titles, protected traits, individual activity, quota, attainment, compensation, departure, ramp, retention, ranking, or performance fields.
4. Require complete declared source and scenario populations. Missing, duplicate, extra, stale, future, unauthorized, or conflicting evidence fails closed.
5. Bind every scenario to one approved source receipt, schema version, authorization, population receipt, observation time, capture time, currency, amount basis, period, and anonymous capacity-unit basis.
6. Require user-supplied target, retained contribution, expansion contribution, current anonymous capacity units, and observed output per anonymous capacity unit. Never supply or infer a benchmark, attrition rate, ramp curve, pipeline ratio, conversion rate, cost, quota, or account-load rule.
7. Use Decimal strings. Reject binary floats, non-finite values, negative contributions, non-positive observed output per unit, mixed currency, mixed period, or mixed basis.
8. Calculate only `target - retained - expansion`, the positive-gap modeled units, an optional whole-unit ceiling under the approved rounding policy, and the signed difference from current anonymous units.
9. A modeled unit is a scenario variable, not a person, role requisition, budget approval, forecast, confidence score, adequacy label, causal estimate, or action authorization.
10. Never claim that a scenario will hit revenue, maintain retention, prevent churn, improve performance, lower cost, or predict future outcomes.
11. Never recommend hiring, firing, replacing, promoting, allocating, ranking, coaching, monitoring, changing quota, changing territory, starting recruiting, approving spend, or selecting a scenario.
12. Never use output as the sole or automatic basis for an employment, compensation, customer, financial, or operational decision. Return `HUMAN_REVIEW_REQUIRED` and `action_authorized: false` for every accepted scenario.
13. R1: never characterize evidence adequacy with an adjective unless an exact approved numeric customer rule defines that exact label. This helper emits no adequacy adjective.
14. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
15. Freeze policy, normalized inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate policy, purpose, dates, calculation rules, prohibited uses, human review, and correction path.
2. **Reconcile sources.** Validate source bindings, complete source populations, and exact authorization/schema receipts.
3. **Reconcile scenarios.** Match the declared complete scenario population exactly once.
4. **Validate inputs.** Confirm anonymous bases, Decimal strings, compatible units, and source lineage without defaults or inference.
5. **Calculate once.** Let the helper create one input receipt and one calculation receipt per scenario.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: one approved anonymous scenario supplies a target, retained contribution, expansion contribution, current capacity-unit count, and observed output per capacity unit on one exact currency, amount, period, and unit basis.

Run the helper. Its JSON response records the supplied values once, calculates the signed gap and modeled anonymous units once, and marks the result `HUMAN_REVIEW_REQUIRED` with no action authorized. It does not say to hire anyone or claim the target will be reached.

## Failure Boundary

Missing or incompatible policy, authorization, population, source, schema, timestamp, currency, amount basis, period, unit basis, calculation, privacy, workforce, or correction evidence remains unresolved. Never replace it with CRM retrieval, a vendor benchmark, a confidence score, fuzzy matching, prediction, causal inference, staffing advice, budget advice, monitoring, alerting, customer action, or workforce action.
