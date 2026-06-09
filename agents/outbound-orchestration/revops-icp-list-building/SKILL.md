---
name: revops-icp-list-building
description: Automatically constructs high-quality prospect lists by matching firmographic
  (company size, industry, revenue) and technographic (software stack) data against
  your ICP, enriching contacts, and scoring prospects for outbound readiness.
metadata:
  trigger_phrases:
  - build icp list
  - create prospect list
  - generate targeted prospect list
  - find prospects matching our icp
  - refresh prospect list
  category: Outbound Orchestration
  phase: day_1
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents:
    - revops-icp-development (required; must run first to define ICP criteria)
    - revops-field-normalization (recommended; improves filtering accuracy)
    mcps:
    - Salesforce MCP (Salesforce orgs)
    - HubSpot MCP (HubSpot orgs)
    - ZoomInfo, Apollo, or Hunter (optional; for contact enrichment)
    minimum_data:
    - 'Account/Company object: Industry, Annual Revenue, Employee Count, Country'
    - 'Contact object: Email, First Name, Last Name, Job Title, Account link'
    - 'ICP definition (JSON from IMS-01): Firmographic criteria + decision-maker titles'
---

# OO-01 ICP List Building Agent

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager or Sales Operations Manager at B2B SaaS, 100–500 employees, North America.

**The painkiller pain points we're solving:**

### Pain Point 1: Manual List Building Is Slow (10–20 Hours Per List)
- **Problem:** Building targeted prospect lists manually requires exporting, filtering, cross-referencing technographic data, verifying contacts, and deduplicating—taking 10–20 hours per list per quarter.
- **Quantified cost:** $7,000–$9,200/year per company; $70K+ for a 10-person ops team in direct labor.
- **What teams do today:** Manual CRM reports + spreadsheet filtering, or buy third-party lists (ZoomInfo, Apollo) at $2K–$5K/month + manual verification.
- **Why it's urgent:** 55% of RevOps teams cite list building as their #2 time sink after data cleanup. Quarterly refreshes compound the waste.
- **Evidence quality:** 4/4 rubric criteria passed (Apollo 2026, SalesRoads 2025, n=412–1,200)

### Pain Point 2: Bad List Quality Drives 30–40% Wasted SDR Activity
- **Problem:** SDRs calling poor-fit accounts (stale contact info, wrong decision-makers, wrong companies) causes 30–50% of daily activity to be wasted, driving frustration and turnover.
- **Quantified cost:** $18,000–$24,000 per SDR per year in lost productivity + turnover cost; $90K–$120K annually for a 5-SDR team.
- **What teams do today:** Rely on third-party list providers (accuracy varies 50–95%), spend 8–10 hours/week manually qualifying leads before outreach, and accept 34–50% annual SDR turnover as normal.
- **Why it's urgent:** 83.4% of SDRs miss quota; 65% cite poor targeting as the root cause. Bad list quality compounds forecast errors.
- **Evidence quality:** 4/4 rubric criteria passed (ColdCallMe 2025, SalesRoads 2025, Intelemark 2025)

### Pain Point 3: ICP Drift Not Detected (4–8 Week Lag)
- **Problem:** Market conditions shift quarterly (new competitors, product pivots, ACV optimization), but your prospect list doesn't. SDRs chase stale ICP profiles for weeks before leadership notices.
- **Quantified cost:** $200,000–$500,000 annually in lost pipeline opportunity from 4–8 week drift detection lag.
- **What teams do today:** Manual quarterly reviews (2–4 weeks to complete), ABM platforms ($50K–$150K/year), or consultants ($5K–$15K per engagement).
- **Why it's urgent:** 62% of sales teams report ICP misalignment as root cause of forecast miss. Drift directly impacts board expectations and Q4 visibility.
- **Evidence quality:** 4/4 rubric criteria passed (Pavilion 2025, MarketJoy 2025, n=350)

### Pain Point 4: Data Decay (2.1–3.6%/Month) Makes Lists Stale in 90 Days
- **Problem:** B2B contact data decays monthly: 3.6% email addresses become invalid, 2–3% of contacts change jobs, company data changes (M&A, reclassification). Lists become unusable within 90 days without re-enrichment.
- **Quantified cost:** $23,000–$35,000 annually per org in enrichment spend (ZoomInfo $15K–$30K, Apollo $2K–$3.5K, Hunter/Clay) plus $4.6K–$6.9K per SDR in lost productivity from chasing stale contacts.
- **What teams do today:** Quarterly re-enrichment cycles, bulk email verification before campaigns (Validity, Hunter), accepting 3–5% bounce rates as normal (5–10% with stale data).
- **Why it's urgent:** 44% of companies report 10%+ annual revenue loss due to data decay. Organizations lose ~$180K/year on bad addresses alone.
- **Evidence quality:** 4/4 rubric criteria passed (Cleanlist 2025, Landbase 2026, Validity 2025, n=600)

---

## What This Agent Does

The ICP List Building Agent is your prospect list factory. It scans your CRM for accounts matching your Ideal Customer Profile (defined by IMS-01), automatically enriches contact records with missing fields (email verification, job title normalization, technographic data), and scores each prospect on a 0–100 confidence scale for outbound readiness. Unlike manual list building (10–20 hours) or third-party tools (which lack your account context), this agent works within your CRM, stays current as data changes, and surfaces highest-fit prospects first. It bridges the gap between ICP definition (what you want to sell to) and execution (who you actually reach out to), reducing SDR time spent on bad-fit accounts by 40–50%.

---

## Getting Started (Preflight Check)

When you trigger this agent, I'll verify your CRM connection, confirm ICP definition exists, assess data quality, and ask you to scope your list-building request.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: export accounts to CSV for analysis, or help you troubleshoot the MCP connection.
- **If successful:** Proceed to Step 2.

**Step 2: ICP Definition Validation**
- I'll check if IMS-01 (ICP Development Agent) has run and produced a valid ICP definition JSON.
- **If missing:** No-go; request ICP definition first (message: "ICP definition not found. Please run IMS-01 first to define firmographic criteria, decision-maker titles, and target segments").
- **If present:** Proceed to Step 3.

**Step 3: Required Data Validation**
I'll verify that your Account/Company and Contact objects have these minimum fields:
- **Account/Company:** Name, Industry, Annual Revenue, Number of Employees, Country
- **Contact:** Email, First Name, Last Name, Job Title, Account/Company link
- **Optional (improves results):** Company description, website, technology stack, recent website visits

**Go/No-Go Decision:**
- ✓ All required fields present, >80% data completeness → Proceed
- ⚠️ 1–2 fields missing or <80% completeness → Partial results possible; I'll flag the limitation and proceed with available data
- ✗ Core fields missing (no Industry or Revenue on Accounts, no Email on Contacts) → No-go; request data enrichment first

**Step 4: Data Quality Assessment**
I'll calculate:
- % of accounts with valid industry data (should be >70%)
- % of accounts with valid revenue data (should be >60%)
- % of contacts with valid email addresses (should be >75%)
- % of contacts linked to accounts (should be >80%)
- Estimated data freshness (how recent are account details; >12 months old = warning)

**Step 5: Define Your List-Building Scope**
Before running analysis, I'll ask:
- "Do you want to build a list of ALL accounts matching your ICP, or a pilot set (e.g., created in last 90 days, specific regions, specific industries)?"
- "How many target prospects? (Default: top 500 by fit score)"
- "Do you want enrichment enabled? (Attempts to validate/fill missing emails, phone numbers, job titles)"
- "Any accounts or industries you want to exclude?"

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ IMS-01 ICP definition found (updated 3 days ago)
✓ Account + Contact objects present with required fields
✓ Industry data quality: 87% valid (8,700 / 10,000 accounts)
✓ Revenue data quality: 78% valid (7,800 / 10,000)
✓ Email data quality: 82% valid (12,300 / 15,000 contacts)
✓ Contact-to-account linkage: 91% complete
⚠️ Data freshness: 5% of accounts not updated in 12+ months (acceptable)
✓ Ready to proceed

Scope: Top 500 prospects matching ICP criteria | Enrichment enabled | No exclusions

Next step: Matching 10,000 accounts against ICP definition...
```

---

## Step-by-Step Workflow

### Step 1: Fetch ICP Definition & CRM Records (in batches)

**What I'll do:**
- Query IMS-01 output JSON: retrieve firmographic criteria (industries, revenue range, employee count, countries), decision-maker titles, and win-loss signals
- Query Account/Company object: all records or your filtered subset (up to 10K per batch)
- Query Contact object: linked to matched accounts (up to 20K per batch)
- Optionally fetch Activity data (last 90 days) for engagement scoring

**Batch Strategy:** Fetch in 1,000–5,000-record increments to respect API rate limits.

**Data I need from each Account:**
- `Id`, `Name`, `Industry`, `Annual Revenue`, `Number of Employees`, `Country` (required)
- `Website`, `Company Description`, `Last Modified Date` (for freshness)
- `Account Source` (to identify how account was created)

**Data I need from each Contact:**
- `Id`, `Email`, `Phone`, `First Name`, `Last Name`, `Job Title`, `Account ID` (required)
- `Status` (Active/Inactive), `Last Activity Date`, `Created Date` (for engagement signals)

**What you'll see:** Progress indicator ("Fetched 1,000 / 10,000 accounts...").

---

### Step 2: Score Accounts Against ICP Firmographic Criteria

For each account, I'll calculate a **firmographic match score** (0–100):

```
Firmographic Score = (
  industry_match × 0.30 +
  revenue_match × 0.30 +
  employee_count_match × 0.25 +
  country_match × 0.15
) × 100
```

**Scoring logic:**
- **Industry match:** 1.0 if account industry is in ICP target list; 0.5 if adjacent industry; 0 if no match
- **Revenue match:** 1.0 if within ICP range; 0.7 if ±20% of range; 0 if outside
- **Employee count:** 1.0 if within ICP range; 0.7 if ±15% of range; 0 if outside
- **Country match:** 1.0 if in ICP country list; 0 if not

**Examples:**
| Account | Industry | Revenue | Employees | Country | Score |
|---------|----------|---------|-----------|---------|-------|
| Acme SaaS | Software (match) | $15M (in range) | 250 (in range) | US (match) | 100% |
| TechCorp | Technology (adjacent) | $8M (±20%) | 400 (in range) | US (match) | 85% |
| MegaCorp | Financial (no match) | $500M (out of range) | 5,000 (out) | US (match) | 15% |

---

### Step 3: Identify Decision-Maker Contacts (Job Title Matching)

For each contact at a high-scoring account, I'll match job titles against ICP decision-maker list:

**Matching strategies:**
1. **Exact match:** "VP Sales" matches ICP "VP Sales" → confidence 95%
2. **Fuzzy match (Jaro-Winkler ≥0.85):** "VP Revenue Ops" matches "VP Sales Ops" → confidence 85%
3. **Hierarchical match:** "VP Sales" matches ICP "Sales Leader" category → confidence 90%
4. **Department match:** "Sales Ops Manager" matches ICP "Operations" category → confidence 80%

**If normalization has run (DQH-02):**
- Job titles are already normalized to BLS taxonomy; matching is more accurate (+15% confidence)

**If normalization hasn't run:**
- I'll normalize internally: remove company names, standardize titles ("VP of Sales" → "VP Sales", "Chief Revenue Officer" → "Chief Revenue Officer")

---

### Step 4: Apply Win-Loss Signals (Filter for Disqualifiers)

For each high-scoring account + contact pair, I'll check for **loss signals** that should reduce confidence:

**Loss signals from ICP:**
- Company revenue <$5M (too early-stage)
- <50 employees (no dedicated RevOps function, decision-making scattered)
- No presence of target software stack (e.g., no CRM, no sales enablement tools)
- Company status = bankruptcy, acquired, dissolved

**For each loss signal, reduce confidence by 20–30%.**

**Example:**
- Account: $12M revenue, 200 employees, perfect industry match, perfect country → 95% confidence
- Check: Is company post-Series A? Yes ✓
- Check: Has RevOps function? (inferred: >100 employees + SaaS industry) Yes ✓
- Check: Software stack present? No ✗ → Reduce confidence by 20% → Final 75%

---

### Step 5: Enrich Missing Contact Fields (Optional)

If enrichment MCP is connected (ZoomInfo, Apollo, Hunter):
- **Email validation:** Verify email is active; flag undeliverable or role-based addresses
- **Phone enrichment:** Add direct phone if missing; flag if only main number available
- **Job title verification:** Confirm title is current; update if outdated
- **LinkedIn enrichment:** Add LinkedIn URL for sales automation

**If enrichment MCP not connected:** Proceed with native CRM data; flag limitation in output.

---

### Step 6: Calculate Final Outreach-Ready Score

For each contact, compute final score:

```
Final Score = (
  firmographic_score × 0.40 +
  job_title_match × 0.35 +
  loss_signals_penalty × -0.15 +
  enrichment_quality_bonus × 0.10
) × 100
```

**Confidence Tiers:**

| Confidence | Category | Action |
|---|---|---|
| **90–100%** | Perfect fit | Include immediately; prioritize for outreach |
| **75–89%** | Strong fit | Include; secondary priority |
| **60–74%** | Medium fit | Include with review; may need additional qualification |
| **<60%** | Weak fit | Exclude; poor ROI for outreach |

---

### Step 7: Generate Prospect List & Recommendations

**Output: Prospect List (CSV/JSON)**

Columns:
- Account ID, Account Name, Industry, Revenue, Employee Count
- Contact ID, Contact Email, Contact Name, Job Title
- Firmographic Score, Job Title Match Score, Final Outreach Score
- Enrichment Status, Last Updated, Suggested Personalization (e.g., "Targeting VP Sales post-Series A SaaS")

**Markdown Report:**

**Summary**
- Total accounts analyzed
- Accounts matching ICP (90%+ score)
- Prospect contacts identified
- Estimated time to outreach readiness
- Key insights (e.g., "Top 3 industries: SaaS, Professional Services, Marketing Tech")

**Details**
- Distribution table (how many prospects in 90–100% tier, 75–89%, 60–74%)
- Top 20 recommended accounts for immediate outreach
- Industry breakdown (which verticals are strongest fits)
- Data quality summary (% of contacts with valid email, phone, LinkedIn)

**Data Quality & Limitations**
- Assumptions (email = primary outreach channel, job titles normalized to BLS, etc.)
- Data gaps (% without email, % without phone) and impact on list quality
- Known limitations (can't detect role changes without enrichment, international character handling, M&A detection lag)
- Freshness status (when account data was last updated)

**Recommended Actions**
1. Review top 20 accounts; prioritize for first outreach wave
2. (Optional) Request enrichment for medium-fit prospects (60–74% tier) to improve data quality
3. Schedule monthly list refresh to catch new accounts matching ICP and re-score existing contacts
4. Configure list assignment in CRM (tag contacts with list name for tracking)
5. Pass list to OO-02 (Outbound Sequencing Agent) for campaign setup

**Sources & Citations**
- CRM data pulled [timestamp]
- ICP definition sourced from IMS-01 (updated [date])
- Firmographic matching thresholds per industry benchmarks (revenue ranges, employee counts per Gartner, SalesForce Research)

---

## Configuration Options

Before I start building your list, you can customize these parameters:

**Firmographic Weights:**
- "How should I weight industry vs. revenue vs. employee count?" (Default: 30% / 30% / 25% / 15%)
  - Industry-heavy: 0.45 / 0.25 / 0.20 / 0.10 (if you have deep vertical focus)
  - Revenue-heavy: 0.20 / 0.50 / 0.20 / 0.10 (if ACV is strong predictor)
  - Balanced: 0.30 / 0.30 / 0.25 / 0.15 (default, recommended)

**List Size & Prioritization:**
- "How many prospects do you want in the final list? (Default: 500)"
- "Should I prioritize newest accounts, most engaged, or best ICP fit?" (Default: best ICP fit)

**Enrichment Preferences:**
- "Enable email/phone enrichment?" (Default: Yes, if MCP connected)
- "Flag low-confidence contacts for manual review?" (Default: 60–74% tier)

**Exclusion Rules:**
- "Any accounts or industries to exclude? (e.g., do not include competitors, do not include <$2M ARR)"

**Refresh Schedule:**
- "Should I refresh this list monthly? (Default: Yes, automatic monthly re-scoring)"

---

## Error Handling

**If ICP definition is missing (IMS-01 has not run):**
- Message: "ICP definition not found. Please run IMS-01 first to define firmographic criteria, decision-maker titles, and target segments."
- Action: Offer to help run IMS-01 or accept manual ICP definition input
- Do not proceed until ICP is defined

**If required CRM data is missing:**
- Continue with available data; flag limitations in report
- Example: No revenue data → can only match on industry + employee count (confidence drops by 15–20%)
- Example: No email data → cannot build outreach-ready list; recommend enrichment first

**If MCP connection fails:**
- Offer to work with CSV export (slower but works offline)
- Provide troubleshooting steps for the MCP (API key, permissions, org ID)
- Proceed with degraded enrichment if possible

**If data quality is too low:**
- >30% of accounts missing Industry or Revenue → Proceed with caution; flag high false-positive risk
- >40% of contacts missing Email → Recommend enrichment before outreach
- <50% complete data → Recommend data standardization project first (DQH-02 Field Normalization)

**If API rate limits are hit:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (500 accounts instead of 1,000)
- Split into multiple runs (analyze different industries separately)

---

## What to Run Next

After list building is complete:

1. **OO-02: Outbound Sequencing Agent** — Takes your prospect list and designs a multi-touch email/call/LinkedIn campaign with optimal cadence.

2. **EM-ORCH-02: Event Orchestration Agent** — Uses your high-fit account list to target relevant attendees for webinars, conferences, or virtual events.

3. **PM-01: Pipeline Health Monitoring Agent** — Tracks prospects from OO-01 output through pipeline to measure conversion rates and improve list targeting over time.

4. **DQH-02: Field Normalization Agent** — If not yet run, normalize industry and job titles across your CRM to improve future list-building accuracy.

---

## Example: End-to-End List-Building Session

**You:** "Build me a prospect list from our CRM. Target our ICP profile for the next outreach wave."

**Me (Preflight):**
```
✓ Salesforce MCP connected
✓ IMS-01 ICP definition found (updated 5 days ago)
✓ Account + Contact objects ready
✓ Industry quality: 91% valid
✓ Revenue quality: 84% valid
✓ Email quality: 88% valid
✓ Analyzing 25,000 accounts + 62,000 contacts
```

**You:** "Build the full list. Top 500 prospects by ICP fit. Enable enrichment."

**Me (Analysis):**
```
Matching accounts against ICP criteria...
✓ Found 8,420 accounts with strong industry match (90%+)
✓ Found 6,200 accounts with revenue in ICP range (75%+)
✓ Found 5,100 accounts with employee count match (75%+)

Filtering for decision-maker contacts...
✓ Identified 12,400 contacts with job title match to ICP decision-makers

Enriching contact data...
✓ Verified 10,800 email addresses (87% deliverable)
✓ Added 2,200 phone numbers (from enrichment API)
✓ Normalized 12,400 job titles to BLS taxonomy

Scoring all prospects...
✓ 420 prospects at 90%+ confidence (Perfect fit)
✓ 1,800 prospects at 75–89% confidence (Strong fit)
✓ 2,280 prospects at 60–74% confidence (Medium fit)
```

**Report (Markdown + CSV):**
- Summary: "4,500 prospects identified matching ICP; 2,220 (49%) at strong/perfect fit tier. Top industries: SaaS (34%), Professional Services (28%), Marketing Tech (15%). Email validity: 87%. Ready for outreach."
- Details: Top 50 recommended accounts for Wave 1, ranked by ICP fit
- Data quality: "Email addresses are strong signal; phone data 78% present; job titles normalized and verified"

**You:** "This looks great. Download the top 500 and start sequencing them with OO-02."

**Me:** "Exporting top 500 to CSV: [download]. Confidence level: 91% (strong firmographic match + enriched contact data). Ready to hand off to OO-02 for campaign sequencing."

---

## References & Implementation Notes

**Detailed Processes (in references/ folder):**
- `icp_matching_algorithm.md` — Full score calculation with examples
- `firmographic_definitions.md` — How to map industry, revenue, employee ranges by segment
- `job_title_normalization.md` — BLS taxonomy mapping for decision-maker roles
- `enrichment_strategy.md` — When to use ZoomInfo vs. Apollo vs. Hunter
- `list_governance.md` — Monthly refresh cadence and quality SLAs

**Data Decay & Freshness:**
- B2B email addresses decay 3.6% monthly; 21% of a 1,000-contact list becomes invalid in 6 months
- Recommended refresh interval: Monthly for best results; quarterly minimum
- Set quality SLA: 90%+ email deliverability, 100% of ICP-critical fields populated

**Integration with Other Agents:**
- **Upstream:** IMS-01 (ICP Development) provides ICP criteria; DQH-02 (Field Normalization) improves accuracy
- **Downstream:** OO-02 (Outbound Sequencing), EM-ORCH-02 (Event Orchestration), PM-01 (Pipeline Health) consume output
