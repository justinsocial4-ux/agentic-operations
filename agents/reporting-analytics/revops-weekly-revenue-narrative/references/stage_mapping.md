# Stage Mapping Guide

Read this when a customer has custom pipeline stages.

## Canonical reporting groups

Use these only as reporting groups, not as replacements for CRM values:

- `PROSPECTING`
- `QUALIFIED`
- `DISCOVERY`
- `PROPOSAL`
- `NEGOTIATION`
- `CLOSED_WON`
- `CLOSED_LOST`

## Mapping rules

1. Retrieve the pipeline and stage IDs plus labels from the CRM.
2. Ask the pipeline owner to approve an exact mapping by `(pipeline_id, stage_id)`.
3. Preserve the original ID and label beside the canonical group.
4. Never infer `is_closed` or `is_won` solely from a label; use CRM outcome metadata.
5. Leave unapproved values as `UNMAPPED` and show them separately.
6. Version every mapping with owner, approval date, and effective date.

Example:

```json
{
  "mapping_version": "2026-07-10",
  "approved_by": "revops-owner",
  "stages": {
    "new_business:appointmentscheduled": "DISCOVERY",
    "new_business:contractsent": "PROPOSAL"
  }
}
```

Do not apply one pipeline's mapping to another pipeline with matching labels. Internal IDs and business meanings can differ.
