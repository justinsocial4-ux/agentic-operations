# Population And Identity

Freeze one complete declared population of pseudonymous account IDs. Reconcile declared count, IDs, every source-population receipt, and every fact. Preserve zero-event and unresolved accounts. Missing, duplicate, extra, or silently excluded accounts invalidate reconciliation.

Each source requires an exact customer-owned mapping from the declared account ID to one external pseudonymous account ID under an approved source, schema, lane, and link version. Reject fuzzy name, domain, address, employee-count, contact, or approximate matching. Do not choose among one-to-many or many-to-one links; preserve the conflict for human correction.

`NO_EVENT_RECORDED` is valid only when the exact source population is declared complete and includes that account. Absence from an incomplete or missing population is `SOURCE_REQUIRED`, not a zero.
