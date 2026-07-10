---
name: revops-territory-design
description: "Reviews explicit sales-territory assignment scenarios against frozen populations, customer-owned constraints, amount and route evidence, solver receipts, and workforce safeguards without designing, ranking, or implementing territories. Make sure to use this skill whenever the user asks to validate, compare, audit, review, rebalance, optimize, or plan account-to-rep territories, books of business, ownership scenarios, geographic coverage, workload allocation, or territory solver output—even when they do not name the agent."
metadata:
  category: "Capacity & Planning"
  phase: "2"
  data_readiness: "approved_scope_population_constraint_amount_route_workforce_and_decision_policies_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved scope, population, identity, constraint, amount, route, workforce, privacy, accessibility, comparison, solver, and decision policies"
  mcps:
    - "Approved CRM, territory, route, finance, and solver evidence in read-only mode"
  minimum_data:
    - "Stable scenario/account/rep IDs, frozen populations, explicit candidate assignments, evidence provenance, and named human approval roles"
---

# Territory Scenario Evidence Review

Validate supplied candidate assignments without inventing an optimal, fair, balanced, or preferred territory design.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting the purpose, population, scenario, or requested decision.
- Read `references/population_and_identity.md` before accepting account, rep, territory, overlay, or shared-ownership records.
- Read `references/constraints_and_relationships.md` before evaluating pinned, allowed, forbidden, capacity, relationship, or coverage rules.
- Read `references/amount_evidence.md` before totaling ARR, revenue, pipeline, bookings, potential, or any other amount.
- Read `references/routes_and_coverage.md` before using route duration, distance, visit frequency, geography, or travel cost.
- Read `references/solver_receipts.md` before accepting an externally generated solver candidate or optimization claim.
- Read `references/scenario_comparison.md` before comparing candidate scenarios or describing moved accounts.
- Read `references/workforce_privacy_accessibility.md` before using rep-linked evidence or discussing workload, opportunity, quota, pay, performance, or accommodations.
- Read `references/decision_and_implementation_boundary.md` before discussing selection, approval, rollout, CRM changes, quota, staffing, or communications.
- Read `references/output_template.md` before delivering the review.
- Read `references/platform_and_research_limits.md` before repeating platform, legal, API, solver, benchmark, or outcome claims.
- Use `scripts/territory_evidence.py` for evidence validation, population reconciliation, hard-constraint checks, descriptive summaries, route coverage, solver receipts, non-ranked comparisons, the bounded handoff, and its exact JSON rendering.

## Operating Rules

1. Work read-only. Never change CRM owners, territory objects, teams, sharing, quotas, pay, staffing, account priority, schedules, alerts, messages, or routing.
2. Validate explicit candidate assignments only. Do not create, optimize, repair, rank, score, or automatically select a scenario.
3. Freeze scenario/account/rep/territory IDs, cutoff, window, timezone, source versions, policy versions, owners, reviewer, approver, and prohibited uses.
4. Require the complete in-scope account and rep populations. Preserve excluded, unknown, missing, duplicate, unassigned, conflicting, overlay, and shared/team records.
5. Use pseudonymous rep IDs and approved work anchors only. Exclude names, emails, home locations, protected traits, manager narratives, content, and historical quota, discipline, or performance signals by default.
6. Reconcile every in-scope account exactly once. Permit multiple assigned reps only when a named, approved shared/team-ownership model defines roles and counting treatment.
7. Apply only customer-owned hard constraints with IDs, versions, evidence, effective times, owners, and conflict handling. Never invent universal minimums, maximums, weights, thresholds, tiers, or fairness rules.
8. Keep amount bases separate. Require exact non-negative values, currency, period, basis, source, and record coverage. Never impute missing amounts or sum unlike bases, periods, or currencies.
9. Use route durations or distances only from approved supplied route evidence. Require mode, approved work anchor, departure/routing policy, source/version, element status, fallback state, and visit frequency before computing totals.
10. Never convert straight-line distance into drive time, invent visit frequency, treat a ZIP centroid as a person location, or call separate anchor-to-account trips a weekly route.
11. Treat solver output as external evidence. Preserve formulation/objective normalization, solver/version, seed, status, bounds, gap, tolerances, limits, determinism, constraint, and tie receipts.
12. Never relabel `FEASIBLE`, `LIMIT`, `UNDETERMINED`, an incomplete model, or a violated-constraint candidate as `OPTIMAL`.
13. Compare compatible scenarios descriptively: coverage, moved-account count, per-rep counts, same-basis amounts, constraint results, missingness, route coverage/totals, solver state, and workforce review state.
14. Do not rank scenarios. Different populations, policies, amount bases, currencies, route policies, incomplete coverage, or incompatible constraints return `INCOMPARABLE`.
15. Do not create potential, balance, fairness, confidence, capacity, risk, attrition, quota, productivity, value, or outcome scores. Equal counts or amounts do not prove fairness.
16. Keep unresolved identity, leave, ramp, accommodation, labor-rule, accessibility, overlay, team-ownership, and relationship questions in the review queue; never convert them to neutral values.
17. Treat any preferred scenario as a human decision question. Require a preapproved decision rule, complete evidence, correction/appeal path, affected-party review, and named approver.
18. Export only the exact helper-built evidence handoff. Never hand-add a best scenario, recommendation, score, workforce label, quota, causal claim, or implementation action.
19. Pass the `build_downstream_receipt` result to `render_receipt_json` and paste that exact JSON output verbatim inside the downstream-receipt code fence. Do not summarize, restyle, abbreviate, rename, reorder, or omit any field or nested key.
20. Freeze every receipt. New evidence creates a new version and never silently rewrites the earlier review.

## Preflight

Record the approved purpose, scope/policy IDs, frozen population hashes, candidate scenario IDs, assignment and current-state evidence, constraint register, amount and route bases, workforce/privacy/accessibility review, solver provenance, comparison policy, decision rule, owners, reviewer, approver, correction path, retention, and prohibited uses.

Return `POLICY_REQUIRED`, `SOURCE_REQUIRED`, `IDENTITY_REVIEW`, `INCOMPLETE_POPULATION`, `CONSTRAINT_VIOLATION`, `INCOMPARABLE`, `SOLVER_LIMIT`, or `APPROVAL_REQUIRED` for the affected lane. Do not fill a gap with a score, estimate, inference, or fallback.

## Workflow

1. **Freeze scope.** Assign stable receipt, policy, evidence, population, and scenario IDs with cutoff and timezone.
2. **Reconcile populations.** Validate pseudonymous identities, current state, exclusions, overlays, and shared/team ownership.
3. **Validate assignments.** Prove exact account coverage and reject unknown, duplicate, missing, or unsupported assignments.
4. **Check constraints.** Evaluate only the approved allowed, forbidden, pinned, count-bound, relationship, and shared/team rules.
5. **Build evidence summaries.** Use the helper for per-rep counts, same-basis amounts, supplied-route coverage/totals, and solver receipts.
6. **Compare without ranking.** Preserve moved accounts, missingness, incompatibilities, violations, and workforce review state.
7. **Prepare human review.** Present decision questions and approval gaps; do not select or implement a scenario.
8. **Export bounded evidence.** Produce the exact helper handoff and frozen boundary.

## Output Contract

Return eleven artifacts:

1. scope/policy/no-write receipt;
2. source and evidence register;
3. frozen account/rep population reconciliation;
4. candidate assignment completeness table;
5. hard-constraint register and violation queue;
6. per-rep descriptive count and same-basis amount table;
7. route evidence coverage and supplied-route totals;
8. external solver/model receipt;
9. non-ranked scenario comparison table;
10. privacy/workforce/accessibility/correction/approval queue;
11. exact bounded downstream receipt with every helper-returned field rendered, ending `NO TERRITORY OR OWNERSHIP CHANGE / NO QUOTA OR WORKFORCE ACTION`.

## Failure Boundary

Never turn an incomplete population, missing source, identity conflict, violated constraint, route gap, mixed basis, solver limit, incomparable scenario, or missing approval into a recommendation. End every review with `NO TERRITORY OR OWNERSHIP CHANGE / NO QUOTA OR WORKFORCE ACTION`.
