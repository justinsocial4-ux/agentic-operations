# Output Template

## Exact Output Rule

Return `render_preview_output(build_preview(document))` verbatim and nothing else. Begin with its opening backtick and end with its boundary. Do not add an introduction or repeat the display-order explanation; those fields are already in the JSON. That deterministic response contains one JSON artifact plus the exact nonnumeric boundary. Every numeric value and identifier is helper-owned and printed once; never add narrative counts, tables, corrections, or a second receipt.

The helper's `artifact_paths` maps these seven requested views to canonical fields without duplicating the underlying values.

## 1. Policy And Scope Receipt

Policy/version/owner; effective date; population receipt/status/count; cutoff; purpose; entity level; five scope states; score policy/version; reviewer; proposed use; affected system/records; reversal path; action approval.

## 2. Candidate Population, Identity, And Eligibility

For every account: identity and eligibility receipt IDs/states, evidence cutoff, and exact disposition. Separate verified ineligible accounts from unresolved accounts.

## 3. Score Evidence

For every account: score state, exact decimal score or null, score policy/version, and compatibility state. Preserve conflicts and unknowns.

## 4. Capacity And Segment Slots

Show global capacity, optional segment field and exact slots, filled/unfilled counts, and candidate counts. For every segmented candidate, quote segment status, value, and receipt ID. State that no redistribution was inferred.

Read each helper field at its canonical path. Never include a superseded number or self-correction in an audit receipt.

## 5. Selection Preview

Return helper gate/status, final selection IDs only when available, provisional-above-boundary IDs, tied review IDs, and every candidate's exact disposition. Account-ID ordering is display-only and never a score tie-break. Never turn provisional IDs into a target list.

## 6. Validation And Prohibited Conclusions

State whether a model card and prospective outcome validation exist. List missing design, cohort, calibration, uncertainty, treatment, or causal evidence. State that the preview does not establish intent, probability, priority truth, expected pipeline, ROI, or forecast.

## 7. Human Decision Preview

Name the reviewer, policy owner, proposed downstream use, action approval state, system/records affected if later approved, and reversal path. End with the exact no-action boundary.
