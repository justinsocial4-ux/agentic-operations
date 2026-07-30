# LM-03 Evidence And Limits

Read this file before citing market evidence, promising improvements, or choosing KPI targets.

## What Current Sources Support

- Salesforce documents that lead assignment rules can route leads to users or queues using criteria such as geography or specialization.
- Salesforce documents queues as a workload-sharing mechanism and warns that ownership changes can affect access.
- HubSpot documents retrieving owner IDs and assigning an owner through CRM property updates.
- LeanData's current vendor guide supports the qualitative link among routing delay, ownership gaps, fallback rules, and response-time measurement.

## What The Skill Does Not Treat As Established

The legacy research asserts exact figures for time savings, conversion lift, first-responder win rate, replacement cost, routing-tool pricing, quota attainment, specialist lift, misroute rate, and revenue loss. Do not repeat those as facts unless a current source directly supports the same figure and population.

The following are internal defaults requiring customer validation:

- territory confidence labels;
- 60% territory-warning threshold;
- seven-day capacity freshness;
- 50/85/100 capacity boundaries;
- 50/30/20 capacity weights;
- Jaro-Winkler 0.85 plus city fallback;
- vertical-specialist preference;
- SLA target.

## Measurement Plan

Establish a customer baseline before promising improvement:

- median and percentile route time;
- unowned-lead rate;
- manual-review and fallback rate;
- reassignment and dispute rate;
- eligible-owner failures;
- first-contact time measured separately from assignment;
- conversion by route type only with adequate volume and controls.

## Current Sources

- Salesforce assignment-rule guidance: https://help.salesforce.com/s/articleView?id=sf.customize_leadrules.htm&type=5
- Salesforce lead distribution example: https://help.salesforce.com/s/articleView?id=sf.networks_lead_assignment_rules_partners.htm&type=5
- HubSpot Owners API: https://developers.hubspot.com/docs/api-reference/latest/crm/owners/guide
- HubSpot Properties API: https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide
- LeanData lead-response guide: https://www.leandata.com/blog/lead-response-time/
