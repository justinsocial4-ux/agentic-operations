# Scope And Policy

The helper performs one `DEAL_EVIDENCE_REVIEW` over one complete frozen deal population. Require stable policy ID/version, owner, reviewer, effective date, UTC cutoff, timezone, source/schema/history semantics, stage policy, amount basis, activity policy, thresholds, privacy/workforce approvals, correction path, and prohibited uses.

The policy defines exact open and terminal stage IDs plus optional per-stage elapsed-day thresholds and one activity elapsed-day threshold. Threshold results are review states, not risk or prediction labels.

The output is evidence for human review only. It cannot authorize a forecast, deal, seller, workforce, or system action.
