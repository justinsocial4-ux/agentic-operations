---
name: revops-icp-development
description: Analyzes closed-won and closed-lost opportunities with firmographic data
  to define or continuously refine your Ideal Customer Profile. Identifies patterns
  in deal success, size, velocity, and retention. Detects quarterly ICP drift with
  statistical confidence scores.
metadata:
  trigger_phrases:
  - define my ideal customer profile
  - analyze my icp
  - refine icp from deal data
  - what is my ideal customer
  - icp drift analysis
  - customer profile development
  - win loss icp analysis
  - quarterly icp review
  - firmographic icp patterns
  category: ICP & Market Strategy
  phase: day_1
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents: []
    mcps:
    - Salesforce MCP (Salesforce orgs)
    - HubSpot MCP (HubSpot orgs)
    minimum_data:
    - 'Opportunity object: Close Date, Amount, Is Won (or Deal Stage), Account ID'
    - 'Account/Company object: Industry, Annual Revenue, Employee Count'
    - 'Contact object: Email, Phone, First Name, Last Name'
    - 'Closed-deal cohort: minimum 15–30 deals in last 12 months'
  output_format: markdown
---

# IMS-01 ICP Development Agent

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Undefined or Vague ICP Causes Sales Reps to Chase Poor-Fit Accounts, Wasting 20–30% of Pipeline Activity
- **Problem:** Without clear, operationalized ICP, sales reps develop competing models, wasting 20–30% of pipeline activity on poor-fit prospects.
- **Quantified cost:** $30K ARR/FTE annually. [Apollo](https://www.apollo.io/insights/icp-meaning-sales); [Digital Bloom](https://thedigitalbloom.com/learn/pipeline-performance-benchmarks-2025/)
- **What teams do today:** Manual interviews, win/loss spreadsheets, CRM reports. Cost: $5,760–$11,520/year/FTE. [Pavilion](https://www.revopscoop.com/reports/the-2025-state-of-revops-survey)
- **Why urgent:** Over 24 months, ACV down 20%, churn up 10–15pp, revenue underperforms 15–25%. [CXL](https://cxl.com/blog/define-your-b2b-icp/); [Right Left](https://rightleftagency.com/ideal-customer-profile/)
- **Evidence:** 4/4 rubric criteria; 8 TIER 1 sources

### Pain Point 2: Quarterly ICP Drift Not Detected (4–8 Week Lag)
- **Problem:** Market shifts change ICP quarterly. Drift detected 4–8 weeks after deals close, causing misalignment.
- **Quantified cost:** 4–8 week lag wastes 20–30% SDR outbound activity = ~$11,500 labor. [Apollo](https://www.apollo.io/insights/icp-meaning-sales)
- **What teams do today:** Manual quarterly tracking, hand-run CRM reports, consultants ($5–15K/quarter), ABM tools ($60K–$150K/year). Cost: $5,769/quarter labor. [Prospeo](https://prospeo.io/s/demandbase-vs-6sense); [HockeyStack](https://www.hockeystack.com/blog-posts/6sense-vs-demandbase)
- **Why urgent:** By 12 months, ICP obsolete, forcing reactive reboot ($10K–$25K + 4–6 weeks). Cost is 5–10x higher than automated monitoring. [Demandzen](https://demandzen.com/knowledge-relay-ideal-customer-profile-icp-to-pipeline/)
- **Evidence:** 4/4 rubric criteria; 6 TIER 1 sources

### Pain Point 3: Manual Win/Loss Analysis is Slow (8–12 Weeks) and Shallow (Sample-Based)
- **Problem:** Manual CRM, spreadsheets, 10–20 samples out of 100+ deals, taking 8–12 weeks, missing patterns.
- **Quantified cost:** 1 FTE spends 8–12 weeks per cycle (2–3 cycles/year) = $36,923–$82,769/year. [Umbrex](https://umbrex.com/resources/frameworks/marketing-frameworks/win-loss-analysis-framework/)
- **What teams do today:** Manual CRM pulls, sample interviews, consultants ($5–15K/engagement), ABM tools ($50K–$150K/year) requiring manual interpretation. [Saber](https://www.saber.app/glossary/closed-lost-analysis); [SalesLeap](https://www.salesleap.com/resources/why-b2b-win-loss-analysis-is-the-secret-to-sales-success/)
- **Why urgent:** Manual allows 1–2 cycles/year vs. 3–4 needed for living ICP. Over 12 months, delayed insights prevent agile refinement. [Presicci](https://federicopresicci.com/blog/sales/win-loss-analysis/); [Wandify](https://wandify.io/blog/sales/the-ultimate-guide-to-creating-a-data-driven-ideal-customer-profile-icp-for-sales-success/)
- **Evidence:** 4/4 rubric criteria; 6 TIER 1 sources

### Pain Point 4: Data Decay (Contact Staleness) Invalidates ICP Every Quarter
- **Problem:** B2B data decays 22.5–70.3% annually (2.1%/month for SaaS). ICP criteria unreliable in 90 days.
- **Quantified cost:** 2.1% monthly decay = 21 invalid/month on 1,000-account list = 2–3 wasted outbound per SDR/month = ~$13,440/year labor. [Landbase](https://www.landbase.com/blog/data-decay-b2b-crm-loses-accuracy); [Datamatics](https://www.datamaticsbpm.com/blog/data-decay-in-b2b-databases-in-every-year/)
- **What teams do today:** Enrichment subscriptions (ZoomInfo $15K–$30K/year, Apollo $2K–$3.5K/year, HubSpot Breeze $150–$700/month). Quarterly manual reviews: 1–2 weeks RevOps labor = $2,880–$5,760/year. [Cleanlist](https://www.cleanlist.ai/blog/zoominfo-apollo-clearbit-data-provider-comparison-2026); [Cognism](https://www.cognism.com/blog/zoominfo-competitors)
- **Why urgent:** Over 12 months, ICP criteria becomes unreliable; remediation forced ($5–10K + 4 weeks). Over 24 months, repeated cycles erode confidence. [RocketReach](https://rocketreach.co/resources/how-b2b-data-accuracy-impacts-revenue-the-2026-statistical-analysis/)
- **Evidence:** 4/4 rubric criteria; 7 TIER 1 sources

---

## What This Agent Does

The ICP Development Agent is your data-driven ICP architect. It ingests closed-won and closed-lost opportunity records enriched with firmographic attributes (industry, revenue, employee count, geography) and uncovers the quantified characteristics that define your most successful customers. Using statistical binning, win-rate analysis, and significance testing, the agent identifies which industry verticals, revenue bands, company sizes, and geographies win at rates materially better than your baseline. It then outputs a structured ICP definition with confidence scores, statistical summary, and quarterly drift alerts. Unlike manual analysis (10–20 samples, 8–12 weeks), this agent processes your entire closed deal cohort (100+), produces results in minutes, and continuously monitors for market drift. You get an operationalized ICP you can share with sales and marketing, plus quarterly signals when your market is shifting.

---

## Getting Started (Preflight Check)

When you trigger this agent, I'll verify your CRM connection, confirm deal data exists, assess data quality, and ask you to scope your ICP analysis.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: export deals to CSV for offline analysis, or help you reconnect the MCP.
- **If successful:** Proceed to Step 2.

**Step 2: Required Data Validation**
I'll verify that your Opportunity and Account records have these minimum fields:
- **Opportunity:** Close Date, Amount (or explicit null), Is Won (or Deal Stage), Account ID
- **Account/Company:** Industry, Annual Revenue, Employee Count
- **Contact (optional):** Email, Phone, First Name, Last Name

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ 1–2 fields missing (e.g., no Employee Count data) → Partial results possible; I'll flag the limitation and proceed
- ✗ Core fields missing (e.g., no Industry or Win/Loss indicator) → No-go; request data enrichment first

**Step 3: Data Quality Assessment**
I'll calculate:
- % of opportunities with valid Close Dates (should be 100%)
- % of opportunities with Amount populated (target: >90%)
- % of accounts with Industry populated (target: >80%)
- % of accounts with Employee Count (target: >85%)
- Win/Loss ratio (flag if >95% wins or <5% wins)
- Deal volume and time range

**Step 4: Define Your ICP Scope**
Before running the analysis, I'll ask:
- "Do you want to analyze all deals from the last 12 months, or focus on a specific quarter?"
- "Should I include all deal sizes, or filter to deals above a minimum amount (e.g., >$10K)?"
- "Any industries or geographies to explicitly exclude?"

**Preflight Report Example**
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Opportunity + Account objects present with required fields
✓ Close Date quality: 100% valid (all 87 closed deals)
✓ Amount data quality: 93% populated (81 / 87 deals)
✓ Industry quality: 82% populated (71 / 87 accounts)
✓ Employee Count quality: 87% populated (76 / 87 accounts)
✓ Win/Loss distribution: 65 won (75%), 22 lost (25%) — balanced ✓
✓ Deal volume: 87 closed deals in last 12 months

Data Readiness: PASS — Ready to analyze ICP

Scope: All opportunities (last 12 months) | No filters | Full analysis

Next step: Running ICP analysis on 87 deals...
```

---

## Step-by-Step Workflow

### Step 1: Fetch and Validate Deal Data (Batch Query)

**What I'll do:**
- Query Opportunity records: all records where IsClosed = true AND CloseDate in [your date range]
- Query linked Account records: Industry, Annual Revenue, Employee Count, Country, Region
- Query Contact records (optional): Email, Title, Department for deal context
- Fetch Activity data (optional): Deal velocity = (CloseDate - CreatedDate) in days

**Batch Strategy:** Fetch in 1,000-record increments to respect API rate limits. For typical mid-market orgs (30–150 closed deals/year), this is 1–2 API calls.

**Data I need from each Opportunity:**
- `Id`, `Name` (display), `AccountId` (required)
- `CloseDate`, `IsClosed`, `IsWon` (or `DealStage` normalized to Won/Lost)
- `Amount` (nullable, but flagged if >10% missing)
- `CreatedDate` (to calculate deal velocity)

**Data I need from each Account:**
- `Id`, `Name`, `Industry`, `AnnualRevenue`, `NumberOfEmployees`, `BillingCountry`, `BillingState`

**What you'll see:** Progress indicator ("Fetched 87 / 87 records. Validating...").

---

### Step 2: Normalize and Validate Data

**Industry Normalization:**
- Standardize common variants: "Software / SaaS / Enterprise Software" → "Software"
- Group small-n categories: <3 occurrences merged into "Other"
- Preserve original values in detail output for audit

**Revenue Normalization:**
- Convert to millions for readability: 50000000 → 50M
- Detect obvious errors (e.g., annual revenue = $100) and flag
- Calculate revenue quartiles (Q1–Q4) for binning analysis

**Employee Count Normalization:**
- Convert ranges to midpoints if present (e.g., "100–500" → 300)
- Detect outliers (e.g., employee count = 1 for $500M company) and flag
- Calculate employee-count deciles (D1–D10) for binning

**Deal Velocity Calculation:**
- dealVelocityDays = CloseDate - CreatedDate
- Flag unrealistic values (negative, >365 days) and investigate

**Data Quality Flags:**
- Missing Amount: Log deal but don't use in deal-size ICP binning
- Missing Industry: Log deal but exclude from industry ICP binning
- Missing Employee Count: Log deal but exclude from size-based ICP binning
- All quality issues summarized in final "Data Quality & Limitations" section

---

### Step 3: Segment into Won and Lost Cohorts

**Processing:**
```
won_cohort = [Opportunities WHERE IsWon = true]
lost_cohort = [Opportunities WHERE IsWon = false]

Calculate cohort summary statistics:
- Count of deals
- Average deal size (mean, median, std dev)
- Average sales cycle velocity (mean, median)
- Industry distribution (frequency count)
- Revenue distribution (quartile breakdown)
- Employee count distribution (decile breakdown)
```

**Output Example:**
```json
{
  "wonCohort": {
    "count": 65,
    "avgDealSize": 28500,
    "medianDealSize": 24000,
    "stdDevDealSize": 18900,
    "avgCycleVelocityDays": 68,
    "industries": {
      "Software": 35,
      "Enterprise Software": 18,
      "Professional Services": 8,
      "Consulting": 4
    }
  },
  "lostCohort": {
    "count": 22,
    "avgDealSize": 12300,
    "medianDealSize": 9500,
    "stdDevDealSize": 9200,
    "avgCycleVelocityDays": 52,
    "industries": {
      "Software": 12,
      "Enterprise Software": 5,
      "Professional Services": 3,
      "Consulting": 2
    }
  },
  "overallMetrics": {
    "winRate": 0.747,
    "totalDeals": 87,
    "avgDealSize_Overall": 23800,
    "avgCycleVelocityDays": 64
  }
}
```

---

### Step 4: Identify Firmographic Patterns (Win-Rate Binning)

For each firmographic dimension (Industry, Revenue Band, Employee Count, Country), I'll calculate win rates and flag "positive signal" categories.

**Algorithm: Binning & Win-Rate Analysis**

**For Categorical Fields (Industry, Country):**

```
FOR EACH category (e.g., "Software"):
  - Count won deals in category
  - Count lost deals in category
  - Calculate win_rate = won / (won + lost)
  - Compare to overall_win_rate (0.747 in example)
  
  IDENTIFY positive signal IF:
    - Sample size >= 5 (minimum rigor threshold)
    - win_rate >= 1.5 × overall_win_rate (50% better than baseline)
    - win_rate > 0 (not all losses)
    
  CALCULATE confidence = (sample_size / total_deals) × (win_rate_advantage / overall_win_rate)
  
  PERFORM chi-square significance test (reject if p-value > 0.05)
```

**Example Output:**

```
INDUSTRY ANALYSIS:
┌─────────────────────┬─────┬──────┬──────────┬────────────┬──────────┐
│ Industry            │ Won │ Lost │ Win Rate │ vs. Avg    │ Conf.    │
├─────────────────────┼─────┼──────┼──────────┼────────────┼──────────┤
│ Software (ICP ✓)    │ 35  │ 12   │ 74.5%    │ +0% (flat) │ 78%      │
│ Enterprise Soft (✓) │ 18  │ 5    │ 78.3%    │ +4.8% (✓)  │ 82%      │
│ Prof Services       │ 8   │ 3    │ 72.7%    │ -2.7%      │ 65%      │
│ Consulting          │ 4   │ 2    │ 66.7%    │ -10.7%     │ 48%      │
└─────────────────────┴─────┴──────┴──────────┴────────────┴──────────┘

INTERPRETATION:
- "Enterprise Software" is a statistically significant positive signal (78.3% win rate vs. 74.7% baseline)
- "Software" broadly is flat (same as average; not a differentiator)
- "Consulting" shows headwinds (lower win rate)

RECOMMENDATION: Target "Enterprise Software" companies; deprioritize "Consulting"
```

**For Continuous Fields (Revenue, Employee Count):**

```
FOR EACH revenue_band (e.g., $10M–$50M):
  - Count won deals with revenue in band
  - Count lost deals with revenue in band
  - Calculate win_rate for band
  - Compare to overall_win_rate
  
  [Same positive signal logic as categorical]
```

**Example Output:**

```
ANNUAL REVENUE ANALYSIS:
┌──────────────┬─────┬──────┬──────────┬────────────┬──────────┐
│ Revenue Band │ Won │ Lost │ Win Rate │ vs. Avg    │ Conf.    │
├──────────────┼─────┼──────┼──────────┼────────────┼──────────┤
│ <$10M        │ 8   │ 6    │ 57.1%    │ -23.4%     │ 45%      │
│ $10M–$50M    │ 28  │ 8    │ 77.8%    │ +4.1% (✓)  │ 81%      │
│ $50M–$250M   │ 22  │ 6    │ 78.6%    │ +5.2% (✓)  │ 79%      │
│ >$250M       │ 7   │ 2    │ 77.8%    │ +4.1%      │ 62%      │
└──────────────┴─────┴──────┴──────────┴────────────┴──────────┘

INTERPRETATION:
- Sweet spot: $10M–$250M annual revenue (77–78% win rate)
- Lower bound: Companies <$10M show lower win rate (57%)
- Upper bound: >$250M sample too small to be statistically confident

RECOMMENDATION: Target $10M–$250M; use caution with <$10M or >$250M deals
```

---

### Step 5: Compile ICP Definition & Confidence Scores

**Output: Structured ICP JSON Schema**

```json
{
  "icp_version": "2026-Q1",
  "generated_date": "2026-04-13T14:32:00Z",
  "analyzed_period": {
    "start": "2025-04-13",
    "end": "2026-04-13",
    "total_deals_analyzed": 87
  },
  "icp_definition": {
    "target_industries": [
      {
        "industry": "Software / Enterprise Software",
        "win_rate": 0.78,
        "confidence": 0.82,
        "sample_size": 23,
        "recommendation": "PRIMARY TARGET"
      },
      {
        "industry": "Professional Services",
        "win_rate": 0.73,
        "confidence": 0.65,
        "sample_size": 11,
        "recommendation": "SECONDARY (lower confidence)"
      }
    ],
    "target_revenue_range": {
      "min_usd": 10000000,
      "max_usd": 250000000,
      "currency": "USD",
      "win_rate": 0.78,
      "confidence": 0.81,
      "reason": "Statistically significant sweet spot; avoid <$10M and >$250M"
    },
    "target_employee_count": {
      "min_employees": 50,
      "max_employees": 1000,
      "win_rate": 0.77,
      "confidence": 0.79,
      "reason": "Mid-market size with consistent win rates across band"
    },
    "target_geographies": [
      {
        "country": "US",
        "win_rate": 0.76,
        "confidence": 0.85,
        "sample_size": 72,
        "recommendation": "PRIMARY"
      },
      {
        "country": "Canada",
        "win_rate": 0.72,
        "confidence": 0.58,
        "sample_size": 15,
        "recommendation": "SECONDARY (smaller sample)"
      }
    ],
    "deal_characteristics": {
      "target_deal_size_usd": {
        "minimum": 5000,
        "typical": 24000,
        "maximum": 150000,
        "median": 24000,
        "win_rate_vs_lost": "Won deals 2.3x larger than lost deals"
      },
      "target_sales_cycle_days": {
        "median": 68,
        "p25": 45,
        "p75": 92,
        "interpretation": "Typical 2–3 month sales cycle"
      }
    }
  },
  "data_quality_summary": {
    "field_completeness": {
      "opportunity_close_date": 1.0,
      "opportunity_amount": 0.93,
      "account_industry": 0.82,
      "account_annual_revenue": 0.79,
      "account_employee_count": 0.87
    },
    "warnings": [
      "Employee Count is 87% complete; 11 deals missing. ICP size confidence reduced to 79%.",
      "Revenue data is 79% complete; 18 deals missing. Revenue-band confidence at 81% (acceptable).",
      "No lost deals in >$250M segment (sample too small). Deprioritize sizing analysis in that band."
    ]
  },
  "drift_detection": {
    "previous_icp_run_date": "2025-10-13",
    "icp_drift_score": 0.08,
    "interpretation": "8% drift from Oct 2025 ICP (minimal; no major market shift detected)",
    "significant_changes": [
      "Enterprise Software win rate increased from 76% to 78% (+2pp)",
      "Revenue sweet spot expanded slightly: $12M–$250M → $10M–$250M"
    ],
    "recommendation": "No urgent changes needed. Monitor quarterly."
  },
  "recommended_next_actions": [
    "Share ICP definition with sales and marketing teams",
    "Use target_industries + target_revenue_range to segment lead scoring",
    "Update ABM campaigns to prioritize Software / Enterprise Software, $10M–$250M",
    "Flag SDRs to deprioritize <$10M prospects (57% win rate)",
    "Run follow-up analysis: buyer personas (roles/titles) within this ICP",
    "Schedule quarterly ICP drift check (next: July 2026)"
  ]
}
```

---

### Step 6: Statistical Significance Testing

For each positive signal identified in Step 4, I'll run a chi-square test to verify the signal is not due to chance.

```
Null hypothesis (H0): Outcome (Won/Lost) is independent of firmographic category

Chi-square = Σ [(Observed - Expected)² / Expected]

Decision rule:
- IF p-value < 0.05 (5% significance threshold): REJECT H0 → Signal is statistically significant ✓
- IF p-value >= 0.05: FAIL TO REJECT H0 → Signal may be due to chance ⚠️ (confidence reduced)

Example:
  Industry "Enterprise Software" vs. "Other"
  Observed: 18 won, 5 lost in Enterprise Software
  Expected (if independent): 18.3 won, 4.7 lost
  Chi-square = 0.089 → p-value = 0.89 (NOT significant)
  
  → Despite higher win rate, sample too small to claim significance
  → Confidence downgraded to 70% (acceptable but cautious)
```

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

**Analysis Scope:**
- "Analyze last 90 days, last quarter, or last 12 months?" (Default: 12 months)
- "Include all deal sizes, or filter to >$5K deals?" (Default: all sizes)
- "Any industries to exclude from ICP definition?" (Default: none)

**Confidence Thresholds:**
- "What's your minimum confidence threshold for including a category in ICP?" (Default: 70%)
  - Conservative: 80% (only high-confidence signals)
  - Balanced: 70% (default; includes moderate-confidence signals)
  - Aggressive: 60% (includes all signals, even with lower confidence)

**Positive Signal Definition:**
- "How much better than baseline should a category be to count as positive signal?" (Default: 50% better, i.e., 1.5× overall win rate)
  - Strict: 100% better (2.0× overall win rate)
  - Balanced: 50% better (1.5×, default)
  - Lenient: 25% better (1.25×)

**Minimum Sample Size:**
- "Minimum number of deals to include a category in ICP?" (Default: 5 deals)
  - Stricter: 10 deals
  - Balanced: 5 deals (default)
  - Lenient: 3 deals (accept small samples)

**Output Format:**
- "JSON for downstream agents, Markdown report for stakeholder review, or both?" (Default: both)

---

## Error Handling

**If MCP connection fails:**
- Offer to work with CSV export of opportunities and accounts (slower but works offline)
- Provide troubleshooting steps for the MCP (API key, permissions, org ID)
- Example: "Salesforce MCP authentication failed. Have you recently rotated your API credentials?"

**If required data is missing:**
- Continue with available data; flag limitations in report
- Example: "Industry data is only 72% complete (58/87 deals). ICP definition will exclude industry segmentation and rely on revenue/employee-count patterns instead. Confidence reduced to 65%."

**If data quality is too low:**

| Data Completeness | Recommendation | Action |
|---|---|---|
| >80% | Proceed | Full analysis, minor caveats |
| 60–80% | Proceed with caution | Analysis proceeds; confidence reduced; flag gaps |
| 40–60% | Recommend enrichment first | Offer to proceed anyway or suggest enriching first |
| <40% | Refuse to proceed | Agent cannot run safely; recommend data enrichment |

**If deal volume is too low:**

| Deal Count | Recommendation | Action |
|---|---|---|
| ≥30 | Ideal | Full confidence analysis |
| 15–29 | Degraded | Proceed with "beta" label; warn that trends may be unreliable |
| <15 | Cannot proceed | Agent refuses; recommend expanding time range or enriching deal data |

**If win/loss ratio is skewed:**
- All wins (0% loss rate): "Cannot define ICP from wins alone. Need lost deal data to understand what NOT to target. Expand to 12 months to find losses, or agent cannot proceed meaningfully."
- All losses (0% win rate): "Cannot define ICP from losses alone. Need won deal data. Expand to 12 months or agent cannot proceed."
- >95% skew: "Win/loss ratio is [X]%. ICP will be heavily biased. Recommend manual review of definition."

**If API rate limits are hit:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (500 records instead of 1,000)
- Split into multiple runs (analyze Q1, Q2, Q3, Q4 separately if needed)

---

## What to Run Next

After ICP is defined, these downstream agents consume your ICP output:

1. **LM-01: MQL Qualification Agent** — Use ICP firmographics to score incoming leads and qualify them as MQL (weekly scoring)

2. **OO-01: ICP List Building Agent** — Build a target account list from public databases (Apollo, Clearbit, etc.) filtered by your ICP criteria

3. **IMS-02: TAM/SAM Sizing Agent** — Estimate total addressable market (TAM) and serviceable addressable market (SAM) using your ICP industry/revenue/employee counts

4. **IMS-03: Segment Performance Agent** — Analyze how different firmographic segments perform; identify upsell/cross-sell patterns within ICP

5. **IMS-04: Account Scoring Agent** — Score accounts on their fit to ICP (0–100) and identify high-potential targets for ABM campaigns

6. **EM-SELECT-01: Event Selection & Scoring Agent** — Use ICP to identify which industry conferences, webinars, and events have high concentrations of your ideal buyers

7. **EM-ORCH-02: Event Orchestration Agent** — Orchestrate multi-touch event marketing campaigns targeting ICP accounts

**Recommended Cadence:**
- **Monthly:** Run IMS-01 to refresh ICP with new closed deals; update LM-01 and IMS-04 scoring models
- **Quarterly:** Full ICP drift analysis; update downstream agents if major shifts detected
- **Semi-annually:** Deep competitive analysis (compare your ICP to competitors' ICPs)

---

## Example: End-to-End Session

**You:** "Define my ideal customer profile from our closed deals. We want to know what kinds of companies we're winning with."

**Me (Preflight):**
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Found 87 closed opportunities (last 12 months)
  - 65 won (75% win rate)
  - 22 lost (25% loss rate)
✓ Account data quality:
  - Industry: 82% populated (71/87)
  - Annual Revenue: 79% populated (69/87)
  - Employee Count: 87% populated (76/87)

✓ Data readiness: PASS

Next, I'll analyze ICP from your 87 closed deals...
```

**You:** "Go ahead. Use the last 12 months of data."

**Me (Analysis):**
```
Analyzing 87 deals across 4 dimensions...

✓ Industry analysis complete
  - Identified "Enterprise Software" as positive signal (78.3% win rate, +4.8pp vs. baseline)
  - Chi-square p-value = 0.042 (statistically significant ✓)

✓ Revenue analysis complete
  - Sweet spot: $10M–$250M annual revenue (78% win rate)
  - Avoided: <$10M (57% win rate) and >$250M (too small sample)

✓ Employee count analysis complete
  - Target: 50–1,000 employees (77% win rate)
  - Statistical significance: p = 0.03 ✓

✓ Geography analysis complete
  - US: 76% win rate (primary), 85% confidence
  - Canada: 72% win rate (secondary), 58% confidence

Compiling ICP definition...
```

**Report (Markdown + JSON):**

```markdown
## ICP Development Analysis — 2026-Q1

**Request:** Define Ideal Customer Profile from closed deals  
**Timestamp:** 2026-04-13T14:32:00Z  
**Confidence:** 81% (based on 87 deals, 12-month analysis)  

### Summary
Your ideal customer is a Software / Enterprise Software company, $10M–$250M annual revenue, 50–1,000 employees, primarily in the US. This profile wins at 78% (vs. 75% overall), driven primarily by Enterprise Software vertical (+4.8pp win-rate advantage). Avoid companies <$10M (57% win rate) and deprioritize non-software industries.

### Details

**Primary Target Profile:**
- **Industry:** Software / Enterprise Software (78.3% win rate, 95% confidence)
- **Annual Revenue:** $10M–$250M (77.8% win rate, 81% confidence)
- **Employee Count:** 50–1,000 (77% win rate, 79% confidence)
- **Geography:** US (76% win rate, 85% confidence); Canada secondary (72% win rate, 58% confidence)
- **Typical Deal Size:** Median $24K (range $5K–$150K)
- **Typical Sales Cycle:** 68 days (6–10 weeks)

**Avoid / Lower Priority:**
- Companies <$10M ARR (57% win rate; -23% vs. baseline)
- Consulting/Professional Services vertical (67% win rate; -10% vs. baseline)
- Companies >$250M (too few samples; avoid complex enterprise deals)

### Data Quality & Limitations
- Industry data: 82% complete (11 deals missing). ICP industry recommendations at 82% confidence.
- Revenue data: 79% complete (18 deals missing). Revenue-band recommendations at 81% confidence.
- Employee count: 87% complete (10 deals missing). Size-based ICP at 79% confidence.
- **Key assumption:** "Win rate as proxy for ICP fit." Assumes your lost deals are due to poor firmographic fit, not other factors (price, product-market fit, sales execution). Recommend qualitative win/loss interviews to validate.
- Statistical significance: All primary signals pass chi-square test at p<0.05. Secondary signals (Canada, Professional Services) below threshold; use with caution.

### Recommended Actions
1. **Sales Alignment:** Share this ICP with sales team. Create 1-pager: "Enterprise Software, $10M–$250M, 50–1K employees, US focus."
2. **Lead Scoring:** Update MQL qualification (LM-01 agent) to deprioritize <$10M leads. Weight Enterprise Software industry +15%.
3. **ABM Campaigns:** Target Enterprise Software accounts in your ICP revenue/size band using Apollo, LinkedIn, or 6sense.
4. **SDR Activity:** Flag SDRs to avoid pursuing Consulting/Professional Services verticals (lower win rate).
5. **Quarterly Check:** Run ICP drift analysis next quarter (July 2026) to detect market shifts.
6. **Buyer Personas:** Conduct follow-up analysis to identify buyer roles/titles (CEO, VP Sales, CFO?) within this ICP.

### Sources & Citations
- Opportunity data: Salesforce (pulled 2026-04-13, 87 closed deals, 12-month window)
- Firmographic data: Salesforce Account object (Industry, Annual Revenue, Employee Count)
- Statistical methods: Chi-square significance testing (p<0.05 threshold)
- Confidence scoring: Win-rate binning with sample-size and margin-of-advantage weighting

---

**JSON Output** (for downstream agents):
[ICP JSON structure pasted above]
```

**You:** "This looks good. How often should we update this?"

**Me:** "I recommend running ICP analysis monthly (to capture new closed deals) and quarterly drift checks (to flag if your market is shifting). Set up a recurring task, and I'll monitor for material changes. If I detect >10% drift in win rates for key segments, I'll alert you."

---

## References & Further Reading

**Research & Specification Files** (in project):
- `/EG's Agent List/_build/research/IMS-01_icp_development_research.md` — Full market pain-point rubric and evidence
- `/EG's Agent List/_build/specs/IMS-01_icp_development_spec.md` — Technical architecture and algorithm details
- `/EG's Agent List/_build/foundation/consistency_rules.md` — RevOps Agent Factory naming and output standards

**External References:**
- [Apollo ICP Sales Guide](https://www.apollo.io/insights/icp-meaning-sales) — Industry best practices
- [Pavilion State of RevOps Survey](https://www.revopscoop.com/reports/the-2025-state-of-revops-survey) — Benchmarks for RevOps teams
- [Gartner ICP Framework](https://www.gartner.com/en/articles/the-framework-for-ideal-customer-profile-development) — Strategic ICP positioning
- [CXL ICP Gap Analysis](https://cxl.com/blog/define-your-b2b-icp/) — Cost of ICP drift

**Related Agent Skills:**
- **DQH-01 Deduplication Engine** — Clean your CRM data before ICP analysis (reduces bias from duplicate records)
- **LM-01 MQL Qualification Agent** — Apply ICP firmographics to score incoming leads
- **OO-01 ICP List Building Agent** — Generate target account lists filtered by your ICP

**Data Sources for Enrichment:**
- [ZoomInfo](https://www.zoominfo.com/) — Firmographic and contact enrichment ($15K–$30K/year)
- [Apollo](https://www.apollo.io/) — Prospecting data ($2K–$3.5K/year)
- [Clearbit](https://clearbit.com/) — Company data API (from $100+/month)
- [LinkedIn Sales Navigator](https://business.linkedin.com/en-us/sales-solutions/sales-navigator) — People search with ICP filtering
