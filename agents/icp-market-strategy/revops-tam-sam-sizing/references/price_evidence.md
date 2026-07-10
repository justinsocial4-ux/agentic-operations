# Price evidence

Require one exact price receipt per segment: non-negative Decimal-compatible value, currency, period, business basis, source/version, cutoff, evidence ID, and finance/metric owner.

Keep list price, contract value, ACV, ARR, bookings, recognized revenue, customer spend, and average won-deal amount separate. A won-deal average is selected historical evidence, not automatically the price of every addressable unit.

Do not impute a missing price, borrow a price from another segment, mix currencies or periods, or silently apply exchange/inflation factors. Any conversion needs its own approved rate, timestamp, source, rounding, and policy receipt outside this helper version.
