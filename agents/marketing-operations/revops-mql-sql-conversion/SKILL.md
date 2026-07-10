---
name: revops-mql-sql-conversion
description: "Measures MQL-to-SQL conversion from historical stage events, keeps immature leads out of the failure denominator, analyzes rejection capture and cohort differences, and separates observed score-tier performance from unsupported model-drift claims. Make sure to use this skill whenever the user asks what their MQL-to-SQL rate is, why sales rejects MQLs, whether conversion changed, which source or score tier underperforms, how fast MQLs become SQLs, or whether marketing and sales qualification are misaligned—even if they do not name the agent."
metadata:
  category: "Marketing Operations"
  phase: "1"
  data_readiness: "30_days"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved MQL and SQL lifecycle definitions"
  mcps:
    - "Salesforce MCP or HubSpot MCP for read-only lifecycle evidence"
  minimum_data:
    - "Stable lead/contact ID and timestamped MQL entry"
    - "Timestamped SQL entry or approved terminal disposition"
    - "Analysis cutoff and customer-approved conversion window"
---

# MQL-to-SQL Conversion

Measure the handoff the customer's process actually records. Do not treat current status as historical truth, count leads that have not had time to convert as failures, or compare the result to a universal benchmark.

## Bundled Resources

- Read `references/data_contract.md` before querying a CRM or accepting an export.
- Read `references/cohort_rules.md` before building denominators, outcome windows, or comparisons.
- Read `references/rejection_analysis.md` before interpreting rejection reasons.
- Read `references/scoring_drift.md` before discussing score tiers or model drift.
- Read `references/output_template.md` before producing the final report.
- Read `references/research_and_claims.md` before repeating benchmarks, lift, labor, or vendor claims.
- Use `scripts/mql_sql_metrics.py` for exact rates, intervals, cohort comparisons, rejection capture, and velocity summaries.

## Operating Rules

1. Analyze read-only evidence. Do not change lifecycle stages, scoring rules, workflows, routing, or rejection fields.
2. Require customer-approved definitions for MQL entry, SQL entry, rejection, recycle, duplicate, and disqualification.
3. Use timestamped transitions or stage-entry properties. Current status alone cannot reconstruct a historical funnel.
4. Define one stable episode key and deduplicate repeated events before counting.
5. Give every MQL episode the same approved observation window. Keep immature episodes pending, not failed.
6. Keep converted, rejected, recycled, other terminal, and unresolved outcomes mutually exclusive for the chosen window.
7. Report counts beside every rate. Label the denominator in every table.
8. Show absolute percentage-point change separately from relative percent change.
9. Treat small cohorts and incomplete history as insufficient evidence, not poor performance.
10. Report rejection reasons with capture coverage and an explicit unknown bucket.
11. Call score-tier movement or conversion differences observed association. Claim model drift only when comparable historical cohorts and an approved test support it.
12. Use customer baselines or targets. Do not apply the legacy 80–90% benchmark as a universal standard.
13. Use the bundled helper for exact arithmetic. If it cannot run, label hand calculations approximate and never claim the helper produced them.
14. Report p-values and intervals without a decision verdict unless the threshold was approved before inspecting results. Without that rule, do not call evidence significant, weak, strong, distinguishable, noise, confirmed, or insufficient for a change claim.

## Preflight

### 1. Confirm the decision

Ask what decision the report must support: diagnose a rate change, review rejection quality, compare sources, inspect scoring, or establish a baseline.

### 2. Lock the lifecycle contract

Record:

- MQL-entry event and timestamp
- SQL-entry event and timestamp
- terminal dispositions and precedence
- conversion window, such as 30 days
- analysis cutoff in UTC
- repeated-entry rule: first episode, latest episode, or separately keyed episodes
- customer target or comparison cohort, if any

If this contract is missing, return `POLICY_REQUIRED` and a mapping checklist. Do not guess from labels.

### 3. Verify evidence

Accept Salesforce field history, HubSpot lifecycle-stage history/calculated stage dates, an event warehouse, or a validated export. Record the earliest covered history date, timezone, coverage, filters, and exclusions.

If only current statuses exist, return a current-state inventory and mark historical conversion `NOT_MEASURABLE`.

### 4. Declare enabled analyses

Enable only analyses supported by the supplied fields:

| Evidence | Enabled analysis |
|---|---|
| MQL and SQL timestamps | Mature-cohort conversion and velocity |
| Terminal disposition timestamp | Rejection/recycle/unresolved outcomes |
| Rejection reason | Reason distribution with capture coverage |
| Source/segment at MQL entry | Cohort comparison |
| Score captured at MQL entry | Score-tier observed performance |
| Comparable prior cohort | Change and uncertainty |

## Workflow

### 1. Build MQL episodes

Create one row per approved MQL episode. Freeze source, segment, owner, and lead score at MQL entry when history permits. Never use a later value as if it were known at entry.

Deduplicate source events by episode key. Quarantine impossible orderings, duplicate terminal outcomes, SQL-before-MQL timestamps, and ambiguous merged records.

### 2. Apply maturity and outcomes

Set:

```text
maturity_deadline = mql_entered_at + approved_conversion_window
mature = maturity_deadline <= analysis_cutoff
converted = sql_entered_at is within [mql_entered_at, maturity_deadline]
```

Classify each mature episode once. Keep non-mature episodes in `PENDING_NOT_MATURE`; exclude them from conversion and rejection denominators.

### 3. Calculate the funnel

Use the helper and report:

```text
conversion_rate = converted_within_window / mature_mql_episodes
rejection_rate = rejected_within_window / mature_mql_episodes
unresolved_rate = unresolved_at_deadline / mature_mql_episodes
```

Include Wilson intervals when the report supports a decision. If the mature denominator is zero, return `INSUFFICIENT_MATURE_COHORT`.

### 4. Analyze velocity

Calculate conversion time only for episodes that converted within the window. Report median and 75th percentile with the converted count. Do not use `LastModifiedDate` as either lifecycle or response time.

### 5. Analyze rejections

Preserve the customer's reason taxonomy. Report each reason as a share of all rejections and, separately, captured reasons. Show missing reasons as `UNKNOWN_REASON`; do not redistribute them.

### 6. Compare cohorts

Compare cohorts only when definitions, observation windows, history coverage, and filters match. Report counts, rates, Wilson intervals, absolute difference, relative difference when the baseline is nonzero, and a two-proportion p-value when appropriate. If no decision threshold was approved before analysis, report the p-value without converting it into a pass/fail label.

Do not call a difference causal unless assignment was randomized. Do not rank tiny cohorts as winners or losers.

### 7. Review scoring evidence

Group by the score captured at MQL entry. Report conversion and rejection by tier. A high-score tier with weaker conversion is a review signal, not proof that a specific scoring feature is broken.

Require the evidence in `references/scoring_drift.md` before using `DRIFT_SUPPORTED`. Otherwise report `ASSOCIATION_ONLY` or `INSUFFICIENT_EVIDENCE`.

### 8. Produce a preview

Use `references/output_template.md`. Recommend investigation or a controlled scoring review; do not deploy threshold changes or rewrite lifecycle automation.

## Worked Example

An approved 30-day window contains 100 MQL episodes at the cutoff. Seventy are mature: 42 converted, 18 rejected, and 10 remained unresolved. Thirty are still immature.

```text
Conversion = 42 / 70 = 60.00%
Rejection = 18 / 70 = 25.71%
Unresolved = 10 / 70 = 14.29%
Pending, excluded = 30
```

If the prior comparable cohort converted 36 of 70, the observed change is `+8.57 percentage points` and `+16.67%` relative. Report the interval and test result before recommending a response. Do not call the 30 pending episodes failures.

If 15 of 18 rejections have a reason, capture is `83.33%`. A reason appearing 9 times is 50.00% of all rejections and 60.00% of captured reasons. Show both denominators.

## Output Contract

Return six artifacts:

1. **Preflight receipt** — source, policy, window, cutoff, coverage, exclusions, enabled analyses.
2. **Maturity funnel** — total episodes, pending, mature, converted, rejected, recycled/other, unresolved.
3. **Conversion and velocity table** — counts, exact denominators, rates, intervals, median, p75.
4. **Rejection table** — reason counts, all-rejection share, captured-reason share, unknown bucket.
5. **Cohort and scoring review** — comparable differences, uncertainty, evidence label, confounders.
6. **Action preview and validation receipt** — human-owned next steps, arithmetic checks, and explicit no-write confirmation.

## Failure States

- `POLICY_REQUIRED` — lifecycle or observation-window definition is not approved.
- `HISTORY_UNAVAILABLE` — current state exists but timestamped transitions do not.
- `INSUFFICIENT_MATURE_COHORT` — no episodes have completed the observation window.
- `INCOMPARABLE_COHORTS` — definitions, coverage, filters, or windows differ.
- `REJECTION_ANALYSIS_DEGRADED` — rejection reason coverage is incomplete.
- `SCORING_REVIEW_UNAVAILABLE` — score-at-MQL evidence is missing.
- `DATA_CONFLICT` — timestamps or outcomes violate the approved contract.

Never silently replace an unavailable analysis with a guessed result.
