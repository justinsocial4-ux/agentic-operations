# Rejection Analysis

Read this file before interpreting rejection reasons or recommending process changes.

## Preserve the taxonomy

Use the customer's approved reason codes. Do not silently merge free text into categories. If normalization is needed, keep raw text, normalized code, mapping version, and reviewer.

## Show missingness

Calculate:

```text
reason_capture = rejections_with_reason / all_rejections
reason_share_all = reason_count / all_rejections
reason_share_captured = reason_count / rejections_with_reason
```

Keep missing reasons in `UNKNOWN_REASON`. A top captured reason can be biased when capture differs by rep, team, source, or period.

## Interpretation limits

- A rejection reason is a recorded disposition, not independently verified root cause.
- A changed reason distribution can reflect policy, coaching, UI, required-field, or rep-compliance changes.
- Do not infer that marketing scoring caused every rejection.
- Do not automate score changes from a reason count.

Recommend a sample audit of source records when one reason dominates or capture changes materially.
