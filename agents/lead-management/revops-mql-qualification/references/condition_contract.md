# Condition contract

Each customer-authored condition has a stable ID/version, one kind (`required` or `disqualifying`), an approved source/version, a field-definition receipt, and a condition-definition receipt. Every record-condition pair has exactly one bound observation state.

Required conditions pass only with `recorded-true`. Disqualifying conditions pass only with `recorded-false`. Missing, conflicting, suppressed, or unauthorized evidence propagates before condition evaluation. Do not create points, weights, score bands, neutral values, or threshold defaults.
