---
name: revops-tam-sam-sizing
description: Converts your ICP definition into addressable market estimates. Calculates
  Total Addressable Market (TAM), Serviceable Addressable Market (SAM), and Serviceable
  Obtainable Market (SOM) by segment using closed-deal win rates, firmographic data,
  and analyst benchmarks. Delivers prioritized segment rankings and revenue opportunity
  sizes for quota-setting and GTM strategy.
metadata:
  trigger_phrases:
  - calculate tam and sam
  - size my total addressable market
  - estimate market opportunity
  - segment market size by industry
  - quantify tam by geography
  - what is our serviceable addressable market
  - market sizing analysis
  category: ICP & Market Strategy
  phase: 6_months
  data_readiness: 6_months
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents:
    - IMS-01 (ICP Development Agent) — MANDATORY BLOCKER
    mcps:
    - Salesforce MCP (Salesforce orgs) — Required
    - HubSpot MCP (HubSpot orgs) — Required
    - ZoomInfo API MCP (optional but recommended)
    - Apollo API MCP (optional but recommended)
    minimum_data:
    - IMS-01 output JSON with ICP definition (industries, revenue range, employee
      range, countries, confidence ≥0.65)
    - 'Closed opportunities (≥20 in last 12 months; ≥50 preferred): Amount, CloseDate,
      IsClosed, IsWon, AccountId'
    - 'Account/Company records: Industry, AnnualRevenue, EmployeeCount, BillingCountry
      (≥60% completeness)'
    - Company universe by segment (from external DB or manual CSV input)
  output_format: markdown
---

# TAM/SAM Sizing Agent

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Manual Market Sizing Takes 3–4 Weeks and Produces Inconsistent Results (±25–40% Variance)
- **Problem:** Manual pull of industry reports, hand-calculated TAM/SAM from disparate sources, spreadsheet stitching produces inconsistent estimates across runs.
- **Quantified cost:** 80–120 hours/quarter × $72/hr = $5,760–$8,640/quarter ($23,040–$34,560/year).
- **What teams do today:** Analyst reports ($2K–$5K/report), CRM manual pulls, spreadsheet modeling. 40% hire consultants ($3K–$8K/quarter).
- **Why urgent:** Over 12 months, misaligned sizing cascades: wrong quotas → SDR burnout; wrong territory assignment → chasing low-opportunity accounts; wrong GTM budget → 8–12% revenue miss.
- **Evidence:** 4/4 rubric criteria; 3 TIER 1 sources

### Pain Point 2: Market Sizing Errors Cause Quota and GTM Budget Misallocation
- **Problem:** Weak segmentation and data quality errors cause 20% TAM over/under-estimation, driving misallocated quotas and GTM spend.
- **Quantified cost:** 20% TAM overestimation on $50M ARR = $10M misallocated quota; 15–20% rep turnover vs. 8% baseline = $80K+ attrition cost.
- **What teams do today:** External consulting validation ($5K–$15K/engagement); intent-data tools ($50K–$150K/year: 6sense, Demandbase).
- **Why urgent:** Quota misalignment compounds: rep churn, morale collapse, 10–15% revenue miss over 12 months.
- **Evidence:** 4/4 rubric criteria; 3 TIER 1 sources

### Pain Point 3: Firmographic Data Decay (2.1%/Month) Invalidates TAM/SAM Quarterly
- **Problem:** B2B data decays 22.5–70.3% annually. Over 3–4 months, 10–15% of firmographic data is stale, invalidating TAM/SAM boundaries.
- **Quantified cost:** Data validation labor $4,320/year; enrichment tools $2K–$30K/year; quarterly audits 1–2 weeks RevOps labor.
- **What teams do today:** Enrichment subscriptions (ZoomInfo $15K–$30K, Apollo $2K–$3.5K); quarterly manual audits.
- **Why urgent:** Over 12 months, 20–25% of firmographic data becomes unreliable. TAM/SAM estimates become untrustworthy; leadership loses confidence.
- **Evidence:** 4/4 rubric criteria; 3 TIER 1 sources

### Pain Point 4: No Cross-Segment Revenue Attribution Prevents Identification of High-Opportunity Micro-Segments
- **Problem:** Single-dimension segmentation (industry OR company size OR geography) misses high-fit 3-way intersections and mis-allocates resources.
- **Quantified cost:** RevOps spends 40–60 hours/quarter on segment analysis ($11,520–$17,280/year); misallocation costs 5–10% of revenue upside.
- **What teams do today:** Manual Excel segment models (iterated 3–5 times); ABM platforms ($50K–$150K/year) for cross-segment modeling.
- **Why urgent:** GTM reallocations lag by 30–45 days. Over 12 months, lost opportunity upside = 5–10% potential New ARR.
- **Evidence:** 4/4 rubric criteria; 3 TIER 1 sources

---

## What This Agent Does

The TAM/SAM Sizing Agent is your market-sizing automation engine. It takes your ICP definition (output from IMS-01) and converts it into quantified revenue opportunity across market segments. Using your closed-deal history, firmographic data, and public company counts, it calculates three metrics for each segment:

- **TAM (Total Addressable Market):** The full revenue opportunity in each segment (market size × average customer value)
- **SAM (Serviceable Addressable Market):** The portion of TAM you can realistically reach (adjusted for competition, product fit, and geography)
- **SOM (Serviceable Obtainable Market):** Your realistic annual revenue target in each segment (based on your historical win rates and ramp capacity)

Unlike manual spreadsheet-based sizing, this agent runs deterministically, handles data decay, validates assumptions against your deal history, and updates quarterly. Output is a searchable segment ranking table showing which segments are highest-opportunity and how much revenue they represent—directly informing quota-setting, territory planning, and GTM budget allocation.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is validate that IMS-01 has run, verify your CRM connection, assess deal history and data quality, and ask you to confirm the company universe source.

**Step 1: IMS-01 Output Verification**
- I'll check if IMS-01 (ICP Development Agent) has produced a confidence-scored ICP definition JSON.
- **If missing:** Stop and explain that IMS-01 must run first. Offer to run IMS-01 as a prerequisite.
- **If present but confidence <0.65:** Warn that ICP confidence is low; proceed with caution and flag in output.
- **If present and confidence ≥0.65:** Proceed to Step 2.

**Step 2: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If neither connected:** No-go; ask you to reconnect one of them.
- **If one connected:** Proceed.

**Step 3: Deal History Assessment**
I'll query your CRM for closed opportunities (won + lost) in the past 12 months and calculate:
- Total deal count (target: ≥50 for high confidence; accept ≥20 for degraded confidence)
- Average deal size (ACV) by segment
- Win rate by segment (closed-won / closed total)
- Date range of deals available
- Completeness of Amount, CloseDate, IsClosed, IsWon fields

**Step 4: Firmographic Data Quality Check**
I'll assess Account/Company records for:
- % with valid Industry field (should be >60%)
- % with AnnualRevenue (should be >60%)
- % with EmployeeCount (should be >50%)
- % with valid BillingCountry (should be >70%)
- Freshness (when records were last updated; >6 months stale = warning)

**Step 5: Company Universe Source**
I'll ask: "How do you want to supply company counts by segment?"
- Option A: I'll query ZoomInfo or Apollo API (if connected)
- Option B: You provide a CSV with segment labels and company counts
- Option C: I'll use a default market-sizing benchmark (Gartner, IBISWorld estimates)

**Step 6: Exclusion Filters**
I'll ask: "Are there any accounts I should exclude?" (e.g., test/internal accounts, non-target industries)

**Preflight Report**
I'll summarize:
```
✓ IMS-01 output loaded (ICP confidence: 0.78)
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Deal history: 87 opportunities in last 12 months (average ACV: $245K)
✓ Firmographic data quality: 82% complete (Industry: 91%, Revenue: 76%, Employees: 71%, Country: 93%)
✓ Data freshness: 89% of accounts updated in last 6 months
✓ Company universe: Ready to query (ZoomInfo or manual CSV)

Ready to proceed. Analyzing 87 deals across [N] segments...
```

---

## Step-by-Step Workflow

### Step 1: Load and Validate ICP Definition

**What I'll do:**
- Fetch IMS-01 JSON output
- Parse schema: industries[], revenue_min/max, employee_min/max, countries[], win_rate_by_segment, confidence_score
- Validate all required fields are populated
- Extract segment definitions

**Error handling:**
- If schema invalid: Stop, explain error, ask you to re-run IMS-01 or provide corrected JSON
- If confidence <0.65: Flag in output ("Low-confidence ICP; TAM/SAM estimates may be unreliable")

---

### Step 2: Fetch and Normalize Deal History

**What I'll do:**
- Query Opportunities: last 12 months, IsClosed=true
- For each opportunity: extract Amount, CloseDate, IsWon, AccountId
- Query linked Accounts: Industry, AnnualRevenue, EmployeeCount, BillingCountry
- Normalize industry names (e.g., "SaaS", "Software as a Service" → standardized taxonomy)
- Normalize country names to ISO 3166 codes
- Handle edge cases: $0 amounts (marked as lost), null values (flagged but included if possible)
- Build dataset: 87 rows × [Amount, CloseDate, IsWon, Industry, Revenue, Employees, Country]

**Data quality flags:**
- Missing Amount: [count] records flagged
- Missing Industry: [count] records excluded from segment analysis
- Missing AnnualRevenue: [count] records flagged (reduces firmographic accuracy)
- Stale data (>6 months old): [count] records warned

---

### Step 3: Create Segment Universe

**What I'll do:**
- Generate Cartesian product of ICP boundaries:
  - Industries (from IMS-01)
  - Revenue bands (from IMS-01: e.g., $1M–$10M, $10M–$100M)
  - Employee bands (from IMS-01: e.g., 50–150, 150–500)
  - Countries (from IMS-01: e.g., US, CA, UK)
- For each segment, derive label: e.g., "SaaS, $2–10M ARR, 50–150 emp, US"
- Assign segment_id: SEG-001, SEG-002, ..., SEG-N

**Example output:**
```
SEG-001 | SaaS | $2M–10M ARR | 50–150 emp | US
SEG-002 | SaaS | $2M–10M ARR | 50–150 emp | CA
SEG-003 | SaaS | $10M–50M ARR | 150–500 emp | US
...
```

---

### Step 4: Classify Deals into Segments

**What I'll do:**
- For each closed opportunity, determine which segment(s) it belongs to based on:
  - Account's Industry (normalized) — matches ICP industry boundaries
  - Account's AnnualRevenue — falls into a revenue band
  - Account's EmployeeCount — falls into an employee band
  - Account's BillingCountry — matches ICP country
- Assign opportunity to segment(s)
- Flag deals that fall outside ICP boundaries ("out-of-segment" deals) but count them separately

**Output: Segment Deal Roster**
```
SEG-001: 12 opportunities (8 won, 4 lost)
  Win rate: 67%
  Average ACV: $280K
  Total revenue: $3.36M

SEG-002: 5 opportunities (3 won, 2 lost)
  Win rate: 60%
  Average ACV: $195K
  Total revenue: $975K

[Out-of-segment: 22 opportunities] (flagged but not counted in TAM/SAM)
```

---

### Step 5: Calculate TAM for Each Segment

**What I'll do:**
- For each segment, determine total company count (from ZoomInfo API, Apollo, benchmark data, or user CSV)
- Calculate average customer value:
  - Use ACV from closed deals in that segment (preferred)
  - If no deals in segment, use weighted average ACV from similar segments
- Formula: **TAM = Company Count × Average Customer Value**

**Example:**
```
SEG-001: SaaS, $2M–10M ARR, 50–150 emp, US
  Company count: 2,400 (from ZoomInfo)
  Average ACV: $280K (from 12 deals)
  TAM = 2,400 × $280K = $672M
```

**Data quality flags:**
- If company count unavailable: Mark as [Estimate pending], offer manual input
- If ACV unreliable (<3 deals in segment): Flag confidence drop
- If company count >2 years old: Flag data freshness warning

---

### Step 6: Calculate SAM (Serviceable Addressable Market)

**What I'll do:**
- Apply SAM reduction factors to TAM:
  - **Competitive presence factor:** If 3+ competitors identified in segment, apply 0.7–0.8 discount
  - **Geographic reach factor:** If segment is multi-country, apply country-level penetration (e.g., US = 1.0, CA = 0.8, UK = 0.6)
  - **Product-market fit factor:** If segment has ≤2 closed deals, apply 0.5–0.7 discount (low validation)
  - **Buyer concentration factor:** If segment has extreme buyer concentration (e.g., 1 buyer = 30% of segment), apply 0.8 discount
- Formula: **SAM = TAM × (Competitive Factor × Geographic Factor × PMF Factor × Concentration Factor)**

**Example:**
```
SEG-001:
  TAM: $672M
  Competitive factor: 0.75 (3 competitors)
  Geographic factor: 1.0 (US-focused segment)
  PMF factor: 0.95 (12 deals, strong validation)
  Concentration factor: 0.9 (low concentration)
  SAM = $672M × (0.75 × 1.0 × 0.95 × 0.9) = $430M
```

---

### Step 7: Calculate SOM (Serviceable Obtainable Market)

**What I'll do:**
- SOM is your realistic revenue target in each segment, based on:
  - Your win rate in that segment (from closed deals)
  - Your ramp capacity (sales headcount, sales cycle length, average contract value)
- Formula: **SOM = (TAM × Win Rate × Market Share Assumption)**
  - Win rate: Historical closed-won / (closed-won + closed-lost) for segment
  - Market share assumption: Typically 2–5% for mature companies, 5–10% for emerging segments
- Conservative: Assume 2% market share × win rate
- Optimistic: Assume 5% market share × win rate

**Example:**
```
SEG-001:
  TAM: $672M
  SAM: $430M
  Win rate: 67%
  Conservative SOM (2% market share): $672M × 0.02 × 0.67 = $9M
  Optimistic SOM (5% market share): $672M × 0.05 × 0.67 = $22.5M
  Recommended SOM: $12–15M (middle ground, based on sales capacity)
```

---

### Step 8: Rank Segments by Opportunity Value

**What I'll do:**
- Calculate opportunity score for each segment:
  - **Score = SAM × Win Rate × Data Confidence**
  - Data confidence: 1.0 (>10 deals), 0.8 (5–10 deals), 0.5 (<5 deals)
- Sort segments by score descending
- Flag segments with high SAM but low win rate (warning: "High opportunity but low product fit")
- Flag segments with high win rate but low SAM (warning: "Strong execution but limited market")

**Output: Segment Ranking Table**
```
Rank | Segment ID | Industry | Revenue | Employees | Country | TAM | SAM | Win Rate | SOM (Conservative) | SOM (Optimistic) | Opportunity Score | Notes
1 | SEG-001 | SaaS | $2–10M | 50–150 | US | $672M | $430M | 67% | $9M | $22.5M | 280 | Strong fit, high deal volume
2 | SEG-005 | SaaS | $10–50M | 150–500 | US | $1.2B | $780M | 60% | $14.4M | $36M | 468 | Largest opportunity
3 | SEG-002 | SaaS | $2–10M | 50–150 | CA | $156M | $98M | 60% | $1.9M | $4.7M | 59 | Small but consistent
...
```

---

### Step 9: Generate Output Report

**Markdown Report with:**

**Summary**
- Total segments analyzed: [N]
- Total TAM across all ICP-aligned segments: $[X]B
- Total SAM across all ICP-aligned segments: $[Y]B
- Weighted average win rate across segments: [Z%]
- Top 3 segments by opportunity: [segment IDs + SAM]
- Overall confidence level: [0–100%] based on deal volume and data quality

**Details**

**Segment Rankings Table** (as above)

**Segment Deep Dives** (Top 5 segments):
- Segment name + ID
- Deal history: [count] wins, [count] losses, [win rate]
- Average ACV + total revenue closed
- Firmographic profile (typical company in this segment)
- TAM, SAM, SOM breakdown
- Key observations ("High win rate but smaller market", "Largest opportunity with moderate fit", etc.)

**Cross-Segment Insights:**
- Highest TAM segment: [Segment], $[X]B
- Highest SAM segment: [Segment], $[Y]B
- Highest win rate segment: [Segment], [Z%]
- Best value-per-company segment: [Segment] (SOM ÷ Company Count)
- Highest-concentration risk segment: [Segment] (if one customer = >25% of segment)

**Data Quality & Limitations**
- Deal count by segment: [breakdown]
- Data completeness: Industry [%], Revenue [%], EmployeeCount [%], Country [%]
- Data freshness: [%] of accounts updated in last 6 months; [%] stale >12 months
- ICP confidence: [0–1.0] (from IMS-01)
- Company count data source: [ZoomInfo | Apollo | Benchmark | User CSV]
- Company count data age: [date pulled]
- Assumptions made:
  - Market share assumption for SOM: [2–5%]
  - Competitive discounting applied: [Yes/No]
  - Geographic penetration factors applied: [Yes/No]
  - Segments with <3 deals marked as "Low validation"; confidence in ACV reduced
- Known limitations:
  - Cannot detect competitive displacement in segment
  - Geographic factors are simplified; sub-regional variation not captured
  - Data decay over time; recommend quarterly refresh

**Recommended Actions**
1. Review top-3 ranked segments; confirm alignment with strategic priorities
2. Validate win rates and ACVs in top-2 segments with Sales leadership
3. If any segment has <5 deals, request additional deal examples to strengthen confidence
4. Set annual quota targets for each segment based on SOM (Conservative) bands
5. Schedule quarterly refresh (run this agent again in 90 days to update deal data and recalculate)
6. Identify and resolve data quality gaps (missing Industry, Revenue, etc.) to improve future analysis
7. Next step: Run IMS-03 (Segment Performance Agent) to track actual vs. opportunity by segment

**Sources & Citations**
- Closed opportunities: Salesforce/HubSpot [pulled [date], [N] records]
- Account firmographic data: Salesforce/HubSpot [pulled [date], [N] records]
- Company counts: [ZoomInfo | Apollo | Benchmark source] [pulled [date]]
- ICP definition: IMS-01 output [date generated, confidence: [score]]
- Industry taxonomy: [standardized reference]
- Win rate calculation: (closed-won) / (closed-won + closed-lost) for each segment
- Confidence scoring: Deal count, data completeness, recency

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

**TAM/SAM Reduction Factors:**
- "How aggressive should I be with competitive discounting? (Default: Moderate 0.75)"
  - Conservative: 0.85 (minimal discount for competition)
  - Moderate: 0.75 (default; assumes 2–3 competitors)
  - Aggressive: 0.65 (assumes heavy competition)

**SOM Market Share Assumption:**
- "What market share range should I target? (Default: 2–5%)"
  - Conservative: 1–3% (cautious growth)
  - Balanced: 2–5% (recommended)
  - Aggressive: 5–10% (growth-focused)

**Company Count Source:**
- "How should I fetch company counts by segment?"
  - Option A: Query ZoomInfo API (if connected) — most accurate, real-time
  - Option B: Query Apollo API (if connected) — fast, good coverage
  - Option C: Use public benchmarks (Gartner, IBISWorld) — slower, less precise
  - Option D: You provide a CSV — fastest, requires manual prep

**Minimum Deal Threshold for Segment Confidence:**
- "What's the minimum deal count to validate a segment? (Default: 3 deals)"
  - Strict: 5+ deals required (fewer segments, higher confidence)
  - Balanced: 3+ deals (default)
  - Loose: 1+ deals (more segments, lower confidence)

**Data Freshness Tolerance:**
- "How old should deal data be before I flag it? (Default: >6 months)"
  - Strict: >3 months = warning
  - Balanced: >6 months = warning (default)
  - Lenient: >12 months = warning

---

## Error Handling

**If IMS-01 output is missing:**
- No-go. Explain that IMS-02 depends on IMS-01 to define segments. Offer to run IMS-01 first or ask if you have an ICP JSON to provide manually.

**If IMS-01 confidence is <0.65:**
- Proceed with caution. Flag in output ("Low-confidence ICP; market sizing estimates are degraded"). Recommend strengthening ICP definition before using TAM/SAM for quota decisions.

**If deal history is sparse (<20 deals):**
- Proceed but degrade confidence. Calculate TAM/SAM based on available data; flag all segments with <5 deals as "Low Validation." Recommend collecting more deal data before using for quota.
- Offer fallback: "Would you like to provide benchmark ACVs by segment instead?"

**If firmographic data is incomplete:**
- Continue with available data. Flag impact in output:
  - <60% Industry data: "Cannot reliably segment; using default taxonomy"
  - <60% Revenue data: "ACV estimates are unreliable; using benchmark averages"
  - <50% EmployeeCount: "Employee band analysis is degraded"
- Recommend data enrichment (ZoomInfo, Apollo) before next quarter's run.

**If company count data is unavailable:**
- Offer fallback options:
  - "You can provide a CSV with company counts by segment"
  - "I can use public market-sizing benchmarks (Gartner, IBISWorld)"
  - "Would you like me to estimate company counts based on LinkedIn industry data?"

**If external company database API fails:**
- Fall back gracefully: "ZoomInfo API is unavailable. I can proceed with benchmark data or manual CSV input."

**If Salesforce/HubSpot connection fails:**
- Offer workaround: "You can provide a CSV export of Opportunities and Accounts for offline analysis."

**If deal clustering reveals data anomalies:**
- Flag and explain: "I noticed 3 very large deals ($5M+) in segment SEG-001. They may be outliers or indicate enterprise expansion. Should I include or exclude them from ACV calculation?"

---

## What to Run Next

After TAM/SAM sizing is complete:

1. **IMS-03: Segment Performance Agent** — Tracks sales/marketing performance against opportunity by segment. Answers: "Are we winning in our highest-opportunity segments?"

2. **IMS-04: Account Scoring Agent** — Scores inbound leads and accounts by segment opportunity value. Uses TAM/SAM rankings to prioritize target accounts.

3. **OO-01: ICP List Building Agent** — Builds target account lists, prioritizing highest-opportunity segments first.

4. **LM-01: MQL Qualification Agent** — Weights lead qualification and routing by segment opportunity.

5. **Schedule Quarterly TAM/SAM Refresh** — Set a recurring task to re-run this agent every 90 days as deal data and market conditions evolve.

---

## Example: End-to-End TAM/SAM Sizing Session

**You:** "Calculate TAM and SAM for our market based on the ICP we built."

**Me (Preflight):**
```
✓ IMS-01 output loaded (ICP confidence: 0.82)
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Deal history: 87 opportunities in last 12 months
✓ Firmographic data: 84% complete
✓ Company universe: Ready to query ZoomInfo

Proceeding with analysis...
```

**Me (Analysis):**
```
Loaded ICP segments:
- 4 industries (SaaS, Healthcare Tech, FinTech, MarTech)
- 3 revenue bands ($2M–10M, $10M–50M, $50M–500M)
- 2 employee bands (50–150, 150–500)
- 3 countries (US, CA, UK)
- Total segments: 72

Classifying 87 closed deals into segments...
✓ 65 deals map to ICP segments (75%)
⚠️ 22 deals outside ICP boundaries (25%)

Calculating TAM, SAM, SOM...
✓ Total TAM across 72 segments: $4.8B
✓ Total SAM across 72 segments: $2.7B
✓ Weighted average win rate: 58%

Top 3 segments by opportunity:
1. SaaS, $10M–50M, 150–500 emp, US: SAM = $1.2B, Win rate 62%
2. SaaS, $2M–10M, 50–150 emp, US: SAM = $430M, Win rate 67%
3. FinTech, $10M–50M, 150–500 emp, US: SAM = $320M, Win rate 54%
```

**Report:**
- Full segment ranking table (72 segments)
- Top-5 segment deep dives
- Data quality assessment (84% complete, strong)
- Confidence: 82% (good deal volume, solid data)
- Recommended annual revenue targets by segment
- Quarterly refresh scheduled for July 2026

**You:** "This looks good. I'll use these segments for quota-setting. Can you help us set quotas based on the SOM?"

**Me:** "Absolutely. Based on top-5 segments and Conservative SOM estimates, here are recommended quota targets by segment:
- Segment 1: $18M (highest opportunity + win rate)
- Segment 2: $12M (proven execution)
- Segment 3: $8M (emerging opportunity)
- [etc.]"

---

## References & Further Reading

**Key Concepts:**
- **TAM (Total Addressable Market):** Full revenue opportunity in a market segment (Company Count × Average Customer Value)
- **SAM (Serviceable Addressable Market):** Realistic addressable opportunity after adjusting for competition, geography, and market maturity (TAM × Reduction Factors)
- **SOM (Serviceable Obtainable Market):** Your annual revenue target in a segment based on win rate and market share assumptions (TAM × Win Rate × Market Share %)
- **Segment:** A unique combination of Industry + Revenue Band + Employee Band + Country

**Data Sources (Typical):**
- Company counts: ZoomInfo, Apollo, Crunchbase, G2 database
- Closed deals: Salesforce Opportunity object, HubSpot Deal object
- Firmographic data: Salesforce Account object, HubSpot Company object
- Industry benchmarks: Gartner, IBISWorld, Forrester, industry-specific analyst reports

**Refresh Cadence:**
- Run quarterly (every 90 days) as new deal data accumulates
- After major ICP updates or market changes
- After significant competitive events or GTM strategy shifts

**Related Agents:**
- IMS-01 (ICP Development Agent) — Upstream; defines the segments
- IMS-03 (Segment Performance Agent) — Downstream; tracks performance vs. opportunity
- IMS-04 (Account Scoring Agent) — Downstream; prioritizes accounts by segment value
- OO-01 (ICP List Building Agent) — Downstream; builds target lists from top segments
- LM-01 (MQL Qualification Agent) — Downstream; weights lead routing by segment opportunity
