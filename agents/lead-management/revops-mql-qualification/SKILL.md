---
name: revops-mql-qualification
description: Scores and classifies marketing-qualified leads using a composite model
  combining ICP fit, behavioral engagement, firmographic data, and contact recency.
  Produces MQL scores (0–100), routes high-confidence leads to sales, and flags low-confidence
  leads for manual review.
metadata:
  trigger_phrases:
  - qualify leads for sales
  - score mql candidates
  - identify sales-ready leads
  - assess lead quality
  - prioritize high-intent leads
  category: Lead Management
  phase: day_1
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents:
    - IMS-01 (ICP Development Agent) — MANDATORY
    - DQH-02 (Field Normalization Engine) — MANDATORY
    - DQH-01 (Deduplication Engine) — RECOMMENDED
    mcps:
    - Salesforce MCP (Salesforce orgs) OR HubSpot MCP (HubSpot orgs)
    - Snowflake MCP (optional, for enriched account health scores)
    minimum_data:
    - Lead object with Email, Phone, FirstName, LastName, Company, LeadSource, CreatedDate,
      Title (post-DQH-02)
    - Account/Company object with Name, Industry (post-DQH-02), AnnualRevenue, NumberOfEmployees,
      BillingCountry, CreatedDate
    - Activity records (Task, Event, Call, CampaignMember) for engagement history
    - IMS-01 output (ICP definition JSON with firmographic criteria, win-rate thresholds,
      excluded signals)
  output_format: markdown
---

# LM-01 MQL Qualification Agent

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Poor Lead Qualification Wastes 20–30% of Sales Pipeline on Poor-Fit Accounts
- **Problem:** Without accurate lead qualification, sales reps waste 20–30% of pipeline activity chasing poor-fit prospects.
- **Quantified cost:** $30K ARR/FTE annually in lost productivity; $150K/year for 5-FTE team.
- **What teams do today:** Manual CRM reviews, spreadsheets, consultants ($5–15K/quarter), ABM tools ($60K–$150K/year).
- **Why it's urgent:** Over 24 months, ACV drops 20%, churn rises 10–15pp, revenue underperforms 15–25%.
- **Evidence:** 4/4 rubric criteria, 4 TIER 1 sources

### Pain Point 2: Manual Lead Qualification Takes 3–5 Days, Missing Sales-Ready Signals
- **Problem:** Lead qualification happens 42 hours after lead gen, missing high-intent signals.
- **Quantified cost:** 42-hour delay vs. 5-minute window = 60–80% conversion loss = $18K–$27K/month on 500 leads/month.
- **What teams do today:** Manual CRM triage (4–8 hours/week), engagement tools ($300–$600/mo).
- **Why it's urgent:** Over 12 months, 1,800+ stale leads = 450–600 lost SQLs = $900K–$1.5M lost pipeline.
- **Evidence:** 4/4 rubric criteria, 4 TIER 1 sources

### Pain Point 3: Behavioral Signals Not Integrated — Sales Can't Prioritize High-Intent Leads
- **Problem:** Behavioral signals scattered across 5+ tools, invisible to sales reps.
- **Quantified cost:** Behavioral + intent scoring 55% MQL-to-SQL vs. 35% demographic-only = +$2.4M–$4.8M pipeline/year.
- **What teams do today:** Intent tools ($50K–$250K/year), manual cross-reference (4–6 hrs/week).
- **Why it's urgent:** 1,200 MQLs/year with hidden intent = 300+ lost SQLs = $7.2M–$14.4M opportunity cost.
- **Evidence:** 4/4 rubric criteria, 4 TIER 1 sources

### Pain Point 4: Lead Decay Makes Qualification Unreliable — 21% Annual Contact Decay
- **Problem:** Contact data decays 2.1%/month; 6% stale by 90 days.
- **Quantified cost:** 2–3 wasted SDR touches/week = $6,720/year/SDR ($33,600 for team).
- **What teams do today:** Enrichment subscriptions ($15K–$30K/year), quarterly manual cleanup (1–2 weeks).
- **Why it's urgent:** 6–12% routing to invalid contacts; SDR morale declines.
- **Evidence:** 4/4 rubric criteria, 4 TIER 1 sources

---

## What This Agent Does

The MQL Qualification Agent scores every lead on a 0–100 scale using four dimensions: ICP fit (40%), behavioral engagement signals (30%), data recency (20%), and account health (10%). Leads scoring 70+ are marked "MQL" and routed to sales; 50–69 are marked "Nurture" and kept in marketing; <50 are marked "Archive" and moved to warehouse. You get a detailed report showing which leads are ready for sales, why they score high or low, what engagement signals matter most, and exactly which leads need manual review. The agent integrates ICP criteria from IMS-01, normalized job titles and industries from DQH-02, and engagement activity from your CRM into a single composite score.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your CRM connection, confirm required data exists, assess data quality, and ask you to scope your MQL run.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: export lead data to CSV for analysis, or help you troubleshoot the MCP connection.
- **If successful:** Proceed to Step 2.

**Step 2: Required Data Validation**
I'll verify that your Lead/Contact and Account/Company objects have these minimum fields:
- Lead: Email, Phone, FirstName, LastName, Company, LeadSource, CreatedDate, Title (normalized by DQH-02)
- Account: Name, Industry (normalized by DQH-02), AnnualRevenue, NumberOfEmployees, BillingCountry, CreatedDate
- Activity records (Task, Event, Call, CampaignMember) linked to leads

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ 1–2 fields missing → Partial results possible; I'll flag the limitation and proceed with available data
- ✗ Core fields missing (e.g., no Email, no Title post-normalization, no Activity data) → No-go; request data preparation first

**Step 3: IMS-01 ICP Definition Check**
I'll confirm that IMS-01 (ICP Development Agent) has run and its output is available:
- Firmographic criteria (target industries, revenue range, employee count, countries)
- Win-rate thresholds and excluded signals
- Priority personas and job titles

**If missing:** I'll ask you to run IMS-01 first, or provide ICP criteria manually.

**Step 4: Data Quality Assessment**
I'll calculate:
- % of leads with valid emails (should be >50% for meaningful scoring)
- % of leads with valid phone numbers (should be >30%)
- % of leads with linked accounts (should be >60%)
- % of leads with activity history (engagement signal quality)
- Data freshness (when leads were created; >90 days old = lower intent confidence)
- Current estimated ICP match rate (sample ~500 leads; extrapolate to full set)

**Step 5: Define Your MQL Run Scope**
Before scoring, I'll ask:
- "Do you want to score ALL leads, or a specific subset (e.g., created in last 90 days, specific lead sources, specific accounts)?"
- "Do you want analysis-only mode (I show you scores and recommendations, but don't update CRM), or analysis + write (I score and update CRM fields)?"
- "Do you want to include previously-scored leads, or only new ones?"
- "Any lead sources, industries, or accounts to exclude?"

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Lead + Account objects present with required fields
✓ Email data quality: 87% valid (6,960 / 8,000)
✓ Activity data quality: 72% of leads have ≥1 activity
✓ IMS-01 ICP definition loaded: 5 target industries, 3 personas, win-rate 42%
⚠️ Title standardization: DQH-02 has standardized 94% of titles; 6% remain variant
✓ Estimated ICP match rate: 52% based on sample
✓ Ready to proceed

Scope: All 8,000 leads created in last 180 days | Analysis + write mode | Exclude: Competitors, Test accounts

Next step: Fetching lead and activity data...
```

---

## Step-by-Step Workflow

### Step 1: Fetch Lead Records and Linked Data (in batches)

**What I'll do:**
- Query Lead object (or Contact with Lead type in HubSpot): all records or your filtered subset (up to 10K per batch)
- For each lead, fetch linked Account/Company data
- Fetch Activity records (Task, Event, Call, CampaignMember) from last 180 days
- Optional: Fetch Opportunity history if lead converted to SQL (for validation of scoring accuracy)

**Batch Strategy:** Fetch in 1,000-record increments to respect API rate limits.

**Data I need from each lead:**
- `Id`, `Email`, `Phone`, `FirstName`, `LastName`, `Company` (required)
- `Title` (post-DQH-02 normalized)
- `LeadSource`, `CreatedDate`, `LastModifiedDate`
- `LinkedAccountId` (if already matched to Account)
- Activity count by type (emails, calls, meetings, campaign engagements) in last 90/180 days

**What you'll see:** Progress indicator ("Fetched 1,000 / 8,000 leads...").

---

### Step 2: Prepare Data and Load ICP Criteria

**ICP Criteria Extraction (from IMS-01 output):**
- Parse target industries list (e.g., ["SaaS", "Financial Services", "Healthcare Tech"])
- Parse firmographic ranges: AnnualRevenue (min/max), NumberOfEmployees (min/max), BillingCountry (target regions)
- Parse priority personas: Job titles, seniority levels, decision-making roles
- Parse win-rate thresholds (e.g., "if lead matches 3+ ICP criteria, expected win rate is 42%")
- Parse excluded signals (e.g., "do not score leads from non-target countries, do not score test accounts")

**Lead Data Preparation:**
- Trim and normalize email (lowercase, remove extra spaces)
- Validate phone format (remove non-digits, check length)
- Normalize title using DQH-02 mapping (if not already normalized, flag as data quality issue)
- Normalize industry using DQH-02 mapping
- Link lead to Account via email domain or fuzzy company name match (if not pre-linked)
- Build activity summary: count emails, calls, meetings, campaign clicks in 90-day window

---

### Step 3: Calculate ICP Fit Score (40% of composite)

For each lead, calculate ICP fit as a 0–100 scale based on how many firmographic criteria it matches:

**Criteria Scoring:**

| Criterion | Exact Match | Fuzzy Match | No Match |
|-----------|-----------|-----------|----------|
| Industry in target list | 25 points | 15 points | 0 points |
| Employee count in range | 20 points | 10 points | 0 points |
| Annual revenue in range | 20 points | 10 points | 0 points |
| Country in target region | 15 points | 5 points | 0 points |
| Title in priority persona list | 15 points | 5 points | 0 points |
| Account known/existing customer | 5 points | 2 points | 0 points |

**Calculations:**
- Sum points across all criteria (max 100)
- If any excluded signals present (test account, non-target industry, etc.), cap score at 30
- ICP Fit Score = (Total points / 100) × 100

**Examples:**
- Lead at Fortune 500 tech company, VP of Sales, in US, industry exact match → 25+20+20+15+15 = 95 ICP fit
- Lead at mid-market startup, India, wrong industry → 0+10+10+0+0 = 20 ICP fit
- Lead is test account → capped at 30 ICP fit regardless of criteria

---

### Step 4: Calculate Behavioral Engagement Score (30% of composite)

For each lead, evaluate engagement signals from activities in the last 90 days:

**Engagement Signals:**

| Signal | Points | Notes |
|--------|--------|-------|
| 10+ email opens/clicks in 90d | 30 points | High intent signal |
| 5–9 email opens/clicks in 90d | 20 points | Moderate intent |
| 1–4 email opens/clicks in 90d | 10 points | Low engagement |
| 0 email activity in 90d | 0 points | No engagement |
| 1+ call/meeting in 90d | 15 points | Direct conversation signal |
| 2+ calls/meetings in 90d | 25 points | Multiple touchpoints |
| Attended webinar/event in 90d | 15 points | Active interest signal |
| Filled out high-intent form (demo, pricing, trial) | 20 points | Direct intent signal |
| Demo scheduled or proposal sent | 25 points | Sales engagement underway |

**Calculations:**
- Sum all signals that apply (max 100 points)
- If activity is >90 days old, reduce signal by 50% (decay factor)
- If lead has 0 activities, score is 0
- Behavioral Engagement Score = (Total points / 100) × 100

**Examples:**
- Lead with 8 email opens, 1 meeting, pricing form = 20+15+20 = 55 engagement
- Lead with 1 email open 120 days ago = 10 × 0.5 = 5 engagement
- New lead with no activity = 0 engagement (but will improve as activities arrive)

---

### Step 5: Calculate Recency Score (20% of composite)

For each lead, assess how current the data and engagement are:

**Recency Signals:**

| Signal | Points |
|--------|--------|
| Lead created 0–14 days ago | 30 points |
| Lead created 15–30 days ago | 25 points |
| Lead created 31–60 days ago | 20 points |
| Lead created 61–90 days ago | 10 points |
| Lead created 91–180 days ago | 5 points |
| Lead created >180 days ago | 0 points |
| Last activity 0–7 days ago | 20 points |
| Last activity 8–30 days ago | 15 points |
| Last activity 31–60 days ago | 10 points |
| Last activity 61+ days ago | 0 points (no recent engagement) |

**Calculations:**
- If lead has no activity, use creation date only
- If lead has activity, use creation date + most recent activity date (average of both)
- Recency Score = (Total points / 100) × 100

**Example:**
- Lead created 25 days ago (25 points) + last activity 5 days ago (20 points) = 45 recency score

---

### Step 6: Calculate Account Health Score (10% of composite)

For each lead, assess the health and seniority of the linked account:

**Account Health Signals:**

| Signal | Points |
|--------|--------|
| Account is existing customer (contract end date >today) | 10 points |
| Account has open opportunities (SQL or higher stage) | 8 points |
| Account has contact with title "VP" or "C-suite" | 5 points |
| Account has 3+ contacts in CRM | 4 points |
| Account has activity in last 30 days | 3 points |

**Calculations:**
- Sum signals that apply (max 30 points)
- If account is not found/linked, use default 5 points (neutral)
- Account Health Score = (Total points / 30) × 100

**Example:**
- Account is existing customer (10) + 2 open opps (8) + C-suite contact (5) = 23 / 30 = 77 account health

---

### Step 7: Calculate Composite MQL Score

For each lead, combine all four dimensions using weighted formula:

```
MQL Score = (
  ICP_Fit_Score × 0.40 +
  Behavioral_Engagement_Score × 0.30 +
  Recency_Score × 0.20 +
  Account_Health_Score × 0.10
)
```

**Example Calculation:**
```
ICP Fit: 85 × 0.40 = 34
Behavioral: 70 × 0.30 = 21
Recency: 65 × 0.20 = 13
Account Health: 60 × 0.10 = 6
MQL Score = 34 + 21 + 13 + 6 = 74
```

---

### Step 8: Classify and Route Leads

For each lead, assign MQL status based on score thresholds:

| Score | Status | Action | Confidence |
|-------|--------|--------|------------|
| **70–100** | MQL | Route to sales immediately | High |
| **50–69** | Nurture | Keep in marketing nurture | Medium |
| **<50** | Archive | Move to cold lead list | Low |

**Additional Classifications:**

- **High-confidence MQL (85–100):** Route to top sales rep; suggest immediate outreach
- **Medium-confidence MQL (70–84):** Route to sales; flag for rep review before outreach
- **Borderline (65–69):** Flag for sales/marketing review; consider nurture workflow
- **Low engagement despite ICP fit (ICP 80+, Engagement <20):** Flag for sales team to research competitor activity or objections

---

### Step 9: Generate Output Report

**Markdown Report with sections:**

**Summary**
- Total leads analyzed
- MQL count and percentage (70+)
- Nurture count and percentage (50–69)
- Archive count and percentage (<50)
- Average MQL score across population
- Top engagement signals driving conversions

**Details**
- Distribution table (score ranges and lead counts)
- Top 20 high-confidence MQLs (scores 85+) with names, companies, ICP fit, engagement summary
- Top 10 borderline cases (65–69) requiring manual review
- Top 10 unqualified leads with ICP fit but no engagement (opportunity for nurture or re-engagement)
- Score breakdown by ICP segment (e.g., "SaaS leads average 68; Fintech leads average 55")
- Top engagement signals (e.g., "Email opens driving 35% of high MQL scores; demo requests driving 20%")

**Data Quality & Limitations**
- % of leads missing email, phone, title, account link
- % of leads with <5 activities (engagement confidence reduced)
- % of leads >90 days old (recency confidence reduced)
- Impact of DQH-02 standardization gaps (% of titles not normalized)
- Impact of missing IMS-01 ICP data (how many leads could not be scored on persona criteria)
- Assumption: Activity records are complete in last 90 days (no integration gaps)

**Recommended Actions**
1. Review high-confidence MQLs (85+); route 80% to sales immediately, hold 20% for territory assignment review
2. Manually review borderline leads (65–69); sales/marketing decide on nurture vs. archive
3. For high-ICP, low-engagement leads (ICP 80+, engagement <20), launch targeted re-engagement campaign or manual outreach
4. Validate top 50 MQLs against sales intuition (did we catch the right leads? any surprises?)
5. Monitor conversion rate: Track which MQLs converted to SQL in 30/60/90 days; recalibrate score weights based on actual outcomes
6. Run next scoring cycle in 30 days (recommend weekly scoring to capture fresh engagement)

**Sources & Citations**
- Lead data pulled from Salesforce/HubSpot [timestamp]
- IMS-01 ICP criteria loaded [date]
- DQH-02 title normalization applied [date, % of titles standardized]
- Activity data includes Task, Event, Call, CampaignMember objects from [date range]

---

## Configuration Options

Before I start scoring, you can customize these parameters:

**Score Thresholds:**
- "What's your MQL threshold? (Default: 70)"
  - Conservative: 75 (fewer false positives, more false negatives, slower sales ramp)
  - Balanced: 70 (recommended)
  - Aggressive: 65 (catches more leads, more manual review burden)

**Dimension Weights:**
- "Should I prioritize ICP fit, engagement, recency, or account health equally?" (Default: 40/30/20/10)
  - Account-centric: 0.35 / 0.25 / 0.20 / 0.20 (if you trust account signals more)
  - Engagement-heavy: 0.35 / 0.40 / 0.15 / 0.10 (if you trust behavior over firmographics)

**Engagement Decay:**
- "How quickly should engagement decay? (Default: 50% reduction after 90 days)"
  - Aggressive decay: 75% reduction (only very recent activity counts)
  - Slow decay: 25% reduction (older activity still valuable)

**Scope Filters:**
- "Limit to specific lead sources? Date range? Accounts?" (Default: all)

**Write Mode:**
- "Update CRM with scores and status? (Default: Analysis-only; you review first)"

---

## Error Handling

**If MCP connection fails:**
- Offer to work with CSV export instead (slower but works offline)
- Provide troubleshooting steps for the MCP (API key, permissions, org ID)

**If IMS-01 ICP definition is missing:**
- Continue with default firmographic criteria (industry, revenue, employee count)
- Reduce ICP Fit weight from 40% to 25%
- Flag in report: "ICP definition not loaded; using generic firmographic criteria"
- Recommend: "Run IMS-01 first to get organization-specific ICP criteria"

**If DQH-02 title normalization is incomplete:**
- Continue with available normalized titles
- Flag: "X% of titles not standardized; persona matching will be degraded"
- Reduce Behavioral score weight by 5%

**If activity data is sparse:**
- >80% leads with <5 activities in 90d → Proceed with caution; flag engagement confidence as low (50–60%)
- 50–80% sparse → Degraded results; recommend running score again in 30 days when more engagement data arrives
- <50% sparse → Proceed normally

**If account linking fails:**
- >30% leads unlinked to accounts → Reduce Account Health weight from 10% to 5%; note in report
- <30% unlinked → Proceed normally; attempt fuzzy matching on company name

**If data quality is too low to proceed:**
- <30% of leads have email addresses → Refuse to proceed; email is primary identifier
- <50% of leads have title field → Warn; persona matching will fail; recommend DQH-02 first
- <20 leads in sample → No-go; need larger dataset to calculate meaningful score distribution

---

## What to Run Next

After MQL qualification is complete:

1. **LM-02: Lead-to-Account Matching Agent** — Match unlinked MQLs to existing accounts; consolidate duplicate account references.

2. **LM-03: Lead Routing Agent** — Automatically route MQL leads to assigned sales reps; send Nurture leads to marketing automation; move Archive leads to cold storage.

3. **Sales Validation Check** — Ask sales team to validate top 50 MQLs: "Did we score the right people? Any false positives? Any false negatives?" Use feedback to recalibrate weights.

4. **Conversion Tracking** — Set up tracking: "Of these MQLs, which converted to SQL in 30/60/90 days?" Use conversion data to validate model accuracy.

5. **Recurring Weekly Scoring** — Schedule LM-01 to run weekly or daily (depending on lead generation volume) to continuously qualify new leads as they arrive.

6. **IMS-04: Account Scoring Agent** — Once MQL-to-SQL conversion data is available, use it to calibrate account-level scoring and predict which accounts are most likely to engage.

---

## Example: End-to-End MQL Qualification Session

**You:** "Score all leads created in the last 90 days and show me which ones are sales-ready."

**Me (Preflight):**
```
✓ Salesforce MCP connected
✓ Lead + Account objects ready
✓ Email quality: 88% valid
✓ Activity quality: 76% of leads have ≥1 activity
✓ IMS-01 loaded: 5 target industries, 4 personas, 42% win-rate threshold
✓ DQH-02 title normalization: 96% complete
✓ Analyzing 6,200 leads (created in last 90 days)
```

**You:** "Analyze all. Show me everything; don't update CRM yet. I want to validate the scores first."

**Me (Analysis):**
```
Fetching lead and activity data...
✓ 6,200 leads + account links + 90-day activity history

Calculating ICP fit scores...
✓ 3,248 leads (52%) match target ICP (ICP score 70+)

Calculating engagement scores...
✓ 2,156 leads (35%) have active engagement (5+ activities in 90d)
✓ 1,840 leads (30%) have 1–4 activities (low engagement)
✓ 2,204 leads (35%) have 0 activities (no engagement yet)

Calculating recency scores...
✓ 3,120 leads (50%) created in last 30 days (high recency)
✓ 2,080 leads (33%) created 31–60 days ago (medium recency)

Calculating account health...
✓ 1,488 leads (24%) linked to existing customer accounts
✓ 4,712 leads (76%) linked to prospect accounts

Computing composite MQL scores...
✓ MQL (70+): 1,240 leads (20% of 6,200)
✓ Nurture (50–69): 2,480 leads (40%)
✓ Archive (<50): 2,480 leads (40%)

Average MQL score: 61 (healthy distribution)
```

**Report (Markdown + JSON):**

Summary: "1,240 leads qualify as MQL (sales-ready). Top drivers: ICP fit (40% of scores), engagement signals (30%), and recency (20%). 20% of leads are ready for immediate sales outreach. If you route these 1,240 MQLs with typical 50% conversion rate, you'll generate 620 SQLs in 30 days (estimated pipeline impact: $3.1M at $5K ACV)."

Details:

**Top 10 High-Confidence MQLs (85+):**

| Lead | Company | ICP Fit | Engagement | Recency | Account Health | MQL Score |
|------|---------|---------|------------|---------|---|---|
| Sarah Chen | TechCorp (Fortune 500) | 95 | 80 | 95 | 85 | 90 |
| Michael Lee | Growth Systems | 92 | 75 | 88 | 60 | 85 |
| ... | ... | ... | ... | ... | ... | ... |

**Top 10 Borderline Cases (65–69) Requiring Review:**

| Lead | Company | ICP Fit | Engagement | Issue |
|------|---------|---------|------------|-------|
| Jessica Davis | CloudTech | 88 | 52 | Strong ICP, moderate engagement—nurture vs. route? |
| Robert Kim | DataFlow | 75 | 68 | Mixed signals; sales should validate |
| ... | ... | ... | ... | ... |

**Top 10 High-ICP, Low-Engagement Leads (ICP 80+, Engagement <30):**

Recommendation: "These 156 leads are ICP-fit but not yet engaged. Consider: (1) targeted email campaign with pricing/demo content, (2) direct sales outreach from AE, (3) account-based marketing campaign."

**Data Quality:**
- Email addresses: 88% valid (6% missing, 6% invalid format)
- Activity completeness: 76% of leads have ≥1 activity; 24% are new with no activity yet
- Account linking: 82% linked; 18% require manual account match (recommend LM-02 next)
- Title standardization: 96% of titles normalized; 4% remain non-standard (DQH-02 in progress)
- Assumption: Activity data is complete (no integration gaps). If you have engagement tools (Gong, Marketo) not syncing to Salesforce, actual engagement is higher.

**You:** "This looks great. I see 1,240 MQLs. Before we route them, let me validate the top 50 against my intuition. Are any obvious misses?"

**Me:** "Great idea. Validation loop: I can re-score top 50 and provide a side-by-side comparison of what the model scored vs. what you'd expect, so we can calibrate weights. Or I can run a sample conversion test: pick 100 random MQLs, route them to one rep for 30 days, track which convert to SQL, and compare predicted MQL score vs. actual conversion outcome. That way we know if the model is accurate before routing all 1,240."

**You:** "Let's do the conversion test. Route a random sample of 100 MQLs to Sarah (our best rep) for 30 days. I'll check back in April and we'll see how many actually converted."

**Me:** "Done. I've tagged 100 random MQLs with 'TEST_SAMPLE_APRIL' and sent Sarah a CSV with names, scores, and recommended talking points. I'll remind you to check conversion in 30 days. Once we see how many converted, we can recalibrate the scoring model and then roll out to the full team."

---

## References & Configuration Files

**Detailed Files (in `references/` folder):**
- `icp_criteria_template.md` — Template for IMS-01 ICP definition (firmographics, personas, win-rate thresholds)
- `engagement_signal_examples.md` — Examples of high-intent vs. low-intent behavioral signals
- `score_calibration_guide.md` — How to adjust score weights based on actual MQL-to-SQL conversion data
- `common_scoring_mistakes.md` — Pitfalls: false positives, false negatives, score distribution issues
- `title_normalization_reference.md` — Standard job title categories (VP, Director, Manager, IC, etc.)
- `account_health_scoring_supplement.md` — Extended account health signals (customer health scores, NRR, support sentiment, etc.)
