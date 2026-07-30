# Source and rule contract

Each lane freezes one platform, source version, schema version, observation kind, field definition, value kind, unit, denominator definition, observation window, complete observation population, source authorization, and one versioned customer rule whose effective window covers the observation window.

- Numeric rules use only `lt`, `lte`, `eq`, `ne`, `gte`, or `gt`.
- Boolean and opaque source-code rules use only `eq` or `ne`.
- Ratios and percentages require an exact denominator definition and receipt.
- Each rule threshold appears once in its rule receipt; each matched observation value appears once in its observation receipt.
- Every lane needs source-authorization, field-definition, denominator-definition, rule, rule-approval, population, completeness, privacy, and source-documentation receipts.
- Extra or absent observations fail the complete-population gate.
