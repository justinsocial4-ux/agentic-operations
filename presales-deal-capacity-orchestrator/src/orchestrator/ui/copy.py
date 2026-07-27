"""Centralised, authored user-facing copy plus the terminology/claim scanner.

Every string the Phase 7 UI *authors* (headings, button labels, status lines,
help text) lives here so a single scanner can prove the UI never overclaims.
Domain data rendered at runtime (skill labels, IDs, receipt values) is not
authored copy and is never subject to this scan.

Boundary (Jay-set): connectors and statuses must never read as "live validated",
"integration", "production-ready", "works with", or "recommended by <DB>".
Statuses use the exact proof-qualified vocabulary from plan section 4.1/19.
"""
from __future__ import annotations

import re

# --- Forbidden marketing/overclaim phrases (case-insensitive) ------------------
# These are the exact terms called out by the Phase 7 gate terminology scan.
FORBIDDEN_CLAIM_TERMS: tuple[str, ...] = (
    "live validated",
    "live-validated",
    "integration",
    "production-ready",
    "production ready",
    "works with",
    "recommended by",
    "certified",
    "endorsed",
    "seamless",
)

# Words that must never appear on an action button (read-only/no-write posture).
FORBIDDEN_BUTTON_VERBS: tuple[str, ...] = (
    "assign",
    "staff",
    "send",
    "sync",
    "update",
    "invite",
    "schedule",
)

# Exact proof-qualified vocabulary allowed in status text.
ALLOWED_STATUS_TOKENS: tuple[str, ...] = (
    "FICTIONAL_REPLAY",
    "FILE_IMPORT",
    "DIRECT_CONNECTOR_ENABLED",
    "DIRECT_CONNECTOR_DISABLED",
    "FULLY_IMPLEMENTED_CONTRACT_TESTED",
    "MOCK_TESTED_ONLY",
    "ADAPTER_INTERFACE_ONLY",
    "NOT_LIVE_VALIDATED",
    "LIVE_SANDBOX_VALIDATED",
    "RECOMMENDATION_ONLY",
    "NOT_ASSESSED",
    "WEAKEST_DECISION_BEARING_SOURCE",
)


def scan_text(text: str) -> tuple[str, ...]:
    """Return the forbidden claim terms present in a block of authored copy."""
    lowered = text.lower()
    hits: list[str] = []
    for term in FORBIDDEN_CLAIM_TERMS:
        if term in lowered:
            hits.append(term)
    return tuple(hits)


def scan_button_label(label: str) -> tuple[str, ...]:
    """Return forbidden write-verbs present in an authored button label."""
    words = set(re.findall(r"[a-z]+", label.lower()))
    return tuple(verb for verb in FORBIDDEN_BUTTON_VERBS if verb in words)


# --- Authored copy constants ---------------------------------------------------
APP_TITLE = "Presales Deal & Capacity Orchestrator"
APP_TAGLINE = "Local-first, recommendation-only prototype. No account or credential is required for the demo."

# Landing page
LANDING_HEADING = "Choose how to start"
BTN_RUN_DEMO = "Run fictional demo"
BTN_IMPORT = "Import authorized CSV/JSON"
BTN_CONNECT = "Connect authorized read-only source"
LANDING_DEMO_HELP = "Deterministic fictional fixtures. No account, key, or model needed."
LANDING_IMPORT_HELP = "Local CSV/JSON exports with a field-mapping and data-health review."
LANDING_CONNECT_HELP = "Optional read-only adapters. File import is always available as the contract-validated fallback."

# Authority / privacy gate
AUTHORITY_HEADING = "Authorization and data minimization"
AUTHORITY_BODY = (
    "Confirm you are authorized to access and process the selected exports or account data "
    "for this local evaluation, that you selected the minimum necessary fields and time range, "
    "and that this tool produces recommendations only."
)
TRANSCRIPT_WARNING = (
    "Transcripts may contain customer, employee, or sensitive private information. Full transcript "
    "text stays in process memory only; only hashes, metadata, and cited excerpts can be persisted."
)
BTN_ATTEST = "I attest and continue"
CHK_ATTEST = "I am authorized and selected the minimum necessary data"
CHK_TRANSCRIPT = "I acknowledge the transcript privacy notice"

# Run setup (single combined screen)
SETUP_HEADING = "Run setup"
SETUP_SUBHEAD = "One screen. Choose an output lane, confirm sources and policy in at most two actions."
LANE_LABEL = "Output lane"
LANE_DEAL = "Deal prioritization"
LANE_ASSIGNMENT = "Assignment recommendation"
LANE_CAPACITY = "Capacity heatmap"
HORIZON_LINE = "Planning horizon: 4 weeks (fixed in v1; confirm-only, not editable)"
CORE_GROUP_HEADING = "Core policy — editable, then confirm as one group"
ADVANCED_GROUP_HEADING = "Advanced policy — reviewed defaults"
BTN_CONFIRM_CORE = "Confirm authority and core policy"
BTN_CONFIRM_ADVANCED = "Confirm Advanced reviewed defaults"
SETUP_NO_SECOND_SCREEN = "This is the only setup screen. There is no per-field questioning and no second screen."

# Connect controls (neutral)
CONNECT_HEADING = "Connect a read-only source"
BTN_CONNECT_SALESFORCE = "Connect Salesforce"
BTN_CONNECT_CLICKUP = "Connect ClickUp"
BTN_CONNECT_FATHOM = "Connect Fathom"
BTN_CONNECT_GONG = "Connect Gong"
CONNECT_FALLBACK = "Import authorized export — contract-validated fallback"
LIVE_VALIDATION_STATUS = "Live validation: Not yet validated"

# Mapping / health
MAPPING_HEADING = "Field mapping"
MAPPING_BODY = "Map each source field to a canonical field. Unknown fields are never mapped for you."
HEALTH_HEADING = "Data health"
HEALTH_BODY = "Populations are reconciled. Missing, invalid, duplicate, stale, and conflicting rows are shown, never silently dropped."

# Evidence
EVIDENCE_HEADING = "Readiness evidence"
EVIDENCE_BODY = (
    "Conversation evidence is additive only. It attaches to a Deal prioritization or Assignment "
    "run through an exact deal crosswalk and can affect only the cited readiness-coverage path. "
    "It is never a standalone output lane and never picks or scores a consultant."
)

# Recommendation views
PRIORITY_HEADING = "Deal prioritization queue"
ASSIGNMENT_HEADING = "Assignment recommendation"
CAPACITY_HEADING = "Capacity heatmap"
SCENARIO_HEADING = "EMEA +25% effort assumption (not a forecast)"
DIGEST_HEADING = "Leadership digest (fact-bound)"

# Proof rows
PROOF_HEADING = "Per-source proof"
PROOF_BODY = "Each source shows three separate proof fields. No source row is collapsed into one tuple; there is no strongest-source rule."
RUN_SUMMARY_HEADING = "Conservative run summary"
RUN_SUMMARY_BODY = "Derived from the weakest decision-bearing source. Runtime success never promotes proof."

# Manager dispositions
DISPOSITION_HEADING = "Manager disposition"
BTN_ACCEPT = "Accept recommendation"
BTN_OVERRIDE = "Override to another eligible consultant"
BTN_REJECT = "Reject"
BTN_DEFER = "Defer"
DISPOSITION_NOTE = "Dispositions are recorded locally only. Nothing is assigned, staffed, or written back."

# Export / reset
EXPORT_HEADING = "Export"
BTN_EXPORT = "Create recommendation export"
EXPORT_NOTE = (
    "Export is inert: recommendation only. It performs no CRM write, task, webhook, message, "
    "or production mutation."
)
RESET_HEADING = "Reset"
BTN_RESET = "Reset and delete local run data"
RESET_NOTE = "This purges app-controlled local run state. It cannot revoke credentials or delete vendor data."

PRODUCTION_READINESS_LINE = "Production readiness: NOT_ASSESSED"

# --- Guided step-through walkthrough (Kevin-facing plain-English narration) -----
# The walkthrough narrates the SAME deterministic fictional run in decision order.
# It runs no new computation; it explains, in plain English, what the engine does
# and why, one decision stage at a time. All wording is scanned for overclaim.
WALK_HEADING = "Guided walkthrough"
WALK_PROGRESS_PREFIX = "Step"  # rendered as "Step X of N"
BTN_WALK_NEXT = "Next"
BTN_WALK_BACK = "Back"
BTN_WALK_SKIP = "Skip to full results"
BTN_WALK_RESTART = "Start walkthrough over"

# Live execution entry for the fictional path. Values inserted into these
# templates come only from the real deterministic receipts emitted by demo.py.
RUN_HEADING = "Watch the recommendation happen"
BTN_RUN_ENGINE = "Run the engine"
RUN_HELP = (
    "Execute the deterministic fictional pipeline now. Decision receipts will appear in "
    "the order they are produced; then the seven-step walkthrough remains below for study."
)
RUN_STATUS_EXECUTING = "Executing the fictional pipeline…"
RUN_STATUS_COMPLETE = "Engine run complete — recommendation receipt ready"
RUN_STATUS_PREVIOUS = "Last engine run — receipt-derived reasoning"
RUN_LIST_VIEW_HELP = (
    "Full reasoning trail from the completed run — every stage, top to bottom. "
    "Same receipt-derived data shown live during the run; nothing added or altered."
)
RUN_START = "Starting a fresh FICTIONAL_REPLAY run. No account, credential, vendor call, or remote model is used."

RUN_BEAT_FIXTURES = "1 · Gather the deals and consultants"
RUN_BEAT_FIXTURES_CAPTION = (
    "Reading the test data: which deals need presales help, and which consultants are available."
)
RUN_FIXTURE_TEMPLATE = (
    "Loaded {deal_count} deals ({deal_ids}), {consultant_count} manager-approved consultants "
    "({consultant_ids}), and {conversation_count} attached conversation evidence path(s)."
)
RUN_BEAT_READINESS = "2 · Check each deal's readiness"
RUN_BEAT_READINESS_CAPTION = (
    "Before a deal competes for time, every readiness fact — scope, security, success "
    "criteria — must be backed by an exact citation."
)
RUN_READINESS_TEMPLATE = (
    "Checking `{deal_id}`: {supported_count}/{dimension_count} dimensions are SUPPORTED; "
    "{required_count} are required. Exact citations: {citations}."
)
RUN_TRANSCRIPT_BOUNDARY_TEMPLATE = (
    "`{deal_id}` uses TRANSCRIPT evidence for `{dimensions}`. Those exact citations satisfy "
    "readiness only; conversation text never selects or scores a consultant."
)
RUN_BEAT_PRIORITY = "3 · Rank deals by priority"
RUN_BEAT_PRIORITY_CAPTION = (
    "Each deal gets a priority score from urgency, readiness, and commercial value, "
    "so the most important work competes first for scarce time."
)
RUN_PRIORITY_TEMPLATE = (
    "`{deal_id}`: {formula}; weighted numerator {weighted_total:,} ÷ 10,000 = "
    "**{priority_bp} bp** ({rounding})."
)
RUN_BEAT_ELIGIBILITY = "4 · Find eligible consultants"
RUN_BEAT_ELIGIBILITY_CAPTION = (
    "Only manager-approved consultants are considered. Each is checked for region, skills, "
    "language, time-zone overlap, and capacity for each deal."
)
RUN_ELIGIBILITY_TEMPLATE = (
    "`{deal_id}` × `{consultant_id}`: checked {check_count} hard constraints "
    "({checks}) → **{result}**; projected utilization {utilization_bp} bp."
)
RUN_ELIGIBILITY_SUMMARY_TEMPLATE = (
    "Eligibility closed for `{deal_id}`: {eligible_count} of {roster_count} manager-approved "
    "consultants are eligible ({eligible_ids})."
)
RUN_CONSTRAINTS_TEMPLATE = "Receipt constraints ({check_count}): {checks}."
RUN_BEAT_SOLVER = "5 · Match consultants to deals"
RUN_BEAT_SOLVER_CAPTION = (
    "The optimizer assigns the WHOLE portfolio at once — not deal-by-deal — so scarce "
    "specialists stay available for the work only they can cover."
)
RUN_SOLVER_TEMPLATE = (
    "{engine} solved {deal_count} deals with {eligible_pair_count} eligible deal-consultant pairs "
    "as one portfolio: **{status}**. Objectives: {objectives}."
)
RUN_ASSIGNMENT_TEMPLATE = (
    "`{deal_id}` → `{consultant_id}` (priority {priority_bp} bp, fit {fit_bp} bp). "
    "Eligible alternatives: {alternatives}."
)
RUN_BEAT_CAPACITY = "6 · Check the capacity impact"
RUN_BEAT_CAPACITY_CAPTION = (
    "If EMEA deals take 25% more effort than planned, does capacity flip? This is a planning "
    "input, not a forecast."
)
RUN_SCENARIO_CHANGE_TEMPLATE = (
    "`{deal_id}` EMEA effort: {base_units} → {scenario_units} units under multiplier {multiplier}."
)
RUN_SCENARIO_CELL_TEMPLATE = (
    "Week {week}, `{skill_id}`: base {base_position} → scenario {scenario_position}; "
    "supply {supply_units} units."
)
RUN_SCENARIO_LABEL_TEMPLATE = "Receipt label: **{label}**. This is a planning input, not a prediction."
RUN_BEAT_DONE = "7 · Hand off to the manager"
RUN_BEAT_DONE_CAPTION = (
    "The engine stops here. A manager accepts, overrides, rejects, or defers — nothing is "
    "written back to any system."
)
RUN_DONE_TEMPLATE = (
    "Done. {assignment_status} produced with solver status {solver_status}. Manager decides; "
    "external writes attempted: {external_writes_attempted}. The export remains inert and "
    "nothing is written back."
)
RUN_PROOF_TEMPLATE = (
    "Run proof: {execution_modes} · {implementation_proof} · {live_validation_proof} · "
    "{derivation}. Production readiness: NOT_ASSESSED."
)

# (The earlier in-app "Dark mode" toggle was removed: it could not coherently
# re-theme Streamlit's native widgets, whose light/dark base is set at startup.
# Dark mode now uses Streamlit's native theme switch — Main menu → Settings →
# Theme — which themes every surface coherently.)

# a. Intro
WALK_INTRO_TITLE = "How the engine decides"
WALK_INTRO_BODY = (
    "Here's what we're about to do: figure out which deal work deserves scarce presales "
    "time next. We'll walk through how the engine reaches a recommendation, one decision "
    "stage at a time. Everything here is recommendation-only \u2014 the engine proposes, a "
    "manager decides, and nothing is booked or written back to any system."
)

# b. Readiness
WALK_READINESS_TITLE =  "Is the deal ready?"
WALK_READINESS_BODY = (
    "A deal can't be prioritized until its readiness facts are established. Each dimension "
    "below reads SUPPORTED only when an exact citation backs it. Conversation evidence \u2014 an "
    "exact quote \u2014 can satisfy a versioned readiness dimension, but the engine never scores a "
    "person from call text."
)

# c. Priority
WALK_PRIORITY_TITLE =  "How urgent and valuable is it?"
WALK_PRIORITY_BODY = (
    "Readiness, milestone urgency, and commercial value combine into one priority score, "
    "measured in basis points. Each contributing feature is weighted, so you can see exactly "
    "why one deal sits above another in the queue. Higher score means it competes first for "
    "scarce presales time."
)

# d. Eligible consultants
WALK_ELIGIBLE_TITLE =  "Who is allowed to help?"
WALK_ELIGIBLE_BODY = (
    "The optimizer can only consider consultants a manager has already approved. Fit comes "
    "from approved skills, capacity, and availability \u2014 never from call text. Below is the "
    "approved roster the engine is allowed to draw from for the top deal."
)

# e. Assignment
WALK_ASSIGNMENT_TITLE =  "Which consultant, and why?"
WALK_ASSIGNMENT_BODY = (
    "The optimizer solves the whole portfolio at once, not one deal at a time. It proved an "
    "OPTIMAL match under the frozen eligibility, capacity, and policy receipts. Below is why "
    "this consultant was chosen over the eligible alternative: every hard constraint passed, "
    "and the weighted match components explain the fit. When two candidates tie on the proven "
    "objective, the engine breaks the tie by stable identifier \u2014 never by call text."
)

# f. Capacity impact
WALK_CAPACITY_TITLE =  "What does this do to capacity?"
WALK_CAPACITY_BODY = (
    "This is the capacity picture for the affected region and skills. You can also apply a "
    "what-if lever: an EMEA +25% effort assumption. That figure is a "
    "USER_SELECTED_ASSUMPTION_NOT_A_FORECAST \u2014 a manual planning input, not a prediction."
)

# g. Manager step
WALK_MANAGER_TITLE =  "You decide"
WALK_MANAGER_BODY = (
    "The engine stops here. It hands you a recommendation and the proof behind it. You can "
    "accept, override, reject, or defer. Any export is inert \u2014 nothing is booked, messaged, "
    "or written back to any source."
)


def all_authored_copy() -> dict[str, str]:
    """Every authored string constant, for the terminology scan test."""
    module_globals = globals()
    return {
        name: value
        for name, value in module_globals.items()
        if name.isupper() and isinstance(value, str) and not name.startswith("_")
        and name not in {"FORBIDDEN_CLAIM_TERMS", "FORBIDDEN_BUTTON_VERBS", "ALLOWED_STATUS_TOKENS"}
    }


def all_button_labels() -> dict[str, str]:
    """Every authored button label constant (prefixed BTN_)."""
    return {name: value for name, value in globals().items() if name.startswith("BTN_")}
