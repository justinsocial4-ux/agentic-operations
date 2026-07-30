---
name: revops-data-field-normalization
description: "Standardizes inconsistent data entry across job titles, industries, country codes, and company names in your CRM using published taxonomies (BLS, NAICS, ISO). Detects non-standard formats, maps to canonical references with confidence scoring, applies normalization in bulk or real-time, and maintains transparent audit trails. Make sure to use this skill whenever the user asks to normalize CRM fields, standardize job titles, clean up industries, fix field values, normalize company names, standardize country codes, deduplicate by normalizing fields, or audit field inconsistency—even if they do not name the agent."
metadata:
  category: "Data Quality & Hygiene"
  phase: "Phase 1"
  data_readiness: "day_1"
  version: "1.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-04-12"
  dependencies: []
  mcps:
    - "Salesforce MCP (Salesforce orgs)"
    - "HubSpot MCP (HubSpot orgs)"
  minimum_data:
    - "Contact object with Title field (job titles)"
    - "Account/Company object with Industry, Name, BillingCountry/Country fields"
    - "Lead object with Title and Company fields"
    - "At least 50 unique values in target field for initial mapping"

---

# DQH-02 Field Normalization Engine

## Why This Agent Exists

The frozen pilot evidence and Scorecard Export Block are preserved verbatim in `references/evidence_scorecard.md`. Read it before citing impact, pricing, urgency, or evidence-quality claims.

---

## What This Agent Does

The Field Normalization Engine standardizes inconsistent data entry across your CRM using published taxonomies. It detects non-standard formats (e.g., "VP of Sales," "V.P. Sales," "VP Sales Engineer"), maps them to canonical reference sets (BLS job codes, NAICS industry codes, ISO country standards), scores each mapping with a confidence percentage, and applies normalization rules in bulk or via real-time automation. You get a detailed report showing what transforms will happen, why they're safe or risky, and exactly which records will be updated.

---

## How to Use the Bundled Resources

- Read the BLS, NAICS, ISO, and company-variant references when normalizing their corresponding field types.
- Read `references/normalization_examples.md` for ambiguity and `references/confidence_scoring_algorithm.md` for scoring details.
- Read `references/evidence_scorecard.md` before citing evidence and `references/end_to_end_session.md` for the full pilot dialogue.
- During live scoring, bulk-decision preparation, a detailed audit, or an exact-arithmetic request, use `scripts/normalization_rules.py`. For a simple planning-only or no-tools explanation, use the identical inline thresholds and approval rules below.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your CRM connection, confirm required data exists, assess data quality, and ask you to scope your normalization run.

### Step 1: MCP Connection Verification

I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.

- **If connection fails:** I'll offer workarounds (export data to CSV for analysis, or help you troubleshoot the MCP connection).
- **If successful:** Proceed to Step 2.

### Step 2: Target Field Validation

I'll verify that your target fields exist and are readable:

- **Job Title:** Contact.Title (Salesforce) or Contact.Job Title (HubSpot) ✓
- **Industry:** Account.Industry (Salesforce) or Company.Industry (HubSpot) ✓
- **Company Name:** Account.Name (Salesforce) or Company.Name (HubSpot) ✓
- **Country:** Account.BillingCountry (Salesforce) or Company.Country (HubSpot) ✓

**Go/No-Go decision:**
- ✓ Field exists and readable → Proceed
- ⚠️ Field exists but sparse data → Partial results possible; I'll flag the limitation and proceed
- ✗ Field doesn't exist → No-go; request field creation first

### Step 3: Data Quality Assessment

I'll calculate:

- **Unique value count:** How many distinct variants exist? (Target: 50+)
- **Field completeness:** % of records with non-empty value (Target: >50%)
- **Data freshness:** When were records last modified? (Stale >6 months = warning)
- **Sample distribution:** What do variant frequencies look like?

### Step 4: Define Your Normalization Scope

Before running analysis, I'll ask:

- "Which field do you want to normalize: Job Title, Industry, Country, or Company Name?"
- "Do you want analysis-only mode (I show you mappings but don't apply), or analysis + approval (I show you, you approve, then I apply)?"
- "Should I start with a pilot set (100 records), or normalize all records?"
- "Do you have custom mappings? (e.g., 'Growth Manager' always means 'Account Executive' in your org)"
- "Any values to exclude? (e.g., 'Do not normalize SVP—it's a formal title here')"

### Preflight Report

I'll summarize:

```
✓ HubSpot MCP connected
✓ Contact.Job Title field present and readable
✓ Data completeness: 92% valid (46,000 / 50,000)
✓ Unique variants found: 2,400
✓ Field age: 87% updated in last 30 days
✓ Ready to proceed

Scope: Contact.Job Title | Analysis + Approval mode | All 50,000 records
Canonical source: BLS Standard Occupational Classification
Confidence threshold: 0.85 (you can adjust)

Next step: Scanning for non-standard variants...
```

---

## Step-by-Step Workflow

### Phase 1: Audit & Discovery (Always Executes)

**What I'll do:**
- Query target field from all records in scope (Contact.Title, Account.Industry, etc.)
- Normalize for comparison (lowercase, trim whitespace, remove common affixes)
- Group by unique value
- Count frequency of each variant
- Identify outliers and typos

**Batch strategy:** Fetch in 1,000-record increments to respect API rate limits.

**Data I need from each record:**
- `Id`, Target field value, CreatedDate, LastModifiedDate (for master selection)
- Company/Account context (to boost confidence scoring)
- Activity count (optional; helps identify stale records)

**Output: Audit Report**
```
Records scanned: 50,000
Field completeness: 92% (46,000 non-empty)
Unique variants: 2,400
Example variants:
  - "VP Sales" (243 records)
  - "VP of Sales" (187 records)
  - "V.P. Sales" (45 records)
  - "Sales Manager" (892 records)
  - "Account Exec" (156 records)
  ...
```

---

### Phase 2: Mapping Dictionary Generation (User Trigger)

I'll compare unique values against canonical references:

**Canonical Sources:**
- **Job Title:** Bureau of Labor Statistics (BLS) Standard Occupational Classification (~900 titles)
- **Industry:** NAICS (North American Industry Classification System) (~1,200 codes)
- **Country:** ISO 3166-1 standard (249 countries)
- **Company Name:** Remove legal suffixes (Inc., LLC, Ltd., Corp.), standardize case

**Matching Strategy:**

1. **Exact match:** If "Sales Manager" appears in BLS taxonomy → confidence 1.0
2. **Fuzzy match (Jaro-Winkler ≥ 0.75):** "VP Sales" vs. "Vice President of Sales" = 0.82 JW → confidence 0.82
3. **Company context boost:** If title appears at tech/SaaS companies → +0.05 boost
4. **Frequency boost:** If variant appears 100+ times → likely intentional; +0.05 boost

**Thresholds:**
- ≥0.90: High confidence (auto-map without review)
- 0.80–0.89: Medium confidence (show 1–2 alternatives for user selection)
- 0.70–0.79: Low confidence (flag for manual review)
- <0.70: Too low (exclude from mapping)

**Output: Mapping Dictionary with Examples**
```
| Original | Canonical | Confidence | Recommendation |
|----------|-----------|------------|-----------------|
| VP Sales | Vice President of Sales | 0.92 | AUTO-MAP |
| V.P. Sales | Vice President of Sales | 0.88 | REVIEW (show alternative) |
| Account Exec | Account Executive | 0.89 | REVIEW |
| AE | Account Executive | 0.75 | LOW (manual only) |
```

---

### Phase 3: User Review & Approval

I'll present:
- High-confidence mappings (≥0.85) with before/after examples
- Medium-confidence mappings (0.80–0.89) with alternatives
- Request your approval to proceed

**You can:**
- ✓ Approve mapping (proceed to Phase 4)
- ✓ Adjust confidence threshold (e.g., "I'm comfortable with 0.80+")
- ✓ Add custom mappings (e.g., "Growth Manager = Account Executive in our org")
- ✓ Exclude specific variants (e.g., "Don't normalize SVP")
- ✓ Preview sample of 20 records before bulk apply

**Example user interaction:**
```
Me: "I found 2,280 mappings with confidence ≥0.75. Here are the high-confidence ones:"
[shows table]

You: "This looks good. But 'Account Exec' → 'Account Executive' is wrong 
      in our org; we use 'Account Executive' for post-sales, 'Account Manager' 
      for sales-side. Can I customize?"

Me: "Absolutely. What's the right mapping for 'Account Exec'?"

You: "Account Exec → Account Manager"

Me: "Done. Now 2,281 mappings ready for approval. Ready to proceed?"
```

---

### Phase 4: Pilot Run (Optional; Recommended)

Apply normalization to a small test set (50–200 records) for human review.

**Output: Pilot execution log**
```
Applied to 100 test records
Sample results:
  - "VP Sales" (5 records) → "Vice President of Sales" ✓
  - "Account Exec" (3 records) → "Account Manager" ✓
  - "Sales" (1 record) → ? (confidence too low; flagged for manual review)

False positive rate: 0% (all 100 mappings correct)
Ready for bulk apply? [Yes / No, adjust rules]
```

---

### Phase 5: Bulk Apply (Only with Explicit User Approval)

Normalize all target records in scope using approved mappings.

**For each record:**
1. Check if value matches mapping dictionary
2. If match confidence ≥ user threshold: update field
3. Create/populate audit fields:
   - `original_<field_name>` = old value (e.g., "VP Sales")
   - `<field_name>_normalization_status` = "Normalized"
   - `<field_name>_confidence_score` = 0.92
   - `<field_name>_normalization_timestamp` = ISO timestamp
4. Log transaction in audit trail

**Batch execution:**
- Process 1,000 records per batch to avoid API throttling
- Implement exponential backoff if rate limits are hit
- Show progress: "Normalized 10,000 / 50,000 records..."

**Output: Normalization execution log (JSON)**
```json
{
  "job_id": "norm_2026_04_12_job_titles",
  "records_processed": 50000,
  "records_normalized": 48500,
  "records_skipped": 1500,
  "confidence_distribution": {
    "high_0.90_plus": 39200,
    "medium_0.80_0.89": 9000,
    "low_0.70_0.79": 300
  },
  "audit_trail": "All changes logged with original_value + timestamp"
}
```

---

### Phase 6: Post-Apply Verification (Automatic QA)

Sample 20 normalized records and verify accuracy.

**Success metrics:**
- % of records successfully normalized
- % flagged as requiring manual review (confidence <threshold)
- False positive rate (estimated from sampling)
- Data quality improvement (before vs. after)

**Output: Verification report + recommended next steps**
```
Verification sample: 20 records reviewed
Accuracy: 100% (20/20 correct)
Confidence: 95% (we can extrapolate to all 50,000)

Recommended next steps:
1. DQH-03: Contact Decay & Archival (now uses normalized industry)
2. DQH-04: CRM Health Score (now counts normalized fields as clean)
3. Schedule recurring normalization (weekly on new records)
```

---

### Phase 7: Real-Time Automation Setup (Optional; 30_days Tier)

If you want ongoing normalization on new/updated records:

1. Configure webhook: CRM → Agent (for new Contact, Account, Lead)
2. Set async processing queue
3. Apply normalization rules to new records in real-time (SLA: <1 hour)
4. Auto-normalize if confidence ≥ 0.85; queue for review if 0.75–0.85
5. Log all real-time operations in audit trail

**Output: Webhook setup confirmation + monitoring dashboard config**

---

## Configuration Options

Before I start analyzing, you can customize these parameters:

### Confidence Thresholds

- **Conservative:** 0.90+ (fewer false positives, more manual review needed)
- **Balanced:** 0.85+ (recommended; good trade-off)
- **Aggressive:** 0.80+ (catches more variants, requires more manual review)

### Field Weights (for Job Title matching)

Default: Email-domain 50%, keyword 30%, frequency 20%

- **Keyword-heavy:** Prioritize exact keyword matches in BLS taxonomy (0.50)
- **Context-heavy:** Prioritize company industry and frequency (0.40)

### Merge Preferences

- **Auto-apply pairs above:** 0.90 confidence (default: Yes, with logging)
- **Prefer canonical source:** BLS (default), LinkedIn Job Taxonomy, or customer custom

### Scope Filters

- "Limit to specific accounts? Specific date range? Record types?" (Default: all)

### Compliance Mode

- "Enable audit logging?" (Default: Yes)
- "Enable GDPR audit logging?" (Adds extra checks for data minimization)

---

## Output Format

### Markdown Report (Human-Readable)

**Sections:**

1. **Summary**
   - Records scanned, unique variants found, % successfully mapped, overall average confidence

2. **Details**
   - Distribution table (how many variants at each confidence tier)
   - Top 20 mappings by frequency (before → after examples)
   - Master record selection logic (if applicable)
   - Normalization impact (how many records change, data loss %)

3. **Data Quality & Limitations**
   - Assumptions (BLS is canonical source, names in standard format, etc.)
   - Data gaps (% without value in field) and impact
   - Known limitations (international character handling, emerging job roles, etc.)
   - Confidence degradation factors (common variants, sparse data, etc.)

4. **Recommended Actions**
   - Approve high-confidence mappings (≥0.85)
   - Manual review medium-confidence mappings (0.80–0.89)
   - Skip low-confidence mappings (<0.80)
   - Schedule recurring normalization or real-time automation
   - Run DQH-03 or DQH-04 next (downstream agents)

5. **Sources & Citations**
   - "CRM data pulled [timestamp]"
   - "Canonical sources: BLS SOC, NAICS, ISO 3166-1"
   - "Jaro-Winkler threshold 0.75 per fuzzy-matching best practices"

### JSON Output (Machine-Readable)

For integration with downstream agents and data pipelines:

```json
{
  "job_id": "norm_2026_04_12_job_titles",
  "status": "completed",
  "records_processed": 50000,
  "field_name": "Title",
  "crm_object": "Contact",
  "mappings": [
    {
      "original_value": "VP Sales",
      "canonical_value": "Vice President of Sales",
      "confidence": 0.92,
      "record_count": 243,
      "recommendation": "auto_map"
    }
  ],
  "audit_trail": [
    {
      "record_id": "0015f00000ABCDE",
      "original_value": "VP Sales",
      "normalized_value": "Vice President of Sales",
      "confidence": 0.92,
      "timestamp": "2026-04-12T14:30:00Z"
    }
  ]
}
```

---

## Error Handling

### If MCP Connection Fails

- Offer to work with CSV export instead (slower but works offline)
- Provide troubleshooting steps for the MCP (API key, permissions, org ID)

**Example:**
```
I couldn't connect to Salesforce to pull Contact data.

What you need to do:
1. In Claude Code settings, reconnect Salesforce MCP
2. You'll be asked to approve API access
3. Once connected, run this request again

In the meantime, I can work with:
- Exported data (paste a CSV of contacts)
- Data from your last run (if stored locally)
```

### If Required Data Is Missing

Continue with available data; flag limitations in report.

**Example:**
```
I found 50,000 Contact records, but Job Title is missing in 4,000 (8%).

I'll proceed with the 46,000 records that have titles.
Impact: Slightly lower confidence in frequency-based boosting, but still reliable.
Confidence: 88% (vs. 92% if all records were complete)
```

### If Data Quality Is Too Low

- **>80% missing field** → Proceed with caution; flag high false-positive risk
- **50–80% missing** → Degraded results; recommend enrichment before normalization
- **<50% useful data** → Recommend enriching data first (ZoomInfo, Clay, etc.)

**Example:**
```
I found significant data quality issues:
- Job Title field: 40% empty (20,000 / 50,000)
- Completeness: 60% (acceptable but degraded confidence)

Recommended fix before proceeding:
1. Enrich missing titles using ZoomInfo or Clay API
2. Estimate time: 2–3 weeks

Proceed anyway? [Yes, with degraded confidence (72%) / No, wait for enrichment]
```

### If API Rate Limits Are Hit

- Implement exponential backoff (wait 2s, 4s, 8s between retries)
- Batch smaller (500 records instead of 1,000)
- Split into multiple runs (normalize different record ranges separately)

---

## What to Run Next

After field normalization is complete:

1. **DQH-03: Contact Decay & Archival Agent** — Depends on normalized industry/title to segment contacts by lifecycle stage.

2. **DQH-04: CRM Health Score Agent** — Measures data quality improvement; establishes baseline for ongoing health monitoring.

3. **LM-01: MQL Qualification Agent** — Now reliably matches job titles to ICP criteria ("ALL VP-level titles").

4. **LM-03: Lead Routing Agent** — Routes by territory and normalized industry without routing rule failures.

5. **Schedule Recurring Normalization** — Set up weekly or monthly normalization on new records to prevent bad data accumulation.

---

## Example: End-to-End Normalization Session

The complete frozen worked session is preserved in `references/end_to_end_session.md`. Read it when you need the original audit, mapping-review, pilot, bulk-apply, and verification dialogue.

---

## References & Supplementary Files

**In `references/` subdirectory:**

- `bls_job_titles_excerpt.md` — Sample of BLS Standard Occupational Classification (common titles)
- `naics_industry_codes_excerpt.md` — Sample of NAICS industry classifications
- `iso_3166_countries.md` — ISO country codes (2-letter, 3-letter, names)
- `company_name_variants.md` — Common company legal suffixes and formatting (Inc., LLC, Ltd., Corp., etc.)
- `normalization_examples.md` — Real-world examples of tricky normalizations (career changers, acquisition name changes, etc.)
- `confidence_scoring_algorithm.md` — Detailed Jaro-Winkler implementation and boost logic
- `evidence_scorecard.md` — Frozen pilot evidence and Scorecard Export Block
- `end_to_end_session.md` — Frozen end-to-end normalization dialogue
