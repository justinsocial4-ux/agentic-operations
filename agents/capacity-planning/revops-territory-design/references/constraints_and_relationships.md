# Constraints and relationships

Evaluate only versioned, customer-owned hard constraints with a constraint ID, evidence ID, policy ID, effective time, owner, and conflict path.

Supported deterministic checks are pinned pairs, forbidden pairs, allowed pairs, required relationships, and explicit per-rep minimum/maximum account counts. A minimum or maximum is evidence, not a universal capacity rule. Keep strategic-account, language, product, named-account, channel, overlay, continuity, accessibility, and labor constraints in the register when supplied; do not infer them.

Flag a candidate when a required pair is absent, a forbidden pair is present, a count bound is breached, minimum exceeds maximum, or a pair is both pinned and forbidden. Never repair the assignment or relax a constraint automatically. Return the exact conflict to the policy owner.
