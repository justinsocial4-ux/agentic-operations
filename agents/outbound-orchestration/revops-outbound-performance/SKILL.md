---
name: revops-outbound-performance
description: "Analyzes outbound email delivery, reply, positive-reply, meeting-association, subject, send-window, sequence-step, and rep-level performance with explicit denominators and uncertainty. Make sure to use this skill whenever the user asks what outbound is working, which subject line performs better, why reply rates changed, which send windows or sequence steps deserve a test, how reps compare after controlling for mix, or how to design an outbound experiment—even if they do not name the agent."
metadata:
  category: "Outbound Orchestration"
  phase: "day_1"
  data_readiness: "30_days"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies: []
  mcps:
    - "Outreach or Salesloft MCP for sequence and touch reads"
    - "Salesforce or HubSpot MCP for explicit meeting/opportunity evidence"
  minimum_data:
    - "Touch ID, sequence/step, sender, recipient, send timestamp, delivery outcome"
    - "Reply outcome with reply class and timestamp"
    - "Experiment assignment or comparable segment fields for causal tests"
---

# Outbound Performance Analysis

Turn outreach logs into an auditable performance report. Keep raw counts beside every rate, expose missing evidence, and distinguish descriptive association from causal evidence.

## Bundled Resources

- Read `references/data_contract.md` before querying platforms or accepting an export.
- Read `references/metric_statistics.md` for denominators, intervals, comparisons, clustering, and multiple-testing rules.
- Read `references/meeting_attribution.md` before connecting touches or replies to meetings.
- Read `references/experiment_playbook.md` before recommending a rollout or claiming lift.
- Read `references/report_template.md` when drafting the final deliverable.
- Read `references/research_and_claims.md` before repeating external benchmarks or outcome claims.
- Use `scripts/outbound_performance.py` for exact calculations, subject similarity, group comparisons, and p-value adjustment.

## Safety and Interpretation Rules

1. Read source systems; do not edit sequences, schedules, rep assignments, or CRM records during analysis.
2. Treat opens as diagnostic only. Privacy controls and image loading make them unsuitable as the main success metric.
3. Keep replies, positive replies, meetings, and opportunities separate.
4. Prefer explicit platform/CRM links for meetings. Call time-window matches `associated`, never `caused`.
5. Do not call a p-value statistical confidence or the probability a recommendation is correct.
6. Report effect size, raw counts, uncertainty interval, test design, and adjusted p-value together.
7. Correct for multiple comparisons when ranking many subjects, windows, steps, or reps.
8. Treat observational differences as hypotheses. Recommend rollout only from a valid controlled test or explicit user policy.
9. Do not shame reps. Control for list, territory, persona, tenure, sequence, and volume before coaching conclusions.
10. Never sum or compare unlike timezones, currencies, reply taxonomies, or denominator definitions without normalization.

## Preflight

### 1. Confirm the decision

Ask what the user will decide:

- diagnose a recent change;
- rank subjects or sequence steps descriptively;
- compare a predeclared A/B test;
- inspect send windows in recipient-local time;
- review meeting association;
- identify coaching hypotheses.

Confirm date range, platforms, teams, campaigns, personas, regions, reply taxonomy, and exclusions. State whether the output is descriptive or experimental.

### 2. Verify evidence

- If platforms are connected, retrieve only approved fields from `references/data_contract.md` and paginate.
- If not connected, accept CSV/JSON exports.
- If no records are available, return the exact export contract and stop.

Audit:

- unique touch IDs and deduplication keys;
- sent, delivered, bounced, replied, positive-replied, and meeting-linked states;
- consistent reply taxonomy;
- sequence, step, variant, rep, recipient, and timestamp coverage;
- recipient timezone coverage for local-time analysis;
- explicit experiment assignment and exposure dates for causal comparisons;
- explicit meeting/opportunity links versus heuristic candidates.

Do not impose a fictional global minimum such as “20 sequences.” Report each cohort's sample and interval. Mark analyses unavailable when their required evidence is missing.

## Workflow

### Step 1: Normalize one touch ledger

Preserve source IDs and timestamps. Create one row per delivered attempt with:

- platform, workspace, touch, sequence, step, and variant IDs;
- rep and recipient IDs;
- normalized subject plus original subject;
- send timestamp in UTC and recipient-local time when known;
- delivery state and bounce type;
- reply state, reply class, and reply timestamp;
- explicit meeting/opportunity link or heuristic association status;
- experiment, segment, persona, territory, and account fields.

Deduplicate using source touch ID. If unavailable, use a documented composite key and report collision risk.

### Step 2: Calculate the funnel

Use `scripts/outbound_performance.py`.

- Delivery rate = delivered / sent.
- Reply rate = replies / delivered.
- Positive reply rate = positive replies / delivered.
- Explicit meeting rate = explicitly linked meetings / delivered.
- Heuristic meeting association rate = candidate associations / delivered, labeled separately.
- Bounce rate = bounces / sent.

Show numerator, denominator, rate, and Wilson interval. Return unknown for a missing denominator or taxonomy; do not convert it to zero.

### Step 3: Compare like with like

For subjects, steps, send windows, cadences, and reps:

- keep campaign, persona, territory, date range, list source, and sequence context visible;
- separate randomized experiment results from observational slices;
- use absolute percentage-point difference and relative lift;
- use a two-proportion test only for predeclared comparable cohorts;
- apply Benjamini-Hochberg adjustment when evaluating multiple variants;
- show small samples rather than hiding them, but do not promote a winner from an unstable estimate.

### Step 4: Cluster subjects carefully

Normalize case, whitespace, accents, and punctuation while preserving placeholder meaning. Use Jaro-Winkler only as candidate grouping with a tunable default threshold of 0.90. Review clusters before aggregation because similar wording can express different offers or calls to action.

### Step 5: Analyze send windows

Use recipient-local time only when timezone coverage is sufficient under the user's approved threshold. Otherwise show UTC/source-time distributions and mark local-time conclusions unavailable. Control for weekday, campaign, persona, and sequence step before proposing a test.

### Step 6: Analyze reps without confounding skill and mix

Start with volume and funnel coverage. Compare reps within matched campaign/persona/territory cohorts or a model approved by the user. Treat raw team-average variance as descriptive. Turn gaps into private coaching questions, such as subject selection or reply handling, not performance verdicts.

### Step 7: Convert observations into experiments

Use `references/experiment_playbook.md` to define:

- one changed variable;
- primary metric and denominator;
- assignment unit and randomization method;
- guardrails for bounce, unsubscribe, complaint, and negative replies;
- minimum detectable effect, power, and stopping rule;
- planned segments and number of comparisons;
- rollout rule and rollback condition.

Do not promise a lift. State the observed difference and what the experiment would test.

### Step 8: Validate and deliver

Reconcile every rate to source counts. Verify that subject clusters, reply classes, timezone conversion, and meeting links are traceable. Show a preview; do not alter live sequences unless the user separately approves an implementation action.

## Failure and Degradation Paths

| Condition | Response |
|---|---|
| Engagement platform unavailable | Offer export analysis or connection troubleshooting; do not use stale data silently. |
| Reply taxonomy incomplete | Report total reply rate only; positive-reply analysis is unknown. |
| Delivery state missing | Do not use sends as a reply-rate denominator; return unknown. |
| Recipient timezone missing | Disable recipient-local send-window claims. |
| Experiment assignment missing | Label comparisons observational; do not claim causality. |
| Explicit meeting link missing | Report heuristic candidates separately or omit meeting analysis. |
| Baseline rate is zero | Report absolute difference and `relative lift undefined`. |
| Many variants tested | Adjust p-values and disclose the comparison count. |
| Rep cohorts differ materially | Do not rank; show cohort mix and request a matched analysis. |

## Output Contract

Return:

1. `Preflight receipt` — scope, sources, taxonomy, coverage, enabled/disabled analyses.
2. `Metric table` — raw counts, denominators, rates, and intervals.
3. `Comparison table` — effect sizes, design type, adjusted p-values, and caveats.
4. `Hypotheses and experiment plan` — no guaranteed outcomes.
5. `Data quality and limitations` — missing evidence and confounders.
6. `Validation receipt` — reconciliation, traceability, and action status.

## Worked Example

**Input:** In a predeclared randomized subject test, variant A receives 20 replies from 200 delivered emails. Variant B receives 8 replies from 200 delivered emails. Reply taxonomy and delivery states are complete; no meeting evidence is supplied.

**Result:**

- A reply rate: `20 / 200 = 10.0%`.
- B reply rate: `8 / 200 = 4.0%`.
- Absolute difference: `+6.0 percentage points`.
- Relative lift versus B: `150%`.
- Two-sided pooled two-proportion p-value: approximately `0.018` before any multi-test adjustment.
- Meeting result: unknown.
- Recommendation: treat A as the current test winner only if assignment, stopping, and comparison plan were valid; otherwise rerun a controlled test. Do not promise the observed lift will persist.

## Verification Checklist

- [ ] Every rate shows numerator and denominator.
- [ ] Delivered, reply, positive reply, and meeting definitions are explicit.
- [ ] Explicit meeting links are separate from heuristic associations.
- [ ] Recipient-local time is used only with adequate timezone evidence.
- [ ] Observational and randomized comparisons are labeled.
- [ ] Multiple comparisons are adjusted.
- [ ] Rep mix and sample size are visible.
- [ ] Recommendations are framed as tests unless causal evidence exists.
- [ ] No sequence or CRM change occurred during analysis.
