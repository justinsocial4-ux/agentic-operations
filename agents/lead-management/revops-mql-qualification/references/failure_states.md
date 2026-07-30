# Failure states

- `EVIDENCE_MISSING`: a required observation is explicitly missing.
- `EVIDENCE_CONFLICT`: approved evidence disagrees.
- `SUPPRESSED`: policy or rights handling suppresses the evidence.
- `UNAUTHORIZED`: the evidence is not authorized for this purpose.
- `CUSTOMER_POLICY_CONDITIONS_NOT_MET`: complete authorized evidence does not satisfy the frozen condition set.
- `CUSTOMER_POLICY_CONDITIONS_MET`: complete authorized evidence satisfies the frozen condition set.

Structural defects, incomplete populations, unknown fields, invalid timestamps, stale authorization, or mismatched receipts reject the entire document instead of producing a partial review.
