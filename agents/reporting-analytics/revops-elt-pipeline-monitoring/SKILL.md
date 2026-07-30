---
name: revops-elt-pipeline-monitoring
description: "Reviews complete pseudonymous customer-supplied ELT pipeline observation packets against exact platform-specific source, field-definition, population, window, and customer-owned rule evidence without accessing live systems, accepting credentials, merging unlike lanes, creating health or severity scores, diagnosing causes, relaxing thresholds, alerting, retrying, remediating, scheduling, writing, publishing, or driving downstream decisions. Make sure to use this skill whenever the user asks to monitor, score, diagnose, alert on, fix, retry, or remediate Fivetran, dbt, Workato, Snowflake, BigQuery, warehouse freshness, sync status, job results, test failures, schema changes, rate limits, or pipeline health—even when the request assumes a timestamp, API response, test count, schema difference, missing source, or upstream incident proves completion, staleness, corruption, root cause, business impact, urgency, or the right corrective action."
metadata:
  category: "Reporting & Analytics"
  phase: "1"
  data_readiness: "complete_customer_supplied_pseudonymous_platform_specific_pipeline_observation_packet_with_governance_rule_population_and_source_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-12"
  dependencies:
    - "Customer-approved platform source, field-definition, rule, population, privacy, retention, recipient, and human-review evidence"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable pseudonymous policy, lane, platform, source, schema, definition, rule, observation, population, role, and receipt IDs"
---

# ELT Pipeline Observation and Rule Evidence Review

Review a complete human-supplied pseudonymous pipeline observation packet against frozen customer governance and exact platform-specific rule contracts. Produce evidence receipts for human reviewers, not pipeline health, incident diagnosis, remediation, or system action.

## Exact Response Rule

Build the input document, run `scripts/pipeline_evidence.py`, and return `render_review_output(review_pipeline_evidence(document))` byte for byte. The first response byte must be `{`; the helper supplies one explicit empty terminal line after `}`. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read `references/scope_and_governance.md` before accepting purpose, approvals, recipients, privacy, retention, or review authorization.
- Read `references/source_and_rule_contract.md` before accepting platforms, sources, schemas, definitions, units, rules, windows, or populations.
- Read `references/platform_separation.md` before combining Fivetran, dbt, Workato, Snowflake, BigQuery, warehouse, connector, job, test, or schema observations.
- Read `references/freshness_jobs_and_schema.md` before interpreting freshness, completion, job results, test counts, schema snapshots, or metadata timestamps.
- Read `references/privacy_security_and_logs.md` before handling credentials, owners, URLs, query text, error text, logs, identifiers, or warehouse metadata.
- Read `references/output_and_action_boundary.md` before rendering health, confidence, severity, cause, impact, alerts, retries, remediation, schedules, writes, or downstream states.
- Read `references/verification_sources.md` for current official sources supporting this boundary.
- Read `references/failure_states.md` before handling incomplete, missing, conflicting, stale, future, unauthorized, suppressed, or unmatched evidence.
- Use `scripts/pipeline_evidence.py` for strict validation, complete-population reconciliation, exact lane/rule binding, unresolved-state propagation, condition evaluation, and rendering.

## Operating Rules

1. Work offline and read-only. Never accept credentials, query platforms, execute SQL, inspect live metadata, trigger syncs/tests, reveal identities or operational text, alert, retry, remediate, schedule, write, publish, or trigger workflows.
2. Require one effective customer policy with exact purpose, cutoff, timezone, owners, operations/security/privacy/legal approvals, collection, recipient, retention, review authorization, rule-policy receipts, and prohibited uses.
3. Accept only pseudonymous policy, lane, platform, source, schema, field-definition, denominator-definition, rule, observation, population, role, and receipt IDs. Reject names, emails, domains, IPs, URLs, credentials, tokens, connection strings, query text, error text, free text, table/field names, pipeline names, raw logs, record data, and customer content.
4. Reconcile the complete declared observation population and every lane population. Missing, duplicate, extra, future, stale, partial, or unauthorized evidence fails closed.
5. Bind every observation to one platform, source version, schema version, field definition, value kind, unit, denominator definition, observation window, source authorization, and exact customer-owned rule.
6. Keep connection state, source freshness, job result, test result, schema snapshot, warehouse metadata, record count, and rate-limit lanes separate. Never average, weight, rank, trend, normalize, or combine lanes.
7. Evaluate only the frozen rule operator and threshold. Return `CUSTOMER_RULE_CONDITION_MET` or `CUSTOMER_RULE_CONDITION_NOT_MET`; never rename either state to health, severity, compliance, incident, outage, freshness, corruption, risk, priority, or action.
8. A source-bound value or condition proves only what its exact frozen definition says. An API response does not prove an asynchronous operation completed; a timestamp does not prove data correctness; a schema difference does not prove corruption or impact; a test result does not prove root cause.
9. Missing, delayed, privacy-suppressed, permission-scoped, or unavailable source data remains unresolved. Never replace it with zero, success, unchanged, cached data, a different platform, relaxed thresholds, or a model guess.
10. Return only `SOURCE_OBSERVATION_EVIDENCE_PRESENT`, `SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED`, `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, or `UNAUTHORIZED` per observation and review.
11. Human data-platform, security, privacy, legal, analytics, and RevOps owners decide whether evidence is sufficient and whether any alert, retry, remediation, configuration, scheduling, communication, or downstream use is authorized.
12. Return fixed false action flags. The helper never authorizes live access, threshold relaxation, alerts, retries, remediation, schedules, messages, system writes, publication, or downstream decisions.
13. R1: never characterize adequacy, performance, risk, confidence, quality, accuracy, freshness, health, severity, urgency, reliability, compliance, readiness, or impact with an adjective. The helper emits only exact evidence and condition states.
14. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned observation or rule receipt; never recompute, narrate, duplicate, aggregate, or self-correct it.
15. Freeze policy, lane/rule contracts, observation population, packet, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. Freeze governance, platform-specific lane/rule contracts, complete observation population, packet, cutoff, authorization, and recipient.
2. Reconcile every declared observation and every lane population.
3. Propagate unauthorized, suppressed, conflicting, and missing states before exact source and rule binding.
4. Check platform, source, schema, definition, unit, denominator, window, authorization, rule, and receipt bindings; evaluate only the supplied rule.
5. Render the helper result exactly; humans own every interpretation, incident, alert, retry, remediation, configuration, communication, and downstream decision.

## Worked Example

Input: one Fivetran connection-state observation exactly matches its frozen source code and customer rule; one dbt freshness observation is missing. The helper returns one exact condition state and one `EVIDENCE_MISSING` receipt. It does not combine them into a stack score, call either pipeline healthy or stale, infer a cause, relax an SLA, send an alert, retry a job, or change any system.

## Failure Boundary

Missing or incompatible governance, recipient, privacy, retention, review, platform, source, schema, definition, unit, denominator, rule, authorization, window, population, observation, timestamp, or receipt evidence remains unresolved or unmatched. Never replace it with a cache, proxy, default, zero, score, confidence, severity, diagnosis, impact estimate, threshold change, alert, retry, remediation, schedule, message, write, publication, or downstream action.
