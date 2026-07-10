# Metrics and Statistical Rules

Read this for calculation and comparison rules.

## Rates

Report raw numerator, denominator, percentage, and a Wilson interval. Small samples may be displayed, but unstable estimates should not drive rollout.

## Comparisons

- Absolute difference: `rate_A - rate_B`, in percentage points.
- Relative lift: `(rate_A - rate_B) / rate_B`. When B is zero, relative lift is undefined.
- For a predeclared two-arm comparison, use a pooled two-proportion z-test and report the two-sided p-value.
- A p-value is not the probability that A is better or that the result will repeat.

## Multiple comparisons

If inspecting many subjects, steps, windows, or reps, adjust the family of p-values. The bundled helper uses Benjamini-Hochberg false-discovery-rate adjustment. State the family and number of comparisons.

## Subject clustering

Use normalized Jaro-Winkler similarity only to propose clusters. Default threshold 0.90 is a tuneable heuristic. Review original subjects because transitive string clusters can join semantically different offers.

## Observational slices

Campaign, list quality, persona, territory, rep, offer, step, and time can confound one another. Observational rate differences create hypotheses. Random assignment or an approved causal design is required for lift claims.
