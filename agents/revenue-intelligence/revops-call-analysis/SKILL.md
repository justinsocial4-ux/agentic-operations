---
name: revops-call-analysis
description: 'Automates extraction of structured intelligence from recorded sales
  conversations (Gong/Fathom): objections, competitors, next steps, sentiment, and
  methodology adherence. Populates CRM fields, generates coaching digests, and flags
  deals at risk.'
metadata:
  trigger_phrases:
  - analyze sales calls
  - extract call insights
  - review conversation intelligence
  - populate deal insights from calls
  - generate coaching digest
  - track objections from calls
  - identify competitor mentions
  - assess call sentiment
  - coach from call analysis
  - find deal risk signals
  category: Revenue Intelligence
  phase: 30_days
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents: []
    mcps:
    - Gong MCP (if using Gong)
    - Fathom MCP (if using Fathom)
    - Salesforce MCP (if using Salesforce) OR HubSpot MCP (if using HubSpot)
    - Slack MCP (optional, for digest delivery)
    minimum_data:
    - Call recordings with transcripts (Gong or Fathom)
    - 'Call metadata: participants, dates, company context'
    - CRM opportunity/deal records with basic fields (close_date, stage, amount, account)
    - Sales rep data linked to calls and CRM records
  output_format: markdown (coaching digest + CRM field mapping); JSON (extracted insights)
---

# RI-03 Call Analysis Agent

## Why This Agent Exists

**Who it's for (ICP):** Sales Operations Manager or RevOps Manager at B2B SaaS companies, 100–500 employees, North America, already licensed Gong, Fathom, or Chorus.

**The painkiller pain points we're solving:**

### Pain Point 1: Manual CRM Data Entry After Every Call Consumes 3.4 Hours Per Rep Per Week

- **Problem:** Sales reps spend 3.4 hours per week manually entering call notes, objections, competitors, and next steps into CRM. 70% of rep time spent on admin tasks; 37% fabricate CRM data to meet quota pressure.
- **Quantified cost to the role:** At $57.70/hour, this costs $17,300/year per rep. For a 50-rep team: **$865,000/year in lost selling time.**
- **What teams do today:** Reps log into CRM post-call, read through Gong/Fathom dashboards, manually type notes. No structured extraction. RevOps managers spend 8–12 hours weekly manually reviewing calls to extract coaching insights.
- **Why it's urgent:** Data entry burden drives fabrication; forecasts become unreliable; coaching becomes reactive rather than proactive.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

### Pain Point 2: No Scalable Objection Tracking or Competitive Intelligence Extraction

- **Problem:** Without systematized objection logging, teams cannot identify which objections kill deals at which stage, measure response effectiveness, or track competitor mentions. Competitor intelligence remains trapped in call transcripts.
- **Quantified cost to the role:** Teams updating battlecards monthly achieve **59% win-rate lifts.** Teams tracking competitor mentions achieve **10–25% higher win rates.** Organizations with formal objection handling realize **91% of quota vs. 85%** for unstructured approaches.
- **What teams do today:** Managers manually listen to calls, create notes. No taxonomy = inconsistent tagging = no trend visibility.
- **Why it's urgent:** Competitor trends inform battlecard priority; objection patterns guide training; without visibility, teams can't improve methodology adherence.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 3 TIER 1 sources

### Pain Point 3: Coaching Digest Generation Requires Manual Manager Review (8–12 Hours Weekly)

- **Problem:** Sales managers spend Thursday–Friday afternoons manually auditing deals and collecting call insights to prepare coaching feedback and forecast reports. No proactive alerting.
- **Quantified cost to the role:** Reduce manager prep time by 60% (saving ~5 hrs/week per manager). Enable daily coaching vs. weekly. Increase first-call coaching (within 24 hrs of call) from current <20% to >70%.
- **Impact if solved:** Coaching within 24 hours of call makes reps **2.5x more likely to improve.** Reps getting 2+ hours/week coaching achieve **56% win rates vs. 43%** for those getting ≤30 min/week.
- **What teams do today:** Dashboards show metrics but require manual interpretation. Managers must synthesize: talk-to-listen ratios, discovery question frequency, methodology adherence, deal-risk signals.
- **Why it's urgent:** Daily coaching window closes fast; weekly reports are too slow. By Monday morning, coaching on Friday's call is stale.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 3 TIER 1 sources

---

## What This Agent Does

The Call Analysis Agent is your conversation intelligence analyst and coaching assistant. It watches your sales calls in real-time (or processes them on a schedule), extracts structured insights using LLM-based extraction and sales methodology frameworks (MEDDICC/SPICED), and populates your CRM with deal intelligence. You get an automated coaching digest every morning listing which reps need intervention and why, which deals are at risk, and which objections are trending across your team. The agent handles all the grunt work: linking calls to deals, mapping objections to your custom taxonomy, scoring sentiment, and flagging competitor mentions so your sales leaders can focus on coaching and strategy instead of data hunting.

---

## Getting Started (Preflight Check)

When you trigger this agent, I'll verify your setup is complete and ask you to configure key parameters before analyzing calls.

**Step 1: MCP Connection Verification**
- I'll check if Gong MCP or Fathom MCP is connected and authenticated.
- I'll check if Salesforce MCP or HubSpot MCP is connected.
- **If either connection fails:** I'll offer workarounds (manual transcript upload, export-then-analyze) or help you troubleshoot the MCP.
- **If successful:** Proceed to Step 2.

**Step 2: CRM Configuration Validation**
I'll verify that your CRM has:
- Opportunity (Salesforce) or Deal (HubSpot) objects with: close_date, stage, amount, account linkage
- Contact object linked to Opportunity/Deal
- Sales rep data identifiable in call metadata and linked to opportunity owner
- At least one custom field available for extracted data (or I'll create a new custom object)

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ Some fields missing → Partial results possible; I'll flag limitations and proceed with available data
- ✗ Core objects missing (no Opportunity/Deal or Contact) → No-go; request CRM configuration first

**Step 3: Objection Taxonomy Configuration**
I'll ask:
- "Do you have a custom objection taxonomy (Budget, Timeline, Fit, Authority, Competitor, etc.), or should I use a default?"
- If custom: "Can you share it as JSON or a spreadsheet?"
- If not: "I'll use a default taxonomy; you can customize it anytime."

**Step 4: Sales Methodology Definition**
I'll ask:
- "Which sales methodology do your reps follow: MEDDICC, SPICED, Sandler, or other?"
- "Should I score adherence to your framework in call analysis?"

**Step 5: Define Your Call Processing Scope**
I'll ask:
- "Should I start with new calls only, or backfill the last 30 days?"
- "Any accounts or date ranges to exclude?"
- "How often should I process calls: real-time, daily, weekly?"

**Preflight Report**
I'll summarize:
```
✓ Gong MCP connected (Workspace: abc123)
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Opportunity object ready with required fields
✓ Contact data linkable
⚠️ No custom objection taxonomy configured (will use default)
✓ Sales methodology: MEDDICC (rep training confirmed)
✓ Ready to proceed

Scope: New calls only, starting today | Processing: Daily digest
Next step: Analyzing calls from today onward...
```

---

## Step-by-Step Workflow

### Step 1: Fetch Calls from Gong/Fathom (in batches)

**What I'll do:**
- Query Gong or Fathom API for new/recent calls (in scope you defined)
- Retrieve call metadata: recording URL, transcript, participants, duration, custom fields
- Identify call date, participants, company context
- Fetch transcripts with speaker labels and timestamps

**Batch strategy:** 
- Gong: Poll with 5–10 minute intervals; retrieve up to 50 calls per batch
- Fathom: Retrieve via REST API; handle rate limits gracefully

**Data I need from each call:**
- Call ID, recording URL, transcript text (required)
- Participants: name, email, role (sales_rep vs. prospect), talk/listen time
- Call metadata: date, duration, company name (if available), deal linkage (if in custom fields)
- Gong-specific: custom fields (account name, opportunity ID)
- Fathom-specific: call title, summary (optional but helpful)

**What you'll see:** "Fetched 15 new calls (last 24 hours). Processing..."

---

### Step 2: Transcript Ingestion & Normalization

**What I'll do:**
- Parse transcript with speaker labels and timestamps
- Identify sales rep (from participant list; match to CRM by email/name)
- Identify prospects (all other participants)
- Calculate talk-to-listen ratio per speaker (rep should listen 60–70%)
- Detect hesitation markers: pauses, filler words ("um", "uh"), interruptions, long silences
- Extract call metadata: duration, date, participants, company context
- Flag incomplete transcripts or audio quality issues

**Output:** Normalized call record with speaker roles, timing, and engagement metrics

---

### Step 3: LLM-Based Structured Extraction (5 Extraction Objectives)

**Objective 1: Extract Objections**
- Use few-shot LLM prompt with customer's objection taxonomy
- Identify phrases indicating objection (budget concern, timeline issue, fit question, authority blocker, competitor mention, technical concern, trust/validation request)
- Classify each against taxonomy
- For each objection, extract:
  - Type (from taxonomy)
  - Exact phrase from transcript
  - Timestamp (seconds into call)
  - Speaker (prospect or rep)
  - Severity (high, medium, low based on context and deal stage)
  - Whether rep handled it (yes/no/partially)
  - Effectiveness of rep's response (moved deal forward / neutral / ineffective)
  - Confidence score (0–100)

**Objective 2: Extract Competitor Mentions**
- Identify mentions of known competitors (customer-provided list or default: Salesforce, HubSpot, Pipedrive, Chorus, Gong, Avoma, Fathom, etc.)
- For each mention, extract:
  - Company/product name
  - Context (what was said about it?)
  - Sentiment (positive, neutral, negative, negative_comparison)
  - Likelihood this is a competing deal (0–1 scale; 0.95 = "we're evaluating X", 0.30 = generic reference)
  - Number of times mentioned in call
  - Confidence score

**Objective 3: Extract Next Steps & Commitments**
- Identify commitments made during call (by rep or prospect)
- Examples: "I'll send ROI spreadsheet", "Follow-up call next Tuesday", "You'll schedule implementation kickoff"
- For each, extract:
  - Commitment text
  - Speaker (sales_rep or prospect)
  - Due date or timeline (if mentioned; infer from context if needed)
  - Timestamp
  - Confidence score (high threshold: >0.85 = clear commitment)

**Objective 4: Score Overall & Per-Speaker Sentiment**
- Analyze call tone, energy, engagement
- Assign overall sentiment label and score (0–1 scale):
  - 0.0–0.3: Negative (objections dominant, skeptical tone)
  - 0.3–0.6: Neutral (mixed signals, some concerns)
  - 0.6–0.8: Positive (clear interest, few objections)
  - 0.8–1.0: Very Positive (strong fit, high enthusiasm)
- Per-speaker sentiment: Rep sentiment typically 0.7–0.9 (reps stay upbeat); Prospect sentiment varies
- Sentiment trend within call: Improving / Stable / Declining
- Hesitation markers: Count and flag significant increases
- Discovery depth: Score based on question types (open-ended discovery questions scored higher)

**Objective 5: Score Sales Methodology Adherence (MEDDICC/SPICED)**
- If MEDDICC: Map transcript to 6 elements (Metrics, Economic Buyer, Decision Criteria, Decision Process, Identified Champion, Champion Coach)
- If SPICED: Map to 6 elements (Situation, Pain, Implications, Consequences, Envisioned Solution, Decision)
- For each element, indicate: Present (yes/no), timestamps where it appears, evidence quote from transcript, gap (if missing)
- Score overall adherence percentage (X of Y elements present)
- Identify top 3 gaps for coaching

---

### Step 4: Confidence & Quality Gating

**What I'll do:**
- Assign confidence score to each extraction (0–100)
- Flag low-confidence items (<70%) for manual review
- If overall extraction confidence <80%, add extra review flag
- Create audit trail: timestamp, extraction method, confidence, any manual overrides

**Quality checks:**
- Is transcript complete (>90% of call duration transcribed)?
- Are speaker identifications confident (email match or speech recognition confidence)?
- Are extracted items supported by specific phrases/timestamps (vs. inferred)?

**Output:** Confidence report; final extraction proceeds only if confidence gates pass

---

### Step 5: CRM Deal Matching

**What I'll do:**
- Try to link call to deal record (three methods, in priority order):

  **Method 1: Custom Field Lookup** 
  - If Gong/Fathom custom field contains opportunity ID → direct match to CRM deal

  **Method 2: Prospect Email Fuzzy Match**
  - Extract prospect email from call participants
  - Search CRM Contact by email (exact or fuzzy match)
  - Find linked Opportunity/Deal

  **Method 3: Company + Rep Fuzzy Match**
  - Extract company name from call metadata or email domain
  - Match to Account in CRM (fuzzy name match)
  - Find open Opportunity for that Account owned by the sales rep in call

**Fallback:**
- If no confident match: Log call with best-guess context (prospect name, company, date)
- Flag for manual linking
- Store temporarily; don't write to CRM yet

**Output:** Deal linkage confidence score; if <80%, flag for manual review before CRM write

---

### Step 6: CRM Field Mapping & Normalization

**What I'll do:**
- Map extracted fields to customer's CRM schema (Salesforce or HubSpot)
- Validate target fields exist; if not, offer to create custom object
- For multi-select/array fields (objections, competitors):
  - Store as comma-separated list OR JSON (based on CRM capability)
  - Limit to 10 items max (avoid field overflow)
  - Include confidence scores in notes if needed
- For sentiment scores: Normalize to CRM's scale (PERCENT = 0–100, DECIMAL = 0–1)
- For dates: Validate format and convert to CRM locale
- For text fields: Truncate if CRM has character limit; warn if data loss

**Fallback (if target field unavailable):**
- Write to deal notes with structured prefix:
  ```
  [RI-03 CALL ANALYSIS | 2026-04-13 14:45 UTC]
  Objections: Budget (high, 95% confidence), Timeline (medium, 88%)
  Competitors: Salesforce (85% likely competing deal)
  Next Steps: Send ROI sheet (due 4/15, 95% confidence)
  Sentiment: Cautiously Positive (72%)
  Methodology: MEDDICC adherence 67% (gaps: Economic Buyer, Champion Coach)
  ```

**Output:** Validated CRM payload ready for write-back

---

### Step 7: Coaching Digest Generation

**What I'll do:**
- Aggregate call data by sales rep (across all calls in digest period)
- Identify top 3 coaching opportunities:
  - By impact on pipeline (risk signals + objection severity + deal size)
  - By frequency of pattern (same gap across multiple reps → team training need)
  - By rep readiness (which reps are coachable and will respond?)
- Link to sales plays, battlecards, methodology resources
- Score deal risk based on:
  - Objection patterns (budget early in cycle = high risk)
  - Sentiment trend (declining = risk)
  - Competitor likelihood (0.9+ competing deal = high risk)
  - Days to close (under 15 days + risk signal = escalate)
- Generate text for manager digest with clear, actionable recommendations
- Highlight wins: calls with full methodology adherence, strong sentiment, effective objection handling

**Output:** Structured coaching digest (markdown or Slack message)

---

### Step 8: CRM Write-Back

**What I'll do:**
- Batch updates to minimize API calls
- Write extracted fields to opportunity record:
  - `deal_objections_raised__c` = comma-separated list
  - `deal_competitors_mentioned__c` = comma-separated list
  - `deal_call_sentiment__c` = Positive/Neutral/Cautiously_Positive/Negative
  - `deal_sentiment_score__c` = numeric score
  - `deal_discovery_depth_score__c` = numeric score
  - `deal_methodology_adherence__c` = Full/Partial/Minimal
  - `deal_methodology_gaps__c` = comma-separated gaps
  - `deal_talk_listen_ratio__c` = "X% talk, Y% listen"
  - `deal_last_call_date__c` = date
  - `deal_call_risk_signal__c` = No_Risk/Monitor/High_Risk
- Append activity comment with extraction metadata:
  ```
  [RI-03 CALL ANALYSIS] Call analyzed on 2026-04-13 14:45 UTC. 
  Extraction confidence: 92%. 
  Objections: Budget (high), Timeline (medium). 
  Competitor: Salesforce (85% likely competing deal). 
  Sentiment: Cautiously positive (72%). 
  Gaps: Economic buyer not qualified, champion not coached. 
  Recommendation: Schedule manager coaching within 24 hours.
  ```
- Retry on transient failures (rate limits, timeouts); log permanent failures
- Update `deal_last_call_date__c` field
- Return summary of write operations (X fields updated, Y failed)

**Output:** CRM updates complete; visible on deal record within 5 minutes

---

### Step 9: Output Delivery

**What I'll do:**
- **Coaching Digest:** Format for email + Slack delivery to manager (daily or weekly, per frequency config)
- **Slack Alerts:** Post real-time alerts for HIGH-RISK deals (if Slack MCP connected)
- **CRM Updates:** Visible on opportunity record (fields + activity comment)
- **Audit Log:** Timestamped extraction details stored for 7-year compliance retention
- **Dashboard (Optional):** Generate summary metrics (monthly objection trends, competitor frequency, rep performance, team methodology adherence)

---

## Configuration Options

Before I start analyzing calls, you can customize these parameters:

**Extraction Scope:**
- "Should I analyze all calls, or filter by: date range, specific accounts, specific sales reps, specific deal stages?" (Default: all calls)
- "Should I backfill historical calls or start with new calls only?" (Default: new only)

**Objection Taxonomy:**
- "Should I use a default taxonomy (Budget, Timeline, Fit, Authority, Competitor, Technical, Trust) or your custom one?" (Default: default taxonomy)
- "How should I weight severity? By deal stage (budget early = high risk) or by objection type?" (Default: deal stage + type)

**Sales Methodology:**
- "Which framework: MEDDICC, SPICED, Sandler, or none?" (Default: none; you can add any time)
- "Should I score adherence and flag gaps in coaching digest?" (Default: yes, if framework selected)

**CRM Configuration:**
- "Which CRM: Salesforce or HubSpot?" (Default: first MCP detected)
- "Should I create custom fields if they don't exist, or write to deal notes instead?" (Default: create custom fields)
- "Which fields should I populate? All (comprehensive) or essential only (objections, sentiment, risk)?" (Default: comprehensive)

**Delivery & Frequency:**
- "How often should I process calls: real-time, daily, weekly?" (Default: daily)
- "Who should receive coaching digests? Manager email, Slack channel, both?" (Default: manager email)
- "Should I post HIGH-RISK deal alerts in real-time to Slack?" (Default: yes, if Slack MCP connected)

**Confidence Thresholds:**
- "What confidence threshold should I use for CRM writes? High (>85%), Medium (>70%), or Low (>60%)?" (Default: Medium)
- "Should I flag low-confidence items (<70%) for manual review before CRM write?" (Default: yes)

---

## Error Handling

### If MCP Connection Fails

**If Gong/Fathom connection fails:**
- Offer to work with manual transcript upload (slower but works)
- Provide troubleshooting steps: verify API key, check permissions, confirm workspace ID
- Don't block; proceed with partial workflow if data is available

**If Salesforce/HubSpot connection fails:**
- Skip CRM write-back; deliver extraction results as report instead
- Provide step-by-step instructions to reconnect MCP
- Offer to save extraction results for manual CRM import later

### If Required Data Is Missing

**If transcripts are missing or incomplete:**
- Gong: Some older calls may not have transcripts; skip those calls
- Fathom: Fallback to summary if transcript unavailable (degraded extraction quality)
- Flag affected calls; continue with processable calls

**If deal linkage fails (can't find deal for call):**
- Log call with best-guess context (prospect name, company, date)
- Flag for manual linking by RevOps team
- Don't write to CRM until deal is manually confirmed
- Example: "Call with Jane Smith (person@example.com) on 4/13 — no matching deal found. Please link manually or confirm if this is AcmeCorp Enterprise deal?"

**If CRM fields unavailable:**
- Create custom object `Call_Insights__c` (Salesforce) or new property set (HubSpot) to house extracted data
- If customer declines: Write to deal notes with structured prefix (see Step 6 fallback)
- Alert customer: "Custom fields not available; storing in deal notes instead. Consider creating fields for scalability."

**If taxonomy not configured:**
- Use default taxonomy (Budget, Timeline, Fit, Authority, Competitor, Technical, Trust)
- Process calls successfully; notify customer: "Using default taxonomy. Upload your custom taxonomy anytime to refine results."

### If Data Quality Is Too Low to Proceed

**Poor transcript quality (>20% untranscribed):**
- Flag call; continue processing but lower confidence score by 15–20 points
- Example: "Transcript is 78% complete. Extraction confidence 65% (was 80%). Manual review recommended."

**Incomplete call metadata (missing participants, company context):**
- Proceed with available data; flag in audit log
- Example: "Prospect name unknown (participant role identified but no email). Deal linkage may fail."

**Unidentifiable sales rep:**
- Skip this call (can't link to rep for coaching)
- Flag for manual review: "Call recorded but sales rep not identifiable in participant list"

### If API Rate Limits Are Hit

**Gong rate limiting:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (25 calls instead of 50)
- Resume processing after cooldown; log retry in audit trail

**Fathom rate limiting:**
- Check API credits; stop processing if credits exhausted
- Notify customer: "API credits limit reached. Continue tomorrow or upgrade plan."

**CRM API rate limits:**
- Batch writes in chunks (100 record updates per request)
- Retry with delays; split into multiple daily batches if needed

### Graceful Degradation: Partial Results OK

When data is incomplete but valuable insights exist:
- Continue extraction with degraded confidence
- Flag what's missing and its impact
- Example: "Call sentiment and methodology adherence calculated. Objection extraction skipped (no taxonomy configured yet)."

---

## What to Run Next

After call analysis is complete, consider:

1. **EO-03: Coaching Recommendation Agent** — Takes coaching digest from RI-03 and generates rep-specific, methodology-keyed coaching recommendations (playbooks, role-plays, battlefield scenarios).

2. **PM-DEAL-02: Deal Intelligence Agent** — Takes deal-level signals from RI-03 (objection patterns, competitor mentions, sentiment trend) to compute deal risk scores, pipeline health, and win-rate predictions.

3. **Schedule Recurring Call Analysis** — Set up daily or weekly call processing to build historical trend data for objection patterns, competitor intel, and rep performance metrics.

4. **Build Custom Objection Taxonomy** — Once you've seen 50+ calls, consolidate common objections into your custom taxonomy for improved accuracy.

---

## Example: End-to-End Session

**You:** "Analyze my sales calls from this week. Show me coaching opportunities and deal risks."

**Me (Preflight):**
```
✓ Gong MCP connected (Workspace: acmecorp)
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Opportunity object ready
⚠️ Using default objection taxonomy (no custom config)
✓ MEDDICC methodology selected (reps trained on this)
✓ Analyzing calls from: 2026-04-08 to 2026-04-13 (12 new calls)
```

**Me (Analysis):**
```
Fetching 12 calls from Gong... ✓
Extracting objections, sentiment, methodology adherence...
✓ 12 calls processed
Confidence gates passed: 11/12 high confidence
Flagged for manual review: 1 (poor transcript quality, 68% confidence)
Linking to CRM deals... ✓ 11/12 matched

Generating coaching digest...
✓ Top 3 coaching opportunities identified
✓ 2 HIGH-RISK deals flagged (objection pattern + declining sentiment)
✓ Methodology adherence analysis: 5/12 full adherence, 7/12 partial
```

**Report (Markdown):**

```markdown
## COACHING DIGEST — Week of April 8-13, 2026

### 🎯 TOP COACHING OPPORTUNITIES

1. [HIGH] Marcus Johnson — TechCorp Deal (Close: 4/30)
   - Issue: Unhandled budget objection + missed Economic Buyer qualification
   - Objection: "That's 3x our current tool spend" [HIGH severity, 95% confidence]
   - Gap: Rep never asked "Who controls the budget?" (MEDDICC: E missing)
   - Recommendation: 30-min coaching on ROI justification + stakeholder mapping
   - Confidence: 95%

2. [MEDIUM] Jessica Lopez — GlobalInc Deal (Close: 5/15)
   - Issue: Declining sentiment trend (80% → 55% across 3 calls)
   - Pattern: "We need board approval" mentioned 4x (Authority objection)
   - Gap: Rep never identified champion or coached on internal positioning
   - Methodology: Partial MEDDICC (missing D, Champion Coach)
   - Recommendation: 30-min call on champion mapping + internal positioning brief
   - Confidence: 88%

3. [MEDIUM] David Kim — LocalStart Deal (Close: 4/22)
   - Issue: Competitor mention (Chorus) not addressed with battlecard
   - Competitor: "Considering Chorus instead" [85% likely competing deal]
   - Gap: Rep did not differentiate vs. Chorus
   - Recommendation: Share updated Chorus battlecard; 20-min competitive objection handling
   - Confidence: 85%

### ⚠️ DEAL RISK ALERTS

[HIGH RISK] TechCorp (Marcus Johnson, close 4/30)
- Signals: Budget objection (high) + declining sentiment + timeline compression
- Recommendation: VP intervention + executive sponsor call

[MEDIUM RISK] GlobalInc (Jessica Lopez, close 5/15)
- Signals: Declining sentiment trend + unresolved Authority objection
- Recommendation: Manager coaching + champion engagement

### 📊 TEAM METHODOLOGY ADHERENCE (MEDDICC)

Coverage Across Week (12 calls):
- ✓ Full adherence (6/6 elements): 5 calls (42%)
- ⚠️ Partial (missing 1–2): 7 calls (58%)
- ✗ Minimal (missing 3+): 0 calls (0%)

Most Common Gaps:
1. Economic Buyer (missing 6/12 calls) — "Who controls budget?" not asked
2. Decision Process (missing 4/12 calls) — Approval timeline not mapped
3. Champion Coach (missing 3/12 calls) — Champion not coached on positioning

Team Training Recommendation: 45-min session on Economic Buyer discovery

### 📈 WEEKLY TRENDS

Total calls: 12 | Avg sentiment: 71% (stable)
Most common objection: Budget (33%, 4/12 calls)
Most common competitor: Salesforce (2 mentions, 85% likelihood)
Avg discovery depth: 78%
Calls with risk signals: 2/12 (17%)
```

**You:** "This looks good. How should Marcus approach the budget objection?"

**Me:** "Great question. Marcus needs a two-pronged approach:
1. ROI justification: Quantify cost of the problem they're solving (what does the pain cost them annually?)
2. Stakeholder mapping: Ask 'Who besides you needs to approve this?' to uncover the Economic Buyer

Want me to send Marcus the ROI battlecard template and schedule a quick coaching call with him?"

---

## References & Further Reading

**Detailed Extraction Documentation:**
- `objection_taxonomy_default.md` — Standard objection types, severity drivers, example phrases
- `methodology_meddicc.md` — MEDDICC element mapping and evidence scoring
- `methodology_spiced.md` — SPICED element mapping and evidence scoring
- `competitor_classification.md` — Tier 1/2/3 competitor likelihood scoring
- `sentiment_rubric.md` — Sentiment score interpretation and per-speaker analysis

**External Research & Benchmarks:**
- [Gong: State of Sales 2025](https://www.gong.io/state-of-sales/) — Call analysis benchmarks, objection patterns
- [Klue: The ARR of Objection Handling](https://klue.com/blog/the-arr-of-objection-handling-in-sales) — Competitive intelligence ROI
- [Qwilr: Sales Coaching Statistics 2025](https://qwilr.com/blog/sales-coaching-statistics/) — Coaching effectiveness metrics
- [Gong API Documentation](https://help.gong.io/docs/what-the-gong-api-provides) — Official API specs
- [Fathom API Documentation](https://developers.fathom.ai/quickstart) — Official API specs

**Downstream Agent Dependencies:**
- `EO-03: Coaching Recommendation Agent` — Consumes RI-03 coaching digest; generates rep-specific playbooks
- `PM-DEAL-02: Deal Intelligence Agent` — Consumes RI-03 deal risk signals; enriches with pipeline health metrics

---

**Agent Maintained By:** RevOps Agent Factory  
**Last Reviewed:** April 13, 2026  
**Support:** #revops-agents Slack channel
