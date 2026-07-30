# Employee Data Contract

Require pseudonymous employee ID, approved role/cohort, start anchor, policy ID/version, source-system IDs, requester authorization, cutoff, extraction/effective times, and minimum necessary milestone fields.

Treat names, email, phone, compensation, notes, leave/accommodation reasons, demographic attributes, and employment actions as restricted. Do not output them. Join by stable approved IDs; if email is explicitly approved as a temporary key, report duplicate, changed, unmatched, and collision counts without exposing addresses.

Record retention, output location, access list, deletion policy, source precedence, corrections, and late-entry handling. Report HRIS, LMS, CRM, activity, opportunity, and quota coverage separately.
