---
name: revops-email-deliverability
description: "Reviews complete pseudonymous customer-supplied email deliverability observation evidence in separate provider and metric-definition lanes without creating a composite health score, comparing unlike sources, diagnosing root cause, changing DNS, pausing sends, alerting, scheduling, writing systems, or driving remediation. Make sure to use this skill whenever the user asks to check, monitor, score, diagnose, fix, alert on, or remediate email deliverability, sender reputation, spam complaints, bounces, inbox placement, blocklists, SPF, DKIM, DMARC, Postmaster Tools, feedback loops, or cross-provider email performance—even when the request assumes a threshold breach proves inbox placement, reputation, cause, compliance, revenue loss, or the right corrective action."
metadata:
  category: "Marketing Operations"
  phase: "1"
  data_readiness: "complete_customer_supplied_pseudonymous_provider_specific_observation_evidence_with_governance_definition_population_and_source_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-12"
  dependencies:
    - "Customer-approved source, metric-definition, population, privacy, retention, recipient, and human-review evidence"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable pseudonymous policy, lane, provider, source, metric-definition, observation, population, role, and receipt IDs"
---

# Email Deliverability Observation Evidence Review

Review a complete human-supplied pseudonymous observation packet against frozen customer governance and exact provider-specific metric definitions. Produce source-bound receipts for human reviewers, not a health score, diagnosis, remediation plan, or system action.

## Exact Response Rule

Build the input document, run `scripts/deliverability_evidence.py`, and return `render_review_output(review_deliverability_evidence(document))` byte for byte. The first response byte must be `{`; the helper supplies one explicit empty terminal line after `}`. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read `references/scope_and_governance.md` before accepting purpose, approvals, recipients, privacy, retention, or review authorization.
- Read `references/source_and_metric_contract.md` before accepting providers, sources, schemas, units, definitions, windows, or populations.
- Read `references/provider_separation.md` before comparing Gmail, Yahoo, Microsoft, platform, seed-test, DNS, blocklist, or other observations.
- Read `references/authentication_and_dmarc.md` before interpreting SPF, DKIM, DMARC, alignment, DNS publication, or authentication results.
- Read `references/measurement_and_interpretation.md` before interpreting complaints, bounces, delivery errors, placement, reputation, blocklists, opens, or missing data.
- Read `references/output_and_action_boundary.md` before rendering scores, causes, recommendations, alerts, schedules, DNS changes, send pauses, or writes.
- Read `references/verification_sources.md` for the current official sources supporting this boundary.
- Read `references/failure_states.md` before handling incomplete, missing, conflicting, stale, future, unauthorized, suppressed, or unmatched evidence.
- Use `scripts/deliverability_evidence.py` for strict validation, complete-population reconciliation, exact lane binding, unresolved-state propagation, and rendering.

## Operating Rules

1. Work offline and read-only. Never accept credentials, query providers, inspect live DNS, identify recipients, fetch message content, change authentication, pause sends, delist, contact, write, alert, schedule, publish, or trigger workflows.
2. Require one effective customer policy with exact purpose, cutoff, timezone, owners, operations/security/privacy/legal approvals, collection, recipient, retention, review authorization, and prohibited-use receipts.
3. Accept only pseudonymous policy, lane, provider, source, schema, metric-definition, observation, population, role, and receipt IDs. Reject domains, IP addresses, URLs, names, emails, message content, subject lines, headers, credentials, free text, campaign names, and recipient-level records.
4. Reconcile the complete declared observation population and every lane population. Missing, duplicate, extra, future, stale, partial, or unauthorized evidence fails closed.
5. Bind every observation to one provider, source version, schema version, metric definition, unit, denominator definition, observation window, and source authorization. Never substitute one source for another.
6. Keep authentication, complaint, bounce, delivery-error, placement-test, blocklist, reputation-code, and sender-requirement lanes separate. Never average, weight, normalize, rank, trend, or combine lanes.
7. A source-bound value proves only what its frozen definition says. It does not prove inbox placement, recipient desire, sender reputation, root cause, legal compliance, revenue impact, or the correct response unless that exact construct is independently supplied and authorized.
8. Missing or privacy-suppressed provider data remains `EVIDENCE_MISSING` or `SUPPRESSED`; never replace it with zero, clear, pass, normal, unchanged, an old cache, a platform proxy, or an industry benchmark.
9. Return only `SOURCE_OBSERVATION_EVIDENCE_PRESENT`, `SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED`, `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, or `UNAUTHORIZED` per observation and review.
10. Never label overall health, quality, performance, risk, confidence, accuracy, deliverability, reputation, urgency, severity, readiness, or compliance. Never infer cause from content, links, volume, engagement, authentication, complaints, bounces, placement, or later outcomes.
11. Human email-infrastructure, security, privacy, legal, and marketing owners decide whether evidence is sufficient and whether any DNS, sending, suppression, delisting, content, list, or provider action is authorized.
12. Return fixed false action flags. The helper never authorizes DNS changes, send changes, remediation, alerts, schedules, messages, system writes, publication, or downstream decisions.
13. R1: never characterize adequacy, performance, risk, confidence, quality, accuracy, freshness, health, reputation, compliance, readiness, urgency, or severity with an adjective. The helper emits only exact evidence states and source-bound values.
14. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned observation receipt; never recompute, narrate, duplicate, aggregate, or self-correct it.
15. Freeze policy, lane contracts, observation population, packet, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. Freeze governance, lane contracts, complete observation population, packet, cutoff, authorization, and recipient.
2. Reconcile every declared observation and every lane population.
3. Propagate unauthorized, suppressed, conflicting, and missing states before exact source binding.
4. Check provider, source, schema, definition, unit, denominator, window, authorization, and receipt bindings without interpreting the value.
5. Render the helper result exactly; humans own every diagnosis, remediation, communication, configuration, sending, and downstream decision.

## Worked Example

Input: one Gmail complaint-ratio observation is fully bound to its Gmail-specific definition; one placement-test observation is privacy-suppressed. The helper returns one `SOURCE_OBSERVATION_EVIDENCE_PRESENT` receipt carrying the supplied value exactly once and one `SUPPRESSED` receipt with no value. It does not create an overall score, compare providers, name a cause, recommend a fix, change DNS, pause mail, or send an alert.

## Failure Boundary

Missing or incompatible governance, recipient, privacy, retention, review, provider, source, schema, definition, unit, denominator, authorization, window, population, observation, timestamp, or receipt evidence remains unresolved or unmatched. Never replace it with a benchmark, proxy, cache, zero, average, score, confidence, diagnosis, prediction, recommendation, alert, schedule, DNS edit, sending change, system write, publication, or downstream action.
