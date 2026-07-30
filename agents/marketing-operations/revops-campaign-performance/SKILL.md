---
name: revops-campaign-performance
description: "Reviews customer-supplied pseudonymous campaign measurement evidence under exact source, query, population, reporting-period, currency, and conversion-action contracts without ranking campaigns or recommending budget changes. Make sure to use this skill whenever the user asks to aggregate, compare, monitor, score, rank, alert on, optimize, report, or reallocate cross-channel campaign spend, impressions, clicks, conversions, CTR, CPC, or cost per conversion—even when the request assumes platform metrics are comparable, campaign names identify the same campaign, partial exports are complete, or poor performance should trigger action."
metadata:
  category: "Marketing Operations"
  phase: "2"
  data_readiness: "complete_customer_supplied_measurement_evidence_and_approved_equivalence_contracts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved source, query, population, time, currency, metric-definition, conversion-action, equivalence, recipient, and retention receipts"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable anonymous campaign, contract, row, source, query, population, schema, authorization, period, currency, and metric-definition IDs"
---

# Campaign Measurement Evidence Review

Describe only what complete customer-supplied campaign measurement records support under exact approved contracts. Do not access platforms, merge unlike measures, rank performance, recommend action, or claim attribution or outcomes.

## Exact Response Rule

Build the input document, run `scripts/campaign_measurement.py`, and return `render_review_output(review_campaign_measurements(document))` byte for byte. The first response byte must be `{`; the final two response bytes must be the helper's explicit empty terminal line (`0a 0a`) after `}`. Do not use Markdown fences or add model prose. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, recipients, retention, or prohibited uses.
- Read `references/input_and_lineage.md` before accepting sources, queries, schemas, authorizations, pages, populations, or rows.
- Read `references/measurement_contracts.md` before calculating spend, impressions, clicks, conversions, or ratios.
- Read `references/comparability_and_time.md` before combining sources, periods, currencies, conversion actions, or reporting levels.
- Read `references/current_platform_limits.md` before interpreting Google Ads, LinkedIn Ads, Meta, HubSpot, Salesforce, or exported reports.
- Read `references/output_contract.md` before rendering a result.
- Read `references/action_boundaries.md` before discussing performance, anomaly, optimization, budget, alert, attribution, or forecast requests.
- Read `references/verification_sources.md` for current official sources supporting the boundary.
- Use `scripts/campaign_measurement.py` for strict validation, population reconciliation, comparability, Decimal arithmetic, and exact rendering.

## Operating Rules

1. Work offline and read-only. Do not query ad platforms, CRM, analytics, finance, email, Slack, identity, or attribution systems.
2. Require an effective customer policy with stable ID/version, owner, reviewer, cutoff/review time, allowed recipient roles, retention rule, and separate source, measurement, equivalence, recipient, and retention receipts.
3. Accept only campaign IDs beginning `anonymous-campaign-`; reject names, account names, URLs, emails, owners, audiences, creatives, search terms, demographics, contacts, leads, opportunities, free text, and direct identifiers.
4. Require one complete population receipt per measurement contract. Missing, duplicate, extra, unauthorized, stale, future, schema-conflicting, page-incomplete, or lineage-conflicting evidence fails closed.
5. Bind each contract to exact source/version, schema/version, authorization window, query receipt, page receipt, reporting level, local period and IANA timezone, currency, amount basis, metric-definition IDs, freshness time, and conversion-action settings.
6. Keep conversion action/category, counting mode, attribution model, attribution window, and interaction-date versus conversion-date basis explicit. Never call unlike actions simply `conversions` and combine them.
7. Never infer that matching campaign names identify the same campaign. Never fuzzy match, silently deduplicate, sum retry rows, or invent a campaign family.
8. Combine rows only inside a customer-approved comparison group whose contracts match on every measurement-basis field and carry an equivalence receipt. Otherwise fail validation.
9. Let the helper calculate same-basis Decimal totals, CTR, CPC, and cost per conversion. A zero denominator yields `null`; missing or unresolved evidence yields no metric.
10. Exact states are `AVAILABLE`, `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, and `UNAUTHORIZED`. Preserve them without substitution.
11. Outputs are descriptive evidence receipts, not performance, efficiency, quality, anomaly, winner, loser, risk, urgency, confidence, adequacy, attribution, incrementality, or financial-impact labels.
12. Never rank campaigns, choose a channel, recommend pausing or optimizing, move budget, fix tracking, change bids, create alerts, send messages, schedule monitoring, write records, or feed attribution/forecast decisions.
13. Never claim pipeline, revenue, ROI, savings, waste, improvement, causation, future performance, or CMO-CFO alignment.
14. Return `HUMAN_REVIEW_REQUIRED`, `ranking_authorized: false`, `attribution_authorized: false`, and `action_authorized: false` for every valid review.
15. R1: never add an adequacy or performance adjective. Only exact helper states may characterize evidence.
16. R2: return one helper-rendered response. Every calculated number must come from the helper and appear only in its assigned measurement group; never recompute, narrate, duplicate, or self-correct it.

## Workflow

1. **Freeze authority.** Validate purpose, dates, approvals, prohibitions, recipients, and retention.
2. **Validate contracts.** Bind every source, query, page, period, currency, metric definition, and conversion setting.
3. **Reconcile populations.** Match every declared row exactly once and reject direct identifiers or extra fields.
4. **Check comparability.** Require exact bases and an approved equivalence receipt before grouping contracts.
5. **Calculate once.** Let the helper create one numeric receipt per group and preserve unresolved row states separately.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: two complete pseudonymous source populations cover the same approved local period and currency. Their spend, impression, click, and conversion definitions—including conversion action category, counting, attribution, window, and date basis—match under an equivalence receipt. One additional row is `EVIDENCE_MISSING`.

Run the helper. It produces one same-basis group receipt, preserves the missing row without metrics, and authorizes no ranking, attribution, alert, write, budget change, or other action.

## Failure Boundary

Missing or incompatible policy, authorization, source, schema, query, page, population, reporting level, period, timezone, currency, amount basis, metric definition, conversion action, equivalence, recipient, retention, or row evidence fails validation. Never replace it with a live lookup, default metric, fuzzy join, platform benchmark, confidence score, performance label, recommendation, or action.
