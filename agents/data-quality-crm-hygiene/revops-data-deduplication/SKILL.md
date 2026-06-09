---
name: revops-data-deduplication
description: "Finds and merges duplicate contact, lead, and account records in Salesforce or HubSpot using fuzzy-matching algorithms. Identifies near-duplicates that exact-match rules miss, scores match confidence, prevents duplicate outreach, and reduces pipeline inflation. Trigger on: find duplicate contacts, deduplicate my CRM, identify duplicate records, merge duplicate contacts, check for duplicates, find duplicate leads, deduplicate contacts and leads, clean up duplicate records."
metadata:
  category: "Data Quality & Hygiene"
  phase: "Phase 1"
  data_readiness: "day_1"
  version: "1.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-04-12"
  dependencies:
    agents: []
    mcps:
      - "Salesforce MCP (Salesforce orgs)"
      - "HubSpot MCP (HubSpot orgs)"
    minimum_data:
      - "Contact object with Email, Phone, FirstName, LastName fields"
      - "Lead object (Salesforce) or equivalent (HubSpot)"
      - "Account/Company object for company-level deduplication"
---

# DQH-01 Deduplication Engine

## Why This Agent Exists

**Who it's for (ICP):** RevOps Manager or Sales Operations Manager at B2B SaaS companies, 50–500 employees, North America.

**The painkiller pain points we're solving:**

### Pain Point 1: Labor Cost — 550+ Hours of Wasted Sales Time Per Rep Annually
- **Problem:** Sales reps waste ~550 hours per year managing inaccurate CRM data, including duplicate records that confuse prospect status and engagement history.
- **Quantified cost to the role:** 550 hours/rep/year × 10-person sales team × $50/hour = $275,000 in annual labor waste (or $27,500 per rep per year).
- **What teams do today:** Manually identify duplicates, merge records in CRM, maintain dedup rules. Teams pay $240–$10,000/year for point dedup tools (No Duplicates, Cloudingo, DataGroomr) and spend 4 minutes per merge × 5,000 duplicates = 333 hours of manual labor ($16,650) per cleanup cycle.
- **Why it's urgent:** B2B contact data decays at 70% annually. 80% of new integration data is duplicate. Without continuous deduplication, duplicate rate grows from 5–10% to 15–20% within 12 months, and the labor waste compounds. By year 2, sales team loses confidence in CRM as source of truth.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 4 TIER 1 sources

### Pain Point 2: Revenue Impact — Duplicate Outreach & Pipeline Inflation Reduce Deal Win Rate
- **Problem:** Duplicate records cause duplicate outreach (same prospect receives multiple identical emails), damaging relationships. Duplicate opportunities inflate pipeline reports, causing forecast errors and missed board expectations.
- **Quantified cost to the role:** $480,000 in cleanup costs for 5,000 duplicates in a 50,000-record database. Duplicate outreach reduces win rate by 5–10% and revenue gains by 25%; for $10M ARR with 20% growth target, this equals $500,000 in foregone ARR. Additionally, each duplicate costs ~$96 to resolve (identification + merge labor).
- **What teams do today:** Purchase deduplication tools ($240–$10,000/year) and hire consultants to build merge rules and conduct quarterly cleanup cycles. Teams also implement manual CRM governance and spreadsheet-based duplicate tracking as band-aids.
- **Why it's urgent:** 76% of CRM users say less than half their data is accurate and complete (Validity 2025). 37% of organizations lose revenue as a direct result. Pipeline inflation compounds forecast errors; by month 12, forecast accuracy falls below acceptable threshold, triggering emergency data cleanup projects costing $50,000–$100,000.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 5 TIER 1 sources

### Pain Point 3: Regulatory Risk — Duplicate Records Violate GDPR & Create Liability
- **Problem:** Duplicate personal data violates GDPR's data minimization principle (€20M or 4% of global turnover fines). Healthcare organizations face HIPAA liability; duplicate patient records cause medical errors costing $1.7 billion annually in aggregate malpractice claims.
- **Quantified cost to the role:** €20M GDPR fines; 4% of $20M ARR = $800,000 potential loss per violation. Healthcare malpractice costs range $100,000–$5M per patient misidentification error. Large healthcare systems spend >$1M annually fixing duplicates (compliance + operational).
- **What teams do today:** Hire compliance officers ($120,000–$200,000/year) and conduct annual GDPR/HIPAA audit cycles ($50,000–$100,000 per audit) to identify and remediate duplicates. Some engage external consultants for data minimization reviews.
- **Why it's urgent:** 34% of organizations have experienced financial or reputational harm from data governance lapses (Integrate 2025). Each audit cycle that discovers non-compliance triggers legal review and escalating remediation costs. By year 2, regulatory fines and legal costs become material.
- **Evidence quality:** 4/4 rubric criteria passed with population-consistent evidence, 3 TIER 1 sources

---

## What This Agent Does

The Deduplication Engine is your CRM's duplicate detective and cleanup crew. It scans your contact, lead, and account databases to find records that represent the same person or company—even when names, emails, or phone numbers are slightly different. Using fuzzy-matching algorithms (Jaro-Winkler for names, Metaphone for phonetic variants), it scores each potential match on a 0–100 confidence scale, ranks them by likelihood, and proposes intelligent merges while flagging risky ones for manual review. You get a detailed report showing which records will merge, what data will be preserved or lost, and exactly why each merge is safe or risky.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your CRM connection, confirm required data exists, assess data quality, and ask you to scope your dedup run.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: export contacts to CSV for analysis, or help you troubleshoot the MCP connection.
- **If successful:** Proceed to Step 2.

**Step 2: Required Data Validation**
I'll verify that your Contact/Lead objects have these minimum fields:
- Email, Phone, FirstName, LastName (on Contact and/or Lead)
- Account/Company object for company-level matching
- CreatedDate, LastModifiedDate (for master record selection)

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ 1–2 fields missing → Partial results possible; I'll flag the limitation and proceed with available data
- ✗ Core fields missing (e.g., no Email or Phone at all) → No-go; request data enrichment first

**Step 3: Data Quality Assessment**
I'll calculate:
- % of records with valid emails (should be >50% for meaningful dedup)
- % of records with valid phone numbers (should be >30%)
- Data freshness (when records were last modified; >6 months stale = warning)
- Current estimated duplicate rate (sample ~1,000 records; extrapolate to full set)

**Step 4: Define Your Dedup Scope**
Before running the analysis, I'll ask:
- "Do you want to deduplicate ALL contacts and leads, or a pilot set (e.g., created in last 90 days, specific accounts, specific regions)?"
- "Do you want analysis-only mode (I show you duplicates and recommendations, but don't merge), or analysis + approval (I show you, you approve, then I merge)?"
- "Any accounts or record types you want to exclude (e.g., do not touch executive contacts, do not merge parent/child accounts)?"

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Contact + Lead objects present with required fields
✓ Email data quality: 94% valid (47,000 / 50,000)
✓ Phone data quality: 78% valid (39,000 / 50,000)
⚠️ Data freshness: 5% of records >6 months old (acceptable)
✓ Estimated duplicate rate: 1.5–2.5% based on sample
✓ Ready to proceed

Scope: All 50,000 Contact + Lead records | Analysis-only mode | No exclusions

Next step: Analyzing 50,000 records for duplicates...
```

---

## Step-by-Step Workflow

### Step 1: Fetch Records from CRM (in batches)

**What I'll do:**
- Query Contact object: all records or your filtered subset (up to 50K per batch)
- Query Lead object (Salesforce) or Lead-type Contacts (HubSpot)
- Query Account/Company records linked to matched contacts
- Fetch optional Activity data (last 90 days) for engagement scoring

**Batch Strategy:** Fetch in 1,000-record increments to respect API rate limits.

**Data I need from each record:**
- `Id`, `Email`, `Phone`, `FirstName`, `LastName`, `Company` (required)
- `CreatedDate`, `LastModifiedDate`, `Account/Company ID` (for master selection)
- `MailingCity`, `MailingCountry`, `Industry` (for tie-breaking)
- Activity count (calls, emails, meetings in last 90 days)

**What you'll see:** Progress indicator ("Fetched 1,000 / 50,000 records...").

---

### Step 2: Prepare Data (Normalize & Validate)

**Name Normalization:**
- Trim whitespace, convert to lowercase for comparison
- Remove prefixes: "Mr.", "Dr.", "Ms." (but preserve for display)
- Split FirstName + LastName (handle "John Smith" vs. "Smith, John")
- Handle common nicknames (optional mapping file in references/)

**Email Validation:**
- Basic format check (contains @, domain valid)
- Normalize: lowercase, trim, remove dots before @ (Gmail quirk)
- Flag invalid emails; exclude from email-matching phase

**Phone Normalization:**
- Remove non-digits, preserve country code
- Format as `[country]-[area]-[number]` (e.g., `1-415-555-0100`)
- Recognize extensions; note but don't match on them

**Phonetic Encoding:**
- Generate Metaphone code for FirstName and LastName (one-time calculation)
- Store in memory for Step 3

**Build Lookup Tables:**
- Email → Contact ID (for O(1) email-match lookup)
- Phone → Contact ID (for O(1) phone-match lookup)
- Company → Contact IDs (for company validation)

---

### Step 3: Generate Candidate Pairs (Matching)

I'll use a multi-strategy approach to find duplicates:

**Strategy 1: Exact Email Match**
- Iterate through email index; flag any email appearing >1 time
- Confidence: 95% (email is nearly unique)
- Example: `person@example.com` appears in Contact ABC and Contact XYZ → candidate pair

**Strategy 2: Exact Phone Match**
- Iterate through phone index; flag any phone appearing >1 time
- Confidence: 92% (phone is strong signal but can be shared)
- Example: `+1-415-555-0100` appears in Contact ABC and Lead XYZ → candidate pair

**Strategy 3: Fuzzy Name Match (Jaro-Winkler ≥ 0.85)**
- For each Contact, compare first + last name against all others using Jaro-Winkler algorithm
- Threshold: 0.85 (85% similarity)
- Examples:
  - "John Smith" vs. "Jon Smith" = 0.92 JW → candidate
  - "Jane Doe-Smith" vs. "Jane Smith" = 0.88 JW → candidate
  - "John Smith" vs. "John Jones" = 0.75 JW → rejected

**Strategy 4: Phonetic Name Match (Metaphone)**
- Generate Metaphone code for each name component
- Flag if FirstName phonetics match AND LastName phonetics match
- Examples:
  - "Stephen Smith" vs. "Steven Smith" (STFN = STFN) → candidate
  - "Smythe, John" vs. "Smith, John" (X = X) → candidate

**Strategy 5: Company + Name Match**
- If name similarity ≥ 0.85 AND company matches (exact or fuzzy), boost confidence
- If company mismatch, reduce confidence (likely different people despite similar names)

**Output: Candidate Pair List**
- Build list of all pairs meeting thresholds
- Store: Record A ID, Record B ID, matching signals, preliminary confidence estimate

---

### Step 4: Score Each Pair (Weighted Confidence Formula)

For each candidate pair, calculate final confidence:

```
Confidence = (
  email_signal × 0.35 +
  phone_signal × 0.35 +
  name_signal × 0.20 +
  company_signal × 0.10
) × 100
```

**Where:**
- `email_signal`: 1.0 (exact), 0.5 (fuzzy close), 0 (no match)
- `phone_signal`: 1.0 (exact), 0.5 (partial), 0 (no match)
- `name_signal`: Jaro-Winkler score if ≥ 0.85, else 0
- `company_signal`: 1.0 (exact match), 0.5 (email domain match), 0 (mismatch)

**Examples:**
| Scenario | Email | Phone | Name | Company | Score |
|----------|-------|-------|------|---------|-------|
| john.smith@acme vs jon.smith@acme + same phone | 0.95 | 1.0 | 0.92 | 1.0 | 96% |
| jane@corp1 vs jane@corp2 + same name + diff company | 1.0 | 0 | 0.90 | 0 | 53% → reject |
| phone match only, different names | 0 | 1.0 | 0 | 0 | 35% → reject |

---

### Step 5: Apply Thresholds & Filter Pairs

**Confidence Tiers:**

| Confidence | Recommendation | Action |
|---|---|---|
| **95–100%** | Safe to auto-merge | Pre-approved for merge |
| **85–94%** | Review recommended | Flagged for user approval |
| **70–84%** | Manual review required | Requires sales rep confirmation |
| **<70%** | Do not merge | Discarded; too risky |

**False Positive Detection:**
- Flag common names with different companies (e.g., John Smith at Acme vs. John Smith at Microsoft)
- Flag records from different time periods or geographies without additional confirmation
- Flag cross-object matches (Contact to Lead) if email domains differ

---

### Step 6: Select Master Record (Decision Tree)

For each candidate pair, I'll determine which record to keep (master) and which to delete (duplicate).

**Decision Priority:**

1. **Verified Email?**
   - If Record A has verified email and Record B doesn't → A is master
   - If both verified or both unverified → proceed to next criterion

2. **Verified Phone?**
   - If Record A has verified phone and Record B doesn't → A is master

3. **Activity Count (last 90 days)?**
   - Record with ≥10 activities vs. <5 → higher activity = master (more engaged = primary contact)
   - If similar counts → proceed to next criterion

4. **Creation Date?**
   - Older record (30+ days difference) = likely more complete → older is master
   - If similar age → proceed to next criterion

5. **Completeness Score?**
   - % of fields filled: A has 85%, B has 70% → A is master
   - If similar → proceed to last criterion

6. **Last Modified Date (Tiebreaker)?**
   - Newer record likely has more recent data → newer is master

**Field-Level Merge Rules:**

For each field in the master record, I'll decide: keep master's value, copy from duplicate, or concatenate (for notes/history)?

- **Empty field in master, duplicate has value** → Copy duplicate's value (fills gap)
- **Both have values, identical** → No change (consistent)
- **Both have values, different** → Keep master's value; log conflict
- **Multi-line fields (Notes, Description)** → Concatenate with date stamp (preserve history)
- **Special handling:** Activity links, related records—reassign all to master

---

### Step 7: Generate Output Report

**Markdown Report with:**

**Summary**
- Total records analyzed
- Duplicate pairs found
- Estimated dedup rate (%)
- Overall average match confidence

**Details**
- Distribution table (how many pairs at 95–100%, 85–94%, etc.)
- Top 10 flagged pairs requiring manual review
- Master record selection logic (why each pair's master was chosen)
- Merge impact (contacts preserved, deleted, opportunities consolidated, data loss %)

**Data Quality & Limitations**
- Assumptions (email = primary identifier, names in FirstName+LastName format, etc.)
- Data gaps (% without email, % without phone) and impact
- Known limitations (can't detect career changers without enrichment, international character handling, etc.)
- Confidence degradation factors (common names, sparse data, etc.)

**Recommended Actions**
1. Review high-confidence pairs (95–100%)
2. Manual review for medium-confidence (85–94%)
3. Decide on low-confidence pairs (70–84%): merge, enrichment, or skip
4. Approve master record selection criteria
5. Handle orphaned records post-merge
6. Schedule next step (Field Normalization)

**Sources & Citations**
- CRM data pulled [timestamp]
- Jaro-Winkler threshold 0.85 per industry benchmarks
- Activity count sourced from Task/Event objects (90-day window)

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

**Matching Thresholds:**
- "What's your minimum confidence threshold? (Default: 85%)"
  - Conservative: 90% (fewer false positives, more false negatives)
  - Balanced: 85% (recommended)
  - Aggressive: 80% (catches more duplicates, more manual review needed)

**Field Weights:**
- "Should I prioritize email, phone, or name equally?" (Default: email 35%, phone 35%, name 20%, company 10%)
  - Email-heavy: 0.50 / 0.25 / 0.15 / 0.10 (if your org has clean email data)
  - Phone-heavy: 0.25 / 0.50 / 0.15 / 0.10 (if phone data is your strongest signal)

**Merge Preferences:**
- "Auto-merge pairs above 95% confidence? (Default: Yes, with logging)"
- "Prefer which master record: older_record (default), most_complete, or most_recent?"

**Scope Filters:**
- "Limit to specific accounts? Specific date range? Record types?" (Default: all)

**Compliance Mode:**
- "Enable GDPR audit logging?" (Default: Yes)
- "Enable HIPAA mode?" (Adds extra checks for healthcare data)

---

## Error Handling

**If MCP connection fails:**
- Offer to work with CSV export instead (slower but works offline)
- Provide troubleshooting steps for the MCP (API key, permissions, org ID)

**If required data is missing:**
- Continue with available data; flag limitations in report
- Example: No email data → can only match on phone + name (confidence drops to ~70%)

**If data quality is too low:**
- >80% missing email/phone → Proceed with caution; flag high false-positive risk
- 50–80% missing → Degraded results; recommend enrichment before dedup
- <50% useful data → Recommend enriching data first (ZoomInfo, Clay, etc.)

**If API rate limits are hit:**
- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (500 records instead of 1,000)
- Split into multiple runs (analyze different date ranges separately)

---

## What to Run Next

After deduplication is complete:

1. **DQH-02: Field Normalization Agent** — Standardize company names, job titles, industries across the deduplicated records.

2. **DQH-04: CRM Health Score Agent** — Measure data quality improvement; establish baseline for ongoing health monitoring.

3. **Schedule Recurring Dedup Runs** — Set up monthly or quarterly dedup scans to catch new duplicates from integrations and manual data entry.

---

## Example: End-to-End Dedup Session

**You:** "Find duplicate contacts in my Salesforce and show me what would happen if we merged them."

**Me (Preflight):**
```
✓ Salesforce MCP connected
✓ Contact + Lead objects ready
✓ Email quality: 92% valid
✓ Phone quality: 81% valid
✓ Analyzing 35,000 contacts + 8,000 leads = 43,000 records total
```

**You:** "Start with all records. Show me everything; don't merge anything yet."

**Me (Analysis):**
```
Scanning for duplicates...
✓ Found 342 email-exact matches (95% confidence)
✓ Found 156 phone-exact matches (92% confidence)
✓ Found 287 fuzzy name matches (88–91% confidence)
Total candidate pairs: 847

Scoring and filtering...
✓ 621 pairs at 95%+ confidence (safe auto-merge)
✓ 201 pairs at 85–94% confidence (review recommended)
✓ 25 pairs at 70–84% confidence (manual review required)

Determining master records...
✓ Master selection criteria applied
✓ Data loss calculated for each merge
✓ Compliance flags checked (GDPR safe)
```

**Report (Markdown + JSON):**
- Summary: "847 duplicates found (2% of 43K records). Recommended merges will reduce database to 42,153 unique records while preserving 94% of engagement history."
- Details table showing top 10 flagged pairs, why they're risky, what sales ops team should do
- Master record selection: "Maria Garcia / Contact vs. Lead: Contact chosen (older, more activities, verified email); Lead's LeadSource='Webinar' will be copied to Contact"
- Data quality: "Email addresses are strong signal; phone data is clean; identified 847 probable duplicates with high confidence"

**You:** "This looks good. Approve the 621 high-confidence merges. I want to manually review the 201 medium-confidence ones before we touch them."

**Me:** "Executing 621 merges... [batch operation] ✓ Complete. 621 records merged; 42,532 unique contacts remain. Review report for low-confidence pairs; send me approval when ready."

---

## References & Further Reading

**Detailed Files** (in `references/` folder):
- `nickname_mapping.md` — Common first-name variants (Jon/John, Jane/Jean, etc.)
- `company_variants.md` — Common company name variants (Inc., Ltd., Corp., etc.)
- `international_characters.md` — Handling non-Latin names and accents
- `merge_scenarios.md` — Real-world examples of tricky merges (parent/child accounts, career changers, etc.)

