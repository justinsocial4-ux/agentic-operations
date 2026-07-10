---
name: revops-vendor-performance
description: "Builds an evidence-backed vendor review that keeps contractual obligations, observed service, support, product commitments, adoption, cost, and security evidence separate. Make sure to use this skill whenever the user asks for a vendor scorecard, SLA or support review, SaaS vendor performance, QBR evidence, renewal or replacement analysis, vendor accountability, service credits, vendor risk evidence, or which tools are underperforming—even if they do not name the agent."
metadata:
  category: "Tech Stack & Operations"
  phase: "2"
  data_readiness: "approved_contract_policy_and_evidence_required"
  version: "2.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-07-10"
  dependencies:
    - "Customer-approved contract, service, support, utilization, cost, security, and decision policies"
  mcps:
    - "Contract, ticketing, telemetry, finance, identity, and approved vendor-risk sources in read-only mode"
  minimum_data:
    - "Named vendor/service, evaluation period, cutoff, source provenance, and exact requirement definitions"
---

# Vendor Performance Evidence Review

Build an auditable vendor review without hiding unlike evidence inside a master grade. Compare only like-for-like evidence to named requirements and leave unsupported decisions with a human owner.

## Bundled Resources

- Read `references/evidence_contract.md` before accepting contract, service, ticket, adoption, finance, roadmap, or security evidence.
- Read `references/requirement_assessment.md` before assigning `MET`, `NOT_MET`, `INDETERMINATE`, `NOT_APPLICABLE`, or `CONFLICTING`.
- Read `references/service_and_support.md` before calculating availability, response, resolution, incident, or support measures.
- Read `references/adoption_cost_commitments.md` before discussing utilization, licenses, costs, credits, pricing, or product commitments.
- Read `references/security_and_due_diligence.md` before assessing security, privacy, certification, questionnaire, or supplier-risk evidence.
- Read `references/decision_boundaries.md` before presenting renewal, negotiation, replacement, consolidation, credit, or escalation options.
- Read `references/output_template.md` before delivering a review.
- Read `references/research_and_claims.md` before repeating benchmark, labor, savings, market, security, or performance claims.
- Use `scripts/vendor_evidence.py` for exact rates, availability, requirement states, currency totals, and state summaries.

## Operating Rules

1. Work read-only. Do not update CRM/procurement fields, contact vendors, submit credits, send notices, create tickets, approve security, change spend, renew, terminate, purchase, consolidate, or replace.
2. Require vendor/service identity, evaluation period, cutoff, timezone, source IDs/versions, extraction times, contract/policy IDs/versions, owner, approver, and intended use.
3. Keep seven lanes separate: `CONTRACT`, `SERVICE`, `SUPPORT`, `COMMITMENTS`, `ADOPTION`, `COST`, and `SECURITY`. Never produce a universal vendor score, color, rank, health tier, or weighted rollup.
4. Classify evidence as `CONTRACTUAL`, `CUSTOMER_OBSERVED`, `VENDOR_ATTESTED`, `INDEPENDENT`, or `UNATTRIBUTED`. Vendor status, roadmaps, questionnaires, certifications, and self-reports do not become independent proof.
5. Assess only an exact named requirement. Record comparator, target, unit, clock, severity/scope, window, exclusions, numerator, denominator, and source. A proxy cannot prove contract compliance.
6. Use only `MET`, `NOT_MET`, `INDETERMINATE`, `NOT_APPLICABLE`, or `CONFLICTING`. Missing fields, zero denominators, immature clocks, unmatched services, conflicting terms, and incomparable periods never receive a guessed state.
7. Preserve unresolved and pending cases, excluded minutes, scheduled maintenance, customer-caused events, region/service scope, severity, business hours, pauses, and stop-clock rules. Do not discard hard cases from denominators.
8. Keep source disagreement visible. Customer telemetry and a vendor status page may coexist; neither silently overwrites the other. State which source supports each observation.
9. Treat adoption as customer utilization, not vendor performance. Never infer vendor quality, realized value, shelfware, causality, or renewal fitness from active-seat rate alone.
10. Keep contracted fee, invoice, paid cash, allocated cost, tax, credit candidate, credit approved, and credit received separate. Require currency, period, FX policy, and clause/formula provenance.
11. Product commitments require a named commitment record, accepted scope, due date, change history, and status evidence. Public roadmap language or sales conversation is not a contractual promise unless the approved policy says it is.
12. Security/privacy evidence is a risk-review lane, not a certification or legal conclusion. Record scope, issuer, issue/expiry dates, exceptions, attestation status, and reviewer. Never claim a vendor is secure, compliant, approved, or low-risk from a document name alone.
13. Compare vendors or periods only under identical definitions, scopes, clocks, currencies, maturity, and evidence policies. Otherwise return `INCOMPARABLE`.
14. Do not invent thresholds, weights, market medians, typical price increases, confidence percentages, savings, credits, switching costs, or causal explanations.
15. A clause-backed credit calculation is a `CREDIT_CANDIDATE`, not entitlement, approval, invoice offset, or cash received. Legal/procurement review remains required.
16. Recommendations require an approved decision rule and named approver. Without both, provide evidence-backed review options and outstanding questions only.
17. Every finding must link to requirement ID, evidence IDs, exact calculation, state rationale, gaps, conflicts, owner, and next review step.
18. Preserve the frozen receipt. Later evidence creates a new version; it does not silently rewrite the earlier review.

## Preflight

Record:

- vendor, legal entity, product/service, contract ID/version, service tier, owner, approver;
- evaluation period boundaries, cutoff, timezone, renewal date if relevant, and intended decision;
- approved requirement catalog and decision-policy ID/version;
- source/evidence inventory with provenance, evidence kind, coverage, and permissions;
- service scope, availability exclusions, support clocks, severities, pauses, and mature-case rule;
- utilization identity, licensed-seat, active-user, bot/test/admin, and observation rules;
- cost basis, currency/FX, invoices, allocations, taxes, and credit clauses;
- commitment ledger and security/privacy evidence scope.

Stop only the affected lane when its policy or evidence is absent. Do not block a contract review because adoption is unavailable, and do not reweight remaining lanes.

## Workflow

1. **Freeze scope and provenance.** Assign stable requirement/evidence IDs and record source versions, cutoff, period, and owner.
2. **Reconcile definitions.** Map contract language, telemetry, cases, finance records, and attestations without substituting public or proxy definitions.
3. **Calculate lane evidence.** Use the helper for exact availability, rates, currency totals, and numeric requirement comparisons.
4. **Assess requirements.** Assign one allowed state per named requirement and preserve conflicting evidence, exclusions, and unknowns.
5. **Keep business context separate.** Report adoption, cost, commitments, credits, and security evidence without folding them into service compliance.
6. **Prepare review options.** Link each option to evidence and an approved decision rule; otherwise list questions, owners, and review dates.
7. **Issue a receipt.** Freeze inputs, helper version, calculations, states, conflicts, unavailable items, and no-write boundary.

## Worked Example

A contract requires monthly availability of at least 99.9%. The approved 30-day clock contains 43,200 minutes, 60 approved excluded minutes, and 90 minutes of customer-observed in-scope downtime. The eligible denominator is 43,140 minutes; observed available time is 43,050 minutes; exact availability is `43050 / 43140 × 100 = 99.791376912...%`, so the customer-observed lane supports `NOT_MET` for that named requirement.

If the vendor status page says “no incidents,” the final requirement state is `CONFLICTING` unless an approved precedence policy selects the customer observation for assessment. Preserve the lane-level `NOT_MET` calculation, record the disagreement, and do not claim fraud. If 60 of 100 approved seats were active, report 60% utilization in the `ADOPTION` lane only. Do not use it to improve or worsen the availability finding, and do not say renew or replace without an approved decision rule and named approver.

## Output Contract

Return eight artifacts:

1. **Scope/policy receipt** — vendor/service, contract, period, cutoff, timezone, owners, policies, intended use, and no-write boundary.
2. **Source/evidence register** — evidence ID, source, version, extraction time, kind, lane, coverage, conflicts, and limits.
3. **Requirement register** — requirement ID, exact text, comparator, target/unit, scope/clock/exclusions, owner, and evidence IDs.
4. **Assessment table** — numerator, denominator, exact calculation, state, rationale, missing fields, conflict, and reviewer.
5. **Separate context tables** — commitments, adoption/utilization, cost/invoices/credits, and security/privacy evidence.
6. **Gap/conflict queue** — unresolved terms, mismatched services, immature cases, disputed incidents, missing records, and owner/date.
7. **Decision-review preview** — explicit option, supporting evidence, approved rule ID or `RULE_REQUIRED`, named approver, reversibility, and prohibited execution.
8. **Frozen receipt** — input hashes/versions, helper version, output version, generated time, and `NO EXTERNAL ACTION / NO SYSTEM WRITE`.

## Failure States

- `SCOPE_REQUIRED` — vendor, service, period, cutoff, or timezone is absent.
- `POLICY_REQUIRED` — requirement, evidence, denominator, currency, security, or decision policy is absent.
- `SOURCE_PROVENANCE_REQUIRED` — source ID/version or extraction time is missing.
- `REQUIREMENT_AMBIGUOUS` — target, unit, clock, scope, severity, or exclusions cannot be parsed without judgment.
- `INDETERMINATE` — evidence is missing, immature, zero-denominator, or insufficient for the named requirement.
- `CONFLICTING` — material sources or terms disagree and no approved precedence rule resolves them.
- `INCOMPARABLE` — definitions, scopes, periods, clocks, maturity, currencies, or policies differ.
- `MIXED_CURRENCY` — amounts lack one currency or an approved dated FX conversion.
- `CREDIT_FORMULA_REQUIRED` — clause-backed eligibility or formula is absent.
- `SECURITY_REVIEW_REQUIRED` — security/privacy evidence needs an authorized reviewer.
- `RULE_REQUIRED` — no approved decision rule maps evidence to the requested option.
- `APPROVAL_REQUIRED` — renewal, termination, replacement, negotiation, credit, spend, or system action lacks named approval.

Never convert an unavailable or conflicting state into a score, confidence percentage, vendor verdict, or automatic action.
