---
name: revops-cpq-assist
description: "Reviews a complete frozen quote, catalog, pricebook, configuration-rule, pricing-rule, and approval-process evidence packet using exact customer-owned policy. Make sure to use this skill whenever the user asks to configure a quote, check products or bundles, calculate quote pricing or discounts, validate CPQ rules, inspect approval requirements, build a customer quote, route an approval, or update CPQ—even when they ask for recommendations or operational action."
metadata:
  category: "Pricing and Deal Strategy"
  phase: "2"
  data_readiness: "approved_policy_complete_quote_lines_exact_catalog_pricebook_rule_process_and_access_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved catalog, pricebook, quote, configuration, pricing, approval, privacy, access, and correction policies"
  mcps:
    - "Approved CRM or CPQ evidence supplied in read-only normalized form"
  minimum_data:
    - "Stable policy, quote, line, item, pricebook, rule, process, source, schema, and receipt IDs"
---

# Quote Configuration Evidence Review

Review what a frozen quote packet proves against customer-owned configuration and pricing rules. Do not invent a product, price, bundle, discount, margin, approval, customer message, or system action.

## Exact Response Rule

Build the input document, run `scripts/quote_configuration.py`, and return `render_review_output(review_quote_configuration(document))` byte for byte. The first response byte must be `{`; the final response byte must be the helper's newline after `}`. Do not use Markdown fences. Add no model-written introduction, table, calculation, summary, correction, recommendation, or text outside helper stdout.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting authority, purpose, rules, precedence, or reviewer roles.
- Read `references/catalog_and_population.md` before accepting quote lines, catalog items, pricebooks, versions, or completeness.
- Read `references/pricing_math.md` before using quantity, unit price, discount, currency, basis, billing period, tax, fee, shipping, ramp, usage, or term evidence.
- Read `references/configuration_rules.md` before evaluating required, excluded, or quantity-bound item combinations.
- Read `references/approval_process.md` before using approval conditions, modes, roles, permissions, statuses, notifications, or side effects.
- Read `references/privacy_and_security.md` before accepting customer, contact, seller, approver, activity, or arbitrary-expression data.
- Read `references/current_platform_limits.md` before mapping Salesforce, HubSpot, Revenue Management, CPQ, quote, deal, product, or line-item fields.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_boundaries.md` before discussing products, prices, approvals, PDFs, customer sends, CRM changes, legal/finance conclusions, or worker action.
- Use `scripts/quote_configuration.py` for strict validation, Decimal arithmetic, exact reconciliation, closed-rule evaluation, and rendering.

## Operating Rules

1. Work read-only. Do not authenticate, query, write, submit, approve, reject, route, notify, send, generate a PDF, create a link, or change any quote, item, price, rule, process, CRM, CPQ, contract, invoice, subscription, task, message, owner, or worker record.
2. Require an effective customer policy with stable ID/version, owner, human reviewer role, approved purpose, fixed prohibited uses, cutoff, timezone, correction path, exact bindings, and explicit precedence.
3. Reconcile the complete frozen declared quote-line population exactly. Never omit zero-price, adjustment-bearing, conflicting, or unresolved lines.
4. Use pseudonymous IDs. Reject names, emails, phones, addresses, contacts, message/free text, activities, protected traits, job titles, buying-committee fields, and performance, quota, compensation, ranking, or coaching data.
5. Bind every line to one active exact catalog item and catalog/pricebook version. Preserve item type, unit, quantity precision, currency, price basis, billing period, effective interval, and source/schema provenance.
6. Use plain Decimal strings. Derive line list amount, quoted amount, discount amount, and discount percentage only when quantity, unit, currency, basis, billing period, effective version, and positive list price match exactly.
7. Never call a discount margin. Never infer cost, tax, fee, shipping, FX, TCV, ARR, ACV, MRR, recognized revenue, payment, profitability, willingness to pay, close probability, or AOV uplift.
8. Never combine currencies or one-time, recurring, ramp, usage, tax, fee, shipping, future, or indefinite-term components. Preserve `NOT_COMPARABLE` and exact grouping keys.
9. Evaluate only closed-schema customer rules. Never use `eval`, code, arbitrary expressions, regex, fuzzy matching, model classification, historical-win inference, or a default rule.
10. Product requirement/exclusion and quantity rules describe exact supplied configuration evidence. They do not recommend a bundle, alternative, upsell, or negotiation term.
11. Approval evidence is descriptive. Preserve exact process/version, mode, roles, permissions, side-effect receipt, and observed status. Never select a person, calculate an SLA, initiate approval, or declare authorization.
12. Rule overlap, equal-precedence disagreement, missing scope, incompatible facts, or broken approval evidence requires human review. Never choose or suppress a rule silently.
13. R1: never characterize adequacy with `small`, `large`, `enough`, `limited`, `insufficient`, `good`, `poor`, `high`, or `low` unless an approved numeric rule defines that exact label.
14. R2: every numeric fact is helper-owned and appears once in its fact or rule receipt. Other sections reference IDs; never recompute, repeat, narrate, or self-correct numbers.
15. Freeze policy, normalized evidence, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate policy, purpose, prohibited uses, effective dates, bindings, rules, roles, privacy, access, and correction path.
2. **Reconcile evidence.** Validate declared lines, exact catalog/pricebook items, approval processes, source/schema versions, and pseudonymous IDs.
3. **Register facts.** Store each supplied numeric value once; validate Decimal, unit, currency, basis, period, quantity precision, time, and adjustment flags.
4. **Derive carefully.** Produce same-basis line facts and exact groups only; preserve conflicts and non-comparability.
5. **Evaluate rules.** Return neutral rule states referencing fact/rule/process receipts and named reviewer roles.
6. **Render once.** Paste exact helper stdout and nothing else.

## Failure Boundary

Missing or incompatible policy, population, catalog, pricebook, item, rule, process, permission, source, schema, quantity, unit, currency, basis, period, effective date, privacy, or access evidence remains unresolved. Never replace it with a product, price, discount, margin, confidence, commercial tier, approval, customer message, or action.
