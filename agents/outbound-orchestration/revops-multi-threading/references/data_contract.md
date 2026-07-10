# Multi-Threading Data Contract

Read this before querying a CRM or accepting an export.

## Opportunity/deal

- opportunity/deal ID, account/company ID, owner ID;
- pipeline ID, stage ID and label;
- amount/currency and close date when prioritization uses them;
- current status and extraction timestamp.

## Contact relationship

- contact ID and account association source;
- opportunity contact-role record or HubSpot Buying role when present;
- role value, source, author, verification timestamp, and primary flag;
- original title, department, seniority, and reports-to evidence;
- privacy, opt-out, and contact restrictions.

## Engagement

- activity ID, type, direction, participants, timestamp, and opportunity/account link;
- meaningful two-way email, call, or meeting evidence;
- coverage window and last successful sync.

Do not use contact or opportunity `Last Modified` as stakeholder activity. Keep account association, opportunity linkage, role evidence, and engagement as separate facts.

## Platform evidence

- Salesforce documents Opportunity Contact Roles as the role each contact plays in a deal: https://help.salesforce.com/s/articleView?id=sf.sales_core_opp_contact_roles.htm&language=en_us&type=5
- HubSpot documents its multi-select Buying role contact property and customizable role options: https://knowledge.hubspot.com/properties/hubspots-default-contact-properties

These fields can still be stale or user-entered. Preserve source and verification dates.
