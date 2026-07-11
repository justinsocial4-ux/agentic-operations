---
name: revops-rep-performance
description: "Reviews exact anonymous sales-team aggregate evidence without ranking or evaluating individual workers. Make sure to use this skill whenever the user asks for a rep performance digest, leaderboard, activity scorecard, coaching signal, quota or pipeline comparison, top or bottom performers, manager intervention, promotion, pay, PIP, firing, territory action, or named-worker analysis—even when the request assumes read-only CRM access makes the analysis safe."
metadata:
  category: "Reporting & Analytics"
  phase: "2"
  data_readiness: "approved_policy_complete_anonymous_aggregate_evidence_and_source_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved purpose, workforce, privacy, source, metric, suppression, comparison, retention, and correction policies"
  mcps:
    - "None; accept pre-supplied structured anonymous aggregates only"
  minimum_data:
    - "Stable policy, source, schema, authorization, cohort, period, cell, and comparison receipts"
---

# Anonymous Rep-Evidence Review

Show only what approved anonymous team aggregates establish descriptively. Do not turn activity, pipeline, stage, or outcome evidence into a worker score, diagnosis, ranking, coaching instruction, or employment decision.

## Exact Response Rule

Build the input document, run `scripts/aggregate_evidence.py`, and return `render_review_output(review_aggregate_evidence(document))` byte for byte. The first response byte must be `{`; the final response byte must be the helper's newline after `}`. Do not use Markdown fences or add model prose. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, prohibited uses, retention, or correction paths.
- Read `references/anonymous_input_and_lineage.md` before accepting sources, populations, cohorts, periods, or aggregate cells.
- Read `references/metric_semantics.md` before accepting calls, emails, meetings, pipeline, stage, or outcome evidence.
- Read `references/comparability_and_calculation.md` before comparing periods or calculating a delta.
- Read `references/privacy_and_workforce.md` before accepting any field or request that may identify, profile, monitor, or affect a worker.
- Read `references/output_contract.md` before rendering a result.
- Read `references/action_boundaries.md` before discussing coaching, quota, territory, pay, promotion, discipline, termination, customer, CRM, or messaging action.
- Read `references/verification_sources.md` for the official sources supporting the employment, privacy, governance, and platform boundaries.
- Use `scripts/aggregate_evidence.py` for strict validation, suppression, Decimal calculation, population reconciliation, and exact rendering.

## Operating Rules

1. Work offline and read-only. Do not query, export, cache, schedule, message, alert, write CRM, contact a customer, or modify a worker or customer record.
2. Require one effective customer policy with stable identifiers, authority, human reviewer, workforce approval, privacy approval, worker-notice receipt, approved descriptive purpose, prohibited uses, UTC cutoff, allowed metrics, exact aggregation rules, approved cohort dimension, minimum-group rule, retention rule, recipients, and correction path.
3. Accept only pre-supplied anonymous aggregate cohorts and cells. Reject names, emails, phones, addresses, domains, URLs, free text, job titles, worker IDs or pseudonyms, protected traits, health or leave data, recordings, individual activity, quota, attainment, compensation, ranking, or performance fields.
4. Reconcile every declared source, cohort, period, cell, and comparison exactly once. Missing, duplicate, extra, stale, future, unauthorized, or conflicting evidence fails closed.
5. Bind each cell to one approved source/schema/authorization receipt, cohort population/anonymity receipts, period, metric code, aggregation rule, unit, and—when monetary—currency and amount basis.
6. Keep calls logged, emails logged, meetings occurred, active pipeline amount, active opportunity count, closed-won count, and closed-lost count in separate evidence lanes. Never sum unlike metrics or call them effort, productivity, conversion, effectiveness, health, or performance.
7. Suppress a cohort when its customer-supplied member count is below the approved customer-supplied minimum. Do not emit suppressed cell values or calculate comparisons from them. Never invent a universal minimum.
8. Compare only the same cohort, metric, source, schema, authorization, unit, currency, amount basis, and equal-duration non-overlapping periods. Calculate only the signed Decimal delta supplied by the exact current and prior cells.
9. Never infer causation, attribution, forecast, confidence, sufficiency, risk, anomaly, intent, effort, skill, morale, personal circumstances, deal quality, quota likelihood, or future outcomes.
10. Never rank, score, percentile, label, coach, mentor, monitor, investigate, promote, pay, discipline, place on a plan, fire, hire, assign quota, change territory, alter schedules, contact customers, move deals, or recommend any such action.
11. Never use output as the sole or automatic basis for an employment, compensation, customer, financial, or operational decision. Every accepted review is `HUMAN_REVIEW_REQUIRED` with `action_authorized: false`.
12. R1: never characterize evidence adequacy with an adjective unless an exact approved numeric customer rule defines that exact label. This helper emits no adequacy adjective.
13. R2: return one helper-rendered response. Every numeric fact comes from the helper and appears only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
14. Freeze policy, normalized input, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate purpose, authority, dates, recipients, retention, prohibited uses, human review, and correction path.
2. **Reconcile evidence.** Match every declared source, cohort, period, cell, and comparison exactly once.
3. **Validate anonymity.** Reject direct, pseudonymous, sensitive, free-text, individual, quota, ranking, and performance fields.
4. **Validate semantics.** Keep each approved source-specific metric lane separate and prove exact period and unit bases.
5. **Suppress first.** Apply the approved minimum-group rule before any value or comparison can enter output.
6. **Calculate once.** Let the helper calculate only same-basis signed deltas.
7. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: one approved anonymous cohort supplies separate aggregate calls-logged and meetings-occurred cells for two equal, non-overlapping periods, with complete source, policy, population, and minimum-group receipts.

Run the helper. Its JSON response records each permitted unsuppressed cell once and each signed same-basis delta once, then marks the review `HUMAN_REVIEW_REQUIRED` with no action authorized. It does not name a worker, combine the lanes, rank the cohort, explain a cause, or recommend coaching.

## Failure Boundary

Missing or incompatible policy, authorization, source, schema, population, cohort, period, timestamp, unit, currency, amount basis, metric, suppression, comparison, privacy, workforce, retention, recipient, or correction evidence remains unresolved. Never replace it with CRM retrieval, a vendor benchmark, a confidence score, fuzzy matching, prediction, ranking, causal inference, coaching, customer action, or workforce action.
