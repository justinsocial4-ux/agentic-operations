# Research and Claim Status

Read this before repeating market benchmarks or outcome claims.

## Current evidence used

- HubSpot documents current and historical deal properties and internal pipeline/stage IDs: https://developers.hubspot.com/docs/api-reference/legacy/crm/objects/deals/guide
- HubSpot documents property types and UTC date/datetime formats: https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide
- Salesforce documents REST/SOQL object access, pagination beyond 2,000 query records, and API-call accounting: https://developer.salesforce.com/blogs/2024/04/accessing-object-data-with-salesforce-platform-apis
- Salesforce documents org-specific API entitlements, usage headers, and the Limits resource: https://developer.salesforce.com/blogs/2024/11/api-limits-and-monitoring-your-api-usage
- Digital Bloom's current vendor article supports general funnel, win-rate, sales-cycle, and pipeline-velocity benchmarking, but not the old skill's “27% lost forecasted revenue” or deal-slip claims: https://thedigitalbloom.com/learn/pipeline-performance-benchmarks-2025/
- Pavilion's current landing page says its benchmark analyzed 4.2 million opportunities and $54B in revenue, but the page alone does not support the old skill's exact manual-reporting claims: https://www.joinpavilion.com/resource/2024-b2b-sales-benchmarks
- Everstage repeats Salesforce's broad finding that salespeople spend substantial time on nonselling work; that does not establish how many hours a RevOps manager spends on Monday reporting: https://www.everstage.com/sales-productivity/sales-productivity-statistics/

## Removed from customer-facing instructions

Do not repeat these old figures as verified facts without a source that directly supports the exact claim and population:

- 27% lost forecasted revenue and $1.08M annual impact;
- forecast accuracy falling from 70% to below 45% after four weeks;
- four to eight weekly RevOps reporting hours and exact labor savings;
- 60% of forecasted deals slipping and 15–25% recovery from early detection;
- exact improvement claims for optional engagement, conversation, or enrichment tools;
- 5–10% as a “typical” high-risk-deal rate;
- guaranteed forecast, engagement, recovery, or time-saving targets.

Measure customer baselines and outcomes instead. Keep the risk thresholds in `metric_rules.md` labeled as tuneable heuristics until backtesting proves otherwise.
