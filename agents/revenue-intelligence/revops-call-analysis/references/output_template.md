# Output Template

```markdown
# Call Evidence Review

## 1. Scope And Policy Receipt
- Call/source/cutoff:
- Purpose/audience:
- Policy IDs/versions/owner:
- Requester access:
- Redaction/retention/downstream-use rules:
- Status:

## 2. Transcript Quality Receipt
| Duration ms | Covered ms | Coverage | Uncovered ms | Overlap ms | Uncertain ms | Redacted ms | Language/version |
|---:|---:|---:|---:|---:|---:|---:|---|

## 3. Speaker Receipt
| Speaker ID | Mapping status/source/reviewer | Segment ms | Share of segment time | Limits |
|---|---|---:|---:|---|

## 4. Evidence Table
| Annotation | Category | Review state | Segment/time | Speaker | Exact quote | Rule version | Reviewer | Limits/conflicts |
|---|---|---|---|---|---|---|---|---|

## 5. Descriptive Metrics
| Metric | Numerator | Denominator | Value | Definition | Interpretation limit |
|---|---:|---:|---:|---|---|

## 6. Unknowns And Prohibited Conclusions
- Unknown/missing evidence:
- Contradictions:
- This review does not establish:

## 7. Human Review Preview
- Named reviewer:
- Proposed downstream use:
- Required separate approval:
- Approval state:
- Boundary: NO CRM WRITE / NO TASK / NO MESSAGE / NO EMPLOYMENT OR DEAL DECISION
```

Use failure-state tokens exactly. Keep direct evidence, tags, CRM context, interpretations, and unknowns in separate fields.
