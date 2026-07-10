# PM-01 Alert And Write Safety

Read before sending email/Slack alerts, editing CRM records, or scheduling a recurring audit.

## Confirmation Gate

1. Produce a read-only preview.
2. Show recipients, channels, count, exact sample, and records affected.
3. Re-read live state and skip changed deals.
4. Obtain explicit final confirmation.
5. Send or write a bounded batch.
6. Verify each response and report success, failure, and skipped counts.

## Messaging Rules

- Describe facts and evidence gaps, not employee intent or performance.
- Do not disclose one rep's pipeline to another rep.
- Avoid unsupported claims about commission, forecast loss, or buyer disengagement.
- Use gross flagged amount, not predicted revenue loss.
- Preserve a link or stable ID for the underlying record.

## CRM Rules

PM-01 is read-only by default. Never fill missing amount, stage, close date, or next step automatically. A separate approved correction workflow must identify the exact field, old value, proposed value, and rollback evidence.

## Scheduling

A request for “daily” output does not authorize creating a recurring automation unless the user explicitly asks to schedule it. Record timezone, owner, recipients, stop conditions, and failure notifications before creating one.
