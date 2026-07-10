# PM-01 Output Contract

Read before producing a full deal table, digest, or JSON receipt.

## Deal Record

```json
{
  "deal_id": "EXAMPLE_DEAL_ID",
  "owner_id": "EXAMPLE_OWNER_ID",
  "stage": "Negotiation",
  "amount": 100000,
  "currency": "USD",
  "raw_points": 64,
  "evidence_coverage": 100,
  "health_score": 64.0,
  "health_status": "Green",
  "stall_status": "NOT_STALLED",
  "activity_source": "crm_buyer_activity",
  "flags": ["MISSING_OR_PLACEHOLDER_NEXT_STEP"],
  "as_of": "2026-07-10T12:00:00Z",
  "rule_version": "1.1"
}
```

## Reconciliation

Require:

```text
input = open_in_scope + excluded + closed_out_of_scope
open_in_scope = green + yellow + red + unknown
```

Stalled, overdue, and flagged are overlapping subsets and must not be added to status totals.

## Amount Rules

- Group by currency unless an approved conversion exists.
- Label sums as gross pipeline amount.
- Never turn a status amount into revenue loss without a separate approved forecast model.

## Run Status

- `COMPLETE_READ_ONLY`
- `INCOMPLETE_PAGINATION`
- `INCOMPLETE_API_ERROR`
- `PENDING_ALERT_CONFIRMATION`
- `ALERTS_PARTIAL`
- `ALERTS_COMPLETE`
