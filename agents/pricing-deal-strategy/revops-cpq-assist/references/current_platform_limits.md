# Current Platform Limits

Current official documentation shows why platform behavior cannot be generalized:

- HubSpot quotes vary by Revenue Hub edition/seat, line-item pricing model, quantity, currency, billing timing, tax, payment, contract automation, and quote state. Publishing or acceptance can affect deal amounts/lines and create contracts, subscriptions, or invoices: https://knowledge.hubspot.com/quotes/create-and-send-quotes
- HubSpot approvals are customer-admin configured by pipeline, conditions, permissions, approvers, and `All` versus `Any` semantics; requests and status changes trigger platform actions: https://knowledge.hubspot.com/object-settings/pipeline-approvals
- Salesforce Revenue Management pricing and approval behavior depends on configured pricing procedures, product constraints, transaction types, editions, licences, permissions, sequential/parallel chains, notifications, and audit state: https://help.salesforce.com/s/articleView?id=release-notes.rn_salesforce_pricing.htm and https://help.salesforce.com/s/articleView?id=ind.qocal_advanced_approvals.htm

Accept normalized evidence only. Do not claim an object, field, quota, permission, side effect, or platform capability without an exact customer binding.
