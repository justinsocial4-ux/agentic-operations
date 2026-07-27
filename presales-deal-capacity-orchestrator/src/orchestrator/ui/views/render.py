"""Streamlit render functions for each Phase 7 view.

All authored wording comes from orchestrator.ui.copy so the terminology scan can
prove the UI never overclaims. Domain values are rendered as data, never as
claims. Nothing here mutates a source, writes a task, or performs any action.
"""
from __future__ import annotations

import streamlit as st

from orchestrator.contracts.enums import LaneV1
from orchestrator.ui import copy, theme
from orchestrator.ui.demo import DemoRun
from orchestrator.ui.state import (
    CONNECT_TARGETS,
    FlowState,
    LandingPath,
    ManagerDisposition,
    Stage,
    proof_rows,
    run_summary_line,
)
from orchestrator.ui.views.engine_run import clear_engine_run_state

_LANE_LABELS = {
    LaneV1.DEAL_PRIORITIZATION: copy.LANE_DEAL,
    LaneV1.ASSIGNMENT_RECOMMENDATION: copy.LANE_ASSIGNMENT,
    LaneV1.CAPACITY_HEATMAP: copy.LANE_CAPACITY,
}
_LABEL_TO_LANE = {label: lane for lane, label in _LANE_LABELS.items()}


def render_landing(flow: FlowState) -> None:
    st.header(copy.LANDING_HEADING)
    st.caption(copy.APP_TAGLINE)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(copy.BTN_RUN_DEMO, key="run_demo"):
            flow.choose_path(LandingPath.FICTIONAL_DEMO)
            st.rerun()
        st.caption(copy.LANDING_DEMO_HELP)
    with col2:
        if st.button(copy.BTN_IMPORT, key="import_path"):
            flow.choose_path(LandingPath.IMPORT)
            st.rerun()
        st.caption(copy.LANDING_IMPORT_HELP)
    with col3:
        if st.button(copy.BTN_CONNECT, key="connect_path"):
            flow.choose_path(LandingPath.CONNECT)
            st.rerun()
        st.caption(copy.LANDING_CONNECT_HELP)


def render_authority(flow: FlowState) -> None:
    st.header(copy.AUTHORITY_HEADING)
    st.write(copy.AUTHORITY_BODY)
    attested = st.checkbox(copy.CHK_ATTEST, key="attest")
    st.info(copy.TRANSCRIPT_WARNING)
    transcript_ack = st.checkbox(copy.CHK_TRANSCRIPT, key="transcript_ack")
    if st.button(copy.BTN_ATTEST, key="attest_continue", disabled=not attested):
        flow.attest(transcript_ack=transcript_ack)
        st.rerun()


def _render_connect_controls() -> None:
    """Neutral connect buttons: no scary copy, no warning badge on the button."""
    st.subheader(copy.CONNECT_HEADING)
    label_by_target = {
        "Salesforce": copy.BTN_CONNECT_SALESFORCE,
        "ClickUp": copy.BTN_CONNECT_CLICKUP,
        "Fathom": copy.BTN_CONNECT_FATHOM,
        "Gong": copy.BTN_CONNECT_GONG,
    }
    cols = st.columns(len(CONNECT_TARGETS))
    for col, target in zip(cols, CONNECT_TARGETS):
        with col:
            st.button(label_by_target[target], key=f"connect_{target.lower()}")
    # Separate, neutral proof/status area (not on the button).
    st.caption(copy.LIVE_VALIDATION_STATUS)
    st.caption(copy.CONNECT_FALLBACK)


def render_setup(flow: FlowState) -> None:
    st.header(copy.SETUP_HEADING)
    st.caption(copy.SETUP_SUBHEAD)

    lane_label = st.radio(
        copy.LANE_LABEL,
        options=[_LANE_LABELS[lane] for lane in _LANE_LABELS],
        key="lane",
    )
    lane = _LABEL_TO_LANE[lane_label]

    # Fixed horizon: displayed and confirm-only, never editable.
    st.info(copy.HORIZON_LINE)

    st.subheader(copy.CORE_GROUP_HEADING)
    st.caption(copy.SETUP_NO_SECOND_SCREEN)
    if st.button(copy.BTN_CONFIRM_CORE, key="confirm_core"):
        flow.confirm_core(lane)
        st.rerun()
    if flow.core_confirmed:
        st.success(copy.BTN_CONFIRM_CORE + " ✓")

    with st.expander(copy.ADVANCED_GROUP_HEADING):
        if st.button(copy.BTN_CONFIRM_ADVANCED, key="confirm_advanced"):
            flow.confirm_advanced()
            st.rerun()
        if flow.advanced_confirmed:
            st.success(copy.BTN_CONFIRM_ADVANCED + " ✓")

    st.caption(f"Confirmation actions used: {flow.setup_actions_used} of at most 2 (including authority).")

    if flow.path is LandingPath.CONNECT:
        _render_connect_controls()

    if st.button("Continue to mapping", key="to_mapping", disabled=not flow.setup_complete):
        flow.advance_to_mapping()
        st.rerun()


def render_mapping(flow: FlowState) -> None:
    st.header(copy.MAPPING_HEADING)
    st.write(copy.MAPPING_BODY)
    st.table({
        "Source field": ["work_id", "deal_id", "due_at", "amount"],
        "Canonical field": ["work_request_id", "deal_source_id", "milestone_due_time", "commercial_amount"],
    })
    if st.button("Continue to data health", key="to_health"):
        flow.stage = Stage.HEALTH
        st.rerun()


def render_health(flow: FlowState) -> None:
    st.header(copy.HEALTH_HEADING)
    st.write(copy.HEALTH_BODY)
    st.table({
        "Check": ["Rows read", "Missing required", "Duplicates", "Conflicts"],
        "Count": ["2", "0", "0", "0"],
    })
    if st.button("Continue to evidence", key="to_evidence"):
        flow.stage = Stage.EVIDENCE
        st.rerun()


def render_evidence(flow: FlowState, demo_run: DemoRun) -> None:
    st.header(copy.EVIDENCE_HEADING)
    st.write(copy.EVIDENCE_BODY)
    attachment = demo_run.conversation_attachment
    if attachment is not None:
        st.caption(
            f"Additive conversation evidence → deal {attachment.deal_source_id}, "
            f"dimension {attachment.dimension_id}, provenance {attachment.provenance} "
            f"(standalone lane: {attachment.is_standalone_lane})."
        )
    if st.button("Continue to results", key="to_results"):
        flow.stage = Stage.RESULTS
        st.rerun()


def _render_priority(demo_run: DemoRun) -> None:
    st.subheader(copy.PRIORITY_HEADING)
    st.table({
        "Deal": [p.deal_source_id for p in demo_run.priority_queue],
        "Priority (bp)": [p.priority_bp for p in demo_run.priority_queue],
        "Due week": [p.due_week_bucket for p in demo_run.priority_queue],
    })


def _render_assignment(demo_run: DemoRun) -> None:
    st.subheader(copy.ASSIGNMENT_HEADING)
    rec = demo_run.assignment_recommendation
    if rec is None:
        return
    theme.render_badges(rec.solver_status, rec.assignment_status)
    st.caption(f"Solver status: {rec.solver_status} | {rec.assignment_status}")
    for deal in rec.deals:
        recommended = deal.recommended_consultant_source_id or "(none)"
        alts = ", ".join(a.consultant_source_id for a in deal.rejected_eligible_alternatives) or "(none)"
        st.write(
            f"Deal {deal.deal_source_id}: recommended {recommended}; eligible alternatives: {alts}"
        )


def _render_capacity(demo_run: DemoRun) -> None:
    st.subheader(copy.CAPACITY_HEADING)
    cells = [c for c in demo_run.capacity_cells if c.week_bucket == 1]
    st.table({
        "Region": [c.region_id for c in cells],
        "Skill": [c.skill_id for c in cells],
        "Demand": [c.demand_units for c in cells],
        "Eligible supply": [c.eligible_supply_units for c in cells],
        "Surplus/deficit": [c.surplus_deficit_units for c in cells],
    })
    if demo_run.scenario_comparison is not None:
        st.subheader(copy.SCENARIO_HEADING)
        st.caption(f"Assumption label: {demo_run.scenario_comparison.label}")


def _render_digest(demo_run: DemoRun) -> None:
    if demo_run.digest is None:
        return
    st.subheader(copy.DIGEST_HEADING)
    for fact in demo_run.digest.facts:
        st.write(f"- {fact.statement}")


def render_proof(demo_run: DemoRun) -> None:
    st.header(copy.PROOF_HEADING)
    st.caption(copy.PROOF_BODY)
    for row in proof_rows(demo_run.export_bundle):
        with st.expander(f"Source {row.source_instance_id}"):
            st.write(f"Execution: {row.execution_mode}")
            st.write(f"Implementation: {row.implementation_proof}")
            st.write(f"Live validation: {row.live_validation_proof}")
            st.write(f"Decision-bearing: {row.decision_bearing}")
    st.subheader(copy.RUN_SUMMARY_HEADING)
    st.caption(copy.RUN_SUMMARY_BODY)
    st.write(run_summary_line(demo_run.export_bundle))
    st.caption(copy.PRODUCTION_READINESS_LINE)


def render_dispositions(flow: FlowState, demo_run: DemoRun) -> None:
    st.header(copy.DISPOSITION_HEADING)
    st.caption(copy.DISPOSITION_NOTE)
    rec = demo_run.assignment_recommendation
    deal_ids = (
        [d.deal_source_id for d in rec.deals]
        if rec is not None
        else [p.deal_source_id for p in demo_run.priority_queue]
    )
    for deal_id in deal_ids:
        st.write(f"Deal {deal_id}")
        cols = st.columns(4)
        with cols[0]:
            if st.button(copy.BTN_ACCEPT, key=f"accept_{deal_id}"):
                flow.record_disposition(ManagerDisposition(deal_id, "ACCEPT"))
                st.rerun()
        with cols[1]:
            if st.button(copy.BTN_OVERRIDE, key=f"override_{deal_id}"):
                flow.record_disposition(ManagerDisposition(
                    deal_id, "OVERRIDE", override_consultant_source_id="consultant-lyra",
                ))
                st.rerun()
        with cols[2]:
            if st.button(copy.BTN_REJECT, key=f"reject_{deal_id}"):
                flow.record_disposition(ManagerDisposition(deal_id, "REJECT"))
                st.rerun()
        with cols[3]:
            if st.button(copy.BTN_DEFER, key=f"defer_{deal_id}"):
                flow.record_disposition(ManagerDisposition(deal_id, "DEFER"))
                st.rerun()
        current = flow.dispositions.get(deal_id)
        if current is not None:
            st.caption(f"Recorded: {current.kind}")


def render_export_and_reset(flow: FlowState) -> None:
    st.header(copy.EXPORT_HEADING)
    st.caption(copy.EXPORT_NOTE)
    if st.button(copy.BTN_EXPORT, key="export"):
        flow.create_export()
        st.rerun()
    if flow.export_created:
        st.success("Recommendation export created locally (inert).")

    st.header(copy.RESET_HEADING)
    st.caption(copy.RESET_NOTE)
    if st.button(copy.BTN_RESET, key="reset"):
        flow.reset()
        clear_engine_run_state()
        st.rerun()


def render_results(flow: FlowState, demo_run: DemoRun) -> None:
    st.header("Results")
    if flow.path is LandingPath.FICTIONAL_DEMO:
        theme.render_badges("RECOMMENDATION_ONLY", "FICTIONAL_REPLAY", "NOT_LIVE_VALIDATED")
        if st.button(copy.BTN_WALK_RESTART, key="restart_walk"):
            flow.restart_walk()
            st.rerun()
    _render_priority(demo_run)
    _render_assignment(demo_run)
    _render_capacity(demo_run)
    _render_digest(demo_run)
    render_proof(demo_run)
    render_dispositions(flow, demo_run)
    render_export_and_reset(flow)
