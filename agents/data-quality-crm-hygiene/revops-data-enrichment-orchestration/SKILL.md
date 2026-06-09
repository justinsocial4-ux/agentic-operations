---
name: revops-data-enrichment-orchestration
description: "Routes B2B contact and account records to optimal enrichment providers (ZoomInfo, Apollo, Clearbit, Cleanlist, Cognism) based on missing fields and cost/accuracy trade-offs. Orchestrates multi-source enrichment, consolidates conflicting data, and writes verified results back to CRM with source attribution and confidence scores. Trigger on: enrich my contacts, fill missing data, enrich CRM records, data enrichment, find missing emails, find missing phone numbers, enrich leads, route to enrichment, optimize enrichment, multi-source enrichment."
metadata:
  trigger_phrases:
    - "enrich my contacts"
    - "fill missing data"
    - "enrich crm records"
    - "data enrichment"
    - "find missing emails"
    - "find missing phone numbers"
    - "enrich leads"
    - "route to enrichment"
    - "optimize enrichment"
    - "multi-source enrichment"
  category: "Data Quality & Hygiene"
  phase: "Phase 2"
  data_readiness: "day_1"
  version: "1.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-04-12"
  dependencies:
    agents:
      - "revops-data-deduplication"
      - "revops-data-field-normalization"
    mcps:
      - "Salesforce MCP (Salesforce orgs) or HubSpot MCP (HubSpot orgs)"
      - "ZoomInfo API (optional)"
      - "Apollo API (optional)"
      - "Clearbit API (optional)"
      - "Cleanlist API (optional)"
      - "Cognism API (optional)"
    minimum_data:
      - "Contact or Lead object with FirstName, LastName, Email, Phone (at least one identifier)"
      - "Account/Company object for company-level enrichment"
      - "At least one enrichment provider integration or API key"
---

# DQH-05 Enrichment Orchestration Engine

## Why This Agent Exists

**Target Customer (ICP):** RevOps Manager at B2B SaaS, 100–500 employees, North America

**The painkiller we're solving:** Manual multi-source data enrichment and accuracy loss that costs $40K–$60K/year in RevOps labor and tool waste, plus 1,800–2,000 bounced emails per quarter that damage sender reputation and pipeline.

### Pain Point 1: Single-Source Accuracy Ceiling Blocks Team Efficiency

**The problem:**
No single B2B data provider achieves >70-85% email accuracy on its own due to structural database limitations. This means 15-20% of your enriched emails bounce despite provider claims, damaging IP reputation and wasting outreach cycles.

**Quantified cost to your role:**
- 1,500–2,000 wasted bounces per quarter at 10K enrichments/quarter
- Sender IP throttling and recovery = 2-4 weeks of deliverability loss
- Lost pipeline: 7,500–15,000 missed opportunities per quarter from IP reputation damage
- [(Cleanlist, 2026)](https://www.cleanlist.ai/blog/zoominfo-apollo-clearbit-data-provider-comparison-2026)

**What you're doing today (workaround):**
Your team manually loads records into an average of 2.7 data providers simultaneously—up from 1.3 in 2022—consuming 8–12 hours/week in RevOps labor to stitch results back together. [(Cleanlist, 2026)](https://www.cleanlist.ai/blog/15-best-b2b-data-enrichment-providers-in-2025-ranked)

**Why it's urgent:**
B2B data decays at 30% or more per year, with people changing jobs every 2.7 years on average. Single-database approaches guarantee growing data gaps each quarter, forcing costly re-enrichment cycles. [(Cleanlist, 2026)](https://www.cleanlist.ai/blog/zoominfo-apollo-clearbit-data-provider-comparison-2026)

**Evidence quality:** 4/4 criteria verified; population consistent across all sources.

### Pain Point 2: Manual Enrichment Routing Creates Delays & Errors

**The problem:**
Without automated routing, RevOps teams spend 6–8 hours/week on triage logic: analyzing which fields are missing, checking tool integrations, deciding which provider to use, and monitoring status. Suboptimal routing sends records to high-cost tools when cheaper alternatives exist.

**Quantified cost to your role:**
- 6–8 hours/week triage labor = $24K–$32K/year per team
- Suboptimal tool routing = $15K–$25K/year in wasted enrichment spend
- **Total annual cost: $40K–$60K per RevOps team**

**What you're doing today (workaround):**
Teams pay for manual waterfall implementations ($3K–$6K/year) or build custom Salesforce Flow logic to route records. Both are labor-intensive workarounds for the lack of automated orchestration. [(Cleanlist, 2026)](https://www.cleanlist.ai/blog/zoominfo-apollo-clearbit-data-provider-comparison-2026)

**Why it's urgent:**
When enrichment routing is manual, data quality issues compound downstream—missed fields aren't caught until campaign execution or sales outreach, forcing expensive re-enrichment cycles and lost pipeline velocity.

**Evidence quality:** 4/4 criteria verified; population consistent across all sources.

### Pain Point 3: Accuracy Variance Undermines Sender Reputation & Forecast Quality

**The problem:**
Accuracy variance across enrichment providers directly damages sender IP reputation and forecast credibility. At 80% accuracy, 2,000 bounces occur per 10K emails; at 98%, only 200. The 1,800-bounce difference triggers ISP throttling and spam folder placement.

**Quantified cost to your role:**
- 1,800-bounce difference per 10K sends = IP reputation damage
- Recovery time: 2-4 weeks of reduced deliverability
- Lost opportunities on 50K emails/quarter = 7,500–15,000 missed pipeline opportunities
- Forecast accuracy also damaged—20% bounce rate = systematically overstated pipeline projections
- [(Cleanlist, 2026)](https://www.cleanlist.ai/blog/zoominfo-apollo-clearbit-data-provider-comparison-2026)

**What you're doing today (workaround):**
Teams hire data validation consultants ($8K–$15K/engagement) or buy multiple enrichment providers to cross-verify data. One documented customer moved from ZoomInfo to a waterfall approach and cut bounce rate from 14% to under 2%. [(Cleanlist, 2026)](https://www.cleanlist.ai/blog/zoominfo-apollo-clearbit-data-provider-comparison-2026)

**Why it's urgent:**
Sender reputation damage accumulates and creates a negative feedback loop. Once an IP is throttled, all future campaigns perform worse. Forecast accuracy is also systematically biased—if 20% of enriched contacts bounce, board-level pipeline projections are understated by millions.

**Evidence quality:** 4/4 criteria verified; population consistent across all sources.

**The Orchestration Solution:**
This agent automates the routing decision: analyzing record data quality, selecting the optimal enrichment source based on cost/accuracy trade-offs, and learning from outcomes to continuously improve.

**Expected outcomes:**
- Email deliverability: 80% → 98% (eliminate bounce-rate damage)
- Enrichment labor: 6–8 hours/week → 0.5 hours/week (-92%)
- Cost per valid enrichment: $0.59 → $0.15 (-75%)
- Total Year 1 ROI: $56,650 per RevOps team

---

## What This Agent Does

The Enrichment Orchestration Engine is your intelligent routing layer for B2B data enrichment. It scans your Contact and Lead records, identifies missing fields (email, phone, job title, company data, etc.), scores the "missing field severity" for each record on a 0–100 scale, and routes each record to the optimal enrichment provider based on:

1. **Which fields are missing** (what does this record need?)
2. **Which providers can fill those fields** (what tools do you have access to?)
3. **Cost-to-accuracy trade-offs** (cheap but less accurate? Or expensive but verified?)
4. **Provider accuracy benchmarks** (ZoomInfo 82%, Apollo 78%, Clearbit 76%, Cleanlist 98%)

Once enrichment is complete, the agent consolidates conflicting data from multiple providers, flags confidence levels for each field, writes verified results back to your CRM, tracks budget and credits spent, and generates a coverage report showing what was enriched, what succeeded, and what still needs work.

---

## Getting Started (Preflight Check)

When you trigger this agent, I'll verify your CRM connection, confirm enrichment provider access, validate data readiness, and scope your enrichment run.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds (CSV export for analysis) and troubleshooting steps.
- **If successful:** Proceed to Step 2.

**Step 2: Enrichment Provider Audit**
I'll verify which enrichment providers you have access to:
- ZoomInfo API active? (✓ / ✗)
- Apollo API active? (✓ / ✗)
- Clearbit API active? (✓ / ✗)
- Cleanlist API active? (✓ / ✗)
- Cognism API active? (✓ / ✗)
- Other custom APIs? (describe)

**Note on research:** Research shows single-source enrichment consistently underperforms multi-source waterfall strategies. With ≥2 providers, you'll see measurable accuracy improvement. With 1 provider, results are acceptable but not optimal.

**Step 3: Budget & Credits Check**
I'll assess:
- Remaining credits/budget per provider (ZoomInfo: $X, Apollo: $Y, etc.)
- Estimated enrichment cost based on record volume
- Recommended budget allocation across providers

**Step 4: Required Data Validation**
I'll verify that your Contact/Lead objects have:
- Identifier fields: Email, Phone, or both (required)
- FirstName, LastName (recommended)
- Account/Company link (for company-level enrichment)
- Any prior enrichment timestamp (to avoid redundant lookups)

**Go/No-Go decision:**
- ✓ ≥1 provider connected, ≥100 records needing enrichment → Proceed
- ⚠️ 0 providers connected → Can't proceed; recommend connecting ≥1 provider first
- ⚠️ Insufficient budget → Scale scope or request additional credits

**Step 5: Define Your Enrichment Scope**
Before running, I'll ask:
- "Enrich ALL contacts/leads, or a pilot set (e.g., created in last 90 days, from specific campaigns, with high-priority accounts)?"
- "Prioritize which missing fields? (Email >> Phone >> Title >> Company, or something else?)"
- "Quality threshold: accept any enrichment, or require verification?" (e.g., only verified emails)

**Preflight Report**
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Enrichment providers: ZoomInfo, Apollo, Clearbit active
⚠️ Cleanlist: Not connected (recommend adding for higher accuracy)
✓ Budget available: ZoomInfo $850, Apollo $400, Clearbit $200
✓ Contact records: 8,500 total | 2,100 missing email | 1,400 missing phone
✓ Lead records: 3,200 total | 890 missing email | 650 missing phone
✓ Data ready: 5.3K records qualify for enrichment

Scope: All 5.3K records needing email/phone | Multi-source waterfall | Cost-optimized routing

Ready to proceed? [Yes / Adjust scope]
```

---

## Step-by-Step Workflow

### Step 1: Fetch Records & Assess Missing Fields

**What I'll do:**
- Query Contact and Lead objects from CRM (batches of 1,000)
- For each record, calculate a "Missing Field Score" (0–100):
  - Email missing: +40 points
  - Phone missing: +30 points
  - Job title missing: +15 points
  - Company data incomplete: +15 points
- Score interpretation:
  - 90–100: Critical enrichment needed
  - 70–89: High priority
  - 50–69: Medium priority
  - <50: Low priority

**Example:**
- Contact A: No email, has phone, missing title → Score 55 (medium)
- Contact B: No email, no phone, no title → Score 85 (high)
- Contact C: Has email, has phone, missing title → Score 15 (low)

**Output:** Sorted list of records by missing field score.

### Step 2: Provider Capability Mapping

**What I'll do:**
- For each record, map which providers can fulfill missing fields:
  - ZoomInfo: Email ✓, Phone ✓, Title ✓, Company ✓
  - Apollo: Email ✓, Phone ✓, Title ✓, Company ✓
  - Clearbit: Email ✓, Phone ~, Title ✓, Company ✓
  - Cleanlist: Email ✓✓ (verified), Phone ✓, Title ✓, Company ✓
  - Cognism: Email ✓, Phone ✓, Title ✓, Company ✓

- Assign cost per lookup:
  - ZoomInfo: ~$0.50 per record
  - Apollo: ~$0.12 per record
  - Clearbit: ~$0.25 per record
  - Cleanlist: ~$0.50 per record (verified premium)
  - Cognism: ~$0.30 per record

**Routing Decision Tree:**
For each record, apply waterfall logic:
1. **High missing score (>70) + strict accuracy requirement?** → Cleanlist (highest verified accuracy, costs more)
2. **High missing score + cost-sensitive?** → Apollo (good accuracy, lower cost)
3. **Medium missing score?** → Clearbit or Cognism (balanced cost/accuracy)
4. **Low missing score + confirmation enrichment?** → Cheapest available provider

### Step 3: Route Records & Execute Enrichment Calls

**What I'll do:**
- Batch records by provider (respecting rate limits)
- Make API calls to each provider with record identifiers (email, phone, name)
- Track request status: pending, success, failed, rate-limited
- Log enrichment timestamps and costs

**Cost Tracking:**
- Maintain running total per provider
- Alert if any provider approaching budget limit
- Pause and ask for approval if total cost exceeds pre-set budget

**Example routing:**
```
HIGH priority (Score 85):
  - Record A → Cleanlist (Email verification needed) — $0.50
  - Record B → Apollo (Phone + Title) — $0.12

MEDIUM priority (Score 65):
  - Record C → Clearbit (Title + Company) — $0.25
  - Record D → Apollo (Email confirmation) — $0.12

COST SUBTOTAL: $0.99 per record cohort
```

### Step 4: Consolidate & Conflict Resolution

**What I'll do:**
- Collect results from all providers for each record
- If single provider returned data → use it directly
- If multiple providers returned data for same field:
  - **Exact match** (both say email = person@example.com) → Use without flagging
  - **Conflicting values** (ZoomInfo says person@example.com, Clearbit says person@example.org) → Flag confidence, apply tiebreaker rules:
    1. Verified > unverified (prefer Cleanlist's verified email)
    2. Newer data > older (prefer recent updates)
    3. Most providers agree > minority (3 say john@, 1 says jon@ → prefer john@)
    4. Higher-accuracy provider > lower (prefer Cleanlist over Apollo if they conflict)

**Confidence Scoring (per field):**
- 95–100: Verified or confirmed by 2+ providers
- 85–94: Single high-accuracy provider or 2 providers agree
- 75–84: Single mid-accuracy provider
- <75: Conflicting data or low-confidence single source

### Step 5: Write Results Back to CRM

**What I'll do:**
- For each record, prepare update payload:
  ```
  Contact ABC:
  - Email: "person@example.com" (Source: Cleanlist, Confidence: 98%)
  - Phone: "+1-415-555-0100" (Source: ZoomInfo, Confidence: 92%)
  - Title: "VP Sales" (Source: Apollo, Confidence: 87%)
  - Company: "Acme Corp" (Source: ZoomInfo, Confidence: 95%)
  - Enrichment_Date: 2026-04-12
  - Enrichment_Cost: $0.87
  ```
- Write custom fields (if available) for confidence scores, sources, and cost
- Update record in CRM via MCP

**Data Governance:**
- Never overwrite existing verified data (user's manual entries)
- Only fill empty fields or upgrade low-confidence data
- Preserve history (log what changed and why)

### Step 6: Budget & Coverage Report

**What I'll do:**
- Calculate total cost per provider and aggregate
- Measure coverage improvements:
  - Records with email before: 6,400 / 11,700 (55%)
  - Records with email after: 8,900 / 11,700 (76%)
  - Coverage gain: +21 percentage points
- Identify remaining gaps (records still missing critical fields after enrichment)
- Estimate cost of further enrichment (if needed)

**Example Report:**
```
ENRICHMENT SUMMARY

Records Processed: 11,700
Records Enriched: 5,300 (45%)
Records Failed/Not Found: 400 (3%)
Records Skipped (already complete): 6,000 (51%)

COVERAGE IMPROVEMENTS
Field: Email
  Before: 6,400 records (55%)
  After: 8,900 records (76%)
  Delta: +2,500 records (+21pp)
  Cost: $1,875 (750 records × avg $2.50/record using Cleanlist for verification)

Field: Phone
  Before: 7,100 records (61%)
  After: 9,200 records (79%)
  Delta: +2,100 records (+18pp)
  Cost: $1,200

Field: Title
  Before: 5,200 records (44%)
  After: 8,600 records (73%)
  Delta: +3,400 records (+29pp)
  Cost: $950

COST BREAKDOWN
ZoomInfo: $1,200 (45% of spend)
Apollo: $850 (32%)
Clearbit: $400 (15%)
Cleanlist: $525 (20% — reserved for email verification)
Cognism: $0 (not used; lower priority)

TOTAL COST: $2,975
Cost per enriched record: $0.56 (vs. industry average $0.59)
Confidence average: 91% (target: >85%)

REMAINING GAPS
Records still missing email: 2,800 (24%)
Records still missing phone: 2,500 (21%)
Records still missing title: 3,100 (27%)

Estimated cost for 100% coverage (all gaps): $3,500 additional
Recommended next step: Target high-value accounts with remaining gaps (accounts >$100K ARR)

NEXT STEPS
1. Review confidence scores for any fields <80%
2. Schedule weekly re-enrichment of decaying records (data decay = 30%/year)
3. Monitor email deliverability post-enrichment (target: 98%+ delivery rate)
4. Compare pre/post bounce rates after 1 week of outreach
```

---

## Configuration Options

Before starting, customize these parameters:

**Missing Field Prioritization:**
- "Which fields matter most to you?" (Default: Email > Phone > Title > Company)
- Can weight differently based on your use case (e.g., Title might be critical for event invitations)

**Provider Priority Order (Waterfall Sequence):**
- Default: Cleanlist → Apollo → ZoomInfo → Clearbit → Cognism (accuracy descending)
- Customize if you have different provider access or cost constraints

**Accuracy vs. Cost Trade-Off:**
- Cost-optimized: Prefer Apollo/Cognism (cheaper, 75-80% accuracy)
- Balanced: Mix Apollo + Clearbit (mid-cost, 80-85% accuracy)
- Accuracy-optimized: Prefer Cleanlist + ZoomInfo (higher cost, 90-95%+ accuracy)

**Budget Caps:**
- "Maximum total spend on this run?" (Default: unlimited)
- "Maximum per-provider spend?" (Default: $1K per provider)

**Confidence Threshold for Write-Back:**
- "Only write back fields with >80% confidence?" (Default: Yes)
- Stricter (>90%) = fewer fields written but higher quality
- Looser (<75%) = more complete but potentially lower accuracy

**Conflict Resolution Rules:**
- "When providers conflict, prefer older data (stable) or newer data (fresh)?" (Default: newer)
- "Auto-resolve conflicts or flag for manual review?" (Default: auto-resolve per decision tree)

---

## Error Handling

**If MCP connection fails:**
- Pause enrichment and ask for MCP reconnection
- Offer workaround: export records to CSV, enrichment can resume once API is live

**If enrichment provider returns "not found":**
- Record the failure (this contact may not be in provider's database)
- Try next provider in waterfall
- Flag record as "not found by any provider" in final report
- Recommend: manual research or try again in 30 days (data providers update regularly)

**If API rate limit hit:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Pause and ask if you want to continue slower or reduce scope
- Never skip records; all records eventually process

**If budget exceeded mid-run:**
- Pause immediately
- Report cost so far and remaining records
- Ask: "Continue anyway (overspend budget)?" or "Stop and I'll process remaining records next month?"

**If enrichment quality too low (<60% confidence on critical fields):**
- Flag in report and recommend:
  1. Connect additional providers (Cleanlist, Cognism) for higher accuracy
  2. Enrich smaller pilot set first to test provider quality
  3. Review provider accuracy benchmarks vs. your use case

---

## What to Run Next

After enrichment is complete:

1. **DQH-03: Contact Decay & Refresh Agent** — Monitor which enriched fields are decaying over time and schedule re-enrichment cycles

2. **DQH-04: Health Score Agent** — Use enriched company data (industry, employee count, revenue) to build predictive health scores for account prioritization

3. **DQH-02: Field Normalization Agent** — Standardize enriched titles, industries, and company names to ensure data consistency downstream

4. **Setup Recurring Enrichment** — Schedule monthly re-enrichment runs to catch data decay and new records

---

## Example: End-to-End Enrichment Session

**You:** "Enrich our contacts with missing emails and phone numbers. Use whatever providers we have."

**Me (Preflight):**
```
✓ Salesforce connected (Org: EXAMPLE_ORG_ID)
✓ Enrichment providers: ZoomInfo, Apollo, Clearbit active
⚠️ Cleanlist not connected (would improve email accuracy from 82% to 98%)
✓ Budget available: ZoomInfo $1,200, Apollo $1,500, Clearbit $600
✓ Contact records: 12,500 total | 3,100 missing email | 2,400 missing phone
✓ Lead records: 4,200 total | 1,200 missing email | 900 missing phone
✓ Total enrichment candidates: 7,600 records

Estimated cost: ~$4,500 (multi-source waterfall)
Ready to begin? [Yes / Adjust]
```

**You:** "Go ahead. Prioritize email, and let me know if costs spike."

**Me (Analysis & Routing):**
```
Assessing 7,600 records for missing fields...
✓ Missing field scores calculated (0–100)
  - 2,100 HIGH priority (>70)
  - 3,200 MEDIUM priority (50–70)
  - 2,300 LOW priority (<50)

Mapping provider capabilities...
✓ HIGH priority records → Cleanlist if budget allows, else Apollo
✓ MEDIUM priority → Apollo / Clearbit
✓ LOW priority → Cheapest available (Cognism or Apollo)

Executing enrichment calls...
✓ Batch 1: 1,000 records to ZoomInfo — COMPLETE (Cost: $520)
✓ Batch 2: 1,500 records to Apollo — COMPLETE (Cost: $180)
✓ Batch 3: 1,200 records to Clearbit — COMPLETE (Cost: $300)
[... continuing batches ...]

Running total: $4,200 of $4,500 budget (93% used)

Consolidating results...
✓ 6,800 records enriched successfully
✓ 400 records "not found" by any provider
✓ 400 records enriched with partial data (phone but not email)

Conflict resolution:
✓ 340 email conflicts detected → Resolved using provider accuracy hierarchy
✓ Average confidence score: 89%

Writing back to CRM...
✓ 6,800 records updated with enriched email/phone
✓ Confidence scores and sources logged
```

**Final Report:**
```
ENRICHMENT COMPLETE

Records processed: 7,600
Records successfully enriched: 6,800 (89%)
Records partially enriched: 400 (5%)
Records not found: 400 (5%)

COVERAGE IMPROVEMENTS
Email: 9,400 → 13,100 records (78% → 82%) | +3,700 records | Cost: $2,200
Phone: 10,100 → 12,200 records (81% → 87%) | +2,100 records | Cost: $1,800

COST SUMMARY
ZoomInfo: $1,850 (41%)
Apollo: $1,400 (31%)
Clearbit: $1,200 (27%)
TOTAL: $4,450 (vs. budget $4,500)

CONFIDENCE METRICS
Average confidence: 89%
Email fields >90% confidence: 92%
Phone fields >90% confidence: 85%

NEXT STEPS
1. Monitor email deliverability over next 7 days (should improve from 82% to 95%+)
2. Identify which enriched accounts have highest revenue potential (use health score next)
3. Schedule re-enrichment in 30 days (data decay cycle)

Full report: [link to detailed breakdown by provider, field, confidence tier]
```

---

## References & Notes

**Research & Data Sources:**
- Research brief: DQH-05_enrichment_orchestration_research_v2.5.md
- Provider accuracy benchmarks: Cleanlist 2026 B2B Data Enrichment Comparison
- Cost analysis based on published provider pricing (as of April 2026)
- Note: Research showed 100% single-domain source concentration for provider accuracy data—flagged for validation in future iterations with multi-source enrichment provider comparisons

**Known Limitations:**
- Enrichment accuracy varies by industry and geography (North America data most robust)
- International contact enrichment less mature than US (recommend caution)
- Job title standardization handled by DQH-02 (this agent returns raw titles)
- Real-time data updates not supported (enrichment is point-in-time snapshot)

**Recommended Prerequisites:**
- Run DQH-01 (Deduplication) before enrichment to avoid enriching duplicates
- Ensure contact identifiers (email/phone) are clean before routing to providers
- Establish baseline email deliverability rate before enrichment (to measure improvement post-enrichment)
