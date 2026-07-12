---
name: revops-board-exec-deck
description: "Assembles customer-approved pseudonymous metric and claim receipts into deterministic slide-ready board or executive evidence blocks without inventing narrative, causes, risk labels, recommendations, or publication approval. Make sure to use this skill whenever the user asks to build, generate, refresh, review, summarize, narrate, export, send, or present a board deck, executive deck, QBR, MBR, investor update, revenue review, forecast presentation, or KPI packet—even when the request assumes CRM fields equal finance measures, prior-period numbers are comparable, the agent can explain why a metric changed, or a draft is ready to share."
metadata:
  category: "Reporting & Analytics"
  phase: "2"
  data_readiness: "complete_customer_supplied_metric_claim_and_slide_receipts_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-11"
  dependencies:
    - "Customer-approved policy, metric, population, comparison, finance, claim, slide, recipient, retention, and publication receipts"
  mcps:
    - "None; accept pre-supplied structured evidence only"
  minimum_data:
    - "Stable anonymous policy, slide, metric, contract, record, source, period, comparison, claim, and receipt IDs"
---

# Board and Executive Deck Evidence Assembly

Assemble only what complete customer-supplied receipts support. Produce slide-ready evidence blocks, not a finished presentation or an invented executive story.

## Exact Response Rule

Build the input document, run scripts/board_packet.py, and return render_packet_output(assemble_board_packet(document)) byte for byte. The first response byte must be {; the helper supplies the final empty terminal line after }. Do not add Markdown fences or model prose. The helper owns every output value and boundary.

## Bundled Resources

- Read references/scope_and_authority.md before accepting purpose, audience, access, recipients, retention, or publication state.
- Read references/metric_contracts.md before accepting any KPI, finance, CRM, forecast, pipeline, ARR, bookings, or revenue number.
- Read references/population_and_lineage.md before accepting sources, queries, schemas, pages, records, freshness, or completeness.
- Read references/comparison_and_time.md before calculating a delta, ratio, trend, period comparison, currency amount, or forecast variance.
- Read references/claims_and_slides.md before assembling slide blocks, claim ledgers, narrative tokens, or visual references.
- Read references/privacy_and_actions.md before handling deal, account, customer, worker, recipient, recommendation, distribution, or action requests.
- Read references/output_contract.md before rendering a result.
- Read references/verification_sources.md for current official sources supporting this boundary.
- Use scripts/board_packet.py for validation, Decimal arithmetic, receipt assembly, and exact rendering.

## Operating Rules

1. Work offline and read-only. Never query CRM, finance, forecast, analytics, email, files, identity, presentation, or messaging systems.
2. Require one effective policy with exact purpose, audience class, confidentiality class, reporting cutoff, reviewer, allowed recipient roles, retention, slide blueprint, and separate approval receipts.
3. Accept only pseudonymous IDs. Reject organization, account, deal, opportunity, customer, worker, owner, requester, recipient, and person names or contact details.
4. Bind every metric contract to exact source and schema versions, authorization window, query and page receipts, population, local period and IANA timezone, unit, currency, amount basis, definition, aggregation method, freshness, and approval.
5. Never equate CRM amount, pipeline, bookings, ARR, forecast, recognized revenue, cash, or a GAAP measure. The exact customer metric definition and finance approval control the label and basis.
6. A non-GAAP financial measure additionally requires its exact label, directly comparable GAAP metric contract, reconciliation receipt, period-consistency receipt, and finance approval. Missing evidence fails closed.
7. Reconcile each declared record population exactly once. Duplicate, extra, stale, future, unauthorized, incomplete, or conflicting evidence produces no calculated metric.
8. Compare only contracts with the same unit, currency, amount basis, definition, aggregation method, and approved comparison-basis receipt. Never use fuzzy stage, date, identity, or measure mapping.
9. Let the helper calculate approved totals, deltas, and percent changes once with Decimal arithmetic. A zero prior value yields a null percent change.
10. Assemble only blueprint-authorized slides, metric slots, comparison slots, and customer-authored claim IDs with exact approval and evidence bindings. Do not write or paraphrase claim text.
11. Exact evidence states are AVAILABLE, EVIDENCE_MISSING, EVIDENCE_CONFLICT, SUPPRESSED, and UNAUTHORIZED. Preserve them without substitution.
12. Never explain why a metric changed, infer cause, predict outcomes, estimate missing values, label risk/confidence/health/readiness, rank deals or workers, or recommend executive, customer, workforce, budget, forecast, or GTM action.
13. Never export, publish, email, message, upload, write records, create tasks, alter a deck, or declare it board-ready. Human reviewers own narrative, legal/finance review, action, and publication.
14. Return HUMAN_REVIEW_REQUIRED plus narrative_authorized: false, action_authorized: false, and publication_authorized: false for every valid assembly.
15. R1: never add an adequacy, performance, risk, confidence, or readiness adjective. Only exact helper states may characterize evidence.
16. R2: return one helper-rendered response. Every number must come from the helper and appear only in its assigned receipt; never recompute, narrate, duplicate, or self-correct it.

## Workflow

1. Freeze authority and blueprint.
2. Validate metric and finance contracts.
3. Reconcile complete populations and lineage.
4. Validate same-basis comparisons and approved claims.
5. Calculate once and assemble only authorized slide slots.
6. Render helper stdout exactly; a human decides what to say and publish.

## Worked Example

Input: an approved blueprint contains exact GAAP and reconciled non-GAAP metric receipts plus a current-versus-prior pipeline comparison. The current pipeline record is EVIDENCE_MISSING. Run the helper: it preserves the approved finance receipts, withholds the pipeline comparison, marks the bound claim EVIDENCE_MISSING, and authorizes no narrative, recommendation, distribution, or publication.

## Failure Boundary

Missing or incompatible authority, confidentiality, source, schema, authorization, query, page, population, period, timezone, unit, currency, amount basis, metric definition, aggregation, finance, non-GAAP, comparison, claim, slide, recipient, retention, or publication evidence fails closed. Never replace it with a live lookup, cached value, assumed CRM meaning, prior-deck prose, generic benchmark, confidence score, recommendation, or action.
