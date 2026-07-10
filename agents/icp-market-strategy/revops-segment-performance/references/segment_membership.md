# Segment Membership

Read this file before assigning, overlapping, combining, or comparing segments.

- Require stable segment IDs, labels, definition-receipt IDs, definition version, and membership evidence.
- Do not fuzzy-match, auto-bin, substitute revenue for employees, infer quartiles from the analyzed outcomes, or choose a “most specific” segment.
- `EXCLUSIVE` requires exactly one segment for every included opportunity.
- `OVERLAPPING` permits multiple supplied memberships but blocks cross-segment totals, shares, rankings, and selections because one opportunity can appear more than once.
- A changed segment definition or membership policy creates a new comparison basis. Never compare as though membership were unchanged.
- Preserve unassigned and unknown memberships as exceptions; do not create an “other” cohort unless the policy explicitly defines one.
