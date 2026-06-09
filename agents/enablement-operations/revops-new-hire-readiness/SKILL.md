---
name: revops-new-hire-readiness
description: Tracks new hire onboarding completion and ramp-to-quota progress from
  Day 1 through productive independence. Aggregates LMS training data, CRM activity,
  and onboarding milestones into a unified dashboard with early-warning alerts for
  at-risk ramps and training-to-performance correlation analysis.
metadata:
  trigger_phrases:
  - track new hire readiness
  - check onboarding progress
  - identify at-risk ramps
  - monitor new hire ramp
  - assess onboarding completion
  - show new hire dashboard
  - new hire readiness report
  - ramp curve analysis
  - training completion status
  - early warning alerts
  category: Enablement Operations
  phase: 30_days
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents: []
    mcps:
    - Salesforce MCP (Salesforce orgs) OR HubSpot MCP (HubSpot orgs)
    - LMS API Integration (Docebo, Lessonly, WorkRamp, or similar)
    - Training Platform API (MindTickle or Allego) — optional but recommended
    - Snowflake MCP (optional; for advanced benchmarking)
    minimum_data:
    - 'Contact/User object with: Email, Phone, FirstName, LastName, Start_Date, Manager'
    - CRM Activity table (Task, Event, Call) with dates and types
    - Opportunity object with Close_Date, Amount, Stage, Owner
    - LMS course enrollments and completion records
  output_format: markdown_report
---

# EO-ONBD-01 New Hire Readiness Agent

## Why This Agent Exists

**Who it's for (ICP):** Sales Enablement Manager or VP Sales at B2B SaaS companies, 100–500 employees, North America.

**The painkiller pain points we're solving:**

### Pain Point 1: Lost Visibility Into Onboarding Completion
- **Problem:** Managers lack real-time visibility into onboarding milestone completion. Tracking relies on email, spreadsheets, or ad-hoc check-ins. Missed training modules or delayed certifications are discovered weeks later or not at all.
- **Quantified impact:** 62% of sales organizations report ineffective onboarding programs (AIHR 2026). Manual tracking costs 2–4 hours/week per manager (8–16 hours/month per org).
- **Painkiller Score:** 4/4 PASS ✓

### Pain Point 2: No Early Warning System for At-Risk Ramps
- **Problem:** Managers cannot identify new hires at risk of extending beyond expected ramp time until the problem is severe. Without benchmarked expectations (e.g., "should complete onboarding by Day 5," "should reach 25% quota by Month 1"), managers react reactively rather than preventatively.
- **Quantified impact:** New hire ramp time increased 32% over four years (4.3 months in 2020 → 5.7 months in 2024). Extended ramp can represent 5% of annual revenue loss. Delayed ramp from 4.2 to 5.7 months costs ~$11.7K in lost revenue per AE.
- **Painkiller Score:** 4/4 PASS ✓

### Pain Point 3: Fragmented Data Across LMS, CRM, and Training Platforms
- **Problem:** Onboarding data lives in silos: training completion in LMS (Docebo, Lessonly, WorkRamp), CRM activity in Salesforce/HubSpot, certifications in MindTickle/Allego. Managers must manually log into 4–5 systems to piece together a new hire's true readiness status.
- **Quantified impact:** Fragmentation introduces delays, errors, and missed correlations. Managers spend 15–20 minutes per new hire per week assembling data manually.
- **Painkiller Score:** 4/4 PASS ✓

### Pain Point 4: No Proactive Correlation Between Training Completion and Performance
- **Problem:** Managers cannot easily see whether completing a training module correlates with improved sales performance (calls, deals, quota progress). This makes it hard to optimize onboarding content or identify which hires need coaching.
- **Quantified impact:** Without training-to-performance data, enablement teams cannot measure ROI or optimize content. Organizations cannot answer "does this module actually improve quota attainment?"
- **Painkiller Score:** 4/4 PASS ✓

| Pain Point | Frequency | Severity | Consistency | Addressability | PASS |
|---|---|---|---|---|---|
| Lost visibility into onboarding completion | High (100+ hires/yr) | High (62% ineffective programs) | High (all target orgs) | High (dashboard solves) | ✓ |
| No early warning for at-risk ramps | High (all ramps) | Critical (5% revenue impact) | High (all target orgs) | High (benchmarks + alerts) | ✓ |
| Fragmented data across LMS/CRM/training platforms | High (multiple logins/week) | Medium-high (data loss, delays) | High (all target orgs) | High (aggregation engine) | ✓ |
| No training-to-performance correlation | High (continuous evaluation) | High (can't optimize programs) | High (all target orgs) | High (real-time correlation) | ✓ |

---

## What This Agent Does

The New Hire Readiness Agent is your visibility layer into how new hires are progressing through their first critical months. It pulls together training completions from your LMS, sales activity from your CRM, and onboarding milestones into a single, unified picture. Rather than requiring you to check five different systems, the agent shows you one dashboard: who's on track, who's at risk, what milestones they're missing, and how their actual quota progress compares to what you'd expect at this stage in their ramp. It runs continuously, flags at-risk new hires before the problem becomes critical, and gives you actionable insights—like which training modules actually correlate with better quota outcomes. Think of it as an early warning system that catches ramp problems when intervention still works.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your data connections, confirm required data exists, assess data quality, and ask you to scope your analysis.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- I'll verify LMS API connection is active (Docebo, Lessonly, WorkRamp, or similar).
- **If CRM connection fails:** I'll offer workarounds: export contact + activity data as CSV, or help you reconnect the MCP.
- **If LMS connection fails:** I'll proceed with CRM data only (you'll get activity tracking but no training correlation).
- **If both fail:** No-go; request MCP reconnection before proceeding.

**Step 2: Required Data Validation**
I'll verify that your Contact/User and Activity objects have these minimum fields:
- Contact/User: Email, FirstName, LastName, Start_Date, Manager, Role (AE, SDR, CSM, Other)
- Activity: ActivityDate, ActivityType, Contact link
- Opportunity: Close_Date, Amount, Stage, Owner

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ 1–2 fields missing → Partial results possible; I'll flag the limitation and proceed
- ✗ Core fields missing (e.g., no Start_Date at all) → No-go; request data standardization first

**Step 3: Data Quality Assessment**
I'll calculate:
- % of new hire records with Start_Date (should be >80%)
- % of records with Manager assigned (should be >75%)
- Data freshness (when CRM/LMS last synced; <24 hours is ideal; >48 hours is warning)
- Sample size (active new hires in past 12 months; need ≥5 for meaningful analysis)
- Current missing data rate (training completions, activities) and impact

**Step 4: Define Your Scope**
Before running the analysis, I'll ask:
- "Which roles do you want to track? (AE, SDR, CSM, or all)"
- "Do you want to track all new hires from the past 12 months, or a specific cohort (e.g., hires in last 90 days)?"
- "Do you want real-time dashboard access, email alerts, Slack notifications, or all three?"
- "Do you have custom onboarding milestones, or should I use default benchmarks for your roles?"

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ LMS API connected (Docebo instance: acme.docebo.com)
✓ Contact data quality: 94% have Start_Date (89/95 new hires in past 12 months)
✓ Manager assignment: 87% (82/95)
⚠️ Data freshness: Last CRM sync 18 hours ago (acceptable)
⚠️ LMS data: 24 hours stale (Docebo sync runs overnight)
✓ Sample size: 95 active new hires (adequate for analysis)
✓ Ready to proceed

Scope: AE + SDR roles | Past 12 months | All 3 alert channels | Default benchmarks

Next step: Loading new hire data and calculating progress...
```

---

## Step-by-Step Workflow

### Step 1: Fetch and Normalize New Hire Master Data

**What I'll do:**
- Query Contact/User objects for all records with Start_Date in the past 12 months (or your specified lookback)
- Filter to active employees (exclude departed, maternity leave, etc.)
- Extract: ID, Name, Email, Phone, Start_Date, Role, Manager_ID, Territory, Quota_Annual
- Normalize timestamps to UTC
- Flag any records with missing required fields

**Batch strategy:** Fetch in 500-record increments to respect API rate limits.

**What you'll see:** Progress indicator ("Loading 47 new hires from Salesforce...").

---

### Step 2: Fetch Training Completions from LMS

**What I'll do:**
- Query LMS for all course enrollments and completions from the past 12 months
- Match LMS user IDs to CRM contacts via email address
- Extract: Course name, Completion date, Score, Certification status
- Normalize course names (handle abbreviations, spelling variants)

**Fallback:** If LMS API is unavailable, proceed with CRM data only (skip training correlation).

---

### Step 3: Fetch CRM Activities and Opportunities

**What I'll do:**
- Query Task, Event, Call records (Salesforce) or Task records (HubSpot) for each new hire
- Extract: Date, Type, Contact link, Duration, Notes
- Identify first call, first demo, first meeting, first task logged
- Query Opportunity/Deal records: Close_Date, Amount, Stage, Owner

**Activity types tracked:**
- First Call (earliest Task/Event/Call)
- First Demo (first "Demo" activity or meeting type)
- First Deal Logged (first Opportunity created)
- First Qualified Deal (first Opportunity at "Qualified" stage or equivalent)

---

### Step 4: Build Milestone Timeline & Track Completion Status

**For each new hire, I'll:**
- Load the onboarding milestone template for their role (AE, SDR, CSM)
- For each milestone, match it to completed activities:
  - Training milestones → LMS completions
  - Activity milestones → CRM activities
  - Certification milestones → Training platform records
- Calculate actual vs. expected dates
- Mark status: ✓ Completed (on-time or late), ⚠️ Overdue, ⏳ In Progress, ○ Pending

**Milestone data structure:**
```
{
  name: "First Demo",
  expected_days_from_start: 21,
  actual_completion_date: "2026-05-23",
  expected_completion_date: "2026-05-22",
  days_behind: 1,
  status: "completed_late",
  data_source: "Salesforce Activity"
}
```

---

### Step 5: Calculate Ramp Progress Snapshot

**For each new hire, I'll calculate:**

- **Days since start:** today - hire_start_date
- **Milestones completed:** count of status = "completed"
- **Milestones on-time:** count of status = "completed" AND days_behind ≤ 0
- **Milestones at-risk:** count of status = "overdue" OR (status = "pending" AND expected_date < today)
- **Current quota attainment:** sum(deal amounts closed this month) / monthly_quota_target × 100%
- **Expected quota attainment:** interpolated from ramp curve benchmark for this day
- **Quota gap:** expected - actual
- **Days behind schedule:** max(days_behind from all milestones)
- **Overall status:** Determine based on thresholds:
  - If days_behind_schedule > 10 OR quota_gap > 20%: 🔴 AT-RISK
  - Else if days_behind_schedule > 5 OR quota_gap > 10%: 🟡 SLIGHTLY BEHIND
  - Else: ✅ ON-TRACK

---

### Step 6: Generate Early Warning Alerts

**I'll evaluate each new hire against these trigger rules:**

| Alert Type | Trigger | Severity | Action |
|---|---|---|---|
| **Milestone Overdue** | Required milestone >10 days past expected date | HIGH | Alert manager; suggest intervention |
| **Quota Gap** | Actual quota <80% of expected for this day | HIGH | Alert manager; review pipeline |
| **Activity Stalled** | No CRM activity in past 7 days (>Day 14) | MEDIUM | Verify data freshness or engagement |
| **Ramp Trajectory At-Risk** | Days behind >10 AND quota gap >15% | CRITICAL | Alert manager + enablement lead |
| **Training Gap** | Required certification incomplete past deadline | MEDIUM | Alert manager; escalate to training |

**Alert delivery:**
- Email subject: `[ALERT] {First_Name} {Last_Name} is at risk: {Reason}`
- Slack format: `:warning: {Severity} {First_Name} ({Role}) — {Reason}. Days behind: {Days_Behind_Schedule}.`
- Dashboard: Priority card (critical first)
- Alert deduplication: Don't re-alert within 24 hours if same hire + alert type already sent

---

### Step 7: Generate Training-to-Performance Correlation Analysis (Monthly)

**Once per month, I'll analyze:**

For each training module and cohort of new hires (by role + hire month):
- Count who completed the module by end of Month 1
- Count who didn't complete it
- Compare average quota attainment in Month 2 between groups
- Classify correlation strength (HIGH, MEDIUM, LOW, NONE)
- Generate recommendation (mandatory, defer, monitor, etc.)

**Output example:**
```
Objection Handling Mastery Module (May 2026 AE Cohort)
├─ Completers: 8 hires | Avg Month 2 Quota: 48%
├─ Non-completers: 3 hires | Avg Month 2 Quota: 32%
├─ Correlation: HIGH (+16 percentage points) ✓
├─ Statistical significance: p < 0.05 ✓
└─ Recommendation: Mandatory completion by Day 8 (strong correlation with quota)
```

---

### Step 8: Generate Output Report

**Markdown Report with standard sections:**

**Summary**
- Total new hires analyzed
- On-track / slightly behind / at-risk breakdown
- Average days behind schedule
- Recommended next actions (top 3)

**Details**
- New Hire Progress Cards (one card per hire with all key metrics)
- Ramp curve chart (actual vs. expected over time)
- Milestone timeline (Gantt or narrative)
- Alert summary (critical alerts first)
- Training correlation findings (if applicable)

**Data Quality & Limitations**
- Data sources and freshness
- Missing data % and impact (e.g., "12% of hires missing first demo date; correlation analysis skipped")
- Assumptions (benchmark ramp curve, email matching for LMS, etc.)

**Recommended Actions**
- Top 3 at-risk new hires and interventions
- Training modules with high correlation to quota
- System improvements (data quality, onboarding refinements, etc.)

**Sources & Citations**
- Salesforce data pulled [timestamp]
- LMS data pulled [timestamp]
- Ramp benchmarks: AE 5.7 months, SDR 4.0 months (industry standard; customizable)

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

**Ramp Benchmarks:**
- "What's the expected ramp time for each role?" (Default: AE 5.7 months, SDR 4.0 months, CSM 3.5 months)
- "Should I use industry benchmarks or your historical data?" (Default: industry benchmarks; switch if you have 12+ months of historical ramp data)

**Milestone Thresholds:**
- "When should milestones be completed?" (Default: Product Training by Day 5, First Call by Day 10, First Demo by Day 21)
- "Which milestones are blocking (must complete before rep can progress)?" (Default: Product Training, CRM Certification, First Call)

**Alert Thresholds:**
- "How many days behind before I get an alert?" (Default: >10 days)
- "What quota gap triggers an alert?" (Default: >20% below expected)
- "Should I receive all alerts or only critical ones?" (Default: HIGH + CRITICAL only; MEDIUM optional)

**Scope & Filtering:**
- "Which roles?" (Default: all AE, SDR, CSM)
- "Which time period?" (Default: past 12 months)
- "Which managers/regions?" (Default: all)
- "Alert channels?" (Default: Dashboard + Email; add Slack if connected)

**Compliance:**
- "Enable audit logging for compliance?" (Default: Yes)
- "Should I flag coaching/PIP status separately?" (Default: No)

---

## Error Handling

**If CRM MCP connection fails:**
- Offer to work with exported contact + activity CSV instead
- Provide troubleshooting steps (check API key, org ID, permissions)
- Suggest deferring analysis until connection is restored

**If LMS connection fails:**
- Proceed with CRM data only (activity milestones work, training correlation skipped)
- Flag in report: "Training data unavailable; correlation analysis skipped"
- Confidence score drops from 85% to 65%

**If required data is missing:**
- **Missing Start_Date on >20% of records:** Proceed but flag; ask for data standardization
- **Missing Manager on >30% of records:** Proceed but alert routing may fail; suggest enrichment
- **No Activity data at all:** Can't calculate "first call" milestone; flag as limitation

**If data quality is too low:**
- **<5 active new hires:** Sample too small for correlation analysis; proceed with individual tracking only
- **<50% training data available:** Training correlation skipped (insufficient coverage)
- **>48 hours data lag:** Proceed but flag in alerts: "Data may be 1–2 days stale"

**If API rate limits are hit:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (250 records instead of 500)
- Split into multiple runs (analyze different date ranges or roles separately)

**If data consistency issues:**
- Example: New hire in LMS with no CRM contact. Offer to reconcile via email matching.
- Example: Deal closed for non-existent new hire. Flag as data quality issue; exclude from analysis.

---

## What to Run Next

After new hire readiness analysis is complete:

1. **EO-04: Certification Tracking Agent** — Deep dive into which training certifications are missing and why. Complements this agent by focusing on specific module performance and skipped content.

2. **PM-01: Pipeline Health Monitoring Agent** (Wave 3) — Use new hire ramp quality as a predictive signal for early-career tenure risk. Flag new hires at risk of attrition based on slow ramp.

3. **RA-01: Weekly Revenue Narrative Agent** (Wave 4) — Contextualize weekly revenue updates with new hire ramp progress (e.g., "new hires are on-track, contributing $X to forecast").

4. **Schedule Recurring Readiness Checks** — Set up weekly or bi-weekly runs to track progress continuously and catch ramp issues early.

---

## Example: End-to-End Session

**You:** "Show me how my May 2026 AE cohort is ramping. I want to know who's at risk and what training modules actually matter."

**Me (Preflight):**
```
✓ Salesforce MCP connected (Org: Acme SalesForce)
✓ LMS API connected (Docebo instance: acme.docebo.com)
✓ Contact data: 23 AEs hired in May 2026, all with Start_Date and Manager
✓ CRM activities: 21/23 have at least one activity logged
⚠️ LMS data: Only 18/23 have training completions (5 pending LMS enrollment)
✓ Ready to proceed

Scope: May 2026 AE Cohort (23 hires) | Industry benchmarks (5.7-month ramp) | All alert channels

Loading data...
```

**Me (Analysis):**
```
Analyzing May 2026 AE cohort (23 hires, 28 days into ramp)...

✓ Data loaded from Salesforce (23 AEs) and Docebo (18 training records)
✓ Milestones tracked: 5 of 8 completion rates calculated
✓ Ramp progress calculated: 16 on-track, 5 slightly behind, 2 at-risk
✓ Early-warning alerts: 2 critical, 3 high severity
✓ Training-to-performance: Preliminary (need 30+ days; will have full analysis by June 1)
```

**Report (Markdown + Dashboard):**

```
## New Hire Readiness Report — May 2026 AE Cohort

**Request:** Ramp progress and at-risk identification for 23 AEs hired in May 2026
**Timestamp:** 2026-05-28T14:22:00Z
**Confidence:** 82% (18/23 with complete LMS data; 5 pending enrollment)

### Summary
- **Active new hires:** 23 AEs in ramp
- **On-track:** 16 (70%)
- **Slightly behind:** 5 (22%)
- **At-risk:** 2 (9%)
- **Average days behind schedule:** 2
- **Urgent action needed:** 2 (critical alerts)

### Details

**🔴 CRITICAL ALERTS (2)**

1. **Sarah Chen (AE) — 12 days behind on First Demo milestone**
   - Expected First Demo: May 23 | Actual: Not yet logged (today is May 28)
   - Milestones: 6/8 completed (all on-time except First Demo)
   - Quota: 8% actual | 15% expected | Gap: -7%
   - Last Activity: May 27 (call review with manager)
   - Recommended Action: Check in today on demo readiness. Consider role-play or pairing with top performer (Lisa Park) for 2–3 live demos.

2. **Marcus Johnson (AE, transferred from SDR) — Quota 22% below expected**
   - Milestones: 7/8 completed (on-time)
   - Quota: 18% actual | 40% expected | Gap: -22%
   - Days behind: 6
   - Last Activity: May 25 (email to prospect; no calls or demos in past 3 days)
   - Recommended Action: Urgent check-in. Likely issue: pipeline quality or objection-handling confidence. Recommend shadowing top AE this week.

**🟡 HIGH ALERTS (3)**

- James Rodriguez: Objection Handling certification 4 days overdue (expected May 24, completed May 28)
- Priya Patel: No demo scheduled; approaching Day 28 with no demo activity
- David Kim: Product Training score 71% (below cohort avg 84%); recommend refresher

**✅ ON-TRACK (16)**

- Lisa Park: 57 days in, 42% quota (2% ahead), all milestones complete
- Jennifer Wu: 31 days in, 18% quota (on-target), trending well
- [List of 14 others]

### Ramp Curve Comparison

```
May 2026 AE Cohort: Actual vs. Expected Quota Attainment

100% ┤                                                    Expected
     ├                                                 ╱──────
  80% ┤                                            ╱─────
     ├                                        ╱────
  60% ┤                                   ╱────
     ├                               ╱────
  40% ┤                          ╱────
     ├                      ╱────  Actual (Mean)
  20% ┤                ╱────
     ├           ╱────
   0% └──────────────────────────────────────────────────
     0    10    20    30    40    50    60
               Days Since Start

Current (Day 28): 18% actual vs 15% expected = +3% (AHEAD)
Cohort Trend: Strong overall; 2 outliers pulling down average
```

### Training-to-Performance Correlation (Preliminary)

**Note:** Full correlation analysis available after Day 30 (June 1). Preliminary findings:

- **Product Training:** All 23 completed by Day 5. 100% completion, too early to correlate.
- **Objection Handling:** 20/23 completed (87%). 
  - Completers avg quota (Day 28): 19%
  - Non-completers avg quota (Day 28): 5%
  - Preliminary correlation: MEDIUM (likely causal; confident reps close more deals)
  - Recommendation: Monitor; likely to be HIGH correlation by Month 2

### Data Quality & Limitations

**Sources:**
- Salesforce: Contact, Activity, Opportunity data pulled May 28, 14:22 UTC
- Docebo LMS: Course enrollment/completion data pulled May 28, 12:00 UTC (24-hour refresh cycle)
- HRIS: Start dates sourced from Salesforce User records

**Missing Data:**
- 5 AEs (22%) not yet enrolled in LMS (data collection lag; enrolled today)
- 2 AEs missing demo activity (may not have logged yet; follow up needed)
- 1 AE (Marcus) transferred from SDR mid-month (ramp time adjusted; benchmark accuracy reduced)

**Assumptions:**
- Ramp benchmarks from industry data (SalesForce benchmarks; 5.7-month AE average)
- Activity timestamps match calendar dates (no time-of-day granularity; assumes logging same day as activity)
- Email matching (LMS to CRM) is 95%+ accurate (verified via spot check)

**Confidence Degradation:**
- Correlation analysis limited by cohort size (23 hires) and timeline (28 days). Wait until Day 60 for statistically significant findings.
- Marcus Johnson data skewed by SDR-to-AE transition (not representative; exclude from cohort-level correlation)

### Recommended Actions

1. **URGENT:** Check in with Sarah Chen today on demo readiness (critical blocker). Offer live demo pairing with Lisa Park.
2. **URGENT:** Meet with Marcus Johnson to diagnose quota gap. Review pipeline (quality?), objection-handling confidence, deal-sizing. Consider sales coaching.
3. **THIS WEEK:** Follow up with James Rodriguez, Priya Patel, David Kim on their specific flags. All are fixable with 1–2 coaching sessions.
4. **MONITOR:** Watch Objection Handling module for correlation; likely to be mandatory by Day 8 in future cohorts.
5. **PROCESS:** Ensure all new AEs are LMS-enrolled by Day 1 (5 of 23 were delayed; implement enrollment automation).
6. **NEXT MONTH:** Re-run correlation analysis on June 1 (full Month 2 quota data available); confirm high-impact training modules.

### Sources & Citations

- Salesforce: 23 AE contacts, 218 activities, 23 opportunities pulled May 28, 2026
- Docebo LMS: 18 course completions, 5 pending enrollments
- Ramp benchmark: 5.7 months (AE) per SalesForce Benchmark Report 2024
- Quota calculations: May 2026 monthly targets (base salary + commission structure)
```

**You:** "Good. I can see Sarah and Marcus are at risk. What should I do with Sarah today?"

**Me:** "Sarah's issue is clear: she's completed all the foundational training (product, CRM, sales process) and is doing well in calls. The gap is demos—she hasn't scheduled or completed a live demo yet by Day 28, but should have 1–2 done by now. 

**Recommended interventions (pick one or combine):**
1. **Live demo shadowing** — Have her sit in on Lisa Park's top 2 demos this week (watch + observe)
2. **Role-play + feedback** — 30-min 1:1 with AE manager or sales trainer; practice 2–3 demo scenarios from your playbook
3. **Demo certification refresher** — She scored 82% on the demo cert (below peer avg 84%); suggest 20-min review + another practice round

Which sounds most doable for your team? I can also schedule a follow-up check for Friday (3 days) to see if her demo activity picks up."

**You:** "Let's do live shadowing + refresh the cert. Can you set a reminder for Friday to check progress?"

**Me:** "Done. I've flagged Sarah's account for follow-up on Friday, May 31 at 9:00 AM. I'll pull her updated activity and send you a brief status note. If she's completed her first demo by then, I'll close the alert. If not, I'll suggest next steps (escalation, more intensive coaching, etc.).

For Marcus, the quota gap is bigger and requires a different approach—likely pipeline or objection-handling confidence. Want me to run a deep dive on his activities (which objections did he miss, who are his top prospects, how does his pipeline compare to peers)?"

---

## References & Further Reading

**Ramp Benchmarking:**
- Sales Ramp-Up Statistics 2025: Benchmarks & Best Practices (SalesForce)
- How to Ramp Sales Reps Faster: Can You Cut Ramp Time in Half? (Hyperbound)
- Shortening the Curve: How to Reduce Ramp Time for New Account Executives with Technology (SalesHQ)

**Onboarding Best Practices:**
- 27+ Employee Onboarding Statistics & Trends You Must Know in 2026 (AIHR)
- Sales Onboarding Process: How to Ramp New Reps Faster and Smarter (Enboarder)
- Onboarding Reports and Dashboards (EMP Trust HR)

**Training-to-Performance Correlation:**
- Sales Enablement Metrics: The 10 Most Important Enablement KPIs to Track (SalesHood)
- 31 Sales Enablement Metrics That Actually Measure Impact (Spekit)
- Sales Readiness Guide: Prepare Sellers for Success (Seismic)

**Configuration & Customization:**
- Standard milestone templates for AE, SDR, CSM roles (included in agent repo)
- Ramp curve interpolation formulas (linear; customizable per org)
- Alert threshold defaults (10 days behind, 20% quota gap; all customizable)

**Data Integration:**
- Salesforce API documentation (Read access on Contact, User, Activity, Opportunity)
- HubSpot CRM API (crm.objects.contacts.read, crm.objects.deals.read)
- Docebo, Lessonly, WorkRamp LMS API specifications
- MindTickle and Allego training platform integrations
