---
name: revops-lead-routing
description: "Routes qualified Salesforce or HubSpot leads to the right active owner using account continuity, territory, rep capacity, vertical specialty, and deterministic round-robin fallbacks. Make sure to use this skill whenever the user asks to assign or reassign leads, route MQLs, balance inbound distribution, resolve territory conflicts, audit misrouted leads, or design capacity-aware lead assignment—even if they do not name the agent."
metadata:
  trigger_phrases:
    - "route MQL leads to reps"
    - "assign qualified leads"
    - "auto-assign inbound leads"
    - "balance lead distribution"
    - "route leads by territory"
  category: "Lead Management"
  phase: "day_1"
  data_readiness: "day_1"
  version: "1.1"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "LM-01 MQL Qualification Agent for qualified-lead scope"
    - "DQH-02 Field Normalization Engine for consistent territory and vertical values"
    - "LM-02 Lead-to-Account Matching Agent for account-owner continuity"
  mcps:
    - "Salesforce MCP or HubSpot MCP for live reads and approved owner updates"
    - "Snowflake MCP, Outreach, Salesloft, or Gong are optional capacity inputs"
  minimum_data:
    - "Qualified lead/contact ID, company, status, and current owner"
    - "Active owner IDs plus territory and availability"
    - "Territory policy or an approved round-robin pool"
  output_format: "markdown"
---

# LM-03 Lead Routing Agent

## Purpose

Assign qualified leads to an eligible owner without hiding uncertainty, inventing CRM state, or silently overwriting existing ownership. Preserve account continuity first, honor territory rules, avoid critically loaded or inactive reps, and make fallback routing reproducible.

The old research contains many exact labor, conversion, pricing, turnover, and revenue figures that current sources do not establish. Treat them as historical hypotheses only. Read `references/evidence_and_limits.md` before making any impact claim.

## Resource Routing

- Read `references/routing_rules.md` before changing thresholds, territory precedence, eligibility, round-robin, or escalation logic.
- Read `references/output_contract.md` before producing a batch report, review queue, or transaction receipt.
- Read `references/crm_write_safety.md` before any live owner update, rollback, or notification.
- Read `references/evidence_and_limits.md` before citing sources, promising outcomes, or setting KPI targets.
- Use `scripts/lead_router.py` for live scoring, boundary decisions, exact arithmetic, or batch ranking. A simple planning-only explanation may use the identical inline rules below.

## Non-Negotiable Safety Rules

1. Default to analysis-only. Never imply a CRM read or write occurred unless a tool receipt proves it.
2. Ask for explicit final confirmation after showing the proposed assignments and before changing any owner.
3. Never reassign an already-owned lead unless the approved scope explicitly allows reassignment.
4. Never auto-route to an inactive owner, excluded owner, territory conflict, invalid owner ID, or Critical-capacity rep.
5. Preserve the previous owner, timestamp, rule version, and reason for every proposed write so the batch can be rolled back.
6. Treat the confidence labels as routing-policy defaults, not statistical probabilities.
7. Do not use a rep's conversion rate to punish a lower performer with extra overloaded leads.

## Preflight

### 1. Verify Connection And Truthfulness

- Confirm Salesforce or HubSpot access if the request requires live records.
- State which objects, fields, timestamps, and permissions are verified.
- If access is absent, stay in analysis-only mode and request a CSV or structured sample.
- Do not claim LM-01, DQH-02, or LM-02 ran unless their current output is available.

### 2. Confirm Scope

Ask only what is still unknown:

- Which qualified leads are in scope: new/unowned only, a time window, a source, or an approved reassignment cohort?
- Is this analysis-only or a requested write run?
- Which reps, queues, territories, accounts, lead sources, or test records are excluded?
- Is account-owner continuity mandatory, preferred, or disabled by policy?
- What is the approved fallback pool and deterministic round-robin cursor?
- What response SLA should be recorded? Never present five minutes or one hour as universal compliance law.

### 3. Validate Minimum Data

Required for every lead:

- stable lead/contact ID;
- qualification state or explicit user-supplied inclusion;
- current owner state;
- company/account context when account continuity or territory routing is used.

Required for every candidate owner:

- stable CRM owner ID;
- active/inactive state;
- approved pool or territory membership;
- exclusion state;
- capacity inputs and freshness if capacity-aware routing is enabled.

Fail closed when there is no valid owner ID or no eligible fallback pool. Missing optional fields degrade the path; they do not justify invented values.

### 4. Assess Data Quality

Report, do not hide:

- percent of leads qualified, unowned, and account-matched;
- territory coverage and conflict count;
- active-owner coverage;
- capacity-input completeness and newest/oldest timestamps;
- fallback share expected from missing mappings.

Defaults from this skill are operating rules to validate with the customer:

- territory coverage below 60% triggers a degraded-routing warning;
- capacity inputs older than 7 days are stale and cannot drive unattended writes;
- combined territory and vertical coverage below 50% forces analysis-only mode;
- any account-territory conflict requires review.

### 5. Show The Contract

Before processing, summarize:

```text
Mode: ANALYSIS_ONLY | WRITE_REQUESTED
Scope: <filter and count>
Reassignment allowed: YES | NO
Account continuity: MANDATORY | PREFERRED | DISABLED
Territory policy: <version or supplied rule>
Fallback pool: <name and eligible count>
Capacity as of: <timestamp or NOT_AVAILABLE>
Exclusions: <list>
SLA target: <customer-approved target or NOT_SET>
```

Stop for clarification if scope, exclusions, or write intent would materially change the result.

## Deterministic Workflow

### Step 1: Build The Lead Cohort

- Select only records inside the approved filter.
- Exclude test, competitor, suppressed, duplicate, disqualified, or already-owned records unless explicitly included.
- Keep record IDs, not names, as write keys.
- Batch reads conservatively and record pagination completeness.

### Step 2: Resolve Account And Territory Context

Use this precedence:

1. Verified matched account and its active owner: `ACCOUNT_OWNER`, default confidence 95.
2. Verified account territory primary/secondary pool: `ACCOUNT_TERRITORY`, default confidence 90.
3. Fuzzy account match at Jaro-Winkler >= 0.85 plus matching city: `FUZZY_ACCOUNT_CITY`, default confidence 80.
4. Explicit geographic territory rule: `GEO`, default confidence 70.
5. Configured industry/vertical territory rule: `INDUSTRY`, default confidence 60.
6. Approved general pool: `ROUND_ROBIN`, default confidence 30.

These confidence values label rule strength; they are not measured probabilities. An ambiguous account match never outranks a verified account owner.

### Step 3: Create Eligible Owner Candidates

Remove any owner who is:

- inactive or archived;
- outside the approved pool or territory;
- explicitly excluded;
- missing a valid CRM owner ID;
- in a conflicting territory;
- Critical capacity at 100 or above.

When no owner remains, return `MANUAL_REVIEW`. Never route to the least-bad invalid candidate.

### Step 4: Calculate Capacity

When all three denominators are present and positive:

```text
opportunity_component = min(active_opportunities / average_active_opportunities, 1) * 50
pipeline_component    = min(pipeline_amount / rep_quota, 1) * 30
activity_component    = min(activities_7d / weekly_activity_target, 1) * 20
capacity_score        = opportunity_component + pipeline_component + activity_component
```

States have non-overlapping boundaries:

- Green: score < 50
- Yellow: 50 <= score < 85
- Red: 85 <= score < 100
- Critical: score >= 100

If a verified, fresh custom capacity score is the approved source of truth, use it instead and label the source. If inputs are missing or stale, set capacity to `UNKNOWN`; do not turn missing data into zero load.

Worked example:

```text
active opportunities: 6 / team average 12 = 25.0 points
pipeline: 300,000 / quota 600,000 = 15.0 points
activities: 20 / weekly target 40 = 10.0 points
capacity score = 50.0 -> Yellow
```

### Step 5: Rank Candidates

Rank eligible candidates by this tuple, in order:

1. verified existing account owner before every other candidate;
2. territory role: primary, then secondary, then general fallback;
3. capacity state: Green, Yellow, Red, Unknown;
4. exact vertical specialist before non-specialist within the same continuity, territory, and capacity tier;
5. deterministic round-robin position;
6. stable owner ID as the final tie-break.

Account continuity and territory correctness outrank specialty. Capacity breaks ties inside a valid ownership/territory path; it does not authorize cross-territory assignment.

### Step 6: Detect Conflicts

Add flags for:

- `ACCOUNT_TERRITORY_CONFLICT` — critical;
- `INACTIVE_OR_INVALID_OWNER` — critical;
- `CRITICAL_CAPACITY` — critical;
- `MULTIPLE_ACCOUNT_OWNERS` — critical;
- `DUPLICATE_OR_RECENT_SAME_COMPANY_LEAD` — review;
- `MULTI_THREADING_POLICY_CONFLICT` — review;
- `UNMAPPED_TERRITORY` — review;
- `STALE_CAPACITY` — review;
- `RED_CAPACITY` — caution.

Manual review is required for any critical flag or two or more review flags. One caution flag may proceed only inside an otherwise valid route and only under the approved mode.

### Step 7: Produce A Preview

For each lead show:

- current owner;
- proposed owner ID and display name;
- route type and policy confidence;
- territory and capacity source;
- capacity score/state or `UNKNOWN`;
- rationale and tie-breaks;
- conflicts and escalation state;
- exact fields that would change.

Also show batch totals, excluded counts, fallback share, manual-review count, and no-owner count. Use `references/output_contract.md` for the full format.

### Step 8: Confirm And Write

For analysis-only requests, stop after the preview.

For requested writes:

1. validate permissions and current owner values again;
2. show the final count and exact fields;
3. obtain explicit final confirmation;
4. write in a bounded batch;
5. verify every response;
6. stop on unexpected validation or permission errors;
7. produce transaction and rollback receipts.

Salesforce may use active assignment rules, direct owner changes, Flow, or queues depending on the approved design. HubSpot owner assignment uses an owner `id`, not a user ID. Read `references/crm_write_safety.md` before choosing a mechanism.

### Step 9: Record SLA And Audit Events

Record the customer-approved response target, but do not claim outreach occurred. LM-04 or another monitoring process must measure the first-contact event separately.

Every routing receipt must include:

```json
{
  "lead_id": "EXAMPLE_LEAD_ID",
  "previous_owner_id": null,
  "proposed_owner_id": "EXAMPLE_OWNER_ID",
  "route_type": "ACCOUNT_TERRITORY",
  "policy_confidence": 90,
  "capacity_score": 50.0,
  "capacity_state": "Yellow",
  "conflicts": [],
  "write_status": "NOT_ATTEMPTED",
  "rule_version": "1.1"
}
```

## Fallbacks

### No Live CRM Connection

State that live state is unverified. Accept CSV/JSON for analysis, return proposed assignments, and do not produce a success receipt.

### No Qualified Leads

Return zero results. Do not widen scope to all leads without approval.

### Low Territory Coverage

Quantify the unmapped share. Use the approved deterministic round-robin pool for analysis only; request approval before a write batch.

### Stale Capacity

Mark capacity `UNKNOWN` and rank through valid account/territory continuity. Do not claim an owner is underloaded.

### All Candidates Critical Or Invalid

Return `MANUAL_REVIEW` or an approved queue. Do not route to the rep with the lowest conversion rate and do not cycle through invalid owners.

### Concurrent Owner Change

If the current owner differs from the preview, skip that record and report `STALE_PREVIEW`. Never overwrite a concurrent change.

## Standard Response

```markdown
## Lead Routing Preview

**Mode:** ANALYSIS_ONLY
**Scope:** 25 new, unowned MQLs created after <timestamp>
**Verified systems:** Salesforce read access; write permission not tested
**Policy:** account continuity -> territory -> capacity -> specialty -> round-robin

### Result
- Ready to route: 20
- Manual review: 3
- No eligible owner: 1
- Excluded: 1
- Round-robin fallback: 4 of 25 (16%)

### Proposed Assignments
| Lead ID | Previous owner | Proposed owner | Route | Capacity | Flags | Write status |
|---|---|---|---|---|---|---|
| EXAMPLE_LEAD_ID | None | EXAMPLE_OWNER_ID | ACCOUNT_TERRITORY (90) | 50.0 Yellow | None | NOT_ATTEMPTED |

### Decision Needed
Review the three escalations. No CRM data has been changed.
```

## Quality Gate

Before presenting the result, verify:

- scope and mode are explicit;
- live facts are separated from assumptions;
- every proposed owner is active, valid, and eligible;
- capacity boundaries are applied exactly;
- account continuity and territory precedence are preserved;
- round-robin is deterministic and auditable;
- manual-review rules are applied;
- write status is truthful;
- prior owner IDs exist for rollback;
- no unsupported impact claim appears;
- totals reconcile to the input cohort.

Do not report completion until the preview, confirmation, write verification, and receipt states agree.

## Dependencies And Handoffs

- LM-01 supplies the qualified cohort. If absent, require explicit user-supplied scope.
- DQH-02 improves normalized territory and vertical values. Missing normalization must be disclosed.
- LM-02 supplies account matches and supports existing-account-owner continuity.
- LM-04 may monitor response SLAs after assignment; routing itself does not prove contact.
- Revenue and performance agents may consume receipts only after assignment status is verified.

## Limits

- Capacity score is a configurable workload proxy, not a measure of rep quality.
- Territory and confidence defaults require customer validation.
- CRM permissions, workflow side effects, queues, assignment rules, and custom fields vary by org.
- Salesforce and HubSpot ownership models differ; never translate IDs or write mechanisms by analogy.
- This skill does not qualify leads, deduplicate accounts, redesign territories, forecast revenue, or evaluate employee performance.
