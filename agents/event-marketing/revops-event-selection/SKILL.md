---
name: revops-event-selection
description: Evaluates candidate conferences, trade shows, and webinars against Ideal
  Customer Profile fit and historical ROI to recommend which events deliver the highest
  pipeline value and lead conversion. Matches attendee rosters to your ICP, calculates
  predicted deal volume and revenue impact based on historical closed-won patterns,
  surfaces competitor sponsorship flags, and ranks events by projected ROI.
metadata:
  trigger_phrases:
  - select best events
  - score event list
  - evaluate sponsorships
  - rank events by fit
  - find high-roi events
  category: Event Marketing
  phase: 30_days
  data_readiness: 30_days
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents:
    - IMS-01 (ICP Development Agent)
    mcps:
    - Salesforce MCP (Salesforce orgs)
    - HubSpot MCP (HubSpot orgs)
    - Snowflake MCP (optional; improves accuracy by 15–20%)
    - Klue / RivalSense / Bombora (optional; competitive intelligence)
    minimum_data:
    - 'Opportunity object with: CloseDate, Amount, IsWon, AccountId (past 12 months,
      ≥30 closed deals)'
    - 'Account/Company object with: Industry (≥80% populated), AnnualRevenue (≥70%),
      NumberOfEmployees (≥60%)'
    - 'ICP definition from IMS-01: firmographics + win-rate thresholds by segment'
    - 'Event attendee list CSV with: Company, Job Title, Industry, Revenue Range,
      Employee Count (user-uploaded)'
---

# EM-SELECT-01: Event Selection & Scoring Agent

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Undefined Event Selection Criteria Wastes 20–30% of Event Budget
- **Problem:** Without operationalized event selection tied to ICP, teams sponsor poor-fit events.
- **Quantified cost:** $16K–$24K/year (20–30% of $50K sponsorship + manual labor). [Cvent, 2024](https://www.cvent.com/en/blog/events/trade-show-roi)
- **What teams do today:** Manual spreadsheets, ZoomInfo/Apollo ($2K–$30K/year), ABM tools ($60K–$150K/year), pre-event research (1 FTE week/event × 5–8 events = $7.5K–$12K labor). [Lead Genius, 2024](https://www.leadgenius.com/resources/maximizing-roi-from-event-attendee-lists-the-power-of-data-enrichment)
- **Why urgent:** Over 24 months, poor fit drives 20–30% worse pipeline quality, $2K–$5K higher CAC per deal, annual event budget underfunded. [Cvent, 2024](https://www.cvent.com/en/blog/events/trade-show-statistics)
- **Evidence quality:** 4/4 criteria with 3 TIER 1 sources

### Pain Point 2: Competitive Event Intelligence Gaps Miss Win Signals
- **Problem:** No visibility into where competitors sponsor; can't detect buying motion signals.
- **Quantified cost:** $315K revenue impact/year (5–10 lost deals at $100K ACV, 45% loss rate to competitor). [Klue, 2024](https://klue.com/blog/3-ways-to-collect-smart-competitive-intelligence-at-events)
- **What teams do today:** Manual LinkedIn monitoring (2 hours/week = $7.5K/year labor), Sales Navigator ($40–$80/user/month), ZoomInfo ($2K–$5K/year), Bombora/6sense ($100K+/year). [Outreach, 2025](https://www.outreach.ai/resources/blog/customer-intelligence-platform)
- **Why urgent:** 12–24 months: competitor win rate at shared events 2–3x higher; market presence weakness noted by prospects. [Factors.ai, 2024](https://www.factors.ai/blog/b2b-marketing-attribution-challenges-and-solutions)
- **Evidence quality:** 4/4 criteria with 3 TIER 1 sources

### Pain Point 3: Multi-Touch Event Attribution Impossible — Can't Prove Event ROI
- **Problem:** Event leads convert 34% faster but teams can't prove it; touchpoints unlinked to deals.
- **Quantified cost:** $45K–$108K/year manual attribution labor (60–90 hours/event × 5–8 events) + $5K–$75K/year budget cuts. [Demand Gen Report, 2024](https://www.getmonetizely.com/articles/measuring-event-marketing-roi-and-lead-quality-a-guide-for-saas-executives)
- **What teams do today:** HubSpot/Marketo (single-touch only), third-party tools ($10K–$50K/year: Bizible, Ruler), consulting ($30K–$80K). Average: $30K–$50K/year for attribution capability. [HockeyStack, 2024](https://www.hockeystack.com/blog-posts/how-to-measure-marketing-attribution)
- **Why urgent:** 24 months: event budget cuts 10–15%, pipeline invisible, event participation drops 20–30% relative to competitors. $50K–$150K wasted annually. [RevSure, 2025](https://revsure.ai/resources/whitepapers/the-state-of-b2b-marketing-attribution-2025)
- **Evidence quality:** 4/4 criteria with 3 TIER 1 sources

---

**Painkiller verification:**
- 3/3 pain points pass ≥3/4 criteria
- All describe: RevOps Manager at B2B SaaS, 100–500 employees, North America
- Population Consistency: PASS

---

## What This Agent Does

The Event Selection & Scoring Agent is your pre-event gatekeeper. It takes a list of candidate conferences, trade shows, and webinars, plus a CSV of event attendee rosters (provided by event organizers or your research). The agent matches attendees to your CRM accounts, scores each attendee by ICP fit using historical win rates from past closed opportunities, flags competitor presence, calculates predicted pipeline value, and ranks all events by projected ROI. You get a ranked table showing which events deliver highest-quality attendees and pipeline opportunity. You avoid poor sponsorships before budget is committed. This agent runs quarterly (before each event planning cycle) and takes 2–5 minutes per evaluation.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your CRM connection, IMS-01 ICP definition, required data exists, and ask you to scope your evaluation.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: export opportunities to CSV, or help you reconnect the MCP.
- **If successful:** Proceed to Step 2.

**Step 2: ICP Definition Availability**
- I'll verify that IMS-01 has run and produced an ICP definition (firmographics + win-rate thresholds by segment).
- **If unavailable:** Agent stops. Error message: "ICP definition from IMS-01 not found. Run IMS-01 first, then retry."
- **If available:** Proceed to Step 3.

**Step 3: Required Data Validation**
I'll verify that your Opportunity/Deal records have these minimum fields:
- Close Date, Amount, IsWon/DealStage, AccountId/Company ID (required)
- Account/Company Industry, AnnualRevenue, NumberOfEmployees (for segmentation)
- CreatedDate, LastModifiedDate (for temporal analysis)

**Go/No-Go decision:**
- ✓ All required fields present + ≥30 closed deals in past 12 months → Proceed
- ⚠️ 1–2 fields missing + ≥30 deals → Partial results possible; flag limitation
- ✗ Core fields missing (IsWon, CloseDate, Industry) OR <30 deals → No-go; request data enrichment first

**Step 4: Data Quality Assessment**
I'll calculate:
- % of records with valid Close Date (should be 100%)
- % of records with Amount (should be ≥95%)
- % of records with Industry populated (should be ≥80%)
- % of records with Revenue/Employee Count (should be ≥70% / ≥60%)
- Estimated win rate confidence by segment (High/Medium/Low based on N and variance)

**Step 5: Event List & Attendee CSV Scope**
Before running analysis, I'll ask:
- "How many candidate events do you want to score? (typically 5–20)"
- "Do you have attendee rosters as CSVs? (required for matching; provide paths or filenames)"
- "Do you have competitor presence data from Klue/RivalSense, or should I flag as 'data not available'?"
- "Analysis-only mode (show recommendations but don't store), or save results to CRM?"

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ IMS-01 ICP definition available (v2026-Q2, 4 segments)
✓ Opportunity + Account objects present with required fields
✓ Close Date data quality: 100% valid
✓ Amount data quality: 98% valid ($1K–$5M range)
✓ Industry data quality: 82% valid (acceptable)
✓ Revenue data quality: 74% valid (acceptable)
✓ Historical deals: 47 closed opps in past 12 months (good sample)
✓ Win rate confidence: Mostly Medium-to-High by segment
✓ Ready to proceed

Scope: 8 candidate events | Attendee lists provided | Klue data available
Next step: Parsing event attendees and matching to CRM...
```

---

## Step-by-Step Workflow

### Step 1: Fetch CRM Historical Opportunity Data

**What I'll do:**
- Query Opportunity object: all records with CloseDate in past 12 months, IsClosed/IsWon = true
- Filter to 100+ records (or all if fewer available)
- Join Account to fetch Industry, AnnualRevenue, NumberOfEmployees
- Batch query in 1,000-record increments to respect API limits

**Data retrieved:**
- Opportunity ID, Name, CloseDate, Amount, IsWon, StageName
- Account ID, Account Name, Industry, AnnualRevenue, NumberOfEmployees, BillingCountry
- Activity count (last 90 days) for engagement scoring

**What you'll see:** Progress indicator ("Fetched 47 opportunities; extracting segments...").

---

### Step 2: Segment Historical Data by Firmographics

**What I'll do:**
- Group closed opportunities by: Industry + Revenue Range + Employee Count Range
- For each segment, calculate:
  - Win Rate = (Opportunities Won) / (Opportunities Won + Lost)
  - Confidence = σ = sqrt(WinRate × (1 - WinRate) / N)
  - Confidence level: "High" if σ < 5pp, "Medium" if 5–15pp, "Low" if >15pp
  - Sample size (N) for each segment

**Example output:**
```
Segment: SaaS, $2M–$10M ARR, 50–200 employees
  Win Rate: 75% (18 won, 6 lost)
  Confidence: Medium (σ = 8pp)
  Avg Deal Size: $45K
  Median Sales Cycle: 95 days
  
Segment: SaaS, $10M–$50M ARR, 200–500 employees
  Win Rate: 68% (13 won, 6 lost)
  Confidence: Medium (σ = 11pp)
  Avg Deal Size: $120K
  Median Sales Cycle: 110 days
```

---

### Step 3: Load Event Attendee List & Match to CRM

**What I'll do:**
- Parse attendee CSV provided by event organizer or your research team
- For each attendee: Extract Company Name, Title, Industry, Revenue Range, Employee Count
- Match Company name to Account in CRM using fuzzy matching (Jaro-Winkler ≥0.88 = ~92% precision)
- If match found: Use CRM Industry, Revenue, Employee Count (more reliable than CSV)
- If no match: Use CSV data as-is; flag as "enrichment candidate"

**Match confidence scoring:**
- Email exact match = 95% confidence
- Phone exact match = 92% confidence
- Fuzzy name match (JW ≥0.88) = 85–92% confidence
- Partial match = 70–84% confidence

**Output:** DataFrame with matched companies, CRM segments, ICP scores.

---

### Step 4: Score Each Attendee by ICP Fit & Win Rate

**What I'll do:**
For each attendee:
1. Determine firmographic segment (Industry, Revenue, EmployeeCount)
2. Look up Win Rate and Confidence for that segment from Step 2
3. Calculate ICP Fit Score = Win Rate × Confidence Multiplier
   - Confidence_Multiplier: High=1.0, Medium=0.8, Low=0.6
4. Attendee Score = ICP Fit Score (0–1.0 scale; 1.0 = best fit)
5. Rank attendees descending by score

**Worked example:**
- Attendee: "Sarah Chen, VP Sales, Acme Corp, SaaS, $5M ARR, 85 employees"
- Segment match: SaaS, $2M–$10M, 50–200 emp
- Win Rate: 75%, Confidence: Medium (σ=8pp)
- ICP Fit Score = 0.75 × 0.8 = 0.60
- Attendee Score: 0.60 (top 40% for this event)

---

### Step 5: Aggregate Attendee Scores & Calculate Event Score

**What I'll do:**
For each event:
- Calculate: Event ICP Score = 75th percentile of attendee scores (avoids outliers; balances quality + coverage)
- Calculate: Event Coverage = % of matched attendees with score ≥ 0.50 (ICP-qualified threshold)
- Calculate: Predicted Revenue Opportunity = (# ICP attendees) × (Avg Deal Size by segment) × (Win Rate by segment)
- Look up Historical ROI Multiplier = (Expected pipeline from event) / (Sponsorship cost), if historical data available
- Flag Competitor Presence = Count of known competitors attending (via Klue/RivalSense or manual input)

**Worked example:**
- Event: Tech Summit SF
- Total attendees: 1,200
- Matched to CRM: 840 (70% match rate)
- ICP-qualified (score ≥0.50): 420 (50% of matched)
- 75th percentile attendee score: 0.58
- Predicted revenue opportunity: 420 attendees × $45K avg deal size × 75% win rate = $14.2M potential
- Predicted pipeline value: $14.2M × 75% win rate = $10.7M
- Historical ROI multiplier: 1.8x (based on past Dreamforce sponsorships)
- Competitor presence: 3 (6sense, Gong, HubSpot)
- Recommendation: RECOMMEND (strong ICP fit + high historical ROI)

---

### Step 6: Rank Events & Generate Output Report

**What I'll do:**
- Sort events by ICP Score (highest first)
- Generate Markdown table with all event metrics
- Export to CSV for downstream use (EM-ORCH-02 event orchestration agent)

**Output format (Markdown + CSV):**

| Event | Date | Attendees Matched | ICP Score | Coverage % | Est. Pipeline | Historical ROI | Competitors | Recommendation |
|-------|------|-------------------|-----------|-----------|----------------|----------------|-------------|-----------------|
| Tech Summit SF | Sept 15–17 | 840/1200 (70%) | 0.58 | 50% | $10.7M | 1.8x | 3 (6sense, Gong, HubSpot) | RECOMMEND |
| SaaStr Annual | Sept 9–11 | 620/2500 (25%) | 0.62 | 55% | $12.4M | 2.1x | 2 (Gong, HubSpot) | RECOMMEND |
| Gartner MDM Summit | Mar 10–12 | 85/1200 (7%) | 0.28 | 15% | $1.9M | 0.4x | 1 (Looker) | PASS (low priority) |

---

## Output Contract

**Summary**
- Total events scored
- Top 3 recommended events (by ICP score)
- Total estimated pipeline opportunity (sum across top events)
- Key insights (e.g., "Tech events show highest ICP fit; competitor presence concentrated in 2 events")

**Details**
- Full ranking table (all events scored)
- ICP score breakdown by segment (which industries, revenue ranges, employee counts are most represented)
- Attendee match rate by event (% of total attendees matched to CRM)
- Competitor presence flags (which competitors at which events; buying signal assessment)
- Historical ROI multipliers (if available from past sponsorships)

**Data Quality & Limitations**
- Assumptions: Email is primary CRM identifier; Jaro-Winkler ≥0.88 achieves 92% precision on company names; win rates by segment are stable month-to-month
- Data gaps: % of attendee records with missing industry, revenue, or employee count; impact on ICP scoring confidence
- Known limitations: Can't detect career changers without enrichment; international character handling in company names; event lists incomplete (missing some companies)
- Confidence degradation factors: Small N segments (σ >15pp), incomplete attendee lists, sparse CRM data

**Recommended Actions**
1. Review top 3 recommended events (RECOMMEND tier); validate attendance expectations with marketing team
2. Investigate medium-confidence events (PASS tier); consider for brand presence or smaller budget allocation
3. Understand competitor presence flags; use as win-signal intelligence for sales outreach
4. If historical ROI multiplier unavailable, run first event from recommended list, measure post-event pipeline, and feed back into next evaluation cycle
5. For low-match-rate events (< 50%), consider requesting attendee list enrichment from event organizer or ZoomInfo before next quarter

**Sources & Citations**
- CRM data pulled [timestamp]
- ICP definition from IMS-01 run [date]
- Win rates calculated from [N] closed opportunities (past 12 months)
- Historical ROI multiplier sourced from [event names] (if available)
- Jaro-Winkler matching threshold 0.88 per fuzzy-matching industry benchmarks

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

**ICP Score Threshold (Default: 0.50)**
- "What minimum attendee score triggers 'ICP-qualified'?" (0–1.0 scale)
  - Conservative: 0.60 (only top 30% of attendees counted as qualified)
  - Balanced: 0.50 (recommended; includes top 50%)
  - Aggressive: 0.40 (includes top 65%; more leads, more noise)

**Attendee Match Confidence Threshold (Default: 0.80)**
- "What minimum fuzzy-match confidence do you require for CRM matching?"
  - High confidence: 0.90 (only very clear matches; may miss 15–20% of true matches)
  - Balanced: 0.85 (recommended; ~92% precision per Jaro-Winkler benchmarks)
  - Aggressive: 0.75 (captures more matches; higher false-positive risk)

**Segment Confidence Handling (Default: reduce confidence if σ >15pp)**
- "How strict should I be on small-N segments?" (where N = number of historical deals)
  - Strict: Exclude segments with N < 20 (only high-confidence scoring)
  - Balanced: Include but flag; reduce score multiplier by 30% (recommended)
  - Lenient: Include all; note in report that confidence is low

**Competitive Intelligence Source (Default: "Data not available")**
- "Do you have Klue/RivalSense API connected? If yes, I'll auto-fetch competitor event presence."
  - Connected: Use API
  - Manual input: Provide competitor list as CSV
  - Not available: Flag as "DATA NOT AVAILABLE" in output

**Event Portfolio Weighting (Default: Equal weight)**
- "Should I bias toward certain event types? (Conference, Tradeshow, Webinar, Virtual Summit)"
  - Equal: Score all equally
  - Conference-heavy: Boost conference scores by 20%
  - Virtual-heavy: Boost virtual/webinar scores by 20%

---

## Error Handling

**If MCP connection fails:**
- Offer to work with CSV export of opportunities (slower but works offline)
- Provide troubleshooting steps for the MCP (API key, permissions, org ID)

**If IMS-01 ICP definition unavailable:**
- Agent refuses to run; message: "ICP definition from IMS-01 not found. Run IMS-01 first, then retry."
- No fallback to generic benchmarks (ICP calibration is critical)

**If required CRM data is missing:**
- <30 closed opportunities: Proceed with caution; flag confidence <60%; recommend extending lookback to 18 months if available
- <70% Industry populated: Reduce ICP fit confidence by 30%; flag in report
- <50% Revenue populated: Reduce confidence by 25%; suggest running DQH-02 (Field Normalization) first

**If event attendee list has low match rate:**
- <50% matched to CRM: Flag "Low match rate (X% matched). Scoring reduced confidence by 25%. Recommendation: Manually enrich unmatched attendees or use ZoomInfo to fill in company data."
- >30% missing revenue/employee count: Flag "Incomplete firmographic data. Scoring may be unreliable. Recommendation: Request detailed attendee list from event organizer or enrich via third-party service."

**If historical ROI data unavailable:**
- Proceed with ICP score only; flag "Historical ROI multiplier not available. Ranking based on ICP fit + attendee coverage only. Recommendation: After event, measure actual pipeline sourced from attendee list and feed back into next evaluation."

**If API rate limits are hit:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (100 records instead of 1,000)
- Split into multiple runs (evaluate different event cohorts separately)

---

## Configuration Examples

**Example 1: Conservative (Highest Quality Leads)**
```
ICP_threshold: 0.60
match_confidence: 0.90
segment_confidence_handling: "strict"
competitive_intelligence: "Klue API"
```
Result: Only top 20–30% of attendees per event counted as qualified. Higher confidence; fewer leads; best fit.

**Example 2: Balanced (Recommended)**
```
ICP_threshold: 0.50
match_confidence: 0.85
segment_confidence_handling: "balanced"
competitive_intelligence: "Manual input"
```
Result: Top 50% of attendees per event. Moderate confidence; good lead volume; practical.

**Example 3: Aggressive (Maximize Coverage)**
```
ICP_threshold: 0.40
match_confidence: 0.75
segment_confidence_handling: "lenient"
competitive_intelligence: "Not available"
```
Result: Top 65% of attendees per event. Lower confidence; high lead volume; flag for post-event quality review.

---

## What to Run Next

After event selection is complete:

1. **EM-ORCH-02 (Event Orchestration Agent)** — Takes top-ranked events from EM-SELECT-01 and orchestrates logistics (booth setup, staffing, travel, budget allocation).

2. **LM-01 (MQL Qualification Agent)** — Post-event; re-scores event leads based on engagement behavior; refines pipeline conversion for next event selection.

3. **PM-04 (Pipeline Attribution Agent)** — Optional downstream; uses event ROI predictions to attribute closed deals back to event source; measures actual vs. predicted ROI.

4. **Schedule Quarterly Evaluation** — Run EM-SELECT-01 again 6–8 weeks before Q+1 event season (e.g., run in July for Q4 events).

---

## Example: End-to-End Event Selection Session

**You:** "Score our candidate events for Q3. Here are the attendee lists."

**Me (Preflight):**
```
✓ Salesforce MCP connected
✓ IMS-01 ICP definition available (v2026-Q2, 4 segments)
✓ Historical opportunities: 47 closed deals (past 12 months)
✓ Data quality: Industry 82%, Revenue 74%, Employee Count 61% (acceptable)
✓ Win rates by segment calculated (Medium confidence across most segments)
✓ Ready to score events
```

**You:** "8 candidate events. Evaluate all. Use balanced configuration."

**Me (Analysis):**
```
Parsing attendee lists...
✓ Tech Summit SF: 1,200 total attendees, 840 matched (70%)
✓ SaaStr Annual: 2,500 total attendees, 620 matched (25%)
✓ Gartner MDM Summit: 1,200 total attendees, 85 matched (7%)
[5 more events...]

Scoring by ICP fit...
✓ Tech Summit: 420 ICP-qualified attendees (50% coverage), score 0.58
✓ SaaStr Annual: 341 ICP-qualified (55% coverage), score 0.62
✓ Gartner MDM: 13 ICP-qualified (15% coverage), score 0.28
[5 more events...]

Calculating ROI predictions...
✓ Tech Summit: $10.7M predicted pipeline, 1.8x historical ROI
✓ SaaStr Annual: $12.4M predicted pipeline, 2.1x historical ROI
✓ Gartner MDM: $1.9M predicted pipeline, 0.4x historical ROI
[5 more events...]

Flagging competitors...
✓ Tech Summit: 3 competitors (6sense, Gong, HubSpot)
✓ SaaStr Annual: 2 competitors (Gong, HubSpot)
✓ Gartner MDM: 1 competitor (Looker)
[5 more events...]
```

**Report (Markdown + CSV):**
- Summary: "8 events scored. Top 2 recommended: SaaStr Annual ($12.4M predicted pipeline, 2.1x ROI) and Tech Summit SF ($10.7M predicted pipeline, 1.8x ROI). Total estimated opportunity: $23.1M if both events executed."
- Details: Full ranking table, attendee match breakdown by event, ICP score by segment, competitor presence flags
- Data quality: "Overall data quality good. Industry field 82% populated (acceptable). Revenue 74% (acceptable). Attendee lists 25–70% matched; low-match events flagged for enrichment."
- Recommendations: "1. Approve SaaStr Annual and Tech Summit SF for full sponsorship. 2. Investigate Gartner MDM (0.28 score, low priority); sponsor at lower tier or skip. 3. Three competitors at Tech Summit = high buying motion signal; prepare competitive positioning. 4. Enrich low-match events (< 50%) and re-score in week 2 if more attendee data available."

**You:** "This looks good. Approve SaaStr and Tech Summit. What about the other 6?"

**Me:** "Here's the breakdown for the other 6:
- 2 are PASS tier (0.40–0.50 score): Recommend for brand presence or smaller budget ($5K–$10K sponsorship vs. $50K+ for top tier)
- 4 are SKIP tier (<0.40 score): Not recommended unless they become strategic for other reasons (new market entry, competitive defense)

Shall I save this ranking to your CRM and notify EM-ORCH-02 to start logistics planning for SaaStr and Tech Summit?"

**You:** "Yes, save and notify."

**Me:** "Done. Ranking saved to [CRM location]. EM-ORCH-02 has been queued with top 2 events. You'll see booth setup, travel, and staffing recommendations from EM-ORCH-02 within 24 hours."

---

## References & Further Reading

**Detailed metrics & benchmarks:**
- Cvent Trade Show ROI Best Practices: https://www.cvent.com/en/blog/events/trade-show-roi
- Landbase Lead Qualification Statistics (2026): https://www.landbase.com/blog/lead-qualification-statistics
- HockeyStack Multi-Touch Attribution Guide: https://www.hockeystack.com/blog-posts/how-to-measure-marketing-attribution
- Demandbase ICP Fit Grade Documentation: https://help.rollworks.com/hc/en-us/articles/360045715211-Account-scoring-Use-ICP-Fit-Grade-to-assess-fit
- Klue Competitive Intelligence at Events: https://klue.com/blog/3-ways-to-collect-smart-competitive-intelligence-at-events

**Optional tools & resources:**
- fuzzy matching: `fuzzywuzzy` Python library; Jaro-Winkler algorithm
- Event data: Most event organizers (Salesforce Dreamforce, SaaStr Annual, Gartner Summits) provide attendee CSVs 2–4 weeks pre-event
- Competitive intelligence: Klue, RivalSense, Bombora APIs (optional; agent works without them)
- Historical ROI: Track in CRM custom field `Event_Source__c` on Opportunity; link to event ID for attribution
