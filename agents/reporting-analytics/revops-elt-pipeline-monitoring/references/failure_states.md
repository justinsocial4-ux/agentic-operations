# Failure states

Precedence is `UNAUTHORIZED`, `SUPPRESSED`, `EVIDENCE_CONFLICT`, then `EVIDENCE_MISSING`.

- `UNAUTHORIZED`: policy, review, source, recipient, or capture authorization does not cover the review.
- `SUPPRESSED`: privacy or customer suppression intentionally withholds the observation; no value or condition may appear.
- `EVIDENCE_CONFLICT`: mutually incompatible source, schema, definition, unit, denominator, rule, window, state, or receipt evidence exists.
- `EVIDENCE_MISSING`: required evidence is absent, incomplete, stale, future, permission-scoped away, or outside the window.
- `SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED`: evidence is present but does not exactly bind to its lane/rule contract.
- `SOURCE_OBSERVATION_EVIDENCE_PRESENT`: every required binding and receipt matches; the helper evaluates only the frozen customer rule.

Never repair a failure with cache, proxy, default, zero, success, relaxed rules, another platform, or model judgment.
