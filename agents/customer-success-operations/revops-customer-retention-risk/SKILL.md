---
name: revops-customer-retention-risk
description: Consolidates product usage, support health, customer sentiment, and engagement
  signals into a unified weekly health score. Predicts which accounts will churn or
  fail to renew 60-90 days in advance, enabling proactive intervention before revenue
  is lost.
metadata:
  trigger_phrases:
  - assess customer retention risk
  - identify at-risk accounts
  - evaluate churn risk
  - check renewal health
  - score customer health
  - predict churn and renewal
  - flag renewal risk accounts
  - measure account risk
  category: Customer Success Operations
  phase: 30_days
  data_readiness: 30_days
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents: []
    mcps:
    - Salesforce MCP (or HubSpot MCP)
    - Product Analytics MCP (Amplitude, Mixpanel, Pendo, or equivalent)
    - Support/Helpdesk MCP (Zendesk, Intercom, HubSpot Service Hub, or equivalent)
    - Snowflake MCP or BigQuery MCP (optional but recommended)
    minimum_data:
    - CRM Account object with email domain, industry, employee count, auto-renew flag
    - 'Product analytics data: DAU, MAU, core feature adoption, usage events (30–60
      day window)'
    - 'Support ticketing data: ticket count, creation/resolution times, ticket descriptions
      (30–60 day window)'
    - NPS/CSAT survey responses (90-day window, minimum 30 responses for account population)
    - 'CRM activity log: calls, emails, meetings linked to accounts (60-day window)'
    - 'Contract/billing data: renewal dates, MRR/ARR, auto-renew status, payment status'
    - 'Account linking: Product Account ID ↔ CRM Account ID ↔ Billing Customer ID
      mapping'
  output_format: Markdown report + JSON + CSV export
---

# Customer Retention Risk Agent (CSO-CUST-01)

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager or Customer Success Operations Manager at B2B SaaS companies, 100–500 employees, North America, managing 50–500 customer accounts.

**The painkiller pain points we're solving:**

### Pain Point 1: Inability to Predict Churn/Renewal Failure Before Intervention Windows Close

**Problem:** Mid-market RevOps and CS operations managers lack a unified signal that surfaces accounts entering the danger zone 60–90 days before renewal. Teams fly blind without consolidated health scores, relying on manual QBRs or crisis mode when accounts announce non-renewal.

**Quantified cost to the role:** 
- SaaS industry average annual churn: 10–14% (vs. <5% best-in-class benchmark). This 5–9% gap represents 5–9% of ARR leakage annually.
- For a $20M ARR company, this equals $1–1.8M in unnecessary revenue loss per year.
- Typical SaaS acquisition cost (CAC) is 3–5x monthly recurring revenue (MRR), so each churned account wastes $15K–$150K in customer acquisition costs.
- **What teams do today:** Manually maintain spreadsheet health scores updated quarterly; by renewal time, data is stale and intervention windows are closed. Teams that use CS platforms (Gainsight, ChurnZero) have static health scores that miss late-stage risk signals.

**Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence. "Risks flagged 60–90 days before renewal give teams room to intervene without last-minute panic" (Renewal Probability Scoring, SparkCo). "SaaS companies experiencing a 30% increase in support tickets related to product functionality see a 10–15% increase in customer churn over the following quarter if issues remain unresolved" (Support Ticket Volume, GetMonetizely).

---

### Pain Point 2: Data Fragmentation Across Systems Blocks Real-Time Health Assessment

**Problem:** Product usage lives in analytics platforms, support tickets in helpdesks, NPS in survey tools, and CRM activity in Salesforce/HubSpot. RevOps managers spend 10–15 hours per week stitching these together in spreadsheets, or give up and rely on gut feel.

**Quantified cost to the role:**
- Data integration tax: 2–4 hours per week maintaining even a basic health score dashboard.
- For a RevOps team of 3, this equals 312–624 hours annually = $31K–$62K in labor waste.
- "Companies integrating at least three data sources see 32% higher prediction accuracy" (Churn Prediction Models, UserPilot), implying most teams use 1–2 sources and have unreliable predictions.

**Evidence quality:** 4/4 rubric criteria. "Poor data quality, setting clear benchmarks, and determining appropriate metric weighting are primary challenges" (Health Score Challenges, SupportBench). "Manual scoring systems lead to outdated information and inconsistent decision-making" (Health Scoring, SuccessCOACHING).

---

### Pain Point 3: No Consistent Playbook for Tiered Intervention Based on Risk Level

**Problem:** Without clear playbooks, teams can't distinguish between "yellow flag: customer is quiet, needs engagement" and "red flag: revenue at risk, needs executive intervention." Everything escalates (alert fatigue) or nothing escalates (churn goes unmanaged).

**Quantified cost to the role:**
- Alert fatigue reduces intervention effectiveness: teams investigating low-risk accounts while high-risk ones slip through.
- Result: Same intervention (check-in call) applied to 20% health accounts and 80% health accounts wastes intervention capacity on likely-to-renew accounts while high-risk ones are missed.

**Evidence quality:** 4/4 rubric. "Determining appropriate metrics and weighting is complex; different businesses have varying customer success goals, making it difficult to establish universal metrics" (Health Score Metrics, Coefficient).

---

### Pain Point 4: Renewal Risk and Churn Risk Are Treated Separately, Missing Cross-Functional Dependencies

**Problem:** Renewal risk scoring lives in Salesforce. Churn prediction lives in ChurnZero. Health scores sit in Vitally. None talk to each other, so teams can't align on which accounts need renewal-focused saves vs. churn-focused health checks.

**Quantified cost to the role:**
- Existing customers now generate 40% of new ARR across B2B SaaS. Yet renewal and churn are typically managed by separate teams with separate tools.
- An account can have high engagement (low churn risk) but be at renewal risk due to contract terms or budget cuts. Scoring them separately means Sales doesn't know Renewal is at risk, or CS doesn't know to proactively upsell.

**Evidence quality:** 4/4 rubric. "Existing customers now generate 40% of new ARR across B2B SaaS, and over 50% for companies above $50M ARR" (B2B SaaS Retention, CustomerScore), yet teams manage them separately.

---

## What This Agent Does

The Customer Retention Risk Agent is your unified health score engine. It scans your CRM, product analytics, support ticketing, and survey data to generate a single, actionable account health score every week. Instead of juggling four different platforms (each with a different score), you get one consolidated health signal: your account is Green (healthy, low touch), Yellow (at risk, needs attention), or Red (critical, escalate now).

The agent combines four critical signals:
- **Product Usage** (35%): Are customers logging in? Using core features? Or has engagement suddenly dropped?
- **Support Health** (25%): How many support tickets? How fast are we resolving them? Is sentiment improving or deteriorating?
- **Customer Sentiment** (20%): What does NPS, CSAT, and in-app feedback tell us about satisfaction?
- **Engagement & Growth** (15%): How active is your team with the customer? Are they expanding or stalling?

From these signals, the agent calculates two risk scores—**Churn Risk** (0–100, where 100 = imminent churn) and **Renewal Risk** (0–100, where 100 = likely non-renewal)—plus an **Overall Health** score and a specific **playbook recommendation** (e.g., "product quality fix," "expansion push," "executive save play").

You'll get a detailed report showing which accounts are at risk, why, and what to do about them. The scores automatically write to your CRM, and high-risk accounts trigger alerts to your team within minutes of scoring completion.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your data connections, confirm required data exists, assess data quality and readiness, and ask you to define your scoring scope.

**Step 1: MCP Connection Verification**

I'll check if your required MCPs are connected and authenticated:
- Salesforce MCP or HubSpot MCP (mandatory; choose one)
- Product Analytics MCP (Amplitude, Mixpanel, Pendo, etc.)
- Support Ticketing MCP (Zendesk, Intercom, HubSpot Service Hub, etc.)

**Go/No-Go decision:**
- ✓ All required MCPs connected → Proceed
- ⚠️ One MCP missing → Offer workaround (manual data upload, query via API key) or note it will affect confidence
- ✗ CRM MCP not connected → No-go; agent cannot write scores back or read account data

**Step 2: Required Data Validation**

I'll verify that your CRM and external systems have these minimum fields:

| System | Required Fields | Status |
|--------|-----------------|--------|
| **CRM (Salesforce)** | Account Name, Email Domain, Industry, Auto-Renew flag, Contract/Renewal dates, MRR | ✓/✗ |
| **Product Analytics** | DAU, MAU, core feature list, feature usage events | ✓/✗ |
| **Support Ticketing** | Ticket count, creation date, resolution time, title/description | ✓/✗ |
| **Surveys** | NPS score, CSAT score, response date | ✓/✗ |
| **CRM Activity** | Calls, emails, meetings linked to account | ✓/✗ |

**If a field is missing:** I'll flag its impact. For example, "No NPS responses in past 90 days → Sentiment score will use CSAT only; confidence reduced by 10%."

**Step 3: Data Quality Assessment**

I'll calculate:
- **Completeness:** % of accounts with all required fields (target: >80%)
- **Recency:** When was data last synced? (target: <24 hours old)
- **Data readiness:** Do we have 30+ days of historical data? (30-day tier requirement)
- **Account linking quality:** % of accounts successfully mapped across systems (target: >85%)
- **Estimated duplicate rate:** Sample ~50 accounts; flag potential duplicates

**Example Quality Report:**
```
CRM Data Quality:
✓ 950 accounts in Salesforce (95% of expected 1,000)
✓ 912 accounts have renewal date (96%)
✓ 885 accounts have MRR field (93%)
⚠️ 78 accounts missing email domain (8%) → Will use company name + employee count as fallback

Product Analytics Quality:
✓ 850 accounts successfully linked to product (90%)
✓ Data freshness: 6 hours old (yesterday at 2 PM)
✓ 30+ days of usage events available for all linked accounts

Support Data Quality:
✓ 900 accounts have support history (95%)
⚠️ Ticket descriptions: 12% missing (integration gap?) → Sentiment analysis will use title only

NPS/CSAT Quality:
⚠️ 320 accounts with recent NPS (33% response rate) → Confidence -15%
✓ 650 accounts with CSAT from support (69%)

Account Linking Quality:
✓ 905 accounts linked across CRM + Product + Support (95%)
✓ 8 unmappable accounts (missing critical IDs) → Will be excluded from scoring

Overall Data Readiness: 88% (above 30-day minimum threshold)
```

**Step 4: Define Your Scoring Scope**

Before running analysis, I'll ask:

1. **"Do you want to score ALL accounts, or a specific cohort?"**
   - All accounts (recommended for first run)
   - Specific segment (e.g., >$5K MRR, created in last 90 days, specific regions)
   - Pilot (top 50 accounts)

2. **"What's your target refresh cadence?"**
   - Weekly (recommended; aligns with standard CS business cycle)
   - Monthly
   - On-demand (ad-hoc scoring)

3. **"Which team should receive Red-tier alerts?"**
   - CS team leads (default)
   - CS Manager + Sales VP (for escalations)
   - Custom Slack channel or email group

4. **"Any accounts to exclude?"** (e.g., "Don't score startup accounts with <30 days of usage")

**Preflight Report Example**

```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Amplitude analytics connected (Project ID: proj_xyz)
✓ Zendesk support connected (Subdomain: company.zendesk.com)
✓ NPS platform connected (Delighted)

✓ CRM data: 950 accounts, 96% with renewal dates
✓ Product data: 850 accounts linked, 30+ days of usage available
✓ Support data: 900 accounts with tickets, recency: 6 hours
⚠️ NPS data: 320 responses (33% response rate, lower confidence)

✓ Account linking quality: 95% coverage
✓ Data readiness: 88% completeness (30-day minimum met)

Confidence Level: 78% (sufficient for scoring; improves as outcomes feed back)

Scope: Score all 950 accounts | Weekly cadence | Alerts to #cs-operations Slack channel

RECOMMENDATION: PROCEED with scoring
Next step: Explain the scoring model and weights before running first batch?
```

---

## Step-by-Step Workflow

### Step 1: Fetch Data from All Sources (Parallel)

**What I'll do:**
- Query CRM Account object: all accounts or your filtered scope (in 1,000-record batches)
- Query Product Analytics API: fetch DAU, MAU, feature usage for each linked account (30–60 day windows)
- Query Support Ticketing API: fetch ticket count, creation dates, resolution times, sentiment data (30–60 day windows)
- Query Survey Platform API: fetch latest NPS, CSAT responses for each account (90-day window)
- Query CRM Activity: fetch calls, emails, meetings linked to accounts (60-day window)
- Query Billing/Contract System: fetch renewal dates, MRR, auto-renew status, payment status

**Parallelization:** All API calls run in parallel to minimize wall-clock time. I'll show a progress indicator ("Fetching 950 accounts... 25% complete").

**Data I'll capture for each account:**
- Account ID, Name, Email Domain, Industry, Employee Count, Account Owner
- DAU (30d), MAU (30d), Core Feature Adoption, Usage Volatility
- Ticket Count (30d, 60d), MTTA, MTTR, Escalation Count
- Latest NPS score, CSAT rolling average, In-app feedback sentiment
- Activity Count (60d), C-level engagement, Expansion signals (new users, tier upgrades, MRR growth)
- Renewal Date, Days Until Renewal, Current MRR, Auto-Renew Flag, Payment Status

**Error handling:** If a single account's data fetch fails, log it and continue; don't block the whole run. I'll report failures at the end.

---

### Step 2: Prepare & Normalize Data

**Account Linking:** For each account, establish a 1:1 mapping across systems using this priority:
1. Explicit ID mapping (if maintained in your data warehouse)
2. Email domain + company name fuzzy match
3. Company name + employee count match

If an account can't be confidently linked, flag it for manual review; don't score it.

**Data Normalization:**
- Convert all metrics to 0–100 scale (e.g., DAU/MAU ratio → 0–100 engagement score)
- Apply 30-day rolling averages to smooth spiky data
- Detect anomalies: usage drop >30% in <7 days, ticket spike >50% vs. baseline
- Handle missing data: replace with neutral defaults (50/100) or exclude the component with confidence penalty

**Exemplar Anomaly Detection:**
- Usage drops from 25 daily logins to 8 daily logins within 3 days → Flag as "sudden drop"; churn risk elevated
- Support tickets jump from 2 to 5 in one week → Flag as "spike"; investigate sentiment

---

### Step 3: Calculate Component Scores

I'll calculate four component scores (each 0–100):

#### **Usage Score (35% weight)**

Formula: `Usage = 0.4 × DAU_Trend + 0.3 × Feature_Adoption + 0.3 × Usage_Volatility`

- **DAU Trend:** Compare 30-day average to 60-day baseline. Growth ≥15% → 100. Decline >30% → 0.
- **Feature Adoption:** % of available features used. <20% adoption → 0–20. >80% adoption → 90–100.
- **Usage Volatility:** Consistency of login patterns. Coefficient of variation <0.3 (steady) → 95. >1.0 (erratic) → 20.
- **Critical Signal:** If daily logins drop >50% in <3 days, override to 0 (imminent churn signal).

**Interpretation:**
- 80–100: Healthy, consistent usage; product engagement strong
- 40–79: Moderate usage; some adoption gaps or minor volatility
- 0–39: Low usage or usage collapse; high churn risk

---

#### **Support Health Score (25% weight)**

Formula: `Support = 0.35 × Ticket_Volume + 0.35 × Sentiment + 0.2 × Resolution_Efficiency + 0.1 × Escalations`

- **Ticket Volume:** Detect spikes. 30-day vs. 60-day baseline. Spike <10% → 90–100. Spike >100% → 0.
  - Exception: High ticket volume + positive sentiment (engagement tickets) → Boost score by +20
- **Sentiment:** NLU classification of ticket titles/descriptions. Blockers (−20 pts/ticket), frustration (−5 pts/ticket), engagement (+10 pts/ticket). Aggregate over 30 days: Score = Clamp(50 + points, 0, 100).
- **Resolution Efficiency:** MTTA (mean time to acknowledge) ≤4 hours → 100. MTTR (mean time to resolve) ≤48 hours → 100. Scale down for slower response/resolution.
- **Escalations:** 0 escalations → 100. ≥3 escalations → 0.

**Interpretation:**
- 80–100: Responsive support, positive sentiment, no escalations
- 40–79: Mixed signals; some tickets or delays but recovering sentiment
- 0–39: Support issues (volume, delays, sentiment, escalations); intervention needed

---

#### **Sentiment Score (20% weight)**

Formula: `Sentiment = 0.5 × NPS + 0.3 × CSAT + 0.2 × InApp_Feedback`

- **NPS:** Latest score from survey (within 90 days). Promoter (≥9) → 90–100. Passive (7–8) → 50–70. Detractor (0–6) → 0–40. Apply recency decay: old data (>60 days) → capped at 50.
  - No recent NPS → default to 50 (neutral)
- **CSAT:** Rolling 30-day average from support surveys. Convert to 0–100 scale.
  - <5 responses → flag low sample confidence
  - Zero responses → default to 50
- **In-App Feedback:** Sentiment from product feedback (Pendo, Canny, etc.). Positive → +10 pts/item. Negative → −10 pts/item. Score = Clamp(50 + points, 0, 100).

**Interpretation:**
- 80–100: High NPS, satisfied with support, positive sentiment
- 40–79: Mixed sentiment; some concerns but not critical
- 0–39: Detractors, low CSAT, negative feedback; retention at risk

---

#### **Engagement & Expansion Score (15% weight)**

Formula: `Engagement = 0.3 × Login_Frequency + 0.25 × Feature_Breadth + 0.25 × CRM_Activity + 0.2 × Expansion_Signals`

- **Login Frequency:** Days active per week (avg 30 days). 5+ days/week → 95–100. 1–3 days/week → 40–70. 0 days → 0.
- **Feature Breadth:** Unique features used / total available. <5% → 0–25. >50% → 75–100.
- **CRM Activity:** Count of calls, emails, meetings in 60 days. 0 activities → 0. 8+ activities → 85–100. Boosters: +10 for customer-initiated, +10 for executive involvement, +10 for positive outcome. Detractors: −10 for "save play" emergency calls.
- **Expansion Signals:** Track new users added, tier upgrades, add-on purchases, MRR growth in 90 days. New user: +5 pts/user. Tier upgrade: +20 pts. Add-on: +15 pts. MRR growth >10%: +20 pts. Score = Clamp(50 + points, 0, 100). No expansion signals → 50 (neutral, not declining).

**Interpretation:**
- 80–100: Active login patterns, broad feature use, strong CS engagement, expansion signals
- 40–79: Moderate engagement; some activity and growth
- 0–39: Inactive or disengaged; no expansion; at-risk for churn

---

### Step 4: Calculate Risk Scores

**Churn Risk Score (0–100, inverted from health components):**
```
Churn_Risk = 100 − (0.35 × Usage + 0.25 × Support + 0.2 × Sentiment + 0.2 × Engagement)
```
- 0–20: Safe (strong signals across all dimensions)
- 20–40: Low risk (some weakness but mostly healthy)
- 40–60: Moderate risk (mixed signals; intervention can help)
- 60–80: High risk (multiple red flags; urgent intervention needed)
- 80–100: Critical (imminent churn risk; all-hands escalation)

**Renewal Risk Score (0–100, contract-adjusted):**
```
Base = 100 − weighted components (same formula as Churn)
Adjustments:
  + Days_Until_Renewal < 30? Reweight: Usage 20%, Support 35%, Sentiment 20%, Engagement 25% (support becomes more critical)
  + Days_Until_Renewal 30–90? Balanced weights (defaults)
  + Days_Until_Renewal > 90? Reweight: Usage 40%, Support 20%, Sentiment 25%, Engagement 15% (usage + satisfaction matter more)
  + Auto_Renew = TRUE? Reduce Renewal_Risk by 15 points
  + Auto_Renew = FALSE? Increase by 10 points
  + MRR declined >20% in 90d? Add 20 points (distress signal)
  + MRR grew >10% in 90d? Subtract 15 points (growth = strong renewal likelihood)
  + Payment_Status = "Past Due"? Add 25 points
  + Payment_Status = "Failed"? Add 20 points

Renewal_Risk = Clamp(Base + Adjustments, 0, 100)
```

**Overall Health Score (0–100, weighted aggregate):**
```
Overall_Health = 0.6 × (100 − Churn_Risk) + 0.4 × (100 − Renewal_Risk)
```
- Rationale: Weight renewals (40%) heavier than churn (60%) because revenue certainty is critical
- 80–100: Healthy (Green tier)
- 40–79: At risk (Yellow tier)
- 0–39: Critical (Red tier)

---

### Step 5: Assign Risk Tiers & Playbooks

**Green Tier (Overall Health 80–100):**
- Profile: Strong usage, positive sentiment, active engagement, healthy renewal outlook
- Churn Probability: <5% | Renewal Probability: >95%
- CS Cadence: Quarterly QBR, monthly check-in if expansion opportunity
- Playbook: Low-touch nurture (engagement focus)
- Sales Involvement: Minimal (expansion discussions only)

**Yellow Tier (Overall Health 40–79):**
- Profile: Mixed signals (e.g., usage flat but NPS declining; support spike but sentiment recovering)
- Churn Probability: 10–30% | Renewal Probability: 70–90%
- CS Cadence: Bi-weekly check-in, QBR if renewal <90 days
- Playbook (assign one based on signal pattern):
  - **"Product Quality"** if Usage down + Support issues up → Product fix + training
  - **"Value Realization"** if NPS down + Engagement low → QBR focus on ROI
  - **"Expansion Stall"** if Usage stable but MRR flat → Expansion strategy session
  - **"Save Play"** if renewal <60 days + risk rising → Executive engagement
- Sales Involvement: Medium (renewal support, possible save play)

**Red Tier (Overall Health 0–39):**
- Profile: Multiple red flags (usage drop, high support volume, low NPS, no engagement)
- Churn Probability: 50–80% | Renewal Probability: 20–50%
- CS Cadence: Weekly check-in + daily escalation monitoring
- Intervention Timeline:
  - Week 1: Executive account review, identify business blockers
  - Week 2: Propose solution (product fix, custom integration, cost relief)
  - Week 3: Customer sign-off + contract commitment
  - Week 4–8: Deliver solution, measure improvement
- Playbook: Executive save play (highest priority)
- Sales Involvement: High (VP-level engagement, contract review, product roadmap alignment)

**Escalation Triggers (override tier):**
- If Churn_Risk ≥ 80 OR Renewal_Risk ≥ 80 → Auto-escalate to CS Manager + Sales VP
- If BOTH Churn_Risk ≥ 80 AND Renewal_Risk ≥ 80 → Escalate to RevOps VP + CFO (risk: $500K–$5M+ ARR at stake)
- If Renewal_Date ≤ 30 days AND Risk_Status = Red → Escalate to Sales VP (last-minute save play)
- If Payment_Status = "Past Due" or "Failed" → Flag for Finance (payment risk)

---

### Step 6: Generate Output Report

I'll produce a comprehensive markdown report with:

**Summary**
- Total accounts scored
- Tier breakdown (# Green, # Yellow, # Red)
- Average scores by tier
- Key escalations (highest-risk accounts)

**Details**
- Table: Top 20 Red-tier accounts with Account ID, Health Score, Churn Risk, Renewal Risk, Days Until Renewal, Recommended Playbook, Account Owner
- Table: Yellow-tier accounts trending to Red (highest risk within tier)
- Chart: Score distribution (% of accounts in each tier)
- Explanation: Why each Red/Yellow account is flagged (which component scores are driving risk?)

**Data Quality & Limitations**
- Account linking coverage: % of accounts successfully mapped across systems
- Data recency: How old is each data source?
- Component confidence: Which signals had missing or incomplete data? How does that affect scores?
- Known limitations: "We only have 4 weeks of NPS responses; confidence improves after 8 weeks." "12% of support tickets missing descriptions; sentiment analysis uses title only."
- Score reliability: Confidence score per account (0–100) based on data completeness

**Recommended Actions**
1. Review all Red-tier accounts (20–30 likely) with CS manager; initiate save plays for top 5
2. For Yellow-tier accounts, schedule QBRs within 2 weeks (use playbook assignments to prepare)
3. For unmappable or low-confidence accounts, escalate to data ops for cleanup
4. Schedule next scoring run (weekly recommended)
5. Set up webhook alerts: Slack notification when any account moves from Green to Yellow (early warning)

**Sources & Citations**
- CRM data pulled [timestamp] from Salesforce (950 accounts)
- Product analytics pulled [timestamp] from Amplitude (850 accounts linked)
- Support data pulled [timestamp] from Zendesk (900 accounts)
- NPS data pulled [timestamp] from Delighted (320 responses, 33% response rate)
- Account linking methodology: Email domain + company name fuzzy matching for unmapped accounts

---

## Configuration Options

Before running your first scoring cycle, you can tune these parameters:

**Component Weights (Default: 35% Usage, 25% Support, 20% Sentiment, 15% Engagement)**
- "Do you want to adjust these weights? E.g., if support is your biggest churn driver, boost to 35%?"
  - Conservative (emphasize usage): 45% Usage, 25% Support, 20% Sentiment, 10% Engagement
  - Balanced (default): 35% Usage, 25% Support, 20% Sentiment, 15% Engagement
  - Support-heavy (if you're a support-driven churn vector): 30% Usage, 35% Support, 20% Sentiment, 15% Engagement

**Feature Adoption Baseline (Default: 60% of features used = healthy)**
- "What's your 'minimum healthy feature adoption' threshold? (Low = 30%, Aggressive = 70%)"
  - This adjusts the feature adoption scoring curves

**NPS Response Rate (Default: flag if <30% accounts responded)**
- "Should I use NPS even if response rate is low? Or wait for more data?"
  - Aggressive: Use available NPS regardless of response rate (lower confidence)
  - Conservative: Only use NPS if ≥30% of accounts responded (higher confidence, smaller sample)

**Renewal Risk Window (Default: adjust weights if renewal <30 days)**
- "How many days before renewal should we boost Support weight? (Default: 30 days)"
  - E.g., "boost when <45 days" if your sales cycle is long

**Escalation Thresholds (Default: Red tier ≥80% Churn Risk OR ≥80% Renewal Risk)**
- "Should we escalate at different thresholds? (E.g., ≥70% Churn Risk for more aggressive outreach?)"

**Output Channels (Default: Write to CRM + JSON export + Slack alerts)**
- "Should I also export to CSV? Trigger webhooks to ChurnZero/Vitally/Marketo?"
- "Which Slack channel should receive Red-tier alerts?"

---

## Error Handling

**If MCP Connection Fails:**

```
I couldn't connect to Salesforce to pull account data.

Reason: Salesforce MCP authentication expired or credentials missing.

What to do:
1. In Claude Code settings, reconnect Salesforce MCP
2. You'll be prompted to approve API access
3. Once connected, run this request again

In the meantime, I can:
- Work with a CSV export of your accounts (paste data directly)
- Help you debug the connection (check API key, org ID, user permissions)
```

**If Required Data Is Missing:**

```
I found significant gaps in your data that will affect confidence:

Missing Data:
- 150 accounts (16%) missing renewal dates → Can't assess renewal risk accurately
- 50 accounts (5%) not linked to product analytics → Can't score usage

Impact:
- Churn risk scores for unlinked accounts will be degraded (confidence: 60% instead of 80%)
- Renewal risk can't be calculated without renewal dates (will default to 50/100 neutral score)

Recommended fixes:
1. Populate missing renewal dates in Salesforce (import from billing system or ask CSMs)
2. Link product analytics to CRM (use email domain + company name matching)
3. Re-run scoring after fixes

For now, I can:
- Score the 800 accounts with complete data (provide high-confidence results)
- Flag the 150–200 incomplete accounts for manual review
- Show you a report of what's missing and how to fix it
```

**If Data Quality Is Too Low (Insufficient Data Readiness):**

```
Your data isn't ready for scoring yet.

Data Readiness Audit:
- Product usage data: Only 2 weeks old (need 30 days minimum) ✗
- Support data: 3 weeks old ✓
- NPS data: Only 2 responses (need 30+) ✗
- Account linking: 72% coverage (need >80%) ⚠️

Result: 52% data readiness (threshold: 70%)

To proceed, you need:
1. Wait 2 more weeks for usage baseline (product data older than 30 days)
2. Collect 28 more NPS responses (launch survey campaign or wait for responses)
3. Improve account linking from 72% to >80% (map 80 more product IDs to CRM accounts)

Timeline: ~2–3 weeks to full readiness

Would you like:
- A preview report based on available data (lower confidence: 60%)?
- A checklist of what to do to get ready faster?
- To wait and retry in 2 weeks?
```

**If API Rate Limits Are Hit:**

```
Zendesk API rate limit reached while fetching ticket data.

Impact: Ticket volume and sentiment scores will be incomplete; re-running in 30 seconds.

Mitigation:
- Implementing exponential backoff (wait 2s, then 4s, then 8s between retries)
- Batching requests in 500-record increments instead of 1,000
- Retrying failed accounts in next scheduled run

If this persists: Reduce batch size or stagger scoring across 2–3 days instead of weekly.
```

**Graceful Degradation (Partial Results OK):**

```
I found 950 accounts to score, but hit some data issues. Here's what I can deliver:

Complete Scores (800 accounts):
- Full Usage, Support, Sentiment, Engagement scores
- Churn Risk, Renewal Risk, Overall Health
- Risk tier and playbook assignment
- Confidence: 85%

Partial Scores (150 accounts, missing renewal dates):
- Can score Churn Risk and component scores
- Cannot score Renewal Risk (needs renewal date)
- Defaulting Renewal Risk to 50/100 (neutral)
- Confidence: 65%
- Recommendation: Escalate to RevOps to populate missing renewal dates

Unmapped (no account linking):
- 8 accounts cannot be scored (data gaps too severe)
- Recommendation: Manual data cleanup or ask customer support

ACTION: I'll deliver a report with 800 high-confidence scores + 150 partial scores + 
a list of 8 accounts to fix. This gives you 95% coverage immediately; you can improve 
to 100% after data cleanup.
```

---

## What to Run Next

After CSO-CUST-01 completes its first scoring cycle:

1. **CSO-02: QBR Prep Agent** (Wave 2) — Depends on your health scores to prioritize which accounts need QBRs and what topics to cover. Feed this agent your Red/Yellow-tier accounts.

2. **CP-CAP-01: Revenue Capacity Planning Agent** (Wave 2) — Uses Churn Risk and Renewal Risk to forecast customer retention and plan CS headcount. Your scores are inputs.

3. **DQH-02: Field Normalization Agent** (parallel, if not run yet) — Standardizes company names, job titles, industries across your CRM. Complements CSO-CUST-01 by improving account linking quality.

4. **Set up recurring scoring** — Create a weekly schedule (recommended: Monday 8 AM) to run CSO-CUST-01 automatically. Feed outputs to your Slack #cs-operations channel or Salesforce dashboard.

5. **Integrate with your CS workflow** — Use the health scores + playbook assignments to automatically assign tasks in your CS platform (Gainsight, ChurnZero, Vitally). E.g., "When account moves to Red tier, create a QBR task for assigned CSM."

---

## Example: End-to-End Scoring Session

**You:** "Assess customer retention risk for all our accounts. I want to know which ones we're about to lose."

**Me (Preflight):**
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID, 950 accounts)
✓ Amplitude analytics connected (850 accounts linked, 45 days of usage data)
✓ Zendesk support connected (900 accounts with tickets)
✓ Delighted NPS connected (320 responses, 33% response rate)
✓ HubSpot CRM activity logged (900 accounts tracked)

Data Quality: 88% completeness (above 30-day minimum)
Account Linking: 95% coverage
Confidence Level: 78% (improves to 85%+ as NPS responses accumulate)

Ready to proceed with full scoring run? [Yes / Ask questions first]
```

**You:** "Yes, go ahead. Slack alert me when Red-tier accounts are identified."

**Me (Scoring):**
```
Fetching data from 4 systems... ✓ Complete (6 minutes)
Linking accounts across systems... ✓ Complete (950 accounts, 95% coverage)
Normalizing metrics... ✓ Complete
Calculating component scores... ✓ Complete (Usage, Support, Sentiment, Engagement)
Calculating risk scores... ✓ Complete (Churn, Renewal, Overall Health)
Assigning tiers and playbooks... ✓ Complete
Writing to Salesforce... ✓ Complete (950 custom field updates)
Generating alerts... ✓ Complete

SCORING COMPLETE: 950 accounts scored in 18 minutes
```

**Report (Markdown):**
```
## CUSTOMER RETENTION RISK SCORE — Weekly Cycle (April 15, 2026)

### Summary
Scored 950 accounts across your customer base. Identified 42 Red-tier (at-risk) 
accounts, 156 Yellow-tier (needs attention), and 752 Green-tier (healthy).

**Tier Breakdown:**
- Green (80–100 health): 752 accounts (79%)
- Yellow (40–79 health): 156 accounts (16%)
- Red (0–39 health): 42 accounts (4%)

**Escalations:**
- Critical (Churn + Renewal both Red): 3 accounts ($500K+ ARR at risk)
- High Renewal Risk (<30 days to renewal + Red tier): 8 accounts ($2M+ ARR)

### Details

**Red-Tier Accounts (Highest Risk — Immediate Action Required)**

| Account | MRR | Health | Churn Risk | Renewal Risk | Days to Renewal | Primary Issue | Playbook |
|---------|-----|--------|-----------|-------------|-----------------|--------------|----------|
| Acme Corp | $8K | 22 | 87 | 75 | 45 | Usage collapsed 40% | Executive Save Play |
| Beta Inc | $5K | 15 | 92 | 88 | 18 | Payment past due + support escalations | Save Play (Finance + CS) |
| Gamma LLC | $12K | 31 | 68 | 82 | 25 | Renewal risk with NPS declining | Contract Review + QBR |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Yellow-Tier Accounts (Medium Risk — Proactive Intervention)**

High-risk Yellow accounts (trending to Red):
- Delta Corp ($3.5K MRR): NPS dropped from 8 to 6; feature adoption flat. → Value Realization playbook
- Echo Tech ($4.2K MRR): Support spike (6 tickets in 2 weeks); positive sentiment. → Product Quality investigation
- Foxtrot Inc ($2.8K MRR): Expansion stalled; MRR flat for 60 days. → Expansion strategy session

### Data Quality & Limitations

- **Account Linking:** 95% coverage (905/950 accounts successfully linked across CRM + Product + Support). 45 accounts unmappable (missing email domain or product ID).
- **Data Recency:** Salesforce (6 hours old), Amplitude (6 hours), Zendesk (12 hours), NPS (updated daily). All current.
- **Component Confidence:**
  - Usage Score: 95% confidence (complete usage data for 850 linked accounts)
  - Support Score: 90% confidence (12% of tickets missing descriptions; sentiment analysis on titles only)
  - Sentiment Score: 75% confidence (33% NPS response rate; lower signal strength)
  - Engagement Score: 92% confidence (CRM activity fully logged)
- **Known Limitations:**
  - NPS response rate (33%) is below best-in-class (50%+); sentiment scores will improve as survey responses increase
  - Product feature list hasn't been updated in 60 days; feature adoption baseline may be stale
  - 8 accounts not scored due to missing data (recommend cleanup)

### Recommended Actions

1. **Immediate (This Week):**
   - Call all 3 Critical accounts (Acme, Beta, Gamma) with your VP of CS. Document blockers and propose solutions.
   - Escalate Beta's payment issue to Finance (past-due invoice + support strain).
   - Schedule executive save play for Acme (usage collapse is end-stage churn signal).

2. **Short-term (Next 2 Weeks):**
   - QBR all 42 Red-tier accounts with assigned CSMs. Use playbook recommendations to guide discussion topics.
   - Bi-weekly check-ins for Yellow-tier accounts; assess if trending to Green or Red.

3. **Medium-term (Next 30 Days):**
   - Implement product quality fixes for accounts with high support volume + usage decline (Delta, Echo).
   - Launch expansion campaign for stalling accounts (Foxtrot, others in Yellow tier).

4. **Data Improvements:**
   - Improve NPS response rate (currently 33%). Target 50%+ for stronger sentiment signals.
   - Update product feature list in Amplitude (feature adoption baseline needs refresh).
   - Clean up 45 unmappable accounts (populate missing email domains or product IDs).

### Sources & Citations

- **CRM Data:** Salesforce (pulled April 15, 6 AM PT). 950 accounts, 96% with renewal dates. 8 accounts missing.
- **Usage Data:** Amplitude (pulled April 15, 6 AM PT). 850 accounts linked. 100 accounts not yet integrated.
- **Support Data:** Zendesk (pulled April 15, 12 PM PT). 900 accounts with tickets (30–60 day window).
- **Sentiment Data:** Delighted (pulled April 15). 320 NPS responses (33% response rate). Qualtrics for in-app feedback.
- **CRM Activity:** Salesforce Activity objects (calls, emails, meetings). 60-day window. 900 accounts tracked.
- **Billing Data:** Stripe (pulled April 15). Renewal dates, MRR, payment status for 950 accounts.

**Scoring Model:** CSO-CUST-01 v1.0 (35% Usage, 25% Support, 20% Sentiment, 15% Engagement). Risk formula: Churn = 100 − (weighted health components). Renewal = Churn + contract adjustments.

**Confidence:** 78% overall (higher for Green tier, lower for accounts with missing NPS). Improves to 85%+ after 4 more weeks as sentiment data accumulates.
```

**Slack Alert (automated to #cs-operations):**
```
🚨 CRITICAL: 3 accounts at risk of churn AND non-renewal

| Account | Risk | Action |
|---------|------|--------|
| Acme Corp ($8K MRR) | Churn 87 | VP CS: Executive save play needed |
| Beta Inc ($5K MRR) | Renewal 88 | VP Sales + Finance: Payment + renewal at risk |
| Gamma LLC ($12K MRR) | Churn 68, Renewal 82 | CS Manager: Contract review + QBR |

⚠️ 42 Red-tier accounts total. 156 Yellow-tier trending to Red. View full report: [link]
```

**You (next week):** "Re-run scoring. Show me changes from last week."

**Me (Delta Report):**
```
CUSTOMER RETENTION RISK — Week-over-Week Changes (April 22, 2026)

Accounts Improved (moved from Red/Yellow to higher tier): 3
- Acme Corp: Health 22 → 38 (Yellow) [executive save play + product fix deployed]
- Delta Corp: Health 48 → 62 (Yellow) [Value Realization QBR completed]

Accounts Declined (moved to Red/Yellow): 2
- Hotel Tech: Health 75 (Green) → 42 (Yellow) [support spike: 5 tickets, sentiment negative]
- India Inc: Health 65 (Yellow) → 28 (Red) [usage drop 35%, NPS detractor, no activity]

Tier Breakdown Changes:
- Green: 752 → 755 (+3)
- Yellow: 156 → 157 (+1)
- Red: 42 → 38 (−4)

Action Items:
- 1 new Red-tier account (Hotel Tech) + 1 escalation (India Inc) to CS Manager
- Monitor Acme Corp weekly (showing improvement but still at risk)
- Celebrate Delta Corp (Value Realization playbook worked!)
```

---

## References & Further Reading

**Detailed Documentation (in references/ folder):**
- `scoring_formulas.md` — Full algorithm details with formulas and edge cases
- `data_mapping.md` — Account linking strategy and deduplication rules
- `playbook_library.md` — Tier-specific playbooks (Value Realization, Product Quality, Expansion Stall, Save Play) with templates and talking points
- `api_integration.md` — How to connect product analytics, support, and survey tools to CSO-CUST-01
- `webhook_configuration.md` — Set up webhooks to ChurnZero, HubSpot, Slack for automated alerts
- `sample_output.json` — Example JSON output for all 950 accounts (use for API consumption)

**Industry Benchmarks & Research:**
- "Net Revenue Retention in SaaS" — Industry average NRR: 105–110% (healthy). <95% indicates churn/downsell risk.
- "Churn Prediction Leading Indicators" — 70% of churns preceded by 30%+ usage drop (research: Vitally, Totango)
- "Support Ticket Volume & Churn Correlation" — 30%+ spike in support volume predicts 10–15% churn increase (research: GetMonetizely)
- "NPS as Renewal Predictor" — Detractors (NPS 0–6) are 3x more likely to churn; Promoters (NPS 9–10) are 2x more likely to upsell

**Related Agents (Wave 2+):**
- CSO-02: QBR Prep Agent — Uses health scores to prioritize QBRs and recommend topics
- CP-CAP-01: Revenue Capacity Planning Agent — Uses churn/renewal risk to forecast retention and plan CS headcount
