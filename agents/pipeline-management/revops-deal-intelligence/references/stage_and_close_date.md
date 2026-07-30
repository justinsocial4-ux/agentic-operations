# Stage And Close Date

Use stable pipeline and stage IDs from the approved policy. A current stage value is not a dated entry event. Calculate stage age only from the approved current-stage entry receipt; preserve re-entry and conflicting same-time events.

Compare elapsed days only with an approved threshold fixed before results. Return `THRESHOLD_EXCEEDED` or `WITHIN_THRESHOLD`, not stalled, slow, healthy, risk, or slippage.

Treat close date as recorded CRM evidence. Compare it to cutoff and return the exact date state. A past date does not prove expected loss, seller error, buyer delay, or forecast impact.
