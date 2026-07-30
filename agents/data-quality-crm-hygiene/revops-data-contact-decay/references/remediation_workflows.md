# Remediation Workflows

Use this reference before preparing live actions. It expands the frozen tier routes without changing them.

## ACTIVE — MONITOR

- Take no remediation action.
- Retain the current record and continue scheduled monitoring.
- Log the score, evidence timestamps, and data limitations.

## DECAYING — RE_ENGAGE

- Prepare an SDR task explaining the inactivity evidence.
- Suggest an email and call sequence.
- Track response for 30 days.
- If there is no reply, reassess; do not force a tier change without a new score.

## STALE — ENRICH_AND_DECIDE

- Prepare the contact for phone and company re-verification.
- Create a RevOps review task.
- After enrichment, recompute all five signals.
- Use the new score to choose re-engagement versus archival review.

## ARCHIVED_CANDIDATE — ARCHIVE_RECOMMEND

- Mark the record as recommended for review only.
- Show the score, evidence, missing-data caveats, and proposed disposition.
- Create an approval task or review queue only when the user authorizes that write.
- Never archive automatically. Explicit user approval is mandatory.

## Execution controls

Before any live write, show:

1. scope and exclusions;
2. counts by tier and proposed action;
3. source timestamps and data gaps;
4. rollback or recovery approach;
5. exact actions awaiting approval.

Analysis-only means no task creation, campaign enrollment, enrichment call, field write, Slack alert, or archival. After approval, execute only the approved tier and scope, then record IDs and outcomes in the transaction log.

The skill mentions expected reactivation and turnaround ranges. Treat those as frozen pilot assumptions, not guarantees; measure actual customer outcomes and replace the defaults with observed results.
