---
name: revops-competitive-pricing
description: "Reviews complete pseudonymous competitive-price evidence and calculates exact differences only for customer-approved same-basis observation pairs. Make sure to use this skill whenever the user asks to compare competitor prices, monitor pricing, analyze a pricing objection, recommend a discount, hold or change price, rank pricing threats, create a battle card, alert sales, update CRM, or coach a seller—even when the request assumes scraped pages, transcripts, reviews, deal amounts, or historical outcomes are comparable."
metadata:
  category: "Pricing and Deal Strategy"
  phase: "2"
  data_readiness: "approved_policy_complete_source_populations_exact_basis_authorization_and_timestamp_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved purpose, source, comparison-basis, privacy, calculation, and correction policies"
  mcps:
    - "Approved structured price evidence in read-only mode"
  minimum_data:
    - "Stable policy, source, basis, party, item, observation, population, comparison, and receipt IDs"
---

# Competitive Price Evidence Review

Report only what supplied structured price records prove. Do not scrape, infer a price from text, manufacture package equivalence, or turn a price difference into negotiation, discount, positioning, or seller guidance.

## Exact Response Rule

Build the input document, run `scripts/price_evidence.py`, and return `render_review_output(review_price_evidence(document))` byte for byte. The first response byte must be `{`; the final response byte must be the helper's newline after `}`. Do not use Markdown fences or add model prose. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, dates, prohibited uses, calculation policy, or correction paths.
- Read `references/source_and_population.md` before accepting source authorization, capture provenance, or completeness.
- Read `references/comparison_basis.md` before treating two price observations as comparable.
- Read `references/price_math.md` before calculating differences or percentages.
- Read `references/privacy_and_workforce.md` before accepting customer, competitor, seller, transcript, review, or page data.
- Read `references/current_platform_limits.md` before mapping Salesforce, HubSpot, public-page, quote, transcript-code, or review-code evidence.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_boundaries.md` before discussing discounts, negotiation, positioning, monitoring, alerts, CRM changes, or workforce action.
- Use `scripts/price_evidence.py` for strict validation, population reconciliation, Decimal arithmetic, comparability, and exact rendering.

## Operating Rules

1. Work read-only. Do not query, scrape, crawl, monitor, message, alert, schedule, export, cache, log externally, or modify any CRM, quote, pricebook, page, task, channel, deal, price, product, or worker record.
2. Require an effective customer policy with stable ID/version, owner, human reviewer, approved purpose, prohibited uses, UTC cutoff, timezone, correction path, exact calculation policy, source bindings, and comparison bases.
3. Accept only pre-supplied structured observations. Reject names, domains, URLs, emails, phones, addresses, free text, notes, transcripts, quotes, reviews, posts, job titles, protected traits, and seller-performance fields.
4. Keep `public_list`, `supplied_quote`, `transcript_code`, `review_code`, and `internal_offer` lanes independent. Never use one lane to fill, validate, average, or reinterpret another.
5. Reconcile the complete declared observation population and every complete lane/source population. Missing, duplicate, extra, stale, future, unauthorized, or conflicting evidence fails closed.
6. Require each observation to bind exact party/item/source/schema/authorization/basis IDs, price kind, product/configuration scope, quantity, unit, currency, billing basis and period, term, region, tax/fee/discount basis, effective window, occurrence time, and capture time.
7. Compare only a customer-declared observation pair with the same approved comparison-basis ID/version and a comparison time inside both effective windows. Otherwise return `NOT_COMPARABLE` or `SOURCE_REQUIRED`.
8. Never convert currency, annualize, normalize quantity, average prices, infer discounts, allocate tax or fees, translate packages, impute missing values, or treat a CRM deal amount as a unit price.
9. Use Decimal strings and the exact approved scale and rounding mode. The right-side amount must be positive before calculating a percentage difference.
10. A public list, supplied quote, transcript code, review code, and internal offer remain what their lane says. None proves a paid price, market price, product parity, customer intent, outcome, cause, or future availability.
11. Never calculate or claim confidence, threat, risk, rank, win rate, churn, elasticity, lost revenue, margin, ROI, market share, forecast impact, or intervention effect.
12. Never recommend holding, raising, lowering, matching, or discounting price; walking away; changing terms; adding value; creating messaging or battle cards; monitoring; alerting; writing CRM; or acting on a customer or worker.
13. R1: never characterize evidence adequacy with an adjective unless an exact approved numeric customer rule defines that exact label. This helper emits no adequacy label.
14. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
15. Freeze policy, normalized inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate policy, source authorization, dates, bases, calculation rules, prohibited uses, and correction path.
2. **Reconcile populations.** Validate the declared observation IDs and every complete lane/source population.
3. **Register observations.** Validate exact structured fields, positive Decimal price, source/basis bindings, and timestamps.
4. **Evaluate pairs.** Return `COMPARABLE`, `NOT_COMPARABLE`, or `SOURCE_REQUIRED` from exact receipt evidence.
5. **Calculate carefully.** For comparable pairs only, create one Decimal difference receipt and one percentage receipt referencing the two observation receipts.
6. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: an approved internal-offer observation and public-list observation reference the same customer-approved product/configuration/quantity/unit/currency/period/term/region/tax/fee/discount/price-kind basis and overlap at the declared comparison time.

Run the helper. Its JSON response marks the pair `COMPARABLE` and places the exact amount difference and percentage in their assigned receipts. It does not call either price expensive, recommend a discount, explain a deal outcome, or authorize action.

## Failure Boundary

Missing or incompatible policy, authorization, population, party, item, source, schema, basis, amount, effective window, timestamp, privacy, calculation, or correction evidence remains unresolved. Never replace it with scraping, text extraction, fuzzy matching, conversion, normalization, confidence, causal inference, commercial advice, alerting, CRM activity, customer action, or workforce action.
