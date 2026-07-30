# Failure states

Apply unresolved precedence in this order:

1. `UNAUTHORIZED`
2. `SUPPRESSED`
3. `EVIDENCE_CONFLICT`
4. `EVIDENCE_MISSING`

Otherwise, an unknown or incompatible supplied route, owner, channel, authorization window, or planned time is `CUSTOMER_EVENT_PLAN_EVIDENCE_NOT_MATCHED`; every participant must match for review-level `CUSTOMER_EVENT_PLAN_EVIDENCE_MATCHED`. Never substitute a default route, owner, channel, timestamp, recipient, cached record, generic ICP, enrichment result, score, tier, or fallback.
