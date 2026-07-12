---
name: revops-qbr-prep
description: "Assembles customer-approved pseudonymous metric, comparison, claim, and section receipts into a deterministic QBR or customer-review evidence packet without inventing health, churn, renewal, sentiment, root cause, expansion, recommendations, or publication authority. Make sure to use this skill whenever the user asks to prepare, build, generate, refresh, review, summarize, narrate, export, send, or present a QBR, business review, customer review, account review, renewal review, success review, or customer-facing KPI packet—even when the request assumes CRM fields are comparable, a health score is valid, missing renewal data can be estimated, or the packet is ready to share."
metadata:
  category: "Customer Success Operations"
  phase: "2"
  data_readiness: "complete_customer_supplied_policy_blueprint_metric_comparison_and_claim_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved purpose, privacy, source, metric, comparison, claim, section, recipient, retention, and publication-policy receipts"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable pseudonymous policy, source, schema, metric, record, comparison, claim, section, role, and receipt IDs"
---

# QBR Evidence Packet Assembly

Assemble only what complete customer-supplied receipts support. Produce a reviewable evidence packet, not a customer narrative, account diagnosis, renewal strategy, or finished QBR.

## Exact Response Rule

Build the input document, run `scripts/qbr_packet.py`, and return `render_qbr_output(assemble_qbr_packet(document))` byte for byte. The first response byte must be `{`; the helper supplies the final empty terminal line after `}`. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read `references/scope_and_authority.md` before accepting purpose, audience, recipients, retention, or publication-policy state.
- Read `references/metric_and_time_contracts.md` before accepting any account, adoption, support, sentiment, contract, renewal, usage, or commercial metric.
- Read `references/population_and_lineage.md` before accepting sources, schemas, queries, pages, records, freshness, or completeness.
- Read `references/comparisons.md` before calculating a delta or percent change.
- Read `references/claims_and_sections.md` before assembling claim bindings or QBR section blocks.
- Read `references/privacy_and_actions.md` before handling identities, quotes, customer decisions, worker decisions, or delivery requests.
- Read `references/output_contract.md` before rendering a result.
- Read `references/verification_sources.md` for current official sources supporting this boundary.
- Use `scripts/qbr_packet.py` for strict validation, Decimal arithmetic, evidence-state propagation, assembly, and exact rendering.

## Operating Rules

1. Work offline and read-only. Never query CRM, support, product, survey, billing, email, calendar, storage, presentation, identity, or messaging systems.
2. Require one effective policy with the exact purpose, audience class, confidentiality class, reporting cutoff, reviewer, allowed recipient roles, retention rule, privacy review, QBR blueprint, and separate approval receipts.
3. Accept only pseudonymous IDs. Reject organization, account, customer, contact, worker, owner, requester, recipient, and person names; contact details; free text; and direct CRM identifiers.
4. Bind every metric contract to exact source/schema versions, authorization window, query/page/population/pseudonymization receipts, approved local period and IANA timezone, unit, currency, amount basis, metric definition, aggregation rule, freshness, section slot, and approval.
5. Treat every metric label as customer-defined. Never equate activity with engagement, usage with value, support volume with sentiment, CRM amount with recognized revenue, contract dates with renewal intent, or a supplied score with validated health/churn/renewal risk.
6. Reconcile each declared record population exactly once. Duplicate, extra, omitted, stale, future, unauthorized, partial, or conflicting evidence yields no calculated metric.
7. Compare only non-overlapping contracts with the same unit, currency, amount basis, definition, aggregation rule, timezone, and exact customer-approved comparison receipt.
8. Let the helper calculate approved totals, deltas, and percent changes once with Decimal arithmetic. A zero prior value yields a null percent change.
9. Assemble only blueprint-authorized sections, metric slots, comparisons, and customer-authored claim IDs/templates with exact approval and evidence bindings. Never accept, create, paraphrase, or display claim prose.
10. Preserve only `AVAILABLE`, `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `SUPPRESSED`, and `UNAUTHORIZED`; never replace a state with a guess, cache, prior period, benchmark, standard term, generic template, or confidence adjustment.
11. Never infer health, churn, renewal intent, urgency, sentiment, root cause, seasonality, business impact, executive alignment, expansion, conversation topics, action items, owner performance, or customer strategy.
12. Never rank accounts by risk, commercial value, renewal date, activity, or any other field. Never recommend customer, CSM, workforce, product, pricing, renewal, expansion, or escalation action.
13. Never export, publish, email, message, upload, write records or files, create tasks, schedule refreshes, alter a deck, or declare a packet customer-ready or compliant.
14. Return `HUMAN_REVIEW_REQUIRED` plus `narrative_authorized: false`, `action_authorized: false`, `delivery_authorized: false`, and `publication_authorized: false` for every valid assembly.
15. R1: never add an adequacy, performance, risk, confidence, health, or readiness adjective. Only exact helper evidence states may characterize evidence.
16. R2: return one helper-rendered response. Every calculated number must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.

## Workflow

1. Freeze authority, privacy, recipients, retention, and blueprint.
2. Validate metric contracts and complete record populations.
3. Validate same-basis comparisons and approved claim bindings.
4. Assemble only authorized QBR section slots.
5. Render helper stdout exactly; a human decides what to say, do, deliver, and publish.

## Worked Example

Input: an approved QBR blueprint contains current and prior adoption-metric contracts plus a customer-authored claim binding. One current record is `EVIDENCE_MISSING`. Run the helper: it withholds the current metric value, marks the comparison and bound claim `EVIDENCE_MISSING`, assembles only receipt IDs into the approved section, and authorizes no narrative, recommendation, delivery, or publication.

## Failure Boundary

Missing or incompatible authority, privacy, source, schema, authorization, query, page, population, pseudonymization, period, timezone, unit, currency, amount basis, definition, aggregation, freshness, comparison, claim, section, recipient, retention, or publication-policy evidence fails closed. Never replace it with a live lookup, cached value, inferred renewal date, supplied risk score, prior-QBR prose, generic benchmark, confidence score, recommendation, or action.
