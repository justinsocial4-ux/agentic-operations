# Policy And Candidate Contract

## Policy

Require `policy_id`, `version`, `owner`, `effective_date`, `candidate_population_id`, `candidate_population_receipt_id`, `candidate_population_status`, `candidate_count`, timezone-aware `cutoff`, `purpose`, `entity_level`, `capacity`, `reviewer`, `action_approval_status`, `proposed_use`, `records_system`, `reversal_path`, `score_policy_id`, and `score_policy_version`.

Allow only preview purposes `NEW_ADDITIONS_PREVIEW` and `FULL_REFRESH_PREVIEW`; require `legal_account` entity level. Require the policy to be effective by the cutoff. Require `candidate_population_status=COMPLETE` and the declared count to equal the submitted cohort. Require these five states to equal `APPROVED`: `identity_policy_status`, `eligibility_policy_status`, `selection_policy_status`, `privacy_scope_status`, and `downstream_use_status`.

## Candidates

Require each candidate to provide `account_id`, `population_membership_status`, `population_membership_receipt_id`, `identity_status`, `identity_receipt_id`, `eligibility_status`, `eligibility_receipt_id`, `score_status`, `score`, `score_receipt_id`, `score_policy_id`, `score_policy_version`, and UTC `evidence_cutoff`. Reject duplicate IDs, floats, non-finite values, evidence before policy effectiveness, and evidence after the selection cutoff.

When segment slots are used, also require `segment_status`, `segment`, and `segment_receipt_id`. Every candidate must belong to the declared population; the helper does not discover or expand the cohort.
