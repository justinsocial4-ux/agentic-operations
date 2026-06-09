---
name: revops-qbr-prep
description: Generates quarterly business review (QBR) materials for B2B SaaS customer
  accounts by synthesizing health scores from CSO-CUST-01, CRM account data, product
  usage trends, support history, and customer sentiment into cohesive, data-driven
  QBR narratives in 15–30 minutes. Prioritizes accounts by renewal urgency and risk
  tier; produces risk-tier-specific talking points and conversation starters for CSMs.
metadata:
  trigger_phrases:
  - generate qbr materials
  - prepare quarterly business review
  - build qbr deck
  - create qbr reports
  - prep qbr for accounts
  category: Customer Success Operations
  phase: 30_days
  data_readiness: 30_days
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents:
    - CSO-CUST-01 (Customer Retention Risk Agent)
    mcps:
    - Salesforce MCP or HubSpot MCP (mandatory)
    - Product Analytics MCP (Amplitude, Mixpanel, Pendo, etc.; optional but recommended)
    - Support/Helpdesk MCP (Zendesk, Intercom, HubSpot Service Hub; optional but recommended)
    minimum_data:
    - Health_Score__c, Churn_Risk__c, Renewal_Risk__c, Risk_Status__c populated on
      ≥80% of accounts by CSO-CUST-01
    - 'CRM Account data: ID, Name, MRR/ARR, Contract Term, Renewal Date, Account Owner'
    - 'CRM Contact data: Email, Phone, Title'
    - 'CRM Activity data: Tasks, Events, Calls with timestamps (≥30 days of history)'
  output_format: markdown
---

# CSO-02 QBR Prep Agent

## Why This Agent Exists

**Who it's for (ICP):** Customer Success Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Manual Data Gathering From Fragmented Systems
- **Problem:** CSMs spend 6–8 hours per account per QBR pulling data from CRM, product analytics, support, billing, and surveys.
- **Quantified cost:** $480–576 per account per QBR ($1,920–2,304/year × 4 QBRs). 5 CSMs × 15 accounts = $144k–$173k annual labor. [ChurnZero: From Burnout to Balance](https://churnzero.com/blog/from-burnout-to-balance-reinventing-qbr-workflows-for-cs-leaders/)
- **What teams do today:** Adopt CS platforms (Gainsight, ChurnZero, Totango: $30–50k/year), hire CS Ops reps ($85–100k/year), or use presentation tools (Slideform, Dock: $3–10k/year). [Velaris: Platform Pricing Comparison 2026](https://www.velaris.io/comparison/gainsight-vs-totango-vs-churnzero)
- **Why urgent:** CSMs choose between 8 hours/account on data (losing expansion discovery) or lightweight QBRs (missing churn signals). Over 12–24 months: lost expansion (20–30% target → 10–15% degraded), higher churn ($50k–$200k+ impact), 50% CSM turnover. [Bain: Why Software Companies' CS is Failing 2024](https://www.bain.com/insights/why-software-companies-customer-success-is-failing-tech-report-2024/)
- **Evidence quality:** 4/4 rubric criteria passed, 7 TIER 1 sources

### Pain Point 2: QBR Decks Lack Narrative Coherence
- **Problem:** CSMs manually synthesize 20–50 data points without consistent framework or template, resulting in data-heavy, insight-light decks.
- **Quantified cost:** $80–144 per account per cycle ($320–576/year), plus 1–2 week delays in renewal planning. 5 CSMs × 15 accounts = $24k–$43k labor on synthesis alone. [ChurnZero: From Burnout to Balance](https://churnzero.com/blog/from-burnout-to-balance-reinventing-qbr-workflows-for-cs-leaders/)
- **What teams do today:** Hire senior CSMs (salary premium +$30–50k), adopt presentation automation (Slideform, Dock: $3–10k/year), or purchase CS platform templates ($30–50k/year). [Slideform Blog: Automate QBRs](https://slideform.co/blog/automate-qbrs-with-slideform)
- **Why urgent:** Weak narratives delay renewals, weaken upsells, erode CSM credibility. Over 12–24 months: expansion drops 3–5 points (20–30% → 15–25%), renewal delays, customer perception shifts to reactive. $10M ARR company: 1–2 lost deals = 5–10% revenue impact. [TSIA: State of CS 2025](https://www.tsia.com/blog/the-state-of-customer-success-2025)
- **Evidence quality:** 4/4 rubric criteria passed, 5 TIER 1 sources

### Pain Point 3: Health Scores Not Translated Into QBR Narrative
- **Problem:** CSO-CUST-01 health scores lack account-specific narrative: why at-risk? What data drives it? What actions fix it? Health and QBR conversations remain disconnected.
- **Quantified cost:** $40–96 per account per quarter ($160–384/year) on manual health interpretation. 5 CSMs with 10–15% Yellow/Red = 5–7 high-touch accounts each, costing $4k–$13k annually. Misaligned scores delay intervention 1–2 weeks, reducing save-play success 10–15 percentage points. [CSO-CUST-01 Spec](https://sessions/beautiful-clever-mendel/mnt/EG's Agent List/_build/specs/CSO-CUST-01_customer_retention_risk_spec.md)
- **What teams do today:** Buy CS platforms with health-to-playbook workflows ($30–50k/year), hire CS Ops to translate scores ($85–100k/year), or build manual Slack/Airtable integrations. [Process.st: CS Operations](https://www.process.st/customer-success-operations/)
- **Why urgent:** Without translation, save-play effectiveness drops 15–20 points, health scores feel disconnected. Over 12 months: churn among at-risk accounts rises, CSMs ignore health signals as noise, downstream agents inherit unreliable health data. [ChurnZero: From Burnout to Balance](https://churnzero.com/blog/from-burnout-to-balance-reinventing-qbr-workflows-for-cs-leaders/)
- **Evidence quality:** 4/4 rubric criteria passed, 5 TIER 1 sources

---

## What This Agent Does

CSO-02 consumes weekly health scores from CSO-CUST-01, aggregates real-time CRM account data, product usage trends, support metrics, and customer sentiment, then generates risk-tier-specific QBR materials in Markdown format. For each account, it produces:

- **Account prioritization** (by renewal urgency + ARR)
- **Business snapshot** (health status + key wins/risks)
- **Metrics dashboard** (usage, sentiment, support, engagement)
- **Root cause analysis** (why is health Green/Yellow/Red?)
- **Conversation starters** (3–5 priority topics tailored to risk tier and playbook)
- **Expansion assessment** (opportunity or stabilization focus)
- **Data quality caveats** (what's missing, what drives confidence)
- **Recommended actions** (2–5 specific next steps for CSM)

Expected runtime: 15–30 minutes for 50 accounts (sequential); 5–10 minutes with parallelization.

---

## Getting Started (Preflight Check)

When you trigger this agent, I'll verify CRM connectivity, validate CSO-CUST-01 health scores, assess data quality, and ask you to scope your QBR run.

### Step 1: MCP Connection Verification

I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds (CSV export analysis, connection troubleshooting) or ask you to reconnect.
- **If successful:** Proceed to Step 2.

### Step 2: Dependency Validation

I'll verify that:
- CSO-CUST-01 health scores are populated on ≥80% of accounts
- Required CRM fields exist: Health_Score__c, Churn_Risk__c, Renewal_Risk__c, Risk_Status__c, Account ID, Name, MRR/ARR, Renewal Date
- Activity logging is enabled (Tasks, Events, Calls linked to Accounts)

### Step 3: Data Quality Assessment

I'll calculate:
- % of accounts with valid health scores
- % of accounts with valid renewal dates
- % of accounts with MRR/ARR populated
- Data freshness (when health scores were last updated)
- Estimated account count and risk tier distribution

### Step 4: Scope Your QBR Run

I'll ask:
- "Do you want to generate QBRs for ALL accounts, or a specific subset (e.g., renewal within 90 days, Yellow/Red accounts only, specific CSM segment)?"
- "How many accounts are in your target set? (Helps estimate runtime)"
- "Do you want analysis-only (show me what you'd generate), or ready-to-use (generate reports immediately)?"

### Preflight Report

Example output:
```
✓ Salesforce MCP connected
✓ CSO-CUST-01 health scores: Populated on 45 of 50 accounts (90%)
✓ CRM fields: All required fields present
✓ Data freshness: Health scores last updated 5 days ago (current)
✓ Account data: 99% have ID, 96% have renewal date, 94% have MRR
✓ Activity data: Last 30 days available on 48/50 accounts

Risk tier distribution:
  - Green: 28 accounts
  - Yellow: 14 accounts
  - Red: 3 accounts

Estimated runtime: 18–24 minutes for 50 accounts

Ready to proceed? [Yes / Define custom scope / Get more data first]
```

---

## Workflow

### Step 1: Account Prioritization

**Input:** All accounts with Health_Score__c populated

**Prioritization logic:**
- Bucket by Risk Status: Green (80–100), Yellow (40–79), Red (0–39)
- Within each bucket, sort by: [Days to Renewal ASC, ARR DESC]
- Assign priority tier: CRITICAL (Red + ≤30d), HIGH (Red/Yellow + ≤90d), SCHEDULED (Green or >90d)

**Output:** Ranked account list with priority, risk status, days to renewal, ARR

### Step 2: Data Aggregation (Per Account)

For each account in priority order, fetch and compile:

**CRM Data:**
- Account Name, MRR/ARR, Industry, Owner, Contract Term, Auto-Renew status
- Primary Contact Email/Phone/Title
- Contract renewal date (or calculated from start date + term)

**Health Score & Components (from CSO-CUST-01):**
- Overall Health Score (0–100)
- Churn Risk (0–100), Renewal Risk (0–100)
- Component scores: Usage, Support, Sentiment, Engagement
- Churn Risk Reason, Renewal Risk Reason
- Recommended Playbook (value-realization, product-quality, expansion-stall, save-play)
- Last Health Scored timestamp

**Product Usage Trends:**
- DAU/MAU ratio, core feature adoption %, last active date
- Trend (↑/→/↓) vs. 30-day baseline

**Support Health:**
- Ticket count (30d, 60d), MTTA, MTTR, escalations
- Sentiment summary (detractor/neutral/promoter)

**Customer Sentiment:**
- NPS score, CSAT, recent feedback quotes
- Engagement: Days since last email/call/meeting

**Expansion Signals:**
- New seat additions, feature expansion, upsell conversations in last 90 days

### Step 3: Narrative Generation

Apply risk-tier-specific template:

**For Green Accounts (Low-touch monitoring QBR):**
- Focus: Metrics validation, expansion opportunities, relationship maintenance
- Tone: Upbeat, forward-looking
- Length: 1–2 pages

**For Yellow Accounts (Standard QBR):**
- Focus: Root cause of health decline, stabilization playbook, intervention plan
- Tone: Balanced, data-driven, action-oriented
- Length: 2–3 pages

**For Red Accounts (High-touch save-play QBR):**
- Focus: Critical risk factors, executive alignment, intervention milestones, renewal urgency
- Tone: Urgent, executive-ready, accountability-focused
- Length: 3–4 pages

**Template sections:**
1. Business Snapshot (1–2 sentences, status indicator, wins/risks/playbook)
2. Key Metrics (tables: usage, sentiment, support, engagement)
3. Root Cause Analysis (3–5 sentences explaining health score drivers)
4. Recommended Conversation Topics (3–5 priority topics, tier-specific)
5. Expansion Opportunities (or note "Stabilization priority")
6. Data Quality & Limitations (what's missing, confidence score)
7. Recommended Actions (2–5 specific next steps)

### Step 4: Output & Logging

**Deliverables:**
- Markdown QBR report per account: `QBR_Report_[Account_ID]_[Quarter].md`
- Optional CSV export: Account ID, Name, Health Score, Risk Status, Days to Renewal, ARR, Playbook, CSM, Generated timestamp
- Optional Slack notification summary (account count, risk tier breakdown, high-priority accounts)

**Logging:**
- Record execution metrics: total accounts processed, success rate, avg time/account, errors
- Persist reports for audit trail (2-year retention)

---

## Output Contract

### Standard QBR Report (Markdown)

```markdown
# Quarterly Business Review — [Account Name]

**Q1 2026 Summary**

Generated: [ISO 8601 timestamp]
Health Score: [Score] ([Status: Green/Yellow/Red])
Days to Renewal: [N]
Contract Value: $[ARR]
Confidence: [0–100%]

---

## 1. Business Snapshot

[1–3 sentence executive summary]

### Status Indicator
- **Wins:** [2–3 positive signals]
- **Risks:** [2–3 risk drivers]
- **Recommended Playbook:** [value-realization | product-quality | expansion-stall | save-play]

---

## 2. Key Metrics

### Product Adoption & Usage
| Metric | Value | Target | Trend |
| --- | --- | --- | --- |
| DAU/MAU | [%] | 50%+ | ↑/→/↓ |
| Core Feature Adoption | [%] | 75%+ | ↑/→/↓ |
| Last Active | [N days ago] | <7d | ↑/→/↓ |

### Customer Sentiment
| Metric | Value | Notes |
| --- | --- | --- |
| NPS | [Score] | [Detractor/Neutral/Promoter] |
| CSAT (Support) | [Score]/5 | — |
| Key Feedback | "[Quote]" | — |

### Support Health
| Metric | Value | Notes |
| --- | --- | --- |
| Tickets (30d) | [N] | Trend: ↑/→/↓ |
| MTTR | [Hours] | Target <24h |
| Escalations | [N] | — |

### Engagement
| Metric | Value | Notes |
| --- | --- | --- |
| Last Email | [N days ago] | — |
| Last Call/Meeting | [N days ago] | — |
| Expansion Signals | [Yes/No] | — |

---

## 3. Root Cause Analysis

### Why is Health [Green/Yellow/Red]?

[Detailed explanation of health score drivers and business impact]

---

## 4. Recommended Conversation Topics

[3–5 priority conversation starters, tier-specific, with suggested talking points]

---

## 5. Expansion Opportunities

[Summary of expansion potential or note "None at this time"]

---

## 6. Data Quality & Limitations

- Health scores last updated: [date]
- Data completeness: [%]
- Confidence level: [0–100%]
- Missing data impact: [explanation]

---

## 7. Recommended Actions

[2–5 specific, actionable next steps]

---

**Agent:** CSO-02 QBR Prep
**Data Sources:** Salesforce/HubSpot (CRM), CSO-CUST-01 (health scores), Product Analytics, Support System
**Next Refresh:** [Automatic weekly]
```

---

## Error Handling

### Preflight Checks Fail

**Error:** CSO-CUST-01 health scores not populated on ≥80% of accounts

**Response:**
```
Preflight Check Failed: CSO-02 cannot run.

✗ CSO-CUST-01 health scores not populated on ≥80% of target accounts
✓ CRM connectivity: Active (Salesforce)
✓ Account count: 45 accounts
✓ Data quality: 88% accounts meet minimum thresholds

Resolution: Deploy CSO-CUST-01 for 30 days, then retry CSO-02.

Would you like help deploying CSO-CUST-01, or proceed in degraded mode?
```

### Per-Account Data Gaps

**Error:** Missing renewal date on 12% of accounts

**Response:** Include warning in QBR output; use fallback logic (contract start + standard term); flag for CSM manual review.

### Health Score Freshness

**Error:** Health scores last updated 14 days ago (stale)

**Response:** Include warning in confidence section; reduce confidence score by 10–15%; recommend re-running CSO-CUST-01.

### LLM Narrative Generation Fails

**Error:** LLM timeout or empty response

**Response:** Generate minimal QBR using template + data injection only; flag for manual review; log error.

### CRM API Timeout

**Error:** Salesforce API unresponsive

**Response:** Implement exponential backoff retry (2s, 4s, 8s); fall back to cached CSO-CUST-01 data if recent.

---

## Configuration

### Tunable Parameters

Before running, you can customize:

**Data Quality Thresholds:**
- Health score population threshold (default: 80%)
- Account ID completeness (default: 99%)
- Renewal date completeness (default: 90%)
- MRR completeness (default: 85%)

**Prioritization Weights:**
- Risk status weights (Red 3.0, Yellow 2.0, Green 1.0; tunable)
- Revenue weight (default 1.0)

**Health Score Freshness:**
- Max acceptable age (default: 7 days)

**Narrative Generation:**
- Template style (default: professional)
- Include root cause analysis (default: yes)
- Confidence threshold (default: 50%)

**Output:**
- Include CSV export (default: yes)
- Send Slack notification (default: optional)

---

## Worked Example

**Scenario:** Generate QBRs for 50 accounts; focus on Yellow/Red accounts renewing within 90 days.

**Preflight:**
```
✓ Salesforce MCP connected
✓ CSO-CUST-01 health scores: 45/50 accounts (90%)
✓ Data freshness: 4 days old
✓ Risk distribution: Green 28, Yellow 14, Red 3

Scope: Yellow/Red accounts renewing within 90 days = 16 accounts
Estimated runtime: 6–8 minutes
```

**Account Prioritization:**
```
1. (RED, 21 days to renewal, $45k ARR) — CRITICAL
2. (YELLOW, 35 days to renewal, $75k ARR) — HIGH
3. (YELLOW, 52 days to renewal, $12k ARR) — HIGH
...
16. (YELLOW, 87 days to renewal, $8k ARR) — HIGH
```

**Sample QBR Output (Account 2):**
```
# Quarterly Business Review — Acme Finance Corp

**Q1 2026 Summary**

Generated: 2026-04-13T10:32:00Z
Health Score: 68 (Yellow)
Days to Renewal: 35
Contract Value: $75,000 ARR
Confidence: 82%

---

## 1. Business Snapshot

Acme Finance is at-risk due to declining product adoption and weakening customer sentiment. 
Usage metrics show a 18% drop in DAU/MAU over the past month, and NPS has fallen to detractor 
territory (25). However, support experience remains strong, and auto-renewal is enabled.

### Status Indicator
- **Wins:** Strong support CSAT (4.2/5); low escalations; auto-renew enabled
- **Risks:** DAU down 18% MoM; Feature adoption at 60% (vs. 75% target); NPS = 25 (detractor)
- **Recommended Playbook:** value-realization

---

[Additional sections: Metrics, Root Cause, Conversation Topics, Expansion, Actions...]
```

---

## What to Run Next

After QBR prep is complete:

1. **CSO-03: Account Expansion Agent** (future) — Use QBR materials to identify expansion vectors for Green/Yellow accounts.

2. **CSO-04: Renewal Management Agent** (future) — Use QBR prep output as input to renewal workflow automation.

3. **Schedule recurring QBR refresh** — Set up weekly or monthly automated runs to keep materials current.

4. **Gather CSM feedback** — Collect feedback on QBR usefulness, narrative quality, and conversation starter relevance to iterate on templates.

---

## References

- **CSO-02 Architecture Spec:** `/sessions/beautiful-clever-mendel/mnt/EG's Agent List/_build/specs/CSO-02_qbr_prep_spec.md`
- **CSO-02 Research Brief:** `/sessions/beautiful-clever-mendel/mnt/EG's Agent List/_build/research/CSO-02_qbr_prep_research.md`
- **CSO-CUST-01 (Upstream Dependency):** `/sessions/beautiful-clever-mendel/mnt/EG's Agent List/_build/specs/CSO-CUST-01_customer_retention_risk_spec.md`
- **DQH-01 Reference Skill:** `/sessions/beautiful-clever-mendel/mnt/.claude/skills/dqh-01-deduplication-engine/SKILL.md`
- **Consistency Rules:** `/sessions/beautiful-clever-mendel/mnt/EG's Agent List/_build/foundation/consistency_rules.md`
- **ChurnZero QBR Workflows:** [From Burnout to Balance: Reinventing QBR Workflows for CS Leaders](https://churnzero.com/blog/from-burnout-to-balance-reinventing-qbr-workflows-for-cs-leaders/)
- **Gainsight vs Alternatives:** [Gainsight vs Totango vs Churnzero: Features and Pricing Compared 2026](https://www.velaris.io/comparison/gainsight-vs-totango-vs-churnzero)

---

**Status:** Ready for Implementation
**Last Updated:** April 13, 2026
**Maintainer:** RevOps Agent Factory
