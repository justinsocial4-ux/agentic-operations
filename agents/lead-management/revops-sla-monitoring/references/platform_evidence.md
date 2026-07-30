# Platform evidence

Map each platform field to the customer's event contract before evaluation.

Salesforce represents Tasks and Events as related activity entities; association and field meaning must be verified in the customer org: https://developer.salesforce.com/docs/platform/data-models/guide/tasks-events.html .

HubSpot represents calls, emails, meetings, notes, and tasks as separately associated CRM activity objects. Its meeting API distinguishes `hs_timestamp` (occurrence) from object `createdAt`: https://developers.hubspot.com/docs/api-reference/latest/crm/activities/meetings/guide and https://developers.hubspot.com/docs/api-reference/latest/crm/understanding-the-crm .

Do not assume platform editions, object availability, custom fields, scopes, limits, associations, or timestamps are portable. Record the exact source/version and verify live configuration.
