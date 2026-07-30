# Score Evidence

- Rank only `score_status=AVAILABLE` values from the exact `score_policy_id` and `score_policy_version` named by the selection policy.
- Accept exact integer or decimal-string values from 0 through 100. Reject binary floating-point input and non-finite values.
- Require `score=null` for `UNAVAILABLE`, `UNKNOWN`, or `CONFLICT` states. These states block a complete selection because the missing value could cross a capacity boundary.
- Treat a score-policy mismatch as conflict, not as a comparable number.
- Call the value a `policy score`. Do not relabel it fit truth, intent, probability, quality, propensity, qualification, or forecast.
- Keep component evidence and missing-value rules in the upstream scoring receipt. Selection must not recompute or repair an incomplete score.
