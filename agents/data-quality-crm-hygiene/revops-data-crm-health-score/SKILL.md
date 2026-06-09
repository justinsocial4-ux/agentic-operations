---
name: revops-data-crm-health-score
description: "Generates a unified health score for your CRM across six data quality dimensions (completeness, accuracy, duplicates, freshness, consistency, connectivity). Benchmarks against industry standards, tracks improvement over time, and delivers prioritized remediation recommendations. Trigger on: score my CRM data, check data health, CRM health score, data quality score, measure data quality, assess CRM health, what's my data quality, evaluate CRM data quality."
metadata:
  category: "Data Quality & Hygiene"
  phase: "Phase 2"
  data_readiness: "30_days"
  version: "1.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-04-12"
  dependencies:
    agents:
      - "revops-data-deduplication (DQH-01)"
      - "revops-data-field-normalization (DQH-02)"
    mcps:
      - "Salesforce MCP (Salesforce orgs)"
      - "HubSpot MCP (HubSpot orgs)"
      - "Snowflake MCP (optional; for engagement history)"
    minimum_data:
      - "Contact/Company object with Email, Phone, FirstName, LastName fields"
      - "Account/Company object with Name, Industry fields"
      - "Opportunity/Deal object with Amount, CloseDate, StageName, AccountId"
      - "Activity records (Task, Event, EmailMessage) for freshness scoring (optional)"
---

# DQH-04 CRM Health Score Agent

## Why This Agent Exists

**Population:** RevOps Manager at B2B SaaS, 50–500 employees, North America

**Pain Points Qualified: 3 of 3 PASS**

### Pain Point 1: Unknown Data Quality Drives Pipeline Unreliability (4/4 criteria)
- **Quantified Cost:** 37% revenue loss directly attributed to data quality (Prospeo)
- **Labor Workaround:** 16–20 hours/week manual validation (estimated from 1–2 hr baseline audit cycle)
- **Problem Prominence:** Completeness, accuracy, duplicates, freshness, consistency, connectivity (Landbase)
- **Compounding Cost:** Decay accelerates; 22.5–70.3% annual decay rate (unaddressed → 70% loss in 24 months)
- **Sources:** Landbase, Cleanlist, Prospeo
- **Last Verified:** 2026-04-12 (URLs live-checked)

### Pain Point 2: Missing Thresholds Create Ambiguous Remediation Priorities (4/4 criteria)
- **Quantified Cost:** 44% lose 10%+ annual revenue; $15M average organizational loss (Gartner/Validity)
- **Tool Spend:** $5k–$50k/year on point-solution tools (Cleanlist, Insycle, DataGroomr)
- **Problem Prominence:** 10-metric scorecard with tiers (Excellent, Good, Average, Poor, Critical) (Cleanlist)
- **Compounding Cost:** Cascading failures without thresholds; >5% bounce damages ISP reputation (Cleanlist)
- **Sources:** Cleanlist, Databar, Gartner, Validity
- **Last Verified:** 2026-04-12 (URLs live-checked)

### Pain Point 3: Baseline Audits Take Excessive Manual Labor, Preventing Continuous Monitoring (4/4 criteria)
- **Quantified Cost:** 1–2 hours per baseline (50K records) = 30–40 hours/year; ~$1,800–$2,400 labor cost
- **Tool Spend:** Teams hire consultants ($3k–$10k per audit) or buy software (Insycle, Cleanlist, DataGroomr)
- **Problem Prominence:** Landbase advocates continuous intake validation (not manual audits) as industry best practice
- **Compounding Cost:** Quarterly audits miss early decay detection; decay compounds 2–5%/month; missed 8-week window
- **Sources:** Prospeo, Landbase, Cleanlist
- **Last Verified:** 2026-04-12 (URLs live-checked)

**Business Case Strength: STRONG**
- Revenue Impact: 37–44% of teams report direct revenue loss due to poor CRM data
- Organizational Cost: $15M average annual loss (Gartner enterprise benchmark)
- Adoption Signal: $300M–$750M TAM in North America; 3,000 companies in SAM (willing buyers of AI RevOps tools)
- Tool Market: $2B+ data quality software market; high adoption of fragmented point solutions

---

## What This Agent Does

The CRM Health Score Agent is your data quality scorekeeper. It generates a single, unified health score (0–100) for your entire CRM by measuring six key dimensions: completeness (are core fields populated?), accuracy (are values correct?), duplicates (are there unwanted copies?), freshness (is data recent?), consistency (are formats and linkages valid?), and connectivity (are records properly linked?). Instead of running manual quarterly audits, you get a data health dashboard you can run weekly or on-demand. The agent benchmarks your scores against industry standards for RevOps teams, shows you exactly where data quality gaps exist, and prioritizes remediation actions with estimated effort and ROI impact.

---

## Getting Started (Preflight Check)

When you trigger this agent, I'll verify your CRM connection, confirm required data exists, assess data quality, and ask whether you want a full assessment or a pilot sample.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: export contacts to CSV for offline analysis, or help you troubleshoot the MCP connection.
- **If successful:** Proceed to Step 2.

**Step 2: Required Data Validation**
I'll verify that your Contact, Account, and Opportunity objects have these minimum fields:
- Contact: Email, Phone, FirstName, LastName, CreatedDate, LastModifiedDate
- Account/Company: Name, Industry, BillingCity
- Opportunity/Deal: Amount, CloseDate, StageName, AccountId
- Activity (optional but recommended): ActivityDate, Type, RelatedToId

**Connectivity Fallback Note:** If custom fields `email_verified` or `phone_verified` don't exist, I'll use field-population and format-validation as proxies for connectivity scoring.

**Go/No-Go Decision:**
- ✓ All required objects and fields present → Proceed
- ⚠️ 1–2 fields missing → Partial results possible; I'll flag the limitation and proceed
- ✗ Core objects missing (e.g., no Contact or Opportunity) → No-go; request basic CRM setup first

**Step 3: Data Readiness Assessment**
I'll calculate:
- Record counts (contacts, accounts, opportunities)
- % of core fields populated (email, phone, title, company, industry)
- Data freshness (when records were last modified)
- Estimated duplicate rate (sample ~1,000 records; extrapolate)
- Activity/engagement recency

**Step 4: Confirm Prerequisite Completion**
I'll check: Have you run DQH-01 (Deduplication) and DQH-02 (Field Normalization) recently? If not, health score will be degraded; I'll explain the impact and offer to run those first.

**Preflight Report**
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Contact + Account + Opportunity objects present
✓ Email data quality: 91% valid (45,500 / 50,000)
✓ Phone data quality: 74% valid (37,000 / 50,000)
✓ Data freshness: 88% updated in past 90 days
✓ Estimated duplicate rate: 2.1% based on sample
✓ DQH-01 deduplication completed: 2026-04-10
✓ DQH-02 field normalization completed: 2026-04-11
✓ Ready to proceed

Scope: All 50,000 contacts + 12,000 accounts + 4,300 opportunities | Full assessment

Next step: Running health score assessment...
```

---

## Step-by-Step Workflow

### Step 1: Fetch Records from CRM (in batches)

**What I'll do:**
- Query Contact records: Id, Email, Phone, FirstName, LastName, Company, Title, CreatedDate, LastModifiedDate
- Query Account records: Id, Name, Industry, BillingCity, BillingCountry
- Query Opportunity records: Id, Amount, CloseDate, StageName, AccountId
- Query Activity records (optional): ActivityDate, Type, RelatedToId (last 90 days)
- Fetch field metadata to identify custom fields

**Batch Strategy:** Fetch in 2,000-record increments to respect API rate limits.

**What you'll see:** Progress indicator ("Fetched 2,000 / 50,000 records...").

---

### Step 2: Calculate Six Dimension Scores

For each dimension, I'll measure specific metrics and convert to a 0–100 score. Weights are: Completeness 20%, Accuracy 15%, Duplicates 20%, Freshness 20%, Consistency 15%, Connectivity 10%.

**Dimension 1: Completeness (20% weight)**
- Measures: % of core Contact fields populated (Email, Phone, FirstName, LastName, Title, Company, Industry)
- Calculation: For each contact, count populated required fields / total required fields; aggregate to average %
- Thresholds: 90%+ = 90 points, 80–89% = 80, 65–79% = 65, 50–64% = 50, <50% = 25
- Sources: Cleanlist industry benchmarks

**Dimension 2: Accuracy (15% weight)**
- Measures: Spot-sample validation (100–200 contacts) of email validity, phone format, company name consistency
- Calculation: [ASSUMPTION] 
  - Email accuracy: validate format (regex check for @ and valid domain)
  - Phone accuracy: validate format (digits only after stripping, correct length for country)
  - Company name accuracy: fuzzy match against Account.Name (Jaro-Winkler ≥ 0.85)
  - Aggregate to % accurate across sample
- Thresholds: 95%+ = 95, 90–94% = 90, 80–89% = 80, 70–79% = 70, <70% = 50
- Sources: Landbase B2B baseline research

**Dimension 3: Duplicates (20% weight)**
- Measures: % duplicate Contact records (matched by email or phone, Jaro-Winkler ≥ 0.88)
- Calculation: DQH-01 dedup results OR fuzzy-match analysis; estimate % dupes of total
- Thresholds: <3% dupes = 95, 3–5% = 90, 5–10% = 75, 10–20% = 50, >20% = 25
- Sources: Cleanlist, Landbase deduplication benchmarks

**Dimension 4: Freshness (20% weight)**
- Measures: % of Contacts updated within 90 days
- Calculation: (Contacts with LastModifiedDate within 90 days) / total contacts
- Thresholds: 80%+ = 80, 65–79% = 65, 50–64% = 50, 35–49% = 35, <35% = 20
- Sources: Cleanlist freshness benchmark, Prospeo data decay research

**Dimension 5: Consistency (15% weight)**
- Measures: % of Contacts linked to valid Account; data type/format consistency
- Calculation: Contacts with valid AccountId / total contacts; flag invalid data types (e.g., text in phone field)
- Thresholds: >95% linked = 95, 88–95% = 85, 75–87% = 70, 60–74% = 50, <60% = 30
- Sources: Cleanlist contact-to-account match metric

**Dimension 6: Connectivity (10% weight)**
- Measures: % of Contacts with verified email or phone; % of Opportunities linked to Contact
- Calculation: 
  - If `email_verified` field exists: use it directly
  - If `email_verified` field does NOT exist → fallback to "email field populated AND passes format validation"
  - If `phone_verified` field exists: use it directly
  - If `phone_verified` field does NOT exist → fallback to "phone field populated AND passes format validation"
  - Also measure: (Opps with Contact record) / total opps
  - Aggregate to overall % connected
- Thresholds: >95% = 90, 88–95% = 80, 75–87% = 70, 60–74% = 50, <60% = 30
- Sources: Cleanlist connectivity benchmark

---

### Step 3: Calculate Per-Object Health Scores

I'll generate completeness, freshness, and connectivity distributions:
- For each Contact: individual completeness %, freshness days, linked account yes/no
- For each Account: completeness %, # of linked contacts, # of linked opportunities
- For each Opportunity: completeness %, days in current stage, amount populated
- Aggregate: mean, median, 10th percentile, 90th percentile (shows data spread)

**Example output:**
```
Contact Completeness Distribution:
  Mean: 78% | Median: 85% | 10th percentile: 42% | 90th percentile: 95%
  → Skewed distribution: half your contacts are well-populated; 10% are critically incomplete

Opportunity-to-Contact Linkage:
  3,847 / 4,300 opportunities (89%) linked to at least one contact
  → 453 opportunities (11%) missing contact associations
```

---

### Step 4: Composite Health Score Calculation

Apply dimension weights and calculate overall score:

```
Health Score = (Completeness × 0.20) + (Accuracy × 0.15) + (Duplicates × 0.20) 
             + (Freshness × 0.20) + (Consistency × 0.15) + (Connectivity × 0.10)
```

**Rating Scale:**
- 85–100 = **EXCELLENT** — Data is reliable; proceed with confidence
- 75–84 = **GOOD** — Mostly usable; address 1–2 weak dimensions
- 65–74 = **AVERAGE** — Has gaps; 4–8 week improvement plan needed
- 50–64 = **POOR** — Significant issues; impacts operations; prioritize remediation
- <50 = **CRITICAL** — Data quality is a business risk; stop advanced automation; fix hygiene first

---

### Step 5: Trend Calculation & Historical Tracking

**Trend data storage:** I'll save each health score run as a JSON snapshot in a `health_score_history/` directory with timestamp. Each snapshot includes the composite score, per-dimension scores, and record counts.

**Minimum for trending:** At least 2 snapshots (runs) needed to calculate trends. I'll tell you when trending data becomes available.

**Per-dimension trends:** I'll track which dimensions are improving and which are declining, and highlight the biggest movers.

**Example (if historical baseline exists):**
```
Current Health Score: 76 (GOOD)
Previous Assessment (2 weeks ago): 72 (AVERAGE)
Delta: +4 points ↑ improving
Trend rate: +2 points/week

Dimension-by-dimension trends:
  Completeness: 75 → 81 (+6 points) ↑
  Freshness: 50 → 54 (+4 points) ↑
  Duplicates: 85 → 84 (-1 point) ↓
  Accuracy: 87 → 89 (+2 points) ↑
  
Biggest movers: Completeness (+6), Freshness (+4)
```

---

### Step 6: Identify Remediation Priorities

I'll analyze the three lowest-scoring dimensions and suggest actions:

**For each weak dimension, recommend:**
1. **Data quality action** — Standardize, enrich, or clean specific fields
2. **Process action** — Change a form, validation rule, or workflow to prevent future decay
3. **Tool/integration action** — Enable a data sync, enrichment service, or automation

**Estimate effort:** Low (1–2 weeks), Medium (2–4 weeks), High (4+ weeks)

**Estimate ROI impact:** Which action will move your health score the most per hour of effort?

**Example:**
```
Bottom 3 Dimensions:
1. Freshness (50/100) — 35% of contacts >90 days old
   Actions:
   a. Run enrichment on stale contacts (2 weeks, +15 points to Freshness)
   b. Add "last activity date" to your Account view so AEs know when to refresh
   c. Enable email bounce sync from Gong (integrates updated status)
   Recommended: (a) + (c), Low effort, High ROI

2. Completeness (68/100) — 22% missing phone numbers
   Actions:
   a. Enrich phone data via ZoomInfo or RocketReach (1 week, +12 points)
   b. Make phone required on Contact creation form (ongoing)
   c. Run data standardization on Title field (3 days, +3 points)
   Recommended: (b) + (c), Low effort, Medium ROI

3. Consistency (72/100) — 8% of contacts not linked to account
   Actions:
   a. Run account match algorithm on orphaned contacts (1 day, +5 points)
   b. Create Account-matching rule to auto-link future records
   Recommended: (a) + (b), Low effort, High ROI
```

---

### Step 7: Generate Output Report

**Markdown Report with:**

**Summary**
- Overall health score and tier (EXCELLENT/GOOD/AVERAGE/POOR/CRITICAL)
- Key finding in 1–2 sentences (e.g., "Your CRM is GOOD overall but freshness is dragging down the score. 35% of contacts haven't been updated in 90+ days.")
- Trend (if available): improving ↑ / declining ↓ / stable →
- Confidence level (0–100) based on data quality and sample size

**Details**
- Dimension breakdown table (score, tier, benchmark comparison for each of 6 dimensions)
- Per-object distribution curves (contact completeness spread, opportunity linkage %, etc.)
- Top 10 flagged records with lowest scores and reasons
- Trend history (if available): health score over time
- Benchmark comparison: "Your completeness (78%) is below industry benchmark (85%); your duplication rate (2%) is excellent vs. benchmark (8%)"

**Data Quality & Limitations**
- Assumptions (email = primary contact identifier, scores based on DQH-01/DQH-02 completion status, etc.)
- Data gaps (% contacts without email, % without phone) and impact on dimensions
- Known limitations (can't validate accuracy without external data [ASSUMPTION], international character handling, etc.)
- Confidence degradation factors (small sample size <100 records, sparse activity history, etc.)

**Recommended Actions**
- 2–5 specific, prioritized remediation steps (not generic advice)
- For each action: effort estimate, expected impact, owner, timeline
- Quick wins (1-day actions that move score 3–5 points)
- Long-term bets (4-week initiatives that move score 15+ points)

**Sources & Citations**
- CRM data pulled [timestamp]
- Benchmark thresholds per Cleanlist (2026), Landbase (2026), Prospeo (2026)
- Industry research citations

---

## Configuration Options

Before I run the full assessment, you can customize these parameters:

**Dimension Weights:**
- "Do you want equal weighting (20% each) or custom? (Default: Completeness 20%, Accuracy 15%, Duplicates 20%, Freshness 20%, Consistency 15%, Connectivity 10%)"
- Example: "We care more about duplicates than completeness" → Duplicates 30%, Completeness 10%

**Scope:**
- "Full assessment or pilot? (Default: all records)"
- "Analyze Contacts only, or include Accounts and Opportunities? (Default: all)"
- "Date range? (Default: all time)"

**Benchmark Comparison:**
- "Compare to industry benchmark (default), or use custom threshold? (Default: industry)"
- Example: "Our industry standard for completeness is 90%, not 85%"

**Historical Tracking:**
- "Store this assessment for trend tracking? (Default: Yes)"
- "How often should I run health assessments? (Default: quarterly; recommend weekly)"

**Output Format:**
- "Markdown report only, or also export JSON + CSV? (Default: markdown + JSON)"

---

## Error Handling

**If MCP connection fails:**
- Offer to work with CSV export instead (slower but works offline)
- Provide troubleshooting steps for the MCP (API key, permissions, org ID)

**If required data is missing:**
- Continue with available data; flag limitations in report
- Example: No Activity data → Freshness score skipped; uses account-level defaults with confidence downgrade

**If prerequisite agents haven't run:**
- Proceed with health assessment (duplicates and inconsistencies will be flagged as issues, not hidden)
- Recommend running DQH-01 + DQH-02 first, then re-assess to see improvement
- Example: "You have 2.1% duplicates (poor score). Run DQH-01 first to clean these up, then re-assess."

**If data quality is too low to assess:**
- <20 Contact records total → Refuse to run; too small to measure meaningful health
- <30% average field completion → Proceed with CRITICAL tier warning; "Data quality is too poor to trust for operations"
- No Activity data available → Freshness dimension uses defaults; explain impact

**If API rate limits are hit:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (1,000 records instead of 2,000)
- Split into multiple runs (analyze different time periods separately)

---

## What to Run Next

After health assessment is complete:

1. **DQH-01: Deduplication Engine** (if not recently run) — Remove duplicate contacts that inflate pipeline and damage outreach
2. **DQH-02: Field Normalization Agent** (if not recently run) — Standardize company names, job titles, industries per ruleset
3. **Based on weakest dimension:**
   - **Low Completeness?** Run enrichment agent to fill missing phone, title, company
   - **Low Freshness?** Enable data refresh integrations (email, phone verification sync)
   - **Low Accuracy?** Validate and standardize data types; run field normalization
   - **High Duplicates?** Run deduplication again; check integration syncing for duplicate sources

4. **Schedule recurring health assessments** — Set up weekly or monthly health score runs to track improvement and catch decay early

5. **Downstream agents (Phase 3+):**
   - **PM-01: Pipeline Health Monitoring** — Uses CRM health score as preflight check before advanced pipeline analytics
   - **DQH-05: Enrichment Orchestration** — Routes enrichment efforts based on health score gaps (low completeness → prioritize phone fill, etc.)

---

## Example: End-to-End Health Score Session

**You:** "Check my CRM data health and tell me where to focus cleanup efforts."

**Me (Preflight):**
```
✓ Salesforce MCP connected
✓ Contact + Account + Opportunity objects ready
✓ Email quality: 91% valid
✓ Phone quality: 74% valid
✓ DQH-01 deduplication last run: 2026-04-10 ✓
✓ DQH-02 normalization last run: 2026-04-11 ✓
✓ Analyzing 50,000 contacts + 12,000 accounts + 4,300 opportunities
```

**Me (Assessment):**
```
Calculating six dimensions...
✓ Completeness: 78% (Good)
✓ Accuracy: 87% (Good) — Sample validation against company standards
✓ Duplicates: 2.1% (Excellent) — DQH-01 dedup working well
✓ Freshness: 50% (Average) — 35% of contacts >90 days old
✓ Consistency: 89% (Excellent) — Strong account linkage
✓ Connectivity: 92% (Excellent) — 89% opps linked to contacts

Composite Health Score: 76 (GOOD)
Trend: +4 points ↑ improving (vs. 2 weeks ago: 72)
Confidence: 92% (n=50K records, clean data)
```

**Report (Summary):**
```
Your CRM is GOOD overall but freshness is the bottleneck. 35% of contacts 
haven't been touched in 90+ days, which erodes data quality and hurts 
outreach effectiveness. Fix this to push your score to 82+.

Benchmark comparison:
- Completeness 78% vs. industry 85% (you're 7 points below) ⚠️
- Duplicates 2.1% vs. industry 8% (you're crushing it) ✓
- Freshness 50% vs. industry 68% (you're 18 points below) ⚠️
- All other dimensions at or above industry average ✓
```

**Recommended Actions (in priority order):**
```
1. QUICK WIN: Auto-link 11% of orphaned opportunities to accounts
   Effort: 1 day | Impact: +5 health points | Owner: Sales Ops

2. HIGH ROI: Enrich stale contact records (35% of base) with current phone + title
   Effort: 2 weeks | Impact: +15 health points | Owner: RevOps + enrichment tool
   
3. ONGOING: Enable email verification sync from outreach tool (Outreach, Salesloft)
   Effort: 1 week setup | Impact: +8 health points (ongoing) | Owner: Sales Ops

4. FOUNDATIONAL: Add phone field to Contact creation form + make it required
   Effort: 1 day | Impact: +4 health points (ongoing) | Owner: Sales Ops

Expected combined impact: 76 → 85+ (EXCELLENT) within 4 weeks
```

**You:** "Perfect. I'll do the quick win today and the enrichment next week. Should I wait to run the other health score agents?"

**Me:** "DQH-01 and DQH-02 are already done (you ran them 2–3 days ago), so your health score is already at your best-case dedup+norm state. Freshness is your real lever. Once enrichment completes, run this assessment again—you should see a 15-point jump."

---

## References & Further Reading

**Detailed Files** (in `references/` folder):
- `health_score_benchmarks.md` — Complete benchmark thresholds by dimension (Cleanlist, Landbase sources)
- `remediation_playbook.md` — Step-by-step fixes for each dimension (enrichment, process changes, integrations)
- `dimension_calculations.md` — Technical details on how each score is calculated
- `trend_tracking_examples.md` — Real-world before/after assessments
- `crm_tech_stack_notes.md` — Salesforce vs. HubSpot specific gotchas

