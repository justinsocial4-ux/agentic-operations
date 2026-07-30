# LM-03 CRM Write Safety

Read this file before changing ownership, invoking assignment rules, creating queue assignments, or sending notifications.

## Universal Gate

1. Preview first in analysis-only mode.
2. Re-read current owner and eligible-owner state.
3. Show count, objects, fields, and side effects.
4. Obtain explicit final confirmation.
5. Write a bounded batch with stable record IDs.
6. Verify responses and record previous values.
7. Stop on unexpected permission, validation, or automation errors.

## Salesforce

Salesforce assignment rules can assign leads to users or queues and can be triggered differently depending on creation/edit path and configuration. Confirm whether the org wants:

- an active Lead Assignment Rule;
- a direct owner update;
- Flow-managed queue assignment;
- or analysis-only recommendations.

Do not assume `Lead.AssignmentStatus` or `Lead.RoutingTimestamp` custom fields exist. Inspect schema first. Verify queue membership and sharing behavior before using a queue.

Official references:

- https://help.salesforce.com/s/articleView?id=sf.customize_leadrules.htm&type=5
- https://help.salesforce.com/s/articleView?id=sf.queues_overview.htm&type=5

## HubSpot

Retrieve owners through the Owners API. Use the returned owner `id` for assignment; do not substitute `userId`. Update the record's owner property only after validating the property name for that object and portal.

Official references:

- https://developers.hubspot.com/docs/api-reference/latest/crm/owners/guide
- https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide

## Rollback Receipt

For every successful write retain:

- CRM object and record ID;
- previous owner ID;
- new owner ID;
- transaction timestamp and response ID;
- rule version and confirmation reference.

Rollback is a new controlled write, not an unlogged local undo.
