# Output Contract

Read this file before returning any result.

- Use `review_segments(...)` and return `render_review_output(review)` byte for byte.
- The response is one JSON code block followed by the exact helper-owned boundary.
- Preserve policy/evidence, periods, segment definitions, per-segment/per-period lanes, comparisons, exceptions, approval state, and authorization booleans.
- Sort stable IDs deterministically. Use JSON `null` for unavailable values; never insert a guessed zero.
- R2 prohibits introductions, numeric prose, copied tables, recomputation, alternate rounding, inline correction, or a second artifact.
- Do not omit helper fields, rename keys, or summarize the response.
