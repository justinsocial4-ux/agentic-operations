# Failure states

Precedence is `UNAUTHORIZED`, `SUPPRESSED`, `EVIDENCE_CONFLICT`, then `EVIDENCE_MISSING`.

- `UNAUTHORIZED`: policy, review, source, recipient, or capture authorization does not cover the review.
- `SUPPRESSED`: privacy or customer suppression intentionally withholds the observation; no value may appear.
- `EVIDENCE_CONFLICT`: mutually incompatible source, schema, definition, unit, denominator, time, state, or receipt evidence exists.
- `EVIDENCE_MISSING`: required evidence is absent, incomplete, stale, future, or outside the observation window.
- `SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED`: evidence is present but does not exactly bind to its frozen lane contract.
- `SOURCE_OBSERVATION_EVIDENCE_PRESENT`: every required binding and receipt matches; the value remains uninterpreted.

Never repair a failure with a proxy, cache, benchmark, default, zero, guessed category, or model judgment.
