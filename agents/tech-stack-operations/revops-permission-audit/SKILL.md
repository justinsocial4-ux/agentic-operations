---
name: revops-permission-audit
description: "Reviews a supplied, pseudonymous account-access snapshot against customer-approved account-type, authorization, entitlement, exception, and activity rules with exact population receipts—without claiming effective permissions, compliance, risk, savings, or remediation authority. Make sure to use this skill whenever the user asks to audit permissions, review access, find access mismatches, inspect inactive accounts, check role entitlements, prepare access-review evidence, or validate a permission report—even when they do not name the agent."
metadata:
  category: "Tech Stack & Operations"
  phase: "2"
  data_readiness: "complete_approved_account_assignment_entitlement_authorization_exception_and_activity_evidence_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved source, population, account-type, access-rule, authorization, exception, activity, privacy, and workforce policies"
  mcps:
    - "Approved pseudonymous access evidence in read-only mode"
  minimum_data:
    - "Stable account, subject, rule, entitlement, evidence, receipt, and policy IDs with source control totals"
---

# Account Access Evidence Review

Compare supplied observed entitlements with approved rules. Do not discover live access, certify compliance, score risk, or remediate.

## Exact Response Rule

Build the input document, run `scripts/access_evidence.py`, and return `render_review_output(review)` byte for byte. Write no model-generated introduction, table, calculation, summary, correction, or text outside helper stdout. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting the purpose, control context, roles, or requested decision.
- Read `references/source_and_population.md` before using account, assignment, entitlement, or activity snapshots.
- Read `references/account_and_identity.md` before joining identities or classifying individual, shared, service, emergency, temporary, or contractor accounts.
- Read `references/access_rules_and_exceptions.md` before comparing required, allowed, prohibited, or temporary access.
- Read `references/activity_and_authorization.md` before using login/activity or employment/authorization state.
- Read `references/compliance_and_uncertainty.md` before discussing effective access, risk, confidence, severity, SOC 2, or other compliance.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_and_privacy_limits.md` before discussing access changes, tickets, alerts, savings, or workforce actions.
- Use `scripts/access_evidence.py` for validation, reconciliation, set comparison, activity calculation, exceptions, and exact rendering.

## Operating Rules

1. Work read-only from supplied evidence. Do not call admin APIs, query live systems, use cached substitutes, or change access.
2. Require a customer-owned policy with stable IDs/versions, cutoff, source/schema and entitlement namespace, observed-access semantics, control totals, account types, access rules, authorization source, exception rules, optional activity rule, privacy/workforce scope, control context, roles, correction path, and prohibited uses.
3. Reconcile declared account, assignment, and entitlement-occurrence totals exactly. Duplicate, future, stale, unknown, or incomplete evidence blocks conclusions; never produce a partial audit verdict.
4. Use stable pseudonymous account and subject IDs. Reject names, emails, phones, message content, fuzzy matching, and inferred identity links.
5. Preserve organization-defined account types. Never infer individual, shared, group, service, integration, emergency, guest, developer, temporary, or contractor status from labels or domains.
6. Call the result `OBSERVED_ENTITLEMENT_COMPARISON`. Do not claim effective access because platform grants, muting/denies, dependencies, licenses, groups, sharing, record scope, or connected-app paths may be outside the snapshot.
7. Compare only exact entitlement IDs in the policy's namespace/version. Keep required-missing, prohibited-observed, outside-allowed, active-exception, expired-exception, and unknown states explicit.
8. Treat authorization state separately from observed platform state. Report a mismatch; do not infer termination, compromise, business need, or a required access change.
9. Apply activity logic only when the policy supplies a numeric threshold and eligible account types. Missing activity is not inactivity. Report `THRESHOLD_EXCEEDED`, `WITHIN_THRESHOLD`, or an unresolved state without an adequacy or risk label.
10. Keep population, entitlement, authorization, exception, and activity lanes independent. One unresolved lane must not manufacture or erase another.
11. Do not calculate severity, probability, confidence, compliance, savings, license recoverability, breach impact, or remediation priority.
12. Do not rank accounts or infer role fitness, productivity, employment status, intent, cause, or workforce performance.
13. R1: never characterize data adequacy with `small`, `large`, `enough`, `limited`, or `insufficient` unless an approved numerical policy defines that exact label. Report helper states and counts.
14. R2: return one helper-rendered response. Every numeric value must come from the helper and appear only in that response; never recompute, narrate, round differently, or self-correct.
15. Freeze the policy, evidence, helper output, and review receipt. Corrections require a new review version.

## Workflow

1. **Freeze policy.** Validate source, namespace, population, account-type, access, authorization, exception, activity, privacy, and control-context definitions.
2. **Register evidence.** Validate source/version/schema/as-of/extraction/access receipts.
3. **Reconcile population.** Match declared accounts, assignments, and entitlement occurrences exactly.
4. **Compare lanes.** Evaluate supplied authorization, observed entitlements, exceptions, and activity independently.
5. **Preserve boundaries.** Mark the packet as review evidence, not certification or action authority.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: complete pseudonymous account rows, approved rules, one time-bounded exception, authoritative authorization states, and an activity threshold.

Output: the helper returns exact population receipts and per-account lane states. It prints no name, email, effective-access claim, severity, compliance verdict, savings estimate, or remediation action.

## Failure Boundary

Missing or incompatible evidence remains `SOURCE_REQUIRED`, `POLICY_REQUIRED`, `CONFLICTING`, `STALE`, or `POPULATION_INCOMPLETE`. Never turn an unresolved lane into an access or compliance conclusion.
