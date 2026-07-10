---
name: revops-tool-adoption
description: "Builds an evidence-backed SaaS utilization review that reconciles entitlements, assigned identities, approved meaningful activity, source coverage, and matched-window changes without turning employee telemetry into value, waste, renewal, or consolidation verdicts. Make sure to use this skill whenever the user asks about tool adoption, license utilization, active seats, inactive licenses, feature usage, SaaS usage trends, renewal evidence, right-sizing evidence, or overlapping tools—even if they do not name the agent."
metadata:
  category: "Tech Stack & Operations"
  phase: "2"
  data_readiness: "approved_population_event_privacy_and_source_policies_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved entitlement, population, identity, meaningful-event, privacy, comparison, cost, and downstream-use policies"
  mcps:
    - "Approved SaaS usage, identity, procurement, and contract sources in read-only mode"
  minimum_data:
    - "Stable tool IDs, frozen observation windows, source provenance, population counts, and exact event definitions"
---

# Tool Utilization Evidence Review

Measure recorded utilization without pretending activity proves value, waste, employee performance, or the right renewal decision.

## Bundled Resources

- Read `references/policy_and_scope.md` before accepting a portfolio, tool, window, or requested decision.
- Read `references/source_and_event_contract.md` before treating any login, view, message, edit, API, audit, or feature event as meaningful activity.
- Read `references/population_and_identity.md` before calculating any seat, assignment, identity, or active-user ratio.
- Read `references/utilization_metrics.md` before calculating utilization, feature reach, or cost-per-active context.
- Read `references/comparisons_and_maturity.md` before reporting trends or comparing tools, groups, or periods.
- Read `references/privacy_and_workforce.md` before using person-, team-, department-, location-, or manager-linked evidence.
- Read `references/cost_contract_and_decisions.md` before discussing cost, renewal, right-sizing, savings, training, or consolidation.
- Read `references/tso03_handoff.md` before exporting utilization evidence to Vendor Performance.
- Read `references/output_template.md` before delivering a review.
- Read `references/platform_and_research.md` before repeating API, benchmark, privacy, or market claims.
- Use `scripts/utilization_evidence.py` for exact population receipts, rates, cost-per-active context, matched-window comparisons, currency totals, evidence validation, and the TSO-03 handoff.

## Operating Rules

1. Work read-only. Do not change licenses, users, groups, permissions, contracts, renewals, spend, routing, training, procurement/CRM fields, schedules, alerts, messages, or vendor records.
2. Require tool/service identity, license model, scope, equal observation windows, cutoff, timezone, source IDs/versions, extraction times, policy IDs/versions, owner, reviewer, approver, and intended use.
3. Separate `PAID_ENTITLEMENT`, `ASSIGNED`, `ELIGIBLE_ASSIGNED`, `ACTIVE_ELIGIBLE`, `UNASSIGNED`, `UNCLASSIFIED_ASSIGNED`, `EXCLUDED`, `UNMATCHED`, `UNKNOWN`, `WITHHELD`, and `CONFLICTING` populations. State every numerator and denominator.
4. Apply only a source-specific approved meaningful-event policy. A login, view, message, API call, admin event, background sync, bot action, or session has no universal adoption meaning.
5. Classify actor type from approved identity evidence. Never infer human/service/bot/test/admin status from activity volume, email shape, or name alone.
6. Keep missing, unmatched, withheld, stale, immature, duplicate, and conflicting evidence visible. Never convert it to zero, inactive, average, neutral, or synthetic confidence.
7. Report assignment rate only for compatible entitlement models. Report observed active-assigned rate as `active eligible / eligible assigned`; it is a utilization observation, not an adoption score.
8. Do not label people heavy, light, inactive, productive, engaged, wasteful, risky, or replaceable. Person-level reporting is disabled unless an approved privacy/workforce policy explicitly allows the purpose, viewer, minimum fields, suppression, retention, and correction path.
9. Prefer aggregate tool-level outputs and pseudonymous IDs. Exclude names, emails, IPs, content, message/file/channel titles, free text, and manager-linked drill-down by default.
10. Compare only equal, non-overlapping, mature windows under the same event, population, identity, source-coverage, and cohort policies. Otherwise return `INCOMPARABLE` or `IMMATURE_WINDOW`.
11. Report both counts and rates, percentage-point change, denominator change, and relative change only when the prior rate is nonzero. A rate change does not prove cause, intent, seasonality, displacement, satisfaction, or future use.
12. Keep contracted, invoiced, paid, allocated, bundled, committed, forecast, and quoted cost separate. Cost per observed active identity is descriptive and does not prove waste, value, savings, or removable spend.
13. Never create universal weights, scores, tiers, colors, confidence percentages, tool-category benchmarks, login targets, seat buffers, price medians, discount targets, savings, migration effort, or causal explanations.
14. Low utilization does not prove low value or replaceability; high utilization does not prove value, security, satisfaction, or renewal fitness.
15. Consolidation requires workflow, stakeholder, contract, security/privacy, accessibility, integration, continuity, switching, and decision-rule evidence. Category or feature overlap alone is insufficient.
16. Renewal, right-sizing, consolidation, training, security, and workforce actions remain review questions unless an approved decision rule and named approver are supplied. Execution always remains outside this skill.
17. Export only the exact helper-built descriptive utilization handoff to TSO-03; do not add fields by hand. Never export adoption score, vendor-health input, renewal-risk tier, consolidation flag, savings, or recommendation.
18. Freeze every input/output receipt. Later evidence creates a new version and never silently rewrites the earlier review.
19. Render every field returned by `build_tso03_handoff`, including the complete sorted `evidence` provenance array. Do not omit, rename, or hand-add fields. If source lag is not supplied, use `SOURCE_REQUIRED`; complete coverage never means zero lag.
20. When person-level reporting is disabled, do not ask the reviewer to reveal which people are unmatched, unknown, or conflicting. Route aggregate resolution to the authorized identity steward and return only updated counts/provenance.

## Preflight

Record the tool/legal service, license model, review purpose, tool/population/event/privacy/comparison/cost/downstream policy versions, source permissions, source/event taxonomies, windows/cutoff/timezone, lag and coverage, identity authority, exclusion reasons, owners, approver, and prohibited uses.

Stop only the affected metric when a source, policy, population, identity, window, or denominator is absent. Do not fill gaps with another tool's event semantics or benchmark.

## Workflow

1. **Freeze scope and sources.** Assign stable tool, evidence, policy, and window IDs; preserve source versions and extraction times.
2. **Reconcile populations.** Produce entitlement, assignment, eligible-human, active, exclusion, unmatched, unknown, withheld, and conflict counts.
3. **Apply event policy.** Record included/excluded events, actor types, deduplication, lag, coverage, and transformations.
4. **Calculate exact evidence.** Use the helper for rates, population receipts, equal-window changes, currency context, and unavailable states.
5. **Keep context separate.** Report cost/contract, workflow, security/privacy, and stakeholder evidence without creating a score or verdict.
6. **Prepare review questions.** Link each question to evidence/gaps and an approved decision rule or `RULE_REQUIRED`.
7. **Export bounded evidence.** Produce the TSO-03 handoff and frozen receipt with `NO LICENSE CHANGE / NO RENEWAL OR CONSOLIDATION ACTION`.

## Worked Example

For a compatible named-seat tool, 120 paid entitlements include 100 assigned identities. The approved identity policy resolves 80 eligible assigned humans, 60 of whom performed at least one approved meaningful event in the window; 10 assigned identities are excluded service/test accounts, 5 are unmatched, 3 are unknown, and 2 conflict.

Report assignment rate `100 / 120 = 83.333...%` and observed active-assigned rate `60 / 80 = 75%`. The population state is `CONFLICTING` because two identities remain conflicted. Do not call 40 seats waste, 20 people inactive, or recommend a seat cut. If a matched prior window was 54 of 80, report `+7.5` percentage points and `+11.111...%` relative change; do not infer why it changed.

## Output Contract

Return ten artifacts:

1. scope/policy/no-write receipt;
2. source/event provenance register;
3. population and identity reconciliation;
4. utilization and feature-event evidence table;
5. matched-window comparison table;
6. cost/contract context table;
7. privacy, missingness, and conflict queue;
8. decision-review questions with rule/approver state;
9. complete exact helper-returned TSO-03 evidence handoff, including every provenance row;
10. frozen receipt ending `NO LICENSE CHANGE / NO RENEWAL OR CONSOLIDATION ACTION`.

## Failure States

Use `SCOPE_REQUIRED`, `POLICY_REQUIRED`, `SOURCE_REQUIRED`, `IDENTITY_REVIEW`, `ZERO_DENOMINATOR`, `IMMATURE_WINDOW`, `CONFLICTING`, `INCOMPARABLE`, `RELATIVE_CHANGE_UNAVAILABLE`, `MIXED_CURRENCY`, `RULE_REQUIRED`, or `APPROVAL_REQUIRED`. Never translate one of these states into a score, confidence, waste estimate, person label, vendor verdict, or automatic action.
