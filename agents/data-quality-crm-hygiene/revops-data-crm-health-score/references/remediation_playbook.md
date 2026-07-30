# Remediation Playbook

Use this file only after the six scores are complete. Rank the bottom three dimensions, then give one data action, one process action, and one tool/integration action for each. Include effort, expected score impact, owner, and timeline. Do not promise ROI that the available evidence cannot support.

## Completeness

- Data: enrich missing phone, title, company, or industry fields.
- Process: require the truly essential fields at record creation.
- Tool/integration: add an approved enrichment or form-validation path.

## Accuracy

- Data: validate formats and spot-check against an approved truth source.
- Process: define ownership for disputed values and a review queue.
- Tool/integration: connect a verification source only after budget and permissions are confirmed.

## Duplicates

- Data: run DQH-01 and review high-confidence duplicate groups.
- Process: add duplicate-prevention rules at intake.
- Tool/integration: fix sync behavior that repeatedly creates duplicates.

## Freshness

- Data: refresh stale Contacts and flag records untouched for more than 90 days.
- Process: make record review part of the owner workflow.
- Tool/integration: sync approved engagement or verification events back to the CRM.

## Consistency

- Data: normalize types, formats, and Contact-to-Account links through DQH-02 rules.
- Process: standardize picklists and naming conventions.
- Tool/integration: add safe account matching for orphaned Contacts.

## Connectivity

- Data: validate reachable email/phone values and Opportunity-to-Contact links.
- Process: require a Contact role where the sales process depends on one.
- Tool/integration: sync approved bounce, call, or engagement signals.

## Prioritization Rule

Choose the actions that move the weakest dimensions most for the least effort. Preserve the pilot effort labels: Low = 1-2 weeks, Medium = 2-4 weeks, High = more than 4 weeks. Call out one-day quick wins separately when supported by the customer's system.
