---
name: revops-vendor-performance
description: Evaluates SaaS vendor performance against contractual SLAs, tracks uptime
  and support responsiveness, assesses adoption alignment, and produces vendor health
  scorecards to drive renewal and replacement decisions.
metadata:
  trigger_phrases:
  - evaluate vendor performance
  - check vendor sla compliance
  - score vendor health
  - assess saaS vendor
  - vendor scorecard
  - renewal decision
  - which vendors are underperforming
  category: Tech Stack & Operations
  phase: 30_days
  data_readiness: 30_days
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents:
    - revops-tool-adoption (TSO-02)
    mcps:
    - Salesforce MCP (Salesforce orgs, Enterprise license required for Event Logs
      API)
    - HubSpot MCP (HubSpot Professional+ plan required)
    minimum_data:
    - Contract object with vendor_name, sla_details, contract_end_date, annual_cost_usd
    - Support ticket object (Case or Ticket) with vendor_name, created_date, first_response_date,
      resolved_date
    - Vendor incident/uptime data (from status page API or manual incident log)
    - Adoption metrics from TSO-02 Agent (DAU, MAU, adoption_rate_pct, trend_direction)
  output_format: markdown
---

# Vendor Performance Agent

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager or Procurement Manager at B2B SaaS companies, 100–500 employees, North America.

**The painkiller pain points we're solving:**

### Pain Point 1: Blind SLA Compliance Tracking — $2,900–$17,500 Annual Cost Per Manager

**Problem:** Most mid-market companies lack visibility into whether vendors actually meet contractual SLA commitments (uptime, response time, resolution time). SLA violations go undetected until a high-impact incident reveals the gap. By renewal time, company has no documented evidence of breaches and loses all negotiating leverage.

**Quantified cost to the role:** RevOps teams spend 8–12 hours per month manually tracking vendor SLAs across spreadsheets, Slack, and vendor status pages. At $145k RevOps Manager salary, this is ~$2,900 per year in labor per manager. Additionally, mid-market companies miss $5,000–$15,000 annually in unclaimed SLA credits when breaches go undetected. Without documented breach history, renewal negotiations default to vendor's requested increase (industry average 12% in 2025). Over 3 years, one vendor relationship with no performance accountability costs $15,000–$30,000 in hidden labor and foregone credits.

**What teams do today:** 62% of mid-market companies maintain manual spreadsheets or Slack integrations to track SLAs; 34% subscribe to third-party SLA monitoring tools ($200–$500/month per tool). No single solution aggregates SLA compliance across the entire vendor ecosystem. Teams that manually track SLAs only monitor 3–5 critical tools max; remaining 45–195 vendors go unsupervised.

**Why it's urgent:** Unchecked SLA violations compound. Month 1–2: missed credits ($500–$1,500). Month 3–6: vendor relationship deteriorates, support becomes reactive. Month 6+: at renewal, no negotiating leverage; company pays full renewal price. By year 2, blind vendor management costs exceed $30,000 and adoption data reveals the vendor is underused (see Pain Point 2).

**Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

### Pain Point 2: Vendor Underperformance Hidden in Adoption Data — $480,000 Hidden Cost Over 3 Years

**Problem:** A vendor can maintain 99.9% uptime but still represent poor ROI if adoption is 15%. These misalignments are never surfaced because SLA data lives in isolation from adoption data. Teams renew low-adoption vendors at full price, failing to consolidate or replace them until year 2 of a 3-year contract, locking in waste.

**Quantified cost to the role:** For a $10M ARR company using 120 SaaS tools, typical vendor stack includes 3–5 low-adoption tools (adoption <30%) costing $180,000–$300,000 annually. Without a performance dashboard connecting adoption to SLA health, teams renew these at 12% increases annually. By year 3, the company has paid $30,000–$50,000 more for tools it doesn't use. Additionally, poor vendor support (evidenced by high ticket response times + low feature delivery) depresses adoption; teams blame tools instead of vendor performance. Fixing this misalignment alone typically unlocks $50,000–$150,000 in consolidation savings.

**What teams do today:** Teams track adoption in one system (TSO-02 Tool Adoption Agent) and vendor SLA health in another (native vendor dashboards). Renewal decisions are based on politics ("we've always used this tool") or gut feel, not data. Procrastination teams use spreadsheets across 3+ tools to track vendor contracts, adoption, and SLA performance—manually maintained, never synchronized, always stale.

**Why it's urgent:** Renewal decisions made without performance context are expensive. A company signs a 3-year renewal in Month 18 of a 24-month contract based on outdated adoption and zero SLA history. By year 2, adoption has dropped from 60% to 22% and the vendor has had 6 SLA breaches. Company is locked in and cannot escape without paying break fees. Total cost: $180,000 tool cost + $35,000 break fee + $50,000 in lost optimization savings = $265,000 avoidable loss.

**Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

### Pain Point 3: Unstructured Vendor Feature Delivery Tracking — $100,000+ in Lost Roadmap Leverage

**Problem:** Teams lack visibility into whether vendors deliver promised features on schedule. When features slip, there's no mechanism to hold vendors accountable, escalate during renewals, or adjust contract terms. Vendors routinely deprioritize customer-requested features, and teams have no negotiating leverage to prevent it.

**Quantified cost to the role:** Delayed features cost teams in two ways: (1) engineering workarounds (devs build custom integrations for missing features, costing 40–160 hours = $10,000–$40,000 per feature), and (2) renewal leverage loss (undocumented feature delays provide no basis for discount negotiation). Mid-market companies experience 20–40% of vendor roadmap items slip >3 months per year. Without documented history, vendors concede zero discounts at renewal; companies pay 10–15% increases despite chronic delivery failures.

**What teams do today:** Teams manually check vendor public roadmaps every 3–6 months, screenshot feature status, and track delivery in Slack or email. Critical features are tracked in project management tools but never connected to vendor health scoring. When renewal time arrives, teams have anecdotal complaints but zero documented evidence of delays to support negotiation.

**Why it's urgent:** Unaccountable vendor roadmaps entrench bad behavior. After 3 years, a vendor with chronic delivery failures has been rewarded with 3 renewals at inflated prices. Switching costs are now high (migration effort, team retraining) and company capitulates rather than replace. This locks in $10,000–$20,000 annual waste per underperforming vendor.

**Evidence quality:** 3/4 rubric criteria passed, 2 TIER 1 sources

---

## What This Agent Does

The Vendor Performance Agent evaluates SaaS vendor performance against contractual Service Level Agreements (SLAs), tracks uptime compliance, measures support responsiveness, assesses feature delivery progress, and integrates adoption data to produce quarterly vendor health scorecards. Unlike standalone SLA trackers (which ignore adoption context) or native vendor dashboards (which are disconnected), this agent aggregates performance metrics across your entire vendor ecosystem and surfaces misalignments that matter: a vendor with 99.9% uptime but 15% adoption is a consolidation candidate, not a renewal at list price. You get a detailed scorecard showing which vendors are at risk, which are over-priced for their performance, and what action to take (renew, negotiate, consolidate, or replace).

---

## Getting Started (Preflight Check)

When you trigger this agent, I'll verify your CRM connection, validate required data exists, assess data quality, and clarify the scope of your vendor analysis before running the evaluation.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP (Enterprise license required) or HubSpot MCP (Professional+ required) is connected and authenticated.
- **If connection fails:** I'll offer workarounds (export contracts + tickets to CSV for offline analysis) or help troubleshoot the MCP connection.
- **If successful:** Proceed to Step 2.

**Step 2: Required Data Validation**
I'll verify that your CRM contains:
- Contract object with: `vendor_name`, `sla_details` (uptime %, response time, resolution time), `contract_end_date`, `annual_cost_usd`
- Support ticket object with: `vendor_name`, `ticket_created_date`, `first_response_date`, `resolved_date`
- At least 1 vendor status page API connected (Slack, Salesforce Trust, AWS, or manual incident log)
- TSO-02 adoption data available (adoption rate, DAU, trend direction per tool)

**TSO-02 Dependency Check:**
I'll verify that TSO-02 (Tool Adoption Agent) has been executed and output data is available:
- ✓ TSO-02 output present → Adoption Alignment Score (10%) included in overall health calculation
- ⚠️ TSO-02 not yet run OR output unavailable → Overall health score will use fallback 3-factor formula (SLA 45% + Support 35% + Features 20%); adoption scoring will be unavailable and flagged in report

**Go/No-Go decision:**
- ✓ All required data present → Proceed
- ⚠️ 1–2 data sources missing → Partial results possible; I'll flag limitations and proceed with available data
- ✗ Core CRM data missing (no contracts, <50 tickets, or no adoption data) → No-go; request data enrichment first

**Step 3: Data Quality Assessment**
I'll calculate:
- Count of vendor contracts with populated SLA terms (should be ≥5 for meaningful analysis)
- % of support tickets with valid created/resolved dates (should be ≥90%)
- Estimated incident data completeness from vendor status pages (should be ≥80% trailing 30 days)
- % of SaaS tools in license inventory mapped to contracts via TSO-02 (should be ≥70%)
- Data freshness (when contract and ticket data were last updated)

**Step 4: Define Your Vendor Analysis Scope**
Before running the analysis, I'll ask:
- "Which vendors should I analyze? (All contracts, or specific vendors by name? Exclude any vendors?)"
- "What time window? (30 days, 90 days, or since contract start?)"
- "Do you want analysis-only mode (I show you scorecards and recommendations, but don't modify your CRM), or should I write scorecard records to your CRM?"
- "Are there vendors you don't want evaluated? (e.g., do not touch critical infrastructure vendors without escalation)"

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID, Enterprise license confirmed)
✓ Contract object present; found 18 contracts with SLA details
✓ Support ticket data quality: 94% of 287 tickets have valid created/resolved dates
✓ Vendor status page API access: 4 vendors (Slack, Salesforce, AWS, Figma)
✓ TSO-02 adoption data available; 14 of 18 vendors mapped (78% coverage)
✓ Data freshness: contracts updated [X days ago], tickets from last 90 days ✓

Scope: All 18 vendor contracts | 90-day analysis window | Analysis + CRM write mode enabled

Ready to begin vendor health evaluation...
```

---

## Step-by-Step Workflow

### Step 1: Fetch Contract Data (With SLA Terms)

**What I'll do:**
- Query Contract object: all records or your specified subset
- Extract: `vendor_name`, `contract_id`, `annual_cost_usd`, `support_tier`, `contract_end_date`, `renewal_date`, `total_licensed_seats`
- Parse SLA terms into structured fields:
  - `sla_uptime_threshold_pct` (e.g., "99.9%" → 99.9)
  - `sla_response_time_hours` (e.g., "4 hours" → 4)
  - `sla_resolution_time_hours` (e.g., "24 hours" → 24)

**Data I need from each contract:**
- Vendor name (required; join key for all downstream data)
- Annual cost and licensed seat count (for cost-per-user benchmarking)
- SLA commitments in structured format (uptime %, response time, resolution time)
- Contract end date and days-to-renewal (for risk tier assignment)
- Support tier (Standard, Premium, Enterprise)

**What you'll see:** Progress indicator ("Fetched 8 / 18 contracts...").

---

### Step 2: Fetch Support Ticket Data (Last 90 Days)

**What I'll do:**
- Query Case (Salesforce) or Ticket (HubSpot) object for last 90 days
- Group by `vendor_name`
- Extract: `ticket_created_date`, `first_response_date`, `resolved_date`, `issue_severity`, `ticket_category`

**Batch strategy:** Fetch in 500-record increments to respect API rate limits.

**Data I need from each ticket:**
- Vendor name (required; must match contract vendor_name for join)
- Created, first-response, and resolved timestamps (all required for SLA calculations)
- Ticket severity (for trend analysis)
- Resolution status (for completion rate calculation)

**Quality checks:**
- Validate created < first_response < resolved (timestamps are logical)
- Flag tickets missing vendor_name or date fields
- Count tickets per vendor (should be ≥50 per vendor for reliable SLA calculation)

---

### Step 3: Fetch Vendor Incident Data (From Status Pages)

**What I'll do:**
- Query each vendor's public status page API (Slack, Salesforce Trust, AWS, etc.)
- Extract incident history: `incident_date`, `incident_start_time`, `incident_end_time`, `services_affected`, `incident_severity`
- Trailing window: 90 days (or as far back as status page API retains)

**Fallback if API unavailable:**
- Ask user for manual incident log as CSV (columns: `vendor_name`, `incident_date`, `incident_duration_minutes`, `services_affected`)
- If manual log unavailable, calculate uptime using support ticket SLA data as proxy (see Step 5 below)

**Data I need from each incident:**
- Vendor name
- Incident start and end times (both required)
- Duration (calculated: end - start)
- Services affected (for impact assessment)
- Severity classification

---

### Step 4: Fetch Adoption Data (From TSO-02)

**What I'll do:**
- Access TSO-02 Agent output: adoption metrics per tool
- Extract: `tool_name` (must match vendor_name), `adoption_rate_pct`, `active_users`, `total_licensed_seats`, `trend_direction`, `trend_change_pct`

**Join logic:**
- Match TSO-02 tool_name to Contract vendor_name (should be 1:1 mapping)
- If tool missing from TSO-02, flag as "adoption data unavailable" and degrade adoption-alignment scoring

**Data I need from each tool:**
- Tool name or vendor name (join key)
- Adoption rate (% of licensed seats with activity)
- Active user count and licensed seat count (for cost-per-user calculation)
- Trend direction (up, flat, down) and velocity

---

### Step 5: Calculate SLA Compliance Score (0–100)

**Part A: Uptime Compliance**

For each vendor:
1. Sum total downtime from incident data (last 90 days): `total_downtime_minutes = SUM(incident_duration_minutes)`
2. Calculate available minutes: `total_available_minutes = 90 days * 1440 minutes/day = 129,600 minutes`
3. Calculate achieved uptime: `uptime_pct = (total_available_minutes - total_downtime_minutes) / total_available_minutes * 100`
4. Compare to SLA: `sla_uptime_breach = uptime_pct < sla_uptime_threshold_pct ? TRUE : FALSE`
5. Assign preliminary score:
   - If uptime_breach = TRUE: score = 60 (uptime breach is critical failure)
   - If uptime_pct >= sla_uptime_threshold: score = 100

**Part B: Response Time SLA Compliance**

For each support ticket:
1. Calculate response time: `response_time_hours = (first_response_date - ticket_created_date) / 3600 seconds`
2. Check breach: `response_breach = response_time_hours > sla_response_time_hours ? TRUE : FALSE`
3. Calculate compliance percentage: `response_sla_compliance_pct = (tickets_meeting_response_time / total_tickets) * 100`
4. Assign score component:
   - If response_sla_compliance_pct >= 95%: score_component = 30
   - If response_sla_compliance_pct 80–94%: score_component = 20
   - If response_sla_compliance_pct < 80%: score_component = 10

**Part C: Resolution Time SLA Compliance**

For each support ticket:
1. Calculate resolution time: `resolution_time_hours = (resolved_date - ticket_created_date) / 3600 seconds`
2. Check breach: `resolution_breach = resolution_time_hours > sla_resolution_time_hours ? TRUE : FALSE`
3. Calculate compliance percentage: `resolution_sla_compliance_pct = (tickets_meeting_resolution_time / total_tickets) * 100`
4. Assign score component (same scale as response_time)

**Part D: Overall SLA Compliance Score**

Combine three components:
```
sla_compliance_score = (
  uptime_score × 0.5 +
  response_sla_component × 0.25 +
  resolution_sla_component × 0.25
)
sla_compliance_score = MIN(100, MAX(0, sla_compliance_score))
```

**Example:**
- Uptime: 99.92% vs 99.9% threshold → score = 100
- Response time: 94% SLA compliance → component = 30
- Resolution time: 87% SLA compliance → component = 20
- Overall: (100 × 0.5) + (30 × 0.25) + (20 × 0.25) = 50 + 7.5 + 5 = 62.5 → **SLA Compliance Score = 63**

---

### Step 6: Calculate Support Quality Score (0–100)

Based on support ticket resolution metrics:

| Metric | Threshold | Points |
|--------|-----------|--------|
| Avg response time vs. SLA | <SLA threshold | 30 |
| Avg response time vs. SLA | SLA ± 50% | 15 |
| Avg response time vs. SLA | >SLA × 1.5 | 0 |
| Avg resolution time vs. SLA | <SLA threshold | 30 |
| Avg resolution time vs. SLA | SLA ± 50% | 15 |
| Avg resolution time vs. SLA | >SLA × 1.5 | 0 |
| Ticket resolution rate (% closed) | >95% | 20 |
| Ticket resolution rate (% closed) | 80–95% | 10 |
| Ticket resolution rate (% closed) | <80% | 0 |
| Reopened ticket rate (% of resolved) | <5% | 20 |
| Reopened ticket rate (% of resolved) | 5–10% | 10 |
| Reopened ticket rate (% of resolved) | >10% | 0 |

**Example:**
- Avg response: 2.1 hours vs. 4-hour SLA → 30 points
- Avg resolution: 18.3 hours vs. 24-hour SLA → 30 points
- Resolution rate: 98.5% → 20 points
- Reopen rate: 2.1% → 20 points
- **Support Quality Score = 100 (capped)**

---

### Step 7: Calculate Feature Delivery Score (0–100)

**What I'll do:**
1. Fetch vendor's public roadmap (manual list, Featurebase API, or web scrape)
2. For each feature promised in roadmap for last 12 months:
   - Track actual delivery date vs. promised quarter
   - Assign points:
     - On-time or early delivery: **+10 points** per feature
     - Late delivery (<3 months): **+5 points** per feature
     - Very late delivery (>3 months): **0 points** per feature
     - Not delivered / deprioritized: **-5 points** per feature
3. Cap total at 100, floor at 0

**Scoring examples:**
- 3 on-time + 2 late (<3 months): (3 × 10) + (2 × 5) = 40 → **Feature Delivery Score = 40**
- 2 on-time + 2 late + 1 deprioritized: (2 × 10) + (2 × 5) + (-5) = 25 → **Feature Delivery Score = 25**
- No roadmap data available: **Feature Delivery Score = "Data unavailable"**; exclude from overall health score

**Data quality check:**
- Flag features with placeholder status ("TBD", "TK", "Coming soon" without date) as "status unknown"
- Include features promised ≥6 months ago (to allow delivery window)
- Exclude vaporware (promised >18 months ago, never delivered, never deprioritized)

---

### Step 8: Calculate Adoption Alignment Score (0–100)

**What I'll do:**
1. Fetch adoption rate from TSO-02: `adoption_rate_pct = (active_users / total_licensed_seats) * 100`
2. Assign base score:
   - ≥70% adoption: 100 (excellently adopted)
   - 50–69% adoption: 75 (moderately adopted)
   - 30–49% adoption: 50 (low adoption; potential waste)
   - <30% adoption: 25 (very low adoption; consolidation candidate)
3. Apply trend penalty:
   - If adoption declining >5% per month: deduct 15 points
   - If adoption declining 2–5% per month: deduct 5 points
   - If adoption stable or growing: no penalty
4. Calculate cost-per-active-user:
   - `cost_per_active_user = annual_cost / active_users`
   - Compare to market median for tool category (from benchmarking data)
   - If cost significantly above median (>120% of median): flag as "premium-priced" in scorecard

**Example:**
- Adoption: 98% → base score = 100
- Trend: stable (+0.5%) → penalty = 0
- Cost per user: $360 vs. market median $280 → flagged but not deducted from score
- **Adoption Alignment Score = 100**

---

### Step 9: Calculate Overall Vendor Health Score

**Weighted Composite Formula — Branch on Data Availability:**

**If adoption data (TSO-02) is available:**
```
overall_vendor_health_score = (
  sla_compliance_score × 0.40 +
  support_quality_score × 0.30 +
  feature_delivery_score × 0.20 +
  adoption_alignment_score × 0.10
)
```

**If adoption data (TSO-02) is NOT available:**
```
overall_vendor_health_score = (
  sla_compliance_score × 0.45 +
  support_quality_score × 0.35 +
  feature_delivery_score × 0.20
)
```
**Note:** When using the fallback 3-factor formula, flag the overall score in the output report as "adoption-degraded" to indicate that adoption-based consolidation recommendations are unavailable. Re-run this agent after TSO-02 completes for full 4-factor scoring.

**If feature_delivery data unavailable (with adoption data available):**
```
overall_vendor_health_score = (
  sla_compliance_score × 0.40 +
  support_quality_score × 0.35 +
  adoption_alignment_score × 0.25
)
```

**Assign Renewal Risk Tier:**
| Score | Tier | Recommendation |
|-------|------|-----------------|
| 85–100 | LOW | Renew (good vendor, consider negotiating modest improvements) |
| 70–84 | MEDIUM | Negotiate (vendor has gaps; use data to reduce cost or commit to improvements) |
| 60–69 | HIGH | Negotiate or replace (vendor underperforming; explore alternatives) |
| <60 | CRITICAL | Replace (vendor failing; prioritize replacement plan) |

**Assign Recommended Action:**
- RENEW: Score ≥85 + adoption ≥70% + no SLA breaches
- NEGOTIATE: Score 70–84 + at least one SLA metric below threshold OR adoption 50–69%
- CONSOLIDATE: Score ≥70 but adoption <30% (tool is underutilized; merge with competitor or retire)
- REPLACE: Score <60 OR multiple critical breaches OR adoption <30% AND cost above market median
- PAUSE: Contract expires <30 days; waiting for renewal decision

---

### Step 10: Generate Output Report

**Markdown Report with Scorecard Table:**

```markdown
## Vendor Performance Scorecard Report

**Analysis Period:** [start_date] to [end_date]  
**Date Generated:** [timestamp]  
**Vendors Evaluated:** [count]  
**Overall Summary:** [1–2 sentence summary of key findings]

### Summary Statistics
- Average vendor health score: [X]
- Vendors at risk (HIGH/CRITICAL): [count]
- Vendors with SLA breaches: [count]
- Opportunities for consolidation: [count]
- Estimated annual savings from optimization: $[amount]

### Vendor Scorecard Table
| Vendor | Contract Value | SLA Score | Support Score | Feature Score | Adoption Score | Overall Health | Renewal Risk | Recommended Action |
|--------|---|---|---|---|---|---|---|---|
| Slack | $54,000 | 88 | 82 | 75 | 98 | 86 | LOW | RENEW |
| Salesforce | $180,000 | 92 | 78 | 88 | 65 | 82 | MEDIUM | NEGOTIATE |
| Figma | $28,000 | 72 | 68 | 55 | 28 | 63 | HIGH | CONSOLIDATE |
| [continued...] |

### Detailed Findings (Top Issues)

**HIGH PRIORITY: Vendors at Risk**
- [Vendor name] (Score: 58, Renewal in 32 days)
  - SLA Compliance: 62 (2 uptime breaches in 90 days; total downtime: 14.5 minutes vs. 43.2 minute SLA budget)
  - Support Quality: 44 (Avg response time: 8.2 hours vs. 4-hour SLA; 68% of tickets meet SLA)
  - Adoption: 22% (very low adoption; consolidation candidate)
  - Action: Begin replacement search immediately; contract expires [date]

**MEDIUM PRIORITY: Consolidation Opportunities**
- [Vendor name] (Score: 67, Adoption: 28%)
  - This tool is excellently supported (support score 88) but severely underutilized
  - Active users: 14 of 50 licensed seats; cost per user: $850/year
  - Opportunity: Consolidate into [alternative vendor]; estimated savings: $18,000/year

**COST OPTIMIZATION: Vendors Above Market Pricing**
- [Vendor name]: $420/active user vs. market median $310 (35% premium)
  - Negotiation target: Reduce to market median for 26% annual savings ($16,000)

### Data Quality & Limitations
- **Data freshness:** Contracts updated [X days ago] ✓; Tickets from last 90 days ✓; Status page data current ✓
- **Coverage gaps:** Feature delivery data unavailable for 3 vendors (manual roadmap tracking recommended)
- **Adoption data:** 14 of 18 vendors mapped to TSO-02 (78% coverage); 4 vendors have degraded adoption scoring
- **SLA data quality:** 287 support tickets analyzed; 94% have valid timestamps. 6% excluded due to missing vendor name.
- **Confidence level:** 85% (good data coverage, minor quality gaps)

### Recommended Actions
1. **Immediate (within 2 weeks):** Escalate renewal negotiations for 3 vendors at HIGH/CRITICAL risk; begin replacement evaluation
2. **Short-term (1 month):** Start consolidation process for 2 underutilized vendors (adoption <30%); plan feature roadmap reviews with 4 vendors at MEDIUM risk
3. **Ongoing (quarterly):** Re-run vendor scorecard analysis; feed findings into procurement contract management workflow
4. **Data improvement:** Map remaining 4 tools to TSO-02 adoption data; implement feature delivery tracking for 6 vendors without roadmap data

### Sources & Citations
- Contract data: Salesforce Contract object (pulled [timestamp])
- Support ticket SLA metrics: Salesforce Case object, 90-day window (pulled [timestamp])
- Vendor uptime data: [List status pages queried] (pulled [timestamp])
- Adoption metrics: TSO-02 Agent output (from [date])
- SLA compliance thresholds: Per vendor contract terms in CRM
```

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

**Analysis Scope:**
- "Which vendors? (All, or specific by name?)" — Default: all contracts with SLA terms populated
- "What time window? (30 days, 90 days, 12 months?)" — Default: 90 days
- "Should I exclude any vendors?" — Default: none

**Scoring Weights:**
- "SLA Compliance weight: 40% (default) vs. Support Quality 30% vs. Feature Delivery 20% vs. Adoption 10%?"
  - IT-focused: 50% SLA, 30% support, 10% features, 10% adoption
  - Business-focused: 30% SLA, 20% support, 20% features, 30% adoption

**Renewal Risk Thresholds:**
- "At what health score do you want vendor flagged as HIGH risk?" — Default: 60–69
- "Auto-flag vendors with adoption <30% for consolidation?" — Default: yes

**Output Options:**
- "Write scorecard records to Salesforce/HubSpot CRM?" — Default: yes, analysis-only mode
- "Include detailed feature delivery tracking?" — Default: yes (if roadmap data available)

---

## Error Handling

**If MCP connection fails:**
- Offer to work with CSV exports of contracts and tickets (slower but works offline)
- Provide troubleshooting steps for Salesforce/HubSpot API authentication
- Suggest re-running when connection is restored

**If required contract data is missing:**
- Continue with available vendors; flag limitations in report
- Example: "Found only 4 contracts with SLA terms. Analysis is based on 4 vendors; recommend populating SLA details for remaining X contracts to expand coverage."

**If support ticket data is sparse (<50 tickets per vendor):**
- Flag sample size warning: "Found only 23 tickets for [vendor]. SLA compliance calculations are snapshot-only; recommend collecting ≥90 days of ticket history first."
- Proceed with caution; lower confidence score to 60–70%

**If vendor status page API is unavailable:**
- Fallback to support ticket SLA data as proxy (resolution time approximates incident detection time)
- Warn: "Vendor status page data unavailable. Using support ticket SLA metrics for uptime estimate; this will miss incidents that didn't generate tickets. Accuracy degraded to 70%."
- Ask user to provide manual incident log as CSV

**If adoption data from TSO-02 is missing:**
- Proceed without adoption-alignment scoring
- Warn: "TSO-02 adoption data not available. Vendor scorecard will use SLA + support + feature delivery only (3 factors instead of 4). Adoption-based consolidation recommendations unavailable."
- Offer to re-run once TSO-02 is executed

**If feature delivery data is unavailable:**
- Exclude feature delivery from overall health score calculation
- Warn: "Feature delivery data unavailable for [count] vendors. Scorecard uses SLA + support + adoption only. Recommend tracking vendor roadmaps manually or via API."

**If data quality is too low to proceed:**
- <5 contracts: Refuse to proceed. "I need at least 5 vendor contracts with populated SLA terms. Please configure contracts first."
- <30 support tickets total: Refuse to proceed. "I need ≥30 support tickets across all vendors to calculate reliable SLA metrics. Please collect ticket history first."
- <50% adoption data coverage: Proceed with degraded output. "Only 30% of tools mapped to adoption data. Scorecard will have limited adoption-alignment insights. Recommend running TSO-02 first."

---

## What to Run Next

After vendor performance analysis is complete:

1. **TSO-01: Tool Spend Analysis Agent** — Correlate vendor health scores with spend; identify spend-to-performance mismatches and cost-optimization opportunities.

2. **Renewal Management Agent** (future) — Use vendor health scores to prioritize contract negotiations; generate data-driven renewal proposals with benchmarked pricing targets.

3. **Procurement Optimization Agent** (future) — Use consolidation recommendations from TSO-03 to guide vendor rationalization roadmap; plan migrations away from low-health vendors.

4. **Quarterly Vendor Scorecard Run** — Schedule TSO-03 to run quarterly; track vendor health trends over time; identify vendors with improving vs. declining performance.

---

## Example: End-to-End Vendor Scorecard Session

**You:** "Evaluate our SaaS vendor ecosystem. Tell me which vendors to renew, which to renegotiate, and which to replace."

**Me (Preflight):**
```
✓ Salesforce MCP connected (Enterprise license)
✓ Found 18 vendor contracts with SLA terms populated
✓ Support ticket data: 287 tickets in last 90 days (94% have valid timestamps)
✓ Vendor status page access: Slack, Salesforce, AWS, Figma (4 of 18 vendors)
✓ TSO-02 adoption data available; 14 of 18 vendors mapped (78% coverage)
✓ Ready to analyze all 18 vendors for 90-day window
```

**You:** "Go ahead. Include everything."

**Me (Analysis):**
```
Fetching contract data... ✓ 18 contracts loaded
Fetching support tickets... ✓ 287 tickets analyzed
Fetching vendor incident data... ✓ 4 vendors with status page API; 14 without (using ticket SLA as proxy)
Calculating SLA compliance... ✓ Completed
Calculating support quality... ✓ Completed
Calculating feature delivery... ⚠️ 6 vendors without roadmap data; feature score unavailable
Calculating adoption alignment... ✓ 14 vendors mapped; 4 with degraded scoring
Generating vendor scorecards... ✓ Completed
```

**Report Generated:**
```
## Summary

Analyzed 18 vendors over 90 days. Average health score: 74. 
3 vendors at HIGH/CRITICAL risk (score <70); 2 consolidation opportunities (low adoption + high cost).
Estimated annual savings from optimization: $85,000–$125,000.

### Actionable Findings

CRITICAL: Figma (Score: 58, Renewal: 32 days)
- SLA breaches: 1 incident, 2.5 hours unplanned downtime
- Support quality: 44 (response time 8.2h vs 4h SLA)
- Adoption: 22% (very low; 11 of 50 users active)
- Action: Begin replacement search immediately

MEDIUM: Asana (Score: 72, Adoption: 28%)
- Good SLA compliance (88) and support (75), but severely underutilized
- Cost: $420/active user vs. market median $280
- Action: Either increase adoption or consolidate into Monday.com (competitor with 85% adoption at your org)

NEGOTIATE: Salesforce (Score: 78, Renewal: 4 months)
- SLA score strong (92) but support quality below target (78)
- Adoption: 65% (moderate; opportunity to drive deeper use)
- Market cost: $8/user/month; you're paying $12/user (50% premium)
- Action: Negotiate 25% discount based on adoption insights + support SLA targets
```

**You:** "Perfect. Replace Figma with Sketch, and consult with the Asana team about consolidation. Do it."

**Me:** "I've written scorecard records to Salesforce. You now have documented vendor performance data for renewal negotiations. Begin Figma replacement evaluation with IT team. For Asana consolidation, I recommend scheduling a 30-minute alignment meeting with your product and engineering leaders to review adoption data and consolidation ROI."

---

## References & Further Reading

**Inside the Agent:**
- SLA compliance calculations follow industry-standard formulas from TechTarget and Postman SLA monitoring guides
- Feature delivery scoring based on roadmap tracking best practices from Vendr and Productiv vendor management platforms
- Adoption alignment methodology integrates TSO-02 adoption data using standard adoption cohort analysis

**Benchmarking Data Sources:**
- Median cost-per-active-user for each tool category: drawn from Vendr Benchmarks, Productiv Intelligence Reports (2025)
- Industry SLA standards (e.g., 99.9% uptime for enterprise SaaS): per SLA best practices from IDC, Gartner
- Support response/resolution time benchmarks: derived from data shared by 2,400+ organizations surveyed in SpenFlo 2025 SaaS Management Index

**Related Tools & Comparisons:**
- Vendr: Vendor management platform (static contract data + benchmarking; lacks real-time SLA + feature tracking)
- Productiv: SaaS intelligence (strong adoption metrics; lacks SLA compliance + feature delivery)
- New Relic/Datadog: Application performance monitoring (excellent for single-vendor uptime; not cross-vendor aggregation)
- Manual tracking: Spreadsheets + Slack (no scalability; SLA breaches go undetected)

