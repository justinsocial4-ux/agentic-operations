# Platform, Privacy, And Action Boundaries

HubSpot documents that target-account membership can be changed manually, by bulk edit/import, or by workflow. Treat that property mutation as a separate action requiring explicit approval: https://knowledge.hubspot.com/prospecting/use-the-target-accounts-index-page

HubSpot company scores are customer-configured; fit, engagement, combined criteria, populations, limits, decay, associated-contact filters, and aggregation rules can differ: https://knowledge.hubspot.com/scoring/build-lead-scores and https://knowledge.hubspot.com/scoring/understand-the-lead-scoring-tool

Salesforce account-score weights are configurable, and predictive behavior scoring learns from organization-specific prospect/outcome data rather than universal activity weights: https://help.salesforce.com/s/articleView?id=sales.pc_define_account_rules.htm&type=5 and https://help.salesforce.com/s/articleView?id=sf.pardot_einstein_behavior_score_how_it_works.htm&type=5

Require least-privilege read scope for analysis. Account activity may derive from associated people; require approved association, purpose, access, retention, deletion, and downstream-use rules. A platform subscription or CRM policy does not by itself approve this new use.

This skill never mutates a target property, writes CRM fields, creates lists, launches campaigns, enrolls contacts, changes budgets, assigns routes, schedules refreshes, or sends messages. Preview the proposed action, affected records/system, approver, and reversal path for a separate execution workflow.
