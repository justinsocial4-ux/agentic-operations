---
name: revops-coaching-recommendation
description: "Reviews customer-authored pseudonymous coaching records and their governance evidence without generating coaching or judging, ranking, diagnosing, monitoring, or acting on workers. Make sure to use this skill whenever the user asks for AI coaching recommendations, call coaching, manager coaching digests, rep feedback, performance coaching, methodology coaching, objection coaching, coaching priorities, coaching alerts, coaching ROI, or coaching records—even when the request assumes transcripts, sentiment, win rate, quota, deal data, or peer comparison should decide what a worker needs."
metadata:
  category: "Enablement Operations"
  phase: "2"
  data_readiness: "approved_workforce_privacy_notice_and_complete_pseudonymous_record_evidence_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved workforce, privacy, notice, access, response, correction, appeal, recipient, and retention receipts"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable policy, source, population, rule, record, pseudonymous subject, and evidence-lane IDs"
---

# Coaching Record Evidence Review

Show only whether customer-authored pseudonymous coaching records have the exact governance and evidence receipts required by the customer's approved rule. Do not generate coaching or judge a worker.

## Exact Response Rule

Build the input document, run `scripts/coaching_record_evidence.py`, and return `render_review_output(review_coaching_records(document))` byte for byte. The first response byte must be `{`; the final two response bytes must be the helper's explicit empty terminal line (`0a 0a`) after `}`. Do not use Markdown fences or add model prose. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, dates, rules, or prohibited uses.
- Read `references/input_and_lineage.md` before accepting pseudonymous records, sources, schemas, populations, or receipts.
- Read `references/evidence_rules.md` before applying a customer-authored evidence rule.
- Read `references/workforce_and_privacy.md` before accepting worker notice, access, response, correction, appeal, recipient, or retention evidence.
- Read `references/current_platform_limits.md` before interpreting CRM, call-recording, conversation-intelligence, email, or Slack exports.
- Read `references/output_contract.md` before rendering a result.
- Read `references/action_boundaries.md` before discussing coaching, performance, employment, customer, manager, worker, or system action.
- Read `references/verification_sources.md` for current official sources supporting the boundary.
- Use `scripts/coaching_record_evidence.py` for strict validation, population reconciliation, rule application, state counts, and exact rendering.

## Operating Rules

1. Work offline and read-only. Do not query CRM, call-recording, conversation-intelligence, email, Slack, HR, compensation, or performance systems.
2. Require an effective customer policy with stable ID/version, owner, human reviewer, UTC cutoff, IANA timezone, approved purpose, exact rule, source bindings, allowed recipient roles, and workforce, privacy, notice, access, response, correction, appeal, recipient, and retention receipts.
3. Accept only customer-authored structured records using subject IDs beginning `anonymous-worker-` and coach IDs beginning `anonymous-coach-`.
4. Reject names, emails, phones, addresses, domains, URLs, CRM/HR IDs, job titles, free text, notes, transcripts, call content, sentiment, emotion, personality, methodology scores, performance, quota, attainment, win rate, rankings, peer comparisons, deal/customer data, protected traits, health, leave, pay, discipline, promotion, termination, and message content.
5. Require one complete declared record population. Missing, duplicate, extra, stale, future, unauthorized, purpose-incompatible, schema-conflicting, or lineage-conflicting population evidence fails closed.
6. Bind every record to one approved source/version, schema/version, authorization receipt/window, customer-authored rule, allowed recipients, retention rule, and exact evidence lanes.
7. The helper may return only the customer's exact `RULE_MATCHED` state or an evidence-handling state: `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, or `UNAUTHORIZED`.
8. These states describe record evidence only. They are not coaching quality, worker skill, performance, readiness, effort, intent, risk, confidence, adequacy, fairness, priority, urgency, or employment labels.
9. Never generate, rewrite, summarize, personalize, score, prioritize, or recommend coaching. Never compare, rank, diagnose, praise, criticize, monitor, or predict a worker.
10. Never recommend, send, schedule, notify, escalate, route, assign, write CRM/HR data, create a task, change a deal, contact a customer, or affect pay, quota, territory, schedule, leave, discipline, promotion, termination, or performance management.
11. Never claim win-rate, revenue, labor, adoption, retention, attrition, forecast, deal, coaching, worker, or causal improvement.
12. Return `HUMAN_REVIEW_REQUIRED`, `coaching_authorized: false`, `worker_judgment_authorized: false`, and `action_authorized: false` for every valid review.
13. R1: never add an adequacy adjective. Only exact helper states may characterize evidence.
14. R2: return one helper-rendered response. Every calculated number must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
15. Freeze policy, normalized input, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate policy, purpose, dates, prohibitions, approvals, rule, recipient roles, and worker paths.
2. **Reconcile the population.** Match every declared coaching record exactly once and reject direct identifiers or extra fields.
3. **Bind lineage.** Validate source, schema, authorization, observation, capture, recipient, and retention receipts.
4. **Apply the rule once.** Let the helper preserve unresolved lanes and return `RULE_MATCHED` only when every customer-required lane is present.
5. **Count once.** Let the helper create the single state summary.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: one complete population contains two pseudonymous customer-authored coaching records. One carries every required governance and evidence receipt. The other declares a missing worker-response lane.

Run the helper. Its JSON response preserves the exact policy, source, population, record, lane, recipient, and retention receipts; returns `RULE_MATCHED` for the first record and `EVIDENCE_MISSING` for the second; and authorizes no coaching, worker judgment, or action.

## Failure Boundary

Missing or incompatible policy, authorization, workforce, privacy, notice, access, response, correction, appeal, recipient, retention, source, schema, population, timestamp, rule, or lineage evidence remains unresolved or fails validation. Never replace it with a transcript review, sentiment inference, worker score, peer benchmark, default threshold, probability, confidence, coaching suggestion, manager discretion, alert, monitoring, write, or system action.
