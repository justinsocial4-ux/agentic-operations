---
name: revops-event-activation
description: "Reviews complete pseudonymous customer-supplied event follow-up plans against exact collection, privacy, suppression, event, participation-state, route-contract, owner, channel, assignment, and timing evidence without identifying, enriching, scoring, ranking, tiering, contacting, writing, enrolling, alerting, scheduling, publishing, or driving downstream action. Make sure to use this skill whenever the user asks to activate, prioritize, rank, score, enrich, route, contact, or follow up with event attendees or badge scans; interpret rep interest or buying-stage notes; create hot-lead tiers; write event scores to CRM; enroll event contacts into workflows or nurture; or automate event outreach—even when the request assumes badge collection, firmographics, timing, rep judgment, enrichment confidence, or later conversion proves intent, fit, priority, consent, or likely outcome."
metadata:
  category: "Event Marketing"
  phase: "4"
  data_readiness: "complete_customer_supplied_pseudonymous_event_followup_plan_with_governance_source_event_route_and_suppression_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-12"
  dependencies:
    - "Customer-approved event collection, privacy, legal, suppression, recipient, retention, route-contract, assignment, and human-review evidence"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable pseudonymous policy, source, event, participant, plan, route, role, channel, population, and receipt IDs"
---

# Event Follow-Up Plan Evidence Review

Review a complete human-supplied pseudonymous event follow-up plan against frozen customer policy, event, participation-state, and route-contract evidence. Produce receipts for human reviewers, not attendee priorities or outreach actions.

## Exact Response Rule

Build the input document, run `scripts/event_plan_evidence.py`, and return `render_review_output(review_event_plan_evidence(document))` byte for byte. The first response byte must be `{`; the helper supplies one explicit empty terminal line after `}`. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read `references/scope_and_governance.md` before accepting purpose, approvals, lawful basis, collection/direct-marketing notice, objections, suppression, correction/access, recipients, retention, or human review.
- Read `references/source_event_and_population.md` before accepting source authorization, schema, query, page, pseudonymization, event, participation, or complete-population evidence.
- Read `references/route_and_assignment_contract.md` before accepting a human-supplied route, owner role, channel, planned time, or assignment receipt.
- Read `references/privacy_identity_and_profiling.md` before handling attendee identity, contact details, badge data, firmographics, notes, behavior, interest, buying stage, enrichment, protected data, or profiling.
- Read `references/output_and_action_boundary.md` before rendering or responding to scoring, ranking, tiering, contact, CRM, workflow, alert, schedule, publication, or downstream requests.
- Read `references/verification_sources.md` for current official sources supporting this boundary.
- Read `references/failure_states.md` before handling missing, conflicting, suppressed, unauthorized, partial, stale, future, or unmatched evidence.
- Read `references/construct_and_interpretation.md` before interpreting participation, rep observations, firmographics, timing, or later outcomes.
- Use `scripts/event_plan_evidence.py` for strict validation, population reconciliation, exact event/route checks, unresolved-state propagation, and rendering.

## Operating Rules

1. Work offline and read-only. Never accept credentials, access CRM/event/enrichment systems, reveal identity, enrich, search, scrape, match people, score, rank, tier, route, retry, contact, message, write, enroll, alert, schedule, publish, or trigger workflows.
2. Require one effective customer policy with exact purpose, cutoff, timezone, owners, operations/security/privacy/legal approvals, lawful basis, collection notice, direct-marketing notice, objection, suppression, correction/access, recipient, retention, follow-up-policy receipts, and prohibited uses.
3. Accept only pseudonymous participant, event, source, plan, route, role, channel, policy, and receipt IDs. Reject names, emails, phones, domains, URLs, addresses, companies, titles, free text, rep notes, behavior, interest, buying stage, firmographics, protected data, candidate contact details, enrichment responses, scores, tiers, conversions, and raw errors.
4. Reconcile the complete declared participant population, every complete source population, and exactly one plan row per participant. Missing, duplicate, extra, future, partial, or unauthorized evidence fails closed.
5. Require each event to bind to one approved source, exact observation window, event receipt, participation-definition receipt, and capture-policy receipt. Never infer attendance, identity, engagement, interest, or permission from record creation or absence.
6. Accept only the customer-supplied participation state and route assignment. Eligible rows require one supplied route version, owner role, channel, planned time, and unique human-assignment receipt. The helper never selects, ranks, reorders, or recommends a route or person.
7. Require the supplied route contract to bind the exact event, owner role, channel, authorization window, planned-time window, and policy receipts. A matched receipt proves only evidence alignment, not consent, compliance, desirability, urgency, priority, or permission to execute.
8. A suppressed request returns `SUPPRESSED` and cannot carry any route assignment. Honor unauthorized, conflicting, and missing evidence before route checking.
9. Return only `CUSTOMER_EVENT_PLAN_EVIDENCE_MATCHED`, `CUSTOMER_EVENT_PLAN_EVIDENCE_NOT_MATCHED`, `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, or `UNAUTHORIZED` per participant and review.
10. Never label attendee intent, fit, interest, buying stage, engagement, priority, quality, confidence, readiness, risk, contactability, conversion likelihood, value, or outcome. Never use firmographics, title, timing, rep judgment, enrichment, agreement, recency, or later conversion as truth.
11. Human privacy, legal, security, operations, marketing, and CRM owners decide whether collection and any later contact are lawful, necessary, wanted, accurate, and authorized.
12. Return fixed false action flags. The helper never authorizes contact, outreach, CRM writes, workflow enrollment, enrichment, scoring, ranking, alerts, schedules, publication, or downstream decisions.
13. R1: never characterize adequacy, performance, risk, confidence, quality, accuracy, freshness, fit, readiness, interest, intent, or priority with an adjective. The helper emits only exact evidence states.
14. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
15. Freeze policy, sources, event, population, route contracts, plan, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. Freeze governance, source bindings, event contract, participant population, route contracts, plan rows, cutoff, and recipient.
2. Reconcile every source population and every declared participant.
3. Propagate suppression and unresolved evidence before checking the supplied route assignment.
4. Check exact event, owner, channel, authorization, and planned-time bindings without selecting or executing anything.
5. Render the helper result exactly; humans own every contact, CRM, workflow, communication, and downstream decision.

## Worked Example

Input: two pseudonymous participants have complete policy, event, source, and route evidence. A human supplies one route assignment within its exact window and leaves the suppressed participant unassigned. The helper returns one `CUSTOMER_EVENT_PLAN_EVIDENCE_MATCHED` receipt and one `SUPPRESSED` receipt with all action flags false. It does not identify anyone, score or rank attendees, choose a route, contact a person, update CRM, enroll a workflow, or authorize outreach.

## Failure Boundary

Missing or incompatible governance, lawful-basis, notice, objection, suppression, correction/access, recipient, retention, source, schema, authorization, query, page, pseudonymization, event, participation, population, route, owner, channel, assignment, timestamp, or human-review evidence remains unresolved or unmatched. Never replace it with record absence, vendor data, fuzzy identity, firmographics, rep judgment, interest, buying stage, weights, scores, tiers, confidence, recency, prediction, recommendation, write-back, workflow enrollment, alerts, scheduling, publication, or downstream action.
