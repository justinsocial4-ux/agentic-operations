---
name: revops-segment-performance
description: Analyzes revenue performance (win rate, pipeline velocity, ACV, cycle
  time) across customer segments (industry, company size, geography, ACV tier). Produces
  quarterly health scorecards and weekly drift detection. Depends on IMS-01 ICP definition.
metadata:
  trigger_phrases:
  - analyze segment performance
  - compare segments by win rate
  - check segment health
  - segment performance report
  - which segments are underperforming
  - identify declining segments
  - segment revenue trends
  - detect segment drift
  category: ICP & Market Strategy
  phase: 30_days
  data_readiness: 30_days
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents:
    - revops-icp-development
    mcps:
    - Salesforce MCP (Salesforce orgs)
    - HubSpot MCP (HubSpot orgs)
    - Snowflake MCP (optional; enables weekly drift detection)
    minimum_data:
    - 'Opportunities (closed) with: Close Date, Amount, Account ID, Is Won, Stage'
    - 'Accounts/Companies with: Industry, Annual Revenue, Employee Count, Geography
      (Country/State)'
    - 'Contacts with: Email, Phone, First Name, Last Name, Account/Company ID'
    - 'IMS-01 output: ICP definition JSON with segment filters and deal characteristics'
    - 12+ months of closed-deal history
  output_format: markdown
---

# Segment Performance Agent

## Why This Agent Exists

**Who it's for:** RevOps Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Segment Performance Opacity
- **Problem:** Without segment-level visibility, teams continue allocating resources to underperforming or declining segments while missing emerging high-value niches.
- **Quantified cost to the role:** B2B organizations lose ~$1T annually due to poor alignment; for mid-market (~$5M ARR) = $250K–$500K/year leakage. RevOps teams spend 15–20% of time on segment analysis = $15.6K–$24.96K/year per FTE.
- **What teams do today:** Quarterly manual reporting (2–4 weeks/quarter at 40–80 hours = $2.4K–$4.8K/quarter). Consultants ($5K–$15K/quarter). ABM tools ($60K–$150K/year).
- **Why it's urgent:** Underperforming segment consuming 20% of sales capacity but generating 8% of revenue = $240K–$400K/year waste. Over 24 months = $500K–$1.2M total cost.
- **Evidence quality:** 4/4 rubric criteria passed, 4 TIER 1 sources

### Pain Point 2: Segment Drift Undetected 4–8 Weeks
- **Problem:** Market shifts change segment profitability quarterly. Detection lag = 4–8 weeks, causing continued investment in declining segments and missing emerging opportunities.
- **Quantified cost to the role:** 4–8 week lag = 3–6 missed deals/quarter = $75K–$150K lost pipeline/quarter = $300K–$600K/year prevention value.
- **What teams do today:** Manual monthly spot-checks (3–5 hours/month = $2.16K–$3.6K/year labor). Re-plan GTM every 8 weeks, often reactively. Some use ABM tools to surface trends.
- **Why it's urgent:** High-value segment (e.g., Financial Services 35% win rate) underinvested for 8 weeks = ~$100K/quarter missed × 4 = $400K/year.
- **Evidence quality:** 4/4 rubric criteria passed, 3 TIER 1 sources

### Pain Point 3: Manual Analysis 8–12 Weeks per Quarter
- **Problem:** Manual CRM pulls, sample-based analysis (10–30 deals/segment), spreadsheet reconciliation take 8–12 weeks per quarter. Causes delays in GTM replans.
- **Quantified cost to the role:** 320–480 hours/year RevOps FTE time = $19.2K–$28.8K/year per analyst; team of 3–4 = $210K–$360K/year. 8-week planning delay @ 30% growth = $150K–$300K missed revenue/quarter. Over 2 years = $1.2M–$2.4M missed growth.
- **What teams do today:** Build ad-hoc CRM queries, maintain pivot table templates, manually segment by industry/size. Hire analysts or use consultants to accelerate.
- **Why it's urgent:** Sales leadership makes GTM decisions based on stale data. Market shifts (e.g., competitors enter vertical, customer budget cuts) go undetected.
- **Evidence quality:** 4/4 rubric criteria passed, 3 TIER 1 sources

### Pain Point 4: Forecast Accuracy Poor Without Segment Isolation
- **Problem:** Blended forecasts (not segmented by win rate, velocity) degrade accuracy from 85% to 50–70%, causing missed targets and board credibility loss.
- **Quantified cost to the role:** 15% forecast miss on $5M ARR = $750K/quarter variance. Repeated misses cost $50K–$100K in comp rework + unplanned hiring cycles = $200K–$400K/4 quarters. 20pp accuracy gap = $1M/quarter variance on $5M ARR = $4M/year cumulative.
- **What teams do today:** Hire data analysts ($80K–$120K/year) or forecasting specialists. Purchase forecasting software (Forecastio, Spiff: $15K–$40K/year). Re-forecast monthly (36K–$54K/year labor).
- **Why it's urgent:** Board expects accurate quarterly forecasts; misses erode executive credibility and cause reactive hiring/firing cycles.
- **Evidence quality:** 4/4 rubric criteria passed, 3 TIER 1 sources

---

## What This Agent Does

The Segment Performance Agent analyzes revenue metrics—win rate, pipeline velocity, forecast accuracy, ACV, and sales cycle time—across your customer segments (industry vertical, company size, geography, ACV tier). It consumes the ICP definition from IMS-01 and produces **quarterly health scorecards** showing which segments are growing, declining, or underperforming relative to company average and historical trends. It also runs **weekly drift detection** to flag when key metrics shift >10 percentage points (win rate), >15 days (cycle time), or >$50K (ACV).

Unlike manual quarterly reporting (8–12 weeks, sample-based), this agent delivers full-population analysis within 1–2 weeks of quarter-end. Unlike ABM platforms (designed for marketing), it optimizes for RevOps: segment-level forecast accuracy improvement, sales capacity allocation, and pipeline quality.

**Primary use case:** RevOps Manager discovers that a historically strong vertical (e.g., Financial Services) has slipped from 35% win rate to 28% and is losing to competitors. Agent flags this automatically within 1 week and recommends GTM intervention (reposition, reduce allocation, investigate product-market fit).

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your CRM connection, confirm required data exists, assess data quality, and ask you to scope your analysis.

**Step 1: Dependency Verification**
- I'll check if IMS-01 (ICP Development Agent) has run and produced an ICP definition. This is **required** to segment your analysis.
- If IMS-01 hasn't run, I'll ask: "Should I run IMS-01 first, or do you have an ICP definition you'd like to provide?"

**Step 2: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: export recent opportunities to CSV for analysis, or help you troubleshoot the MCP connection.
- **If successful:** Proceed to Step 3.

**Step 3: Required Data Validation**
I'll verify that your CRM has:
- Opportunity object with: Close Date, Amount, Account ID, Is Won, Stage (required)
- Account/Company object with: Industry, Annual Revenue, Employee Count, Geography (at least 80% populated)
- 12+ months of closed-deal history (required for trend analysis)

**Go/No-Go decision:**
- ✓ IMS-01 defined, CRM connected, 12+ months closed deals → Proceed
- ⚠️ IMS-01 missing → Ask you to run it first, or provide ICP definition manually
- ⚠️ 6–12 months closed deals → Proceed with degraded trend analysis (month-to-month only, not year-over-year)
- ✗ <6 months closed deals → No-go; request more historical data first

**Step 4: Data Quality Assessment**
I'll calculate:
- % of closed opportunities with valid amounts (should be >95%)
- % of accounts with industry populated (should be >80%)
- % of accounts with employee count or revenue (should be >70%)
- Current win/loss ratio (flag if >90% won/lost, indicates pipeline bias)
- Estimated duplicate rate (sample ~500 records; extrapolate)

**Step 5: Define Your Analysis Scope**
Before running the analysis, I'll ask:
- "Do you want quarterly analysis, weekly drift detection, or both?"
- "Any segments you want to exclude? (e.g., 'don't analyze Federal government segment; it's governed separately')"
- "Should I use custom segment fields (Vertical__c, ACV_Tier__c) if they exist, or derive segments from ICP + employee-count tiers?"

**Preflight Report**
I'll summarize:
```
✓ IMS-01 dependency: ICP definition found (created 2026-04-13)
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Closed opportunities (12-month window): 247 records
  ├─ Completeness: 89% (23 missing amounts flagged)
  ├─ Industry populated: 82% ✓
  └─ Employee count populated: 71% ✓
✓ Win/loss ratio: 34% won, 66% lost (reasonable skew)
⚠️ Data quality: 11% of amounts missing; win-rate estimates will use median ACV
? Segment custom fields: Not found; will segment using ICP industries + employee-count tiers

Confidence: 82% | Proceed? [Yes / Get more data first / Run IMS-01 first]
```

---

## Step-by-Step Workflow

### Step 1: Fetch & Normalize Closed Opportunities

**What I'll do:**
- Query Opportunity object for last 12–24 months of closed deals (closed-won or closed-lost)
- Fetch related Account/Company and Contact records
- Batch queries in 1,000-record increments to respect API limits

**Data fetched from each opportunity:**
- `Id`, `AccountId`, `Amount`, `CloseDate`, `IsClosed`, `IsWon`, `StageName` (required)
- `Account.Industry`, `Account.AnnualRevenue`, `Account.NumberOfEmployees`, `Account.BillingCountry` (required)
- `CreatedDate`, `CreatedBy`, `Owner` (for audit + rep performance later)
- Optional custom fields: `Segment__c`, `Vertical__c`, `ACV_Tier__c` (if defined)

**Data normalization:**
- Validate dates (must be in past and ≥6 months ago for historical comparison)
- Validate amounts (numeric, >0, flag amounts that are placeholders or TBD)
- Validate industry (denylist: "unknown", "TBD", "other"; trim whitespace)
- Normalize country codes to ISO 3166-1
- Calculate deal duration: `CloseDate - CreatedDate` = sales cycle in days

**Output:** Normalized opportunity dataset with metadata (total records, % completeness, data quality flags)

---

### Step 2: Apply ICP Filters & Segment Each Opportunity

**What I'll do:**
- Load ICP definition from IMS-01 (includes industries, revenue ranges, employee-count ranges, geographies)
- For each opportunity, determine which ICP segment it belongs to using ICP filters
- If custom segment fields exist (Vertical__c), cross-validate with ICP segments; flag discrepancies

**Segmentation logic:**
- Match on: Industry (exact or fuzzy), Annual Revenue range, Employee Count range, Geography
- Example: Opportunity for SaaS company, $150M revenue, 500 employees, US → matches "Mid-Market SaaS, US" segment
- If account doesn't match ICP → classify as "Out of ICP" (important for forecast accuracy)
- If account matches multiple segments (rare) → assign to highest-specificity segment

**Output:** Each opportunity labeled with:
- `segment_name` (e.g., "Mid-Market SaaS, US")
- `segment_match_confidence` (0–100%, high if matches ICP exactly)
- `is_in_icp` (boolean)
- `is_in_icp_win_rate_banding` (for forecast banding later)

---

### Step 3: Calculate Base Segment Metrics

**For each segment, calculate:**

**Opportunity Metrics:**
- `total_opportunities` (won + lost in segment, 12-month window)
- `total_opportunities_won` (# closed-won)
- `total_opportunities_lost` (# closed-lost)
- `win_rate` = won / (won + lost) × 100%

**Financial Metrics:**
- `total_acv_won` (sum of amount for all closed-won opps)
- `total_acv_lost` (sum of amount for all closed-lost opps)
- `median_acv_won` (middle value of won amounts; more robust than mean)
- `median_acv_lost`
- `average_acv_won` (mean, flagged if skewed by outliers)

**Velocity & Cycle Time:**
- `median_sales_cycle_days` (median CloseDate - CreatedDate for all closed opps)
- `median_sales_cycle_won` (median for closed-won only; faster = better execution)
- `median_sales_cycle_lost` (median for closed-lost; longer = stalled deals)

**Forecast Accuracy (if historical forecast data available):**
- `forecast_accuracy_pct` = (actual_closed / forecasted) × 100%
- `forecast_accuracy_by_stage` (e.g., "70% of opps in 'Proposal' stage close within 30 days")

**Engagement Metrics (if activity data available):**
- `avg_activities_per_opp_won` (calls, emails, meetings for won deals)
- `avg_activities_per_opp_lost` (activities for lost deals)
- Activity ratio = activities_won / activities_lost

**Data Quality Flags Per Segment:**
- `% missing amounts` (if >5%, flag confidence as degraded)
- `sample size` (if <20 opps, mark as "too small for reliable trend")
- `recency` (e.g., "20% of closed opps are >18 months old; analysis skewed to older deals")

**Output:** Base metrics table (one row per segment)

---

### Step 4: Calculate Trend Analysis (Quarterly YoY)

**What I'll do:**
- Divide 12-month history into quarters (Q1, Q2, Q3, Q4 of current year, same quarters prior year if available)
- Recalculate win rate, ACV, cycle time for each quarter
- Calculate trend: `this_quarter - last_quarter` (acceleration/deceleration)

**Trend Calculations:**
- `win_rate_trend` = current_q_win_rate - prior_q_win_rate (e.g., -5pp = declining)
- `acv_trend` = current_q_avg_acv - prior_q_avg_acv (e.g., +$50K = increasing deal size)
- `cycle_time_trend` = current_q_median_cycle - prior_q_median_cycle (e.g., +10 days = deals stalling)
- `trend_direction` (↑ improving, ↓ declining, → flat)
- `trend_velocity` (accelerating if trend worsening across 2+ quarters, decelerating if stabilizing)

**Example Trend Output:**
| Segment | Q1 Win Rate | Q2 Win Rate | Trend | Velocity |
|---------|-------------|-------------|-------|----------|
| Mid-Market SaaS, US | 38% | 35% | -3pp ↓ | Accelerating (Q0: 40%) |
| Enterprise FinTech | 25% | 28% | +3pp ↑ | Stabilizing |

**Output:** Trend analysis table; flag segments with >10pp adverse drift

---

### Step 5: Benchmark Against Company Average & ICP Baseline

**What I'll do:**
- Calculate company-wide average metrics (blended across all segments)
- Compare each segment's performance vs. company average and ICP expected metrics (from IMS-01)

**Benchmark Calculations:**
- `segment_win_rate_vs_company_avg` (e.g., "34% segment vs. 28% company = +6pp better")
- `segment_acv_vs_company_avg`
- `segment_cycle_time_vs_company_avg`
- `segment_vs_icp_baseline` (e.g., "32% segment win rate vs. ICP-forecasted 35% = -3pp below target")

**Percentile Ranking:**
- Rank all segments by win rate, ACV, cycle time (e.g., "Rank 1 of 8 in win rate")
- Highlight top and bottom performers

**Output:** Benchmark comparison table; identify outliers (high/low performers)

---

### Step 6: Apply Risk & Opportunity Flags

**High-Risk Flags (Segment Needs Intervention):**
- 🚨 **Declining Win Rate:** >10pp drop over last 2 quarters
- 🚨 **Cycle Time Slipping:** >15 days increase in sales cycle (indicates deal stalls)
- 🚨 **Shrinking ACV:** >$50K decline in median deal size (product-market fit concern)
- ⚠️ **Below ICP Baseline:** Segment performing >5pp below ICP forecast (execution issue or wrong positioning)
- ⚠️ **Below Company Average:** >10pp win rate gap vs. company (either segment is weak or company avg is inflated)
- ⚠️ **Small Sample:** <20 closed opps in segment (results not reliable; increase sample before acting)

**High-Opportunity Flags (Segment to Invest In):**
- ✅ **Emerging Growth:** Win rate improving >5pp over last 2 quarters
- ✅ **Above Baseline:** Segment performing >5pp above ICP forecast (market fit strong)
- ✅ **Large ACV:** >$50K above company average (high-value segment; should prioritize)
- ✅ **Short Cycle:** <60 days (predictable, fast execution; less execution risk)

**Output:** Risk/opportunity scorecard per segment; recommendations

---

### Step 7: Produce Quarterly Health Scorecard Report

**Markdown Report with:**

**Summary**
- Total segments analyzed: _X_
- Segments improving: _Y_ (with % change)
- Segments declining: _Z_ (with % change)
- Overall company win rate: _A%_
- Overall company median ACV: _$B_
- Overall company median cycle time: _C_ days

**Executive Dashboard**
| Segment | Win Rate | ACV | Cycle Days | Trend | Benchmark | Risk Level | Action |
|---------|----------|-----|------------|-------|-----------|-----------|--------|
| Mid-Market SaaS, US | 34% | $125K | 82 | -5pp ↓ | +6pp vs. company | 🚨 HIGH | Investigate market shift; reposition |
| Enterprise FinTech | 28% | $180K | 95 | +3pp ↑ | -2pp vs. baseline | 🟡 MEDIUM | Sustained improvement; monitor |
| SMB Europe | 42% | $45K | 60 | → flat | +14pp vs. company | ✅ LOW | High performer; consider expansion |

**Segment Deep Dive (for top 3 segments by revenue or risk)**
- Segment name & filters (industry, geography, size)
- Historical metrics: 12-month YoY win rate, ACV, cycle time
- Quarterly trend: Q1 → Q4 performance trajectory
- Forecast accuracy: % of deals closed on/before forecast date
- Engagement: avg activities per opp (high engagement = more sales motion)
- Competitive positioning: Any evidence of competitive loss? (from deal notes if available)
- Recommended GTM action: Reposition, increase/decrease allocation, investigate product-market fit, etc.

**Data Quality & Limitations**
- Records analyzed: 247 closed opportunities over 12 months
- Data completeness: 89% (11% missing amounts; used median ACV for estimates)
- Segments with <20 opps flagged as "unreliable sample size"
- Assumptions: Industry field is source of truth; Company size based on employee count (not revenue)
- Missing data: No custom Vertical__c field; agent derived segments from ICP + employee tiers
- Forecast data not available from CRM (cannot validate forecast accuracy vs. CRM forecast date)

**Recommended Actions (Top 5)**
1. **Immediate:** Mid-Market SaaS win rate declined 5pp in Q2. Root cause: [from deal notes / lost reason analysis]. Recommend: re-validate positioning, interview 3 lost customers, assess competitive threat.
2. **Near-term (2 weeks):** Increase allocation to SMB Europe (42% win rate, +14pp vs. company average). Segment underserved relative to opportunity.
3. **Near-term (2 weeks):** Investigate cycle time creep in Enterprise segment (now 95 days vs. ICP baseline 85 days). Longer cycle = higher carry costs, lower forecast confidence.
4. **Ongoing:** Set up weekly drift detection for high-value segments (Mid-Market SaaS, Enterprise) to catch further shifts early.
5. **Planning (next month):** Segment-based forecast model: Replace blended forecast with segment-weighted model using these win rates. Expect forecast accuracy to improve from 75% to 85%+.

**Sources & Citations**
- Data pulled from Salesforce (org: EXAMPLE_ORG_ID) on 2026-04-13
- 12-month window: 2025-04-13 to 2026-04-13
- ICP definition from IMS-01 (created 2026-04-13)
- Benchmark data: Company historical average (last 24 months)
- Win rate methodology: (Closed-Won) / (Closed-Won + Closed-Lost)
- Cycle time: Median of (CloseDate - CreatedDate) for all closed opps in segment

---

## Weekly Drift Detection (Optional)

Once quarterly analysis is complete, I can set up **weekly monitoring** that flags segment metric shifts:

**Drift Thresholds (flag if exceeded):**
- Win rate shift: >10 percentage points (e.g., 34% → 24%)
- ACV shift: >$50K (e.g., $125K → $75K)
- Cycle time shift: >15 days (e.g., 82 days → 97 days)
- Sample size: <5 new closed opps this week (too small; hold flag for next week)

**Weekly Report Format (Slack or email):**
```
📊 Weekly Segment Drift Report (Week of Apr 13–19, 2026)

⚠️ Alert: Mid-Market SaaS win rate declined 12pp (34% → 22%)
  • 8 closed opps this week: 2 won, 6 lost
  • Compare to prior 4-week avg: 38% win rate
  • Action: Review lost deal reasons; schedule 1:1 with Mid-Market AE manager

✅ No other segments exceeded drift thresholds

Next full analysis: May 15, 2026 (end of Q2)
```

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

**Analysis Scope:**
- "Do you want quarterly analysis, weekly drift detection, or both?" (Default: Quarterly only)
- "Limit to specific segments, geographies, or account size bands?" (Default: all)
- "Exclude any accounts/segments?" (Default: none)

**Segment Derivation:**
- "Use custom Vertical__c / ACV_Tier__c fields if they exist?" (Default: Yes, cross-validate against ICP)
- "If custom fields don't exist, derive segments from [Industry + Employee Count] or [Industry + Revenue]?" (Default: Employee Count)

**Metric Focus:**
- "Prioritize win rate, ACV, or cycle time?" (Default: all equally weighted)
- "Include forecast accuracy analysis?" (Default: Yes if forecast data available)
- "Include engagement metrics (activity count)?" (Default: Yes if activity data available)

**Threshold Tuning:**
- "Minimum sample size before flagging segment as unreliable?" (Default: 20 closed opps)
- "Drift detection threshold for win rate?" (Default: >10pp)
- "Drift detection threshold for ACV?" (Default: >$50K)
- "Drift detection threshold for cycle time?" (Default: >15 days)

**Reporting:**
- "Which 3 segments should get deep-dive analysis in report?" (Default: top 3 by revenue)
- "Include competitive loss analysis?" (Default: Yes, if deal notes contain competitor mentions)

---

## Error Handling

**If IMS-01 dependency is not available:**
- I'll ask: "Should I run IMS-01 first, or do you have an ICP definition (JSON) you'd like to provide?"
- If you provide ICP manually, I'll proceed with that definition
- If you want to run IMS-01 first, I'll guide you to that agent

**If MCP connection fails:**
- Offer to work with CSV export (slower but works offline)
- Provide troubleshooting steps for the MCP (API key, permissions, org ID)
- If you can't reconnect, I'll proceed with manual data import

**If required data is missing or incomplete:**
- Continue with available data; flag limitations clearly in report
- Example: "No Industry field populated → can only segment by geography + company size (confidence drops to 65%)"
- If <12 months closed deals: Proceed with month-to-month trend analysis (quarter-over-quarter not possible)
- If >20% of amounts missing: Calculate win rate normally, but flag ACV metrics as degraded (use median instead of mean)

**If data quality is too low:**
- Assess completeness score (% of required fields populated)
- >80% completeness → Proceed with full analysis; flag the 20% gap
- 50–80% completeness → Proceed with degraded analysis; lower confidence score (60–70%)
- <50% completeness → Refuse to proceed; explain why (too unreliable) and what data cleaning is needed

**If API rate limits are hit:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (500 records instead of 1,000)
- Split into multiple runs (analyze different date ranges separately)

**If sample size is too small:**
- Segment with <5 closed opps: Flag as "insufficient sample; results unreliable"
- Segment with 5–19 closed opps: Flag as "small sample; use with caution"
- Segment with 20+ opps: Proceed with full analysis (minimum confidence met)

---

## What to Run Next

After segment analysis is complete:

1. **IMS-04: Account Scoring Agent** — Uses segment win-rate binning rules from IMS-03 to improve account prioritization. Segment-level confidence scores boost overall account ranking.

2. **EM-SELECT-01: Event Selection & Scoring Agent** — Uses segment performance trends to identify high-growth, high-engagement vertical(s) for event sponsorship and targeting.

3. **Set Up Recurring Analysis** — Schedule monthly segment refreshes (lightweight) and quarterly full analyses to track ongoing performance. Use weekly drift detection for early warning.

4. **Build Segment-Based Forecast Model** — Replace blended forecast with segment-weighted model using these win rates. Expected forecast accuracy improvement: 75% → 85%+.

5. **Adjust Sales Capacity Allocation** — Use segment performance data (win rate, ACV, cycle time) to recommend optimal rep assignments and territory planning per segment.

---

## Worked Example: End-to-End Segment Analysis

**You:** "Analyze segment performance for my Salesforce org. I want to know which customer segments are strong and which are weak."

**Me (Preflight):**
```
✓ IMS-01 dependency: ICP definition found (created 2026-04-13)
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Closed opportunities (12-month window): 247 records
  ├─ Completeness: 89% (23 missing amounts flagged)
  ├─ Industry populated: 82% ✓
  └─ Employee count populated: 71% ✓
✓ Win/loss ratio: 34% won, 66% lost (reasonable skew)

Data quality: Good. Ready to proceed with quarterly analysis.
```

**You:** "Yes, run the full analysis. Include weekly drift detection."

**Me (Analysis):**
```
Fetching 247 closed opportunities (12-month window)...
✓ Fetched 247 records from Salesforce
✓ Normalized dates, amounts, industry, company size

Applying ICP filters and segmenting...
✓ Mapped 247 opps to 6 ICP segments
✓ Found 18 opps outside ICP (reviewed separately)

Calculating base metrics by segment...
✓ Mid-Market SaaS, US: 82 opps, 34% win rate, $125K median ACV, 82-day cycle
✓ Enterprise FinTech: 45 opps, 28% win rate, $180K median ACV, 95-day cycle
✓ SMB Europe: 38 opps, 42% win rate, $45K median ACV, 60-day cycle
✓ 3 additional segments calculated

Calculating quarterly trends...
✓ Mid-Market SaaS: Q1 38% → Q2 35% (-3pp declining)
✓ SMB Europe: Q1 40% → Q2 42% (+2pp improving)

Benchmarking against company average and ICP baseline...
✓ Company blended win rate: 28%
✓ Mid-Market SaaS: 34% (+6pp vs. company, +2pp vs. ICP baseline)
✓ Enterprise FinTech: 28% (on target vs. ICP)
✓ SMB Europe: 42% (+14pp vs. company, strong outperformer)

Generating health scorecard...
✓ Report ready
```

**Report (Key Sections):**

**Summary**
- Total segments: 6 ICP segments + 1 "Out of ICP" cohort (18 opps)
- Segments improving: 2 (SMB Europe, Mid-Market UK)
- Segments declining: 1 (Mid-Market SaaS, -5pp trend)
- Company win rate: 28% | Median ACV: $95K | Median cycle: 85 days

**Executive Scorecard**
| Segment | Win Rate | ACV | Cycle | Trend | vs. Baseline | Risk | Action |
|---------|----------|-----|-------|-------|--------------|------|--------|
| SMB Europe | 42% | $45K | 60d | +2pp ↑ | +7pp | ✅ LOW | Invest more; underserved |
| Mid-Market SaaS, US | 34% | $125K | 82d | -5pp ↓ | +2pp | 🚨 HIGH | Investigate market shift |
| Enterprise FinTech | 28% | $180K | 95d | +3pp ↑ | -7pp | 🟡 MEDIUM | Improve execution speed |
| Mid-Market UK | 31% | $110K | 88d | +4pp ↑ | -4pp | 🟡 MEDIUM | New growth signal |

**Recommended Actions**
1. Investigate Mid-Market SaaS decline (5pp in 2 quarters). Schedule call with top AE in segment to root-cause lost deals.
2. Increase SMB Europe allocation (42% win rate, 14pp above company avg). Segment is underserved relative to win rate.
3. Reduce Enterprise FinTech deal size expectations (median ACV $180K but only 28% win rate). Longer cycle (95 days) indicates execution issues.
4. Monitor Mid-Market UK (new growth trend; could indicate market expansion opportunity).
5. Enable weekly drift detection on Mid-Market SaaS and Enterprise FinTech to catch further metric shifts early.

**You:** "This is helpful. Let's enable weekly drift detection starting next week and run next quarterly analysis at end of Q2."

**Me:** "Setting up weekly drift detection for Mid-Market SaaS and Enterprise FinTech. You'll get a brief report every Monday showing metric shifts >10pp (win rate), >$50K (ACV), or >15 days (cycle time). Next full quarterly analysis scheduled for May 15, 2026."

---

## Advanced Topics (Optional)

### Forecast Accuracy Validation

If your CRM stores forecast data (e.g., forecasted close date, forecasted amount), I can calculate:
- **Forecast accuracy by segment:** Which segments hit forecast dates most often?
- **Bias detection:** Does your sales team consistently overestimate (forecast too optimistic) or underestimate (forecast too conservative) by segment?
- **Stage-based forecast confidence:** "Deals in Proposal stage close within 30 days 70% of the time in your org; use this to weight forecast."

### Competitive Loss Analysis

If your CRM tracks competitor names in lost deal records (e.g., "Lost to Competitor__c" field), I can:
- **Identify which competitors are winning in each segment**
- **Flag if competitive loss rate is increasing** (indicates market threat)
- **Recommend repositioning** based on who you're losing to

### Sales Rep Performance by Segment

If you want to see which reps excel in each segment:
- Calculate win rate, ACV, cycle time per rep per segment
- Identify rep strengths (e.g., "Jane has 52% win rate in Enterprise; assign her Enterprise deals")
- Flag reps struggling in high-value segments (coaching opportunity)

---

## Config & Sources

**Config Files (in `references/` folder):**
- `segment_thresholds.md` — Drift detection thresholds (adjustable)
- `icp_integration.md` — How to import ICP definition from IMS-01
- `forecast_accuracy_model.md` — Advanced forecasting validation
- `competitive_loss_tracking.md` — Competitor loss analysis

**Data Sources:**
- CRM: Opportunity, Account, Contact, Activity objects (via Salesforce or HubSpot MCP)
- Optional warehouse: Snowflake pre-computed segment aggregations (faster weekly drift detection)
- IMS-01 output: ICP definition JSON

**Methodology & Benchmarks:**
- Win rate: (Closed-Won) / (Closed-Won + Closed-Lost)
- Sales cycle: Median of (CloseDate - CreatedDate) for closed opps
- ACV: Median of Opportunity Amount (more robust than mean; ignores outliers)
- Trend: Quarter-over-quarter YoY comparison (requires 12+ month history)
- Drift thresholds: 10pp (win rate), $50K (ACV), 15 days (cycle), tunable per org
