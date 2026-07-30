---
name: revops-icp-development
description: "Builds an evidence-backed ICP review from frozen eligible cohorts while exposing selection bias, missingness, uncertainty, and validation needs. Make sure to use this skill whenever the user asks to define or refine an ICP, analyze won/lost firmographics, find customer-fit segments, review ICP drift, compare industries or company sizes, or operationalize an ideal customer profile—even if they do not name the agent."
metadata:
  category: "ICP and Market Strategy"
  phase: "1"
  data_readiness: "approved_cohort_and_segment_policy_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved ICP decision, cohort, segment, and downstream-use policy"
  mcps:
    - "CRM and approved customer-outcome sources in read-only mode"
  minimum_data:
    - "Frozen eligible opportunity cohort with mature outcomes and versioned firmographic fields"
---

# ICP Evidence Review

Describe which firmographic segments differ in the approved historical cohort. Treat them as hypotheses for prospective validation—not causal customer-fit facts or automatic targeting rules.

## Bundled Resources

- Read `references/data_contract.md` before accepting opportunity, account, outcome, or firmographic data.
- Read `references/cohort_policy.md` before defining eligibility, maturity, outcome, period, or comparability.
- Read `references/segment_analysis.md` before binning, calculating rates, uncertainty, or multiple comparisons.
- Read `references/interpretation_and_bias.md` before naming ICP signals, drift, fit, or business impact.
- Read `references/downstream_use.md` before proposing lead scoring, ABM, routing, exclusion, or alerts.
- Read `references/output_template.md` before producing the review.
- Read `references/research_and_claims.md` before repeating market, labor, decay, confidence, or outcome claims.
- Use `scripts/icp_metrics.py` for exact rates, percentage-point differences, Wilson intervals, and coverage.

## Operating Rules

1. Analyze read-only snapshots. Do not change accounts, scores, routes, campaigns, territories, segments, or CRM records.
2. Require a versioned customer-approved decision, eligible cohort, outcome, segment, currency, and downstream-use policy.
3. Use opportunities eligible by a frozen as-of rule with mature won/lost/other outcomes. Never reconstruct history from current fields.
4. Exclude contact names, email, phone, and unnecessary deal/account identifiers. ICP analysis normally needs pseudonymous deal/account IDs and firmographics only.
5. Preserve raw category values, mapping version, missing bucket, and exclusions. Do not silently merge rare categories, convert ranges to midpoints, impute values, or drop nulls.
6. Keep acquisition outcome, deal amount, cycle duration, retention, expansion, margin, and product usage as separate evidence domains.
7. Name amount basis, currency, dated FX policy, period, and zero/null handling before aggregating money. Never sum mixed currencies directly.
8. Calculate binary win rate as won / (won + lost). Report that denominator plus other/unresolved, eligible, known, and missing counts beside every rate. Other/unresolved and missing records stay visible but are not silently converted into losses or non-fit.
9. Use a preapproved segment/band definition created before inspecting outcomes. Post-hoc bins are exploratory hypotheses only.
10. Report absolute percentage-point differences and Wilson intervals. Do not manufacture confidence scores or call interval overlap a significance test.
11. A significance claim requires a preapproved test, assumptions, multiple-comparison correction, and decision rule. Otherwise return descriptive evidence only.
12. Do not use the legacy 15/30-deal gates, 1.5× baseline rule, p<0.05 default, confidence formula, quartile/decile bands, completeness gates, or drift score.
13. Expose selection bias: historical deals reflect earlier targeting, qualification, product, price, channel, territory, seller behavior, and data coverage.
14. Do not call observational segment differences causal fit, demand, addressable market, buyer intent, future win probability, or expected revenue.
15. Drift requires comparable frozen cohorts, identical policy/mappings, equivalent outcome maturity, and a preapproved metric. Otherwise return `INCOMPARABLE_COHORTS`.
16. Output `PROSPECTIVE_HYPOTHESIS` with a validation plan. If its validation owner is not provided, return `OWNER_REQUIRED`; do not invent a person, team, or role. Do not automatically deprioritize/exclude segments or modify downstream agents.
17. Apply new rules only to future independent cohorts. Require named human approval for downstream operational use.

## Preflight

Record the decision target, cutoff, analysis window, eligible population, pipelines/products/channels, outcome maturity, segment policy, currency/amount basis, sources, and intended downstream use.

Lock policy ID/version, mapping versions, missing-data treatment, comparable cohort rules, predeclared segments, statistical plan, customer-outcome domains, privacy threshold, validation period, approver, and no-write boundary.

If policy, maturity, identity, or outcome evidence is absent, stop the affected analysis instead of borrowing defaults.

## Workflow

1. **Build the frozen cohort.** Reconcile eligible deals/accounts and preserve outcome/missing/exclusion receipts.
2. **Audit each dimension.** Report known/eligible coverage, raw values, mapping version, missing bucket, and fixed bands.
3. **Calculate descriptive evidence.** Use the helper for counts, rates, percentage-point differences, intervals, and coverage.
4. **Check comparability and bias.** Surface prior targeting, pipeline, seller, product, price, geography, time, and missingness differences.
5. **Review customer outcomes separately.** Acquisition alone cannot define a durable ICP; report retention/expansion/margin evidence only when comparable and mature.
6. **Prepare hypotheses.** State supporting/contrary evidence, uncertainty, data gaps, validation population/period, success/kill rule, owner, and approver.

## Worked Example

In an approved 100-deal mature cohort, overall win rate is 60/100 = 60%. A 15-deal segment with 12 wins has an observed 80% rate and +20 percentage points versus overall. Report its exact counts and Wilson interval as a `PROSPECTIVE_HYPOTHESIS`; do not call it statistically significant, 80% future win probability, or the ICP without a preapproved test and independent validation.

## Output Contract

Return six artifacts:

1. **Preflight/cohort receipt** — policy, cutoff, eligibility, maturity, outcome, scope, currency, and sources.
2. **Coverage/bias table** — known/missing/excluded counts, mapping versions, prior-selection mechanisms, and limitations.
3. **Segment evidence table** — won/lost/other, total outcomes, explicit won-plus-lost rate denominator, observed rate, percentage-point difference, interval, and evidence label.
4. **Customer-outcome table** — separate acquisition, amount, cycle, retention, expansion, margin, and unavailable domains.
5. **Comparability/uncertainty table** — cohort differences, statistical plan, multiple comparisons, confounders, and prohibited conclusions.
6. **Hypothesis/action preview** — prospective validation, owner, named approver, downstream change preview, and `NO SCORE / NO EXCLUSION / NO WRITE`.

## Failure States

- `POLICY_REQUIRED` — cohort, outcome, segment, currency, statistics, or downstream policy is absent.
- `IDENTITY_CONFLICT` — deal/account identity is unresolved or duplicated.
- `OUTCOME_IMMATURE` — eligible outcomes are not mature at cutoff.
- `MIXED_CURRENCY` — money cannot be aggregated safely.
- `SEGMENT_UNAVAILABLE` — required field/mapping/coverage is absent.
- `INCOMPARABLE_COHORTS` — drift/comparison policies or maturity differ.
- `INFERENCE_UNAVAILABLE` — statistical assumptions or correction plan is absent.
- `OWNER_REQUIRED` — the prospective validation owner was not provided.
- `APPROVAL_REQUIRED` — downstream operational use lacks human approval.

Never convert a failure state into an ICP score.
