# Output Contract

Return only `render_review_output(review_aggregate_evidence(document))`.

The helper returns one canonical JSON object containing:

- a policy receipt;
- population receipts;
- source, cohort, period, cell, and comparison receipts;
- limitations and the no-action boundary;
- `HUMAN_REVIEW_REQUIRED` and `action_authorized: false`.

Unsuppressed cells contain their input value and aggregation-rule ID exactly once. Suppressed cells contain no value. Accepted comparisons contain the two cell IDs and one signed delta; they do not repeat the current or previous values. Suppressed comparisons contain no delta.

The model must not add a title, summary, interpretation, Markdown fence, caveat, correction, or follow-up. If an input is invalid, let the helper fail closed; do not repair or reinterpret it in prose.
