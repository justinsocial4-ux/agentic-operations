# End-To-End Enrichment Example

Read this when the user asks for a full sample run. This is the pilot example moved intact for progressive disclosure; only the fake organization identifier is replaced with a public-safe placeholder.

**You:** "Enrich our contacts with missing emails and phone numbers. Use whatever providers we have."

**Me (Preflight):**
```text
✓ Salesforce connected (Org: EXAMPLE_ORG_ID)
✓ Enrichment providers: ZoomInfo, Apollo, Clearbit active
⚠️ Cleanlist not connected (would improve email accuracy from 82% to 98%)
✓ Budget available: ZoomInfo $1,200, Apollo $1,500, Clearbit $600
✓ Contact records: 12,500 total | 3,100 missing email | 2,400 missing phone
✓ Lead records: 4,200 total | 1,200 missing email | 900 missing phone
✓ Total enrichment candidates: 7,600 records

Estimated cost: ~$4,500 (multi-source waterfall)
Ready to begin? [Yes / Adjust]
```

**You:** "Go ahead. Prioritize email, and let me know if costs spike."

**Me (Analysis & Routing):**
```text
Assessing 7,600 records for missing fields...
✓ Missing field scores calculated (0–100)
  - 2,100 HIGH priority (>70)
  - 3,200 MEDIUM priority (50–70)
  - 2,300 LOW priority (<50)

Mapping provider capabilities...
✓ HIGH priority records → Cleanlist if budget allows, else Apollo
✓ MEDIUM priority → Apollo / Clearbit
✓ LOW priority → Cheapest available (Cognism or Apollo)

Executing enrichment calls...
✓ Batch 1: 1,000 records to ZoomInfo — COMPLETE (Cost: $520)
✓ Batch 2: 1,500 records to Apollo — COMPLETE (Cost: $180)
✓ Batch 3: 1,200 records to Clearbit — COMPLETE (Cost: $300)
[... continuing batches ...]

Running total: $4,200 of $4,500 budget (93% used)

Consolidating results...
✓ 6,800 records enriched successfully
✓ 400 records "not found" by any provider
✓ 400 records enriched with partial data (phone but not email)

Conflict resolution:
✓ 340 email conflicts detected → Resolved using provider accuracy hierarchy
✓ Average confidence score: 89%

Writing back to CRM...
✓ 6,800 records updated with enriched email/phone
✓ Confidence scores and sources logged
```

**Final Report:**
```text
ENRICHMENT COMPLETE

Records processed: 7,600
Records successfully enriched: 6,800 (89%)
Records partially enriched: 400 (5%)
Records not found: 400 (5%)

COVERAGE IMPROVEMENTS
Email: 9,400 → 13,100 records (78% → 82%) | +3,700 records | Cost: $2,200
Phone: 10,100 → 12,200 records (81% → 87%) | +2,100 records | Cost: $1,800

COST SUMMARY
ZoomInfo: $1,850 (41%)
Apollo: $1,400 (31%)
Clearbit: $1,200 (27%)
TOTAL: $4,450 (vs. budget $4,500)

CONFIDENCE METRICS
Average confidence: 89%
Email fields >90% confidence: 92%
Phone fields >90% confidence: 85%

NEXT STEPS
1. Monitor email deliverability over next 7 days (should improve from 82% to 95%+)
2. Identify which enriched accounts have highest revenue potential (use health score next)
3. Schedule re-enrichment in 30 days (data decay cycle)

Full report: [link to detailed breakdown by provider, field, confidence tier]
```
