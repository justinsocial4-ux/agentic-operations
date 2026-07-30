# Amount and discount evidence

Use Decimal strings. Preserve currency and basis such as annual recurring, total contract, gross, net, tax-inclusive, quantity, and term semantics. Do not convert currency or combine unlike bases.

A derived discount is allowed only when customer-approved list and quoted facts belong to the same deal, currency, and basis and list amount is positive. Calculate `(list - quoted) / list * 100` without binary floating point. Keep supplied discount and derived discount separate; unequal values create `EVIDENCE_CONFLICT`.

Missing stays missing and zero stays zero. Do not infer margin, profitability, leakage, forecast impact, revenue, business value, or discount reason.
