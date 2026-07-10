# Research and Claim Status

Read this file before repeating external benchmarks, vendor features, lift, labor, pricing, or outcome claims.

## Current primary documentation

- Salesforce Field History Tracking documents that tracked changes include time and old/new values, history begins only after tracking is enabled, and history is stored in object-specific history objects: <https://help.salesforce.com/s/articleView?id=xcloud.tracking_field_history.htm&language=en_US&type=5>
- Salesforce Lead Fields documents that Lead Status is an org picklist such as Open, Contacted, or Qualified: <https://help.salesforce.com/s/articleView?id=sales.leads_fields.htm&language=en_US&type=5>
- HubSpot lifecycle-stage documentation defines Marketing Qualified Lead and Sales Qualified Lead, supports customized stages, and documents stage-entry/exit history properties: <https://knowledge.hubspot.com/records/use-lifecycle-stages>
- HubSpot's Contacts API supports requesting current and historical property values through `propertiesWithHistory`: <https://developers.hubspot.com/docs/api-reference/latest/crm/objects/contacts/guide>

These sources support the data-access and lifecycle-history contract. They do not establish one universal MQL-to-SQL benchmark, conversion window, minimum sample size, drift threshold, or guaranteed revenue lift.

## Legacy claims excluded from decisions

Do not present the old 80–90% healthy rate, 15-point alert, 30% drift index, 85% accuracy band, 37% cycle claim, labor estimates, tool prices, or revenue-lift figures as universal facts. The legacy research relies heavily on vendor and consultancy material, includes arithmetic extrapolations, and does not establish that those values apply to a customer's process.

Use customer history, targets, and preapproved monitoring rules. Label external context by source and date; never convert it into an automatic threshold.
