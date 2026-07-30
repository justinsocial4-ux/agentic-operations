# Output contract

Return only `render_review_output(review_signal_evidence(document))`. The helper emits normalized policy and source receipts, one receipt per observation, one state summary, `HUMAN_REVIEW_REQUIRED`, and false inference/action flags.

No prose may precede or follow the JSON. Preserve the helper's explicit empty terminal line: the final bytes are `7d 0a 0a`. Do not duplicate counts, timestamps, recency windows, or any other numeric fact outside its helper-owned location.
