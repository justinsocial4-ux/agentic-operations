---
name: revops-data-contact-decay
description: "Identifies contacts in your CRM that have gone stale (no email opens, calls, meetings, or website visits for a configurable period) and routes them for archival, re-engagement campaigns, or data remediation. Tracks decay across multiple contact fields, assigns decay severity scores, and triggers workflows to clean up contact lists before stale data damages email sender reputation or inflates engagement metrics. Make sure to use this skill whenever the user asks to find stale contacts, check contact decay, identify outdated records, clean up old contacts, detect bounced emails, flag decaying contacts, remediate stale contact data, or archive inactive contacts—even if they do not name the agent."
metadata:
  category: "Data Quality & Hygiene"
  phase: "Phase 2"
  data_readiness: "30_days"
  version: "1.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-04-12"
  dependencies:
    - "revops-data-field-normalization"
  mcps:
    - "Salesforce MCP (Salesforce orgs)"
    - "HubSpot MCP (HubSpot orgs)"
    - "Outreach MCP (email engagement data)"
    - "SalesLoft MCP (email engagement data)"
    - "Gong MCP (call engagement data)"
  minimum_data:
    - "Contact object with Email, Phone, Title, Company, Last_Activity_Date fields"
    - "Lead object (Salesforce) or equivalent (HubSpot)"
    - "Account/Company object for company-level linking"
    - "30+ days of engagement history (Task, Event, or email platform records)"
---

# DQH-03 Contact Decay Detection & Remediation

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Compounding Contact Data Decay Destroys CRM Accuracy
- **Problem:** B2B contact data decays 22.5–70.3% annually; without re-verification, a CRM with 85% initial accuracy degrades to 45% within 12 months, rendering outreach unreliable.
- **Quantified cost to the role:** 20% of RevOps/Sales team time spent verifying outdated contacts (~$92k–$135k/year in labor per 5-person team) [RocketReach 2026]
- **What teams do today:** 16% clean lists once/twice per year; most spend $2k–$10k/year on paid hygiene tools (ZoomInfo, Apollo, Clearbit) [Porch Group 2026]
- **Why it's urgent:** 30% annual decay; if unchecked, 12-month accuracy drops from 85% → 45%. At 45%, the CRM is less useful than guessing. 30% bounce rates trigger domain blacklisting.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence; 3 TIER 1 sources

### Pain Point 2: Email Decay & Domain Blacklisting Risk
- **Problem:** Email addresses decay at 3.6% per month; after 6 months, 20%+ are invalid. 30% bounce rates trigger ISP blacklisting.
- **Quantified cost to the role:** Blacklist remediation costs $5k–$20k+ and takes 2–3 months; lost revenue during blacklist = $50k–$200k+ [KeepSync]
- **What teams do today:** Implement email validation tools ($500–$5k/year), hire data providers ($2k–$15k/year), manually segment lists to reduce bounces [Landbase, KeepSync]
- **Why it's urgent:** Stale email lists compound: 35%+ annual decay. Domain blacklisting is cumulative and irreversible without 2–3 month rehabilitation.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence; 2 TIER 1 sources

### Pain Point 3: Manual Re-Engagement & Archival Workflows Waste Time
- **Problem:** RevOps teams manually identify and archive stale contacts; 30% annual decay = ~546 hours/year wasted on dead contacts.
- **Quantified cost to the role:** 546 hours/year × $60/hour fully-loaded RevOps labor = $32,760/year; total workaround cost (contractors + tools) = $25k–$50k/year [SignalHire]
- **What teams do today:** Build custom Salesforce workflows, hire contractors for manual audits, or subscribe to third-party stale-contact flagging tools [Cognism, SignalHire]
- **Why it's urgent:** Manual archival backlog accumulates; new hires spend 40+ hours understanding which segments are viable. Revenue reps waste time chasing dead leads instead of real opportunities.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence; 2 TIER 1 sources

---

## What This Agent Does

The Contact Decay Detection & Remediation agent is your CRM's stale contact detective. It scans your contact and lead database to identify records that haven't engaged (email opens, calls, meetings, website visits) in a defined period. Using multi-field decay detection, it scores each contact on a 0–100 severity scale, classifies them into tiers (Active, Decaying, Stale, Archived Candidate), and routes them automatically to re-engagement campaigns, data enrichment, or archival workflows. Unlike quarterly manual cleanups, this agent runs continuously and integrates directly with your CRM and email platform to detect engagement decay in real-time and propose actions with confidence scores.

For live scoring, detailed audits, bulk-decision preparation, or exact-arithmetic requests, use `scripts/contact_decay_rules.py`. For a simple planning-only or no-tools explanation, use the identical inline weights, tiers, and approval rules below.

Load bundled references only when the task needs their detail:
- Read `references/decay_scoring_guide.md` for formula interpretation, exact weights, tier boundaries, or score QA.
- Read `references/field_decay_signals.md` when converting raw activity and data-quality evidence into the five signal scores.
- Read `references/remediation_workflows.md` before preparing live tasks, enrichment jobs, reassessment, or archival review.
- Read `references/decay_thresholds_by_segment.md` when the user wants to customize defaults by sales cycle or segment.
- Read `references/enrichment_vendor_guide.md` before choosing or invoking an enrichment source.
- Read `references/archival_playbook.md` before any archival plan or execution; explicit approval remains mandatory.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your CRM connection, confirm required engagement data exists, assess data quality, and ask you to scope your decay detection run.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- I'll also check for email engagement data sources: Outreach, SalesLoft, Gong, or native CRM EmailTracker.
- **If CRM connection fails:** I'll offer workarounds: export contacts to CSV for analysis, or help you troubleshoot the MCP connection.
- **If email platform is unavailable:** I'll proceed with degraded accuracy (using CRM's Last Activity Date only; confidence drops 20–30%).
- **If successful:** Proceed to Step 2.

**Step 2: Required Data Validation**
I'll verify that your Contact/Lead objects have these minimum fields:
- Email, Phone, FirstName, LastName (on Contact and/or Lead)
- Title, Company (for job title and company departure detection)
- Last_Activity_Date or equivalent engagement timestamp
- Account/Company linkage

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ Email engagement data incomplete → Partial results possible; I'll flag the limitation and proceed
- ⚠️ Email platform not connected → I'll use CRM Last Activity Date only (confidence: 65–75%)
- ✗ Core fields missing (Email field null in >20% of records) → No-go; request data enrichment first

**Step 3: Data Quality Assessment**
I'll calculate:
- % of contacts with valid emails (should be >80% for meaningful decay detection)
- % of contacts with activity data in past 24 months (should be >70%)
- Decay baseline: average days since last engagement by segment
- Current estimated stale contact rate (sample 500+ records)

**Step 4: Define Your Decay Run Scope**
Before proceeding, I'll ask:
- "Do you want to analyze ALL contacts, or a pilot set (e.g., created in last 180 days, specific accounts, specific lead sources)?"
- "What thresholds matter for your business? (Default: no email opens in 180+ days = stale; no calls in 240+ days = stale)"
- "Run mode: Analysis only (I show you decay and recommendations), or analysis with approval (I show you, you approve, then I execute re-engagement and archival)?"
- "Any contacts to exclude? (E.g., VIP accounts, active deals, current opportunities)"

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Outreach MCP connected (engagement data available)
✓ Contact object present with required fields
✓ Email data quality: 92% valid (46,000 / 50,000)
⚠️ Email engagement tracking: 84% of contacts have open data (some contacts lack Outreach integration)
✓ Last Activity Date: 89% of contacts have timestamp <24 months old
✓ Estimated decay baseline: 8.2% of contacts show no engagement >180 days
✓ Ready to proceed

Scope: All 50,000 Contact records | Analysis-only mode | Exclude: closed-won opportunities, active deals

Next step: Scanning 50,000 records for decay signals...
```

---

## Step-by-Step Workflow

### Step 1: Fetch Contact Records & Engagement History (in batches)

**What I'll do:**
- Query Contact object: all records or your filtered subset (up to 5K per batch to respect API limits)
- Query Lead object (Salesforce) or Lead-type Contacts (HubSpot)
- Query Account/Company records linked to contacts
- For each contact, fetch engagement history from email platform (Outreach, SalesLoft, Gong) or CRM Task/Event records

**Data I need from each record:**
- `Id`, `Email`, `Phone`, `FirstName`, `LastName`, `Title`, `Company` (required)
- `CreatedDate`, `LastModifiedDate`, `Account_Id` (for company linkage)
- `Last_Activity_Date` or equivalent engagement timestamp
- Email engagement: Last open date, bounce status, sent count
- Phone engagement: Last call date, call count
- Account linkage status (linked, unlinked, company acquired)

**What you'll see:** Progress indicator ("Fetched 5K / 50K records...").

---

### Step 2: Calculate 5 Core Decay Signals

For each contact, I'll assess decay across five dimensions:

#### Signal 1: Email Engagement Decay
- Days since last open
- Bounce status (hard bounce = high decay, soft bounce = medium, valid = low)
- Email decay rate: 3.6% per month = 35%+ annually
- Score: 0 (active: <30 days) → 25 (decaying: 31–90 days) → 60 (stale: 91–180 days) → 90 (archived: >180 days)

#### Signal 2: Phone Engagement Decay
- Days since last call
- Phone validity status (from data enrichment or carrier verification)
- Phone decay rate: 1.5% per month = 15% annually
- Score: 0 (active: <120 days) → 35 (decaying: 121–240 days) → 70 (stale: >240 days)

#### Signal 3: Job Title Staleness
- Title field completeness (missing title = higher decay risk)
- Title recency: changed in past 12 months (current), 12–24 months (aging), 24+ months (stale)
- Title accuracy: compare to industry/company baseline for role inflation/degradation
- Score: 0 (current and accurate) → 30 (aging) → 60 (very stale)

#### Signal 4: Company Departure Risk
- Account linkage status (linked to active account = low risk; orphaned = high risk)
- Company acquisition detection (if account was acquired, contact may have left)
- LinkedIn/ZoomInfo confirmation of current employer (if available)
- Score: 0 (linked, active company) → 50 (orphaned or company changed owner) → 85 (company acquired or deleted)

#### Signal 5: Overall Engagement Decay
- Last engagement date (MAX of all engagement channels: email, phone, meetings, website visits)
- Days since last engagement
- Score: 0 (<30 days) → 25 (31–90) → 60 (91–180) → 90 (>180 days)

---

### Step 3: Compute Composite Decay Severity Score (0–100)

**Weighted formula:**
```
Decay Score = (
  Email Engagement Score × 0.35 +
  Phone Engagement Score × 0.25 +
  Title Staleness Score × 0.15 +
  Company Departure Score × 0.15 +
  Overall Engagement Score × 0.10
) × 100
```

**Example:**
- Email engagement: no opens in 120 days → Score 60
- Phone engagement: no calls in 150 days → Score 35
- Title: unchanged 18 months → Score 20
- Company: linked, active → Score 0
- Overall engagement: 120 days → Score 60
- **Composite = (60×0.35 + 35×0.25 + 20×0.15 + 0×0.15 + 60×0.10) = 21 + 8.75 + 3 + 0 + 6 = 38.75 → Score 39 (DECAYING)**

---

### Step 4: Classify Contacts into Severity Tiers

**Tier Assignment (based on composite score):**

| Score | Status | Interpretation | Action |
|-------|--------|---|---|
| **0–30** | ACTIVE | Recent engagement; all fields current | MONITOR — no action needed |
| **31–60** | DECAYING | Some engagement drop-off; field aging begins | RE_ENGAGE — create SDR task, nurture campaign |
| **61–85** | STALE | Significant engagement gap (120+ days) + field decay | ENRICH_AND_DECIDE — verify/refresh data, then decide on re-engagement vs. archival |
| **86–100** | ARCHIVED_CANDIDATE | No engagement 180+ days + multiple field failures | ARCHIVE_RECOMMEND — flag for archival review + approval |

---

### Step 5: Route to Remediation Workflows

**For Decaying Contacts (31–60):**
- Create SDR task: "Reach out to [contact] — no activity in [X days]"
- Suggest re-engagement template (email + call sequence)
- Track response; if no reply in 30 days, escalate to Stale

**For Stale Contacts (61–85):**
- Batch enqueue for data enrichment (ZoomInfo, Clay, Apollo) to verify phone + company
- Create RevOps task: "Review [contact] — stale decay signal. Enrich and re-verify."
- After enrichment, auto-reassess decay score; if still stale, flag for archival consideration

**For Archived Candidates (86–100):**
- Set `Archival_Recommended__c = TRUE`
- Create escalation task for RevOps: "Approve archival for [contact] — no engagement 180+ days, email bounced, phone disconnected."
- REQUIRES explicit user approval before archival (safety mechanism)
- Post Slack alert to RevOps team: "N archived candidates ready for review"

---

### Step 6: Generate Outputs

**Output 1: Markdown Decay Report**
```
## Agent: DQH-03 Contact Decay Detection & Remediation

**Request:** [Your request]  
**Timestamp:** [ISO 8601]  
**Confidence:** [0–100 based on data completeness]  
**Run ID:** DQH-03-RUN-[DATE-TIME]

### Summary
[1–2 sentences: total analyzed, decay distribution, primary recommendation]

### Details

#### Decay Status Distribution
| Status | Count | % | Avg Score | Action |
|--------|-------|---|-----------|--------|
| Active (0–30) | 9,603 | 77.1% | 12 | Monitor |
| Decaying (31–60) | 891 | 7.2% | 45 | Re-engage |
| Stale (61–85) | 574 | 4.6% | 72 | Enrich & Review |
| Archived Candidate (86–100) | 178 | 1.4% | 92 | Archival Review |

#### Decay Drivers (Top Reasons)
[Table showing primary decay factors: no email opens, phone disconnected, title stale, company departure, etc.]

#### Contacts Recommended for Re-Engagement (Top 20)
[Sample table with contact name, company, title, days since engagement, email status, phone status, recommendation]

#### Contacts Recommended for Archival (Top 10)
[Sample table with contact, company, decay score, reason, archival recommendation]

### Data Quality & Limitations

**Assumptions made:**
- Email engagement timestamps from [Outreach/SalesLoft/Gong]; falls back to CRM Last Activity Date if unavailable.
- Phone validation based on last enrichment (90 days old); actual validity may have changed.
- Company departure inferred from account unlinking; LinkedIn confirmation not automated.

**Data gaps and impact:**
- X% of contacts lack email engagement data → Decay score relies on phone + title signals only (confidence -15–20%)
- Y% have no phone data → Cannot detect phone decay; flagged for enrichment
- Z% not enriched in 6+ months → Phone validity is stale; re-enrichment recommended before archival

**Known limitations:**
- Cannot confirm email undeliverability without sending; relies on bounce history (recommend Zerobounce/NeverBounce for hard validation)
- Job title promotions ("Director" → "VP") are not penalized; title changes are scored contextually
- Job departures detected only via account unlinking or LinkedIn refresh; no automated employment verification

### Recommended Actions

1. **Approve Re-Engagement for [N] Decaying Contacts:** Schedule review of re-engagement template. Create SDR tasks for top [M] by company size. Run automated campaign for remainder. Track re-activation rate (expect 10–20%). Timeline: Next 7 days.

2. **Enrich [N] Stale Contacts:** Batch enqueue for ZoomInfo/Clay/Apollo refresh. Cost: $[X]. Turnaround: 3–5 business days. Reassess decay scores after enrichment. Timeline: Execute immediately; reassess in 5 days.

3. **Review & Approve Archival for [N] Archived Candidates:** Schedule 30-min meeting. Spot-check via LinkedIn that contacts are no longer at company. Approve batch archival. Timeline: Approve this week; execute next week.

4. **Set Up Continuous Monitoring:** Configure weekly runs. Enable Slack alerts for new archived candidates. Review decay trends monthly.

### Sources & Citations

- Contact counts: Salesforce/HubSpot Contact + Lead objects, pulled [DATE]
- Engagement data: Outreach/SalesLoft API, pulled [DATE]
- Decay rate benchmarks: RocketReach 2026, Landbase, KeepSync (email decay 3.6%/mo, phone decay 1.5%/mo)
```

**Output 2: JSON Transaction Log**
(Full remediation metadata: contact IDs, decay scores, assigned actions, task IDs, enrichment job IDs, archival approval status)

**Output 3: CSV Export**
(For bulk import into CRM or external workflow systems: contact_id, email, name, company, decay_score, decay_status, action, task_id)

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

**Decay Thresholds (Days of Inactivity):**
- "Email no-open threshold: [default: 180 days]"
- "Phone no-call threshold: [default: 240 days]"
- "Title stale threshold: [default: 24 months]"

**Severity Thresholds (Score Ranges):**
- "Active range: [default: 0–30]"
- "Decaying range: [default: 31–60]"
- "Stale range: [default: 61–85]"
- "Archived candidate range: [default: 86–100]"

**Remediation Automation:**
- "Auto-create re-engagement tasks? [default: Yes]"
- "Auto-enqueue enrichment? [default: Yes]"
- "Require approval before archival? [default: Yes — enforced for safety]"
- "Re-engagement campaign ID: [optional]"
- "Enrichment vendors: [default: ZoomInfo, Clay]"
- "Slack webhook for alerts: [optional]"

---

## Error Handling

**If MCP connection fails (Salesforce, HubSpot):**
- Offer to work with CSV export instead
- Provide troubleshooting steps for MCP reconnection (API key, permissions, org ID)

**If email platform integration unavailable:**
- Proceed with degraded accuracy (CRM Last Activity Date only)
- Decay scores will be 20–40% less reliable; clearly flag this
- Recommend connecting Outreach, SalesLoft, or Gong to improve accuracy

**If insufficient engagement data (<30% of contacts have activity):**
- Refuse to proceed; explain why (too unreliable)
- Recommend data recovery or enrichment first
- Provide timeline estimate for getting data ready

**If data quality too low (<50% email completeness):**
- Flag high false-positive risk
- Recommend enrichment (ZoomInfo, Clay) before proceeding
- Offer degraded analysis with very low confidence score

**If API rate limits hit:**
- Implement exponential backoff (2s, 4s, 8s between retries)
- Batch smaller (500 records instead of 1K)
- Split into multiple runs (different date ranges)

---

## What to Run Next

After decay detection is complete:

1. **DQH-04: CRM Health Score Agent** — Measure data quality improvement; establish baseline for ongoing health monitoring.

2. **DQH-05: Enrichment Orchestration Agent** — Routes stale contacts needing re-verification to enrichment sources before re-engagement.

3. **Schedule Recurring Decay Runs** — Set up weekly or monthly scans to catch new decay as it emerges.

---

## Example: End-to-End Decay Session

**You:** "Find stale contacts in my Salesforce and show me which ones to clean up."

**Me (Preflight):**
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Outreach MCP connected (email engagement data available)
✓ Contact object ready with required fields
✓ Email quality: 91% valid (45,500 / 50,000)
✓ Engagement data: 87% of contacts have Last Activity <24mo
✓ Analyzing 50,000 contacts...
```

**You:** "Run a full analysis. Show me everything; no automated actions yet."

**Me (Analysis):**
```
Scanning for decay signals across 5 dimensions...
✓ Processed email engagement (Outreach API)
✓ Processed phone engagement (Salesforce Task records)
✓ Processed title staleness (CRM field history)
✓ Processed company departure risk (Account linkage)
✓ Calculated composite decay scores

Classifying contacts...
✓ 9,603 Active (77.1%)
✓ 891 Decaying (7.2%)
✓ 574 Stale (4.6%)
✓ 178 Archived Candidates (1.4%)
Total: 11,246 at-risk contacts

Generating report...
```

**Report Summary:**
- "Analyzed 50,000 contacts. Found 1,643 with decay signals (3.3%). Breakdown: 891 Decaying (no action yet, but at risk); 574 Stale (need enrichment + review); 178 Archived Candidates (recommend archival). Top decay driver: no email opens in 180+ days (47% of decaying contacts)."

**Details Table:**
- Decay status distribution (counts, %)
- Top 20 decaying contacts by company size (for SDR prioritization)
- Top 10 archived candidates by decay score
- Segment breakdown (decay rate by industry, company size, lead source)

**You:** "This looks good. I want to approve the re-engagement for Decaying. But hold off on archival until I manually spot-check a few archived candidates."

**Me:** "Executing re-engagement task creation for 891 Decaying contacts... ✓ Complete. Created 891 SDR tasks (assigned to sales_ops_queue). Review archival candidates in the report; send me approval when ready."

---

## References & Further Reading

These six files are routed near the top of this skill. They preserve the frozen pilot defaults, identify assumptions that need customer validation, and separate detailed operating guidance from the main workflow.
