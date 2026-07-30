# Metric Semantics

## Approved lanes

The helper recognizes only:

- `calls_logged` with unit `count`;
- `emails_logged` with unit `count`;
- `meetings_occurred` with unit `count`;
- `active_pipeline_amount` with unit `money` plus currency and amount basis;
- `active_opportunity_count` with unit `count`;
- `closed_won_count` with unit `count`;
- `closed_lost_count` with unit `count`.

The policy may allow a subset. It may not rename a lane into a judgment.

## No semantic substitution

A logged call is not a conversation, effort, productivity, or customer impact. An email log is not a delivered or read email. A meeting occurrence is not necessarily a booked meeting. An opportunity count is not pipeline quality. A closed state is not proof of a transition time or cause without source-specific history evidence.

Never sum calls, emails, and meetings into one activity score. Never divide unlike periods or unlinked populations into a conversion or attribution rate. Never convert missing evidence to zero.

## Platform boundary

CRM schemas, fields, associations, timestamps, stages, currencies, amount bases, and permissions are organization-specific. This skill does not query or map a CRM. It accepts only the customer's already-approved aggregate evidence and exact source receipts.
