# Constraints and relationships

Evaluate only customer-owned hard constraints whose exact type-specific record contains `constraint_id`, `constraint_version`, `type`, a declared `evidence_id`, `policy_id`, `policy_version`, second-precision UTC `effective_at`, `owner_role_id`, and `conflict_path_id`, plus only the account/rep or rep/count fields required by that type. Reject missing or extra fields so unpreserved prose cannot ride through the register.

Supported deterministic checks are pinned pairs, forbidden pairs, allowed pairs, required relationships, and explicit per-rep minimum/maximum account counts. A minimum or maximum is evidence, not a universal capacity rule. Keep strategic-account, language, product, named-account, channel, overlay, continuity, accessibility, and labor constraints in the register when supplied; do not infer them.

Flag a candidate when a required pair is absent, a forbidden pair is present, a count bound is breached, minimum exceeds maximum, or a pair is both pinned and forbidden. Never repair the assignment or relax a constraint automatically. Return the exact conflict to the policy owner.
