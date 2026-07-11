---
name: revops-deal-governance
description: "Reviews a complete frozen set of deal, amount, contract-observation, and approval-process evidence against an approved versioned customer governance policy, then returns exact neutral rule receipts without approving, routing, changing CRM state, or making legal or workforce determinations. Make sure to use this skill whenever the user asks to validate deal governance, check discount policy, inspect contract-policy evidence, review approval requirements, audit deal terms, route a deal for approval, or check whether a quote follows policy—even if they do not name the agent."
metadata:
  category: "Pipeline Management"
  phase: "2"
  data_readiness: "approved_policy_complete_deal_population_amount_document_process_privacy_and_access_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved deal-governance, document-review, approval-process, privacy, access, and correction policies"
  mcps:
    - "Approved CRM, CPQ, contract, or warehouse evidence in read-only mode"
  minimum_data:
    - "Stable policy, deal, account, owner, fact, document, observation, process, source, schema, and receipt IDs"
---

# Deal Governance Evidence Review

Review what supplied evidence proves against customer-owned deal-governance rules. Do not turn a numeric comparison, phrase observation, missing field, or configured approval step into deal approval, legal compliance, risk, severity, or an operational action.

## Exact Response Rule

Build the input document, run `scripts/deal_governance.py`, and return `render_review_output(review_governance(document))` byte for byte. The first response byte must be `{`; the final response byte must be the helper's newline after `}`. Do not use Markdown code fences. Write no model-generated introduction, table, calculation, summary, correction, or text outside helper stdout. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, rules, dates, roles, or precedence.
- Read `references/source_and_population.md` before using deal, quote, account, policy, or platform evidence.
- Read `references/amount_and_discount.md` before calculating or comparing money, price, discount, term, currency, or basis.
- Read `references/contract_observations.md` before using contract text, clause observations, documents, amendments, or locators.
- Read `references/approval_process.md` before using approval criteria, roles, submitters, permissions, sequence, notifications, locks, or side effects.
- Read `references/privacy_and_workforce.md` before accepting seller, approver, customer, contract, activity, or performance data.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_boundaries.md` before discussing approvals, CRM changes, tasks, messages, escalations, contract edits, or downstream action.
- Read `references/current_platform_limits.md` before mapping Salesforce, HubSpot, CPQ, CLM, file, or workflow fields.
- Use `scripts/deal_governance.py` for strict validation, Decimal arithmetic, population reconciliation, independent rule evaluation, and exact output rendering.

## Operating Rules

1. Work read-only. Do not query or modify a CRM, CPQ, CLM, quote, contract, approval process, price, discount, owner, stage, task, message, alert, schedule, or record lock.
2. Require an effective customer policy with stable ID/version, owner, named human reviewer role, approved purpose, prohibited uses, UTC cutoff, timezone, source/schema bindings, correction path, and explicit rule precedence.
3. Require a complete frozen declared deal population and reconcile it exactly. Never omit zero-value, missing-document, unresolved, or conflicting deals.
4. Use pseudonymous deal, account, and owner IDs. Reject names, emails, phones, free text, message content, protected traits, home location, rep seniority, historical performance, manager ranking, and coaching fields.
5. Treat supplied discount and price-derived discount as separate evidence. Derive only from same-currency, same-basis positive list and quoted amounts using Decimal; preserve conflicts and never default missing values.
6. Preserve money and percentage basis, currency, term, tax, quantity, recurring/non-recurring, annual, and total-contract-value semantics. Never convert or combine incompatible facts.
7. Do not parse, OCR, fuzzy-match, summarize, or interpret contract language. Accept only structured observations tied to an exact document ID, version, SHA-256, locator, method, timestamp, and policy key.
8. `OBSERVED` and `NOT_OBSERVED` describe supplied evidence only. They do not establish legal compliance, enforceability, risk, severity, or required remediation.
9. Require complete-document, amendment, and precedence receipts. Missing or conflicting versions, locators, amendments, or governing-document relationships require human document review.
10. Treat approval entry criteria, submitters, roles, sequence, permissions, edition, notifications, locks, and side effects as customer/platform evidence. Never invent or execute them.
11. Evaluate exact applicable policy rules independently. If top-precedence rules overlap, conflict, lack a fact, or have incompatible units/bases, return an unresolved state instead of choosing.
12. A rule match is not an approval. A rule non-match is not a rejection, violation, or legal conclusion. Human reviewers own every decision and action.
13. Never infer margin leakage, revenue impact, forecast effect, sales-cycle change, causal outcome, seller intent, performance, coaching need, or the correct approver.
14. R1: never characterize evidence adequacy with `small`, `large`, `enough`, `limited`, `insufficient`, `good`, `poor`, `high`, or `low` unless an approved numeric rule defines that exact label.
15. R2: return one helper-rendered response. Every numeric value must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
16. Freeze policy, normalized inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze scope.** Validate purpose, policy authority, dates, rules, precedence, sources, roles, privacy, access, and prohibited uses.
2. **Register evidence.** Validate complete deals, numeric facts, contract observations, approval-process observations, and field-level provenance.
3. **Reconcile.** Check declared population, stable IDs, source/schema bindings, deal links, document versions, and process versions.
4. **Calculate facts.** Use Decimal for approved derived discounts; preserve missing, incompatible, and conflicting facts.
5. **Evaluate rules.** Return exact neutral states with fact/observation receipt references and named human-review roles.
6. **Render once.** Paste exact helper stdout and nothing else.

## Failure Boundary

Missing or incompatible policy, population, source, schema, amount, currency, basis, document, amendment, locator, process, permission, privacy, or access evidence remains unresolved. Never replace it with a default, proxy, fuzzy match, score, confidence, severity, legal conclusion, or recommendation.
