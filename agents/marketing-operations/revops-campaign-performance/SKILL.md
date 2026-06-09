---
name: revops-campaign-performance
description: Aggregates spend, impressions, clicks, and conversions across all marketing
  channels (Google Ads, LinkedIn, Meta, CRM campaigns) into a unified daily dashboard.
  Normalizes disparate field names into standard schema, detects anomalies (spend
  spikes, zero conversions, tracking gaps), and flags underperforming campaigns for
  reallocation decisions.
metadata:
  trigger_phrases:
  - aggregate campaign performance
  - show campaign metrics across channels
  - unified campaign dashboard
  - compare campaign spending by channel
  - analyze ad performance trends
  - check campaign roi across platforms
  - campaign data consolidation
  - detect underperforming campaigns
  - daily campaign performance report
  - multi-channel campaign analysis
  category: Marketing Operations
  phase: 30_days
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents: []
    mcps:
    - Google Ads MCP (recommended)
    - LinkedIn Ads MCP (recommended)
    - Meta Ads MCP (recommended)
    - HubSpot MCP or Salesforce MCP (for CRM campaign data)
    minimum_data:
    - 'Campaign object with: campaign name, spend/cost, impressions, clicks, conversions'
    - At least one ad platform API connection (Google Ads, LinkedIn, or Meta)
    - Or CRM campaign records (HubSpot Campaign or Salesforce Campaign)
  output_format: markdown + JSON dashboard + CSV export
---

# MO-01 Campaign Performance Agent

## Why This Agent Exists

**Who it's for (ICP):** Marketing Operations Manager or Demand Gen Manager at B2B SaaS, 100–500 employees, North America.

**The painkiller pain points we're solving:**

**1. Marketing teams spend 10–15 hours per week manually aggregating data from 15–50 ad platforms.**
- Your team logs into Google Ads, LinkedIn, Meta, HubSpot, email platforms, and webinars to export and consolidate performance data by hand. This costs $39k–$78k/year in labor alone, plus $24k–$96k/year in third-party BI tools. Automated daily aggregation frees 0.15–0.25 FTE and cuts data lag from 1–2 days to same-day.

**2. CMO and CFO cannot align on campaign performance because data is siloed and stale.**
- Your CMO and finance team argue about which campaigns drive revenue because marketing dashboards live in 5+ systems and update 1–2 days late. When aligned on a single truth, CMO-CFO teams increase marketing-driven revenue by 12% within 2 quarters. This agent unifies all campaign data into one daily-updated dashboard, cutting audit time by 60–80 hours/year.

**3. Teams waste 20–30% of campaign budget on underperforming channels because they lack daily visibility.**
- Without daily dashboards, you wait 1–2 weeks before reallocating budget away from money-losing channels. Meanwhile, 20–30% of spend continues to burn on underperformers. Companies with daily optimization achieve 30–40% better campaign performance than those optimizing weekly. For a typical $1M paid budget, daily visibility saves $250k–$300k annually in wasted spend.

---

## What This Agent Does

The Campaign Performance Agent is your unified campaign dashboard generator and anomaly detective. It pulls campaign spend, impressions, clicks, and conversions from Google Ads, LinkedIn, Meta, and your CRM, normalizes all the different field names and metric definitions into a single standard schema, detects anomalies (spend spikes, zero conversions, tracking gaps), and publishes an updated dashboard every day. You get a JSON dashboard for BI tools, a CSV snapshot for manual analysis, and an alert summary flagging underperforming campaigns. The agent handles currency conversions, timezone normalization, and multi-platform deduplication so you don't have to.

---

## Getting Started (Preflight Check)

When you trigger this agent, I'll verify your API connections, confirm required data exists, assess data quality, and ask you to scope your run.

**Step 1: MCP Connection Verification**
- I'll check if at least one ad platform MCP is connected (Google Ads, LinkedIn, or Meta).
- I'll check if at least one CRM MCP is connected (HubSpot or Salesforce) for campaign metadata.
- **If no ad platform is connected:** No-go; you need at least one. I'll guide you to connect one.
- **If CRM is missing:** Partial results possible; you'll get ad platform data only.
- **If successful:** Proceed to Step 2.

**Step 2: Required Data Validation**
I'll verify that your ad platforms and CRM have these minimum fields:
- **Ad Platforms (Google Ads, LinkedIn, Meta):** campaign_name, spend, impressions, clicks, conversions or lead_form_fills, date
- **CRM (HubSpot or Salesforce):** campaign_name, cost, status, created_date

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ 1–2 fields missing → Partial results possible; I'll flag the limitation
- ✗ Core fields missing (no spend/cost or no conversions tracking) → No-go; request data configuration first

**Step 3: Data Quality Assessment**
I'll calculate:
- % of campaigns with valid spend data (should be >80%)
- % of campaigns with conversion tracking configured (should be >50%)
- Data freshness (API lag; platforms report T+1 or same-day)
- Estimated campaign count across all platforms

**Step 4: Define Your Scope**
Before running the analysis, I'll ask:
- "Which date range? (Default: last 30 days rolling)"
- "Which platforms to include? (Default: all connected)"
- "Should I focus on paid campaigns only or include email/webinars?" (Default: paid campaigns; email/webinars phase 2)

**Preflight Report**
I'll summarize:
```
✓ Google Ads MCP connected
✓ Meta Ads MCP connected
⚠️ LinkedIn Ads MCP not connected (data will be incomplete for LinkedIn campaigns)
✓ HubSpot MCP connected
✓ Spend data quality: 94% of campaigns have valid spend (156 / 165 campaigns)
✓ Conversion tracking: 87% configured (143 / 165 campaigns)
✓ Data freshness: Google Ads (same-day), Meta (same-day), HubSpot (T+1)
✓ Ready to proceed

Scope: Last 30 days | Google Ads, Meta, HubSpot | Paid campaigns only

Next step: Authenticating to APIs and fetching campaign data...
```

---

## Step-by-Step Workflow

### Phase 1: Authentication & API Initialization

**What I'll do:**
- Retrieve API credentials for each connected platform (OAuth2 tokens or API keys)
- Test connectivity to each API (ping health endpoint)
- Log authentication timestamp and token expiration
- Confirm list of accessible campaigns (sample query)

**Error handling:**
- If any platform auth fails, skip it and proceed with available platforms
- Example: "Google Ads API unavailable (auth expired). Proceeding with Meta and HubSpot."

---

### Phase 2: Data Retrieval from Each Platform

For each connected platform, I'll query campaign metrics for your date range:

**Google Ads:**
- Query: campaigns, ad_groups, metrics
- Fetch: spend, impressions, clicks, conversions by campaign and date
- Result: 100–1,000 rows per day (varies by account size)

**LinkedIn Ads:**
- Query: campaigns, analytics
- Fetch: spent, impressions, clicks, lead_form_fills by campaign and date
- Result: 20–50 rows per day (fewer campaigns than Google)

**Meta Ads:**
- Query: campaigns, adsets, insights
- Fetch: spend, impressions, clicks, conversions (or leads) by campaign and date
- Result: 50–200 rows per day (varies by account structure)

**HubSpot / Salesforce Campaign:**
- Query: Campaign object
- Fetch: campaign_name, cost, status, created_date, associated contacts/leads count
- Result: 10–100 active campaigns per customer

---

### Phase 3: Data Normalization (Field Mapping)

I'll normalize all platform field names to a standard schema:

| Google Ads | LinkedIn | Meta | Salesforce | HubSpot | **Normalized Field** |
|---|---|---|---|---|---|
| campaign | campaignName | campaign_name | Name | name | campaign_name |
| cost | spent | spend | Cost__c | cost | spend_usd |
| impressions | impressions | impressions | — | hs_impressions | impressions |
| clicks | clicks | clicks | — | hs_clicks | clicks |
| conversions | leadFormSubmits | conversions | — | hs_conversions | conversions |
| date | date | date | CreatedDate | hs_created_date | date |

**Standardization rules:**
- All currency → USD (apply daily FX rate or agreed rate for GBP, EUR, CAD)
- All dates → ISO 8601 (YYYY-MM-DD) + UTC timezone
- Campaign names → trimmed, lowercased for dedup check
- Missing values → `null` (not 0, not empty string)

---

### Phase 4: Metric Calculation (Derived Fields)

For each normalized campaign record, I'll calculate:

```
ctr = clicks / impressions  (avoid divide-by-zero; ctr = null if impressions = 0)
cpc = spend_usd / clicks  (cost per click)
cpl = spend_usd / conversions  (cost per lead/conversion)
cpp = spend_usd / impressions  (cost per impression)
conversion_rate = conversions / clicks  (% of clicks that convert)
```

**Edge case handling:**
- If `impressions = 0` → set `ctr = null`, `cpp = null`
- If `clicks = 0` → set `cpc = null`, `conversion_rate = null`
- If `conversions = 0` → set `cpl = null`
- (Use `null` to signal missing data, not actual zero)

---

### Phase 5: Anomaly Detection & Data Quality Scoring

For each campaign record, I'll evaluate against anomaly rules:

| Anomaly | Rule | Severity | Action |
|---|---|---|---|
| **Zero impressions** | impressions = 0 | ⚠️ Warning | Campaign may be paused; flag for review |
| **CTR unusually high** | ctr > 5% | ⚠️ Warning | Exceeds 0.5–3% typical range; may indicate tracking error |
| **CTR unusually low** | ctr < 0.1% | ⚠️ Warning | Below typical range; quality issue or broad targeting |
| **CPC spike** | cpc > (7-day avg × 2) | 🔴 Alert | Budget efficiency concern; bid increase or competition change |
| **No conversions + high spend** | conversions = 0 AND spend > $1000 | ⚠️ Warning | Conversion tracking may be broken |
| **Currency mismatch** | Expected USD, received GBP | 🔴 Critical | Requires operator intervention |
| **Data lag** | Data timestamp > 24 hours old | ℹ️ Info | Platform API lag; dashboard will show stale numbers |

**Data Quality Score:**
- `data_quality_score = (valid_fields / total_fields) × 100`
- Example: 9 of 10 fields valid → 90% quality score
- Records with ≥2 anomalies flagged for manual review

---

### Phase 6: Deduplication & Multi-Channel Aggregation

**Same Campaign Across Multiple Platforms:**

Example: "Spring Product Launch 2026" runs on both Google Ads and LinkedIn.

```
Google Ads:   spend=$2,500, clicks=3,900, conversions=280
LinkedIn:     spend=$1,800, clicks=1,700, conversions=210

Action (v1): Keep separate by channel (for clarity)
Output:
  Spring Product Launch 2026 (Google Ads):  spend=$2,500, conversions=280
  Spring Product Launch 2026 (LinkedIn):    spend=$1,800, conversions=210

Note: "campaign_family" metadata will be added in v2 for rollup aggregation
```

**Exact Duplicate Detection (Same Campaign in Same Platform):**
- Rule: Two records are duplicates if (channel, campaign_id, date) tuple is identical
- Action: Sum metrics (spend, clicks, impressions); keep single record
- Likelihood: Low (platforms auto-deduplicate), but handled defensively

---

### Phase 7: Aggregation & Rollup

Group normalized records by dimension:

**By (date, channel):**
- Sum: spend, impressions, clicks, conversions
- Calculate: ctr, cpc, cpl, conversion_rate
- Count: campaigns, anomalies_detected

**By (date, campaign_name):**
- Sum: spend, impressions, clicks, conversions
- List: channels (google_ads, linkedin, meta)
- Add: campaign_metadata (owner, product_category, budget if from CRM)

**By date (total):**
- Sum: all metrics across all channels
- Calculate: aggregate_ctr, aggregate_cpc, aggregate_cpl
- Count: total_campaigns, active_channels, anomalies_count

---

### Phase 8: Output Generation

I'll deliver three outputs:

**A. JSON Dashboard (For BI tools, email, web viewers)**
```json
{
  "metadata": {
    "generated_timestamp": "2026-04-13T22:30:00Z",
    "date_range": { "start": "2026-04-13", "end": "2026-04-13" },
    "platforms_included": ["google_ads", "linkedin", "meta"],
    "data_freshness": "same-day",
    "quality_score": 0.95
  },
  "summary": {
    "total_spend_usd": 18500.00,
    "total_impressions": 1200000,
    "total_clicks": 28500,
    "total_conversions": 2100,
    "aggregate_cpl": 8.81,
    "active_campaigns": 45,
    "anomalies_detected": 3
  },
  "by_channel": [
    {
      "channel": "google_ads",
      "spend_usd": 8000,
      "impressions": 600000,
      "clicks": 15000,
      "conversions": 900,
      "cost_per_conversion": 8.89,
      "data_quality_score": 0.98
    }
  ],
  "top_campaigns": [...],
  "worst_performing": [...],
  "anomalies": [...]
}
```

**B. CSV Export (Daily Snapshot for pivot tables, manual analysis)**
```
date,channel,campaign_name,spend_usd,impressions,clicks,ctr,cpc,conversions,cost_per_conversion,data_quality_score,anomalies
2026-04-13,google_ads,Spring Product Launch,2500,145000,3900,0.0269,0.641,280,8.93,0.99,none
2026-04-13,linkedin,Webinar Promotion,1800,52000,1700,0.0327,1.059,210,8.57,0.97,none
```

**C. Alert Summary (For Slack/Email)**
```
Daily Summary:
• Total Spend: $18,500 | Impressions: 1.2M | Conversions: 2,100
• Overall CPL: $8.81
• Anomalies: 3 detected

⚠️ Attention Needed:
1. Retargeting Q2 (Meta): CPC spiked to $2.15 (baseline: $1.20)
2. Brand Awareness – GDN (Google): CPL $22.86 (2.5x channel avg)
3. Facebook Awareness Ads (Meta): Conversion tracking not configured
```

---

## Configuration Options

Before I start, you can customize these parameters:

**Matching Thresholds:**
- "What's your minimum CPC/CPL anomaly threshold?" (Default: 2× baseline = warning)
- "Should I flag all zero-impression campaigns or only high-spend ones?" (Default: all)

**Aggregation Level:**
- "Roll up by campaign, channel, or both?" (Default: both)
- "Include paused campaigns in dashboard?" (Default: exclude paused, flag separately)

**Data Range:**
- "Rolling window or fixed date range?" (Default: rolling 30 days)
- "What time of day should the daily run occur?" (Default: midnight UTC)

**Platform Filtering:**
- "Which platforms to include?" (Default: all connected)
- "Exclude any campaigns by name pattern?" (Default: none)

**Output Destinations:**
- "Should I email CSV to stakeholders?" (Default: no, dashboard only)
- "Slack channel for daily alert?" (Default: no, dashboard only)

---

## Error Handling

**If MCP connection fails:**
- Identify which platform(s) failed and why
- Offer immediate workarounds: use cached data from last run, or export CSV manually
- Provide reconnection instructions (no debugging required; clear next step)
- Example: "Google Ads API unavailable (OAuth token expired). Using last run's data + Meta/LinkedIn data for today. To include Google Ads, reconnect in Claude Code settings."

**If required data is missing:**
- Continue with available data; flag limitations clearly
- Example: "Campaign conversion tracking not configured on Meta. Showing spend, impressions, clicks, but CPL will be unavailable for Meta campaigns."
- Confidence score degrades accordingly (80% → 65%)

**If data quality is too low:**
- `>80% data completeness` → Proceed with full analysis; flag the gap
- `50–80% completeness` → Proceed with degraded output; lower confidence score (60–75%)
- `<50% completeness` → Refuse to proceed; explain why (too unreliable) and suggest fixes

**If API rate limits are hit:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (500 records instead of 1,000)
- Split run into multiple time windows if needed
- Alert user: "Rate limits hit; will retry tomorrow or split data range."

**If multi-platform data is inconsistent:**
- Flag specific inconsistencies (e.g., "clicks > impressions on LinkedIn Oct 15")
- Document assumptions used for reconciliation
- Example: "Meta reported zero conversions Oct 15; assuming tracking pixel offline. CPL unavailable for that day."

---

## What to Run Next

After campaign performance aggregation is complete:

1. **RA-03: Funnel Conversion Analysis Agent** — Join MO-01 campaign data with CRM lead/contact/opportunity records to calculate conversion rates (leads per dollar spent, conversions per campaign, revenue per campaign).

2. **ATTR-01: Attribution Engine Agent** — Use MO-01 baseline + RA-03 funnel data to model multi-touch attribution and answer "which campaign touchpoints influenced which pipeline stage?"

3. **RA-01: Weekly Revenue Narrative Agent** — Consume MO-01 dashboard for cross-channel reporting context in weekly exec updates.

4. **Schedule Recurring Runs** — Set up daily automated runs (e.g., 6 AM UTC every weekday) to keep dashboards fresh.

---

## Example: End-to-End Session

**You:** "Aggregate campaign performance across Google Ads and LinkedIn for the last 30 days and flag underperformers."

**Me (Preflight):**
```
✓ Google Ads MCP connected
✓ LinkedIn Ads MCP connected
⚠️ Salesforce MCP not connected (I'll use HubSpot CRM data for campaign metadata instead)
✓ Spend data quality: 92% of campaigns have valid spend
✓ Conversion tracking: 85% configured
✓ Data freshness: Both platforms same-day
✓ Ready to proceed

Scope: Last 30 days rolling | Google Ads, LinkedIn | Paid campaigns
```

**Me (Analysis):**
```
Fetching campaign data...
✓ Google Ads: 156 campaigns, 4,680 rows of daily metrics
✓ LinkedIn: 48 campaigns, 1,440 rows of daily metrics
Total: 204 campaigns, 6,120 records to process

Normalizing field names and calculating metrics...
✓ Normalized spend to USD
✓ Calculated CTR, CPC, CPL for all campaigns
✓ Detected 7 anomalies (CPC spikes, zero conversions, low CTR)

Aggregating by channel and campaign...
✓ Compiled summary by channel
✓ Ranked top 10 performers and bottom 10 underperformers
✓ Generated dashboard JSON + CSV + alert summary
```

**Report Output:**

**Summary**
You're spending $187,400 across 204 campaigns on Google Ads and LinkedIn. Overall cost per lead is $9.12, with Google Ads outperforming LinkedIn (Google CPL: $8.40, LinkedIn CPL: $10.80). 7 campaigns flagged as underperformers (CPL > 2× channel average or CTR < 0.5%).

**Details**
- **By Channel:**
  - Google Ads: $120,000 spend, 642 leads, $8.40 CPL (top performer)
  - LinkedIn: $67,400 spend, 424 leads, $10.80 CPL
- **Top 10 Campaigns:** Spring Product Launch (Google Ads, $8.12 CPL), Webinar Promotion (LinkedIn, $9.45 CPL), etc.
- **Worst Performers:** Brand Awareness GDN (Google Ads, $22.80 CPL, CTR 0.4%), Cold Outreach (LinkedIn, $18.50 CPL), etc.

**Data Quality & Limitations**
- Google Ads conversion tracking 100% configured; LinkedIn conversion tracking 78% (check LinkedIn Insight Tag installation)
- Data lag: Both platforms same-day; dashboard reflects activity through end of yesterday
- Currency: All USD (no multi-currency accounts detected)

**Recommended Actions**
1. Pause or optimize "Brand Awareness GDN" (CPL 2.7× Google Ads average)
2. Audit LinkedIn conversion tracking; 22% of campaigns missing pixel
3. Shift $10k weekly budget from underperforming to top 3 campaigns (estimated 15% CPL improvement)
4. Investigate why LinkedIn CPL is 29% higher than Google Ads; check audience/bidding strategy
5. Review "CPC spike" anomaly on Retargeting Q2 campaign (bid increase detected)

**Sources & Citations**
- Google Ads data: pulled 2026-04-14 08:00 UTC
- LinkedIn Ads data: pulled 2026-04-14 08:15 UTC
- FX rate (if applicable): N/A (USD only)
- Campaign metadata: HubSpot pulled 2026-04-14 08:30 UTC

---

## References & Further Reading

**Related Agents (Downstream):**
- **RA-03: Funnel Conversion Analysis Agent** — Joins campaign data with lead/opportunity records to calculate funnel metrics
- **ATTR-01: Attribution Engine Agent** — Multi-touch attribution modeling using MO-01 + RA-03 data

**Configuration & Troubleshooting:**
- Google Ads API: [Authentication & setup guide](https://developers.google.com/google-ads/api/docs/client-libs/python)
- LinkedIn Ads API: [Campaign Analytics documentation](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting-api)
- Meta Ads API: [Insights endpoint reference](https://developers.facebook.com/docs/marketing-api/reference/ad-account/insights)
- HubSpot Campaign API: [Campaigns object documentation](https://developers.hubspot.com/docs/api/crm/campaigns)
- Salesforce Campaign: [Campaign standard object reference](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_campaign.htm)

**Best Practices:**
- Run aggregation daily at consistent time (recommend 6 AM UTC) to minimize API throttling
- Archive CSV snapshots weekly for historical trend analysis
- Review anomalies weekly; adjust thresholds if too many false positives
- Audit conversion tracking configuration quarterly (especially on Meta)
- Monitor CPC trends weekly to catch bid changes early

