# Output Contract

Read before returning any result.

- Use `review_access(...)` and return `render_review_output(review)` byte for byte.
- The response is one JSON code block followed by the exact helper-owned boundary.
- Preserve policy/evidence, population reconciliation, per-account entitlement/authorization/exception/activity lanes, exceptions, control-context boundary, approval state, and authorization booleans.
- Sort stable IDs deterministically and use JSON `null` for unavailable values.
- R2 prohibits introductions, numeric prose, copied tables, recomputation, alternate rounding, inline correction, omitted fields, renamed keys, or a second artifact.
