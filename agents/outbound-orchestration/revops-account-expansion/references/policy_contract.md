# Expansion Policy Contract

An expansion review is customer-specific. Before classification, require a versioned policy containing:

- approved customer/account population and hierarchy treatment
- products, SKUs, editions, entitlements, and whitespace definition
- observation window and freshness rules
- active-user, eligible-user, adopted-feature, and utilization definitions
- health, support, payment, contract, exclusion, and renewal gates
- seat, cross-sell, upgrade, rollout, or other play eligibility
- score components, transformations, weights, missing-data treatment, target, and threshold
- amount field/basis, price source, quantity rule, currency, discounts, and FX policy
- contact-selection, privacy, approval, CRM-write, and outreach rules

## Decision order

1. Verify identity and evidence availability.
2. Apply blocking/exclusion rules.
3. Apply eligibility rules.
4. Calculate an approved score only if complete.
5. Select an approved play only after eligibility.
6. Calculate value only from verified commercial evidence.
7. Preview an action for human approval.

## Forbidden defaults

Do not import the legacy 15-account minimum; ARR floor; 80%, 70%, or 85% coverage gates; 90-day freshness; six-month maturity; 1.3 seat buffer; 40/30/30 score; 20–25% ARR multiplier; 15% plan uplift; 1.5–2x rollout estimate; tier bands; or 90–120-day renewal window.

Those values may appear only when the customer's named policy approves them for the stated population and decision.

## Prospective changes

Document a rule before inspecting the decision outcomes it will govern. A rule invented after seeing results is a hypothesis for a future independent review, not a valid verdict on the current population.
