---
name: revops-pipeline-health
description: "Audits open Salesforce opportunities or HubSpot deals for missing fields, overdue close dates, stale buyer activity, excessive time in stage, and pipeline-health risk while reporting evidence coverage separately from the score. Make sure to use this skill whenever the user asks which deals are stalled, whether pipeline is healthy, what revenue is at risk, why forecast data is unreliable, which opportunities need cleanup, or how to create rep and manager pipeline alerts—even if they do not name the agent."
metadata:
  trigger_phrases:
    - "show me stalled deals"
    - "audit pipeline health"
    - "find opportunities missing next steps"
    - "which deals are at risk"
    - "check pipeline hygiene and activity"
  category: "Sales Operations"
  phase: "day_1"
  data_readiness: "day_1"
  version: "1.1"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "No hard agent dependency"
    - "DQH-02 may normalize custom field values"
  mcps:
    - "Salesforce MCP or HubSpot MCP for live opportunity/deal reads"
    - "Gong MCP is optional and cannot replace missing CRM activity without an approved mapping"
    - "Slack or email connector is optional and requires approval before sending"
  minimum_data:
    - "Open opportunity/deal ID, stage, amount, close date, owner, and next step"
    - "Buyer-activity timestamp or explicit activity-unavailable state"
    - "Stage-entry timestamp and customer-approved expected duration for stage-age scoring"
  output_format: "markdown"
---

# PM-01 Pipeline Health Monitoring Agent

## Purpose

Produce an evidence-backed view of open pipeline health without presenting missing telemetry as a healthy deal, confusing CRM edits with buyer activity, or turning gross at-risk pipeline into forecast loss.

The legacy research contains unsupported exact claims about forecast variance, labor, tool pricing, zombie-deal rates, and revenue impact. Treat them as hypotheses only. Read `references/evidence_and_limits.md` before citing an impact figure or proposing a target.

## Resource Routing

- Read `references/health_rules.md` before changing required fields, activity bands, stall thresholds, score weights, or status boundaries.
- Read `references/output_contract.md` before producing the full deal table, manager digest, JSON receipt, or reconciliation.
- Read `references/alert_and_write_safety.md` before sending a rep alert, posting to Slack, editing CRM fields, or scheduling a recurring run.
- Read `references/evidence_and_limits.md` before citing benchmarks, describing vendor behavior, or estimating forecast impact.
- Use `scripts/pipeline_health.py` for exact scoring, stall classification, boundary decisions, or batch validation. Simple planning-only explanations may use the identical inline rules.

## Safety And Honesty

1. Default to read-only analysis. Never imply a CRM query, alert, field update, or schedule occurred without a tool receipt.
2. Ask for explicit approval before sending alerts or changing any external system.
3. Keep pipeline amount, weighted forecast, and booked revenue separate. “At-risk pipeline” is not “revenue lost.”
4. Report evidence coverage beside every health score. A low-coverage deal is `UNKNOWN`, not Green.
5. Use buyer-facing activity when possible. Do not substitute `LastModifiedDate`; admin edits and automation are not buyer engagement.
6. Do not invent standard custom fields such as budget confirmation or decision maker. Inspect the schema and map them explicitly.
7. Do not use DQH-04 as a source of stage-velocity benchmarks; it measures CRM data health, not rep stage history.

## Preflight

### 1. Verify Access And Mode

- Confirm Salesforce or HubSpot access only when live records are requested.
- State which objects, fields, time zones, activity sources, and permissions are verified.
- If access is absent, accept CSV/JSON and remain analysis-only.
- Separate `READ_ONLY`, `ALERT_REQUESTED`, and `WRITE_REQUESTED` modes.

### 2. Confirm Scope

Ask only what is unknown:

- Which open pipelines, teams, owners, currencies, regions, record types, and close-date windows are included?
- Which stages are open, won, lost, omitted, or held in this org?
- Which accounts, internal tests, renewals, or zero-dollar deals are excluded?
- Is the user asking for a one-time audit, approved alerts, or an external schedule?
- What “as of” time and timezone govern day counts?

Audit every in-scope open deal. Do not silently exclude newly created deals or deals younger than 90 days. A seven-day grace period may suppress a stall flag, but the deal still belongs in the cohort.

### 3. Map Fields

Map and verify:

- stable deal/opportunity ID;
- open/closed state and stage;
- amount and currency;
- close date;
- next step;
- owner ID;
- created timestamp;
- latest qualifying buyer-activity timestamp;
- stage-entry timestamp or Days In Stage;
- optional customer-approved budget, stakeholder, push-count, or methodology fields.

For HubSpot and Salesforce, field names and available activity sources differ. Never translate names by analogy.

### 4. Configure Rules

Confirm the customer's stage taxonomy and expected duration per stage. When no policy is supplied, present these legacy defaults for approval rather than calling them universal benchmarks:

| Normalized stage | Stall threshold |
|---|---:|
| Prospecting | 30 days |
| Qualification | 30 days |
| Proposal | 21 days |
| Negotiation | 21 days |
| Pending Signature | 14 days |

Also confirm:

- newly created deal grace period: default 7 days;
- Green/Yellow/Red score boundaries: default `>=60`, `40–<60`, `<40`;
- minimum evidence coverage for a classified score: default 80%;
- required-field mappings and placeholder values;
- alert recipients and delivery approval.

### 5. Report Data Readiness

Show:

- field availability and value completeness separately;
- activity-source coverage and freshness;
- stage-age availability;
- currency consistency;
- invalid stage and overdue-close-date counts;
- percentage of deals expected to receive `UNKNOWN` status.

If the cohort cannot reconcile, IDs are unstable, or open/closed stages are unmapped, stop and request correction.

## Deterministic Workflow

### Step 1: Build The Open Cohort

- Query every in-scope record mapped to an open stage.
- Exclude closed-won, closed-lost, omitted, held, test, or other approved exclusions.
- Preserve zero-dollar deals when the customer uses them; flag amount validity instead of silently dropping them.
- Record pagination, source timestamp, currency, and filter completeness.

### Step 2: Validate Core Fields

Score four core fields at ten points each when the field exists in the schema:

- `stage`: valid open-stage mapping;
- `amount`: present and valid under the customer's amount policy;
- `close_date`: present and not overdue for an open deal;
- `next_step`: nonempty and not a configured placeholder such as `TBD`, `None`, or `N/A`.

Each valid value earns 10 points. An available but invalid/missing value earns 0 and a flag. A field absent from the schema reduces evidence coverage by 10 rather than pretending the value failed.

Common flags:

- `MISSING_OR_INVALID_STAGE`
- `MISSING_OR_INVALID_AMOUNT`
- `MISSING_CLOSE_DATE`
- `OVERDUE_CLOSE_DATE`
- `MISSING_OR_PLACEHOLDER_NEXT_STEP`
- `CLOSE_DATE_OUTLIER` under an approved horizon

Optional budget/stakeholder fields create separate flags only when mapped and required by customer policy. They do not silently change the default score.

### Step 3: Measure Activity Recency

Use the latest qualifying buyer-facing call, email, or meeting timestamp. Include tasks only when the customer explicitly treats completed tasks as engagement evidence.

Activity points, maximum 30:

- fewer than 7 full days: 30;
- 7 through 13 days: 22;
- 14 through 20 days: 14;
- 21 through 29 days: 7;
- 30 days or more: 0.

If the activity source is connected but no qualifying history exists, score 0 and flag `NO_BUYER_ACTIVITY_HISTORY`. If activity data is unavailable, remove these 30 points from evidence coverage and flag `ACTIVITY_DATA_UNAVAILABLE`.

Never use record modification time as a fallback for engagement. For a deal with no activity history, created age may determine whether the grace period has ended, but the source must remain `created_age_no_activity`.

### Step 4: Measure Stage Age

Stage-age points, maximum 30, require a stage-entry timestamp and a positive customer-approved expected duration:

```text
stage_ratio = days_in_stage / expected_stage_days
```

- ratio <= 0.50: 30;
- ratio <= 1.00: 20;
- ratio <= 1.50: 10;
- ratio > 1.50: 0.

If either input is unavailable, remove these 30 points from evidence coverage and flag `STAGE_AGE_UNAVAILABLE`. Do not import a fictional benchmark from DQH-04.

### Step 5: Calculate Health And Coverage

```text
raw_points = field_points + activity_points + stage_age_points
evidence_coverage = available_max_points
health_score = raw_points / evidence_coverage * 100
```

Round the score to one decimal. Classify only when evidence coverage is at least 80:

- Green: score >= 60;
- Yellow: 40 <= score < 60;
- Red: score < 40;
- Unknown: evidence coverage < 80.

Worked example with full coverage:

```text
fields: stage, amount, close date valid; next step missing = 30/40
activity: 16 days since buyer activity = 14/30
stage age: 24 days / 30 expected = ratio 0.80 = 20/30
raw = 64; coverage = 100; score = 64.0 -> Green
flags = [MISSING_OR_PLACEHOLDER_NEXT_STEP]
```

Green means the configured score cleared its threshold; it does not erase flags. Always show score, coverage, component points, and flags together.

### Step 6: Detect Stalls

After the newly created grace period:

- a deal is stalled when days since qualifying activity are greater than or equal to its configured stage threshold;
- a connected activity source with no history uses deal age for the threshold and carries `NO_BUYER_ACTIVITY_HISTORY`;
- 30 or more days without qualifying activity is Critical under the legacy default;
- Pending Signature at its threshold is Critical;
- other threshold crossings are Alert.

Do not calculate a stall state when activity data itself is unavailable. Return `STALL_UNKNOWN`.

### Step 7: Aggregate Without Overclaiming

Report:

- audited deal count and amount;
- Green, Yellow, Red, and Unknown count/amount;
- stalled and overdue count/amount;
- missing-field counts;
- fallback/unknown-data counts;
- unique currencies or the conversion policy used.

“At-risk amount” is the gross amount on flagged deals. Do not convert it to forecast loss, apply an arbitrary 50% probability, or call it revenue impact without an approved forecast model.

### Step 8: Produce Recommendations

Sort action priority by:

1. Critical data or stall flags;
2. overdue close date;
3. Red status;
4. Yellow status;
5. Unknown status with high amount;
6. amount descending only within the same severity and currency.

Recommendations should name the evidence gap or buyer action required. Do not tell reps to fabricate field values to improve a score.

### Step 9: Alert Or Write Only After Approval

For read-only requests, stop after the report.

For alerts or writes:

1. show exact recipients, channels, counts, records, and message samples;
2. re-read live state to prevent stale alerts;
3. obtain explicit final confirmation;
4. send or write in a bounded batch;
5. verify every response and produce receipts;
6. stop on permission, validation, or unexpected automation errors.

Read `references/alert_and_write_safety.md` first.

## Standard Output

```markdown
## Pipeline Health Audit

**Mode:** READ_ONLY
**As of:** <timestamp and timezone>
**Scope:** <pipeline, owners, stages, close-date window>
**Source truth:** <verified CRM fields and activity source>

### Reconciliation
- Input records: 145
- Open and in scope: 140
- Excluded: 5
- Classified: 126
- Unknown: 14

### Health Summary
| Status | Deals | Gross amount | Meaning |
|---|---:|---:|---|
| Green | 80 | <amount> | Score >=60 with coverage >=80 |
| Yellow | 28 | <amount> | Score 40–<60 with coverage >=80 |
| Red | 18 | <amount> | Score <40 with coverage >=80 |
| Unknown | 14 | <amount> | Evidence coverage <80 |

### Priority Deals
| Deal ID | Owner | Stage | Score | Coverage | Stall | Flags | Gross amount |
|---|---|---|---:|---:|---|---|---:|
| EXAMPLE_DEAL | EXAMPLE_OWNER | Negotiation | 64.0 Green | 100 | No | Missing next step | 100,000 USD |

### Limits
- Gross flagged amount is not forecast loss.
- No alerts were sent and no CRM fields were changed.
```

Use `references/output_contract.md` for full JSON and reconciliation rules.

## Failure Modes

### No Live Connection

State that live pipeline is unverified, accept a structured export, and return analysis only.

### Activity Data Unavailable

Return `STALL_UNKNOWN`, reduce coverage by 30, and avoid claims about buyer inactivity.

### Stage Age Unavailable

Reduce coverage by 30. Do not use opportunity creation age as time in the current stage.

### Multiple Currencies

Group amounts by currency unless an approved dated conversion table exists. Never sum unlike currencies.

### Empty Cohort

Return zero open deals for the exact filter. Do not widen the query silently.

### Partial Pagination Or API Error

Mark the run incomplete, show fetched versus expected counts, and do not publish a complete manager digest.

### Stale Preview Before Alert

Skip changed records and report `STALE_PREVIEW`. Never send a now-incorrect alert as if current.

## Quality Gate

Before presenting the audit, verify:

- scope, timezone, and as-of time are explicit;
- open/closed stage mapping is verified;
- buyer activity is not record modification time;
- score and evidence coverage use exact boundaries;
- missing telemetry yields Unknown when coverage is below 80;
- stall grace and threshold boundaries are exact;
- optional fields do not silently alter the default score;
- counts reconcile;
- currencies are not improperly summed;
- gross pipeline is not labeled forecast loss;
- alert/write status is truthful;
- unsupported benchmarks are absent.

Do not report completion until these checks pass.

## Dependencies And Limits

- PM-01 has no hard agent dependency.
- DQH-02 may normalize custom values but must not invent missing commercial facts.
- DQH-04 does not provide stage-velocity benchmarks.
- Salesforce Pipeline Inspection and HubSpot deal tooling may expose different fields and scores; this skill's score is a transparent policy score, not a vendor-native prediction.
- The skill does not predict win probability, edit forecast categories, close deals, coach employee performance, or schedule recurring work without separate approval.
