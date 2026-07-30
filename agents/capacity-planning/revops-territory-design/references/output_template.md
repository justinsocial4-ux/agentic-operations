# Output template

Return one exact helper-owned response and nothing else:

`render_receipt_json(build_downstream_receipt(...))`

The first response character is `{`. Do not add a heading, Markdown fence, introduction, table, explanation, arithmetic, summary, adequacy label, correction, or closing sentence. Do not repeat any number outside the helper rendering.

The JSON contains the frozen policy IDs, exact population-bound rep-pseudonymization receipt, separate frozen current-assignment and candidate evidence-register receipts, per-lane evidence references, complete per-rep count/amount/route rows including zero-assignment rows, fully versioned constraint provenance, solver receipt, non-ranked comparison receipt, approval state, and boundary. The comparison receipt preserves its state, all declared and actual compatibility checks, exact incompatible lanes, and one moved-account count/ID record per scenario. Preserve every helper field and fail-closed state exactly.
