# Outbound Experiment Playbook

Read this before recommending a rollout or claiming improvement.

## Design

1. State one hypothesis and change one variable.
2. Choose the assignment unit: recipient, account, rep, or sequence.
3. Prevent contamination across variants.
4. Define the eligible population and exclusions before exposure.
5. Choose one primary metric and its exact denominator.
6. Set guardrails: bounce, unsubscribe, complaint, negative reply, and deliverability.
7. Choose minimum detectable effect, power, alpha, duration, and stopping rule before the test.
8. Record planned segments and comparison count.

## Analysis

- Analyze assigned cohorts, not only completed exposures, when the design requires intent-to-treat.
- Report counts, rates, Wilson intervals, absolute difference, relative lift, and adjusted p-value.
- Check sample-ratio mismatch and data loss.
- Do not stop early because one variant temporarily leads.

## Decision

Promote only under the predeclared rule and only if guardrails pass. Record implementation scope, rollback trigger, and measurement window. A statistically detectable difference can still be too small or risky to matter operationally.
