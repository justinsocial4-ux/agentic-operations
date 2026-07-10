---
name: revops-lead-account-matching
description: "Matches incoming leads to existing Salesforce or HubSpot accounts using company-name similarity, email domain, employee count, location, phonetic fallback, and optional DQH-06 hierarchy context. Make sure to use this skill whenever the user asks to match or associate leads to accounts, resolve orphaned leads, find the right company for a lead, review ambiguous account matches, or route subsidiary leads to a parent account—even if they do not name the agent."
metadata:
  trigger_phrases:
    - "match leads to accounts"
    - "find account for lead"
    - "link leads and accounts"
    - "resolve orphaned leads"
    - "associate leads with accounts"
  category: "Lead Management"
  phase: "day_1"
  data_readiness: "day_1"
  version: "1.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-04-13"
  dependencies:
    - "DQH-06 Account Hierarchy Agent for parent/subsidiary routing"
    - "DQH-02 Field Normalization Engine for consistent company names and domains"
  mcps:
    - "Salesforce MCP (Salesforce orgs) or HubSpot MCP (HubSpot orgs)"
    - "Snowflake MCP (optional, for historical associations)"
  minimum_data:
    - "Lead object with Email, Company, and optional EmployeeCount"
    - "Account/Company object with Name, Industry, NumberOfEmployees, BillingCity, BillingCountry, ParentAccountId"
    - "Contact object with Email and AccountId for cross-matching"
  output_format: "markdown"
---

# LM-02 Lead-to-Account Matching Agent

## Why This Agent Exists

**Evidence warning:** The figures below are frozen research hypotheses, not guaranteed outcomes; several original citations do not support the exact numbers. Use `references/evidence_metrics_and_limits.md` before repeating them.

**Who it's for (ICP):** RevOps Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Orphaned Leads & Missing Account Context Delay Sales Response 24–72 Hours
- **Problem:** New leads lack account association or are misassociated, delaying follow-up by 24–72 hours and losing deal context.
- **Quantified cost:** 84% of CRM leads untouched after 30 days; average business loses $127,000/year from missed follow-ups. A 5-rep sales org loses $50K–$75K/year from context delays.
- **What teams do today:** RevOps manually match via CRM lookups and email research (5–8 hours/week = $18.2K–$29.1K/year per FTE).
- **Why it's urgent:** Over 12 months, 3,600+ unassociated leads = $1.6M–$2.4M pipeline leakage.
- **Evidence:** 4/4 rubric criteria, 4 TIER 1 sources

### Pain Point 2: Duplicate/Mismatched Accounts Inflate Pipeline & Corrupt Forecasting
- **Problem:** 10–20% duplicate accounts; leads misrouted to wrong parent account; forecast corrupted.
- **Quantified cost:** Phantom pipeline: $50K–$150K per quarter. Duplicate detection: $2K–$5K/year. Quarterly audit: $1,680–$2,520/quarter.
- **What teams do today:** Manual quarterly account audits, duplicate detection tools, consultant-led cleanup ($5K–$15K per engagement).
- **Why it's urgent:** 360 misrouted leads/year = $1.8M–$3.6M revenue impact from forecast corruption and lost deals.
- **Evidence:** 4/4 rubric criteria, 4 TIER 1 sources

### Pain Point 3: Manual Lead-to-Account Matching Takes 5–8 Hours/Week, Blocks Scaling
- **Problem:** RevOps manually look up company data and match leads to accounts; process doesn't scale with lead volume growth.
- **Quantified cost:** 5–8 hours/week per FTE = $18.2K–$29.1K/year in labor per RevOps team member.
- **What teams do today:** Manual CRM lookups, spreadsheet cross-reference, or (partially) intent/enrichment tools costing $50K–$250K/year.
- **Why it's urgent:** 20–30% YoY lead volume growth forces hiring (add 0.5–1 FTE = $35K–$90K/year) just to stay flat on matching.
- **Evidence:** 4/4 rubric criteria, 4 TIER 1 sources

### Pain Point 4: Account Hierarchy Mismanagement Breaks ABM & Expansion Strategy
- **Problem:** Expansion leads routed to wrong person; parent company relationships lost; ABM motions fail from subsidiary-to-parent mismatches.
- **Quantified cost:** 3–5 expansion leads misrouted/month = $40K–$80K lost expansion pipeline/year. Account hierarchy maintenance: $3.4K–$6.7K per quarter.
- **What teams do today:** Manual hierarchy review (2–4 weeks/quarter), Salesforce native config, or $100K–$300K/year ABM tools.
- **Why it's urgent:** 12 expansion leads/year misrouted = 6–10 lost deals = $120K–$300K lost ARR; NRR misses by 2–5pp.
- **Evidence:** 4/4 rubric criteria, 4 TIER 1 sources

---

## What This Agent Does

The Lead-to-Account Matching Agent finds the correct existing account in your CRM for every new unassociated lead using fuzzy matching on company name (Jaro-Winkler similarity), email domain, and employee count. It generates a match confidence score (0–100%) showing how confident it is in the match (e.g., "92% confidence: company name 95%, domain 100%, employee count ±10%"). HIGH-confidence matches (90%+) are auto-associated in your CRM. MEDIUM-confidence matches (75–89%) are routed to you for review before association. LOW-confidence matches (<75%) are flagged for manual lookup. If DQH-06 Account Hierarchy data is available, the agent also checks if a matched subsidiary has a parent account and intelligently routes expansion leads to the parent account owner. You get a detailed report showing all matches, their confidence scores, and the reasoning behind each match, plus a prioritized review queue for ambiguous cases.

## How to Use the Bundled Resources

- Read `references/matching_rules.md` before detailed normalization, candidate generation, tie-breaking, or threshold tuning.
- Read `references/output_contract.md` before producing the full Markdown report or JSON transaction log.
- Read `references/review_playbook.md` when presenting ambiguous matches or building a human review queue.
- Read `references/evidence_metrics_and_limits.md` before citing impact claims, setting KPI targets, or explaining limitations.
- During live scoring, a detailed audit, or an exact-arithmetic request, use `scripts/lead_account_matcher.py`. For a simple planning-only or no-tools explanation, use the identical inline formula and thresholds below without pausing to read or run bundled files.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your CRM connection, confirm DQH-06 hierarchy data is available, assess lead and account data quality, and ask you to define the scope and confidence thresholds for your matching run.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: export lead data to CSV for analysis, or help you troubleshoot the MCP connection.
- **If successful:** Proceed to Step 2.

**Step 2: DQH-06 Account Hierarchy Data Check**
- I'll verify that DQH-06 Account Hierarchy data is available and recent (<1 day old).
- **If available and recent:** I can enable subsidiary-to-parent routing.
- **If stale (>1 day):** I'll warn you but proceed without hierarchy routing.
- **If unavailable:** I'll warn you that parent/subsidiary linking is disabled, but core matching still works.

**Step 3: Required Data Validation**
I'll verify that your Lead/Contact and Account/Company objects have these minimum fields:
- Lead: Email (required), Company (required), optional EmployeeCount
- Account: Name, Industry, NumberOfEmployees, BillingCity, BillingCountry, ParentAccountId (for hierarchy)
- Contact: Email, AccountId (for cross-matching)

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ Email or Company missing in >30% of leads → Proceed but warn confidence scores will be degraded
- ✗ Email or Company missing in >70% of leads → No-go; request data quality fixes first

**Step 4: Data Quality Assessment**
I'll calculate:
- % of unassociated leads (should be >0 for matching to work)
- % of leads with valid email addresses (should be >50%)
- % of leads with company names populated (should be >50%)
- % of accounts with employee count data (used to improve match confidence)
- % of leads with valid account hierarchy data (if DQH-06 available)
- Age distribution of unmatched leads (how old are they?)

**Step 5: Define Your Matching Scope & Thresholds**
Before matching, I'll ask:
- "Do you want to match ALL unassociated leads, or a specific subset (e.g., leads from past 30 days, specific lead sources)?"
- "What should be the auto-associate threshold? (default: 90%; range: 80–100%)" → Matches at or above this score are auto-updated in CRM without review
- "What should be the review queue threshold? (default: 75%; range: 50–90%)" → Matches below auto-associate but above this score are queued for human review
- "Should I proceed with CRM updates (write mode), or just show you the analysis first (read-only mode)?"
- "Any account segments to exclude? (e.g., competitors, test accounts, specific industries)"

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ DQH-06 Account Hierarchy data loaded (updated 2 hours ago)
✓ Lead + Account objects present with required fields
✓ Email data quality: 88% valid (7,040 / 8,000 unassociated leads)
✓ Company name quality: 84% populated and normalized
✓ Account employee count: 76% available
⚠️ Lead age: 32% are >90 days old (lower intent); 68% are <30 days old (fresher)
✓ Ready to proceed

Scope: Unassociated leads from past 90 days (5,280 leads) | Auto-associate at 90% | Review queue at 75% | Write mode enabled

Next step: Fetching lead records and building fuzzy match index...
```

---

## Step-by-Step Workflow

### Step 1: Fetch Records in Batches

**What I'll do:**
- Query all unassociated Lead records (or Contact with Lead type in HubSpot) in your specified scope
- Fetch all Account/Company records with required fields
- Fetch Contact records (to enable email-to-account cross-matching)
- Load DQH-06 Account Hierarchy data (parent/subsidiary relationships)

**Batch strategy:** Fetch in 1,000-record increments to respect API rate limits.

**Data I need from each lead:**
- `Id`, `Email`, `Company` (required)
- `EmployeeCount`, `CreatedDate`, `LeadSource` (optional but helpful)

**Data I need from each account:**
- `Id`, `Name`, `Industry`, `NumberOfEmployees`, `BillingCity`, `BillingCountry`, `ParentAccountId`
- Any custom domain fields (e.g., `KnownDomains__c`)

**What you'll see:** Progress indicator ("Fetched 1,000 / 5,280 leads...").

---

### Step 2: Data Preparation & Normalization

**Normalize Lead Data:**
- Trim and lowercase company names
- Remove common suffixes: "Inc.", "LLC", "Corp.", "Ltd.", "GmbH", "Limited"
- Extract email domain from lead email (e.g., "person@example.com" → domain: "example.com")
- Normalize special characters (replace "&" with "and", etc.)
- Flag missing company names or emails

**Normalize Account Data:**
- Trim and lowercase account names
- Remove common suffixes (same as leads)
- Build lookup index by: account name, email domain, employee count range
- Load parent/subsidiary mapping from DQH-06 (if available)

**Create Phonetic Codes:**
- Generate Metaphone and Soundex codes for company names (used in fallback matching)

---

### Step 3: Candidate Account Selection

For each lead, perform matching in this priority order:

**1. Domain Match (Highest Priority)**
- Extract lead email domain (e.g., "acmecorp.com")
- Search for accounts with matching or known domains
- Confidence contribution: +0.30 (30% of final score)
- Example: Lead email "person@example.com" → Account with domain "example.com" → domain match found

**2. Exact Company Name Match (Case-Insensitive)**
- Lowercase lead company name and remove suffixes
- Match against normalized account names
- Confidence contribution: +0.25 (25% of final score)
- Example: Lead "Acme Corp." vs. Account "Acme Corporation" (after normalization, both become "acme corp") → exact match

**3. Fuzzy Company Name Match (Jaro-Winkler Similarity)**
- Calculate Jaro-Winkler similarity between lead company and account names
- Threshold: 0.85 or higher (configurable via `jaro_winkler_min` parameter)
- Confidence contribution: +0.40 × similarity score
- Example: "Acme Corp." vs. "Acme Corporation" → 0.92 similarity → +0.37 to confidence

**4. Phonetic Match (Fallback)**
- If fuzzy match fails, compare phonetic codes (Metaphone, Soundex)
- Lower confidence contribution: +0.05
- Example: "ACME" (phonetic) vs. "ACM" (phonetic code of similar company) → partial match

**5. Multi-Field Match (Employee Count + Location)**
- Check if lead employee count is within ±25% of account employee count
- Contribution: +0.15 if match
- Check if lead/account location (city/country) matches
- Contribution: +0.10 if match
- Example: Lead "500 employees, San Francisco" vs. Account "480 employees, San Francisco" → both match

**6. Subsidiary-to-Parent Match (if DQH-06 Available)**
- Check if lead company name matches a known subsidiary of an account
- If match found, route to parent account instead of subsidiary
- Flag as "expansion lead" for ABM team awareness
- Example: Lead "Acme Labs Inc." (subsidiary) → matches parent "Acme Corporation" → route to parent owner

**Candidate Ranking:**
- Generate top-N candidate accounts (default: top 3) ranked by confidence score
- If no candidates above threshold, mark as "no good candidates found" for manual review

---

### Step 4: Confidence Scoring

For each lead-account candidate pair, calculate a composite confidence score (0–100%):

During live scoring, a detailed audit, or an exact-arithmetic request, use `python3 scripts/lead_account_matcher.py score ...`; simple no-tools explanations may apply the same formula inline.

```
confidence = 0.40 × name_similarity         (Jaro-Winkler 0–1)
           + 0.30 × domain_match            (1 if match, 0 otherwise)
           + 0.15 × employee_count_match    (1 if within ±25%, 0 otherwise)
           + 0.10 × location_match          (1 if city/country match, 0 otherwise)
           + 0.05 × phonetic_match          (0.5 if codes match, 0 otherwise)

Final score (0–100%) = confidence × 100
```

**Example Calculation:**
```
Lead: "Acme Corp." | Domain: acmecorp.com | Employees: 500
Account: "Acme Corporation" | Domain: acmecorp.com | Employees: 480

name_similarity (Jaro-Winkler): 0.92
domain_match: 1.0 (exact match)
employee_count_match: 1.0 (480 within ±25% of 500)
location_match: 1.0 (both San Francisco)
phonetic_match: 0.5 (partial code match)

confidence = 0.40(0.92) + 0.30(1.0) + 0.15(1.0) + 0.10(1.0) + 0.05(0.5)
           = 0.368 + 0.30 + 0.15 + 0.10 + 0.025
           = 0.943 = 94.3%

Result: HIGH confidence (94.3%)
```

---

### Step 5: Confidence Bucketing & Filtering

**HIGH Confidence (90–100%):**
- Matches above 90% confidence threshold
- Action: AUTO_ASSOCIATE (update Lead.AccountId in CRM without review)
- Minimal human review needed
- Example: "94.3% match: Acme Corp. → Acme Corporation (domain + name + employee count align perfectly)"

**MEDIUM Confidence (75–89%):**
- Matches above review threshold but below auto-associate threshold
- Action: REVIEW_QUEUE (route to RevOps for human review and approval before CRM update)
- Human can accept, override, or request manual lookup
- Example: "82% match: Acme → Acme Inc. (name close but not exact; need human eye on suffix)"

**LOW Confidence (<75%):**
- Matches below review threshold
- Action: MANUAL_LOOKUP (flag for RevOps to research and match manually)
- Confidence too low to auto-associate or even queue for review
- Example: "58% match: 'Smith & Associates' (too generic; matches 50+ accounts; manual research required)"

**Tie-Breaking for Multiple HIGH-Confidence Matches:**
If a lead matches multiple accounts at 90%+ confidence:
1. Prefer exact name match over domain-only match
2. Prefer domain match if both names are equally distant
3. If still tied, prefer account with higher employee count alignment
4. If still tied, flag for manual review (ambiguous)

---

### Step 6: Hierarchy-Aware Routing (if DQH-06 Available)

**For leads matching subsidiary accounts:**
- Check DQH-06 hierarchy data: does this subsidiary have a parent account?
- If parent exists:
  - **Expansion motion:** Route lead to parent account owner + notify expansion team (buying signal at subsidiary = potential parent-level expansion deal)
  - **New business motion:** Route to subsidiary account owner (if subsidiary is independent or has unique sales team)
  - **Multi-thread motion:** Notify both subsidiary owner and parent owner (coordinate cross-account approach)
  - Document hierarchy relationship in lead notes: "Matched subsidiary ABC Corp. (parent: Acme Parent Inc.); routed to [owner]"
- If parent does not exist: Route normally to subsidiary owner

**For leads matching parent accounts:**
- Assume expansion motion
- Route to parent account owner
- Flag for expansion/account success team

---

### Step 7: Output Generation

- Generate a Markdown summary with HIGH, MEDIUM, LOW, expansion-routing, and data-quality sections.
- Generate a JSON transaction log with run metadata, every candidate's component scores, bucket, recommendation, hierarchy context, and aggregate counts.
- Keep pipeline-impact estimates out of deterministic output unless the customer supplies a validated model.
- Use the exact templates and field contract in `references/output_contract.md`.

---

### Step 8: User Review & Approval

**High-Confidence Matches:**
- Display summary: "I found 4,200 matches at 90%+ confidence. These are ready for auto-associate."
- Ask: "Review these samples and approve bulk auto-associate?" → User reviews 5–10 examples, then approves batch

**Medium-Confidence Matches:**
- Display review queue sorted by confidence (highest first)
- For each match: Show lead, matched account, confidence score, reasoning
- Ask: "Approve this match?" → User can Accept, Decline, or Request Manual Lookup
- Keyboard shortcuts for fast review: Y = Accept, N = Decline, M = Manual Lookup, NEXT

**Low-Confidence Matches:**
- Display: "400 leads need manual research. No good automated candidates found. [Download list]"
- Offer: "Would you like me to flag these for [RevOps team | Sales reps] to research manually?"

**Final Confirmation:**
- Summary: "Ready to execute: Auto-associate 4,200 leads (HIGH) + [N] approved (MEDIUM) = [Total] CRM updates. Estimated runtime: [X minutes]. Proceed?"
- User confirms: "Yes" → Move to execution; "No" → Abort and show what would have happened

---

### Step 9: Association Execution & Logging

**CRM Update (Salesforce / HubSpot):**
- For each approved match (HIGH + approved MEDIUM):
  - Update Lead.AccountId to matched_account_id
  - Add timestamp and match confidence to Lead notes or custom field
  - Log match transaction in audit table

**Error Handling During Execution:**
- If CRM API returns error for a lead: Log the error, continue with next lead, report summary at end
- If rate limit hit: Pause, wait, resume
- If connection drops: Offer to resume from last successful batch

**Post-Execution Reconciliation:**
- Count: Leads before update vs. after (should match approved count)
- Verify: Sample 50 random updates to confirm AccountId actually changed
- Report: "Successfully associated 4,880 leads (92.4% of 5,280 processed). 26 errors (0.5%) — these need manual review."

**Audit Trail:**
- Log timestamp, user, action, lead count, match confidence distribution
- Store in transaction log for future training data and compliance

---

## Configuration & Tuning Parameters

### User-Configurable Thresholds

| Parameter | Default | Range | Impact |
|-----------|---------|-------|--------|
| `auto_associate_threshold` | 90% | 80–100% | Matches ≥ this are auto-updated without review |
| `review_queue_threshold` | 75% | 50–90% | Matches ≥ this but < auto_associate are queued for human review |
| `jaro_winkler_min` | 0.85 | 0.70–0.95 | Fuzzy match minimum similarity; lower = more permissive |
| `employee_count_tolerance` | ±25% | ±10–50% | Employee count variance allowed for match |

### Dimension Weights (Tunable)

| Dimension | Default Weight | Range |
|-----------|---|---|
| Company name similarity (Jaro-Winkler) | 40% | 20–60% |
| Email domain match | 30% | 10–50% |
| Employee count match | 15% | 5–30% |
| Location match (city/country) | 10% | 0–30% |
| Phonetic match | 5% | 0–10% |

---

## Error Handling & Graceful Degradation

### Data Quality Issues

| Issue | Severity | Handling | Impact |
|-------|----------|----------|--------|
| Lead missing company name | Medium | Skip lead; add to skip log | Lead cannot be matched; flag for manual entry |
| >30% of leads missing company name | High | Warn user; offer data quality fixes | Batch matching unreliable; recommend manual entry first |
| Account missing ParentAccountId | Low | Proceed; assume account is root | Subsidiary-to-parent linking skipped for that account |
| DQH-06 hierarchy stale (>1 day) | Medium | Warn user; proceed without hierarchy routing | Expansion leads may be routed to subsidiary instead of parent |

### MCP Connection Failures

| Scenario | Handling |
|----------|----------|
| Cannot fetch leads | Retry with exponential backoff; explain error and offer CSV import |
| Cannot write updates | Log partial results; offer CSV export for manual import |
| Rate limit exceeded | Implement 5–10 second backoff; retry batch |
| Salesforce / HubSpot down | Defer execution; ask user to retry later |

### Graceful Degradation Examples

```
I found 14 high-confidence matches. Here's what I can tell you:

Matches (confidence 90%+):
[table of 14 accounts]

Limitations:
- I couldn't pull DQH-06 hierarchy data, so subsidiary-to-parent routing is disabled
- Data is 2 days old (warehouse sync lag)

Confidence: 85% (hierarchy routing disabled)
Suggested next step: Update hierarchy data or manually route expansion leads
```

---

## Success Metrics & KPIs

- Measure match coverage, precision, recall, false positives, review acceptance, hierarchy-routing accuracy, latency, and write errors.
- Treat old percentage and business-impact targets as unvalidated pilot targets until a labeled customer sample and baseline exist.
- Read `references/evidence_metrics_and_limits.md` for definitions, validation requirements, and the frozen research caveats.

---

## Dependencies & Data Requirements

### Hard Dependencies (Must Exist First)

- **DQH-06 Account Hierarchy Agent** — LM-02 uses DQH-06 hierarchy data to route expansion leads to parent accounts correctly
- **DQH-02 Field Normalization Agent** — LM-02 depends on normalized company names and email domains for reliable fuzzy matching

### Soft Dependencies

- **Salesforce MCP or HubSpot MCP** — Required to read/write Lead, Account, Contact data
- **Snowflake MCP (optional)** — Allows LM-02 to query historical lead-to-account associations for pattern learning

### Minimum CRM Configuration

**Salesforce:**
- Lead object with: FirstName, LastName, Email, Company, DomainName (or extract from Email)
- Account object with: Name, Industry, NumberOfEmployees, BillingCity, BillingCountry, ParentAccountId
- Contact object with: Email, AccountId
- Writable field on Lead to store AccountId (native or custom)
- Account hierarchy configured (ParentAccountId populated)

**HubSpot:**
- Contact object with Company, Email, Phone
- Company object with Name, Industry, Number of Employees, Billing City, Billing Country
- Custom property on Contact or Company to capture parent company relationship (if using hierarchy)
- Ability to write Company associations to Contact

---

## Known Limitations & Future Enhancements

- v1 uses CRM fields only; it does not call external enrichment systems.
- Matching uses company/account evidence, not personal phone or contact-name matching.
- DQH-06 supplies complex hierarchy context; core matching still works without it but cannot route to ultimate parents.
- The algorithm is static and does not learn from corrections.
- Read `references/evidence_metrics_and_limits.md` for detailed workarounds, future options, and claims that require customer validation.

---

## Interaction Patterns & Tone

- Explain every candidate with component scores, missing evidence, bucket, and next action.
- Never present a rounded example as a different bucket than the exact formula produces.
- Keep write mode behind an explicit final confirmation.
- Read `references/review_playbook.md` for the full introduction, ambiguous-match template, and worked HIGH/MEDIUM/LOW examples.

---

## Related Agents & Workflow Integration

**Upstream (Must Run First):**
- **DQH-06 Account Hierarchy Agent** — Builds the parent/subsidiary hierarchy that LM-02 uses
- **DQH-02 Field Normalization Agent** — Normalizes company names and domains for reliable matching

**Downstream (Uses This Agent's Output):**
- **LM-03 Lead Routing Agent** — Routes matched leads to the correct rep or account team
- **OO-04 Multi-Threading Agent** — Uses matched account data to identify all contacts and buying committees
- **PM-04 Forecast Agent** — Uses account associations to prevent orphaned opportunities from inflating forecast
