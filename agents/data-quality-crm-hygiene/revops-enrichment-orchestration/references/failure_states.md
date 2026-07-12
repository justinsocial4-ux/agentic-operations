# Failure states

Apply unresolved precedence in this order:

1. `UNAUTHORIZED`
2. `SUPPRESSED`
3. `EVIDENCE_CONFLICT`
4. `EVIDENCE_MISSING`

Otherwise, any unsupported, expired, or unknown supplied provider assignment is `CUSTOMER_ROUTE_EVIDENCE_NOT_MATCHED`; every route must match for review-level `CUSTOMER_ROUTE_EVIDENCE_MATCHED`. Never substitute a default provider, price, field, route, cached value, or fallback.
