# Output Contract

Use this file before producing the full report or transaction log.

## Markdown Report

```markdown
## Lead-to-Account Matching Report
**Generated:** [timestamp]
**Scope:** [all unassociated leads | date/source filter]

### Summary
- Leads processed: [count]
- HIGH matches: [count and percent]
- MEDIUM matches: [count and percent]
- LOW/no-good-candidate: [count and percent]
- Write mode: [read-only | approved execution]

### HIGH-Confidence Matches
[Lead ID | Company | Matched Account | Exact Score | Component Scores | Recommended Action]

### MEDIUM-Confidence Review Queue
[Lead ID | Company | Candidate | Exact Score | Missing/Conflicting Evidence | Priority]

### LOW-Confidence Manual Lookup
[Lead ID | Company | Top Candidate | Exact Score | Why Low | Next Step]

### Expansion/Hierarchy Routing
[Lead ID | Subsidiary | Parent | Motion | Owner Routing | Hierarchy Freshness]

### Data Quality and Limitations
- missing company/email counts
- hierarchy availability/freshness
- skipped records and reasons
- assumptions and confidence degradations
```

Do not include pipeline-recovery dollars unless the customer supplies a validated baseline and conversion model.

## JSON Transaction Log

```json
{
  "run_id": "LM-02-EXAMPLE-001",
  "timestamp": "2026-04-13T14:23:45Z",
  "scope": "unassociated_leads",
  "write_mode": "read_only",
  "matches": [
    {
      "lead_id": "EXAMPLE_LEAD_ID",
      "lead_company": "Acme Corp.",
      "matched_account_id": "EXAMPLE_ACCOUNT_ID",
      "matched_account_name": "Acme Corporation",
      "confidence_score": 94.3,
      "confidence_bucket": "HIGH",
      "components": {
        "name_similarity": 0.92,
        "domain_match": 1.0,
        "employee_count_match": 1.0,
        "location_match": 1.0,
        "phonetic_match": 0.5
      },
      "recommended_action": "AUTO_ASSOCIATE_AFTER_APPROVAL",
      "hierarchy_parent_id": null,
      "status": "PROPOSED"
    }
  ],
  "summary": {
    "total_leads": 1,
    "high_confidence": 1,
    "medium_confidence": 0,
    "low_confidence": 0,
    "errors": 0
  }
}
```

## Execution Receipt

For an approved write run, add approver, approval timestamp, attempted/succeeded/failed counts, per-record error, retry state, reconciliation sample result, and final status. Never mark a proposal as written without a successful CRM response.
