# Output contract

Return one deterministic JSON document containing the frozen policy and blueprint receipts, metric receipts, comparison receipts, claim-ledger bindings, section blocks, unresolved evidence, and fixed human-review/no-action/no-delivery/no-publication boundaries. Helper-defined ordering controls all arrays and keys.

Render exactly once. Do not repeat a calculated metric, delta, or percentage in narrative, claim, section, summary, recommendation, or correction text. The final output ends with the helper's explicit empty terminal line.
