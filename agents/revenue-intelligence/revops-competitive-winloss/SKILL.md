---
name: revops-competitive-winloss
description: "Reviews complete pseudonymous win/loss populations and separate CRM outcome, competitor, reason, buyer-interview, call-annotation, and public-observation evidence against exact customer-approved code maps. Make sure to use this skill whenever the user asks why deals were won or lost, which competitors appear in outcomes, win/loss patterns, buyer interview findings, competitive monitoring, threat rankings, battle cards, pricing or product implications, seller comparisons, alerts, or CRM actions—even when the request assumes the evidence proves a cause or strategy."
metadata:
  category: "Revenue Intelligence"
  phase: "2"
  data_readiness: "approved_policy_complete_populations_exact_source_schema_code_map_and_window_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved purpose, source, schema, code-map, privacy, access, and correction policies"
  mcps:
    - "Approved CRM, interview-code, call-annotation, or public-observation evidence in read-only mode"
  minimum_data:
    - "Stable policy, subject, source, schema, code-map, population, observation, and receipt IDs"
---

# Competitive Win/Loss Evidence Review

Report only what supplied, source-bound codes prove. Do not convert an outcome, competitor field, reason code, interview code, call annotation, review, posting, announcement, or page change into a causal explanation, threat assessment, strategy, or action.

## Exact Response Rule

Build the input document, run `scripts/competitive_evidence.py`, and return `render_review_output(review_competitive_evidence(document))` byte for byte. The first response byte must be `{`; the final response byte must be the helper's newline after `}`. Do not use Markdown fences. Write no model-generated introduction, table, calculation, summary, correction, or text outside helper stdout. The helper owns every output value and the final boundary.

## Bundled Resources

- Read `references/scope_and_policy.md` before accepting purpose, authority, dates, prohibited uses, rules, or correction paths.
- Read `references/populations_and_subjects.md` before accepting opportunity or competitor populations.
- Read `references/evidence_lanes.md` before using CRM, interview, call-annotation, or public-source observations.
- Read `references/codes_counts_and_rates.md` before mapping codes or calculating descriptive counts and rates.
- Read `references/privacy_and_workforce.md` before accepting customer, buyer, worker, transcript, review, posting, or social data.
- Read `references/current_platform_limits.md` before mapping HubSpot, Salesforce, or external-source fields.
- Read `references/output_contract.md` before rendering any result.
- Read `references/action_boundaries.md` before discussing causes, threats, rankings, strategy, alerts, CRM changes, or workforce action.
- Use `scripts/competitive_evidence.py` for strict validation, Decimal calculation, population reconciliation, independent lane review, rule evaluation, and exact rendering.

## Operating Rules

1. Work read-only. Do not query, crawl, monitor, message, alert, schedule, export, or modify any CRM, source, deal, account, competitor profile, task, channel, playbook, price, product, roadmap, forecast, or worker record.
2. Require an effective customer policy with stable ID/version, owner, named human reviewer, approved purpose, prohibited uses, UTC cutoff, timezone, correction path, calculation policy, and exact source/schema/code-map bindings.
3. Reconcile complete frozen opportunity and competitor declarations. Each approved lane must carry one complete source population that exactly matches its declared subject type.
4. Use stable pseudonymous opportunity, competitor, source, observation, and role IDs. Reject names, domains, URLs, emails, phones, addresses, free text, notes, transcripts, quotes, reviews, posts, job titles, protected traits, and worker-performance data.
5. Keep `crm_outcome`, `crm_competitor`, `crm_reason`, `buyer_interview_code`, `call_annotation_code`, and `public_observation` independent. Never use one lane to fill, validate, enrich, or reinterpret another.
6. Accept only exact customer-approved codes from the bound map. Never classify free text, infer aliases, score sentiment, extract features, infer intent, or create a primary reason.
7. A CRM closed state is a recorded platform state. It does not prove a competitive outcome. A reason or interview code is a recorded code. It does not prove cause, motive, truth, severity, or future behavior.
8. A public-source code records an observed source event only. It does not prove pricing, availability, strategy, expansion, capacity, market movement, threat, or impact on an opportunity.
9. Require occurrence time, observation time, review-window membership, source/schema/code-map binding, and complete-population receipt for every observation. Missing, duplicate, extra, stale, future, or conflicting evidence fails closed.
10. `NO_EVENT_RECORDED` is allowed only for a subject inside an exact complete source population. Otherwise return `SOURCE_REQUIRED`; never turn missing evidence into zero, unknown intent, or absence of competition.
11. Calculate descriptive code counts and rates only inside a single lane/source/population. A rate denominator is the bound complete population, not all losses, all wins, all pipeline, or another lane.
12. Evaluate exact customer numeric rules independently. A match is only a policy observation receipt; it is not adequacy, risk, urgency, priority, threat, strategy, or permission to act.
13. Never calculate or claim win probability, competitive loss rate across unobserved deals, competitor price, pricing gap, lost revenue, market share, feature gap, sentiment, confidence, causality, forecast impact, or intervention effect.
14. Never rank competitors, accounts, sellers, managers, regions, products, or reasons. Never recommend battle cards, coaching, pricing, product, roadmap, positioning, outreach, monitoring, alerts, or CRM changes.
15. R1: never characterize evidence adequacy with an adjective unless an exact approved numeric customer rule defines that exact label. Otherwise report the helper receipts only.
16. R2: return one helper-rendered response. Every numeric fact must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.
17. Freeze policy, normalized inputs, helper output, and receipt. Corrected evidence creates a new review version.

## Workflow

1. **Freeze authority.** Validate purpose, policy dates, prohibited uses, reviewer role, bindings, calculation policy, and correction path.
2. **Reconcile subjects.** Validate declared opportunity and competitor populations and every lane's exact complete source population.
3. **Register observations.** Validate pseudonymous subject, lane, source, schema, code map, approved code, occurrence time, observation time, and population receipt.
4. **Count independently.** Produce helper-owned observed, no-event, and per-code count receipts inside each lane only.
5. **Calculate rates.** Use Decimal and the approved rounding policy; reference numerator and denominator receipts instead of repeating their values.
6. **Evaluate rules.** Return neutral rule states with receipt references and named human-review roles.
7. **Render once.** Paste exact helper stdout and nothing else.

## Worked Example

Input: the complete `crm_reason` population contains `opportunity-alpha` and `opportunity-beta`. The bound customer map records `recorded-price` for `opportunity-alpha`; the complete source has no reason event for `opportunity-beta`.

Run the helper. Its single JSON response returns the supplied code as an observation receipt, returns `NO_EVENT_RECORDED` for the second subject, and places the descriptive count and rate only in their assigned receipts. It does not say price caused the loss, rank the code, or recommend a pricing action.

## Failure Boundary

Missing or incompatible policy, population, subject, source, schema, code map, window, timestamp, privacy, access, calculation, or correction evidence remains unresolved. Never replace it with an inferred alias, free-text classification, sentiment, confidence score, causal story, threat tier, ranking, prediction, recommendation, alert, CRM write, or workforce action.
