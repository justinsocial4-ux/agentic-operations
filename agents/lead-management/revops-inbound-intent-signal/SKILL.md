---
name: revops-inbound-intent-signal
description: "Reviews customer-supplied pseudonymous inbound-signal observations and their evidence lineage without inferring buying intent or identifying, ranking, or contacting anyone. Make sure to use this skill whenever the user asks to detect, monitor, score, rank, prioritize, or alert on buyer intent, website visits, product research, review-site activity, content engagement, inbound signals, account surges, or buying-committee behavior—even when the request assumes an IP address, domain, CRM match, vendor intent score, or page visit proves who is interested."
metadata:
  category: "Lead Management"
  phase: "2"
  data_readiness: "approved_policy_complete_pseudonymous_observation_and_source_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved purpose, source, collection, notice, objection, retention, privacy, marketing, and correction receipts"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable policy, source, schema, authorization, population, rule, observation, and pseudonymous organization IDs"
---

# Inbound Signal Evidence Review

Show only what customer-supplied pseudonymous observation evidence supports. Do not infer buying intent, resolve identity, rank targets, or turn an observation into outreach, routing, notification, CRM, campaign, forecast, customer, or worker action.

## Exact Response Rule

Build the input document, run `scripts/signal_evidence.py`, and return `render_review_output(review_signal_evidence(document))` byte for byte. The first response byte must be `{`; the final two response bytes must be the helper's explicit empty terminal line (`0a 0a`) after `}`. Do not use Markdown fences or add model prose. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, dates, rules, prohibited uses, or correction paths.
- Read `references/input_and_lineage.md` before accepting pseudonymous organizations, observations, sources, schemas, populations, or receipts.
- Read `references/classification_rules.md` before applying any customer-authored descriptive state.
- Read `references/privacy_and_marketing.md` before accepting behavioral, third-party, notice, objection, retention, or direct-marketing evidence.
- Read `references/current_platform_limits.md` before interpreting analytics, CRM, review-site, or intent-vendor exports.
- Read `references/output_contract.md` before rendering a result.
- Read `references/action_boundaries.md` before discussing identity, intent, prioritization, outreach, alerts, or system action.
- Read `references/verification_sources.md` for current official sources supporting the boundary.
- Use `scripts/signal_evidence.py` for strict validation, population reconciliation, rule application, state counts, and exact rendering.

## Operating Rules

1. Work offline and read-only. Do not query analytics, CRM, enrichment, review-site, advertising, email, Slack, or intent-vendor systems.
2. Require an effective customer policy with stable ID/version, owner, human reviewer, UTC cutoff and observation window, timezone, approved purpose, correction and objection paths, privacy and marketing review receipts, notice-program receipt, exact prohibitions, source bindings, and descriptive classification rules.
3. Accept only pre-supplied structured evidence using pseudonymous organization IDs beginning `anonymous-org-`. Reject names, emails, phones, addresses, domains, URLs, IP addresses, cookie/device IDs, CRM IDs, job titles, notes, free text, message content, protected traits, worker identity/activity, and contact-level behavior.
4. Require complete declared source populations. Missing, duplicate, extra, stale, future, unauthorized, purpose-incompatible, schema-conflicting, or lineage-conflicting evidence fails closed.
5. Bind every observation to one approved source/version, schema/version, authorization window, collection-authority receipt, purpose-compatibility receipt, notice receipt, objection-sync receipt, retention receipt, event type, observation time, and capture time.
6. A customer-authored rule may classify only whether an observed event falls inside or outside its exact approved recency window. Other evidence lanes remain exactly `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, or `UNAUTHORIZED`.
7. These states describe evidence handling only. They are not buying-intent, identity, fit, priority, urgency, likelihood, confidence, qualification, contactability, or outcome labels.
8. Never merge records, reverse-resolve IP/domain/device data, identify a person/company, infer a buying committee, score or rank an organization, select a contact, or draft a message.
9. Never recommend, send, schedule, notify, route, enrich, segment, suppress externally, write CRM, create a task, trigger a campaign, alter a forecast, monitor a worker, or tie compensation to output.
10. Never claim conversion, revenue, labor, speed, attribution, prediction, or causal improvement. Output is an evidence receipt, not proof of customer interest.
11. Return `HUMAN_REVIEW_REQUIRED`, `inference_authorized: false`, and `action_authorized: false` for every valid review.
12. R1: never add an adequacy adjective. The only recency labels are exact customer-rule states produced by the helper.
13. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
14. Freeze policy, normalized inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate policy, purpose, dates, descriptive rules, prohibitions, review receipts, and correction/objection paths.
2. **Reconcile sources.** Validate complete source bindings and populations with exact authorization, collection, notice, objection, retention, and schema receipts.
3. **Reconcile observations.** Match every declared observation exactly once; reject direct identifiers and extra fields.
4. **Apply rules once.** Let the helper preserve unresolved lanes and apply only the approved event-type recency rule to observed evidence.
5. **Count once.** Let the helper create the single state summary.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: one approved source population declares three pseudonymous organization observations. One has an authorized event receipt inside its customer-authored recency window, one is missing evidence, and one is suppressed under an objection or privacy control.

Run the helper. Its JSON response preserves the exact source and policy receipts, assigns only the rule-defined evidence states, counts each state once, and authorizes neither intent inference nor action.

## Failure Boundary

Missing or incompatible policy, authorization, collection, purpose, notice, objection, retention, source, schema, population, timestamp, event, rule, privacy, marketing, or correction evidence remains unresolved. Never replace it with a vendor score, assumed consent, IP/domain matching, CRM lookup, enrichment, default threshold, probability, confidence score, fuzzy match, prediction, causal inference, outreach advice, monitoring, alerting, or system action.
