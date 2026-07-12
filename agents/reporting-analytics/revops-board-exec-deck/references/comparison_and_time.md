# Comparison and time

Compare only non-overlapping approved periods whose contracts match on unit, currency, amount basis, metric definition, aggregation method, and timezone, with an exact comparison-basis receipt. The supplied local timestamp offsets must match the named IANA timezone. The helper calculates only the approved current-minus-prior delta and percent change.

Never substitute created date for close date, annualize an unknown contract term, convert currency without an approved rate contract, or treat forecast adjustments as raw opportunity amount. A zero prior value produces a null percent change.
