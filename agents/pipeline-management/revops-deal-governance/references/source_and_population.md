# Source and population

Freeze the declared deal population at one offset-aware cutoff. Reconcile the declared count, supplied deal rows, and stable pseudonymous IDs exactly. Preserve zero-value and unresolved rows.

Every deal and evidence row must carry approved source ID, schema version, and occurrence or extraction timestamp. A policy source binding must match each row. Do not silently prefer CRM over CPQ, current over history, or one duplicate over another.

Reject names, email addresses, phones, free-text notes, contract text, message content, protected traits, home location, rep seniority, historical performance, manager rankings, and coaching attributes. Source conflicts remain `EVIDENCE_CONFLICT`.
