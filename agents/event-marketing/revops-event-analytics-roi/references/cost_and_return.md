# Cost And Return

Lock the cost basis: actual versus estimate, direct/allocated categories, internal labor, travel, sponsorship, taxes, refunds/credits, capitalization, currency, dated FX, period, owner, and approval.

Report estimates as `PRELIMINARY_COST`. Do not blend currencies or actual and estimated categories silently.

Keep these measures separate:

- cost efficiency = approved cost / exact approved count
- CRM amount = the platform's stated opportunity amount basis
- model-attributed CRM amount = CRM amount × configured credit
- finance-defined benefit = recognized revenue, gross profit, contribution, cash, or another explicitly approved basis
- finance-defined return = (approved benefit − approved actual cost) / approved actual cost
- incremental ROI = the same formula using a causally estimated incremental benefit

No approved benefit means `BENEFIT_BASIS_REQUIRED`. No counterfactual/incremental estimate means `INCREMENTAL_ROI_UNAVAILABLE`.
