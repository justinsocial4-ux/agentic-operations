# Output template

Return one exact helper-owned response and nothing else:

`render_receipt_json(build_downstream_receipt(...))`

The first response character is `{`. Do not add a heading, Markdown fence, introduction, table, explanation, arithmetic, summary, adequacy label, correction, or closing sentence. Do not repeat any number outside the helper rendering.

The JSON contains the frozen policy IDs, exact population-bound rep-pseudonymization receipt, evidence IDs, complete per-rep count/amount/route rows including zero-assignment rows, constraints, solver receipt, non-ranked comparison state, approval state, and boundary. Preserve every helper field and fail-closed state exactly.
