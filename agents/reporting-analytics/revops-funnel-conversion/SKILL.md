---
name: revops-funnel-conversion
description: "Builds evidence-backed, customer-defined funnel conversion reports across ordered lifecycle or deal stages, keeps immature records out of failure denominators, separates completed dwell from current age, compares segments without inventing causality, and surfaces review candidates only against approved targets or baselines. Make sure to use this skill whenever the user asks where leads or deals drop off, what their full-funnel conversion is, which stage is a bottleneck, how conversion differs by source or segment, which records are aging in stage, or whether funnel performance changed—even if they do not name the agent."
metadata:
  category: "Reporting & Analytics"
  phase: "1"
  data_readiness: "30_days"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved funnel and transition-window policy"
  mcps:
    - "Salesforce MCP or HubSpot MCP for read-only lifecycle/deal-stage evidence"
  minimum_data:
    - "Stable record or episode ID"
    - "Timestamped ordered stage-entry events"
    - "Analysis cutoff and approved observation window per transition"
---

# Funnel Conversion Analysis

Measure the customer's actual funnel without turning current status, incomplete observation, or guessed stage mappings into false conversion outcomes.

## Bundled Resources

- Read `references/data_contract.md` before querying a CRM or accepting an export.
- Read `references/funnel_policy.md` before mapping stages, repeated entries, terminal outcomes, or observation windows.
- Read `references/metric_rules.md` before calculating conversion, dwell, trends, or segment comparisons.
- Read `references/bottleneck_evidence.md` before labeling a bottleneck, root cause, stuck record, or revenue impact.
- Read `references/output_template.md` before producing the report.
- Read `references/research_and_claims.md` before repeating platform, benchmark, labor, or outcome claims.
- Use `scripts/funnel_metrics.py` for exact transition rates, Wilson intervals, comparisons, ordered counts, dwell summaries, the complete report, and exact JSON rendering.

## Operating Rules

1. Analyze read-only evidence. Do not change stages, targets, routing, ownership, workflows, or CRM records.
2. Require a customer-approved, versioned funnel policy. Do not auto-map unfamiliar stage names from string similarity.
3. Use timestamped stage-entry events. Current status alone supports a snapshot, not historical conversion.
4. Anchor the population once and preserve one stable episode key through the funnel.
5. Apply the approved observation window separately to every transition. Keep records whose deadline is after the cutoff in `PENDING_NOT_MATURE`.
6. Count a transition only when the next stage follows the prior stage under the approved repeated-entry policy.
7. Keep skipped, recycled, regressed, merged, and conflicting paths visible; do not silently force them into a linear funnel.
8. Put counts and denominator definitions beside every rate. Report uncertainty for decision-bearing comparisons.
9. Separate completed-stage dwell from the current age of active records. Do not substitute record modification time.
10. Freeze source, segment, rep, and other dimensions at the policy-approved cohort point. Keep missing values in an explicit bucket.
11. Use customer targets or comparable historical baselines. Do not apply the legacy universal conversion, dwell, record-count, or severity thresholds.
12. Describe segmented differences as observed associations. Do not infer root cause from a rate difference.
13. Treat active pipeline amount as exposure, not delayed or lost revenue. Scenario value requires explicit assumptions.
14. Use the helper for every output value. If it cannot run, return `HELPER_REQUIRED`; do not hand-calculate.
15. Report p-values and intervals without decision labels unless the rule was approved before inspecting the evaluated cohort.
16. Once a cohort has been inspected, do not create a rule and apply it retroactively to that cohort. Treat it as exploratory and validate the rule on a new independent cohort.
17. Never compare interval overlap or statistical distinguishability across different transition rows. Each transition has a different population, window, and business question.
18. R1: never characterize evidence adequacy with `small`, `large`, `enough`, `limited`, or `insufficient` unless a decision-specific, preapproved numerical policy defines that label. Report helper states and counts.
19. R2: pass the complete `build_funnel_report` result to `render_funnel_json` and paste that JSON verbatim once. Put no numeric value in prose, tables, headings, or corrections outside that JSON.
20. Never recompute, paraphrase, summarize, or self-correct a numeric value. Fix the input or helper and rerun instead.

## Preflight

### 1. Confirm the decision

Record whether the user needs a baseline, a period comparison, a segment/source breakdown, an aging review, or an approved bottleneck check.

### 2. Lock the funnel policy

Record:

- pipeline and population
- ordered stages and terminal outcomes
- stage-entry evidence fields
- cohort anchor and analysis cutoff in UTC
- observation window for each transition
- skipped-stage, regression, re-entry, recycle, merge, and duplicate rules
- dimension-freeze point
- customer target/baseline and decision rule, if one already exists

If the policy is absent or ambiguous, return `POLICY_REQUIRED` with a mapping worksheet. Do not guess.

### 3. Verify history coverage

Accept Salesforce Opportunity Stage History, tracked lifecycle fields, HubSpot stage-entry properties/property history, a validated event warehouse, or a validated export. Record the earliest covered date, extraction time, timezone, completeness, and filters.

If only current stage exists, return `SNAPSHOT_ONLY`. You may report current counts and age when a valid entry timestamp exists, but not conversion or completed dwell.

### 4. Declare enabled analyses

| Evidence | Enabled analysis |
|---|---|
| Ordered stage-entry events | Transition and end-to-end reach |
| Approved transition windows | Mature-cohort conversion |
| Stage entry and exit | Completed dwell |
| Current stage entry and cutoff | Current age distribution |
| Frozen source/segment | Comparable breakdowns |
| Approved target/baseline | Bottleneck-candidate evaluation |

## Workflow

### 1. Build canonical episodes

Create one row per approved episode and an ordered event list. Quarantine negative durations, impossible orderings, duplicate events, unresolved merges, and conflicting terminal states.

Do not infer MQL, SQL, SAL, Opportunity, or Closed Won timestamps from later stages. Missing evidence stays missing.

### 2. Build each transition cohort

For transition `A → B`:

```text
deadline = entered_A_at + approved_window_A_to_B
mature = deadline <= analysis_cutoff
advanced = entered_B_at is after entered_A_at and on or before deadline
pending = entered_A but deadline is after cutoff
not_advanced = mature and no valid B entry by deadline
```

Run `transition_summary` from the helper. A record can be mature for an early transition and pending for a later one.

### 3. Calculate funnel reach and conversion

Report:

- ordered reach count at each stage
- mature, pending, advanced, and not-advanced counts for each transition
- transition rate and Wilson interval
- end-to-end reach for the anchored cohort, clearly separated from mature-window conversion; if the end-to-end window is undefined, return `POLICY_REQUIRED`, not an insufficient-data verdict

If no records are mature for a transition, return `INSUFFICIENT_MATURE_COHORT` for that row.

### 4. Calculate dwell and current age

For completed visits, calculate time from stage entry to the policy-approved exit. For current active visits, calculate age from the latest valid stage entry to the cutoff.

Report count, median, p75, and p90. Do not combine completed dwell and current age into one distribution. If stages may repeat, follow the policy for first visit, latest visit, or accumulated time.

### 5. Compare periods and segments

Compare only when stage policy, cohort anchor, windows, history coverage, filters, and dimension definitions match. Report counts, rates, intervals, absolute percentage-point difference, relative difference when defined, and a test result when appropriate.

Do not rank small cohorts by point estimate alone. Do not call observational differences causal.

### 6. Evaluate bottleneck candidates

Use `references/bottleneck_evidence.md`. Without an approved target/baseline and decision rule, report the lowest point estimate and aging distributions as observations only—not bottlenecks, failures, or stuck deals.

Where a rule exists, report the exact evidence that triggered it, missing evidence, and plausible alternative explanations. Keep root-cause statements as hypotheses until independently verified.

### 7. Produce the preview

Use `references/output_template.md`. Return the helper's human-review questions without adding a recommendation. Do not deploy stage, routing, scoring, staffing, or workflow changes.

## Worked Example

Input: an approved ordered funnel, frozen reach counts, and mature/advanced counts for each adjacent transition, with no approved target or decision rule.

Output: `build_funnel_report` identifies the minimum-rate transition as `OBSERVATION_ONLY`, returns `TARGET_NOT_APPROVED`, keeps pending records outside the denominator, and emits no action. Render that object once with `render_funnel_json`; do not restate any value.

## Output Contract

Return exactly one `render_funnel_json` code block containing the complete helper report. Add no prose before or after it. The helper report contains the preflight identifiers, reach, transitions, unavailable analyses, minimum-point observation, human-review questions, validation states, action boundary, and no-write receipt.

## Failure States

- `POLICY_REQUIRED` — stage order, windows, or path rules are not approved.
- `HISTORY_UNAVAILABLE` — timestamped stage events do not exist.
- `SNAPSHOT_ONLY` — current state is available but historical conversion is not.
- `INSUFFICIENT_MATURE_COHORT` — a transition has no mature episodes.
- `INCOMPARABLE_COHORTS` — definitions, windows, coverage, or filters differ.
- `DWELL_UNAVAILABLE` — valid entry/exit evidence is missing.
- `TARGET_NOT_APPROVED` — no bottleneck or stuck-record verdict is allowed.
- `DATA_CONFLICT` — path or timestamp evidence violates the approved policy.

Never silently replace an unavailable analysis with a proxy.
