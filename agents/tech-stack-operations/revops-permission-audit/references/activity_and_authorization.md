# Activity and Authorization

Read before using login/activity or authorization state.

- Authorization state must come from the customer-designated authoritative source as `AUTHORIZED`, `REVOKED`, `PENDING`, or `UNKNOWN`.
- Platform account state is observed evidence. Report exact mismatches without inferring employment termination, compromise, or remediation.
- Activity is optional and separate. Require a customer-owned threshold, eligible account types, cutoff/timezone semantics, occurrence timestamp definition, and registered evidence.
- Missing activity is `SOURCE_REQUIRED`, never zero or inactivity.
- Report only `THRESHOLD_EXCEEDED`, `WITHIN_THRESHOLD`, `NOT_APPLICABLE`, or an unresolved state. Do not call an account dormant, wasteful, orphaned, risky, or deactivatable.
