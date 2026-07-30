# Source and metric contract

Each lane freezes one provider, source version, schema version, lane kind, metric definition, value kind, unit, denominator definition, observation window, complete observation population, and authorization window.

- Never rename a vendor field into a broader construct.
- Never silently convert ratios, percentages, counts, codes, or booleans.
- A denominator is required for ratios and percentages.
- Every lane needs source-authorization, metric-definition, denominator, population, completeness, privacy, and source-documentation receipts.
- Every observation repeats the exact contract identifiers and supplies unique capture and state receipts.
- Extra or absent observations fail the complete-population gate.
