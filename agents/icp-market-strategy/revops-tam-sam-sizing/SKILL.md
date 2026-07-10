---
name: revops-tam-sam-sizing
description: "Builds a read-only TAM, SAM, or obtainable-market scenario from supplied population, source-unit, price-basis, serviceability, overlap, and horizon evidence without inventing market counts, capture rates, confidence, rankings, forecasts, or GTM actions. Make sure to use this skill whenever the user asks to size a market, calculate TAM or SAM, estimate addressable companies or revenue, compare market-size scenarios, review a market-sizing model, or validate a segment opportunity—even when they do not name the agent."
metadata:
  category: "ICP & Market Strategy"
  phase: "2"
  data_readiness: "approved_population_price_serviceability_aggregation_and_scenario_policies_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved source-unit, coverage, taxonomy, geography, price, serviceability, aggregation, freshness, obtainability, privacy, and decision policies"
  mcps:
    - "Approved market, finance, and CRM evidence in read-only mode"
  minimum_data:
    - "Stable segment/evidence IDs, exact source unit and coverage, supplied counts and price basis, cutoff, and named approval roles"
---

# Market-Size Evidence Review

Validate a supplied market-size scenario. Do not discover, rank, forecast, or select a market.

## Exact Response Rule

Build the input document, run `scripts/market_sizing_evidence.py`, and return `render_review_output(review)` byte for byte. Write no model-generated introduction, table, calculation, summary, correction, or text outside helper stdout. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting the purpose, definitions, roles, or requested decision.
- Read `references/population_sources.md` before using firms, establishments, accounts, locations, employees, source counts, taxonomies, or geographies.
- Read `references/price_evidence.md` before using ACV, ARR, spend, revenue, price, currency, period, or contract measures.
- Read `references/serviceability_and_obtainability.md` before calculating SAM, SOM, capture, share, capacity, or a horizon scenario.
- Read `references/aggregation_and_overlap.md` before summing segments or comparing periods.
- Read `references/uncertainty_and_validation.md` before describing precision, confidence, adequacy, stability, or validation.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_and_research_limits.md` before discussing rankings, quotas, budgets, campaigns, territories, lists, CRM changes, benchmarks, vendors, or outcomes.
- Use `scripts/market_sizing_evidence.py` for all validation, Decimal arithmetic, exception states, aggregation, and exact output rendering.

## Operating Rules

1. Work read-only. Do not call market databases, query a CRM, create a list, change a record, allocate budget, set quota, assign territory, schedule work, send a message, or trigger a campaign.
2. Require a customer-owned policy with stable IDs/versions, exact definitions of total/serviceable/obtainable, cutoff, source unit, coverage, taxonomy, geography, price basis, currency, period, freshness, overlap, horizon, roles, correction path, and prohibited uses.
3. Treat firms, establishments, legal accounts, locations, contacts, employees, and vendor records as different units. Never relabel or combine them.
4. Preserve the source dataset, version, year, as-of/extraction times, coverage, geography, taxonomy/code, disclosure/suppression state, and evidence ID for every count.
5. Use only supplied counts. Suppressed, unavailable, conflicting, future, stale-by-policy, mismatched, or missing source evidence stays unresolved; never substitute a benchmark, cache, analyst estimate, zero, or model guess.
6. Use only a supplied non-negative Decimal-compatible price with exact currency, period, business basis, source/version, cutoff, and evidence ID. Do not infer ACV from won deals or mix ARR, bookings, recognized revenue, spend, contract value, or list price.
7. Calculate total-addressable scenario as compatible supplied count times compatible supplied price. This is a scenario value, not a forecast or market truth.
8. Calculate serviceable value only from a supplied serviceable count bounded by the same total universe and governed by an approved serviceability receipt. Never invent competition, geography, product-fit, or reach discounts.
9. Calculate obtainable value only from an approved exact fraction and horizon receipt applied to the serviceable value. Label it `SCENARIO_NOT_FORECAST`; never use sales win rate as market share.
10. Sum segments only when a verified-disjoint aggregation receipt exists and every segment has compatible unit, coverage, geography/taxonomy semantics, currency, period, and price basis. Otherwise return `AGGREGATION_UNAVAILABLE`.
11. Do not infer why a source count changed. Period comparisons require matched definitions and a supplied decomposition receipt.
12. Do not rank segments, choose a market, create a top list, or infer intent, fit, priority, probability, revenue, quota, pipeline, ROI, or causal outcome.
13. R1: never characterize data adequacy with `small`, `large`, `enough`, `limited`, or `insufficient` unless an approved numerical policy defines that exact label. Report helper states and source receipts.
14. R2: return one helper-rendered response. Every numeric value must come from the helper and appear only in that response; never recompute, narrate, round differently, or self-correct.
15. Freeze the policy, inputs, helper output, and receipt. New evidence creates a new review version.

## Workflow

1. **Freeze policy.** Validate definitions, units, coverage, price basis, freshness, overlap, horizon, roles, and prohibited uses.
2. **Register evidence.** Validate source/version/year/as-of/extraction/access receipts.
3. **Validate segments.** Reconcile one universe row and one price row per segment; preserve source exceptions.
4. **Evaluate scenarios.** Apply supplied serviceable counts and obtainable fractions only through approved receipts.
5. **Aggregate conditionally.** Sum only compatible, complete, verified-disjoint segments.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: a supplied firm count, a compatible annual price receipt, a bounded serviceable count, and an approved horizon fraction for one segment.

Output: the helper returns sourced total and serviceable scenario values plus `SCENARIO_NOT_FORECAST` for the obtainable lane. It prints no ranking or action and does not repeat any value in prose.

## Failure Boundary

Missing or incompatible evidence remains `SOURCE_REQUIRED`, `POLICY_REQUIRED`, `CONFLICTING`, `SUPPRESSED`, `STALE`, or `AGGREGATION_UNAVAILABLE`. Never turn an unresolved lane into a market claim.
