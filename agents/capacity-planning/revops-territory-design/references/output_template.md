# Output template

Return these sections in order. Preserve helper field names and fail-closed states exactly.

1. **Scope and no-write receipt** — purpose, cutoff, timezone, policies, owners, prohibited uses, boundary.
2. **Evidence register** — evidence/source/version/as-of/extraction/policy/purpose/access fields.
3. **Population reconciliation** — frozen counts plus missing, duplicate, unknown, excluded, shared/team, and identity-review records.
4. **Assignment completeness** — one row per candidate account with assigned pseudonymous rep IDs and evidence IDs.
5. **Constraint register** — each exact rule, result, violation, conflict, owner, and evidence.
6. **Descriptive summaries** — per-rep counts and same-basis amounts with coverage.
7. **Route coverage** — supplied route policy, pair coverage, element/fallback states, supplied-frequency totals.
8. **Solver receipt** — raw status and every required model/solver field.
9. **Scenario comparison** — non-ranked rows and incomparability reasons.
10. **Human review queue** — workforce/privacy/accessibility/correction/approval states.
11. **Bounded downstream receipt** — render exactly from the helper; do not add a winner or action.

Close with `NO TERRITORY OR OWNERSHIP CHANGE / NO QUOTA OR WORKFORCE ACTION`.
