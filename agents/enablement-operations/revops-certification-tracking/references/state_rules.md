# State rules

The customer supplies one rule ID and the exact allowed output state identities. A record must explicitly say `recorded-complete`, `recorded-incomplete`, `missing`, `conflicting`, `suppressed`, or `unauthorized`; absence never proves non-enrollment or incompletion.

Recorded completion at or before cutoff returns `RECORDED_COMPLETE_BY_CUTOFF`. Recorded incomplete evidence returns `NO_DUE_DATE_RULE` when no due rule exists, otherwise the helper compares the exact due time to the cutoff and returns `RECORDED_INCOMPLETE_DUE_AT_OR_BEFORE_CUTOFF` or `RECORDED_INCOMPLETE_DUE_AFTER_CUTOFF`.
