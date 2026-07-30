---
name: revops-event-selection
description: "Compares a declared set of candidate conferences, trade shows, webinars, or other events under one approved customer criteria policy and produces a read-only selection preview with exact evidence, score, capacity, and tie receipts. Use whenever someone asks to score events, select events, compare sponsorships, rank an event list, evaluate conference fit, or choose which events to review—even if they do not name the agent."
metadata:
  category: "Event Marketing"
  phase: "2"
  data_readiness: "approved_event_population_identity_criteria_cost_privacy_and_selection_policies_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved candidate population, organization identity, criteria, cost, privacy, capacity, and downstream-use policies"
  mcps:
    - "Approved event, CRM, and finance evidence in read-only mode"
  minimum_data:
    - "Stable event, organization, source, schema, policy, criterion, evidence, and receipt IDs"
---

# Event Criteria Selection Preview

Compare candidate events under one approved policy. Treat the result as policy arithmetic for human review, not proof of event quality, buyer intent, pipeline, revenue, ROI, conversion, causality, or future performance.

## Exact Response Rule

Build the input document, run `scripts/event_selection.py`, and return `render_selection_output(build_selection(document))` byte for byte. Write no model-generated introduction, table, calculation, summary, correction, or text outside helper stdout. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting the purpose, candidate set, roles, capacity, or requested decision.
- Read `references/source_and_population.md` before using event rosters, organizer claims, CRM records, finance records, or public sponsor lists.
- Read `references/identity_and_privacy.md` before matching or reporting attendee or organization evidence.
- Read `references/criteria_and_scoring.md` before applying eligibility rules, criterion weights, scores, ranks, or ties.
- Read `references/cost_and_event_evidence.md` before using dates, attendance, sponsorship tiers, costs, currencies, historical events, or competitor evidence.
- Read `references/uncertainty_and_claims.md` before describing confidence, fit, quality, intent, pipeline, ROI, cause, or forecast.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_boundaries.md` before discussing sponsorships, budgets, lists, campaigns, outreach, staffing, scheduling, or orchestration.
- Use `scripts/event_selection.py` for all validation, Decimal arithmetic, reconciliation, capacity handling, tie detection, and exact output rendering.

## Operating Rules

1. Work read-only. Do not query or change a CRM, approve a sponsorship, change a budget, create a list or campaign, contact an organizer or attendee, schedule work, or trigger another agent.
2. Require a named/versioned customer policy with owner, reviewer, effective date, cutoff, source/schema versions, candidate-population receipt, organization-identity rule, criteria and weights, cost/currency basis, capacity, tie handling, privacy/downstream approvals, correction path, and prohibited uses.
3. Require the declared candidate population to be complete and count-reconciled. A missing or extra event makes the final selection unavailable.
4. Use stable event IDs and pseudonymous organization IDs. Reject names, emails, phone numbers, titles, social URLs, free text, and attendee-level output.
5. Accept organization links only when an approved source-system identity rule produced a stable receipt. Do not improvise fuzzy, email-domain, name, phone, or model matching.
6. Require a complete evidence population for every event under the same cutoff and source/schema policy. Preserve incomplete, stale, future, duplicated, unregistered, unknown, and conflicting evidence.
7. Each criterion must have a stable ID, exact non-negative Decimal weight, required/optional status, customer definition, and approved evidence rule. Weights must total exactly 100.
8. Each event must provide one state and receipt for every criterion: `MATCHED`, `NOT_MATCHED`, `UNKNOWN`, or `CONFLICT`. Never turn missing evidence into zero or a match.
9. An event is rankable only when its identity, membership, cost, currency, evidence population, and every required criterion resolve under the approved policy.
10. The helper's weighted score is exact policy arithmetic only. Do not call it quality, propensity, fit truth, conversion likelihood, expected value, or a validated prediction.
11. Use supplied approved actual or quoted sponsorship cost only. Keep cost separate from score; never calculate pipeline, revenue, return, ROI, cost per lead, or cost per opportunity.
12. Rank rankable events by policy score only. If equal scores cross the capacity boundary, return the tied review set and no final selection. Never break a tie by name, ID, input order, cost, or model preference.
13. Competitor or sponsor presence is descriptive evidence only when an approved criterion defines it. It never proves buyer activity, threat, demand, or event value.
14. Historical event evidence is descriptive only unless a separately approved comparable-population attribution and finance contract exists. This helper does not forecast from history.
15. R1: never characterize evidence adequacy with `small`, `large`, `enough`, `limited`, `insufficient`, `good`, `poor`, `high`, or `low` unless an approved numeric rule defines that exact label.
16. R2: return one helper-rendered response. Every numeric value must come from the helper and appear only in that response; never recompute, narrate, round differently, duplicate, or self-correct.
17. Freeze the policy, inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze scope.** Validate the decision purpose, complete candidate set, owners, approvals, capacity, and prohibited uses.
2. **Register sources.** Validate source/schema versions, cutoff, extraction, cost, and population receipts.
3. **Reconcile identities and evidence.** Validate stable event and pseudonymous organization receipts without personal data.
4. **Apply criteria.** Preserve every criterion state and compute exact approved policy arithmetic only for resolved events.
5. **Apply capacity.** Expose exclusions, unresolved events, provisional events above the boundary, and boundary ties.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: a complete candidate set, approved criteria whose weights total exactly 100, complete per-event evidence, and equal policy scores crossing the final slot.

Output: the helper returns events above the boundary as provisional, the equal-score events as `BOUNDARY_TIE_REVIEW`, and no final selection. It prints no confidence, forecast, ROI, recommendation, or action.

## Failure Boundary

Missing or incompatible policy, population, identity, cost, currency, criterion, or source evidence remains `POLICY_REQUIRED`, `POPULATION_INCOMPLETE`, `IDENTITY_REVIEW`, `EVIDENCE_REVIEW`, or `BOUNDARY_TIE_REVIEW`. Never turn an unresolved state into an event recommendation.
