# Decision and implementation boundary

The review stops before selection or execution. A preferred scenario requires a preapproved decision rule, complete and comparable evidence, named reviewer and approver, affected-party review, correction/appeal path, implementation plan, rollback plan, and customer change-management approval.

Do not update `Account.OwnerId`, territory models, territory/object/user associations, teams, sharing, assignment rules, quotas, pay, staffing, hiring, account priority, schedules, alerts, or communications. Do not generate an import file that could execute those changes.

Salesforce territory management includes model, hierarchy, user-territory, object-territory, assignment, and sharing surfaces; it is not portable to a flat ownership rewrite: https://developer.salesforce.com/docs/platform/data-models/guide/territory-management.html . Platform-specific implementation must be separately designed and approved.

End with `NO TERRITORY OR OWNERSHIP CHANGE / NO QUOTA OR WORKFORCE ACTION`.
