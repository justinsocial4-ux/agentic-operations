---
name: revops-sequence-enrollment
description: "Produces a policy-controlled, preview-only sequence recommendation after verifying qualification, contactability, suppression, ownership, active enrollment, frequency rules, approved persona/vertical mappings, and a versioned sequence library. Make sure to use this skill whenever the user asks to enroll contacts, route prospects to sequences, assign an outbound cadence, match personas to sequences, review sequence eligibility, or bulk-route qualified leads—even if they do not name the agent."
metadata:
  category: "Outbound Orchestration"
  phase: "1"
  data_readiness: "policy_and_suppression_evidence_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved contactability and sequence-routing policy"
  mcps:
    - "CRM and sales-engagement sources in read-only mode"
  minimum_data:
    - "Resolved contact identity, current qualification, contactability, suppression, ownership, and enrollment state"
    - "Versioned persona/vertical mapping and active sequence library"
---

# Sequence Enrollment Review

Recommend an approved outbound sequence for human review. Never treat qualification, job title, email opens, or a fallback rule as permission to contact or authorization to enroll.

## Bundled Resources

- Read `references/data_contract.md` before accepting contact, account, activity, suppression, or enrollment data.
- Read `references/contactability_policy.md` before deciding whether routing is allowed.
- Read `references/matching_policy.md` before classifying persona, vertical, engagement, or selecting a sequence.
- Read `references/evidence_language.md` before describing intent, authority, confidence, or engagement.
- Read `references/action_preview.md` before proposing enrollment, unenrollment, CRM writes, or outreach.
- Read `references/output_template.md` before producing the review.
- Read `references/research_and_claims.md` before repeating platform, legal, benchmark, speed, conversion, or deliverability claims.
- Use `scripts/sequence_router.py` for exact normalization, eligibility, matching, priority, and coverage logic.

## Operating Rules

1. Read source evidence only. Do not enroll, unenroll, send, create tasks, change owners, or update CRM fields.
2. Require a versioned customer-approved contactability policy and sequence library. Do not invent persona, vertical, engagement, priority, fallback, cooldown, or frequency rules.
3. Resolve the durable person/contact identity and account before routing. Quarantine duplicates and conflicting identities.
4. Treat MQL, SAL, SQL, score, or lifecycle stage as qualification evidence only—not consent, lawful basis, contactability, current employment, authority, or intent.
5. Check suppression, opt-out, do-not-contact, hard-bounce, legal/jurisdiction policy, owner/territory scope, active enrollment, cooldown, and frequency cap before matching.
6. A positive suppression or contactability blocker returns `INELIGIBLE`. Missing required evidence returns `ELIGIBILITY_UNKNOWN`; never replace it with a default sequence.
7. Use stable internal IDs and the sequence library version. Confirm the recommended sequence is active and available in the intended workspace/team at the cutoff.
8. Use only exact approved title-to-persona and industry-to-vertical mappings. Do not infer buying authority or persona from title seniority, fuzzy similarity, department, or company size. In the receipt, reproduce the helper's normalized string exactly; never drop, add, or paraphrase tokens.
9. Keep verified current title, mapped persona, and verified buying role separate. A mapped persona is a routing category—not proof of budget or decision authority.
10. Do not treat opens, page views, record modification, or missing activity as human engagement. Use only evidence types approved by policy and preserve each event type.
11. Missing engagement is `UNKNOWN`, not Cold. Missing title or industry is `MAPPING_REQUIRED`, not a wildcard/default match.
12. Match the exact approved dimensions. Wildcards or fallback sequences apply only when the policy explicitly allows them for that dimension and contact population.
13. If multiple best matches share priority, return `AMBIGUOUS_MATCH`; do not choose by file order.
14. If already enrolled in the same sequence, return `NO_CHANGE`. If any active conflicting enrollment exists, return `ENROLLMENT_CONFLICT` for human review.
15. Do not create a 0–100 confidence score. Report rule results, evidence coverage, matched dimensions, unknowns, and conflicts.
16. Do not promise reply, meeting, conversion, speed, labor, pipeline, or deliverability improvement.
17. Minimize contact data in output. Mask email and exclude unnecessary personal/activity detail.
18. Any policy changed after viewing results applies only to future independent routing decisions.
19. Produce a preview with a named approver. Execution requires separate authorization for the exact contact, sequence, channel, and system action.

## Preflight

Record the decision, cutoff, contact population, workspace/team, channel, account/contact unit, and whether the request is one contact or a batch.

Lock the policy:

- contactability policy ID/version, owner, jurisdiction scope, suppression precedence, and required evidence
- qualification statuses and their exact source values
- owner/territory, cooldown, frequency, and active-enrollment rules
- title/persona and industry/vertical mapping versions
- allowed engagement evidence and observation window
- sequence library ID/version, active dates, workspace/team, dimensions, priorities, and explicit wildcard/fallback behavior
- approver and permitted preview fields

If policy or required evidence is absent, return the relevant failure state before sequence matching.

## Workflow

### 1. Build the evidence receipt

Capture source, object/table, stable ID, extraction time, effective time, freshness, field meaning, coverage, conflicts, and exclusions. Mask direct identifiers in the report.

### 2. Run eligibility first

Use the helper to evaluate qualification, email/contactability status, suppression, do-not-contact, bounce, owner scope, active enrollment, cooldown, and frequency. Preserve pass, fail, and unknown per rule.

### 3. Map approved categories

Normalize the source value only for case and whitespace, then perform an exact lookup in the approved mapping. Report the helper's exact normalized value, mapping key/version, and result. Do not shorten `explicit demo request` to `demo request` or otherwise paraphrase a normalized value. Do not use the legacy universal personas, company-size buckets, Jaro-Winkler threshold, or title-derived authority.

### 4. Match the versioned library

Evaluate only active sequences in the correct workspace/team. Match every required dimension, including explicit wildcard rules. Use the approved integer priority only to resolve otherwise valid matches. Keep zero, one, multiple, and tied-best outcomes distinct.

### 5. Check current enrollment and action state

Reconcile current active enrollment immediately before preview. Same sequence yields `NO_CHANGE`; a different or multiple active enrollment yields `ENROLLMENT_CONFLICT`. Never propose automatic unenrollment.

### 6. Produce the preview

Show the recommended sequence ID/name, library version, matched policy rules, blockers, unknowns, masked contact identifier, owner, approver, expiration/recheck requirement, and `NO WRITE / NO SEND` receipt.

## Worked Example

Approved policy `SEQ-7` maps the verified current title `vp sales` to routing persona `revenue_leader`, industry `software` to vertical `saas`, and an explicit demo request to engagement `demo_request`. The contact is qualified, contactable, unsuppressed, in owner scope, under frequency limits, outside cooldown, and has no active enrollment.

Library `LIB-3` has one active sequence matching all three exact categories at priority 10. Return that sequence as `RECOMMENDED_PREVIEW`. Do not call the persona buying authority, the demo request purchase intent, the result high confidence, or the contact enrolled.

## Output Contract

Return six artifacts:

1. **Preflight receipt** — policies, cutoff, scope, source coverage, identity, workspace, and enabled analyses.
2. **Eligibility table** — qualification, contactability, suppression, bounce, owner, enrollment, cooldown, frequency, and pass/fail/unknown.
3. **Mapping table** — masked contact, source values, approved mapping versions, persona, vertical, engagement, and unknowns.
4. **Match table** — active candidates, dimension results, priority, ambiguity, library version, and recommendation state.
5. **Risk/data-gap table** — missing policy/evidence, conflicts, stale data, privacy limits, and excluded contacts.
6. **Action preview and receipt** — exact proposed action, owner, named approver, recheck-before-execution rule, and `NO WRITE / NO SEND`.

## Failure States

- `POLICY_REQUIRED` — contactability, mapping, frequency, or sequence policy is absent.
- `IDENTITY_CONFLICT` — person/contact identity is duplicate or unresolved.
- `INELIGIBLE` — an approved blocking rule failed.
- `ELIGIBILITY_UNKNOWN` — required contactability or suppression evidence is absent.
- `MAPPING_REQUIRED` — a required persona, vertical, or engagement mapping is missing.
- `NO_MATCH` — no active sequence matches all required dimensions.
- `AMBIGUOUS_MATCH` — multiple best matches share the approved priority.
- `NO_CHANGE` — the contact is already active in the recommended sequence.
- `ENROLLMENT_CONFLICT` — another or multiple active enrollments require review.
- `APPROVAL_REQUIRED` — execution lacks separate human approval.

Never turn a failure state into a fallback send.
