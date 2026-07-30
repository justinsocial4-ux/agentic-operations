# Output Contract

The helper returns one deterministic JSON document containing the review type/state, policy receipt, declared population receipt, identity-link receipts, source-population receipts, fact receipts, account-and-lane reviews, rule-result references, and fixed boundary.

Return helper stdout byte for byte. The first byte is `{`; the last byte is the helper's newline after `}`. Add no prose, Markdown fence, heading, table, calculation, interpretation, correction, or second rendering.

Each supplied or derived numeric fact belongs in exactly one helper-owned receipt. Other sections refer to its ID. Never repeat, paraphrase, recompute, round, label, or self-correct a number in model prose. Do not use an adequacy adjective unless an approved customer numeric rule explicitly defines that exact label.
