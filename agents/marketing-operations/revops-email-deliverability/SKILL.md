---
name: revops-email-deliverability
description: Monitors sending domain health, bounce rates, spam complaints, and inbox
  placement across email platforms and ISPs. Aggregates data from Mailchimp, HubSpot,
  Klaviyo, and free tools (Google Postmaster, MXToolbox) into a unified real-time
  scorecard with alerts and remediation playbooks.
metadata:
  trigger_phrases:
  - check email deliverability
  - monitor sending domain health
  - diagnose bounce and complaint rates
  - validate email authentication
  - check domain blacklist status
  - review inbox placement rates
  - audit email sender reputation
  - debug email delivery issues
  - assess domain reputation
  category: Marketing Operations
  phase: day_1
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents: []
    mcps:
    - Mailchimp MCP (preferred)
    - HubSpot MCP (preferred)
    - Klaviyo MCP (preferred)
    - SendGrid MCP (optional)
    - Constant Contact MCP (optional)
    minimum_data:
    - 'Email platform OAuth connection (at least one of: Mailchimp, HubSpot, Klaviyo,
      SendGrid)'
    - Verified sending domain with SPF/DKIM/DMARC records
    - Email volume >100/day to establish baseline metrics
  output_format: JSON scorecard + Markdown report + optional Slack alert
---

# Email Deliverability Agent

## Why This Agent Exists

**Who it's for:** Marketing Operations Manager or Email Marketing Manager at B2B SaaS companies (100–500 employees, North America), sending 2,000–50,000 emails/day.

**The problem it solves:**

Silent deliverability collapse is an invisible revenue drain. For a B2B SaaS team sending 2,000 emails per day, a 40% drop in Gmail inbox placement = $240,000+ in lost pipeline per month. Yet most teams don't realize their emails are landing in spam until campaign performance craters—by then, 2–4 weeks of damage has already occurred.

B2B SaaS marketing ops teams are drowning in scattered tools: Gmail Postmaster Tools (Gmail-only), MXToolbox (DNS-focused), email platform dashboards (incomplete metrics), ISP feedback loops (delayed 24–48h), and reputation tools (expensive: $59–$399/month). Without a unified, real-time view, mean-time-to-detect (MTTD) for deliverability issues stretches from minutes to days.

**What this agent delivers:**
- **Unified scorecard** with domain reputation, bounce rates, complaint rates, authentication status, blacklist status, and per-ISP inbox placement—all in one place
- **Composite health score** (0–100) that weighs complaint severity (35%), bounce health (25%), authentication alignment (25%), and blacklist status (15%)
- **Real-time alerts** when thresholds breach (complaint >0.1%, reputation <50, blacklist listing, authentication <95%)
- **Root-cause guidance** via remediation playbooks (e.g., "Complaint spike → check content for spam triggers")
- **Works on day 1** with OAuth-connected email platforms; no 30-day historical data required

---

## What This Agent Does

The Email Deliverability Agent is your domain's health monitor and incident responder. It pulls data from multiple sources in parallel—email platform APIs (bounce, complaint, reputation metrics), DNS records (SPF/DKIM/DMARC validation), blacklist registries, and optional ISP tools (Google Postmaster, MXToolbox)—then aggregates everything into a single, unified scorecard.

You get a composite health score (0–100) that updates every 4 hours, per-ISP inbox placement rates (Gmail, Outlook, Yahoo), a detailed breakdown of authentication alignment, and a clear alert hierarchy (CRITICAL, HIGH, MEDIUM, LOW). When metrics degrade, the agent doesn't just flag the problem—it provides a step-by-step remediation playbook to fix it fast.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your email platform connection, test DNS resolution, confirm required data exists, and identify optional data sources.

**Step 1: Email Platform MCP Verification**
- I'll check if Mailchimp, HubSpot, Klaviyo, SendGrid, or Constant Contact MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: manual domain input for DNS checks, or help you reconnect the MCP.
- **If successful:** Proceed to Step 2.

**Step 2: DNS Validation**
I'll verify your sending domain is accessible and has SPF/DKIM/DMARC records configured:
- Test DNS resolution for the domain
- Confirm SPF record exists and has valid syntax
- Confirm DKIM record(s) exist
- Confirm DMARC policy is set (p=none, p=quarantine, or p=reject)

**Go/No-Go decision:**
- ✓ Email platform + domain verified → Proceed
- ⚠️ One optional source unavailable (Postmaster, MXToolbox) → Proceed with reduced visibility; flag limitation
- ✗ Email platform unreachable OR domain has no SPF/DKIM/DMARC → No-go; ask you to configure domain first

**Step 3: Data Quality Assessment**
I'll calculate:
- Email platform connectivity and API health (is data flowing?)
- Estimated email volume to each ISP (Gmail, Outlook, Yahoo)
- Whether Postmaster Tools or MXToolbox are enabled (optional but recommended)
- Data freshness (when were metrics last updated?)

**Step 4: Define Your Monitoring Scope**
Before analyzing, I'll ask:
- "Which sending domain would you like me to monitor?" (if your account has multiple)
- "Would you like me to enable blacklist monitoring via MXToolbox?" (optional; free tier ~1,000 queries/month)
- "Would you like me to set up Google Postmaster Tools integration?" (free; requires domain verification + 100+ daily emails to Gmail)

**Preflight Report**
I'll summarize:
```
✓ Mailchimp MCP connected
✓ Domain: marketing.example.com with SPF, DKIM, DMARC records
✓ Estimated email volume: 5,000/day (1,200 Gmail, 800 Outlook, 600 Yahoo, 2,400 other)
⚠️ Google Postmaster Tools: Not configured (recommended for full Gmail visibility)
? MXToolbox: Not enabled (optional; enable for enhanced blacklist monitoring)
✓ Ready to proceed

Monitoring: marketing.example.com | Email Platform: Mailchimp

Next step: Fetching metrics and validating DNS records...
```

---

## Step-by-Step Workflow

### Step 1: Parallel Data Collection

I'll fetch data from multiple sources simultaneously (no blocking):

**Email Platform Metrics (Spoke 1) — Timeout: 10s**
- Bounce rate (hard + soft)
- Spam complaint rate
- Domain reputation score
- Authentication pass rate (SPF+DKIM+DMARC aligned)
- Inbox placement % (if available from platform)
- Unsubscribe rate (for engagement assessment)

**DNS Records (Spoke 2) — Timeout: 5s**
- SPF policy and validity
- DKIM public key and alignment
- DMARC policy and alignment
- Timestamp of last check

**Google Postmaster Tools (Spoke 3) — Timeout: 10s (if enabled)**
- Gmail inbox placement %
- Gmail spam folder %
- Gmail feedback loop complaints (24h)

**Blacklist & Reputation (Spoke 4) — Timeout: 5s (if MXToolbox enabled)**
- Active blacklist listings (Spamhaus, Barracuda, etc.)
- Sender score (if available)
- IP reputation status

**ISP Feedback (Spoke 5) — Timeout: 8s (Phase 2 feature)**
- Outlook/Yahoo complaint counts
- Per-ISP delivery rates
- ISP-specific warnings

**Graceful Degradation:** If one spoke times out or fails, results continue with available data. I'll flag what's missing.

---

### Step 2: Normalize & Validate Metrics

All metrics are converted to standard scales:
- Percentages: 0–100%
- Reputation scores: 0–100 scale
- Bounce/complaint rates: % format
- Authentication: binary (pass/fail) + % pass rate
- Blacklist: binary (listed/clear)

Invalid data is rejected: bounce rate >100% = flagged as data error; negative complaint % = excluded.

---

### Step 3: Calculate Composite Health Score

I calculate a unified deliverability health score (0–100) using a weighted formula:

```
Composite Score = (
  (Bounce Score × 0.25) +
  (Complaint Score × 0.35) +
  (Authentication Score × 0.25) +
  (Blacklist Score × 0.15)
)
```

**Bounce Score (0–100):**
- Hard bounce >2.0% = 0 (critical failure)
- Hard bounce 1.0–2.0% = declining linearly to 0
- Hard bounce 0.5–1.0% = 80–100 range
- Hard bounce ≤0.5% = 100 (healthy)

**Complaint Score (0–100):**
- Complaint >0.5% = 0 (ISP throttling)
- Complaint 0.3–0.5% = 50 (warning zone)
- Complaint 0.1–0.3% = 75 (elevated)
- Complaint ≤0.1% = 100 (healthy)

**Authentication Score (0–100):**
- SPF+DKIM+DMARC pass rate ≥98% = 100
- Pass rate 95–98% = 85
- Pass rate 90–95% = 70
- Pass rate <90% = 50 (Gmail/Yahoo non-compliance)

**Blacklist Score (0–100):**
- Listed on any blacklist = 10 (critical; recovery 6–12 weeks)
- Provider warning flags = 50
- Clear = 100

**Interpretation:**
| Score | Status | Action |
|-------|--------|--------|
| 90–100 | Excellent | Maintain current practices |
| 80–89 | Good | Monitor; minor issues emerging |
| 70–79 | Fair | Investigate & remediate |
| 50–69 | Poor | Immediate action required |
| <50 | Critical | Escalate; pause non-critical sends |

---

### Step 4: Detect Anomalies & Trending

I calculate 7-day and 30-day trends to identify velocity:

```
Trend velocity = (score_today - score_7_days_ago) / 7 days
```

**Trend Signals:**
- DEGRADING RAPIDLY ⬇: Velocity < -2 points/day (red flag)
- Declining ↓: Velocity < 0 (monitor)
- Improving ↑: Velocity > 0 (positive)
- IMPROVING RAPIDLY ⬆: Velocity > 2 points/day (green flag)
- Stable →: No change

Anomalies detected:
- Complaint spike: Increase >0.05% in 24h
- Bounce trend: Hard bounce increasing >0.1% daily for 3 consecutive days
- Authentication failure: Pass rate <98%
- Reputation drop: Score decrease >15 points in 24h

---

### Step 5: Classify & Generate Alerts

I classify all issues by severity and generate alert payloads:

**CRITICAL** (Immediate escalation; pause sends)
- Blacklist listing (any active listing)
- Domain reputation <50
- Complaint rate >0.3% in 24h
- Authentication pass rate <95%
- Hard bounce rate >2%

**HIGH** (Address within business hours)
- Complaint rate 0.1–0.3%
- Domain reputation 50–70
- Hard bounce rate 1.0–2.0%
- Authentication pass rate 95–98%

**MEDIUM** (Address within 24–48 hours)
- Hard bounce rate 0.5–1.0%
- Engagement decline (unsubscribe >0.5%)
- DNS/auth partial failures

**LOW** (Informational)
- Authentication improved
- Reputation improved
- Blacklist delisted

**Alert Deduplication:** Same alert not sent twice within 4 hours (unless severity increases).

---

### Step 6: Generate Remediation Playbooks

For each alert, I provide a step-by-step remediation playbook:

**Example: Complaint Rate Spike**
```
Playbook Step 1 (IMMEDIATE, ~15 min)
Title: Investigate Content Triggers
Action: Review email content from past 3 days for spam triggers:
  - Excessive links (>10 links)
  - ALL CAPS text
  - Misleading subject lines
  - Unverified sender info
  - Suspicious attachments
Expected Outcome: Identify content or list quality issue
Next Step: If content issue found, pause similar campaigns

Playbook Step 2 (HIGH, ~30 min)
Title: Check List Quality
Action: Review signup flow and recent list imports
  - Are new signups validating email addresses?
  - Did you import a purchased list?
  - Are there obvious invalid emails (typos, freemail)?
Expected Outcome: Identify invalid email sources
Next Step: Remove invalid emails; improve signup validation

Playbook Step 3 (HIGH, ~10 min)
Title: Monitor ISP Feedback Next 48h
Action: Check Google Postmaster Tools daily for complaint reasons
Expected Outcome: Identify whether issue is content or domain reputation
Next Step: If complaints persist, escalate to email infra team
```

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

**Thresholds:**
- "What's your acceptable complaint rate threshold?" (Default: 0.1% warning, 0.3% critical)
- "What's your acceptable hard bounce threshold?" (Default: 0.5% acceptable, 1.0% warning, 2.0% critical)
- "What's your authentication alignment requirement?" (Default: 98% SPF+DKIM+DMARC)

**Data Sources:**
- "Enable MXToolbox integration for blacklist monitoring?" (Default: No; enables if you provide API key)
- "Enable Google Postmaster Tools?" (Default: No; requires domain TXT verification)
- "Which email platforms should I monitor?" (Default: All connected MCPs)

**Alerting:**
- "Send Slack alerts for CRITICAL issues only?" (Default: Yes)
- "Send daily email digest?" (Default: Yes, 9am)
- "Alert frequency cap?" (Default: 4 hours minimum between same alert)

**Scoring Weights:**
- "Custom component weights?" (Default: Complaint 35%, Bounce 25%, Auth 25%, Blacklist 15%)

---

## Error Handling

**If email platform MCP connection fails:**
- Suggest: Reconnect via Claude Code settings; provide MCP troubleshooting steps
- Workaround: Offer to analyze DNS records only (limited but useful)
- Next step: Ask you to reconnect, then retry

**If DNS records are missing/invalid:**
- Flag which records are missing (SPF? DKIM? DMARC?)
- Explain impact: Missing DMARC = can't assess alignment; missing SPF/DKIM = authentication failures likely
- Recommend: Contact DNS admin or email platform support to configure records

**If email volume is too low (<100/day):**
- ⚠️ Warn: Metrics may be unreliable or sparse
- Proceed anyway: Some metrics (bounce, complaint) may take 24–48h to populate
- Note: ISP-specific data (Gmail Postmaster) requires 100+ daily emails to appear

**If data is stale (>24 hours old):**
- Flag the staleness: "Last update: 48 hours ago"
- Explain impact: Trends may not reflect current reputation status
- Recommend: Reconnect MCP or request manual data refresh

**If blacklist listing detected:**
- 🚨 CRITICAL escalation: Provide delisting instructions (usually: go to Spamhaus/Barracuda website, submit delisting request)
- Timeline: Delisting takes 6–12 weeks depending on severity
- Recommend: Contact email infra immediately; begin investigation into root cause (low engagement? complaint spike? IP issue?)

**Graceful degradation for missing optional data:**
- Postmaster Tools unavailable → Note that Gmail-specific placement data unavailable; use email platform metrics as proxy
- MXToolbox unavailable → Can't monitor blacklist status; recommend enabling later
- ISP feedback loops unavailable → Note that complaint counts are from email platform, not ISP, so data may lag 24–48h

---

## What to Run Next

After reviewing your Email Deliverability scorecard:

1. **If alerts are present:** Follow the remediation playbook step-by-step. Most issues (complaint spikes, bounce trends, auth failures) are actionable within 15–60 minutes.

2. **If domain reputation is declining:** Consider running alongside a list quality audit (DQH agent) to identify invalid/low-engagement emails.

3. **If authentication scores are low:** Work with your email platform support or DNS admin to fix SPF/DKIM/DMARC alignment (usually 24–48h fix).

4. **Set up recurring monitoring:** Schedule this agent to run weekly (or daily if you're in remediation mode). I'll track trends and alert you to degradation before it becomes critical.

---

## Example: End-to-End Session

**You:** "Check our email deliverability. Our bounce rate has been weird lately."

**Me (Preflight):**
```
✓ HubSpot MCP connected
✓ Domain: sending.example.com with SPF, DKIM, DMARC
✓ Estimated volume: 8,000/day
✓ Google Postmaster Tools: Enabled (Gmail data available)
? MXToolbox: Not enabled (I can enable it with your API key)
✓ Ready to proceed

Analyzing your domain...
```

**Me (Analysis):**
```
✓ Fetched HubSpot metrics (bounce, complaint, reputation)
✓ Validated DNS records (SPF valid, DKIM valid, DMARC partial)
✓ Queried Google Postmaster Tools (Gmail delivery data)
✓ Calculated composite scores and trends

Generating scorecard...
```

**Report (Markdown Excerpt):**
```
## Email Deliverability Scorecard: sending.example.com

**Overall Health: 68/100 (Poor)**
Trend: Declining ↓ (-12 points in past 7 days)

### Component Scores:
- Bounce Score: 75 (Hard bounce 0.8%)
- Complaint Score: 55 (Complaint rate 0.18%)
- Authentication Score: 85 (SPF+DKIM aligned, DMARC misaligned)
- Blacklist Score: 100 (Clear)

### Alerts:
🔴 HIGH: Complaint Rate Elevated (0.18% vs. 0.1% threshold)
   Root Cause: Review email content from past 3 days
   Timeline: Address within 24h

🟡 MEDIUM: DMARC Alignment Failure
   Root Cause: DKIM subdomain mismatch
   Timeline: Address within 48h

### Remediation Playbook:
Step 1 (IMMEDIATE): Review content from recent campaigns for spam triggers
Step 2 (HIGH): Contact HubSpot support to verify DKIM signing alignment
Step 3 (HIGH): Monitor Postmaster Tools daily for next 48h

### Key Metrics:
Gmail Inbox Placement: 93%
Outlook Inbox Placement: 74%
Hard Bounce: 0.8% (acceptable)
Soft Bounce: 2.1% (normal)
Unsubscribe: 0.4% (healthy)
```

**Me (Next Steps):**
"Your complaint rate spiked to 0.18%. First, review your email content from the past 3 days—look for spam triggers like too many links, all-caps text, or misleading subject lines. Second, fix your DMARC alignment with HubSpot support (should take ~30 min). Third, check Postmaster Tools daily for the next 48h. If complaint rate doesn't drop below 0.1%, we may need to audit your list quality or check IP reputation. Want me to set up weekly monitoring so you catch these issues earlier?"

**You:** "Yes, weekly. We can connect MXToolbox through the secure integration settings."

**Me:** "Great. I've enabled blacklist monitoring. I'll run every Monday at 9am, and alert you immediately if anything goes CRITICAL. Check your email for the weekly digest."

---

## References & Further Reading

**DNS Authentication Standards:**
- [Valimail: Gmail/Yahoo 2024 DMARC Requirements](https://www.valimail.com/blog) — DMARC alignment enforcement
- [MXToolbox: Gmail/Yahoo Sender Requirements](https://mxtoolbox.com) — SPF/DKIM/DMARC validation
- [RFC 7208: SPF](https://tools.ietf.org/html/rfc7208) — Sender Policy Framework spec
- [RFC 6376: DKIM](https://tools.ietf.org/html/rfc6376) — DKIM signing spec
- [RFC 7489: DMARC](https://tools.ietf.org/html/rfc7489) — Domain-based Message Authentication spec

**Deliverability Benchmarks & Best Practices:**
- [Landbase: Email Deliverability Statistics 2025](https://www.landbase.com/blog/email-deliverability-statistics) — ISP placement benchmarks (Gmail 95%, Outlook 75.6%, Yahoo 81%)
- [Validity 2025 Email Deliverability Benchmark Report](https://www.validity.com/resource-center) — Domain reputation scoring, best practices
- [Allegrow: Email Deliverability Impact on Revenue](https://www.allegrow.co/knowledge-base) — ROI framework for deliverability improvements
- [Suped: Domain Reputation Recovery Timeline](https://www.suped.com/blog) — Recovery strategies for blacklist removal

**Tools & Integrations:**
- [Google Postmaster Tools](https://postmaster.google.com) — Free Gmail reputation monitoring
- [MXToolbox](https://mxtoolbox.com) — DNS validation, blacklist checking (free tier: ~1,000/mo)
- [Mailchimp Deliverability Dashboard](https://mailchimp.com) — Email platform native metrics
- [HubSpot Email Monitoring](https://www.hubspot.com) — Bounce, complaint, reputation tracking
- [Klaviyo Deliverability Metrics](https://www.klaviyo.com) — Email platform metrics

**Reference Files (in `references/` folder):**
- `bounce_categories.md` — Hard vs. soft bounce definitions and remediation
- `complaint_triggers.md` — Common spam triggers (links, text, formatting)
- `authentication_troubleshooting.md` — SPF/DKIM/DMARC alignment fixes
- `blacklist_delisting_guide.md` — Spamhaus, Barracuda, other blacklist removal steps
- `isp_feedback_integration.md` — Setting up Gmail, Yahoo, Microsoft feedback loops
