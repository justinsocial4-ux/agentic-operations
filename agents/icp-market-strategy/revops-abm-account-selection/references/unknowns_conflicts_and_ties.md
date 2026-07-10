# Unknowns, Conflicts, And Ties

- Any unresolved identity, eligibility, score, score-policy match, evidence cutoff, or required segment can change the result. Return `CANDIDATE_EVIDENCE_REVIEW_REQUIRED` and no final selection.
- A score tie matters only when it crosses a slot boundary. Return `BOUNDARY_TIE_REVIEW_REQUIRED`, the accounts certainly above the boundary, the full tied set, and the unresolved slot count.
- Do not break a boundary tie by account name, ID, input order, enrichment recency, seller activity, model preference, or randomness.
- Ties wholly inside a selected set or wholly outside it do not change membership. Preserve equal scores and avoid inventing rank order among them.
- Do not treat missing activity as low intent, missing fit as neutral, missing segment as `Other`, or conflict as the newest source winning.
