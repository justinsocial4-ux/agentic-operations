---
name: revops-integration-health
description: "Reviews complete pseudonymous customer-supplied integration observations against exact customer-authored contracts without inventing a universal health score, severity, root cause, business impact, confidence, remediation, alert, escalation, or downstream decision. Make sure to use this skill whenever the user asks whether CRM, iPaaS, warehouse, finance, support, or other RevOps integrations are healthy, down, stale, delayed, failing, flapping, or causing forecast/report problems—even when the request assumes an HTTP response, job status, timestamp, record count, API limit, or vendor warning proves end-to-end health or cause."
metadata:
  category: "Tech Stack Operations"
  phase: "1"
  data_readiness: "complete_customer_supplied_pseudonymous_integration_observations_with_governance_and_contract_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved integration purpose, observation contract, privacy, security, recipient, retention, and human-review policies"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable pseudonymous policy, integration, lane, source, population, observation, and receipt IDs"
---

# Integration Observation Evidence Review

Review complete supplied observations against exact customer-authored integration contracts. Produce receipts for a human integration owner, not a universal health or incident decision.

## Exact Response Rule

Build the input document, run `scripts/integration_evidence.py`, and return `render_review_output(review_integration_evidence(document))` byte for byte. The first response byte must be `{`; the helper supplies one explicit empty terminal line after `}`. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read `references/scope_and_governance.md` before accepting purpose, approvals, recipients, retention, or human review.
- Read `references/source_and_population.md` before accepting source authorization, schema, query, page, pseudonymization, or population evidence.
- Read `references/observation_contract.md` before accepting endpoint, connector-job, checkpoint, freshness, or reconciliation definitions.
- Read `references/construct_and_interpretation.md` before using health, availability, outage, cause, impact, severity, confidence, or reliability language.
- Read `references/privacy_and_security.md` before handling secrets, endpoints, topology, logs, system identity, or operational metadata.
- Read `references/output_and_action_boundary.md` before rendering or responding to alert, escalation, remediation, write, schedule, publication, or downstream requests.
- Read `references/verification_sources.md` for current official sources supporting this boundary.
- Read `references/failure_states.md` before handling missing, conflicting, suppressed, unauthorized, partial, stale, or future evidence.
- Use `scripts/integration_evidence.py` for strict validation, population reconciliation, exact comparisons, state propagation, and rendering.

## Operating Rules

1. Work offline and read-only. Never accept secrets, access systems, call APIs, probe endpoints, poll, retry, cache, store monitoring history, alert, message, escalate, remediate, schedule, publish, or modify any system.
2. Require one effective customer policy with stable ID/version, purpose, cutoff, timezone, owner, human reviewer, operations/security/privacy approvals, recipient, retention, observation-policy receipts, source bindings, and prohibited uses.
3. Accept pseudonymous structured evidence only. Reject credentials, tokens, webhook URLs, direct endpoints, hostnames, tenant names, people, emails, message bodies, raw logs, free text, customer records, and secret-bearing error details.
4. Require one customer-authored contract per integration with exactly five separate lanes: source endpoint, connector job, destination endpoint, checkpoint, and reconciliation.
5. Reconcile every declared integration, source population, lane, and unique observation receipt. Missing, duplicate, extra, future, unauthorized, partial, or conflicting evidence fails closed.
6. Compare endpoint and job observations only to exact customer-authored recorded states. Never convert an HTTP code or vendor label into a universal health, outage, or root-cause claim.
7. Compute checkpoint age only from supplied UTC timestamps and compare it only with the contract's approved maximum age. Do not call the result fresh, stale, delayed, or fit for reporting.
8. Reconcile exact non-negative integer source and target totals only when the contract rule is `source-total-equals-target-total`. A match does not prove record identity, field correctness, semantic equivalence, or end-to-end completeness beyond that declared measure.
9. Return only `CONTRACT_OBSERVATION_MATCHED`, `CONTRACT_OBSERVATION_NOT_MATCHED`, `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, or `UNAUTHORIZED` per lane and integration.
10. Never label an integration healthy, degraded, high risk, critical, available, down, recovered, reliable, complete, or compliant. Never infer cause, cascade, forecast/report impact, dollar loss, priority, severity, confidence, or recommended action.
11. Human integration, security, privacy, and operations owners interpret the receipts, validate system meaning, declare incidents, decide remediation, and control any communication or downstream use.
12. Return fixed false action flags. The helper never authorizes an alert, escalation, remediation, system action, downstream decision, or publication.
13. R1: never characterize adequacy, performance, risk, severity, confidence, quality, health, reliability, freshness, or readiness with an adjective. The helper emits only exact evidence states.
14. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned lane receipt; never recompute, narrate, duplicate, or self-correct it.
15. Freeze policy, contracts, inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. Freeze governance, source bindings, integration contracts, populations, cutoff, and recipient.
2. Reconcile exactly one supplied observation for every required integration lane.
3. Validate authorization, capture time, source membership, unique receipts, and lane-specific value shape.
4. Propagate unresolved evidence before exact contract comparison.
5. Render the helper result exactly; humans own interpretation, incident status, action, communication, and downstream use.

## Worked Example

Input: one pseudonymous integration has complete supplied endpoint and job states, a checkpoint timestamp, and source/target totals. The helper compares each lane only with the frozen customer contract, calculates checkpoint age once, calculates count difference once, and returns exact evidence states with false action flags. It does not call the integration healthy or down, infer root cause or business impact, recommend a fix, send an alert, or authorize downstream use.

## Failure Boundary

Missing or incompatible governance, source, schema, authorization, query, page, pseudonymization, population, contract, state, timestamp, count, recipient, retention, or human-review evidence remains unresolved. Never replace it with live access, generic vendor assumptions, endpoint probing, cached history, score bands, confidence, causal narrative, recommendations, alerts, writes, scheduling, publication, or downstream decisions.
