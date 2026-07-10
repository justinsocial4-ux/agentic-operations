# LM-03 Output Contract

Read this file before producing a full preview, review queue, or transaction receipt.

## Markdown Sections

1. **Run contract** — mode, scope, systems verified, policy version, exclusions, capacity timestamp, SLA target.
2. **Reconciliation** — input, ready, review, no-owner, excluded, and fallback counts.
3. **Proposed assignments** — one row per lead.
4. **Manual review** — critical/review flags with evidence and next action.
5. **Write plan or receipt** — exact fields, confirmation state, attempted/succeeded/failed/skipped counts.
6. **Limits** — missing/stale data and unverified systems.

## Assignment Row

```json
{
  "lead_id": "EXAMPLE_LEAD_ID",
  "previous_owner_id": null,
  "proposed_owner_id": "EXAMPLE_OWNER_ID",
  "route_type": "ACCOUNT_TERRITORY",
  "policy_confidence": 90,
  "capacity_score": 50.0,
  "capacity_state": "Yellow",
  "capacity_source": "computed_from_crm",
  "capacity_as_of": "2026-07-10T12:00:00Z",
  "territory": "East",
  "flags": [],
  "decision": "READY",
  "write_status": "NOT_ATTEMPTED",
  "rule_version": "1.1"
}
```

Use `null`, `UNKNOWN`, or `NOT_VERIFIED` instead of filling gaps with estimates.

## Reconciliation

Require:

```text
input = ready + manual_review + no_owner + excluded
attempted = succeeded + failed + skipped
```

Round-robin fallback is a subset of `ready` or `manual_review`, not an extra record count.

## Write Statuses

- `NOT_ATTEMPTED`
- `PENDING_CONFIRMATION`
- `SUCCEEDED`
- `FAILED`
- `SKIPPED_STALE_PREVIEW`
- `SKIPPED_CONFLICT`

Never label a recommendation `SUCCEEDED`.
