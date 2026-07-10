---
name: revops-segment-performance
description: "Compares supplied closed-opportunity evidence across frozen customer segments and matched periods with exact count, win-rate, amount, duration, membership, and source receipts—without inventing confidence, drift, causes, rankings, forecasts, alerts, or GTM actions. Make sure to use this skill whenever the user asks to analyze segment performance, compare win rates or deal outcomes by segment, review quarterly segment changes, check segment trends, or validate a segment scorecard—even when they do not name the agent."
metadata:
  category: "ICP & Market Strategy"
  phase: "2"
  data_readiness: "approved_segment_membership_outcome_period_amount_duration_and_comparison_policies_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved source schema, outcome mapping, segment membership, periods, amount, duration, privacy, and comparison policies"
  mcps:
    - "Approved CRM or warehouse evidence in read-only mode"
  minimum_data:
    - "Stable opportunity, segment, period, evidence, policy, and revision IDs with exact outcome and membership receipts"
---

# Segment Outcome Evidence Review

Compare supplied segment outcomes. Do not discover, rank, diagnose, forecast, alert on, or select a segment.

## Exact Response Rule

Build the input document, run `scripts/segment_evidence.py`, and return `render_review_output(review)` byte for byte. Write no model-generated introduction, table, calculation, summary, correction, or text outside helper stdout. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting the purpose, definitions, roles, or requested decision.
- Read `references/source_and_outcome_evidence.md` before using CRM fields, stages, close dates, amounts, revisions, or source records.
- Read `references/segment_membership.md` before assigning, overlapping, combining, or comparing segments.
- Read `references/periods_and_comparisons.md` before making quarterly, weekly, prior-period, or year-over-year comparisons.
- Read `references/metric_lanes.md` before calculating counts, win rate, money, duration, velocity, ACV, ARR, or forecast accuracy.
- Read `references/uncertainty_and_labels.md` before describing confidence, adequacy, significance, stability, drift, performance, or cause.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_and_privacy_limits.md` before discussing rankings, alerts, account scores, lists, budgets, campaigns, pricing, staffing, coaching, quotas, or territories.
- Use `scripts/segment_evidence.py` for all validation, Decimal arithmetic, reconciliation, comparison, and exact output rendering.

## Operating Rules

1. Work read-only. Do not query a CRM, change a record, schedule a run, send an alert, create a list, change a score, or trigger an action.
2. Require a customer-owned policy with stable IDs/versions, cutoff, source-schema and outcome mapping, outcome occurrence rule, unique-opportunity/revision rule, segment version and membership mode, periods/timezone, amount and duration bases, comparison rule, roles, correction path, privacy/workforce policy, and prohibited uses.
3. Use only registered, fresh-by-policy evidence. Preserve future, stale, unregistered, duplicated, reopened/reclosed, unknown, conflicting, and out-of-window records as exceptions.
4. Treat CRM Close Date, stage, probability, amount, currency, record creation, and activity counts according to the supplied property definitions. Never invent platform semantics.
5. Count each stable opportunity once per approved outcome period. Use only approved `WON` and `LOST` mappings in the win-rate denominator.
6. Use supplied, frozen segment memberships. In `EXCLUSIVE` mode require exactly one segment per included opportunity. In `OVERLAPPING` mode calculate per-segment metrics but never sum, share, rank, or select across segments.
7. Keep population, money, and duration lanes independent. Missing money or duration evidence must not erase valid outcome counts.
8. Use non-negative Decimal-string amounts only with the approved currency and business basis. Never impute missing values or relabel Amount as ACV, ARR, bookings, or recognized revenue.
9. Use duration only when approved begin/stop occurrence timestamps exist and stop is not before begin. Never relabel CRM record age as a universal sales cycle or pipeline velocity.
10. Compare periods only when segment, membership, outcome, amount, duration, extraction, timezone, and period-length definitions match. Return exact arithmetic deltas without trend, significance, cause, or continuation claims.
11. Do not calculate forecast accuracy without a separately approved timestamped-forecast evaluation contract. Current probability or stage is not a historical forecast snapshot.
12. Do not rank segments or infer fit, health, strength, weakness, risk, opportunity, market shift, competitor effect, product issue, execution quality, or rep performance.
13. R1: never characterize data adequacy with `small`, `large`, `enough`, `limited`, or `insufficient` unless an approved numerical policy defines that exact label. Report helper states and counts.
14. R2: return one helper-rendered response. Every numeric value must come from the helper and appear only in that response; never recompute, narrate, round differently, or self-correct.
15. Freeze the policy, inputs, helper output, and receipt. New or corrected evidence creates a new review version.

## Workflow

1. **Freeze policy.** Validate source, outcome, identity, membership, period, metric, privacy, and comparison definitions.
2. **Register evidence.** Validate source/version/as-of/extraction/access receipts.
3. **Reconcile records.** Check stable IDs, revisions, outcomes, periods, memberships, money, and durations.
4. **Calculate lanes.** Produce exact per-segment/per-period population, amount, and duration receipts independently.
5. **Compare conditionally.** Calculate deltas only for the policy-named matched periods.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: two matched periods, frozen exclusive segment memberships, approved won/lost mappings, compatible money evidence, and one missing duration.

Output: the helper returns exact outcome and money receipts, preserves the duration lane as unresolved, and provides descriptive deltas. It prints no adequacy label, ranking, forecast, alert, cause, or action.

## Failure Boundary

Missing or incompatible evidence remains `SOURCE_REQUIRED`, `POLICY_REQUIRED`, `CONFLICTING`, `STALE`, or `COMPARISON_UNAVAILABLE`. Never turn an unresolved lane into a performance verdict.
