---
name: revops-certification-tracking
description: "Reviews customer-supplied pseudonymous certification-assignment evidence against exact approved completion and due-date rules without claiming compliance or readiness, identifying workers, or sending reminders. Make sure to use this skill whenever the user asks to track, monitor, audit, score, report, remind, alert, or escalate training, course, license, credential, recertification, or certification status—even when the request assumes missing enrollment, lateness, role changes, LMS data, manager hierarchy, or completion gaps should trigger worker or employment action."
metadata:
  category: "Enablement Operations"
  phase: "1"
  data_readiness: "approved_workforce_privacy_notice_and_complete_pseudonymous_assignment_evidence_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved workforce, privacy, notice, access, response, correction, appeal, recipient, retention, source, assignment, and time-rule receipts"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable policy, source, schema, authorization, population, assignment, anonymous worker/group, certification, rule, and evidence IDs"
---

# Certification Assignment Evidence Review

Describe only what customer-supplied pseudonymous assignment and completion evidence records at the approved cutoff. Do not infer enrollment, claim compliance or readiness, identify or judge a worker, or cause an action.

## Exact Response Rule

Build the input document, run `scripts/certification_evidence.py`, and return `render_review_output(review_certification_evidence(document))` byte for byte. The first response byte must be `{`; the final two response bytes must be the helper's explicit empty terminal line (`0a 0a`) after `}`. Do not use Markdown fences or add model prose. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, dates, rules, or prohibited uses.
- Read `references/input_and_lineage.md` before accepting pseudonymous assignments, source bindings, schemas, populations, or receipts.
- Read `references/state_rules.md` before applying completion and due-date states.
- Read `references/workforce_and_privacy.md` before accepting worker notice, access, response, correction, appeal, recipient, or retention evidence.
- Read `references/current_platform_limits.md` before interpreting LMS, CRM, HR, email, Slack, or calendar exports.
- Read `references/output_contract.md` before rendering a result.
- Read `references/action_boundaries.md` before discussing reminders, escalation, compliance, readiness, performance, or employment action.
- Read `references/verification_sources.md` for current official sources supporting the boundary.
- Use `scripts/certification_evidence.py` for strict validation, population reconciliation, state application, date arithmetic, counts, and exact rendering.

## Operating Rules

1. Work offline and read-only. Do not query LMS, CRM, HR, email, Slack, calendar, identity, performance, or compensation systems.
2. Require an effective customer policy with stable ID/version, owner, human reviewer, UTC cutoff and review time, IANA timezone, exact state rule, assignment and completion source bindings, allowed recipient roles, and separate workforce/privacy/notice/access/response/correction/appeal/recipient/retention receipts.
3. Accept only structured assignment evidence using worker IDs beginning `anonymous-worker-` and group IDs beginning `anonymous-group-`.
4. Reject names, emails, phones, addresses, CRM/LMS/HR IDs, job titles, manager hierarchy, notes, free text, messages, scores, attempts, performance, quota, compensation, territory, schedule, leave, health, protected traits, deal/customer data, and direct identifiers.
5. Require one complete declared assignment population observed exactly at the policy cutoff. Missing, duplicate, extra, stale, future, unauthorized, purpose-incompatible, schema-conflicting, or lineage-conflicting population evidence fails closed.
6. Bind every assignment to approved assignment and completion sources/versions, schemas/versions, authorization receipts/windows, one customer-authored rule, one certification ID, one due time or explicit no-due rule, allowed recipient roles, and the policy retention rule.
7. Never infer `not enrolled`, incomplete, due, or complete from an absent record. Preserve `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, or `UNAUTHORIZED` exactly.
8. For recorded evidence, the helper may return only `RECORDED_COMPLETE_BY_CUTOFF`, `RECORDED_INCOMPLETE_DUE_AT_OR_BEFORE_CUTOFF`, `RECORDED_INCOMPLETE_DUE_AFTER_CUTOFF`, or `NO_DUE_DATE_RULE` under the exact customer rule.
9. These states describe evidence and time only. They are not compliance, readiness, validity, qualification, performance, skill, effort, risk, urgency, priority, confidence, fairness, adequacy, or employment labels.
10. Never create, change, assign, waive, supersede, or recommend a certification, course, deadline, prerequisite, role requirement, or worker status.
11. Never remind, email, message, alert, schedule, route, escalate, notify a manager or executive, write CRM/LMS/HR data, create a task, monitor response, or affect pay, quota, territory, schedule, leave, discipline, promotion, termination, or performance management.
12. Never claim completion improvement, compliance, audit readiness, labor savings, revenue, ramp, retention, deliverability, prediction, or causal impact.
13. Return `HUMAN_REVIEW_REQUIRED`, `compliance_authorized: false`, `worker_judgment_authorized: false`, and `action_authorized: false` for every valid review.
14. R1: never add an adequacy adjective. Only exact helper states may characterize evidence.
15. R2: return one helper-rendered response. Every calculated number must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
16. Freeze policy, normalized input, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate policy, purpose, dates, prohibitions, approvals, rule, recipient roles, retention rule, and source bindings.
2. **Reconcile the population.** Match every declared assignment exactly once and reject direct identifiers or extra fields.
3. **Bind evidence.** Validate assignment and completion source/schema/authorization/timestamp receipts.
4. **Apply states once.** Let the helper preserve unresolved evidence or compare the recorded completion state and approved due time to the cutoff.
5. **Count once.** Let the helper create the single state summary.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: one complete population contains three pseudonymous certification assignments. One has recorded completion before the cutoff, one has recorded incomplete evidence with a due time after the cutoff, and one has missing completion evidence.

Run the helper. Its JSON response preserves the policy, population, source, assignment, completion, recipient, and retention receipts; returns only the exact recorded states; and authorizes no compliance judgment, worker judgment, reminder, escalation, write, or employment action.

## Failure Boundary

Missing or incompatible policy, authorization, workforce, privacy, notice, access, response, correction, appeal, recipient, retention, source, schema, population, assignment, timestamp, due rule, completion evidence, or lineage remains unresolved or fails validation. Never replace it with an LMS/CRM lookup, identity match, assumed enrollment, default deadline, role inference, compliance label, confidence score, reminder, alert, manager discretion, or system action.
