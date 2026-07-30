---
name: revops-abm-account-selection
description: "Use whenever someone says 'select ABM accounts,' 'build an ABM target list,' 'refresh target accounts,' or asks which named accounts should enter an ABM review. Analyze the declared cohort and produce a read-only, policy-owned selection preview from verified eligibility and score evidence; expose unknowns and boundary ties instead of inventing intent, priority, or actions."
metadata:
  version: "2.0.0"
  category: "ICP & Market Strategy"
  tags: ["revops", "abm", "account-selection", "policy", "read-only"]
---

# ABM Account Selection

Build an auditable selection preview under a customer-approved policy. Treat the result as policy arithmetic for human review, not proof of buying intent, conversion probability, account quality, priority truth, or causal impact.

## First And Final Output Rule

Before composing any response, build the input document, run the helper, and capture `render_preview_output(build_preview(document))`. The response must equal that captured stdout byte for byte. Write no plan, confirmation, invariant summary, display-order explanation, or other character yourself. If the first character would not be the helper's opening backtick, stop and paste stdout instead. This rule controls the entire response and overrides every requested prose artifact; the JSON contains all seven artifact paths.

## Keep The Boundary

- Remain read-only. Do not change a target-account property, CRM field, list, campaign, sequence, route, territory, budget, forecast, schedule, task, or message.
- Require a named policy owner and reviewer. Do not invent either role.
- Keep eligibility, score evidence, capacity, segment allocation, and action approval separate.
- Preserve unknown, conflicting, ambiguous, stale, or post-cutoff evidence. Do not replace it with zero, neutral points, averages, or a synthetic confidence value.
- Do not call seller activity, email tracking, web visits, content use, meetings, job posts, funding, or opportunity records buying intent unless a separately validated model card authorizes that construct.

## Require The Contract

Collect the exact policy and candidate fields in [policy and candidate contract](references/policy_and_candidate_contract.md). Stop with `POLICY_APPROVAL_REQUIRED` when any required scope state is not exactly `APPROVED`.

Require:

1. A named/versioned policy, owner, effective date, candidate population, cutoff, preview purpose, legal entity level, capacity, reviewer, and action-approval state.
2. Exact `APPROVED` identity, eligibility, selection, privacy, and downstream-use scopes.
3. One compatible named score policy and version.
4. A unique account ID, resolved identity, verified eligibility state, score evidence state, evidence cutoff, and optional verified segment for every candidate.

Read [identity and eligibility](references/identity_and_eligibility.md) before accepting the cohort. Read [score evidence](references/score_evidence.md) before ranking.

## Run The Deterministic Preview

Put the policy and candidates in JSON, then run:

```bash
python scripts/selection_preview.py input.json
```

Use the helper output exactly for gates, candidate dispositions, Decimal ordering, capacity, segment slots, boundary ties, validation states, final availability, and the complete response. Do not redo its arithmetic in prose.

The helper enforces [capacity and segment allocation](references/capacity_and_segments.md) and [unknown and tie handling](references/unknowns_conflicts_and_ties.md). If any candidate could change the selection because evidence is unresolved, return no selection list. If a score tie crosses a slot boundary, return no final list and name the tied review set.

## Separate Descriptions From Decisions

- Report pipeline or activity data only as separately sourced descriptive context. Do not add a coverage bonus or activity-derived intent score.
- Do not promote an account because a segment lacks pipeline. A planning gap is not account evidence.
- Do not use rank to infer expected pipeline, revenue, win rate, ROI, or forecast.
- Treat a supplied score as a policy score unless [validation and outcomes](references/validation_and_outcomes.md) proves a declared predictive construct for the same population, cutoff, and decision.

## Return Seven Artifacts

Follow [the output template](references/output_template.md). The helper's `artifact_paths` maps the seven requested artifacts to their single canonical locations; do not duplicate fields into separate prose or tables.

For every segmented candidate, preserve the exact segment status, segment value, and segment receipt ID in `candidate_receipts`. A segment bucket summary does not replace per-candidate provenance.

R1: never characterize evidence adequacy with `small`, `large`, `enough`, `limited`, or `insufficient` unless an approved numerical policy defines that label. Report helper states and counts.

R2: paste `render_preview_output(build_preview(document))` verbatim as the complete response. The first response character must be the helper's opening backtick and the final response characters must be its boundary. Do not introduce the output, summarize invariants, explain display ordering, or add any text before or after helper stdout; those facts already exist inside the JSON. Every numeric value comes from that helper output and appears only there. Do not add a draft value, approximation, prose summary, table, strikethrough, ellipsis correction, or self-correction. Fix and rerun instead.

## Platform And Privacy Rules

Use [platform, privacy, and action boundaries](references/platform_privacy_and_actions.md). Platform scoring and target-account tools are configurable mechanisms, not evidence that this policy is valid. Require the customer's approved association, access, purpose, retention, and downstream-use rules; never claim compliance is inherited from a CRM.

## Worked Boundary Example

Input: a policy-owned bucket where equal scores cross the slot boundary.

Output: the helper returns accounts above the boundary as provisional, the tied accounts as `BOUNDARY_TIE_REVIEW`, and the final selection as unavailable. Render its complete output once; do not break the tie by account name, ID, input order, or model preference.

## Explain Why

Account selection allocates scarce attention and can trigger consequential downstream treatment. A reproducible formula is still unsafe when its population, evidence, capacity, or tie rule is missing. Fail-closed receipts let a human correct the policy or evidence without laundering assumptions into a target list.
