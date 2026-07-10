# Platform Boundaries

HubSpot documents separate read/write scopes for marketing-event data and notes that attendance write endpoints can create a contact: [Marketing Events API](https://developers.hubspot.com/docs/api-reference/latest/marketing/marketing-events/guide). Treat creation as an explicit write, not a harmless sync.

HubSpot sequence enrollment requires product access and permissions, can reject contacts with missing/bounced email, limits concurrent enrollment, and observes send limits: [sequence enrollment](https://knowledge.hubspot.com/sequences/enroll-contacts-in-a-sequence). Verify the current tenant before any handoff.

Salesforce matching and duplicate behavior depends on active org rules, and duplicate rules can span leads/contacts: [standard duplicate rules](https://help.salesforce.com/s/articleView?id=sales.duplicate_rules_standard_rules.htm&language=en_US&type=5). Salesforce also documents cases where duplicate rules do not run or behave differently for APIs/import paths: [duplicate-rule considerations](https://help.salesforce.com/s/articleView?id=sf.duplicate_rules_overview.htm&language=en_US&type=5).

These sources prove platform capabilities and constraints. They do not define event priority, contact permission, response SLA, conversion expectation, or safe automatic action.
