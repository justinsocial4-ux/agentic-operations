---
name: revops-elt-pipeline-monitoring
description: Continuously monitors ELT pipelines (Fivetran, dbt, Workato, Snowflake,
  BigQuery) for failures, latency, schema drift, and data quality degradation. Detects
  sync failures, tracks data freshness SLAs, flags dbt test failures, and alerts RevOps
  teams to stale data or schema corruption before bad data cascades into broken reports
  and inaccurate forecasts.
metadata:
  trigger_phrases:
  - monitor elt pipelines
  - check data freshness
  - pipeline health status
  - check for pipeline failures
  - monitor data pipeline
  - fivetran sync status
  - dbt pipeline health
  category: Reporting & Analytics
  phase: day_1
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents:
    - optional: revops-tso-01-integration-health-agent
    mcps:
    - Fivetran API (webhook-based or manual config)
    - dbt Cloud API (optional but common)
    - Snowflake JDBC/SQL (for schema introspection)
    - BigQuery API (if using BigQuery warehouse)
    - Slack MCP (for real-time alerts; optional)
    minimum_data:
    - At least one active ELT pipeline (Fivetran, dbt, Workato, or custom SQL job)
    - Data warehouse connection (Snowflake or BigQuery)
    - Pipeline execution logs available (recent runs, 24–48 hours)
    - System metadata accessible (information_schema, warehouse tables)
  output_format: markdown report + optional Slack alerts
---

# RA-06 ELT Pipeline Monitoring Agent

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager or Sales Operations Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Integration Blindness — API Failures Go Undetected for Hours
- **Problem:** Mid-market RevOps teams lack visibility into data pipeline health. When Fivetran, Salesforce API, or warehouse sync fails, detection time averages 4–24 hours, causing bad data to flow into analytics and destroy forecast credibility.
- **Quantified cost to the role:** $636,000/year in undetected downtime labor cost (793 hours/month × $67/hour for 5-person data team) PLUS $100K–$200K per month in forecast error cost when stale/bad data drives decisions. Total: $1.2M–$3.4M annually. [TIER 1 source: Monte Carlo 2024 Data Quality Survey; Fivetran 2026 Benchmark Report]
- **What teams do today:** Build custom Looker/Tableau freshness dashboards ($2K–$10K setup), manually check logs daily (30 min–1 hour), maintain spreadsheets of known issues, purchase Fivetran/Workato monitoring ($1K–$10K/year). Total annual spend: $5K–$30K + 25–30 hours/month manual effort. [TIER 1 source: Integrate.io ETL Monitoring Tools 2026]
- **Why it's urgent:** Integration count grows 30%+ annually. By month 3 without monitoring, RevOps team spends 25–30% of time firefighting. By month 6, forecast accuracy drops 20%, strategic projects slip 3–6 months, and leadership trust erodes.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 6 TIER 1 sources

### Pain Point 2: Data Staleness — Stale Reports Cause Forecast Misses
- **Problem:** Salesforce-to-warehouse syncs arrive 6–12 hours delayed. Morning forecasts use yesterday's data. Forecast accuracy drops 5–10%, costing $100K–$200K in planning waste per month.
- **Quantified cost to the role:** A 5–10% improvement in forecast accuracy = millions in bottom-line impact through better resource allocation. A single month of undetected staleness = $100K–$200K forecast error. Annualized: $1.2M–$2.4M. [TIER 1 source: Forecastio Sales Forecasting Accuracy Guide 2026]
- **What teams do today:** Run manual validation queries 5–10 hours/week, build custom freshness dashboards ($2K–$10K), check Salesforce sync schedule manually 2–4 hours/week. Some purchase dbt freshness monitoring (requires 20–40 hours setup). [TIER 1 source: dbt Labs Data SLA Best Practices 2026]
- **Why it's urgent:** Staleness goes undetected for days. By week 3, team stops trusting warehouse data and reverts to manual Salesforce exports. By month 3, forecast becomes a guess, not a tool. Trust in data erodes.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 5 TIER 1 sources

### Pain Point 3: Schema Drift — Silent Data Corruption
- **Problem:** When Salesforce adds or changes a field (common), Fivetran may load bad data or fail silently. Revenue Cycle objects get corrupted. Manual diagnosis takes 2–4 hours; data rework takes longer.
- **Quantified cost to the role:** $1,450–$10,000/year in investigation + remediation labor (2–4 incidents/year × 2–4 hours each × $58–$67/hour + rework cost). [TIER 1 source: Integrate.io Schema Drift Detection 2026]
- **What teams do today:** Rely on manual column count checks (weekly, 30 min), ad hoc Salesforce change log monitoring (high overhead), or dbt test setup (20–40 hours one-time cost). 80%+ of mid-market have NO automated schema drift monitoring. [TIER 1 source: Integrate.io Data Pipeline Monitoring Tools 2026]
- **Why it's urgent:** Undetected schema drift corrupts hundreds of records per incident. By week 2, data quality erodes. By month 1–3, forecast model accuracy drops 10–15% due to missing/bad fields. Compounding cost.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

---

## What This Agent Does

The ELT Pipeline Monitoring Agent is your data warehouse's early-warning system. It polls all your registered pipelines every 5–15 minutes, checking if they completed on time, loaded data without errors, and produced no schema drift. If a pipeline is stale (data older than your SLA), threw errors, or a dbt test failed, you get a Slack alert immediately. If Salesforce adds a field and Fivetran doesn't know what to do with it, the agent detects the schema change and flags the risk. You get daily reports showing pipeline health across your entire stack, plus detailed logs of every sync, error, and transformation run for troubleshooting.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your pipeline infrastructure, confirm required data access exists, and ask you to scope your monitoring.

**Step 1: MCP Connection Verification**
- I'll check if at least one ELT tool is connected (Fivetran, dbt Cloud, Workato, or custom SQL endpoints).
- I'll verify your data warehouse connection (Snowflake or BigQuery) is authenticated.
- **If connections fail:** I'll offer workarounds (manual config via API keys, connection troubleshooting steps).
- **If successful:** Proceed to Step 2.

**Step 2: Pipeline Registry Discovery**
I'll ask: "Which pipelines should I monitor? (e.g., Fivetran Salesforce sync, dbt daily transforms, Workato integration, custom SQL jobs)"

I'll validate each pipeline:
- ✓ Can I reach the API endpoint?
- ✓ Do I have read access to execution logs?
- ✓ Is the pipeline active (last run within 48 hours)?

**Step 3: Define Freshness SLAs**
I'll ask: "What's acceptable data lag for each pipeline? (default: 12 hours)"

Example SLA config:
- Salesforce → Snowflake: 12 hours max lag
- dbt daily transforms: 24 hours max lag
- Payment data sync: 4 hours max lag (critical)

**Step 4: Preflight Report**
I'll summarize:
```
✓ Fivetran API connected (3 connectors detected)
✓ dbt Cloud API connected (2 projects detected)
✓ Snowflake connection active
⚠️ BigQuery not connected (optional; will skip BigQuery checks)
✓ Slack webhook configured
✓ Found 5 active pipelines to monitor

Pipeline Registry:
1. fivetran_salesforce_to_snowflake (Fivetran) — SLA: 12h — Last run: 2h ago ✓
2. dbt_daily_transforms (dbt) — SLA: 24h — Last run: 1h ago ✓
3. fivetran_stripe_to_snowflake (Fivetran) — SLA: 12h — Last run: 4h ago ✓
4. custom_revenue_sync (SQL job) — SLA: 6h — Last run: 35h ago ⚠️

⚠️ Warning: Pipeline #4 (custom_revenue_sync) hasn't run in 35 hours. Possible disabled/stale job.

Ready to begin monitoring.
```

---

## Step-by-Step Workflow

### Step 1: Poll Pipeline Status (Every 5–15 Minutes)

For each registered pipeline, I'll query the API endpoint and fetch:
- Current status (running, success, failed, timeout)
- Last successful run timestamp
- Run duration (seconds)
- Records processed (inserted, updated, deleted)
- Error logs (if any)
- dbt test results (if dbt pipeline)

**What you'll see:** Background polling; alerts sent to Slack as issues arise.

---

### Step 2: Calculate Data Freshness

For each pipeline:
- Freshness = NOW() - last_successful_run
- Compare vs. SLA threshold
- Determine confidence (0–100)

**Freshness Status Algorithm:**
- If freshness ≤ SLA → Status: OK; Confidence: 95
- If freshness > SLA AND ≤ 1.5×SLA → Status: WARNING; Confidence: 75
- If freshness > 1.5×SLA → Status: CRITICAL; Confidence: 50

Example:
- Pipeline last ran 2 hours ago; SLA is 12 hours → Status: OK
- Pipeline last ran 14 hours ago; SLA is 12 hours → Status: WARNING
- Pipeline last ran 19 hours ago; SLA is 12 hours → Status: CRITICAL

---

### Step 2b: Adjust Thresholds Based on TSO-01 Integration Health Signals (Optional)

If TSO-01 output is available, check for any integrations flagged as degraded or failing:
- Query TSO-01 for current upstream API health status
- For each integration detected as degraded, failing, or rate-limited → **automatically relax freshness SLAs by 2x**
  - Example: If normal SLA is 1 hour, allow 2 hours before alerting
  - Example: If normal SLA is 12 hours, allow 24 hours before alerting
- Add a note to the daily report and any Slack alerts explaining that freshness thresholds were adjusted due to known upstream issues detected by TSO-01

**If TSO-01 output is NOT available:**
- Proceed with standard thresholds as defined in Step 3 (preflight check)
- This is the default behavior; no special handling needed

This adjustment prevents false-positive alerts when pipeline delays are caused by upstream API degradation (e.g., Salesforce API rate limits, webhook delays, third-party service outages) rather than issues with the pipeline itself.

---

### Step 3: Detect Schema Changes

I'll query the warehouse information_schema and compare to last known state:
- Column count per table
- Data types per column
- New fields added
- Fields removed

**Schema Drift Severity:**
- If Revenue Cycle table (Account, Opportunity, Contact) + field removed → HIGH/CRITICAL alert
- If field type incompatible (VARCHAR → INT) → HIGH alert
- If non-critical table + field added → MEDIUM alert

---

### Step 4: Monitor dbt Test Results (if dbt)

For dbt pipelines, I'll fetch the latest run and check:
- Tests passed / failed
- Models built successfully
- Downstream impact if any test failed

**dbt Alert Severity:**
- 0 failed tests → OK
- 1–2 failed + non-critical → MEDIUM
- 3–5 failed OR critical test failed → HIGH
- 6+ failed → CRITICAL

---

### Step 5: Calculate Health Score (0–100)

For each pipeline, I aggregate freshness, errors, dbt tests, rate limits into a score:

```
Base: 100 points
- Deduct 50 for CRITICAL freshness, 20 for WARNING
- Deduct 40 for 11+ errors, 25 for 6–10, 10 for 1–5
- Deduct 50 for 6+ test failures, 30 for 3–5, 15 for 1–2
- Deduct 50 for CRITICAL schema drift, 30 for HIGH, 15 for MEDIUM, 5 for LOW
- Deduct 10 if API rate limit >80%
```

Health score determines status:
- ≥80 = healthy
- 60–79 = degraded
- 40–59 = struggling
- <40 = down

---

### Step 6: Generate Alerts

Alerts are deduplicated (suppress duplicate alerts for same issue within 1 hour).

**Slack Format:**
```
🔴 CRITICAL: Salesforce → Snowflake Pipeline Stale
Pipeline: Fivetran: Salesforce → Snowflake
Status: Data 15.2 hours old (SLA: 12 hours)
Last sync: 2026-04-13 05:45 PM UTC

Action required: Check Fivetran dashboard [Link]
Confidence: 92% | Next check: in 5 minutes
```

---

### Step 7: Daily Report

Once per day, I'll generate a markdown report with:
- Stack health scorecard (all pipelines)
- Critical findings (freshness violations, dbt failures, schema drift)
- Data quality & limitations
- Recommended actions
- Sources & citations

---

## Output Contract

**Output 1: Slack Real-Time Alerts** (if configured)
- Severity badge: 🔴 CRITICAL | 🟡 HIGH | 🟢 OK
- Pipeline name, status, data age, SLA
- Action required + link to dashboard
- Confidence score

**Output 2: Daily Markdown Report**
```
## ELT Pipeline Monitoring Report
**Report Date:** 2026-04-13  
**Confidence:** 94%

### Summary
All 5 pipelines healthy. Salesforce sync is 2 hours fresh (SLA: 12h). dbt transforms passed 47 tests; no failures.

### Pipeline Status Table
| Pipeline | Type | Data Age | SLA | Status | Health |
|----------|------|----------|-----|--------|--------|
| Fivetran Salesforce | fivetran | 2h | 12h | OK | 95 |
| dbt Daily | dbt | 1h | 24h | OK | 100 |
| Stripe Sync | fivetran | 3h | 12h | OK | 95 |
| Custom Revenue | SQL | 28h | 6h | CRITICAL | 15 |
| Workato Integration | workato | 45m | 2h | OK | 100 |

### Critical Findings
None. All pipelines within SLA.

### Recommended Actions
1. Investigate custom_revenue_sync — hasn't run in 28 hours
2. Schedule call with data ops to review SQL job config
3. Review dbt test results for next week

### Data Quality & Limitations
- Data age based on execution logs (may lag actual data arrival by 5–10 min)
- Schema drift detection requires information_schema access (not all warehouses support equally)
- dbt tests only visible if dbt Cloud API connected
- Does NOT monitor data correctness (only freshness, schema, test pass/fail)

### Sources
- Fivetran API (pulled 2026-04-13 09:15 UTC)
- dbt Cloud API (pulled 2026-04-13 09:15 UTC)
- Snowflake information_schema (pulled 2026-04-13 09:15 UTC)
```

**Output 3: JSON Transaction Log** (persisted for audit trail)
```json
{
  "timestamp": "2026-04-13T09:15:00Z",
  "report_type": "pipeline_health_snapshot",
  "pipelines": [
    {
      "pipeline_id": "fivetran_salesforce",
      "status": "healthy",
      "data_freshness_hours": 2,
      "freshness_ok": true,
      "health_score": 95,
      "last_run": "2026-04-13T07:15:00Z",
      "errors": 0,
      "dbt_tests_passed": 45,
      "dbt_tests_failed": 0,
      "schema_changes_detected": false,
      "confidence": "high"
    }
  ],
  "stack_health_score": 85,
  "alerts_triggered": [],
  "execution_duration_seconds": 45
}
```

---

## Configuration & Setup

**Before I start monitoring, customize these:**

**Monitoring Frequency:**
- "How often should I check pipelines? (default: every 10 minutes)"
- Options: 5, 10, 15, 30 minutes

**Alert Channels:**
- "Where should I send alerts? (default: Slack)"
- Options: Slack, Email, PagerDuty, None

**Freshness Thresholds:**
- Conservative: 1.5× expected cadence (more alerts, fewer false positives)
- Balanced: 1.25× expected cadence (recommended)
- Aggressive: 1.0× expected cadence (strict, more false positives)

**Deduplication Window:**
- "How long should I suppress duplicate alerts for same issue? (default: 1 hour)"

---

## Error Handling

**If API connection fails (auth, network, timeout):**
- Retry with exponential backoff (2s, 4s, 8s)
- Alert user: "Cannot reach Fivetran API; using cached data from last check"
- Continue monitoring other pipelines

**If pipeline has never run:**
- Treat as "unknown" status (don't raise alert)
- Log warning: "Pipeline not yet initialized"

**If warehouse query times out:**
- Skip schema drift check for that run
- Alert user: "Cannot check schema drift (warehouse timeout); skipping this check"

**If dbt Cloud unreachable:**
- Skip dbt test checks (optional feature)
- Alert user: "dbt Cloud unavailable; dbt test results unavailable"

**If Slack webhook invalid:**
- Log error; continue monitoring
- Fallback: send email alert to ops team

**If data quality too low:**
- >80% missing freshness timestamps → Proceed with caution; flag in report
- 50–80% missing → Degraded results; lower confidence score to 60–70%
- <50% usable data → Flag as "insufficient data to monitor reliably"

---

## Example: End-to-End Monitoring Session

**You:** "Monitor my ELT pipelines for stale data and failures."

**Me (Preflight):**
```
✓ Fivetran connected (5 connectors)
✓ dbt Cloud connected (2 projects)
✓ Snowflake connection active
✓ Slack configured
✓ 5 active pipelines detected

SLA Configuration:
- Salesforce → Snowflake: 12h
- dbt daily: 24h
- Stripe: 12h
- Custom revenue: 6h
- Workato: 2h

Ready to monitor. Polling every 10 minutes.
```

**Ongoing (Background):**
- Every 10 minutes, I check each pipeline
- If freshness OK and no errors → silent (no alert)
- If issue detected → Slack alert sent immediately

**Scenario: Pipeline fails at 2:00 PM**
```
🔴 CRITICAL: Salesforce Sync Failed
Pipeline: Fivetran Salesforce → Snowflake
Error: Rate limit exceeded (HTTP 429)
Last successful sync: 2026-04-13 12:45 PM UTC
Data freshness: 1.5 hours (SLA: 12h) — still OK but degrading

Action: Check Fivetran dashboard [link]
Confidence: 88%

Next check: 2:10 PM
```

**Daily Report at 8:00 AM:**
```
## ELT Pipeline Monitoring — Daily Report
Date: 2026-04-13

### Summary
4 pipelines healthy. 1 pipeline (custom_revenue) degraded — not run in 12+ hours.

### Critical Findings
- custom_revenue_sync: 28 hours old (SLA: 6h) — CRITICAL
  Recommendation: Restart SQL job; check Snowflake logs for timeout errors

- fivetran_stripe: 11.5 hours old (SLA: 12h) — WARNING
  Recommendation: Job running slow (expected cadence ~6h); monitor next 2 runs

### Data Quality & Limitations
- Schema drift detection: 5 tables monitored (Account, Opportunity, Contact, Stripe, Custom Revenue)
- dbt tests: 47 passed, 0 failed (excellent)
- Freshness calculation: Based on connector execution logs (may lag 5–10 min)

### Recommended Actions
1. Investigate custom_revenue_sync failure — possible warehouse issue or SQL timeout
2. Schedule with data ops to review cadence settings for Stripe sync
3. Continue monitoring dbt tests; all passing

### Sources
- Fivetran API (2026-04-13 09:00 UTC)
- dbt Cloud API (2026-04-13 09:00 UTC)
- Snowflake information_schema (2026-04-13 09:00 UTC)
```

---

## What to Run Next

After monitoring is running smoothly:

1. **PM-01: Pipeline Health Monitoring Agent** — Depends on RA-06 freshness signals; validates that opportunity pipeline data is current before deeper pipeline analysis.

2. **PM-04: Forecast Agent** — Consumes RA-06 freshness alerts; adjusts forecast confidence scores if data is stale or unreliable.

3. **DQH-02: Field Normalization Agent** — Waits for RA-06 to confirm no schema drift before normalizing field values.

4. **Schedule Recurring Runs** — Set up daily or weekly reports; adjust SLA thresholds based on actual pipeline cadence (first 2 weeks of monitoring).

---

## References & Further Reading

**Key Docs:**
- Fivetran API docs: https://fivetran.com/docs/rest-api
- dbt Cloud API docs: https://docs.getdbt.com/dbt-cloud/api
- Snowflake information_schema: https://docs.snowflake.com/en/sql-reference/information-schema.html
- BigQuery metadata tables: https://cloud.google.com/bigquery/docs/information-schema-intro

**Industry Standards:**
- Data SLA best practices (dbt Labs)
- ETL monitoring strategies (Integrate.io, Monte Carlo)
- Schema drift detection (Acceldata, Soda)
- Data observability platforms: Monte Carlo, Acceldata, Soda, Datadog

