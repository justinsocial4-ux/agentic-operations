---
name: revops-icp-list-building
description: "Reviews complete customer-supplied pseudonymous prospect-candidate evidence against exact frozen customer-owned inclusion and exclusion rules without accessing CRM or vendor systems, accepting names or contact details, enriching identities, fuzzy matching, creating fit, confidence, quality, or outreach-readiness scores, ranking or prioritizing people or companies, relaxing rules, exporting lists, writing CRM records, contacting prospects, scheduling, publishing, or driving downstream decisions. Make sure to use this skill whenever the user asks to build, generate, score, rank, enrich, refresh, export, or activate an ICP, target-account, prospect, lead, contact, buyer, outbound, ABM, firmographic, technographic, or decision-maker list—even when the request assumes a company attribute, job title, vendor record, intent signal, engagement event, email status, or prior conversion proves fit, intent, readiness, lawfulness, priority, or permission to contact."
metadata:
  category: "Outbound Orchestration"
  phase: "1"
  data_readiness: "complete_customer_supplied_pseudonymous_candidate_rule_and_governance_packet_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-12"
  dependencies:
    - "Customer-approved purpose, privacy, legal, source, population, rule, pseudonymization, suppression, recipient, retention, and human-review evidence"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable pseudonymous policy, candidate, source, schema, field-definition, rule, role, population, and receipt IDs"
---

# Pseudonymous Prospect-Candidate Rule Evidence Review

Review a complete human-supplied pseudonymous candidate packet against frozen customer inclusion and exclusion rules. Produce exact evidence receipts for human reviewers, not a prospect list, fit score, identity-enrichment result, outreach recommendation, or system action.

## Exact Response Rule

Build the input document, run `scripts/candidate_rule_evidence.py`, and return `render_review_output(review_candidate_evidence(document))` byte for byte. The first response byte must be `{`; the helper supplies one explicit empty terminal line after `}`. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read `references/scope_and_governance.md` before accepting purpose, approvals, recipients, retention, review authorization, or prohibited uses.
- Read `references/candidate_and_population_contract.md` before accepting candidates, populations, pseudonymization, completeness, or human review.
- Read `references/rule_and_observation_contract.md` before accepting sources, schemas, definitions, value kinds, operators, thresholds, windows, or observations.
- Read `references/privacy_direct_marketing_and_identity.md` before handling names, contact details, enrichment, profiling, notices, objections, suppression, or outreach.
- Read `references/platform_permissions_and_sources.md` before interpreting Salesforce, HubSpot, vendor, warehouse, intent, engagement, or enrichment evidence.
- Read `references/output_and_action_boundary.md` before rendering fit, confidence, readiness, ranking, priority, export, CRM, outreach, or downstream states.
- Read `references/verification_sources.md` for current official sources supporting this boundary.
- Read `references/failure_states.md` before handling incomplete, missing, conflicting, stale, future, unauthorized, suppressed, or unmatched evidence.
- Use `scripts/candidate_rule_evidence.py` for strict validation, complete-population reconciliation, exact rule binding, condition evaluation, unresolved-state propagation, and rendering.

## Operating Rules

1. Work offline and read-only. Never accept credentials, query CRM/vendor/warehouse systems, enrich records, reveal identities, export a list, write CRM, contact anyone, notify, retry, schedule, publish, or trigger workflows.
2. Require one effective customer policy with exact purpose, cutoff, timezone, owner, operations/security/privacy/legal approvals, collection, lawful-basis review, notice, objection, suppression, correction/access, recipient, retention, pseudonymization, rule approval, population, review authorization, and prohibited-use receipts.
3. Accept only pseudonymous policy, candidate, source, schema, field-definition, unit, denominator-definition, rule, role, and receipt IDs. Reject names, companies, domains, emails, phones, addresses, URLs, social profiles, credentials, free text, job titles, industries, technologies, behavior, content, notes, and raw CRM/vendor records.
4. Reconcile the complete declared candidate population and every rule population. Missing, duplicate, extra, future, stale, partial, or unauthorized evidence fails closed.
5. Bind every observation to one source version, schema version, field definition, value kind, unit, denominator definition, observation window, source authorization, and exact customer-owned rule.
6. Evaluate only exact numeric operators or exact membership in frozen opaque source-code sets. Never fuzzy-match, infer adjacency, normalize titles, guess seniority, infer company maturity, use proxy behavior, or invent a neutral value, bonus, penalty, weight, threshold, or fallback.
7. Return only `CUSTOMER_RULE_CONDITION_MET`, `CUSTOMER_RULE_CONDITION_NOT_MET`, or an exact unresolved evidence state per rule. An all-conditions state proves only alignment with the frozen supplied rules, not ICP truth, fit, intent, quality, confidence, readiness, lawfulness, effectiveness, or permission to contact.
8. Missing, privacy-suppressed, conflicting, permission-scoped, stale, or unavailable evidence remains unresolved. Never substitute a cache, another provider, a guessed similarity, a relaxed rule, zero, or a model judgment.
9. Keep each candidate and rule separate. Never average, weight, score, rank, tier, prioritize, benchmark, aggregate, or compare candidates.
10. Human privacy, legal, security, marketing, sales, data, and RevOps owners decide whether evidence is sufficient and whether any identity resolution, enrichment, export, CRM use, outreach, publication, or downstream use is authorized.
11. Return fixed false action flags. The helper never authorizes identity resolution, contact-data release, enrichment, fuzzy matching, scoring, ranking, prioritization, outreach, export, CRM writes, notifications, retries, schedules, publication, or downstream decisions.
12. R1: never characterize adequacy, fit, performance, risk, confidence, quality, accuracy, freshness, compliance, readiness, priority, intent, lawfulness, or impact with an adjective. The helper emits only exact evidence and customer-rule condition states.
13. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only once in its assigned policy, rule, or observation receipt; never recompute, narrate, duplicate, aggregate, or self-correct it.
14. Freeze policy, rule contracts, candidate population, packet, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. Freeze governance, exact rule contracts, complete candidate population, packet, cutoff, authorization, and recipient.
2. Reconcile every declared candidate and every candidate-by-rule observation.
3. Propagate unauthorized, suppressed, conflicting, and missing states before exact source and rule binding.
4. Check source, schema, definition, unit, denominator, window, authorization, rule, candidate, and receipt bindings; evaluate only the supplied rule.
5. Render the helper result exactly; humans own every identity, list, enrichment, outreach, export, CRM, publication, and downstream decision.

## Worked Example

Input: two pseudonymous candidates and two frozen customer rules. One candidate has both conditions met; the other has one condition not met and one missing observation. The helper keeps every candidate and rule separate and returns exact condition or missing-evidence states. It does not label either candidate a fit, rank them, reveal contact data, export a list, write CRM, or authorize outreach.

## Failure Boundary

Missing or incompatible governance, privacy, recipient, retention, review, source, schema, definition, unit, denominator, rule, authorization, window, population, candidate, observation, timestamp, or receipt evidence remains unresolved or unmatched. Never replace it with enrichment, fuzzy inference, a default, score, confidence, readiness, rank, priority, recommendation, export, write, contact, notification, retry, schedule, publication, or downstream action.
