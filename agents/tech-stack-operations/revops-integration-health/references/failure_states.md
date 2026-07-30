# Failure states

Apply this precedence when any required lane is unresolved:

1. `UNAUTHORIZED`
2. `SUPPRESSED`
3. `EVIDENCE_CONFLICT`
4. `EVIDENCE_MISSING`

Otherwise, any lane nonmatch makes the integration state `CONTRACT_OBSERVATION_NOT_MATCHED`; every lane must match for `CONTRACT_OBSERVATION_MATCHED`. Never replace unresolved evidence with a cached value, fallback ping, inferred state, generic vendor default, retry, confidence discount, or live query.
