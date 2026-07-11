# Current Platform Limits

HubSpot line items distinguish unit price, quantity, net amount, currency, recurring frequency, and billing begin/end dates. Salesforce price and line-item semantics distinguish catalog item, quantity, unit price, currency, base/net/gross price, tax, and adjustments. Bind the customer's exact platform schema; do not substitute a deal amount.

Public pages, supplied quotes, transcripts, and reviews have different authority and semantics. Keep them separate and accept only pre-structured, authorized evidence.

Sources checked 2026-07-11:
- https://developers.hubspot.com/docs/api-reference/legacy/crm/objects/line-items/guide
- https://developer.salesforce.com/docs/commerce/b2c-commerce/references/b2c-script-api/dw.order.LineItem.html
- https://developer.salesforce.com/docs/data/salesforce-interactions-sdk/guide/c360a-api-line-item-data.html
- https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
- https://airc.nist.gov/airmf-resources/playbook/measure/
- https://docs.python.org/3/library/decimal.html
