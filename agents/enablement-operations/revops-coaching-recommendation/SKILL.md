---
name: revops-coaching-recommendation
description: Synthesizes structured call insights from RI-03 with rep performance
  metrics and deal context to generate personalized, deal-specific coaching recommendations
  for sales managers within 24 hours of a call. Prioritizes mid-performers per SBI
  research and auto-distributes coaching digests.
metadata:
  trigger_phrases:
  - generate coaching recommendations
  - suggest coaching for my reps
  - what coaching does this rep need
  - coaching digest
  - personalize coaching by performance
  - create rep coaching recommendations
  - coaching from call insights
  category: Enablement & Onboarding
  phase: day_1
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents:
    - RI-03 Call Analysis Agent
    mcps:
    - Salesforce MCP (if using Salesforce)
    - HubSpot MCP (if using HubSpot)
    - Slack MCP (optional, for coaching digest delivery)
    minimum_data:
    - 'Call insights from RI-03: objections, sentiment, methodology adherence, next
      steps'
    - 'Sales rep records with: email, name, manager, current win rate'
    - 'Opportunity/Deal records with: close_date, stage, amount, owner'
    - Manager-rep hierarchy (team structure)
  output_format: markdown report + optional Slack delivery
---

# Coaching Recommendation Agent (EO-03)

## Why This Agent Exists

**Who it's for (ICP):** Sales Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Manager Coaching Time Bottleneck
- **Problem:** Sales managers spend 30–60% of their time on admin tasks, have 12+ direct reports, and cannot manually prepare effective, data-driven coaching for each rep.
- **Quantified cost to the role:** $71.5k/year per 50-rep team in lost coaching labor (13 hours/week coaching + 8–12 hours/week prep at $195k loaded manager salary). Alternatively, $50k–$200k/year in platform spend attempting to automate coaching prep.
- **What teams do today:** Deploy Gong ($1,600–$2,380/user/year + $50k platform fee), Outreach, or Chorus for coaching automation; hire external coaches ($5k–$15k/month); or manually build coaching plans in spreadsheets (3–5 hours/week).
- **Why it's urgent:** Without coaching, teams lose 12 points of win rate vs. coached teams (28% higher win rate). Over 24 months at $100k ACV, 50-rep team loses $3.6M–$7.2M in revenue. Manager burnout rises; top performer turnover accelerates.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

### Pain Point 2: Personalization Gap — Coaching is One-Size-Fits-All
- **Problem:** Managers lack data on which reps to coach (SBI: 60% time should go to mid-performers), leaving the highest-ROI segment underserved.
- **Quantified cost to the role:** Reps with ≤30 min coaching/week: 43% win rate; ≥2 hours/week: 56% win rate. 13-point delta × 50 reps × 10 deals/year × $100k ACV = $650k/year lost.
- **What teams do today:** Hire external coaches ($5k–$15k/month) to build personalized coaching plans; managers build manual tracking lists (3–5 hours/week); adopt Gong + Outreach ($100k+/year) for automated prioritization.
- **Why it's urgent:** Mid-performer cohort (highest ROI) remains undercoached. Over 24 months, this drives talent loss and attrition: $600k–$1.2M in turnover costs + $3.6M in lost deals.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

### Pain Point 3: Call-to-Coaching Latency — Coaching Happens Too Late
- **Problem:** Call insights take 2–3 days to surface; coaching within 24 hours is 2.5x more effective. Manual review delays feedback delivery and kills deal momentum.
- **Quantified cost to the role:** Coaching within 24 hours: reps 2.5x more likely to improve. Latency cost on 250 calls/week (50 reps × 5 calls/week) = 500–750 improvement points lost/week, or $2.6M–$3.9M annually in lost revenue at $100k ACV.
- **What teams do today:** Deploy Gong, Outreach, or Chorus ($1,600–$2,380/user/year + $50k–$150k platform fees) for same-day coaching automation; managers still spend 15–30 min/call manually drafting and routing coaching.
- **Why it's urgent:** Latency problem compounds as teams grow. Currently 250 calls/week; in 24 months, 350 calls/week for 65 reps. Manual review becomes untenable. Coaching effectiveness decays 8–12 points of win rate. Cumulative 24-month revenue loss: $7.2M–$10.8M.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

---

## What This Agent Does

The Coaching Recommendation Agent is your real-time coaching engine. It ingests structured call insights from RI-03 (objections, sentiment, methodology gaps, next steps) along with your rep performance data and deal context, then generates targeted coaching recommendations within 24 hours of the call. It automatically tiers reps by performance and prioritizes the mid-performer cohort—the segment SBI research shows should receive 60% of coaching time but typically gets the least—and personalizes every recommendation to the deal in flight. You get a digest showing what rep needs coaching on, why, evidence from the call, and exact actions your manager should take (plus time estimates). Coaching is deal-specific, not rep-generic: instead of "improve objection handling overall," you get "on this Acme deal, prospect said budget is 3x your spend and you didn't explore their approval authority—here's what to do on the follow-up call."

---

## Getting Started (Preflight Check)

When you trigger this agent, I'll verify that the prerequisites are in place before generating coaching recommendations.

**Step 1: Upstream Dependency Verification**
- I'll check if RI-03 (Call Analysis Agent) has been deployed and has produced at least one call analysis record.
- **If RI-03 not found:** Agent cannot proceed. You need to run RI-03 first to extract call insights.
- **If RI-03 found and producing data:** Proceed to Step 2.

**Step 2: CRM Connection Check**
- I'll verify that either Salesforce MCP or HubSpot MCP is connected and authenticated.
- I'll test a read operation to ensure API access is working.
- **If connection fails:** I'll offer troubleshooting steps: re-authenticate, verify API token scope, check org permissions.
- **If successful:** Proceed to Step 3.

**Step 3: CRM Data Validation**
I'll check for required objects and fields:
- **Sales Rep records:** ≥1 rep with email, name, manager assignment ✓
- **Opportunity/Deal records:** ≥1 deal with close_date, stage, amount, owner ✓
- **RI-03 Call Insights:** ≥1 call analysis record with objections, sentiment, methodology fields ✓

**Go/No-Go decision:**
- ✓ All required data present → Proceed
- ⚠️ Rep performance data (win rate) missing → Proceed with degraded tier assignment (all reps default to "neutral" tier)
- ⚠️ Manager-rep hierarchy incomplete → Proceed with manual manager routing (coaching routed to all managers on team)
- ✗ Core fields missing (rep email, deal owner, RI-03 insights) → No-go; request data prep first

**Step 4: Define Your Coaching Scope**
Before generating recommendations, I'll ask:
- "Generate coaching for all reps, or a specific subset (e.g., reps with calls this week, specific teams)?"
- "Should I prioritize mid-performers per SBI research, or show all reps equally?"
- "Delivery preference: CRM fields, email digest, Slack, or markdown report only?"

**Preflight Report**
```
✓ RI-03 Call Analysis Agent deployed (8 call analyses available)
✓ Salesforce MCP connected and authenticated (Org: EXAMPLE_ORG_ID)
✓ Sales rep records: 47 reps with valid emails and manager assignments
✓ Opportunity records: 128 deals in pipeline with owner + close date
✓ Rep performance data: Win rate available for 46/47 reps (98%)
✓ Manager-rep hierarchy: Complete (all reps assigned to a manager)
✓ Ready to generate coaching recommendations

Scope: All reps | Mid-performer prioritization enabled | Email + CRM delivery

Next step: Analyzing 8 calls and generating personalized coaching recommendations...
```

---

## Step-by-Step Workflow

### Step 1: Ingest RI-03 Call Insights

**What I'll do:**
- Fetch all call analysis records from RI-03 output (created in last 24 hours, or user-specified date range).
- For each call, extract:
  - Call metadata (date, duration, rep, prospect, deal context)
  - Structured objections (type, severity, rep handling effectiveness)
  - Sentiment signals (overall call, rep sentiment, prospect sentiment)
  - Methodology adherence (MEDDICC/SPICED gaps, element coverage)
  - Competitors mentioned and competitive positioning by rep
  - Next steps and commitments made by rep

**Data validation:**
- Confirm extraction_confidence ≥ 0.75 (acceptable quality threshold)
- Flag low-confidence insights (0.60–0.74) for manager review; exclude <0.60 from coaching generation
- Confirm rep email matches a record in CRM (fuzzy match threshold: 0.85+)

**Output:** Clean set of 1–N call insights ready for coaching generation

---

### Step 2: Enrich with Rep Performance & Deal Context

**What I'll do:**
- For each rep in the call insights, fetch from CRM:
  - Win rate (YTD and 12-month)
  - Quota attainment (%)
  - Call count this week/month
  - Tenure/ramp date
  - Manager assignment
- For each deal referenced in the call, fetch:
  - Stage, close_date, amount, probability
  - Account industry, size, segment
  - Previous deal history with this account
- Build rep performance tiers:
  - **Top performer:** Win rate ≥40% (or >1.5 std dev above team avg)
  - **Mid performer:** Win rate 25–39% (within 0.5 std dev of team avg)
  - **Low performer:** Win rate <25% (or >1.5 std dev below team avg)

**Output:** Enriched call dataset with rep tier, deal risk assessment, and peer comparison baseline

---

### Step 3: Analyze Objection Handling & Methodology Gaps

**What I'll do:**
For each call, run three parallel analyses:

**Analysis 3a: Objection Handling Assessment**
- For each objection raised by prospect:
  - Did rep acknowledge or dismiss? (engagement score)
  - Did rep provide evidence-based rebuttal? (effectiveness score)
  - Did prospect seem satisfied or concerned after? (sentiment delta)
- Flag unhandled objections as "coaching opportunity"
- Categorize by type: Budget, Timeline, Competitor, Authority, Need, Implementation
- Compare objections handled vs. not handled; if <70% handled, flag for coaching

**Analysis 3b: Methodology Adherence Gap Detection**
- Measure MEDDICC/SPICED element coverage in call
- Identify "missing critical elements" (elements not present, high impact on deal)
- Assign severity: Critical (kills deals), High (slows deals), Medium (nice-to-have)
- Example gaps:
  - Economic Buyer not identified (critical for B2B)
  - Decision Process not clarified (high; enables timeline planning)
  - Champion not coached (high; reduces internal selling risk)

**Analysis 3c: Competitive Positioning Assessment**
- Count competitors mentioned; note prospect sentiment toward each
- Did rep counter with differentiation? (yes/no)
- Quality of counter-argument: (strong/weak/none)
- Risk assessment: Is prospect leaning toward competitor?

**Output:** Prioritized list of 1–3 coaching themes per call (objections, methodology, competition)

---

### Step 4: Generate Personalized Coaching Recommendations

**What I'll do:**
For each coaching theme, synthesize:

**Coaching Recommendation Structure:**
```
[Theme ID] [Category] [Gap Identified]
├─ Evidence from call (transcript snippet, timestamp)
├─ Severity (high/medium/low)
├─ Rep performance context (is this holding rep back?)
├─ Recommended action (specific, actionable play or resource)
├─ Success metric (how will rep know this worked?)
├─ Estimated impact (deal win probability delta, rep win rate improvement)
└─ Time estimate for manager to deliver (5–20 min)
```

**Prioritization Logic:**
1. **Severity + Deal Risk:** High-severity gap + high-risk deal (stalling, competitive pressure) = top priority
2. **Rep Performance Context:** Gap that's holding a mid-performer back from peer average = high priority (per SBI research)
3. **Time Sensitivity:** Gap with imminent next step (call scheduled in 48 hrs) = elevated priority
4. **Peer Comparison:** If rep is below peer average on this dimension, boost priority

**Rep Tier Application:**
- **Top performers:** Flag only critical gaps; assume they'll self-correct on medium gaps
- **Mid-performers:** Flag all gaps; prioritize those that move rep toward peer average
- **Low performers:** Flag all gaps, but note: "Focus on 2 highest-impact items first to avoid overwhelming rep"

**Output:** Ranked coaching recommendations (typically 2–3 per rep per call), each with evidence, action, and impact estimate

---

### Step 5: Manager-Specific Coaching Digest

**What I'll do:**
Generate a digest tailored to each manager:

**Digest Contents:**
- **Your Coaching Summary:** "3 reps on your team had calls this week. 5 coaching opportunities identified. Mid-performer Marcus has 2 high-priority items; recommend 50-minute investment."
- **Rep-by-Rep Breakdown:**
  - Rep name + performance tier + win rate vs. peer avg
  - Deal name + stage + close_date + amount
  - Coaching recommendation(s) + recommended actions
  - Time estimate to deliver coaching
- **Strength Callout:** "Marcus also showed strong discovery skills (8 questions, good talk-listen balance). Leverage this strength with more confident objection handling."
- **Manager Action Items (Ranked by ROI):**
  - [ ] Schedule 15-min 1-1 with Marcus (coaching on 2 MEDDICC gaps) — 15 min
  - [ ] Share battle card: "How to Identify Economic Buyer in Mid-Market" — 5 min
  - [ ] Role-play Budget Objection + ROI rebuttal with Marcus — 20 min
  - Estimated total: 40 min to unlock 3–5 point win rate improvement for Marcus

**Delivery Options:**
- **Email Digest:** Manager-friendly summary email with links to resources
- **Slack Coaching Alert:** Async Slack message with coaching summary + link to full report
- **CRM Custom Object:** Write coaching_recommendation__c records to Salesforce/HubSpot for persistent tracking
- **Markdown Report:** Full narrative report for manager review

---

### Step 6: Generate Output Report

**Markdown Report with Sections:**

**Summary**
- Total calls analyzed [date range]
- Reps with coaching needs
- Coaching opportunities identified (by category: Objection, Methodology, Competition)
- Avg coaching impact estimate (e.g., "If manager coaches all recommendations, team win rate could improve 2–4 points in 30 days")

**Details**
- By Rep (sorted by tier, then by coaching priority):
  - Rep name, current win rate, tier, peer average
  - Deal context (account, stage, close_date, amount)
  - Call data (date, duration, rep sentiment, prospect sentiment)
  - Coaching themes (1–3 per rep), each with:
    - Category (Objection/Methodology/Competition)
    - Gap description + evidence from call
    - Recommended action + resource link
    - Success metric + estimated impact

**Rep Strengths Highlighted**
- What each rep did well in recent calls (e.g., "Strong discovery," "Positive rapport," "Handled competitor mention with confidence")
- How to leverage strengths in coaching (e.g., "Use discovery skill to probe deeper into Budget objection")

**Manager Action Items**
- Ranked by ROI: Which 1-on-1s and coaching actions will unlock the most win rate improvement
- Time estimates for each action
- Resource links for sales playbooks, battle cards, roleplay scenarios

**Data Quality & Limitations**
- RI-03 extraction confidence (if any calls <0.75, noted)
- Rep performance data completeness (if win rate missing for some reps, noted)
- Methodology assumptions (MEDDICC assumed; if customer uses SPICED, note)
- Known limitations (can't assess deal-specific pricing objections without pricing data, etc.)
- Impact estimate confidence (e.g., "Estimated impact is based on SBI research showing 2–4 point win rate improvement with targeted coaching; your results may vary based on rep coaching receptiveness and execution")

**Recommended Next Steps**
1. Review coaching digest for mid-performers this week
2. Conduct 1-on-1 conversations (1 per rep, 15–20 min each)
3. Share relevant battle cards or playbooks
4. Role-play or practice key scenarios (20 min per rep for highest-impact gaps)
5. Schedule follow-up calls with prospects per coaching plan
6. Monitor: Did rep close the deal or move it forward? Track rep win rate improvement weekly

**Sources & Citations**
- RI-03 call analyses (pulled [date])
- Salesforce/HubSpot rep and deal data (pulled [date])
- SBI Micro-Coaching Research, April 2024
- Methodology definitions (MEDDICC; or customer-provided if specified)
- Competitive intelligence (if deal context sourced from Gong competitor mentions)

---

## Configuration Options

Before generating coaching, customize these parameters:

**Coaching Scope:**
- "Should I generate coaching for all reps or filter by team, tenure, performance tier?" (Default: All reps)
- "Should I only include calls from the past 7 days, or look further back?" (Default: 7 days)
- "Should I prioritize mid-performers (SBI approach) or weight all tiers equally?" (Default: Mid-performer prioritization)

**Objection Handling Thresholds:**
- "What % of raised objections should be handled before flagging for coaching?" (Default: 70%; flag if <70% handled)
- "Should I flag unhandled objections as 'critical' or just note them?" (Default: Flag if high-severity unhandled)

**Methodology Coverage:**
- "What sales methodology do you use?" (MEDDICC, SPICED, Sandler, or custom?) (Default: MEDDICC)
- "What % of methodology elements must be present to avoid a coaching flag?" (Default: 80%; flag if <80% adherence)

**Coaching Impact Thresholds:**
- "Show me all coaching recommendations or only those with >2 point win rate impact?" (Default: All recommendations)
- "Should I highlight rep strengths or focus only on gaps?" (Default: Highlight both)

**Delivery Preference:**
- "How should I deliver coaching digests?" (CRM fields / Email / Slack / Markdown report only) (Default: Markdown report)
- "Should I automatically post coaching alerts to Slack or require manager review first?" (Default: Require review)

---

## Error Handling

**If RI-03 agent not found or no call insights available:**
- **Action:** Cannot proceed. Coaching requires call analysis data from RI-03.
- **User instruction:** Run RI-03 first (trigger: "analyze calls"). Once RI-03 produces call insights, re-run EO-03.
- **Workaround:** If RI-03 is not yet deployed, manually input call summaries (objection type, severity, methodology adherence score, sentiment) and agent can generate coaching (lower confidence, but functional).

**If CRM connection fails:**
- **Action:** Cannot retrieve rep performance data or write coaching records to CRM.
- **User instruction:** Reconnect your Salesforce/HubSpot MCP. Verify API token scope includes: READ on Opportunity/Deal, Contact, User objects; WRITE on custom fields.
- **Workaround:** Deliver coaching recommendations as markdown report only (no CRM integration) until connection is restored.

**If rep performance data is missing (win rate, quota, etc.):**
- **Action:** Proceed with "neutral" performance tier for affected reps. Coaching still generated but not optimized by tier.
- **User instruction:** Populate rep performance data in CRM or data warehouse (YTD win rate, quota attainment, calls this month).
- **Impact:** Coaching remains high-quality for mid-performers; just not tier-prioritized. Manager should apply judgment to focus on highest-impact reps.

**If RI-03 extraction confidence is low (<0.75):**
- **Action:** Flag call for manager review. Include coaching with caveat: "Low confidence in AI extraction; manually validate objection classification."
- **User instruction:** Review flagged call in Gong/Fathom directly; confirm objections and sentiment before coaching implementation.
- **Fallback:** Offer generic coaching ("Review this call for objection handling opportunities") until confidence improves.

**If manager-rep hierarchy is incomplete:**
- **Action:** Route all coaching to team manager email (broadcast mode) instead of individual manager inboxes.
- **User instruction:** Confirm manager-rep hierarchy in Salesforce/HubSpot User object (manager_id field). Verify each rep has a manager assigned.
- **Workaround:** Send coaching digest to primary manager email with note: "[Rep name] coaching—please forward to [rep] manager if different from team manager."

**If deal context is missing (opportunity not linked to call):**
- **Action:** Generate coaching with rep-level context only (no deal-specific details).
- **User instruction:** Ensure sales reps link calls to opportunities in Gong/Fathom before RI-03 processes them. This enables deal-specific coaching.
- **Impact:** Coaching is "generic rep coaching" vs. "deal-specific coaching." Still valuable but less contextual.

---

## Configuration Settings

**Field Name Mapping (Customize for Your CRM):**
```
Salesforce:
  rep_email_field = "Contact.Email"
  manager_field = "Contact.Manager_ID__c"
  deal_owner_field = "Opportunity.Owner_ID"
  close_date_field = "Opportunity.CloseDate"
  custom_coaching_object = "Coaching_Recommendation__c"

HubSpot:
  rep_email_field = "hs_email"
  manager_field = "hubspotownerId"
  deal_owner_field = "hs_deal_owner"
  close_date_field = "closedate"
  custom_coaching_object = "coaching_recommendations"
```

**Win Rate Tier Thresholds (Adjust Based on Team Baseline):**
```
top_performer_threshold = 40%  (or >1.5 std dev above team avg)
mid_performer_range = 25–39%   (or within 0.5 std dev of team avg)
low_performer_threshold = <25%  (or >1.5 std dev below team avg)
```

**Objection Handling Effectiveness Weights:**
```
handled_with_rebuttal_evidence = 1.0 (excellent)
handled_with_acknowledgment = 0.6 (neutral)
dismissed_or_avoided = 0.2 (poor)
unhandled = 0.0 (missed opportunity)
```

---

## Worked Example

**Scenario:** Sales manager Susan has 12 direct reports. Last week, 4 reps had calls processed by RI-03. You trigger EO-03 with default settings (all reps, mid-performer prioritization, markdown report + email delivery).

**RI-03 Input (4 calls processed):**
- Marcus Johnson: AcmeCorp demo call, 1 unhandled Budget objection, MEDDICC gap (Economic Buyer missing)
- Priya Patel: TechStart technical evaluation call, all objections handled well, 85% MEDDICC adherence
- David Chen: InnovateCo discovery call, 2 competitors mentioned, weak differentiation response
- Keisha Williams: RetailMax negotiation call (rep in rare deal stage), multiple unhandled objections, low prospect sentiment

**Agent Workflow:**
1. Fetch RI-03 call data for 4 calls + enrich with rep performance (Marcus: 31% WR, mid-tier; Priya: 42% WR, top-tier; David: 25% WR, mid-tier; Keisha: 18% WR, low-tier)
2. Analyze each call for objection handling, methodology gaps, competitive positioning
3. Generate coaching recommendations:
   - Marcus: High priority (2 gaps, mid-performer, high-value deal). Coaching impact: +3–5 points
   - Priya: Low priority (strong call, top-performer, only 1 minor gap). Coaching impact: +1 point
   - David: Medium priority (weak competitor positioning, mid-performer). Coaching impact: +2–3 points
   - Keisha: High priority (multiple unhandled objections, low-performer, deal at risk). Coaching impact: +2–4 points, but also "deal risk" alert
4. Generate manager digest (email + markdown report):

**Email Digest:**
```
Subject: Sales Coaching Digest — Week of Apr 13 | 3 reps need coaching | 40 min manager investment

Hi Susan,

Your team had 4 calls this week. I've identified coaching opportunities for 3 reps. 
Recommended manager investment: 40 minutes total over next 2 days.

HIGH PRIORITY (Estimated impact: +3–5 points win rate)
═══════════════════════════════════════════════════════════
👤 Marcus Johnson | Mid-performer (31% WR, vs. peer avg 33%)
📞 Call: AcmeCorp Demo (Apr 13)
💼 Deal: $50k opportunity, closing Apr 30, Demo stage
🎯 Coaching: 2 high-impact gaps
   • Budget Objection: Unhandled; prospect still concerned
     → Action: Prepare ROI calculator; role-play rebuttal (20 min)
   • Economic Buyer not identified
     → Action: Share "Economic Buyer ID" battle card; 1-on-1 (15 min)
📊 Manager time: 50 min | Estimated deal impact: +10% win probability

MEDIUM PRIORITY (Estimated impact: +2–3 points win rate)
═══════════════════════════════════════════════════════════
👤 David Chen | Mid-performer (25% WR, vs. peer avg 33%)
📞 Call: InnovateCo Discovery (Apr 12)
💼 Deal: $75k opportunity, closing May 15, Qualification stage
🎯 Coaching: Weak competitive positioning
   • Competitors mentioned (HubSpot, Salesforce); rep didn't counter with differentiation
     → Action: Share competitive battle card; prep talking points (10 min)
📊 Manager time: 15 min | Estimated deal impact: +8% win probability

LOW PRIORITY (Monitor, but top-performer performing well)
═══════════════════════════════════════════════════════════
👤 Priya Patel | Top-performer (42% WR, vs. peer avg 33%)
📞 Call: TechStart Technical Evaluation (Apr 13)
💼 Deal: $120k opportunity, closing May 1, Evaluation stage
🎯 Coaching: Minor gap (nice-to-have)
   • All objections handled; MEDDICC adherence 85% (strong)
📊 No coaching needed. Priya is on track.

🚨 DEAL AT RISK — Escalation Recommended
═══════════════════════════════════════════════════════════
👤 Keisha Williams | Low-performer (18% WR, vs. peer avg 33%)
📞 Call: RetailMax Negotiation (Apr 12)
💼 Deal: $200k opportunity, closing Apr 28 (5 days away), Negotiation stage
⚠️  Multiple unhandled objections; prospect sentiment: cautious/negative
🎯 Recommended action: Manager should join next call or have urgent rep coaching session
📊 Deal is stalling. Recommend escalation to sales leadership.

NEXT STEPS:
1. Review full coaching report (linked below)
2. Prioritize Marcus (high ROI) and Keisha (deal risk) for coaching today
3. Schedule 1-on-1s and role-plays using attached action items
4. Track: Did rep close deal or move it forward? We'll measure impact next week.

Full Report: [link to markdown report]
Battle Cards & Resources: [links to playbooks, ROI calculator, etc.]

Questions? Let me know.
—Coach
```

**Markdown Report (Summary Section):**
```
## Coaching Summary — Week of Apr 13, 2026

**Request:** Generate coaching recommendations for all reps with calls this week
**Timestamp:** 2026-04-13T16:45:00Z
**Report Generated By:** EO-03 Coaching Recommendation Agent

### Summary
4 calls analyzed across 4 reps. 3 reps have coaching opportunities; 1 rep (Priya) performing excellently.
- High-priority coaching: Marcus (2 gaps, mid-performer, high-value deal); Keisha (deal at risk)
- Medium-priority coaching: David (competitive positioning gap)
- Coaching impact potential: Team could improve 2–4 points win rate in next 30 days with focused coaching
- Manager investment required: 50 min (Marcus) + 15 min (David) + escalation (Keisha) = ~75 min recommended

### Details by Rep

**Rep: Marcus Johnson | Win Rate: 31% (vs. peer: 33%)**

*Deal Context:* AcmeCorp, $50k, Demo stage, closing Apr 30

*Call Summary:* 24-min demo call. Prospect raised Budget concern (3x current tool spend) and Timeline concern (can't implement until Q3). Marcus handled Budget with acknowledgment but no ROI rebuttal. Timeline objection was unhandled—prospect stated Q3 only; Marcus accepted without negotiation. Overall sentiment: Cautiously positive (0.72). MEDDICC adherence: 67% (gaps in Economic Buyer, Decision Process, Champion Coach).

*Coaching Theme 1: Objection Handling — Budget*
- **Category:** Objection Handling
- **Gap:** Budget objection raised (high severity); rep acknowledged but didn't provide compelling ROI rebuttal
- **Evidence:** Transcript [timestamp 450s]: "Prospect: 'That's 3x our current tool spend.' Rep: 'Let's talk about ROI.' [No follow-up ROI calculation or comparison]"
- **Severity:** High (Budget is top objection blocker)
- **Recommended Action:** Prepare ROI spreadsheet showing TCO comparison vs. current tool + competitor options. Use on next call. [Resource: Internal ROI Calculator](link)
- **Success Metric:** Prospect agrees to 30-min follow-up specifically to discuss ROI. Budget objection moves from "neutral" to "addressed."
- **Estimated Impact:** Win probability +3–5 points
- **Manager Coaching Time:** Role-play rebuttal + review calculator (20 min)

*Coaching Theme 2: Qualification Methodology — Economic Buyer*
- **Category:** Methodology Adherence (MEDDICC)
- **Gap:** Economic Buyer not identified. Rep talked to end-user (Jane Smith, Product Manager) but never asked who approves budget or has final sign-off authority.
- **Evidence:** Call transcript shows 0 questions about approval authority. MEDDICC.Economic_Buyer = missing.
- **Severity:** Critical (Economic Buyer is MEDDICC foundation; without it, deal can stall at executive review)
- **Recommended Action:** Before next call, ask Jane: "Who else needs to approve this from your side?" Then schedule a call with the Economic Buyer (CFO or VP Finance). Share "Economic Buyer ID" battle card with Marcus. [Resource: Battle Card](link)
- **Success Metric:** Marcus identifies Economic Buyer and schedules meeting within 5 days
- **Estimated Impact:** Qualification becomes complete; win probability +5–8 points; reduces deal-stall risk
- **Manager Coaching Time:** 1-on-1 conversation + share resource (15 min)

*Rep Strengths Identified:*
- Discovery Depth: Marcus asked 8 discovery questions; prospect talked 64% of call (ideal for discovery phase). Strong active listening.
- Positive Demeanor: Rep sentiment score 0.85; remained professional and upbeat despite objections.
- Next Steps Accountability: Marcus committed to send ROI spreadsheet by Apr 15; strong follow-through pattern.

*Manager Actions (Ranked by ROI):*
1. [ ] Schedule 15-min 1-on-1 with Marcus within 24 hours — discuss 2 gaps while call is fresh (15 min)
2. [ ] Share "Economic Buyer Identification" battle card — concrete playbook for rep (5 min)
3. [ ] Role-play Budget Objection + ROI rebuttal — practice confident positioning (20 min)
4. [ ] Approve Marcus to reach out to Economic Buyer; set 5-day deadline (5 min async)
Total manager investment: 45 min | Estimated return: +4 point win probability for this deal, +2–3 point win rate improvement over next 30 days

---

[Similar detailed breakdown for David Chen and Keisha Williams...]
```

---

## What to Run Next

After coaching recommendations are generated and delivered:

1. **Manager executes coaching actions** (1-on-1s, role-plays, resource sharing) — typically 2–5 days

2. **Track rep execution:** Monitor if rep takes recommended action (calls scheduled with Economic Buyer, ROI spreadsheet sent, etc.) within 5–7 days

3. **Measure outcome:** Did coaching improve deal outcome?
   - Did rep close the deal or move stage?
   - Did win rate improve in next 30 days?
   - Did rep improve MEDDICC adherence in subsequent calls?

4. **Loop back:** Re-run EO-03 next week to see if coaching had impact and to surface new opportunities from this week's calls

5. **Optional: Enrich with additional data:**
   - If RI-04 (Rep Feedback Loop) agent is available, use it to gather rep feedback on coaching quality and receptiveness
   - If RI-05 (Win/Loss Analysis) agent is available, analyze which coaching themes correlated with wins vs. losses

---

## References & Further Reading

**SBI Sales Coaching Research:**
- [SBI Micro-Coaching Insights](https://salesbenchmarkindex.com/insights/improve-your-teams-sales-performance-through-micro-coaching/)
- Key insight: 60% of coaching time should go to mid-performers (highest ROI segment), but they typically receive the least coaching

**Competitive Coaching Platforms (for comparison):**
- Gong Sales Coaching: $1,600–$2,380/user/year + $50k platform fee
- Outreach KAIA Coaching: $146–$238/user/month
- HubSpot Conversation Intelligence (native to Sales Hub Enterprise)

**Sales Methodology References:**
- MEDDICC: Metrics, Economic Buyer, Decision Criteria, Decision Process, Identified Champion, Champion Coach (use this framework as default if customer doesn't specify)
- SPICED: Situation, Problem, Implication, Consequences, Economic Impact, Decision
- Sandler: Buyer pain discovery, credibility, budget exploration, decision process

**Battle Cards & Sales Playbooks (Sample Structure):**
- Economic Buyer ID: "How to identify and engage the person with budget authority in mid-market deals"
- ROI Calculator: Spreadsheet template showing TCO comparison vs. current tool + competitor options
- Competitive Positioning: Talking points for positioning your solution vs. Salesforce, HubSpot, competitors
- Objection Handling: Rebuttal frameworks for common objections (Budget, Timeline, Competitor, Authority)
