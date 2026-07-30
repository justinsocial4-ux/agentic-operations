---
name: revops-new-hire-readiness
description: "Produces a privacy-controlled, descriptive onboarding milestone review without labeling employees ready, at risk, competent, or suitable for employment action. Make sure to use this skill whenever the user asks to check onboarding progress, review new-hire milestones, compare ramp evidence, find missing training records, assess a ramp cohort, or prepare a manager onboarding review—even if they do not name the agent."
metadata:
  category: "Enablement Operations"
  phase: "1"
  data_readiness: "approved_policy_and_employee_access_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved onboarding policy and employee-data access policy"
  mcps:
    - "HRIS, LMS, and CRM sources in read-only mode"
  minimum_data:
    - "Pseudonymous employee ID, role/cohort, approved hire-date anchor/cutoff dates, milestone definitions, and source coverage"
---

# New-Hire Onboarding Evidence Review

Show what approved onboarding records establish as of a cutoff. Do not turn incomplete system data, sales outcomes, leave, transfers, or arbitrary ramp curves into judgments about an employee.

## Bundled Resources

- Read `references/employee_data_contract.md` before accessing, joining, or reporting employee records.
- Read `references/onboarding_policy.md` before calculating dates or milestone states.
- Read `references/evidence_and_labels.md` before describing progress, readiness, risk, activity, or performance.
- Read `references/cohort_analysis.md` before comparing cohorts or training with sales outcomes.
- Read `references/action_and_access.md` before preparing manager alerts, reminders, coaching, or record changes.
- Read `references/output_template.md` before producing the review.
- Read `references/research_and_claims.md` before repeating ramp, revenue, labor, accuracy, or outcome claims.
- Use `scripts/onboarding_metrics.py` for exact due dates, milestone states, day deltas, counts, and coverage.

## Operating Rules

1. Analyze read-only evidence. Do not message employees/managers, create reminders/tasks, change training status, alter CRM/HRIS/LMS records, or trigger employment workflows.
2. Require a versioned customer-approved onboarding policy and employee-data access policy. Do not import legacy milestones, ramp curves, thresholds, severity bands, or status labels.
3. Use pseudonymous employee IDs in analysis. Exclude names, email, phone, compensation, medical details, and unnecessary note text.
4. Join systems with approved stable IDs. Email matching is allowed only when the policy explicitly approves it and the receipt reports collisions, unmatched rows, and access scope.
5. Verify the requester is authorized for the exact employee/cohort and fields. Aggregate or suppress small groups according to the customer's privacy policy.
6. Treat leave, accommodation, transfer, territory, quota changes, and employment status as restricted policy inputs. Never infer them; apply only HR-approved pause/exclusion adjustments without revealing the reason.
7. Keep `VERIFIED_RECORD`, `POLICY_DERIVATION`, `UNKNOWN`, and `CONFLICT` separate. Missing CRM/LMS evidence is unknown—not inactivity, non-completion, low effort, or poor performance.
8. Calculate each milestone from the approved hire-date anchor, clock, expected-day rule, approved pause days, and verified completion record.
9. Use descriptive milestone states: `COMPLETED_ON_TIME`, `COMPLETED_LATE`, `DUE_NOT_RECORDED`, `PENDING`, or `UNKNOWN_EVIDENCE`.
10. Do not label a person ready, unready, on track, behind, at risk, high/low performer, likely to attrit, or suitable for coaching, PIP, promotion, termination, or lead-routing changes.
11. Quota, activity, pipeline, and training records are different evidence domains. Name period, amount basis, currency, coverage, maturity, and source before comparing them.
12. Do not reconstruct historical milestones from current status or record modification time. Preserve corrections and late-entered records.
13. Do not call observational training/outcome differences causal. Require a preapproved analysis plan, comparable cohorts, mature outcomes, confounder handling, and uncertainty before reporting association.
14. Never recommend mandatory training or an employment action from correlation, a score, a threshold, or this review alone.
15. Show denominators, missingness, cohort definitions, and exclusions beside every percentage or average. Do not manufacture confidence scores.
16. Apply rules created after viewing results only to future independent reviews.
17. Produce neutral manager-review questions and a preview with a named human reviewer. Execution requires separate authorization.

## Preflight

Record the decision, requester role/access, cutoff, employee/cohort scope, role, region, systems, retention/output location, and requested fields.

Lock the policy:

- policy ID/version, owner, effective date, role/cohort and hire-date anchor
- milestone IDs, required evidence, expected-day convention, clock, timezone, and completion rules
- HR-approved pause/exclusion inputs without protected-detail disclosure
- source precedence, correction/late-entry handling, identity join, freshness, and coverage rules
- quota/activity amount basis, currency, period, territory/role changes, if used
- cohort-comparison plan, maturity, minimum-disclosure, confounders, and decision limits
- reviewer/approver, allowed outputs, retention, and action boundary

If access, policy, identity, or required source evidence is absent, stop the affected analysis rather than applying a default.

## Workflow

### 1. Build access and identity receipts

Confirm requester authorization and minimize fields before retrieval. Reconcile approved IDs across HRIS, LMS, and CRM; report matches, unmatched records, duplicates, conflicts, and exclusions.

### 2. Build source coverage

For every milestone domain, report source, extraction/effective time, observation window, eligible count, known count, missingness, corrections, and freshness. Do not interpret unavailable data.

### 3. Calculate milestone states

Use the helper for exact due dates and deltas. When evidence availability is false, return `UNKNOWN_EVIDENCE` even if the calendar due date passed. When evidence is available and no completion is recorded after the due date, return `DUE_NOT_RECORDED`—not failure or poor performance.

### 4. Summarize descriptively

Report milestone counts by state and the individual evidence ledger. Keep quota/activity/training summaries separate. Do not collapse them into a readiness, risk, or confidence score.

### 5. Review cohorts cautiously

Use `references/cohort_analysis.md`. Compare like roles, policies, periods, outcome maturity, territories, leave/transfer treatment, and amount bases. Report association and uncertainty; keep causal and employment decisions unavailable.

### 6. Prepare a human review preview

Ask neutral questions: Is the source complete? Was a correction entered late? Does an HR-approved pause apply? Is the milestone definition current? Does the manager have direct evidence? Do not disclose protected reasons or prescribe employment action.

## Worked Example

Under approved policy `ONB-4`, pseudonymous employee `E-7` starts 2026-06-01. Product training due Day 5 is recorded on its due date; CRM certification due Day 7 is recorded three days late; first demo due Day 21 is pending two days before its due date; another LMS milestone has unavailable source evidence and remains `UNKNOWN_EVIDENCE` even after its calendar due date.

Return exact dates and states. Do not label E-7 ready, behind, at risk, inactive, or in need of coaching.

## Output Contract

Return six artifacts:

1. **Access/preflight receipt** — requester authorization, policy, cutoff, scope, fields, retention, and permitted outputs.
2. **Identity/source coverage** — pseudonymous joins, matches, conflicts, missingness, freshness, and exclusions.
3. **Milestone ledger** — ID, expected/actual dates, approved pause days, exact delta, state, source, and evidence label.
4. **Descriptive summary** — state counts and domain-separated training/activity/quota evidence with denominators.
5. **Cohort/limitations table** — comparability, maturity, confounders, uncertainty, unknowns, and prohibited conclusions.
6. **Human review preview** — neutral questions, named reviewer, exact proposed action, and `NO MESSAGE / NO WRITE / NO EMPLOYMENT DECISION`.

## Failure States

- `ACCESS_DENIED` — requester lacks authorized employee/cohort scope.
- `POLICY_REQUIRED` — milestone, privacy, cohort, or action policy is absent.
- `IDENTITY_CONFLICT` — cross-system employee identity is unresolved or duplicated.
- `SOURCE_UNAVAILABLE` — required HRIS/LMS/CRM evidence cannot be read.
- `UNKNOWN_EVIDENCE` — milestone evidence availability is incomplete.
- `INCOMPARABLE_COHORTS` — policy, role, period, maturity, territory, or treatment differs.
- `ASSOCIATION_UNAVAILABLE` — analysis plan, sample, outcome maturity, or confounder evidence is insufficient.
- `APPROVAL_REQUIRED` — a message, reminder, coaching step, or system action lacks approval.

Never replace a failure state with an employee label.
