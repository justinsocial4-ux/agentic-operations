---
name: revops-customer-retention-risk
description: "Reviews a complete pseudonymous customer population and separate usage, support, survey, engagement, contract, billing, and observed-outcome evidence against exact customer-approved rules. Make sure to use this skill whenever the user asks to assess retention risk, customer health, churn signals, renewal evidence, adoption changes, support burden, NPS or CSAT evidence, engagement, contract renewal records, billing status, or accounts at risk—even if they ask for a score, ranking, forecast, playbook, CRM update, or outreach action."
metadata:
  category: "Customer Success Operations"
  phase: "2"
  data_readiness: "approved_policy_complete_population_exact_identity_source_schema_metric_and_lane_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved retention-evidence, identity, metric, privacy, access, and correction policies"
  mcps:
    - "Approved CRM, product, support, survey, contract, billing, or warehouse evidence in read-only mode"
  minimum_data:
    - "Stable policy, account, source, schema, metric, population, identity-link, fact, and receipt IDs"
---

# Customer Retention Evidence Review

Report what supplied records prove, lane by lane. Do not turn usage, tickets, surveys, activities, contracts, bills, or outcomes into a churn prediction, health score, customer ranking, causal claim, or action plan.

## Exact Response Rule

Build the input document, run `scripts/retention_evidence.py`, and return `render_review_output(review_retention_evidence(document))` byte for byte. The first response byte must be `{`; the final response byte must be the helper's newline after `}`. Do not use Markdown code fences. Write no model-generated introduction, table, calculation, summary, correction, or text outside helper stdout. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, rules, dates, authority, precedence, or reviewer roles.
- Read `references/population_and_identity.md` before linking accounts or accepting a source population.
- Read `references/evidence_lanes.md` before using usage, support, survey, engagement, contract, billing, or outcome evidence.
- Read `references/metrics_and_comparability.md` before comparing values, windows, currencies, units, or metric versions.
- Read `references/privacy_and_workforce.md` before accepting customer, contact, worker, activity, survey, support, contract, or billing data.
- Read `references/current_platform_limits.md` before mapping HubSpot, Salesforce, Amplitude, support, survey, contract, or billing fields.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_boundaries.md` before discussing predictions, rankings, outreach, playbooks, forecasts, CRM changes, or workforce action.
- Use `scripts/retention_evidence.py` for strict validation, Decimal handling, reconciliation, independent rule evaluation, and exact output rendering.

## Operating Rules

1. Work read-only. Do not query or modify any source, CRM, task, message, alert, schedule, account, contract, bill, forecast, playbook, owner, or worker record.
2. Require an effective customer policy with stable ID/version, owner, named human reviewer, approved purpose, prohibited uses, UTC cutoff, timezone, correction path, source/schema/metric bindings, and explicit rule precedence.
3. Reconcile the complete frozen declared account population exactly. Never omit accounts with zero events, missing evidence, conflicts, or unresolved links.
4. Use stable pseudonymous account and external-account IDs. Reject names, domains, emails, phones, addresses, free text, protected traits, contact activity, support text, survey text, seller or CSM performance, and fuzzy linkage fields.
5. Require exact customer-owned identity links. Preserve missing, duplicate, one-to-many, many-to-one, source/schema, and link-version conflicts; never choose a link silently.
6. Keep usage, support, survey, engagement, contract, billing, and observed outcome evidence independent. Never combine lanes into one score, probability, tier, priority, or forecast.
7. Require each lane's exact source, schema, metric definition/version, population, window, timezone, unit, basis, currency where relevant, occurrence time, and completeness receipt.
8. Missing survey response is unknown. Ticket volume, usage change, activity occurrence, renewal date, auto-renew field, billing state, and observed outcome do not prove intent, cause, satisfaction, legal effect, or future behavior.
9. Compare current and prior values only when source, schema, metric, unit, basis, currency, population semantics, and non-overlapping windows match exactly. Otherwise return `NOT_COMPARABLE` or `METRIC_CONFLICT`.
10. `NO_EVENT_RECORDED` is allowed only when the exact source population is declared complete for the account and lane. Missing or incomplete evidence is `SOURCE_REQUIRED`.
11. Evaluate exact applicable customer rules independently. If top-precedence rules overlap or conflict, return `HUMAN_REVIEW_REQUIRED`; never choose, average, or override them.
12. A rule match is only a policy receipt. It is not churn, risk, urgency, priority, cause, severity, a recommendation, or permission to act.
13. Never estimate churn, renewal, expansion, ARR at risk, customer value, confidence, sentiment, health, intervention effect, legal compliance, revenue recognition, customer or worker performance, or business impact.
14. R1: never characterize evidence adequacy with `small`, `large`, `enough`, `limited`, `insufficient`, `good`, `poor`, `high`, or `low` unless an approved numeric rule defines that exact label.
15. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
16. Freeze policy, normalized inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate policy, purpose, prohibited uses, dates, bindings, rules, roles, privacy, access, and correction path.
2. **Reconcile population.** Validate declared accounts, source populations, exact identity links, and every missing, duplicate, extra, or conflicting ID.
3. **Register lanes.** Validate each fact's lane, metric definition, source/schema, window, timezone, unit, basis, currency, population receipt, and occurrence time.
4. **Compare carefully.** Use Decimal and compare only exact current/prior definitions; preserve missingness and incompatibility.
5. **Evaluate rules.** Return neutral rule states with fact and policy-rule receipt references and named human-review roles.
6. **Render once.** Paste exact helper stdout and nothing else.

## Failure Boundary

Missing or incompatible policy, population, identity, source, schema, metric, window, timezone, unit, basis, currency, privacy, access, or correction evidence remains unresolved. Never replace it with a default, proxy, fuzzy match, score, probability, tier, causal story, playbook, forecast, or action.
