# Scope and policy

Use only a customer-approved policy that is effective at the review cutoff. Require stable policy ID/version, policy owner ID, named human-review role ID, effective and expiry timestamps, UTC cutoff, timezone, approved purpose, prohibited uses, source/schema bindings, correction path, and explicit rule precedence.

Each rule needs a stable rule ID, rule type, exact target, applicability tags, operator or expected observation state, unit/basis/currency where relevant, disposition token, human-review role ID, and precedence. The skill ships no thresholds, score cutoffs, SLAs, retention periods, approval chains, or default segments.

Overlapping top-precedence rules are `POLICY_CONFLICT`. Missing authority or an ineffective policy is `POLICY_REQUIRED`. A rule result never becomes approval, rejection, compliance, risk, or an action.
