---
name: revops-sla-monitoring
description: "Builds a read-only SLA evidence review from customer-approved clocks, qualifying-event rules, frozen populations, occurrence timestamps, calendar receipts, and denominator policy without inventing thresholds, judging employees, or sending escalations. Make sure to use this skill whenever the user asks to check SLA compliance, response time, first touch, qualification time, stage dwell, handoff timing, overdue records, breach evidence, SLA reporting, or escalation readiness—even when they do not name the agent."
metadata:
  category: "Lead Management"
  phase: "2"
  data_readiness: "approved_policy_population_event_calendar_denominator_privacy_and_decision_rules_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved SLA, event, calendar, population, exclusion, denominator, privacy, workforce, correction, and decision policies"
  mcps:
    - "Approved CRM and activity sources in read-only mode"
  minimum_data:
    - "Stable record/event IDs, frozen cutoff, exact occurrence timestamps, source provenance, and named human approval roles"
---

# SLA Evidence Review

Evaluate supplied records against an approved SLA policy without writing, alerting, escalating, ranking, or judging people.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting an SLA definition or purpose.
- Read `references/time_and_event_evidence.md` before selecting the clock-opening or qualifying stop event.
- Read `references/calendars_and_due_times.md` before calculating or accepting a due time.
- Read `references/population_and_denominators.md` before reporting counts or a rate.
- Read `references/workforce_privacy_and_correction.md` before using owner-linked evidence.
- Read `references/platform_evidence.md` before mapping Salesforce or HubSpot activity fields.
- Read `references/decision_and_action_boundary.md` before discussing alerts, escalation, coaching, ownership, or workflow changes.
- Read `references/output_contract.md` before rendering any result.
- Read `references/research_limits.md` before repeating benchmark, outcome, pricing, or accuracy claims.
- Use `scripts/sla_evidence.py` for all validation, time math, event selection, classification, aggregation, and exact output rendering.

## Operating Rules

1. Work read-only. Do not create fields, update records, reassign owners, create tasks, send messages, schedule jobs, trigger workflows, alert managers, or escalate records.
2. Require a customer-owned policy with stable ID/version, approved purpose, exact clock-opening event, qualifying stop-event types, clock type, target, timezone, exclusions, denominator, owner, reviewer, approver, correction path, and prohibited uses.
3. Never supply universal response, qualification, dwell, handoff, warning, grace, completeness, coaching, or escalation thresholds.
4. Freeze the full in-scope record population and cutoff. Keep excluded, missing, unknown, duplicate, conflicting, pending, and unassociated records visible.
5. Use event occurrence time only when the source and policy define its meaning. Record-creation time is provenance, not proof that a human touch occurred.
6. Accept only policy-listed event types with verified record association and source provenance. Do not infer contact, intent, response, or qualification from an object existing.
7. For continuous clocks, calculate in UTC with exact integer seconds. For business/service calendars, require a supplied due-time receipt from the approved calendar calculator; never approximate weekends, holidays, shifts, or daylight-saving transitions.
8. Classify `MET`, `BREACHED`, or `PENDING` only after policy, population, time, and event evidence validate. Use `POLICY_REQUIRED`, `SOURCE_REQUIRED`, or `CONFLICTING` otherwise.
9. Count only policy-included records with resolved due and outcome states in the rate denominator. Report every excluded lane separately; never silently shrink the population.
10. Do not call pending work compliant, count a late event as on time, or treat missing events as zero response time.
11. Use pseudonymous owner IDs only. Exclude names, emails, message content, call content, home locations, protected traits, manager narratives, quota, discipline, and historical performance by default.
12. Do not label, rank, compare, coach, reward, penalize, or recommend action for a rep, team, source, region, or manager.
13. Do not claim SLA status caused conversion, revenue, velocity, productivity, forecast, morale, retention, or quota outcomes.
14. R1: never characterize evidence adequacy with `small`, `large`, `enough`, `limited`, or `insufficient` unless an approved bundled rule defines that label numerically. Report the helper states and counts.
15. R2: pass the complete helper report to `render_report_json` and paste that JSON verbatim once. Put no number, timestamp, count, rate, duration, threshold, or identifier in prose outside the JSON; never recompute, paraphrase, or correct a number inline.
16. Freeze the prompt, inputs, helper output, and receipt. New evidence creates a new review version.

## Workflow

1. **Freeze scope and policy.** Validate purpose, clock, events, population, cutoff, roles, and prohibited uses.
2. **Validate evidence.** Reconcile records, event associations, occurrence times, source versions, exclusions, and due-time receipts.
3. **Evaluate records.** Run the helper; do not hand-calculate or override a state.
4. **Aggregate once.** Use the helper denominator and lane counts without adding derived prose.
5. **Render exactly.** Paste the single `render_report_json` result as the complete numeric artifact.
6. **Close safely.** Add only the nonnumeric boundary `NO ALERT / NO ESCALATION / NO CRM OR WORKFORCE ACTION`.

## Output Contract

Return:

1. one exact helper-rendered JSON code block containing policy, evidence, population, record results, denominator, states, conflicts, approval, and boundary; then
2. the exact nonnumeric boundary `NO ALERT / NO ESCALATION / NO CRM OR WORKFORCE ACTION`.

Do not add a summary, table, bullet, headline containing numbers, adequacy adjective, recommendation, or corrected value outside the JSON.

## Worked Example

Input: an approved continuous-clock policy, a frozen record population, registered source evidence, and a qualifying human-call event whose occurrence time falls before the helper-calculated due time.

Output: run the helper, preserve the record's `MET` state and exact receipt fields in the single rendered JSON block, then print only the boundary line. Do not restate the duration or status in prose.

## Failure Boundary

Unresolved policy, source, association, calendar, identity, population, or approval evidence stays unresolved. Never convert a gap into compliance, confidence, employee judgment, or action.
