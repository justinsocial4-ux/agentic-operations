# Activity Evidence

The policy defines qualifying activity types, occurrence timestamp, association rule, source, history window, and completeness receipt. Count the most recent qualifying buyer-facing occurrence only when each rule resolves.

Do not use activity creation time, sync time, record modification, completed internal tasks, email pixel loads, or unverified account/contact association as buyer activity.

Missing activity telemetry is `ACTIVITY_EVIDENCE_UNAVAILABLE`. A complete approved history with no qualifying row is `NO_QUALIFYING_ACTIVITY_RECORDED`. Neither state proves buyer disengagement, deal dormancy, close probability, or cause.
