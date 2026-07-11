# Evidence rules

The customer supplies one rule ID and an exact set of required evidence-lane IDs. The allowed lanes are source observation, worker notice, worker access, worker response, correction, appeal, recipient authorization, and retention binding.

The helper does not judge coaching content. It returns `RULE_MATCHED` only when every required lane is `present`. Precedence for any unresolved lane is `UNAUTHORIZED`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, then `EVIDENCE_MISSING`.
