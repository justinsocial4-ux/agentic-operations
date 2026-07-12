---
name: revops-mql-qualification
description: "Reviews complete pseudonymous evidence against customer-authored marketing-qualification conditions without inventing a lead score, inferring intent or sales readiness, labeling a record MQL, ranking people, or taking routing, nurture, archive, outreach, CRM, or downstream action. Make sure to use this skill whenever the user asks to qualify leads, score MQL candidates, identify sales-ready contacts, prioritize high-intent leads, set MQL thresholds, use email or web behavior for qualification, route qualified leads, archive low-score leads, or tune a lead-scoring model—even when the request assumes opens, clicks, job titles, firmographics, recency, account health, or opportunity value prove intent or conversion likelihood."
metadata:
  category: "Lead Management"
  phase: "2"
  data_readiness: "complete_customer_supplied_pseudonymous_condition_evidence_with_governance_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved marketing-qualification purpose, condition, privacy, legal, notice, objection, correction, recipient, retention, and human-review policies"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable pseudonymous policy, source, condition, record, population, observation, and receipt IDs"
---

# Marketing Qualification Rule Evidence Review

Review whether complete pseudonymous evidence satisfies exact customer-authored conditions. Produce evidence receipts for a human reviewer, not a universal lead score or sales-readiness decision.

## Exact Response Rule

Build the input document, run `scripts/qualification_evidence.py`, and return `render_review_output(review_qualification_evidence(document))` byte for byte. The first response byte must be `{`; the helper supplies one explicit empty terminal line after `}`. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read `references/scope_and_governance.md` before accepting purpose, approvals, human review, notice, objection, correction, recipients, or retention.
- Read `references/source_and_population.md` before accepting source authorization, schema, query, page, pseudonymization, or population evidence.
- Read `references/condition_contract.md` before accepting required or disqualifying customer-authored conditions.
- Read `references/privacy_and_profiling.md` before handling identity, behavior, firmographics, protected data, or direct-marketing profiling.
- Read `references/construct_and_interpretation.md` before using intent, fit, readiness, probability, confidence, quality, or conversion language.
- Read `references/output_and_action_boundary.md` before rendering or responding to label, ranking, route, nurture, archive, outreach, write, alert, or publication requests.
- Read `references/verification_sources.md` for current official sources supporting this boundary.
- Read `references/failure_states.md` before handling missing, conflicting, suppressed, unauthorized, partial, stale, or future evidence.
- Use `scripts/qualification_evidence.py` for strict validation, complete-population reconciliation, condition evaluation, state propagation, and exact rendering.

## Operating Rules

1. Work offline and read-only. Never query, scrape, enrich, monitor, cache, route, nurture, archive, alert, message, export, publish, or modify CRM, marketing, sales, task, campaign, workflow, account, contact, lead, or worker records.
2. Require one effective customer policy with stable ID/version, exact purpose, owner, human reviewer, marketing and sales approvals, privacy and legal reviews, lawful-basis, notice, objection, correction, recipient, retention, qualification-policy, cutoff, timezone, source bindings, condition definitions, and prohibited uses.
3. Accept pseudonymous structured records only. Reject names, emails, phones, domains, addresses, URLs, free text, notes, transcripts, message content, protected traits, special-category data, worker attributes, seller-performance data, and unapproved behavioral surveillance.
4. Reconcile the complete declared record population and every complete approved source population. Missing, duplicate, extra, stale, future, unauthorized, partial, or conflicting evidence fails closed.
5. Bind every condition observation to one exact record, customer-authored condition/version, approved source/schema/authorization/query/page/pseudonymization/population, unique evidence receipt, recorded state, occurrence time, and capture time.
6. Evaluate only exact boolean conditions. Required conditions must be `recorded-true`; disqualifying conditions must be `recorded-false`. Do not invent points, weights, thresholds, decay, neutral values, fuzzy matches, imputation, confidence, or fallback ICP rules.
7. Return only `CUSTOMER_POLICY_CONDITIONS_MET`, `CUSTOMER_POLICY_CONDITIONS_NOT_MET`, `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, or `UNAUTHORIZED` for each record.
8. A condition result is not intent, fit, lead quality, contact validity, sales readiness, conversion probability, account health, priority, compliance, or permission to apply an MQL lifecycle label.
9. Never identify, score, rank, compare, profile, or coach people, accounts, segments, campaigns, or workers. Never recommend a route, owner, sequence, nurture, archive, threshold, outreach, enrichment, monitoring, or model change.
10. Human marketing, sales, legal, privacy, and lifecycle owners decide labels and actions outside this skill after reviewing the evidence and applicable rights.
11. Return fixed no-action boundaries. The helper never authorizes a lifecycle label, outreach, routing, system action, downstream decision, or publication.
12. R1: never characterize adequacy, performance, risk, confidence, quality, intent, fit, or readiness with an adjective. The helper emits only exact evidence states.
13. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
14. Freeze policy, inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. Freeze governance, source bindings, condition definitions, population, and cutoff.
2. Reconcile every declared record across every approved source population.
3. Validate one observation for every record-condition pair.
4. Propagate unresolved evidence before evaluating exact conditions.
5. Render the helper result exactly; humans own any lifecycle label or action.

## Worked Example

Input: one pseudonymous record has complete approved evidence for two required conditions and one disqualifying condition. The required conditions are recorded true and the disqualifying condition is recorded false. Run the helper: it returns `CUSTOMER_POLICY_CONDITIONS_MET`, the exact evidence receipt IDs, and false action flags. It does not call the record an MQL, infer intent, predict conversion, rank it, route it, or authorize outreach.

## Failure Boundary

Missing or incompatible governance, source, schema, authorization, query, page, pseudonymization, population, condition, state, timestamp, lawful-basis, notice, objection, correction, recipient, retention, or human-review evidence remains unresolved. Never replace it with CRM access, enrichment, generic scoring, medians, benchmarks, fuzzy matching, confidence, profiling, prediction, recommendations, writing, messaging, or downstream action.
