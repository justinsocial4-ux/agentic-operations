# Current platform limits

Salesforce approvals depend on org-defined processes, entry criteria, allowed submitters, permissions, configured steps, and actions. Salesforce Files uses ContentDocument, ContentVersion, and ContentDocumentLink; a generic QuoteDocument field does not establish the governing file version.

HubSpot quote approvals depend on the customer's product edition and configured workflow approval steps. Custom objects, properties, associations, and approval behavior are not portable defaults.

Treat every platform mapping as customer-supplied evidence with source, schema, version, access, and side-effect receipts. The helper accepts normalized JSON and makes no API call.

Current sources checked 2026-07-10:

- https://help.salesforce.com/s/articleView?id=sf.process_action_submit.htm&language=en_US&type=5
- https://trailhead.salesforce.com/en/business_process_automation/approvals
- https://developer.salesforce.com/docs/platform/data-models/guide/salesforce-files.html
- https://knowledge.hubspot.com/quotes/set-up-quote-approvals
- https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
- https://www.americanbar.org/content/dam/aba/administrative/professional_responsibility/ethics-opinions/aba-formal-opinion-512.pdf
