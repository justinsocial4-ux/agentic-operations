---
name: revops-quota-setting
description: "Reviews exact anonymous customer-authored quota scenarios without choosing quotas or evaluating workers. Make sure to use this skill whenever the user asks to set, allocate, compare, rebalance, adjust, or validate sales quotas; compare bottom-up and top-down plans; calculate quota changes or pipeline coverage; assess quota fairness or achievability; or prepare quota evidence—even when the request assumes CRM history, rep performance, or industry benchmarks are enough."
metadata:
  category: "Capacity Planning"
  phase: "2"
  data_readiness: "approved_policy_complete_anonymous_plan_and_source_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved purpose, source, scenario, calculation, privacy, workforce, and correction policies"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable policy, source, schema, authorization, population, plan, territory, basis, and receipt IDs"
---

# Quota Scenario Evidence Review

Show only what customer-authored anonymous quota scenarios prove arithmetically. Do not choose a quota, call it fair or achievable, or turn the result into a compensation, territory, account, worker, customer, or CRM action.

## Exact Response Rule

Build the input document, run `scripts/quota_scenario.py`, and return `render_review_output(review_quota_scenarios(document))` byte for byte. The first response byte must be `{`; the final response byte must be the helper's newline after `}`. Do not use Markdown fences or add model prose. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, dates, prohibited uses, or correction paths.
- Read `references/input_and_lineage.md` before accepting plans, anonymous territories, sources, schemas, authorization, or population evidence.
- Read `references/scenario_math.md` before calculating totals, target differences, prior-quota deltas, or coverage ratios.
- Read `references/privacy_and_workforce.md` before accepting worker, quota, attainment, performance, compensation, territory, or account evidence.
- Read `references/current_platform_limits.md` before mapping Salesforce, HubSpot, spreadsheet, finance, or compensation-system evidence.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_boundaries.md` before discussing quota, compensation, territory, account, worker, or customer action.
- Read `references/verification_sources.md` for current official sources supporting platform, governance, and workforce boundaries.
- Use `scripts/quota_scenario.py` for strict validation, population reconciliation, Decimal arithmetic, and exact rendering.

## Operating Rules

1. Work offline and read-only. Do not query, export, cache, schedule, message, alert, write CRM, change quota, change compensation, or modify any territory, account, customer, or worker record.
2. Require an effective customer policy with stable ID/version, owner, human reviewer, approved purpose, prohibited uses, UTC cutoff, timezone, correction and appeal paths, privacy/workforce/compensation review receipts, affected-worker notice receipt, and exact calculation-rule approvals.
3. Accept only pre-supplied structured anonymous plan evidence. Reject names, emails, phones, addresses, domains, URLs, notes, free text, job titles, protected traits, individual activity, attainment, compensation, performance, rank, coaching, departure, retention, absence, schedule, or medical data.
4. Require complete declared source, scenario, and anonymous-territory populations. Missing, duplicate, extra, stale, future, unauthorized, or lineage-conflicting evidence fails closed.
5. Bind every scenario to one approved source receipt, schema version, authorization, population receipt, observation time, capture time, currency, amount basis, period, anonymous territory basis, and coverage basis.
6. Require a customer-authored corporate target and customer-authored candidate and prior quota for every declared anonymous territory. Never create, optimize, infer, or select a quota.
7. Coverage evidence is optional and explicitly stateful. `accepted` requires a customer-supplied amount; `missing`, `conflicting`, or `suppressed` requires no amount and yields no ratio. Never impute coverage.
8. Use Decimal strings. Reject binary floats, non-finite values, negative amounts, zero candidate quota, mixed currency, mixed period, mixed amount basis, mixed territory basis, or mixed coverage basis.
9. Calculate only the submitted candidate-plan total, signed difference from the submitted corporate target, each submitted candidate's signed difference from its prior quota, and accepted same-basis coverage divided by candidate quota.
10. These are arithmetic receipts, not forecasts, recommendations, confidence scores, fairness findings, achievability findings, predictions, causal estimates, or action authorizations.
11. Never recommend increasing, decreasing, approving, rejecting, assigning, or resetting quota; moving an account; changing territory; changing compensation; ranking or evaluating workers; or choosing a scenario.
12. Never use output as the sole or automatic basis for an employment, compensation, customer, financial, or operational decision. Return `HUMAN_REVIEW_REQUIRED` and `action_authorized: false` for every accepted scenario.
13. R1: never characterize evidence, quota, coverage, fairness, or achievability with an adjective unless an exact approved numeric customer rule defines that exact label. This helper emits none of those labels.
14. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
15. Freeze policy, normalized inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate policy, purpose, dates, calculation rules, prohibited uses, human review, and correction path.
2. **Reconcile sources.** Validate bindings, complete source populations, and exact authorization/schema receipts.
3. **Reconcile scenarios.** Match the declared complete scenario population exactly once.
4. **Reconcile territories.** Match each declared anonymous territory exactly once and reject identifiers or extra fields.
5. **Validate bases.** Confirm currency, period, amount, territory, and coverage bases without defaults or inference.
6. **Calculate once.** Let the helper create one input receipt and one calculation receipt per scenario.
7. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: one approved anonymous scenario supplies a corporate target and a complete set of anonymous territory rows. Each row supplies customer-authored candidate and prior quotas; one row supplies accepted same-basis coverage and another declares coverage missing.

Run the helper. Its JSON response records each submitted number once, calculates the plan total and signed target difference once, calculates each prior-quota delta once, calculates only the accepted coverage ratio, preserves the missing lane without a ratio, and marks the result `HUMAN_REVIEW_REQUIRED` with no action authorized.

## Failure Boundary

Missing or incompatible policy, authorization, population, source, schema, timestamp, currency, amount basis, period, territory basis, coverage basis, calculation, privacy, workforce, or correction evidence remains unresolved. Never replace it with CRM retrieval, a vendor benchmark, a default growth rate, stage probability, win rate, confidence score, fuzzy matching, prediction, causal inference, quota advice, monitoring, alerting, customer action, or workforce action.
