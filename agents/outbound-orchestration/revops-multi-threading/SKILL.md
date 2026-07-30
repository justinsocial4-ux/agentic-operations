---
name: revops-multi-threading
description: "Audits opportunity stakeholder coverage, separates verified buying roles from title-based candidates, finds single points of failure, shows missing or dormant roles, and ranks human-reviewable contacts for introduction plans. Make sure to use this skill whenever the user asks which deals are single-threaded, who is missing from a buying committee, whether an opportunity depends on one person, who else to involve, how to map deal contacts, or how to build a multi-threading plan—even if they do not name the agent."
metadata:
  category: "Outbound Orchestration"
  phase: "2"
  data_readiness: "day_1"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "revops-data-account-hierarchy (optional enhancement)"
  mcps:
    - "Salesforce MCP or HubSpot MCP for read-only deal/contact/activity evidence"
  minimum_data:
    - "Opportunity/deal ID, pipeline, stage, account, owner"
    - "Opportunity contact roles or HubSpot Buying role when available"
    - "Contact title, department, seniority, relationship, and meaningful activity evidence"
---

# Opportunity Multi-Threading

Show what the CRM proves about stakeholder coverage, what it merely suggests, and what remains unknown. Do not turn job titles into invented buying authority or convert contact count into a fake win probability.

## Bundled Resources

- Read `references/data_contract.md` before querying a CRM or accepting an export.
- Read `references/role_evidence.md` before assigning, inferring, or displaying buying roles.
- Read `references/stage_policy.md` before deciding which roles matter for a pipeline stage.
- Read `references/scoring_rules.md` before ranking candidate contacts or interpreting coverage.
- Read `references/engagement_playbook.md` before proposing introductions or outreach.
- Read `references/research_and_claims.md` before repeating win-rate, labor, or outcome claims.
- Use `scripts/multi_threading.py` for exact engagement bands, coverage assessment, candidate scoring, and ranking.

## Operating Rules

1. Read CRM records; do not add contacts, assign roles, create tasks, or send outreach during analysis.
2. Prefer explicit Salesforce Opportunity Contact Roles or HubSpot Buying role values over inference.
3. Label title/department matches `INFERRED_CANDIDATE`, not verified role or probability.
4. Treat Champion as a behavior demonstrated in the deal, not a job-title synonym.
5. Do not label a person a Blocker from title or department. Describe the review function needed instead.
6. Use meaningful logged calls, meetings, and two-way messages for engagement. Do not equate record modification, opens, or clicks with stakeholder engagement.
7. Keep stage-role requirements customer-approved and pipeline-specific.
8. Report coverage, dormant roles, and single points of failure. Do not manufacture a 0–100 deal-risk score.
9. Never expose private contact details beyond the approved report audience.
10. Propose human-reviewed introductions; do not automate cold outreach from inferred roles.

## Preflight

### 1. Confirm scope and policy

Show:

- CRM, pipeline, stages, owners, amount band, and date range;
- approved stage-to-role policy version;
- engagement lookback and meaningful-activity definition;
- role taxonomy and evidence levels;
- whether the user wants one deal or a portfolio audit;
- preview-only status.

If no approved stage policy exists, analyze contact depth and role evidence without declaring a role missing.

### 2. Verify evidence

- If a CRM is connected, retrieve the fields in `references/data_contract.md`.
- If not connected, accept a supplied CSV/JSON export.
- If neither exists, return the export contract and stop.

Audit opportunity-account links, contact associations, role fields, contact IDs, title/department coverage, activity timestamps/types, and account hierarchy evidence. Keep unavailable fields unknown instead of failing an unrelated part of the analysis.

## Workflow

### Step 1: Build the deal-contact ledger

Create one row per opportunity-contact relationship. Preserve:

- opportunity, account, contact, owner, pipeline, and stage IDs;
- original stage and approved canonical stage;
- explicit role value, source, author, and last verification date;
- original title, department, seniority, and reports-to evidence;
- meaningful activity count, direction, type, and last timestamp;
- opt-out, do-not-contact, privacy, and access restrictions.

Do not pull every account contact into the deal's active committee. Distinguish associated contacts, opportunity-linked contacts, and meaningfully engaged contacts.

### Step 2: Classify role evidence

Use `references/role_evidence.md`:

- `VERIFIED`: explicit opportunity/deal role confirmed by a human or approved system of record;
- `INFERRED_CANDIDATE`: title, department, seniority, hierarchy, or activity suggests a possible role;
- `UNKNOWN`: evidence is absent or conflicting.

Allow multiple roles per person and multiple people per role. Preserve conflicts for review.

### Step 3: Classify engagement

Use customer-approved bands or these tuneable defaults:

- Active: meaningful activity 0–30 days ago;
- Cold: 31–90 days;
- Dormant: more than 90 days;
- Uncontacted: no meaningful activity exists;
- Unknown: activity coverage is unavailable.

Show the exact last activity and evidence type. A contact can have a verified role but dormant engagement.

### Step 4: Assess coverage without fake risk math

Use `scripts/multi_threading.py` with the approved required-role policy.

Return:

- distinct active stakeholder count;
- verified active roles;
- inferred-only active roles;
- cold/dormant verified roles;
- missing roles;
- single-point-of-failure flag when exactly one stakeholder is active;
- `URGENT_REVIEW`, `REVIEW`, `HEALTHY`, or `DATA_GAP`, with explicit reasons.

`URGENT_REVIEW` is an operating priority, not a predicted loss probability. It applies under the default policy when a late-stage deal has one active stakeholder or lacks a verified active required role.

### Step 5: Rank role candidates

For each missing verified role, score only contacts already lawfully present in the approved account data. Use explicit 0–1 evidence inputs:

- role/title fit × 0.30;
- department/function fit × 0.20;
- seniority fit × 0.15;
- relationship/hierarchy evidence × 0.20;
- prior meaningful engagement × 0.15.

Require every component. The weighted result is a prioritization score, not role confidence or buyer probability. Show all contributions and conflicting evidence. Exclude opted-out or restricted contacts.

### Step 6: Propose an introduction plan

Use `references/engagement_playbook.md`. Prefer:

1. confirm the missing role with the existing verified stakeholder;
2. request a warm introduction;
3. tailor the meeting purpose to the verified review function;
4. ask the rep to approve any outreach;
5. recheck role and engagement evidence after the interaction.

Do not invent contact details, reporting lines, budget authority, or personalized claims.

### Step 7: Validate

Verify:

- every contact is associated with the correct account and opportunity context;
- every verified role has a source and date;
- inferred candidates are never presented as confirmed buyers;
- active engagement uses meaningful evidence;
- required roles come from the approved policy version;
- candidate scores reconcile to five components;
- restricted contacts are excluded;
- no CRM write or outreach occurred.

## Failure and Degradation Paths

| Condition | Response |
|---|---|
| CRM unavailable | Offer export analysis or connection troubleshooting. |
| Stage policy missing | Report depth/evidence only; do not declare role gaps. |
| Explicit role fields missing | Show inferred candidates and request rep verification. |
| Activity coverage missing | Engagement is unknown; disable single-point-of-failure conclusion. |
| Account-contact association uncertain | Exclude the contact from recommendations and show the data gap. |
| Reports-to missing | Disable relationship component; do not default it to a neutral score. |
| Candidate component missing | Do not calculate a complete score. |
| No lawful candidate exists | Recommend asking the verified stakeholder who owns the function; do not scrape or invent a person. |

## Output Contract

Return:

1. `Preflight receipt` — scope, policy, evidence, coverage, enabled/disabled analyses.
2. `Opportunity coverage table` — active stakeholders, verified/inferred/cold/missing roles, priority, reasons.
3. `Role evidence table` — source, evidence level, last verification, conflicts.
4. `Candidate table` — component scores, total, caveats, review state.
5. `Introduction plan` — human-approved steps and purpose.
6. `Validation receipt` — traceability, exclusions, and no-action status.

## Worked Example

**Input:** A Negotiation-stage policy requires Champion, Economic Buyer, Technical Buyer, and Budget Holder. Sarah is a verified Champion with meaningful activity 2 days ago. Tom is a verified Technical Buyer whose last meaningful activity was 45 days ago. No verified Economic Buyer or Budget Holder exists. Jennifer is a CFO candidate with role fit 1.0, department fit 1.0, seniority fit 1.0, relationship evidence 0.8, and prior meaningful engagement 0.2.

**Result:**

- Distinct active stakeholders: 1 (Sarah).
- Verified active roles: Champion.
- Cold verified roles: Technical Buyer.
- Missing verified roles: Economic Buyer, Budget Holder.
- Single point of failure: yes.
- Priority: `URGENT_REVIEW` under the default late-stage policy; this is not a loss prediction.
- Jennifer prioritization score: `1×0.30 + 1×0.20 + 1×0.15 + 0.8×0.20 + 0.2×0.15 = 0.84`.
- Jennifer remains an `INFERRED_CANDIDATE` until a rep or system of record verifies her deal role.
- Proposed next step: ask Sarah who owns financial approval and request an introduction; send nothing automatically.

## Verification Checklist

- [ ] Stage policy is approved and versioned.
- [ ] Verified and inferred roles are separated.
- [ ] Meaningful activity, not record modification, drives engagement.
- [ ] Contact depth and role coverage are both visible.
- [ ] Priority is not framed as predicted win/loss risk.
- [ ] Candidate scores are complete and reconcilable.
- [ ] Restricted contacts are excluded.
- [ ] Outreach remains preview-only until separately approved.
