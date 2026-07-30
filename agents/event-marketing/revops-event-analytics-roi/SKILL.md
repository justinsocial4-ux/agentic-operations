---
name: revops-event-analytics-roi
description: "Produces an evidence-backed event performance review that separates attendance, identity coverage, configured attribution credit, finance-defined return, and causal incrementality. Make sure to use this skill whenever the user asks for event ROI, an event debrief, event-sourced pipeline, cost per attendee or opportunity, event benchmarks, attribution analysis, event budget evidence, or post-event performance—even if they do not name the agent."
metadata:
  category: "Event Marketing"
  phase: "1"
  data_readiness: "approved_population_attribution_and_finance_policies_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved event population, identity, attribution, cost, currency, outcome-maturity, benchmark, and finance-return policy"
  mcps:
    - "Event, CRM, finance, and approved outcome sources in read-only mode"
  minimum_data:
    - "Stable event/participant/opportunity IDs, versioned attribution records, exact cost basis, and explicit metric denominators"
---

# Event Performance And ROI Evidence

Build an auditable event debrief without turning proximity into causality or pipeline into revenue. Report what each evidence layer can prove and return unavailable states for the rest.

## Bundled Resources

- Read `references/data_contract.md` before accepting event, participant, CRM, finance, benchmark, or outcome data.
- Read `references/populations_and_identity.md` before counting registrants, attendees, participants, contacts, meetings, MQLs, or opportunities.
- Read `references/attribution_policy.md` before using campaign influence, time windows, touchpoints, or credit weights.
- Read `references/cost_and_return.md` before calculating costs, return, ROI, revenue, profit, or cash.
- Read `references/benchmarking_and_models.md` before comparing events or using predictions.
- Read `references/platform_boundaries.md` before relying on HubSpot/Salesforce event or attribution outputs.
- Read `references/output_template.md` before producing the debrief.
- Read `references/research_and_claims.md` before repeating benchmark, conversion, speed, labor, pipeline, or ROI claims.
- Use `scripts/event_metrics.py` for exact cost ratios, coverage, attribution rollups, finance-defined return, and direction-aware comparisons.

## Operating Rules

1. Read approved snapshots only. Do not tag campaigns/opportunities, create contacts, update CRM fields, send reports, assign follow-up, change budgets, or write benchmark records.
2. Require versioned customer-approved population, identity, attribution, cost, currency/FX, outcome-maturity, benchmark, finance-return, privacy, and downstream-use policies.
3. Preserve `REGISTERED`, `ATTENDED`, `CANCELLED`, `NO_SHOW`, repeated activity, sponsor/staff, excluded, duplicate, and unknown populations separately. State every denominator.
4. Use stable IDs or approved exact identifiers. Ambiguous fuzzy matches remain `IDENTITY_REVIEW`; never lower a threshold to increase match rate.
5. Minimize participant data. Use pseudonymous IDs and aggregated outputs; exclude names, email, phone, title, social URLs, and free text unless specifically authorized and necessary.
6. A post-event time window or shared contact does not prove event sourcing. Label relationship evidence as `RECORDED_ASSOCIATION`, `MODEL_ATTRIBUTION`, or `CAUSAL_INCREMENTALITY`.
7. Name the CRM platform, attribution model ID/version, eligible interactions, credit rule, lookback/window, contact-role requirements, model settings, sampling, and extraction time. Individual row credit weights are model outputs, not the model's credit-rule definition. If any field is absent, you may total the supplied credit records as `MODEL_CREDIT_RECORDS`, but return `ATTRIBUTION_POLICY_INCOMPLETE`, list the exact gaps, and do not present the rollup as fully auditable model attribution. Model credit is not causal proof.
8. Include active-pipeline, Closed Won, Closed Lost, other, immature, zero, null, duplicate, pre-existing, and unattributed records according to the approved cohort policy. Do not exclude losses to inflate pipeline.
9. Keep opportunity CRM amount, attributed CRM amount, recognized revenue, invoiced amount, cash collected, gross profit, and incremental value separate.
10. Use actual approved event cost for final cost/return metrics. An estimate yields `PRELIMINARY_COST`; preserve cost categories, allocations, tax treatment, currency, dated FX, and zero/null rules.
11. Cost per attendee/meeting/MQL/opportunity requires that exact approved count. Never substitute an opportunity stage for a meeting or an opportunity for an MQL.
12. A finance-defined return requires same-basis approved benefit and cost. Incremental ROI additionally requires an approved counterfactual design and incremental benefit estimate; otherwise return `INCREMENTAL_ROI_UNAVAILABLE`.
13. Opportunity amount and Closed Won status do not prove recognized revenue, profit, or cash. Do not call attributed pipeline revenue.
14. Benchmark only comparable events under identical metric/population/cost/attribution definitions. Report peer count, period, missingness, median, direction, and exact empirical comparison without universal sample or quality labels.
15. For lower-is-better cost metrics, reverse the comparison direction explicitly. Do not call a raw high cost percentile excellent.
16. Do not train or report a forecast without an approved model card, feature definitions, training cutoff, leakage checks, holdout/backtest results, calibration, uncertainty method, and owner. Otherwise return `MODEL_UNAVAILABLE`.
17. Do not manufacture confidence scores, causal explanations, response effects, budget recommendations, pipeline forecasts, or future performance.
18. Produce descriptive findings and prospective validation hypotheses. Budget, targeting, follow-up, attribution-model, or system changes require named human approval.

## Preflight

Record the decision, event ID/type/date/timezone, cutoff, observation/maturity windows, populations, sources, identity key, attribution purpose, amount basis, currencies, cost status, finance benefit basis, benchmark question, model request, privacy scope, and intended use.

Lock policy IDs/versions, owners, effective dates, exclusions, denominators, attribution credit, opportunity states, cost categories/allocations, FX, revenue/profit recognition, incrementality design, benchmark comparability/direction, model card, approver, and no-write boundary.

Stop affected metrics when policy, identity, cost, currency, attribution, maturity, finance, benchmark, or incrementality evidence is absent.

## Workflow

1. **Reconcile populations.** Produce registered/attended/cancelled/no-show/staff/excluded/duplicate/unknown counts and identity coverage.
2. **Build attribution receipt.** Preserve each opportunity, state, amount basis, model credit, maturity, other touches, and exclusions.
3. **Calculate descriptive metrics.** Use exact approved costs and denominators; keep unavailable meeting/MQL/outcome metrics unavailable.
4. **Separate financial layers.** Report CRM amounts, finance-approved benefit, finance-defined return, and incremental ROI independently.
5. **Compare like with like.** Apply the approved peer policy and direction; report peer facts without performance labels.
6. **Prepare validation.** State data gaps, counterfactual/model requirements, owner, approver, and preview-only next decision.

## Worked Example

An event has verified actual cost of USD 100,000, 200 registered, 150 attended, and 120 identities resolved. An approved campaign-influence model gives the event USD 165,000 of model-attributed CRM amount across active-pipeline, Closed Won, and Closed Lost opportunities.

Report USD 500 per registrant, USD 666.67 per attendee, 80% attendee identity coverage, the model/credit receipt, and amounts by state. Do not call USD 165,000 revenue or calculate ROI without a finance-approved benefit basis. Without counterfactual evidence, return `INCREMENTAL_ROI_UNAVAILABLE`.

## Output Contract

Return six artifacts:

1. **Preflight/policy receipt** — event, cutoff, populations, policy versions, sources, cost/amount/currency bases, maturity, benchmark/model status, and owners.
2. **Population/identity table** — exact counts, denominators, coverage, duplicates, exclusions, conflicts, and unknowns.
3. **Attribution/outcome table** — opportunity states, CRM amount, credit, attributed amount, model/settings, maturity, and evidence label.
4. **Metric/finance table** — cost ratios, active-pipeline/won/lost amounts, finance benefit, finance-defined return, incremental ROI, and unavailable states.
5. **Benchmark/model/risk table** — peer definition/count/period/direction, comparison facts, model evidence, confounders, and prohibited conclusions.
6. **Decision preview and receipt** — descriptive finding, prospective validation, owner, named approver, exact proposed decision, and `NO CRM WRITE / NO BUDGET CHANGE / NO FOLLOW-UP ACTION`.

## Failure States

- `POLICY_REQUIRED` — population, identity, attribution, cost, currency, outcome, benchmark, finance, or downstream policy is absent.
- `IDENTITY_REVIEW` — participant/contact/opportunity identity is unresolved or conflicting.
- `COST_BASIS_REQUIRED` — approved event cost categories or allocation are absent.
- `PRELIMINARY_COST` — only an estimate is available.
- `MIXED_CURRENCY` — amounts cannot be combined under an approved dated FX policy.
- `ATTRIBUTION_UNAVAILABLE` — no approved model/association evidence supports credit.
- `ATTRIBUTION_POLICY_INCOMPLETE` — credit records exist but required model settings are absent.
- `OUTCOME_IMMATURE` — the defined outcome window is incomplete.
- `BENEFIT_BASIS_REQUIRED` — finance has not approved the value/benefit basis.
- `FINANCE_APPROVAL_REQUIRED` — cost and benefit bases have not been approved for the same return calculation.
- `INCREMENTAL_ROI_UNAVAILABLE` — no approved counterfactual or incremental benefit exists.
- `INCOMPARABLE_EVENTS` — peer policies, populations, attribution, cost, or maturity differ.
- `MODEL_UNAVAILABLE` — model card, validation, calibration, or uncertainty evidence is absent.
- `APPROVAL_REQUIRED` — a budget, targeting, follow-up, model, or system change lacks named approval.

Never convert an unavailable state into a guessed ROI, revenue amount, cause, or recommendation.
