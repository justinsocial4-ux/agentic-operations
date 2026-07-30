# Criteria And Scoring

Every criterion needs a stable ID, exact definition, approved evidence rule, required flag, and non-negative Decimal weight. Criterion IDs are unique and weights total exactly 100.

Each event supplies exactly one receipt for every criterion with state `MATCHED`, `NOT_MATCHED`, `UNKNOWN`, or `CONFLICT`. The policy score is the sum of weights for `MATCHED` criteria. It is policy arithmetic, not a probability, quality measure, or prediction.

Any unresolved required or optional criterion makes the event unrankable because the unresolved state could alter ordering. A required `NOT_MATCHED` criterion makes the event ineligible. Boundary ties remain unresolved; IDs are display order only.
