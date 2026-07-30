# Missing, Conflict, And Identity Rules

Use these evidence states:

- `VERIFIED` — value passed the approved provenance/validity/freshness rule.
- `UNKNOWN` — absent, stale, invalid, or outside scope.
- `CONFLICT` — approved sources disagree and no precedence rule resolves them.
- `EXCLUDED` — policy excludes the account/feature from this run.

Missing is not zero, cold, low fit, or negative evidence. Apply only the rule attached to that feature: `UNAVAILABLE`, `ZERO`, or `FIXED`. Disclose every applied treatment in the receipt.

Require an approved entity-level and hierarchy rule before scoring. Ambiguous domain/account/contact joins return `IDENTITY_REVIEW`. Never lower a match threshold or score parent/children twice to increase coverage.
