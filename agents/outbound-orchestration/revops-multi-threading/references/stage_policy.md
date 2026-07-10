# Stage-to-Role Policy

Read this before declaring a role missing.

Create a customer-approved policy per pipeline and sales motion:

```json
{
  "policy_version": "2026-07-10",
  "pipeline_id": "new-business",
  "approved_by": "revenue-leader",
  "stages": {
    "discovery": ["Champion", "Technical Buyer"],
    "negotiation": ["Champion", "Economic Buyer", "Technical Buyer", "Budget Holder"]
  },
  "late_stage_ids": ["negotiation", "contract"]
}
```

Requirements vary by product, deal size, procurement process, and sales motion. Preserve original stage IDs. If a stage is unmapped or the policy is absent, report contact depth and evidence but do not invent required roles.

Version changes with owner, date, rationale, and effective scope.
