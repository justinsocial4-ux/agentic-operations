## Example: End-to-End Normalization Session

**You:** "Normalize job titles in my HubSpot. We have a mess of variations like 'VP Sales,' 'V.P. Sales,' 'VP - Sales' and I need them standardized."

**Me (Preflight):**
```
✓ HubSpot MCP connected
✓ Contact.Job Title field ready
✓ Data completeness: 92% (46,000 / 50,000 non-empty)
✓ Unique variants found: 2,400
✓ Field freshness: 87% updated in last 30 days

Ready to analyze. Would you like:
A) Analysis only (show me mappings, no changes)
B) Analysis + Approval (show mappings, I wait for your OK before applying)
C) Pilot + Approval (test on 100 records first, then bulk apply)

Which would you prefer?
```

**You:** "Let's do pilot + approval. I want to see samples before we touch the whole database."

**Me (Audit & Mapping):**
```
Scanning for non-standard variants...
✓ Found 2,400 unique job title variants in 50,000 records
✓ Top variants:
  - "VP Sales" (243 records) → "Vice President of Sales" (0.92 confidence)
  - "VP of Sales" (187 records) → "Vice President of Sales" (0.95 confidence)
  - "V.P. Sales" (45 records) → "Vice President of Sales" (0.88 confidence)
  - "Sales Manager" (892 records) → "Sales Manager" (1.00 confidence)
  - "Account Exec" (156 records) → "Account Executive" (0.89 confidence)
  - "AE" (73 records) → "Account Executive" (0.75 confidence — LOW)

High-confidence mappings: 2,050 (85%)
Medium-confidence mappings: 320 (13%)
Low-confidence mappings: 30 (2%)

Ready for pilot?
```

**You:** "Yes, run the pilot on 100 records. But I want to review that 'AE' mapping first. In our org, AE is Account Executive in sales, but sometimes it's used loosely. Can you be more conservative?"

**Me:** "Got it. I'll exclude 'AE' from auto-mapping for now. If it comes up in the pilot, I'll flag it for your decision. Running pilot on 100 records..."

**Pilot Results:**
```
Normalized 100 test records
Sample results:
  - "VP Sales" (5 records) → "Vice President of Sales" ✓
  - "Account Exec" (3 records) → "Account Executive" ✓
  - "Sales" (1 record) → [confidence 0.65, TOO LOW, flagged for review]

False positive rate: 0% (all 100 mappings correct)

One low-confidence record found: "Sales" — likely typo or incomplete data.
Recommendation: Skip this record; manually review in CRM.

Ready for bulk apply? [Yes / No, adjust rules]
```

**You:** "Looks great. Apply to all 50,000 records."

**Me (Bulk Apply & Verification):**
```
Executing bulk normalization...
✓ Processed 50,000 records in 12 batches
✓ Successfully normalized 48,500 records
⚠️ Skipped 1,500 records (confidence below threshold)

Verifying results (sampling 20 records)...
✓ 20/20 correct (100% accuracy)
✓ False positive rate: 0% (estimated)

Done! Here's what changed:
- 48,500 records normalized to 120 canonical job titles
- Audit trail created (original_Job_Title field populated with old values)
- Data quality improved by ~15% (before: 92% clean, after: 98% clean)

Next steps:
1. Review the 1,500 skipped records at your discretion
2. Run DQH-04 (CRM Health Score) to validate improvement
3. Set up weekly normalization on new records? [Yes / No]
```

---
