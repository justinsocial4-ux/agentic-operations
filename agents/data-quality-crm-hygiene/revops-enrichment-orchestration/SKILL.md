---
name: revops-enrichment-orchestration
description: "Reviews complete pseudonymous customer-supplied enrichment route plans against exact governance, suppression, field, provider-contract, authorization, and charge evidence without choosing or ranking providers, accessing personal data, enriching records, resolving conflicting values, spending credits, writing CRM fields, or taking downstream action. Make sure to use this skill whenever the user asks to enrich contacts, leads, accounts, or CRM records; fill missing emails, phones, titles, firmographics, or intent fields; choose, compare, waterfall, or optimize enrichment providers; resolve multi-source enrichment conflicts; estimate enrichment spend; or automate enrichment—even when the request assumes vendor accuracy, confidence, recency, agreement, price, or availability proves which provider or value is best."
metadata:
  category: "Data Quality & CRM Hygiene"
  phase: "2"
  data_readiness: "complete_customer_supplied_pseudonymous_route_plan_with_governance_provider_contract_and_suppression_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved enrichment purpose, privacy, security, legal, suppression, provider-contract, charge, recipient, retention, and human-review policies"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable pseudonymous policy, source, record, field, provider, contract, route, population, and receipt IDs"
---

# Enrichment Route Plan Evidence Review

Review a complete human-supplied enrichment route plan against exact customer policy and provider-contract evidence. Produce receipts for human reviewers, not provider recommendations or enrichment actions.

## Exact Response Rule

Build the input document, run `scripts/route_evidence.py`, and return `render_review_output(review_route_evidence(document))` byte for byte. The first response byte must be `{`; the helper supplies one explicit empty terminal line after `}`. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read `references/scope_and_governance.md` before accepting purpose, approvals, lawful basis, notice, objections, suppression, correction, recipients, retention, or human review.
- Read `references/source_and_population.md` before accepting source authorization, schema, query, page, pseudonymization, or population evidence.
- Read `references/field_and_route_contract.md` before accepting requested fields or human-supplied route assignments.
- Read `references/provider_and_charge_contract.md` before accepting provider field support, authorization, terms, geography, charge units, currency, or unit prices.
- Read `references/privacy_and_identity.md` before handling people, companies, contact details, firmographics, intent, activity, or field values.
- Read `references/output_and_action_boundary.md` before rendering or responding to provider choice, enrichment, conflict resolution, spend, write, alert, schedule, publication, or downstream requests.
- Read `references/verification_sources.md` for current official sources supporting this boundary.
- Read `references/failure_states.md` before handling missing, conflicting, suppressed, unauthorized, partial, stale, or future evidence.
- Use `scripts/route_evidence.py` for strict validation, population reconciliation, exact contract checks, Decimal planned-charge calculations, state propagation, and rendering.

## Operating Rules

1. Work offline and read-only. Never accept credentials, query CRM/provider systems, reveal personal data, enrich, search, scrape, match identity, retry, spend, write, message, alert, schedule, publish, or trigger workflows.
2. Require one effective customer policy with exact purpose, cutoff, timezone, owners, operations/security/privacy/legal approvals, lawful basis, notice, objection, suppression, correction, recipient, retention, route-policy receipts, and prohibited uses.
3. Accept only pseudonymous record, field, provider, contract, route, source, and receipt IDs. Reject names, emails, phones, domains, URLs, addresses, titles, company names, free text, activity, intent, protected data, candidate values, value hashes, provider responses, and raw errors.
4. Reconcile the complete declared record population, complete source populations, exact requested record-field pairs, and exactly one human-supplied route row per pair. Missing, duplicate, extra, future, partial, or unauthorized evidence fails closed.
5. Require each field to have a customer-approved definition, purpose, minimization, and field-policy receipt. Never infer which fields are missing, useful, critical, accurate, or appropriate.
6. Require each provider version to have exact customer contract, authorization window, terms, geography, field-support, price, charge-unit, and currency receipts. Never use generic prices, credits, accuracy, coverage, confidence, or availability assumptions.
7. Accept only the customer-supplied provider assignment. The helper checks whether that provider contract supports the exact field and authorization window; it never selects, ranks, reorders, falls back, optimizes, or recommends a provider.
8. A suppressed request returns `SUPPRESSED` and cannot carry a provider assignment. Honor unauthorized, conflicting, or missing evidence before any contract check or charge calculation.
9. For a matched supplied assignment, calculate the exact planned charge once from the frozen non-negative Decimal unit cost. Sum only same-policy-currency matched charges once. Planned charge is not an invoice, authorization to spend, or expected result.
10. Return only `CUSTOMER_ROUTE_EVIDENCE_MATCHED`, `CUSTOMER_ROUTE_EVIDENCE_NOT_MATCHED`, `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, or `UNAUTHORIZED` per route and review.
11. Never label provider accuracy, confidence, quality, coverage, recency, fit, optimality, risk, readiness, cost-effectiveness, or compliance. Never resolve candidate values or say agreement/recency/vendor reputation proves truth.
12. Human privacy, legal, security, operations, procurement, and CRM owners decide whether enrichment is lawful, necessary, accurate, affordable, authorized, and allowed to execute.
13. Return fixed false action flags. The helper never authorizes enrichment, spend, provider calls, CRM writes, outreach, downstream decisions, or publication.
14. R1: never characterize adequacy, performance, risk, confidence, quality, accuracy, freshness, fit, or readiness with an adjective. The helper emits only exact evidence states.
15. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned route or aggregate receipt; never recompute, narrate, duplicate, or self-correct it.
16. Freeze policy, contracts, plan, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. Freeze governance, source bindings, fields, provider contracts, record population, requested record-field pairs, route rows, cutoff, and recipient.
2. Reconcile every source population and every declared record-field pair.
3. Propagate suppression and unresolved evidence before checking the supplied provider assignment.
4. Check exact field support and authorization; calculate matched planned charges once.
5. Render the helper result exactly; humans own provider choice, enrichment execution, value review, spend, writes, and downstream use.

## Worked Example

Input: two pseudonymous record-field requests have complete policy and provider-contract evidence. A human supplies one supported provider assignment and leaves the suppressed request unassigned. The helper returns one `CUSTOMER_ROUTE_EVIDENCE_MATCHED` receipt with one planned charge and one `SUPPRESSED` receipt, plus false action flags. It does not identify anyone, choose a provider, call an API, resolve a value, spend credits, update CRM, or authorize outreach.

## Failure Boundary

Missing or incompatible governance, lawful-basis, notice, objection, suppression, correction, recipient, retention, source, schema, authorization, query, page, pseudonymization, population, field, provider, contract, terms, geography, charge, currency, route, timestamp, or human-review evidence remains unresolved. Never replace it with live access, vendor defaults, fuzzy identity, weights, confidence, recency, majority agreement, fallback, prediction, recommendation, write-back, alerts, scheduling, publication, or downstream action.
