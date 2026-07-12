# Amount evidence

Treat each amount as a sourced business measure. Require account ID, exact value, currency, period, basis, evidence ID, source version, cutoff, and finance/metric owner.

Keep ARR, ACV, bookings, recognized revenue, open pipeline, forecast, quoted value, and customer-defined potential separate. Never substitute one for another. Do not impute missing amounts with a median, zero, neutral score, industry value, or model estimate.

Aggregate only exact non-negative values that share currency, period, and basis. Report missing and unknown records beside the coverage count. Cross-currency or mixed-basis candidates are `INCOMPARABLE` unless an approved conversion policy supplies rate source, rate timestamp, target currency, and rounding treatment.

Per-rep totals are descriptive allocation evidence. Include every declared in-scope rep; emit an exact zero only for a rep with no assigned accounts under one valid common basis. When the basis is unresolved or incompatible, keep every rep row and emit `null` rather than dropping the population or inventing a zero. These totals do not prove fairness, capacity, expected revenue, quota attainment, or performance.
