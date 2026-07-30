# Classification rules

Each event type has one customer-authored rule with an integer recency window in seconds. For `observed` evidence, the helper compares the event occurrence time with the policy cutoff and emits exactly `OBSERVED_WITHIN_RULE_WINDOW` or `OBSERVED_OUTSIDE_RULE_WINDOW`.

`missing`, `conflicting`, `suppressed`, and `unauthorized` evidence bypass recency classification and remain exact evidence-handling states. None is an intent, priority, fit, urgency, quality, or confidence label.
