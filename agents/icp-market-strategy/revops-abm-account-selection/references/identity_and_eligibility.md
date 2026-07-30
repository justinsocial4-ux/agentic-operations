# Identity And Eligibility

- Accept cohort membership only when `population_membership_status=VERIFIED_MEMBER` and a traceable receipt ID is present. Any other state blocks the declared population.
- Accept identity for ranking only when `identity_status=RESOLVED` at the declared legal-account level.
- Treat `AMBIGUOUS`, `CONFLICT`, and `UNKNOWN` identity as review-required. Do not merge parents, subsidiaries, domains, or aliases without the approved identity policy.
- Accept eligibility for ranking only when `eligibility_status=VERIFIED_ELIGIBLE`.
- Exclude `VERIFIED_INELIGIBLE` with its receipt; it does not block other candidates.
- Treat `UNKNOWN` and `CONFLICT` eligibility as review-required because the account could change the selected set.
- Keep current-target, suppression, territory, contractual, capacity, customer, partner, sanctions, and other eligibility rules in the customer policy. Do not infer them from score or activity.
- Validate the evidence cutoff before using even a verified-ineligible state; stale or future evidence cannot safely exclude an account.
