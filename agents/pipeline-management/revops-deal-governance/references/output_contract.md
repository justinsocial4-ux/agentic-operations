# Output contract

The helper returns one JSON document with review type, neutral overall state, policy receipt, population receipt, numeric receipts, per-deal rule results, unresolved reasons, and the fixed final boundary.

All numeric facts and thresholds appear only in dedicated helper-owned receipts. Rule results refer to receipt IDs rather than repeating values. The model must return helper stdout byte for byte and add nothing. The response begins with `{`, ends with the helper newline after `}`, and has no Markdown fence.

Allowed states include `REVIEW_READY`, `POLICY_REQUIRED`, `SOURCE_REQUIRED`, `POPULATION_CONFLICT`, `EVIDENCE_CONFLICT`, `RULE_MATCHED`, `RULE_NOT_MATCHED`, `NOT_EVALUABLE`, `DOCUMENT_REVIEW_REQUIRED`, and `HUMAN_APPROVAL_REQUIRED`. Do not add qualitative adequacy, confidence, risk, severity, compliance, approval, or recommendation labels.
