# Scenario comparison

Compare scenarios only when the frozen populations, policies, constraints, amount basis/currency/period, and route policy match. Otherwise return `INCOMPARABLE` and explain which lane differs.

The final helper-built comparison receipt must retain both the customer-declared compatibility flags and the helper's independently calculated checks for population, policy, constraints, amount basis, and route policy. It must list every lane where either value is false. Do not reduce those diagnostics to a state label alone.

For each scenario, report assignment coverage, moved-account count versus the frozen current state, complete-population per-rep account counts, same-basis amount totals, constraint violations, missing/unknown evidence, route coverage and supplied totals, solver state, and workforce-review state. Retain zero-assignment and unresolved rep rows.

Preserve each scenario's moved-account count and exact stable moved-account IDs in the final comparison receipt. The helper validates that counts match the unique IDs and that the comparison scenario set exactly matches the reviewed scenario set.

Sort scenario and evidence rows by stable IDs for reproducibility. Do not rank scenarios, calculate a composite score, color-code a winner, or select a scenario. Equal counts or amounts are not fairness. Lower supplied travel totals do not prove a better business or workforce result.

A preference is a separate human decision question governed by a preapproved lexicographic/decision rule, complete evidence, affected-party review, correction path, and named approver.
