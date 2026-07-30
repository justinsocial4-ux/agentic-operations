# Funnel Policy

Read this file before stage mapping or cohort construction.

## Required policy fields

- policy ID, version, owner, and approval date
- pipeline/process ID
- anchored population and first-stage cohort rule
- ordered stage IDs and display labels
- terminal won, lost, recycled, disqualified, and other outcomes
- observation window for each transition
- skipped-stage treatment
- regression and re-entry treatment
- duplicate, merge, and split handling
- first/latest/accumulated repeated-stage visit rule
- dimension-freeze point
- optional targets/baselines and decision rules

Use internal stage IDs where available. Labels can change; IDs are safer.

## Path exceptions

Report these separately unless the approved policy says otherwise:

- skipped stage
- backward move/regression
- re-entry after exit
- recycle to an earlier lifecycle
- parallel opportunity created from one person/account
- merged or split identity
- terminal outcome followed by reopening

Do not force exceptions into the happy path merely to make counts reconcile.

## Approval rule

Stage similarity, common industry language, and a model's intuition are not approval. If a mapping is ambiguous, return `POLICY_REQUIRED` with the raw stages and candidate mappings for a human decision.
