---
name: revops-integration-health
description: Monitors every API connection in your tech stack (Salesforce, HubSpot,
  Fivetran, Workato, data warehouse, accounting tools) for failures, data staleness,
  and sync errors. Polls health every 5–15 minutes, calculates a 0–100 health score,
  detects data lag, and alerts via Slack before failures cascade to broken reports
  and forecasts.
metadata:
  trigger_phrases:
  - check integration health
  - monitor api status
  - is my data fresh
  - integration status report
  - stack health score
  - detect sync failures
  - api health monitoring
  - integration alerts
  - stack reliability check
  - integration performance
  category: Tech Stack & Operations
  phase: day_1
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents: []
    mcps:
    - Salesforce MCP (primary CRM, read-only)
    - HubSpot MCP (alternative CRM, read-only)
    - Fivetran MCP or REST API (data pipeline monitoring)
    - Workato MCP or REST API (integration platform)
    - Slack MCP (for real-time alerts, optional but recommended)
    minimum_data:
    - At least one CRM (Salesforce or HubSpot) with active sync
    - 'Integration registry: list of systems to monitor'
    - OAuth tokens or API keys for each monitored system
  output_format: slack alerts + markdown report + json dashboard
---

# TSO-01 Integration Health Agent

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager or Sales Operations Manager at B2B SaaS companies, 100–500 employees, North America.

**The painkiller pain points we're solving:**

### Pain Point 1: Integration Blindness — API Failures Go Undetected Until Reports Break
- **Problem:** Mid-market RevOps teams have no visibility into integration health. When an API connection fails (auth token expired, rate limit exceeded, schema change), the failure goes undetected for 4–24 hours. During this time, bad data compounds: stale reports, inaccurate forecasts, eroded trust in reporting systems.
- **Quantified cost to the role:** A single undetected 24-hour integration failure causes forecasting errors worth $750K–$2M in operational waste. For a RevOps manager with 8–15 integrations, the expected annual cost of undetected failures is $1.5M–$4M in forecast error and rework.
- **What teams do today:** Log into each connected system daily to spot-check data sync (Salesforce sync logs, HubSpot activity feed, Fivetran monitoring). Some purchase third-party monitoring (PagerDuty $3K–$10K/year, Datadog $1K–$20K/year).
- **Why it's urgent:** API reliability is degrading—uptime fell from 99.66% to 99.46% year-over-year, resulting in 60% more downtime. By month 3 of continuous failures, sales team loses confidence in CRM as source of truth.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

### Pain Point 2: Data Lag & Staleness — Stale Reports Cause Bad Forecasts
- **Problem:** Integration data arrives 6–12 hours delayed (Salesforce every 6 hours, Fivetran 2–4 hours, HubSpot 10 minutes). RevOps makes forecasting decisions on stale data, missing recent deal movement and causing forecast accuracy to drop.
- **Quantified cost to the role:** Every 1% decrease in forecast accuracy costs $100K–$200K in planning waste. Teams that monitor data freshness achieve 5–10% better accuracy. A single month of undetected staleness can cost $100K–$200K in forecast error and planning misalignment.
- **What teams do today:** Build custom freshness dashboards in Looker/Tableau ($2K–$10K), run manual validation queries (5–10 hours/week), purchase Fivetran/Workato monitoring ($1K–$10K/year).
- **Why it's urgent:** 68% of data engineers spend >5 hours/week investigating staleness. Median forecast accuracy is 70–79%, below acceptable threshold. By month 3 of unaddressed staleness, forecast miss reaches 20%, damaging credibility with leadership.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

### Pain Point 3: Sync Error Recovery Lag — Manual Troubleshooting Wastes RevOps Time
- **Problem:** When an integration fails, RevOps spends 4–6 hours pulling logs, testing API endpoints, checking recent system changes. Per incident: $300–$450 in labor. Mid-market experiences 2–4 integration incidents per month.
- **Quantified cost to the role:** Annual diagnostic labor cost: $9K–$18K. Undetected failures requiring manual rework (re-sync, record validation, cleanup): $2K–$5K per incident. Total annual cost: $25K–$50K in labor and rework.
- **What teams do today:** Check logs manually (30 min–1 hour daily), maintain spreadsheets of known issues (5 hours/week), build custom Zapier/Workato monitoring (20–40 hours setup).
- **Why it's urgent:** By month 6, RevOps team spends 25–30% of time firefighting. Strategic projects (forecasting, pipeline health, data governance) slip 3–6 months.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 3 TIER 1 sources

---

## What This Agent Does

The Integration Health Agent is your tech stack's early-warning system. It continuously monitors every API connection in your RevOps infrastructure (Salesforce, HubSpot, Fivetran, Workato, data warehouse, accounting tools, etc.) for failures, data lag, and sync errors. Every 5–15 minutes, it polls all registered integrations, checks their API health status, measures data freshness, detects failures in recent sync logs, and calculates a stack-level health score (0–100). When degradation is detected, it alerts your RevOps team via Slack with clear severity levels: CRITICAL (API down, data inaccessible), HIGH (data stale beyond acceptable lag), MEDIUM (intermittent errors, rate limits approaching), or LOW (minor issues, monitoring needed). You get a real-time dashboard showing which integrations are healthy, which are degraded, and what action to take next.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your API connections, confirm integration credentials are valid, test connectivity to all systems you want to monitor, and ask you to scope your monitoring setup.

**Step 1: MCP Connection Verification**

I'll check if you have at least one CRM connection (Salesforce MCP or HubSpot MCP) authenticated.

- ✓ If connected and authenticated: Proceed to Step 2.
- ✗ If no CRM connected: Agent stops. "You need to connect at least one CRM (Salesforce or HubSpot). Provide OAuth token or API key."

**Step 2: Integration Registry**

You'll tell me which systems to monitor. I'll ask:

- "Which CRM are you using? Salesforce, HubSpot, or both?"
- "Which data integration tool? Fivetran, Workato, custom, or none?"
- "Do you have a data warehouse (Snowflake, BigQuery, etc.)?"
- "Any accounting or HRIS tools connected?"

Example response:
```
Systems to Monitor:
  ✓ Salesforce (CRM, primary)
  ✓ Fivetran (data pipeline: Salesforce → Snowflake)
  ✓ Snowflake (data warehouse)
  ✓ NetSuite (accounting)
```

**Step 3: Credential Testing**

For each system you named, I'll attempt a test API call:

- ✓ Salesforce: Test OAuth token, query org metadata
- ✓ Fivetran: Test API key, query connector status
- ✓ Snowflake: Test connection, query system tables
- ✓ NetSuite: Test API credentials

Example preflight output:
```
PREFLIGHT CHECK

✓ Salesforce: OAuth token valid (expires 2026-04-20)
  - Can access sync logs and org metadata
  - Found 847 contacts, last modified 15 min ago

✓ Fivetran: API key valid
  - Can access connector status endpoint
  - Found 1 active connector (Salesforce → Snowflake)

✓ Snowflake: Connection successful
  - Query response time: 245ms
  - Database accessible

✓ NetSuite: API credentials valid
  - Can access connector status

✓ Slack webhook: Configured
  - Test message sent successfully

READY TO BEGIN

Integration registry complete. Will monitor 4 systems.
Polling frequency: Every 10 minutes
Alert channel: #revops-alerts (Slack)
First poll: 60 seconds
```

**Step 4: Slack Configuration (Optional)**

If you want real-time alerts, provide a Slack webhook URL.

- ✓ If webhook valid: Alerts enabled
- ⚠️ If no webhook: Alerts disabled (you can view dashboard manually)

---

## Step-by-Step Workflow

### Step 1: Register All Integrations

Build a registry of every system you want monitored, with expected sync cadence:

```json
{
  "integrations": [
    {
      "integration_id": "salesforce_sync",
      "name": "Salesforce (CRM)",
      "category": "crm",
      "api_endpoint": "https://yourorg.salesforce.com/services/data",
      "expected_sync_cadence_minutes": 360,
      "critical": true,
      "weight": 0.40
    },
    {
      "integration_id": "fivetran_sf_to_snowflake",
      "name": "Fivetran: Salesforce → Snowflake",
      "category": "data_pipeline",
      "api_endpoint": "https://api.fivetran.com/v1/connectors",
      "expected_sync_cadence_minutes": 240,
      "critical": true,
      "weight": 0.35
    },
    {
      "integration_id": "snowflake_warehouse",
      "name": "Snowflake (Data Warehouse)",
      "category": "warehouse",
      "api_endpoint": "https://yourorg.snowflakecomputing.com/api/v2",
      "expected_sync_cadence_minutes": 0,
      "critical": false,
      "weight": 0.15
    },
    {
      "integration_id": "netsuite_accounting",
      "name": "NetSuite (Accounting)",
      "category": "accounting",
      "api_endpoint": "https://api.netsuite.com/services/rest/record",
      "expected_sync_cadence_minutes": 720,
      "critical": false,
      "weight": 0.10
    }
  ]
}
```

### Step 2: Poll All Integrations (Every 5–15 minutes)

For each integration in the registry:

1. **Query API health endpoint** — Test connectivity, measure response time
2. **Check last sync timestamp** — From Salesforce SyncLog, Fivetran task history, etc.
3. **Measure data freshness** — Calculate: now - last_successful_sync = freshness_hours
4. **Fetch recent sync logs** — Last 5 syncs to detect patterns (failures, partial syncs, rate limits)

Example output from one polling cycle:

```json
{
  "timestamp": "2026-04-13T09:15:00Z",
  "polls": [
    {
      "integration_id": "salesforce_sync",
      "api_status": "up",
      "http_status_code": 200,
      "response_time_ms": 234,
      "last_sync": "2026-04-13T09:00:00Z",
      "freshness_hours": 0.25,
      "recent_syncs": [
        { "timestamp": "09:00", "status": "success", "records": 234 },
        { "timestamp": "03:00", "status": "success", "records": 198 }
      ],
      "errors": [],
      "rate_limit_usage_percent": 23
    },
    {
      "integration_id": "fivetran_sf_to_snowflake",
      "api_status": "up",
      "http_status_code": 200,
      "response_time_ms": 145,
      "last_sync": "2026-04-13T08:15:00Z",
      "freshness_hours": 1,
      "recent_syncs": [
        { "timestamp": "08:15", "status": "success", "records": 3847 },
        { "timestamp": "04:15", "status": "success", "records": 3921 },
        { "timestamp": "00:15", "status": "partial", "error": "RATE_LIMIT_EXCEEDED", "records": 2100 }
      ],
      "errors": [
        { "error_code": "RATE_LIMIT_EXCEEDED", "timestamp": "2026-04-13T00:15:00Z" }
      ],
      "rate_limit_usage_percent": 67
    }
  ]
}
```

### Step 3: Calculate Per-Integration Health Score

For each integration, calculate a health score from 0–100:

```
base_score = 100
score -= 50 if api_status = "down"
score -= 25 if api_status = "auth_failed"
score -= 20 if data_freshness_hours > 2 * expected_cadence
score -= 15 if rate_limit_usage_percent > 90
score -= 10 per recent_error (capped at -40)
score -= 5 if intermittent (3/5 recent syncs failed)

health_score = max(0, min(100, score))
```

**Score Interpretation:**

| Score | Status | Action |
|-------|--------|--------|
| 90–100 | Healthy (green) | No action needed |
| 70–89 | Degraded (yellow) | Monitor; may need attention |
| 50–69 | High Risk (orange) | Intervention recommended |
| 0–49 | Critical (red) | Immediate action required |

### Step 4: Aggregate Stack Health Score (Weighted Average)

Combine all integration scores into a single stack-level score:

```
stack_health_score = 
  (crm_score * 0.40) +
  (pipeline_score * 0.35) +
  (warehouse_score * 0.15) +
  (secondary_score * 0.10)

IF any critical system (CRM or pipeline) < 50:
  stack_status = "CRITICAL"
ELSE IF stack_health_score < 70:
  stack_status = "HIGH_RISK"
ELSE IF stack_health_score < 85:
  stack_status = "DEGRADED"
ELSE:
  stack_status = "HEALTHY"
```

Example:
```
Salesforce health: 100 (CRM, 40% weight)
Fivetran health: 75 (Pipeline, 35% weight)
Snowflake health: 100 (Warehouse, 15% weight)
NetSuite health: 95 (Secondary, 10% weight)

Stack Score = (100 * 0.40) + (75 * 0.35) + (100 * 0.15) + (95 * 0.10)
            = 40 + 26.25 + 15 + 9.5
            = 90.75/100 (Healthy)
```

### Step 5: Detect Issues & Generate Alerts

For each degraded integration, determine severity and generate alerts:

| Severity | Condition | Time-to-Alert | Action |
|----------|-----------|---------------|--------|
| CRITICAL | API down OR auth failed OR critical system health < 20 | Immediate (1–2 min) | Direct Slack message + #revops-alerts |
| HIGH | Data stale > 2 × expected cadence OR 4/5 recent syncs failed | 10–15 min | #revops-alerts channel |
| MEDIUM | Intermittent errors (2–3/5 syncs failed) OR rate limit >85% | 30 min | #revops-alerts channel |
| LOW | Rate limit 70–85% OR single isolated error | Hourly summary | Daily email only |

**Example Alert (Slack):**

```
:warning: HIGH: Fivetran Data Stale
Integration: Fivetran (Salesforce → Snowflake)
Status: Last sync 15 hours ago (expected 4 hours)
Data Age: 15 hours
Impact: Warehouse data is stale; forecast and pipeline reports may be inaccurate
Recent Syncs: 1 success, 1 partial (rate limit), 3 pending
Recommended Action: Check Fivetran dashboard for blocked connectors. 
Review rate limit usage. Reschedule sync if needed.
Next Check: 09:30 UTC
Incident Link: [View dashboard]
```

### Step 6: Deduplication (Avoid Alert Fatigue)

Track alert history to suppress duplicate alerts:

```json
{
  "alert_dedup_key": "tso01_integration_fivetran_stale",
  "last_alert_timestamp": "2026-04-13T08:45:00Z",
  "alert_count_today": 2,
  "silence_rules": {
    "CRITICAL": "30-minute minimum silence before re-alert",
    "HIGH": "1-hour minimum silence before re-alert",
    "MEDIUM": "2-hour minimum silence before re-alert",
    "LOW": "Daily summary only, never real-time"
  }
}
```

**Logic:** If same integration fails again within silence window, suppress alert but increment counter. Log suppressed alerts for daily digest.

### Step 7: Generate Output Report & Dashboard

Deliver results in three formats:

**Format 1: Slack Dashboard (Real-Time)**

```
Integration Health Status — 2026-04-13 09:15 UTC
Stack Health Score: 87/100 (Healthy) ✓

Salesforce (CRM)          100 ✓
Fivetran (Pipeline)       75  ⚠️
Snowflake (Warehouse)     100 ✓
NetSuite (Accounting)     95  ✓

1 Alert: Fivetran data stale [View]
```

**Format 2: Markdown Report (Human-Readable)**

```markdown
# Integration Health Report
**Generated:** 2026-04-13 09:15 UTC
**Stack Health Score:** 87/100 (Healthy)

## Executive Summary
5 of 6 integrations healthy. Fivetran sync delayed 1 hour. No action required at this time.

## Integration Status

### Salesforce (CRM)
- Status: Healthy ✓
- Last Sync: 2026-04-13 09:00 UTC (15 minutes ago)
- Data Freshness: 15 minutes (expected: 6 hours) ✓
- Health Score: 100/100
- Recent Errors: None

### Fivetran: Salesforce → Snowflake
- Status: Degraded ⚠️
- Last Sync: 2026-04-13 08:15 UTC (1 hour ago)
- Data Freshness: 1 hour (expected: 4 hours)
- Health Score: 75/100
- Recommended Action: Monitor next sync. If delay continues, check Fivetran logs.

## Recommended Actions
1. Monitor Fivetran sync completion at next cycle (12:15 UTC)
2. If delays continue, escalate to Fivetran support
3. No immediate action required; critical systems operational
```

**Format 3: JSON Dashboard (Machine-Readable, for RA-06)**

```json
{
  "timestamp": "2026-04-13T09:15:00Z",
  "stack_health_score": 87,
  "stack_status": "HEALTHY",
  "data_quality_confidence": 0.92,
  "critical_systems_down": false,
  "integrations": [
    {
      "integration_id": "salesforce_sync",
      "health_score": 100,
      "status": "healthy",
      "last_sync": "2026-04-13T09:00:00Z",
      "freshness_hours": 0.25,
      "api_status": "up"
    },
    {
      "integration_id": "fivetran_sf_to_snowflake",
      "health_score": 75,
      "status": "degraded",
      "last_sync": "2026-04-13T08:15:00Z",
      "freshness_hours": 1,
      "api_status": "up",
      "issues": [
        {
          "type": "data_staleness",
          "severity": "high",
          "message": "Sync delayed 1 hour"
        }
      ]
    }
  ],
  "alerts": [
    {
      "alert_id": "tso01_alert_202604130900_fivetran_stale",
      "severity": "HIGH",
      "integration": "fivetran_sf_to_snowflake",
      "message": "Fivetran sync delayed 1+ hours"
    }
  ]
}
```

---

## Configuration Options

Before I start monitoring, you can customize these parameters:

**Polling Frequency (Default: 10 minutes)**
- "How often should I check integration health? 5, 10, 15, or 30 minutes?"
- Shorter = faster detection but higher API overhead
- Recommended: 10 minutes (balance of responsiveness and cost)

**Alert Severity Thresholds (Defaults Shown)**
- "What freshness threshold should trigger a HIGH alert? (Default: >2× expected cadence)"
- "What rate limit % should trigger a MEDIUM alert? (Default: 85%)"
- Adjust based on your SLAs and risk tolerance

**Slack Notification Preferences (Default: Real-time)**
- "Should I send real-time alerts or daily digest? (Default: Real-time CRITICAL/HIGH, daily digest for MEDIUM/LOW)"
- "Who should receive direct messages for CRITICAL alerts? (Default: #revops-alerts channel)"
- "Should I tag specific people on critical failures? (Optional)"

**Integration Weights (Default: CRM 40%, Pipeline 35%, Warehouse 15%, Secondary 10%)**
- "Does this weighting match your business? (E.g., if Salesforce is less critical, reduce CRM weight)"
- Advanced: customize per-integration weights

**Maintenance Windows (Optional)**
- "Provide scheduled maintenance windows to suppress alerts"
- Example: "Salesforce patch maintenance 2026-04-13 02:00–04:00 UTC"

---

## Error Handling

### Integration Unreachable (Network Issue)

**Symptom:** API endpoint times out or returns DNS error.

**Behavior:**
- Mark as "unreachable" (not "down" yet; could be transient)
- Retry after 30 seconds
- If still unreachable: Alert HIGH severity and re-check every 5 minutes

**Agent Output:**
```
⚠️ Fivetran API Unreachable
Status: Cannot connect to api.fivetran.com (timeout after 10s)
Likely Cause: Network issue, Fivetran outage, or DNS problem
Action: Retrying in 5 minutes. Check your network and Fivetran status page.
```

### API Returns Error (Confirmed Down)

**Symptom:** API returns 5xx error (502, 503, etc.).

**Behavior:**
- Mark as "down" immediately
- Alert CRITICAL severity
- Stop retry attempts; check again in 5 minutes

**Agent Output:**
```
🔴 Salesforce API Error
Status: Salesforce returned HTTP 502 Bad Gateway
Likely Cause: Salesforce maintenance or outage
Data Impact: Last successful sync 45 minutes ago
Recommended Action: Check https://status.salesforce.com. 
If outage confirmed, wait. Otherwise, verify OAuth token.
```

### Credential Expiration / Auth Failure

**Symptom:** API returns 401 Unauthorized.

**Behavior:**
- Alert CRITICAL immediately
- Pause monitoring for that integration
- Include re-authentication link in alert

**Agent Output:**
```
🔴 Salesforce Authentication Failed
Status: OAuth token expired or invalid
Likely Cause: Token expiration (Salesforce tokens valid 1–24 hours)
Recommended Action: Re-authenticate Salesforce. [Re-auth Link]
Once refreshed, monitoring resumes automatically.
```

### Partial Stack Failure

**Symptom:** 2 of 6 integrations down; others healthy.

**Behavior:**
- Continue monitoring healthy integrations normally
- Alert CRITICAL only for failed integrations
- Stack health score reflects weighted failure

**Example:** If Salesforce (40% weight) is down but Fivetran (35%) is healthy:
```
Stack Health: 65/100 (HIGH_RISK)
Status Override: CRITICAL (because CRM is down — can't ingest new data)
Recommendation: Restore Salesforce connection ASAP; downstream pipelines affected
```

### Rate Limit Approaching

**Symptom:** API usage >90% or returns 429 Too Many Requests.

**Behavior:**
- Alert MEDIUM severity
- Don't retry immediately (will hit limit)
- Calculate time until reset; include in alert

**Agent Output:**
```
⚠️ Salesforce Rate Limit Approaching
Current Usage: 738 / 850 API calls (87%)
Reset Time: 12 minutes (at 09:27 UTC)
Recommended Action: Monitor closely. If hit, syncs will fail. 
Consider reducing call frequency or requesting higher limit.
```

---

## What to Run Next

After Integration Health Agent runs:

1. **RA-06: ELT Pipeline Monitoring Agent** — Consumes health score from TSO-01 to monitor data freshness in warehouse. If TSO-01 detects stale data, RA-06 flags downstream quality issues.

2. **PM-04: Forecast Agent** — Uses TSO-01 data quality confidence score to adjust forecast confidence. If integrations are degraded, forecast is marked as less reliable.

3. **Escalation Protocol** — If CRITICAL alert is not resolved within 15 minutes, escalate to VP Ops or CTO.

4. **Weekly Review** — Each week, review integration health trends and alerts. Plan upgrades or credential refreshes proactively.

---

## Example: End-to-End Session

**You:** "Check my integration health and tell me if anything's broken."

**Me (Preflight):**
```
PREFLIGHT CHECK

✓ Salesforce MCP connected (OAuth token valid, expires 2026-04-20)
  - Can access sync logs and org metadata
  - 847 contacts, last modified 15 min ago

✓ Fivetran API credentials valid
  - Can access connector status
  - 1 active connector found (Salesforce → Snowflake)

✓ Snowflake connection successful
  - Query response time: 245ms

✓ Slack webhook configured
  - Test message sent; alerts enabled

READY. Monitoring 3 integrations. First poll: 60 seconds.
```

**Me (After First Poll):**
```
Integration Health Report — 2026-04-13 09:15 UTC
Stack Health Score: 87/100 (Healthy) ✓

Salesforce              100 ✓
Fivetran (Salesforce → Snowflake)  75  ⚠️
Snowflake              100 ✓

1 Alert Detected (HIGH): Fivetran data stale
  Last sync: 1 hour ago (expected 4 hours)
  Recommended action: Monitor next sync. If continues, check Fivetran logs.

Detailed Report: [Link]
Dashboard: [Link]
```

**You:** "Is the stale data going to break my forecast?"

**Me:** "Yes, if data stays stale >2 hours longer. I'm monitoring the next sync (due 12:15 UTC). If it completes on time, you're fine. If delayed again, I'll alert you and recommend pausing forecast until data refreshes. The delay is likely a Fivetran rate limit issue (67% usage currently)."

**You:** "How long until I should be concerned?"

**Me:** "If Fivetran next sync at 12:15 UTC also fails or delays, that's 6+ hours of stale data. That would trigger a HIGH → CRITICAL upgrade, and I'd recommend stopping new forecast decisions until resolved. For now, monitor mode. I'll send real-time updates."

---

## References & Further Reading

**Key Concepts:**

- **Health Score:** 0–100 aggregate metric combining API status, data freshness, and error history. See Section 5.1 of TSO-01_integration_health_spec.md for scoring formula.
- **Data Freshness:** Time elapsed since last successful integration sync. Freshness = now - last_successful_sync. Compared to expected sync cadence (e.g., Salesforce every 6 hours expected).
- **Stack Health:** Weighted average of all integration health scores. Weights: CRM 40%, Pipeline 35%, Warehouse 15%, Secondary 10%.
- **Alert Severity:** CRITICAL (immediate action) → HIGH (investigate within 30 min) → MEDIUM (within 2 hours) → LOW (daily digest).
- **Rate Limit:** % of API calls consumed in current window. At 100%, API returns 429 Too Many Requests and sync fails.
- **Cascade Failure:** When one integration failure (e.g., Salesforce down) blocks downstream integrations (e.g., Fivetran can't read from Salesforce).

**Data Contract with RA-06 (ELT Pipeline Monitoring):**

TSO-01 outputs a JSON payload every 10 minutes that RA-06 consumes:

```json
{
  "timestamp": "2026-04-13T09:15:00Z",
  "integration_id": "fivetran_salesforce_to_snowflake",
  "health_score": 87,
  "status": "degraded",
  "data_freshness_hours": 0.5,
  "freshness_ok": true,
  "api_status": "up"
}
```

RA-06 uses this to: (1) Check if data is fresh enough for reliable forecasting, (2) Flag if health_score < 70 and escalate to manager, (3) Adjust downstream report confidence based on data freshness.

**Documentation Files:**

- Full Architecture Spec: TSO-01_integration_health_spec.md (sections 1–17 for deep dives)
- Research Brief: TSO-01_integration_health_research.md (pain points, evidence, current practices)
- Consistency Rules: RevOps_Agent_Consistency_Rules.md (naming, error handling, output formats)

