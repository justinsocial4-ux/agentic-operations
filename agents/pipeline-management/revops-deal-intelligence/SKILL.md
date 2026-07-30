---
name: revops-deal-intelligence
description: "Reviews a complete frozen set of active pipeline deals against approved current-state, stage-history, close-date, buyer-activity, amount, and evidence rules, then returns exact unranked review reasons without inventing probability, risk, forecast, cause, or coaching. Make sure to use this skill whenever the user asks to assess deal health, identify at-risk or stalled deals, inspect deal slippage, check deal probability, prioritize pipeline review, find overdue opportunities, or recommend deal interventions—even if they do not name the agent."
metadata:
  category: "Pipeline Management"
  phase: "1"
  data_readiness: "approved_deal_population_stage_history_activity_amount_privacy_and_workforce_policies_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved deal population, stage history, activity, amount, privacy, workforce, and review policies"
  mcps:
    - "Approved CRM or warehouse evidence in read-only mode"
  minimum_data:
    - "Stable deal, account, owner, stage, source, schema, policy, event, and receipt IDs"
---

# Deal Evidence Review

Review what frozen CRM evidence proves about active pipeline deals. Do not turn record state, elapsed time, or missing telemetry into close probability, deal risk, forecast impact, cause, or seller-performance judgment.

## Exact Response Rule

Build the input document, run `scripts/deal_evidence.py`, and return `render_review_output(review_deals(document))` byte for byte. Write no model-generated introduction, table, calculation, summary, correction, or text outside helper stdout. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting the population, purpose, roles, thresholds, or requested decision.
- Read `references/source_and_population.md` before using current records, history rows, activity rows, snapshots, or platform reports.
- Read `references/stage_and_close_date.md` before calculating stage age, transition facts, date state, or change counts.
- Read `references/activity_evidence.md` before using calls, emails, meetings, tasks, record edits, or associations.
- Read `references/amount_and_forecast.md` before using amount, currency, probability, weighted pipeline, forecast, revenue, or impact.
- Read `references/privacy_and_workforce.md` before reporting account, owner, manager, rep, contact, activity, or performance evidence.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_boundaries.md` before discussing CRM changes, interventions, coaching, alerts, messages, tasks, schedules, or downstream workflows.
- Use `scripts/deal_evidence.py` for validation, elapsed-time calculation, population reconciliation, independent evidence lanes, and exact output rendering.

## Operating Rules

1. Work read-only. Do not query or modify a CRM, probability, stage, category, amount, close date, next step, owner, task, message, alert, or schedule.
2. Require a versioned customer policy with owner, reviewer, effective date, UTC cutoff, timezone, source/schema/history semantics, complete deal population, stable stage IDs, active/terminal mappings, amount/currency basis, activity occurrence rule, exact numeric thresholds, privacy/workforce approvals, correction path, and prohibited uses.
3. Require a complete frozen population and reconcile declared deal count to supplied rows. Never silently omit newly created, zero-amount, overdue-date, missing-activity, or missing-history deals.
4. Use pseudonymous deal, account, and owner IDs only. Reject names, emails, phones, titles, message/call content, sentiment, free text, and manager/rep rankings.
5. Treat current stage and dated stage-entry history as different evidence. Never reconstruct stage entry from record creation, `LastModifiedDate`, current stage, or an average.
6. Preserve repeated stages and source-specific history behavior. Salesforce field history, stage history, and trend snapshots are not interchangeable; HubSpot current properties and `propertiesWithHistory` are not interchangeable.
7. Calculate current-stage elapsed days only from an approved dated stage-entry receipt. Otherwise return `STAGE_ENTRY_UNAVAILABLE` or `STAGE_HISTORY_CONFLICT`.
8. Compare elapsed days only to the exact customer-approved threshold for the current stage. Output `THRESHOLD_EXCEEDED`, `WITHIN_THRESHOLD`, or an unresolved state—never stalled, healthy, risky, urgent, or likely to slip.
9. Treat close date as a seller-entered CRM field. Report `DATE_BEFORE_CUTOFF`, `DATE_ON_OR_AFTER_CUTOFF`, `DATE_UNAVAILABLE`, or `DATE_CONFLICT`; never infer expected close or forecast impact.
10. Count only approved buyer-facing activity occurrence timestamps with verified deal association and source semantics. Record creation, task creation, sync time, field modification, email pixel load, and unverified association are not buyer activity.
11. Missing activity evidence is `ACTIVITY_EVIDENCE_UNAVAILABLE`, not inactivity. A known absence in a complete approved activity population may be `NO_QUALIFYING_ACTIVITY_RECORDED`; neither proves buyer disengagement.
12. Keep current state, stage history, close date, activity, amount, and policy lanes independent. One valid lane never repairs another unresolved lane.
13. Preserve amount only as the approved CRM amount basis and currency. Missing amount stays unavailable; zero stays zero. Do not calculate probability-weighted amount, forecast, revenue, revenue at risk, recoverable value, or ROI.
14. Return an unranked `review_deal_ids` set with exact helper reasons. Do not sort by owner, amount, invented severity, probability, or model preference.
15. Do not infer budget, timeline, competition, champion status, stakeholder consensus, seller effort, rep quality, coaching need, or root cause without separately approved direct evidence. This helper intentionally makes none of those conclusions.
16. R1: never characterize evidence adequacy with `small`, `large`, `enough`, `limited`, `insufficient`, `good`, `poor`, `high`, or `low` unless an approved numeric rule defines that exact label.
17. R2: return one helper-rendered response. Every numeric value must come from the helper and appear only in that response; never recompute, narrate, round differently, duplicate in prose, or self-correct.
18. Freeze policy, inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze scope.** Validate purpose, complete population, source semantics, stages, thresholds, roles, approvals, and prohibited uses.
2. **Register evidence.** Validate current snapshots, stage-entry history, buyer-activity events, cost/amount basis, cutoff, and receipts.
3. **Reconcile deals.** Check stable IDs, membership, source/schema versions, current stage, dates, currencies, and evidence populations.
4. **Calculate lanes.** Produce exact stage-age, close-date, activity, amount, and evidence states independently.
5. **Build review set.** Include unresolved lanes and policy-threshold crossings with exact reasons; do not rank.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: one complete frozen population where a deal's approved stage threshold is crossed, its close date is before cutoff, its activity population is complete with no qualifying activity, and its amount is present under the approved currency basis.

Output: the helper returns those exact lane states and puts the pseudonymous deal ID in the unranked review set. It prints no probability, confidence, risk tier, forecast amount, cause, coaching, or intervention.

## Failure Boundary

Missing or incompatible policy, population, source, stage-history, activity, date, amount, currency, privacy, or workforce evidence remains unresolved. Never replace an unavailable lane with a default, proxy, average, confidence score, or recommendation.
