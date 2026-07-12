# Provider and charge contract

- Require a stable pseudonymous provider and contract version with authorization, terms, geography, field-support, price, and charge-unit receipts.
- Accept only `per-route-assignment` charges in the policy currency. Unit costs are customer-supplied non-negative decimal strings, never vendor defaults.
- Planned charge equals the frozen unit cost for one matched route assignment. Aggregate only matched same-currency routes.
- Planned charge is not actual credit consumption, an invoice, a cost forecast, a provider recommendation, or permission to spend.
