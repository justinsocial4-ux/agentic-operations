# Current Platform Limits

Current official documentation supports these limits:

- HubSpot customer-health scoring is customer-configured: segments, criteria, aggregations, time periods, decay, caps, thresholds, and labels are setup choices, not universal churn truth: https://knowledge.hubspot.com/help-desk/customize-a-health-score-in-the-customer-success-workspace
- Amplitude states that group analytics must be deliberately instrumented; event-level and user-level group properties differ; property updates are not retroactive; official-event designation requires tracking-plan-owner review; and metric definitions have change history: https://amplitude.com/docs/analytics/plan-your-accounts-instrumentation, https://amplitude.com/docs/data/official-events-and-properties, and https://amplitude.com/docs/analytics/metrics
- Salesforce models Tasks and Events as activity records with separate `What` and `Who` relationships. Their presence or association is not generic proof of customer engagement: https://developer.salesforce.com/docs/platform/data-models/guide/tasks-events.html
- NIST AI RMF calls for documented limits, intended use, human oversight, construct validity, context-relevant testing, privacy consideration, and safe failure: https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
- NIST Privacy Framework makes privacy requirements and lifecycle controls organization-specific: https://www.nist.gov/privacy-framework

Platform objects, fields, definitions, editions, permissions, histories, and associations vary. Accept normalized customer-approved evidence; do not invent or call an API.
