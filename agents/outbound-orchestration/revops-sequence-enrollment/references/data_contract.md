# Data Contract

Require durable person/contact ID, account ID, qualification source/status/time, masked email or channel identifier, contactability status/time/source, suppression and do-not-contact state, bounce state, owner/territory, active enrollments, recent send/enrollment timestamps, frequency count/window, and cutoff.

For routing, require verified current title and industry only when the approved policy uses them. Preserve raw values separately from mapped categories. Activity evidence needs event type, event time, source, and actor certainty.

Report identity, contactability, suppression, mapping, enrollment, and activity coverage separately. Quarantine duplicates, conflicting suppression states, stale mappings, unknown workspaces, and events after cutoff. Missing is not false, Cold, or eligible.
