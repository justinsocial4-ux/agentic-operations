# Output Template

Use six tables:

1. **Preflight/source receipt:** policy versions, event/cutoff/timezone, sources, population, allowed fields, counts, freshness, coverage.
2. **Evidence ledger:** pseudonymous participant, exact source states/signals, timestamps, evidence labels, identity result, unknowns.
3. **Review lanes:** participant, rule/lane, priority, matched signals, anchor, response hours, due time, status.
4. **Downstream gates:** contactability, suppression, channel, enrollment, owner, approval, result.
5. **Risks/gaps:** conflict or missing evidence, effect, prohibited conclusion, resolution owner.
6. **Handoff preview:** exact proposed review, validation owner, approver, recheck time, and `NO CRM WRITE / NO TASK / NO MESSAGE / NO ENROLLMENT`.

Use descriptive evidence labels and failure-state tokens. Do not add confidence, intent, fit, likelihood, conversion, ROI, or revenue-impact columns.
