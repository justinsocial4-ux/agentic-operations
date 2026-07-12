---
name: revops-attribution-engine
description: "Allocates an approved measure across complete pseudonymous touchpoint populations using exact customer-authored model weights, while labeling every result as policy-allocated credit rather than causal contribution. Make sure to use this skill whenever the user asks which campaign, channel, content, event, ad, email, call, or touchpoint drove, influenced, sourced, created, or deserves credit for pipeline, bookings, ARR, revenue, conversions, or deals—or asks for first-touch, last-touch, linear, time-decay, U-shaped, W-shaped, multi-touch, model-comparison, ROI, budget, or forecast attribution—even when CRM membership, UTM data, platform reports, or a preferred model are assumed to prove impact."
metadata:
  category: "Reporting & Analytics"
  phase: "2"
  data_readiness: "complete_customer_supplied_touchpoint_populations_and_approved_model_weights_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved purpose, privacy, source, population, identity-linkage, event, eligibility, deduplication, ordering, model-weight, finance, recipient, and retention receipts"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable anonymous opportunity, touchpoint, bucket, model, source, contract, and receipt IDs"
---

# Attribution Credit Allocation Evidence Review

Allocate only what complete customer-supplied evidence and an approved model contract authorize. Credit is a policy allocation, not proof that a touchpoint caused, influenced, sourced, or drove an outcome.

## Exact Response Rule

Build the input document, run scripts/attribution_credit.py, and return render_allocation_output(review_attribution_credit(document)) byte for byte. The first response byte must be {; the helper supplies the final empty terminal line after }. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read references/scope_and_policy.md before accepting purpose, privacy, recipients, retention, or prohibited downstream uses.
- Read references/source_and_lineage.md before accepting sources, schemas, authorizations, queries, pages, cutoffs, or populations.
- Read references/touchpoint_contract.md before accepting identity linkage, event evidence, eligibility, ordering, deduplication, exclusions, or buckets.
- Read references/model_contract.md before accepting first/last/linear/time-decay/U/W/custom model names, weights, versions, or approvals.
- Read references/allocation_math.md before normalizing weights, allocating the approved measure, reconciling rounding, or grouping buckets.
- Read references/privacy_and_actions.md before handling personal data, profiling, rankings, ROI, budget, forecast, message, export, or write requests.
- Read references/output_contract.md before rendering a result.
- Read references/verification_sources.md for current official sources supporting the boundary.
- Use scripts/attribution_credit.py for strict validation, Decimal allocation, conservation, aggregation, and exact rendering.

## Operating Rules

1. Work offline and read-only. Never query CRM, marketing, advertising, analytics, finance, email, web, call, intent, product, identity, or messaging systems.
2. Require one effective customer policy with exact purpose, privacy/lawful-basis review, reviewer, allowed recipient roles, retention, and explicit bans on causal, financial, optimization, forecast, and automated-decision use.
3. Accept only IDs beginning anonymous-opportunity-, anonymous-touchpoint-, or anonymous-bucket-. Reject names, emails, phones, URLs, UTMs, account/contact/deal IDs, campaign names, free text, and direct or reversible identifiers.
4. Bind the allocation contract to exact source/schema versions, authorization window, query/page/population receipts, cutoff, report period, touchpoint window, IANA timezone and offsets, currency, amount basis, measure definition, finance approval, and pseudonymization receipt.
5. Require exact identity-linkage, event-definition, eligibility, deduplication, ordering, exclusion, and bucket-policy receipts. Campaign membership, CreatedDate, LastModifiedDate, status, UTM, or name similarity is never enough by itself.
6. Reconcile the declared opportunity population and each opportunity's touchpoint population exactly once. Duplicate, extra, missing, stale, future, unauthorized, suppressed, or conflicting evidence fails closed for that opportunity.
7. Require one customer-authored model ID/version/definition/approval and one approved raw-weight receipt for every declared touchpoint. Never choose, default, infer, tune, compare, or improve a model or weight.
8. Raw weights must be finite, non-negative Decimal strings and total above zero per opportunity. A model label such as first-touch, time-decay, or W-shaped does not change this evidence requirement.
9. Let the helper normalize weights, allocate the non-negative approved measure, apply the approved lexicographic remainder rule, prove exact per-opportunity conservation, and aggregate only within the single contract's exact period/currency/amount basis/model.
10. Empty or unresolved touchpoint evidence produces no credit. Preserve AVAILABLE, EVIDENCE_MISSING, EVIDENCE_CONFLICT, SUPPRESSED, and UNAUTHORIZED without fallback, Other, Direct Sales, fuzzy match, cached record, or partial result.
11. Outputs are unranked anonymous POLICY_ALLOCATED_CREDIT receipts. They are not revenue driven, contribution, influence, source, ROI, incrementality, effectiveness, accuracy, confidence, performance, risk, or forecast evidence.
12. Never recommend or execute budget, bid, campaign, channel, sales, customer, worker, GTM, forecast, pipeline, or finance action; never send, export, schedule, alert, write records, or feed a downstream decision.
13. Separate model runs may be compared only by a human under separately approved contracts. Never blend models, select a winner, or claim one is truer.
14. Return HUMAN_REVIEW_REQUIRED plus causal_attribution_authorized: false, ranking_authorized: false, downstream_decision_authorized: false, and action_authorized: false for every valid review.
15. R1: never add an adequacy, performance, influence, confidence, accuracy, risk, or readiness adjective. Only exact helper states may characterize evidence.
16. R2: return one helper-rendered response. Every calculated number must come from the helper and appear only in its assigned bucket receipt; never recompute, narrate, duplicate, or self-correct it.

## Workflow

1. Freeze policy, source, period, measure, privacy, and model authority.
2. Reconcile complete opportunity and touchpoint populations.
3. Validate identity/event/eligibility/deduplication/ordering evidence and approved weights.
4. Allocate and conserve once; unresolved opportunities contribute no credit.
5. Aggregate into anonymous buckets without ranking or interpretation.
6. Render helper stdout exactly; a human owns meaning and decisions.

## Worked Example

Input: two anonymous opportunities carry approved USD contracted-amount measures. One has two complete touchpoints with approved weights; the other has a missing touchpoint. Run the helper: it allocates only the complete opportunity, proves conservation, preserves the second as EVIDENCE_MISSING, returns unranked anonymous bucket credits, and authorizes no causal claim, ranking, budget, forecast, or other action.

## Failure Boundary

Missing or incompatible policy, privacy, source, schema, authorization, query, page, population, cutoff, period, timezone, currency, amount basis, measure, finance, pseudonymization, identity-linkage, event, eligibility, deduplication, ordering, exclusion, bucket, model, weight, recipient, or retention evidence fails closed. Never replace it with live access, inferred engagement, fuzzy identity, generic attribution weights, partial data, a confidence score, recommendation, or action.
