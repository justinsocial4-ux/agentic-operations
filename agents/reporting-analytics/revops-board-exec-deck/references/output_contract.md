# Output contract

Return one deterministic JSON document containing policy and blueprint receipts, metric receipts, comparison receipts, claim-ledger bindings, slide blocks, unresolved evidence, and fixed human-review/no-action/no-publication boundaries. All arrays and keys use helper-defined ordering.

Render exactly once. Do not repeat a metric or comparison number in narrative, claim, summary, recommendation, or correction text. The final output ends with the helper's explicit empty terminal line.
