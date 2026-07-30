# Population and identity

Require complete frozen account and rep populations. Each rep ID must match exactly `rep-` plus 32 lowercase hexadecimal characters. Readable suffixes, names, emails, uppercase hex, short values, extra segments, and arbitrary strings are not pseudonymous IDs.

Require a separate approved pseudonymization receipt with an opaque receipt ID, population ID, method ID, namespace ID, policy ID, owner-role ID, approval state, and the exact declared rep-ID set. Missing, unapproved, malformed, extra-field, or population-mismatched receipts fail closed. The receipt proves only that the customer supplied an approved pseudonymization artifact; it does not prove anonymity or authorize re-identification.

Every in-scope account must appear exactly once in each candidate. Multiple reps are permitted only under an approved shared/team model that defines roles and counting treatment. Every declared in-scope rep must remain visible in count, amount, and route summaries, including a zero-assignment row. Preserve missing, duplicate, unassigned, unknown, excluded, pinned, overlay, and relationship records as explicit states.

Use approved work-anchor IDs for route evidence. Do not ingest names, emails, home addresses or coordinates, protected traits, manager narratives, content, historical quota attainment, discipline, or performance by default. Leave, ramp, accommodation, accessibility, labor-rule, and identity conflicts go to `IDENTITY_REVIEW`; they do not become zero capacity or neutral values.
