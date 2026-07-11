# Codes, Counts, and Rates

Accept only codes listed in the exact bound customer code map. Do not map aliases, parse free text, merge codes, select a primary reason, or translate an observation into a causal label.

The helper owns all numbers. It emits each population size, observation count, no-event count, code count, rule threshold, and derived rate once. A rate receipt references its numerator and denominator receipt IDs and uses the customer-approved Decimal scale and rounding mode. Never compare or combine lanes, sources, subject types, windows, schemas, or code-map versions.
