# Route and assignment contract

- Each approved route version binds one event, one owner role, one channel token, one authorization window, one planned-time window, and route/authorization/channel/owner/timing policy receipts.
- Each declared participant has exactly one supplied plan row, participation-state receipt, and plan receipt.
- `eligible` rows require one human-supplied route, owner, channel, planned time, and unique assignment receipt. `suppressed`, `unauthorized`, `conflicting`, and `missing` rows carry none.
- A matched route proves only that the supplied assignment matches the frozen contract. It does not prove permission, contactability, priority, urgency, likely conversion, or authorization to execute.
