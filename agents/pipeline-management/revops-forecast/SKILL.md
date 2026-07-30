---
name: revops-forecast
description: "Produces evidence-backed revenue forecast snapshots that keep CRM category rollups, seller submissions, probability-weighted expectations, scenarios, closed-won actuals, and backtest accuracy separate. Make sure to use this skill whenever the user asks for a weekly, monthly, or quarterly forecast; commit versus best case; forecast changes; weighted pipeline; forecast accuracy; rep submission bias; or a board-ready forecast—even if they do not name the agent."
metadata:
  category: "Pipeline Management"
  phase: "1"
  data_readiness: "30_days"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved forecast policy and currency policy"
  mcps:
    - "Salesforce MCP or HubSpot MCP for read-only forecast evidence"
  minimum_data:
    - "Frozen as-of opportunity/deal snapshot"
    - "Forecast period, pipeline, amount basis, category, close date, currency"
    - "Approved inclusion, probability, and conversion policy for calculated forecasts"
---

# Revenue Forecast

Show what the CRM and approved model say as of a specific cutoff. Do not turn seller categories, stage probabilities, arbitrary scenario weights, or current-state reconstructions into false forecast certainty.

## Bundled Resources

- Read `references/data_contract.md` before querying a CRM or accepting a snapshot.
- Read `references/forecast_policy.md` before including deals, mapping categories, selecting amounts, or converting currency.
- Read `references/forecast_types.md` before naming commit, best case, weighted expectation, scenario, or submitted forecast.
- Read `references/backtesting.md` before discussing accuracy, bias, calibration, confidence, or rep performance.
- Read `references/output_template.md` before producing the report.
- Read `references/research_and_claims.md` before repeating platform, benchmark, lift, labor, or accuracy claims.
- Use `scripts/forecast_metrics.py` for exact currency-safe rollups, weighted expectations, deltas, scenario checks, coverage, and backtest metrics.

## Operating Rules

1. Analyze read-only evidence. Do not change deal categories, stages, probabilities, amounts, dates, ownership, submissions, or CRM records.
2. Require a customer-approved forecast policy, forecast period, as-of cutoff, pipeline scope, and amount basis.
3. Use a frozen as-of snapshot. Never reconstruct an earlier forecast from current deal values.
4. Keep closed-won actuals, active pipeline, forecast categories, seller/manager submissions, weighted expectation, and scenarios as separate measures.
5. Preserve platform category IDs and customer definitions. Do not assume `Commit`, `Best case`, or `Pipeline` means the same thing across orgs.
6. Do not call a probability-weighted sum “commit” or “most likely” unless the approved policy defines it that way.
7. Require probabilities calibrated for the same target, period, cohort, and as-of timing. Missing probabilities stay unknown unless an approved fallback exists.
8. Require one reporting currency and an approved dated exchange-rate policy. Do not sum mixed currencies directly.
9. Include zero outcomes and lost deals in historical evaluation. Do not remove forecast misses as “outliers” merely because they are large.
10. Evaluate rep or team bias from frozen submitted forecasts versus period actuals—not from deal amount changes.
11. Report evidence coverage and backtest metrics. Do not manufacture a 0–100 confidence score or strategic-use label.
12. Scenarios require explicit, approved assumptions and must satisfy downside ≤ base ≤ upside. Forecast categories are not automatically scenarios.
13. Separate observed week-over-week movement from drivers. Deal additions, removals, stage changes, date shifts, amount changes, FX, and policy changes require event evidence.
14. Treat amount in active deals as pipeline exposure, not guaranteed revenue.
15. Use the helper for exact arithmetic. If it cannot run, label hand calculations approximate and never claim machine verification.
16. Do not label samples sufficient, reliable, stable, or accurate without a preapproved decision requirement and valid backtest.
17. Once results are inspected, new accuracy or decision rules apply only to future independent periods.
18. Treat Closed Won as the approved CRM amount basis. Do not call it realized, booked, recognized, earned, billed, collected, cash, or guaranteed unless a finance-controlled policy and source explicitly establish that meaning.

## Preflight

### 1. Confirm the decision

Record whether the user needs a category rollup, seller submission comparison, weighted expectation, approved scenarios, gap to goal, period delta, or backtest.

### 2. Lock the forecast policy

Record:

- policy ID/version and owner
- as-of cutoff and forecast period
- pipeline, team, territory, product, or segment scope
- inclusion/exclusion rules
- amount field and treatment of null/zero/negative values
- category IDs and definitions
- submitted forecast source and timestamp
- reporting currency and dated FX policy
- probability source, calibration target, and model version
- scenario rules, goal, and decision thresholds if approved

If any required element is absent, return `POLICY_REQUIRED` for the affected measure instead of guessing.

### 3. Verify evidence

Accept a frozen CRM export, warehouse snapshot, Salesforce forecast snapshot, HubSpot forecast export, or another validated as-of source. Record extraction time, freshness, row counts, missingness, duplicates, and exclusions.

Historical accuracy requires archived forecast snapshots and actual closed-won results for the exact forecast periods. Current pipeline cannot substitute.

### 4. Declare enabled analyses

| Evidence | Enabled analysis |
|---|---|
| Category + amount + period | Category rollup |
| Submitted forecast snapshot | Submission comparison |
| Approved calibrated probability | Weighted expectation |
| Approved scenario rules | Downside/base/upside |
| Prior comparable snapshot | Period-over-period delta |
| Archived forecasts + actuals | Backtest, bias, calibration |

## Workflow

### 1. Build the as-of snapshot

Create one row per approved forecast unit. Preserve deal ID, owner/territory, pipeline, category, amount, currency, close date, stage, probability source/version, and snapshot timestamp.

Quarantine duplicates, cross-pipeline category collisions, mixed currencies without FX, invalid dates, negative amounts without policy, and contradictory closed states.

### 2. Produce category rollups

Use exclusive category values from the customer policy. Report counts and amounts for `Not forecasted`, `Pipeline`, `Best case`, `Commit`, `Closed won`, or the customer's own categories.

Category rollups are descriptive CRM state. Do not add categories together as nested probabilities unless the policy explicitly defines cumulative rollups.

### 3. Preserve submitted forecasts

Show seller and manager submitted values with submitter, period, currency, and submission timestamp. Do not overwrite submissions with a calculated model.

### 4. Calculate weighted expectation

Only when every included unit has an approved probability:

```text
weighted_expectation = sum(amount × calibrated_probability)
```

Report amount coverage, probability coverage, probability source/version, and missing rows. This is an expectation under the approved model—not commit, closed won, or a guarantee.

### 5. Calculate scenarios

Use only approved scenario inclusion sets or transformations. Show every assumption and reconcile downside, base, and upside. Do not use the legacy 50% early-stage uplift, 30% re-engagement, or 40% risk discount as defaults.

### 6. Calculate deltas

Compare identical policies, periods-at-equivalent-cutoff, currencies, and scopes. Report absolute and relative changes separately. When event history exists, reconcile category, amount, close-date, deal, FX, and policy changes; otherwise label drivers unknown.

### 7. Backtest and review bias

Use `references/backtesting.md`. Compare each archived forecast to the closed-won actual under the same approved amount basis for that exact period and scope. Report count, MAE, WAPE, and signed aggregate bias. Keep zero actual periods visible; percentage metrics are undefined when their denominator is zero.

Rep-level review requires repeated submitted forecasts by rep and period. Report evidence, not coaching verdicts.

### 8. Produce the preview

Use `references/output_template.md`. Recommend human review of data/policy gaps or a prospective validation plan. Do not modify the live forecast.

## Worked Example

One USD snapshot contains exclusive category amounts:

| Category | Amount |
|---|---:|
| Not forecasted | 40,000 |
| Pipeline | 180,000 |
| Best case | 80,000 |
| Commit | 150,000 |
| Closed won | 30,000 |

Total snapshot amount is 480,000. A seller submission of 170,000 remains a separate measure. With approved deal-level probabilities, the weighted expectation may be 239,000; it is not renamed commit. Without approved scenario rules or archived forecast snapshots, scenario and accuracy outputs remain unavailable.

## Output Contract

Return six artifacts:

1. **Preflight receipt** — source, policy, cutoff, period, scope, amount basis, currency, category, probability, and enabled analyses.
2. **Category and closed-won table** — exclusive counts/amounts and closed-won amount under the named basis.
3. **Submission and calculated forecast table** — submitted values, weighted expectation, coverage, and provenance.
4. **Scenario/goal/delta table** — only approved measures with reconciliation and unknown drivers.
5. **Backtest and bias table** — period count, MAE, WAPE, bias, zero-denominator states, limitations.
6. **Action preview and validation receipt** — human-owned next steps, arithmetic checks, and no-write confirmation.

## Failure States

- `POLICY_REQUIRED` — period, scope, amount, category, probability, FX, or scenario policy is absent.
- `SNAPSHOT_REQUIRED` — no frozen as-of forecast snapshot exists.
- `MIXED_CURRENCY` — amounts cannot be summed safely.
- `WEIGHTED_FORECAST_UNAVAILABLE` — probability coverage or calibration is incomplete.
- `SCENARIO_RULES_REQUIRED` — downside/base/upside assumptions are not approved.
- `BACKTEST_UNAVAILABLE` — archived snapshots or matching actuals do not exist.
- `INCOMPARABLE_SNAPSHOTS` — cutoff, period, scope, policy, or currency differs.
- `DATA_CONFLICT` — duplicate, date, state, or amount evidence is contradictory.

Never silently replace an unavailable forecast type with another.
