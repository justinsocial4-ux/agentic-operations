---
name: revops-stage-progression
description: "Audits dated opportunity stage history for policy-defined regressions, skips, re-entry, and extended or rapid dwell without inventing motive or forecast impact. Make sure to use this skill whenever the user asks to check stage progression, find stalled deals, review stage skips or regressions, inspect pipeline movement, detect unusual stage timing, investigate sandbagging, or prepare a stage-progression report—even if they do not name the agent."
metadata:
  category: "Pipeline Management"
  phase: "1"
  data_readiness: "stage_history_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved pipeline and stage-transition policy"
  mcps:
    - "Salesforce or HubSpot read-only stage-history evidence"
  minimum_data:
    - "Stable opportunity/deal ID, stable stage ID, entered-at timestamp, and cutoff"
---

# Stage Progression Audit

Describe what the CRM history proves about stage movement. Do not convert unusual timing into rep motive, buyer behavior, deal risk, forecast impact, or coaching guilt.

## Bundled Resources

- Read `references/data_contract.md` before accepting stage history or snapshots.
- Read `references/stage_policy.md` before classifying transitions or timing.
- Read `references/episode_metrics.md` before calculating dwell or benchmarks.
- Read `references/evidence_and_language.md` before naming anomalies, causes, risk, or sandbagging.
- Read `references/output_template.md` before producing the audit.
- Read `references/research_and_claims.md` before repeating platform, benchmark, accuracy, labor, or outcome claims.
- Use `scripts/stage_progression.py` for exact episode, transition, dwell, and coverage calculations.

## Operating Rules

1. Analyze read-only evidence. Do not change stages, dates, probabilities, close dates, amounts, owners, tasks, or CRM records.
2. Require a versioned customer-approved pipeline policy with stable stage IDs, order, allowed transitions/skips, terminal/reopen rules, clock, benchmark cohort, and thresholds.
3. Use dated stage-entry history available by the cutoff. Never reconstruct prior stages from current stage, LastModifiedDate, or current field values.
4. Preserve repeated visits as separate episodes. Do not collapse re-entry into one accumulated duration unless the approved metric explicitly requires it.
5. Classify a regression or skip only against the approved policy. A non-adjacent forward move is not an error when that exact transition is allowed.
6. Call a long episode `EXTENDED_DWELL`, not zombie/stalled/at-risk, unless an approved operational definition supplies that label.
7. Call a short episode `RAPID_TRANSITION`, not sandbagging, acceleration risk, buyer readiness, or suspicious behavior.
8. Treat CRM stage changes as seller-entered system evidence. They do not prove buyer activity, intent, qualification, deal health, or cause.
9. Keep observed fact, policy exception, hypothesis, and unknown separate. Never infer why a transition occurred without cited event evidence.
10. Do not invent 2x/0.5x dwell rules, 30-record minimums, 80% coverage, 0–100 confidence, anomaly scores, severity weights, or accuracy claims.
11. Benchmarks and thresholds must be approved before results are inspected and must match pipeline, stage definition, segment, outcome cohort, time period, and clock.
12. Show counts and coverage beside rates. Missing history disables path analysis; a known current-stage entry may still enable current-episode age.
13. Report deal amount only under the named CRM amount basis and currency. Do not call it revenue, forecast impact, loss, risk, or recoverable value.
14. Keep transition evidence separate from forecast category, probability, seller submission, and finance outcomes.
15. Frame follow-up as neutral review questions. Do not accuse, score, rank, or coach a rep from stage history alone.
16. Apply any rule created after viewing results only to a future independent review.
17. Preview human-owned actions. Execute nothing without separate approval.

## Preflight

Record the decision, cutoff, pipeline, account/deal population, reporting currency, amount basis, and requested outputs.

Lock the policy:

- policy ID/version, owner, and approval date
- stable stage IDs, labels, order, terminal states, reopen rules
- allowed adjacent, skip, regression, and administrative transitions
- event time, timezone, business/calendar clock, and same-time handling
- benchmark source, comparable cohort, statistic, window, and minimum evidence rule
- preapproved extended/rapid thresholds and missing-data treatment
- action approver and no-write boundary

Verify source, extraction time, row counts, opportunity coverage, stage-ID coverage, history horizon, duplicates, timestamps, and exclusions. If no approved policy exists, return a descriptive event ledger and `POLICY_REQUIRED` instead of classifying exceptions.

## Workflow

### 1. Build stage episodes

Sort each deal's stage-entry events chronologically. Reject duplicate timestamps or events after cutoff. Close each episode at the next stage entry; close the current episode at cutoff. Preserve re-entry as a new episode.

### 2. Classify recorded transitions

Compare each from/to stage pair to the approved stage IDs and allowed-transition set. Report `ADJACENT_FORWARD`, `ALLOWED_SKIP`, `POLICY_SKIP`, `REGRESSION`, `REENTRY`, `TERMINAL_EXIT`, or `UNKNOWN_STAGE` as defined by policy.

### 3. Evaluate dwell

Compare an episode only to its approved stage/cohort benchmark and preapproved multiplier or absolute rule. Show episode days, benchmark, ratio, threshold, clock, and result. Without a comparable benchmark or threshold, return `DWELL_RULE_REQUIRED`.

### 4. Summarize without false impact

Report deal counts, episode counts, transition counts, evidence coverage, and amounts under the named CRM basis/currency. Do not sum mixed currencies or label amounts at risk.

### 5. Prepare a review preview

For each policy exception, propose neutral questions: Was the CRM entry administrative? Is the approved stage definition met? Is history missing? Is the benchmark comparable? What dated buyer or seller evidence explains the movement? Keep owner and approver explicit.

## Worked Example

Policy `SP-2` orders Discovery → Qualification → Proposal → Negotiation, allows no skips, and flags Proposal dwell at or above 1.5 times an approved 10-day comparable median.

A deal records Discovery for 5 days, Qualification for 10, Proposal for 4, a regression to Qualification for 5, and re-entry to Proposal for 20 days at cutoff. The current Proposal episode is exactly 2.0 times the benchmark and is `EXTENDED_DWELL`; Proposal → Qualification is a recorded `REGRESSION`. Neither fact proves sandbagging, buyer concern, deal risk, or forecast impact.

## Output Contract

Return six artifacts:

1. **Preflight receipt** — policy, cutoff, pipeline, stage IDs, clock, benchmark, amount basis, source, and enabled analyses.
2. **Evidence coverage** — deals/events covered, missing history, unknown stages, duplicates, and exclusions.
3. **Episode ledger** — deal, stage ID/label, entry/exit, days, benchmark, ratio, and dwell result.
4. **Transition ledger** — from/to IDs, timestamp, classification, policy rule, and evidence label.
5. **Scope and limitations** — CRM amounts under named basis, unknown causes, unavailable risk/forecast/motive conclusions.
6. **Action preview and receipt** — neutral review questions, owner, approver, and explicit no-write confirmation.

## Failure States

- `POLICY_REQUIRED` — stage order, allowed transition, clock, or threshold is absent.
- `HISTORY_REQUIRED` — path analysis lacks dated stage-entry events.
- `CURRENT_ENTRY_UNKNOWN` — current-stage age cannot be calculated.
- `UNKNOWN_STAGE` — a stage ID is absent from the approved policy.
- `TIMESTAMP_CONFLICT` — events are duplicated, out of order, or after cutoff.
- `DWELL_RULE_REQUIRED` — benchmark, cohort, statistic, or threshold is absent.
- `MIXED_CURRENCY` — CRM amounts cannot be aggregated safely.
- `APPROVAL_REQUIRED` — a proposed CRM or rep action lacks human approval.

Never replace an unavailable conclusion with a confidence score or accusation.
