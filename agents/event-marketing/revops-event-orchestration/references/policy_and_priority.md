# Policy And Priority

Freeze the policy before reviewing the event:

- policy ID/version, owner, effective dates, and eligible population
- exact normalized evidence tokens and source requirements
- unique rule ID and unique non-negative integer priority
- required-all and optional-any signal sets
- lane ID, response hours, anchor field, timezone, and business/calendar-clock rule
- change-control, backfill, success/kill rule, and review date

The helper uses exact text-token equality, the lowest unique priority number, and timezone-aware elapsed-hour arithmetic. It does not score, fuzzy match, infer missing evidence, create a fallback, or evaluate business calendars. A business-hours rule needs a separate approved calendar implementation; otherwise return `TIME_POLICY_REQUIRED`. If the policy is invalid, correct the policy rather than repairing the output by hand.
