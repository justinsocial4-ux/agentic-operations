# Scoring Policy Contract

Require policy ID/version/owner/effective date, purpose, included/excluded population, legal-entity level, sources/cutoff, feature rules, component limits, missing/conflict rules, optional combined weights, label thresholds, validation status, privacy scope, downstream-use status, approver, and change history.

Each feature rule needs a stable ID, component (`fit` or `engagement`), definition, source field/event, transformation, minimum/maximum points, freshness/validity rule, and missing treatment. `UNAVAILABLE` is the safe default. `ZERO` and `FIXED` are allowed only when explicitly approved and receipted.

Combined weights must be exact, non-negative, and sum to one. Thresholds must be non-overlapping. A label is a customer policy bucket, not an empirical quality class. Policy changes create a new version; do not compare scores across versions without recomputation.

The helper's `POLICY_EVIDENCE_PRESENT` means required receipt fields and exact approval states exist. It does not prove the construct is valid, predictive, fair, lawful, or useful for a decision.
