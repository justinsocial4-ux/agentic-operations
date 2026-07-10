---
name: revops-weekly-revenue-narrative
description: "Creates a plain-English weekly revenue update from Salesforce or HubSpot snapshots, showing closed-won and closed-lost results, active pipeline changes, evidence-backed deal risks, close-date slips, and data limitations. Make sure to use this skill whenever the user asks for a weekly revenue update, Monday pipeline summary, executive sales narrative, week-over-week pipeline report, risky-deal digest, forecast-change explanation, or a Slack-ready revenue recap—even if they do not name the agent."
metadata:
  category: "Reporting & Analytics"
  phase: "day_1"
  data_readiness: "30_days"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies: []
  mcps:
    - "Salesforce MCP or HubSpot MCP for CRM reads"
    - "Slack MCP for approved Slack delivery"
    - "Email integration for approved email delivery"
  minimum_data:
    - "Current and prior opportunity/deal snapshots"
    - "Amount, stage, close date, created date, owner, closed status, won status"
    - "Stage-entry and activity timestamps for risk scoring"
---

# Weekly Revenue Narrative

Turn CRM evidence into a short weekly update that leaders can verify. Keep the run read-only. Calculate first, cite the underlying fields, draft the narrative, validate every number, and deliver only to an approved destination.

## Use the Bundled Resources

- Read `references/data_contract.md` before querying a CRM or accepting an export. It defines required snapshots, fields, evidence states, and platform notes.
- Read `references/metric_rules.md` when calculating weekly metrics, deltas, risk, slips, velocity, or forecast accuracy.
- Read `references/stage_mapping.md` when mapping customer stages. Never guess an unknown mapping.
- Read `references/narrative_template.md` when drafting or validating the final report.
- Read `references/research_and_claims.md` before repeating market benchmarks or outcome claims.
- Use `scripts/weekly_revenue.py` for live calculations, exact arithmetic, or detailed QA. Use the identical inline rules below for a simple no-tools explanation.

## Operating Rules

1. Read CRM data; do not modify opportunities, owners, stages, close dates, amounts, or activities.
2. Treat a manual run as preview-only unless the user explicitly asks to send it.
3. Treat an enabled schedule plus approved recipients as standing delivery approval for that schedule only.
4. Do not call `LastModifiedDate` buyer activity. Require an activity timestamp or report silence risk as unknown.
5. Require stage history for days-in-stage and prior snapshots or field history for close-date slips.
6. Keep closed-lost amount separate from churn. Closed-lost pipeline is not customer churn.
7. Show `unknown` instead of converting missing evidence to zero.
8. Label risk thresholds as customer-tunable operating defaults, not industry facts.

## Preflight

### 1. Confirm the request

Ask or infer, then show:

- reporting timezone and current weekly window;
- CRM and pipeline(s) in scope;
- amount meaning: ARR, ACV, TCV, or untyped CRM amount;
- currency and whether mixed currencies exist;
- stage mapping version;
- preview-only or approved delivery destination;
- exclusions such as test deals, renewals, partner deals, or specific pipelines.

Default the completed week to Monday 00:00 through the next Monday 00:00 in the approved business timezone. Include the lower bound and exclude the upper bound so a boundary record is counted once.

### 2. Verify connection and scope

- If Salesforce or HubSpot is connected, request only the fields in `references/data_contract.md` and paginate within live limits.
- If no CRM is connected, accept a supplied CSV/JSON snapshot for offline analysis.
- If neither a connection nor supplied records exists, return the missing-data checklist and stop. Do not invent a report.

### 3. Check completeness

Calculate completeness for amount, stage, close date, owner, closed/won state, stage-entry timestamp, and last-activity timestamp.

- If amount, stage, close date, or closed/won state is below 50% complete, stop the affected metric and explain the repair.
- If active opportunities are below 10, continue but label the cohort small.
- If fewer than four completed historical weeks exist, omit trend claims.
- If stage-entry or activity evidence is missing, continue with aggregate metrics but mark the affected risk component unknown.
- If currencies are mixed without conversion rates, report separate currency totals; never sum them.

Return a preflight receipt with status `GO`, `DEGRADED`, or `NO_GO`, plus enabled and disabled analyses.

## Workflow

### Step 1: Retrieve two comparable snapshots

Collect:

- current opportunity/deal state;
- the prior comparable weekly snapshot;
- completed outcomes in the current and prior weekly windows;
- stage history and activity history when risk analysis is requested;
- prior close dates when slip detection is requested.

Do not reconstruct a prior snapshot from current values. If historical state is unavailable, say week-over-week movement is unknown.

### Step 2: Normalize without hiding source values

- Preserve record ID, source system, pipeline ID, original stage, currency, and source timestamps.
- Map stages only through an approved exact mapping from `references/stage_mapping.md`.
- Keep unmapped stages under their original names and list them as unresolved.
- Use explicit `is_closed` and `is_won` evidence instead of deciding outcomes from names alone.

### Step 3: Calculate the weekly metrics

Use `scripts/weekly_revenue.py` and retain its calculation receipt.

For the current weekly window:

- `closed_won_count` and `closed_won_amount`: records closed and won in the window;
- `closed_lost_count` and `closed_lost_amount`: records closed and not won in the window;
- `win_rate`: won count divided by won plus lost count;
- `open_pipeline_count` and `open_pipeline_amount`: records not closed at snapshot time;
- `new_deal_count` and `new_deal_amount`: records created in the window;
- stage and owner breakdowns when evidence is complete.

For deltas:

- use `(current - prior) / prior × 100` when the prior value is nonzero;
- show `NEW` when prior is zero and current is positive;
- show `UNCHANGED_ZERO` when both are zero;
- do not emit infinity or a fabricated percentage.

### Step 4: Detect risks from available evidence

Use customer-approved thresholds or these clearly labeled defaults:

- stall input: days in current stage divided by the historical median for the same mapped stage;
- stall score: clamp `(multiplier - 1) / 2` to 0–1;
- silence score: 0 below 7 days, then clamp `(days - 6) / 14` to 0–1;
- composite: stall × 0.60 plus silence × 0.40;
- High: at least 0.70; Medium: at least 0.40; Low: below 0.40.

Calculate the composite only when both stage-entry and activity evidence exist. Otherwise return `UNKNOWN` with the missing component. Still show an independently supported stall or silence observation, but do not present a partial composite as complete.

Flag a close-date slip when a prior and current date exist and the current date moved later. Mark more than 7 days as the default urgent threshold. Require at least eight completed baseline weeks for the default velocity signal; otherwise return `INSUFFICIENT_HISTORY`.

### Step 5: Draft the narrative

Follow `references/narrative_template.md`. Lead with what changed, then what needs attention. Distinguish facts, risk heuristics, and unknowns.

For every named risky deal, include:

- deal name or safe identifier;
- amount and currency;
- current stage;
- exact evidence used;
- risk result or unknown state;
- a proposed human follow-up, not an automatic CRM action.

### Step 6: Validate before delivery

Fail the report if any validation check fails:

- section totals reconcile to the calculation receipt;
- won plus lost count equals the win-rate denominator;
- active pipeline excludes closed records;
- all percentages have valid denominators;
- all week-over-week comparisons use comparable scopes and currencies;
- every deal claim maps to a source record and timestamp;
- unknown evidence remains unknown;
- the report contains no unsupported benchmark or causal claim.

Show a preview and validation receipt. Send only after explicit approval or under an already approved schedule and recipient list. Record delivery status without exposing secrets.

## Failure and Degradation Paths

| Condition | Response |
|---|---|
| CRM unavailable | Offer offline CSV/JSON analysis or connection troubleshooting; do not use stale cached data silently. |
| Required metric evidence below 50% | Disable that metric or stop if it affects the headline; show missing fields and counts. |
| Prior snapshot missing | Report current snapshot only; week-over-week change is unknown. |
| Stage history missing | Disable stall score; do not use created or modified date as a substitute. |
| Activity history missing | Disable silence score; do not use record modification as buyer activity. |
| Mixed currencies | Split totals by currency unless approved conversion rates and dates are supplied. |
| No closed deals | Show zero closes and an undefined win rate; focus on active pipeline without calling the week a failure. |
| More than 30% flagged | Show the top 10 by deterministic score and warn that thresholds or data quality need review. |
| Slack/email unavailable | Save the validated preview and report delivery failure; do not claim it was sent. |

## Output Contract

Return:

1. `Preflight receipt` — scope, timezone, data sources, completeness, enabled/disabled analyses.
2. `Calculation receipt` — exact inputs, formulas, totals, deltas, risk evidence, unknown states.
3. `Weekly narrative` — concise markdown using the bundled template.
4. `Validation receipt` — reconciliation and source-trace checks.
5. `Delivery receipt` — preview-only, sent, or failed; channel and timestamp; no credentials.

## Worked Example

**Request:** “Give me a weekly revenue update from this fictional export. Do not send it.”

**Evidence:** Current week has two won deals worth $120,000 and one lost deal worth $30,000. Prior week had $100,000 won. Open pipeline is $500,000 across five deals. One $80,000 deal has been in stage 30 days versus a 10-day historical median and has 20 days since activity.

**Deterministic result:**

- Win rate: `2 / (2 + 1) = 66.67%`.
- Closed-won amount delta: `(120,000 - 100,000) / 100,000 = +20%`.
- Stall multiplier: `30 / 10 = 3.0`; stall score `1.0`.
- Silence score: `(20 - 6) / 14 = 1.0`.
- Composite risk: `1.0 × 0.60 + 1.0 × 0.40 = 1.0`, High.
- Delivery: preview only; nothing sent and no CRM data changed.

**Narrative excerpt:**

> Closed-won amount rose 20% to $120,000 on two wins. Open pipeline is $500,000 across five deals. One $80,000 deal needs review: it has spent three times the historical median in stage and has no recorded activity for 20 days. This is a rules-based High risk flag, not a prediction.

## Verification Checklist

- [ ] Scope, timezone, currency, and amount meaning are explicit.
- [ ] Current and prior values come from comparable snapshots.
- [ ] Stage and activity history are real evidence, not proxies.
- [ ] Calculation and narrative totals reconcile.
- [ ] Unknowns remain visible.
- [ ] Risk thresholds are labeled customer-tunable defaults.
- [ ] Every named deal is source-traceable.
- [ ] No external delivery occurs without approval.
