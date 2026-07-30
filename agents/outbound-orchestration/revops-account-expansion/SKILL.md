---
name: revops-account-expansion
description: "Reviews customer accounts for evidence-backed expansion candidates while keeping entitlements, usage, adoption, whitespace, renewal timing, health, pricing, and human approval separate. Make sure to use this skill whenever the user asks for upsell or cross-sell candidates, seat expansion, product whitespace, expansion pipeline, account growth signals, renewal-adjacent expansion, expansion scoring, or a customer expansion play—even if they do not name the agent."
metadata:
  category: "Outbound Orchestration"
  phase: "1"
  data_readiness: "policy_and_instrumentation_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved expansion policy and product catalog"
  mcps:
    - "CRM, contract, billing, and product-analytics sources in read-only mode"
  minimum_data:
    - "Resolved account identity, contract entitlements, and dated usage evidence"
    - "Approved eligibility rules, amount basis, price source, currency, and action workflow"
---

# Account Expansion Review

Identify accounts that deserve human review for a possible expansion conversation. Do not turn product usage, job titles, arbitrary scores, or missing prices into claimed intent, probability, authority, or expected revenue.

## Bundled Resources

- Read `references/data_contract.md` before joining CRM, contract, billing, support, or product-analytics data.
- Read `references/policy_contract.md` before applying eligibility, timing, scoring, valuation, or play rules.
- Read `references/evidence_labels.md` before labeling signals, candidates, blockers, or unknowns.
- Read `references/metrics_and_scoring.md` before calculating adoption, seat utilization, coverage, value, or a policy score.
- Read `references/actions_and_privacy.md` before using contact data or proposing CRM tasks, messages, or outreach.
- Read `references/output_template.md` before producing the final review.
- Read `references/research_and_claims.md` before repeating platform, benchmark, probability, lift, or revenue claims.
- Use `scripts/expansion_metrics.py` for exact ratios, policy eligibility, weighted scores, dates, coverage, and values.

## Operating Rules

1. Analyze read-only evidence. Do not update CRM fields, create opportunities or tasks, enroll contacts, or send outreach.
2. Require a versioned customer-approved expansion policy. Do not invent thresholds, weights, timing windows, tiers, plays, buffers, or minimum sample sizes.
3. Resolve one durable account identity across systems and report matched, unmatched, duplicate, and conflicting records.
4. Record the product-instrumentation effective-since date, account/group mapping, eligible-user definition, event definition, analysis window, timezone, and coverage.
5. Do not reconstruct historical usage or group properties from current values. Unknown history remains unknown.
6. Keep contracted entitlements, observed use, eligible adoption, unused entitlement, and unpurchased whitespace as different facts.
7. Treat low core adoption, unresolved support risk, delinquency, or poor health as possible expansion blockers according to policy—not automatic cross-sell triggers.
8. Call product activity observed usage, not intent, propensity, likelihood, readiness, or demand.
9. Label direct source evidence `VERIFIED_SIGNAL`, policy-based hypotheses `INFERRED_CANDIDATE`, and absent or conflicting evidence `UNKNOWN` or `DATA_GAP`.
10. Use verified buying authority or an approved contact-selection process. Never infer authority from title alone.
11. Use a score only when the exact components, weights, missing-data treatment, target, and threshold were approved before reviewing results.
12. Call an uncalibrated weighted result a policy score—not probability, confidence, likelihood, expected lift, or predicted outcome.
13. Use verified contract, price-book, quote, or billing evidence for value. Without quantity, unit price, currency, and amount basis, return `VALUE_UNKNOWN`.
14. Do not apply the legacy 1.3 seat buffer, 20–25% ARR multipliers, 15% plan uplift, 1.5–2x rollout value, 40/30/30 score, universal tiers, or 90–120-day window.
15. Require comparable currency and dated FX policy before aggregating values. Never sum mixed currencies directly.
16. Separate candidate eligibility from play selection. Each proposed play must cite its approved rule and all required evidence.
17. Report evidence coverage beside every cohort result. Do not silently turn missing observations into zero.
18. Once results are inspected, any new threshold or rule applies only to future independent reviews.
19. Present action previews to the named approver. Execute nothing unless the user separately authorizes the exact action after review.
20. Avoid guarantees, causal claims, and promised pipeline or revenue outcomes.

## Preflight

### 1. Confirm the decision

Record the business question, account population, products, geography, owner, cutoff, analysis window, and whether the output is an evidence audit, eligible-candidate review, play review, or valuation.

### 2. Lock the policy

Record:

- policy ID/version, owner, approval date, and intended target
- eligible account/customer definition
- product catalog, entitlement definitions, and account hierarchy treatment
- adoption numerator and eligible denominator
- active-user definition, utilization rule, and any approved seat buffer
- health, support, payment, renewal, and exclusion rules
- candidate, play, and score rules, including missing-data treatment
- amount basis, price source, currency, and dated FX policy
- contact/privacy constraints and human approval workflow

If a needed element is absent, return `POLICY_REQUIRED` for that decision instead of borrowing the legacy defaults.

### 3. Verify source evidence

For every source, capture system, object/table, record key, extraction time, field meaning, freshness, historical coverage, missingness, and access scope. Product analytics must also identify the dates from which instrumentation and account mapping are valid.

### 4. Declare enabled analyses

| Evidence | Enabled analysis |
|---|---|
| Contract + product catalog | Entitlement and whitespace evidence |
| Dated user/product events + eligible population | Adoption and utilization |
| Approved health/renewal rules | Eligibility and timing review |
| Approved complete score policy | Policy score and ordering |
| Verified quantity + unit price + currency | Expansion value under named basis |
| Approved play and contact rules | Human action preview |

## Workflow

### 1. Build the account evidence table

Create one row per approved account unit. Preserve account ID, parent/child relationship, owner, contract, entitlements, product, usage window, eligible users, active users, adopted features, renewal evidence, health evidence, pricing source, currency, and provenance.

Quarantine unresolved identities, overlapping contracts, duplicate events, post-cutoff records, conflicting quantities, stale mappings, and ambiguous currencies.

### 2. Calculate evidence coverage

Report known/eligible counts for identity, entitlement, usage, adoption, renewal, health, pricing, and contact evidence. A high score on a thin evidence slice does not repair low coverage.

### 3. Calculate only approved metrics

Use the helper for:

```text
seat_utilization = observed_active_entitled_users / licensed_seats
feature_adoption = adopted_eligible_features / eligible_features
coverage = known_records / eligible_records
expansion_value = approved_quantity × verified_unit_price
policy_score = sum(approved_component × approved_weight)
```

Zero denominators yield unknown. Over-license utilization may be valid evidence but is not automatically a contract breach or expansion opportunity.

### 4. Apply eligibility before scoring

Evaluate approved health, adoption, utilization, renewal, and exclusion rules. Show each pass, fail, and unknown. Missing required evidence returns `ELIGIBILITY_UNKNOWN`; a failed rule returns `NOT_ELIGIBLE` with the exact blocker.

### 5. Review plays and value

Map only eligible accounts to an approved play. Distinguish unused contracted capacity from products the customer has not purchased. Use verified prices for a value preview; otherwise show `VALUE_UNKNOWN` and the missing evidence.

### 6. Produce an action preview

Show the proposed owner, account, play, evidence, blockers, contact-selection method, message purpose, approver, and intended system action. Keep it in preview state.

## Worked Example

Approved policy `EXP-7` defines core adoption at 0.75, seat utilization at 0.90, health eligibility as required, and renewal timing at 0–120 days. It preapproves score weights of adoption 0.35, utilization 0.35, renewal 0.20, and verified sponsor 0.10.

A fictional account has 6 of 8 eligible features adopted, 90 active entitled users across 100 licensed seats, eligible health, a renewal in 100 days, and no verified sponsor. Its exact policy score is 0.7775. This is a policy score, not a probability. It can be an `INFERRED_CANDIDATE`, but value remains `VALUE_UNKNOWN` without verified pricing and outreach remains unapproved.

## Output Contract

Return six artifacts:

1. **Preflight receipt** — policy, cutoff, population, source coverage, identity join, instrumentation, price basis, and enabled analyses.
2. **Evidence matrix** — account, entitlement, usage, adoption, renewal, health, pricing, provenance, and evidence label.
3. **Eligibility and candidate table** — rule-by-rule results, blockers, candidate label, policy score, and score limitations.
4. **Play and value table** — approved play rule, quantity, unit price, currency, amount basis, value or `VALUE_UNKNOWN`.
5. **Risk and data-gap table** — unknowns, conflicts, stale mappings, low coverage, privacy limits, and excluded accounts.
6. **Action preview and receipt** — proposed human-owned next steps, named approver, arithmetic checks, and explicit no-write/no-send confirmation.

## Failure States

- `POLICY_REQUIRED` — eligibility, play, score, timing, price, currency, or approval policy is missing.
- `IDENTITY_UNRESOLVED` — account records cannot be joined safely.
- `INSTRUMENTATION_UNKNOWN` — usage definitions, account mapping, valid-since date, or coverage is absent.
- `ELIGIBILITY_UNKNOWN` — a required rule lacks evidence.
- `NOT_ELIGIBLE` — an approved blocking rule failed.
- `SCORE_UNAVAILABLE` — components, weights, missing-data treatment, or target is incomplete.
- `VALUE_UNKNOWN` — verified quantity, unit price, amount basis, or currency is absent.
- `MIXED_CURRENCY` — values cannot be aggregated safely.
- `APPROVAL_REQUIRED` — a CRM action, contact selection, or outreach step has not been approved.

Never silently convert one failure state into another metric or recommendation.
