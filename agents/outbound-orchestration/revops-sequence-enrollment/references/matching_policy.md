# Matching Policy

Use a versioned customer mapping and library. Each sequence needs stable ID, name, active state/dates, workspace/team, target persona IDs, vertical IDs, engagement IDs, integer priority, and explicit wildcard permissions.

Normalize case and whitespace only. Map exact approved aliases; do not fuzzy-match job titles or infer seniority/authority. Missing dimensions stay unknown.

Match every required dimension. Select the unique lowest-priority-number match only when the customer defines that ordering. A tied best priority returns `AMBIGUOUS_MATCH`. No match returns `NO_MATCH`; do not silently route to a generic sequence.
