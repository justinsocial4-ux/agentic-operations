"""Guided step-through walkthrough for the fictional demo path.

This narrates the SAME deterministic fictional run in decision order, pausing at
each stage to explain in plain English what the engine does and why BEFORE moving
on. It performs no new computation: it reads the already-composed DemoRun.

All authored wording lives in orchestrator.ui.copy so the terminology scan can
prove the walkthrough never overclaims. Domain values are rendered as data.
"""
from __future__ import annotations

import streamlit as st

from orchestrator.ui import copy, theme
from orchestrator.ui.demo import DemoRun
from orchestrator.ui.state import WALKTHROUGH_STEPS, FlowState, WalkStep
from orchestrator.ui.views.engine_run import render_engine_run

_TITLE_BODY = {
    WalkStep.INTRO: (copy.WALK_INTRO_TITLE, copy.WALK_INTRO_BODY),
    WalkStep.READINESS: (copy.WALK_READINESS_TITLE, copy.WALK_READINESS_BODY),
    WalkStep.PRIORITY: (copy.WALK_PRIORITY_TITLE, copy.WALK_PRIORITY_BODY),
    WalkStep.ELIGIBLE: (copy.WALK_ELIGIBLE_TITLE, copy.WALK_ELIGIBLE_BODY),
    WalkStep.ASSIGNMENT: (copy.WALK_ASSIGNMENT_TITLE, copy.WALK_ASSIGNMENT_BODY),
    WalkStep.CAPACITY: (copy.WALK_CAPACITY_TITLE, copy.WALK_CAPACITY_BODY),
    WalkStep.MANAGER: (copy.WALK_MANAGER_TITLE, copy.WALK_MANAGER_BODY),
}


def _top_deal_id(demo_run: DemoRun) -> str:
    return demo_run.priority_queue[0].deal_source_id


# --- per-stage data panels -----------------------------------------------------
def _panel_intro(demo_run: DemoRun) -> None:
    theme.render_badges("RECOMMENDATION_ONLY", "FICTIONAL_REPLAY", "NOT_LIVE_VALIDATED")
    st.caption(copy.APP_TAGLINE)


def _panel_readiness(demo_run: DemoRun) -> None:
    deal_id = _top_deal_id(demo_run)
    readiness = demo_run.readiness_by_deal[deal_id]
    st.markdown(f"**Deal `{deal_id}` — readiness dimensions**")
    rows_dim, rows_state, rows_prov, rows_cite = [], [], [], []
    for dim in readiness.dimensions:
        rows_dim.append(dim.dimension_id)
        rows_state.append(dim.state)
        rows_prov.append(", ".join(dim.provenance))
        rows_cite.append(", ".join(dim.citation_ids))
    st.table({
        "Readiness dimension": rows_dim,
        "State": rows_state,
        "Evidence source": rows_prov,
        "Exact citation": rows_cite,
    })
    # Highlight the transcript-satisfied dimension explicitly.
    transcript_dims = [d.dimension_id for d in readiness.dimensions if "TRANSCRIPT" in d.provenance]
    if transcript_dims:
        st.markdown("Conversation-satisfied dimension(s):")
        theme.render_badges(*[f"TRANSCRIPT" for _ in transcript_dims][:1])
        st.caption(
            f"Dimension `{transcript_dims[0]}` was satisfied by an exact cited quote. "
            "The quote satisfies a versioned readiness fact only — it never picks or scores a consultant."
        )


def _panel_priority(demo_run: DemoRun) -> None:
    st.markdown("**Priority queue (higher basis-point score competes first)**")
    for receipt in demo_run.priority_queue:
        theme.card_open(
            title=f"{receipt.deal_source_id} — priority {receipt.priority_bp} bp",
            subtitle=f"due week {receipt.due_week_bucket} · "
                     f"commercial {receipt.commercial_amount_used} {receipt.commercial_currency}",
        )
        st.table({
            "Contributing feature": [f.feature_id for f in receipt.features],
            "Feature (bp)": [f.feature_bp for f in receipt.features],
            "Weight (bp)": [f.weight_bp for f in receipt.features],
        })
        theme.card_close()
    st.caption(
        "Plain English: each feature score is multiplied by its weight and summed, then "
        "rounded, to give the deal's priority in basis points."
    )


def _panel_eligible(demo_run: DemoRun) -> None:
    deal_id = _top_deal_id(demo_run)
    st.markdown(f"**Manager-approved roster the engine may draw from for `{deal_id}`**")
    for c in demo_run.roster:
        theme.card_open(
            title=c.consultant_source_id,
            subtitle=f"regions {', '.join(c.supported_region_ids)} · "
                     f"languages {', '.join(c.languages)}",
        )
        st.table({
            "Manager-approved skill": [s for s, _ in c.skill_levels],
            "Level": [lvl for _, lvl in c.skill_levels],
        })
        theme.card_close()
    st.caption(
        "Only these manager-approved consultants can be considered. Fit is computed from "
        "approved skills, capacity, and availability — never from call text."
    )


def _panel_assignment(demo_run: DemoRun) -> None:
    rec = demo_run.assignment_recommendation
    sr = demo_run.solver_receipt
    if rec is None:
        st.caption("No assignment recommendation in this run.")
        return
    theme.render_badges(rec.solver_status, rec.assignment_status)
    if sr is not None:
        st.caption(
            f"Portfolio proof: serviced-priority objective {sr.serviced_priority_total}, "
            f"portfolio-match objective {sr.portfolio_match_total} "
            f"(solved as one portfolio, all deals together)."
        )
    deal = next((d for d in rec.deals if d.deal_source_id == _top_deal_id(demo_run)), rec.deals[0])
    recommended = deal.recommended_consultant_source_id or "(none)"
    theme.card_open(
        title=f"{deal.deal_source_id} → recommended {recommended}",
        subtitle="why this consultant, and why not the alternative",
    )
    proof = deal.recommended_hard_constraint_proof
    if proof is not None:
        passed = sum(1 for c in proof.checks if c.passed)
        st.markdown(f"**Hard constraints:** {passed} of {len(proof.checks)} checks passed")
        st.table({
            "Hard constraint": [c.check_id for c in proof.checks],
            "Passed": [c.passed for c in proof.checks],
        })
    mc = deal.recommended_match_contributions
    if mc is not None:
        st.markdown(f"**Match fit:** {mc.fit_bp} bp")
        st.table({
            "Match component": [c.component_id for c in mc.components],
            "Component (bp)": [c.component_bp for c in mc.components],
            "Weight (bp)": [c.weight_bp for c in mc.components],
        })
    alts = deal.rejected_eligible_alternatives
    if alts:
        st.markdown("**Eligible alternative(s):**")
        for a in alts:
            theme.render_badges(a.disposition)
            st.caption(
                f"`{a.consultant_source_id}` — disposition {a.disposition}; "
                f"serviced-priority delta {a.serviced_priority_delta}, "
                f"portfolio-match delta {a.portfolio_match_delta}. "
                "When alternatives tie on the proven objective, the engine breaks the tie by "
                "stable identifier, not by call text."
            )
    else:
        st.caption("No eligible alternative was rejected for this deal.")
    theme.card_close()


def _panel_capacity(demo_run: DemoRun) -> None:
    cells = [c for c in demo_run.capacity_cells if c.week_bucket == 1]
    st.markdown("**Capacity for the affected region/skills (week 1)**")
    st.table({
        "Region": [c.region_id for c in cells],
        "Skill": [c.skill_id for c in cells],
        "Demand": [c.demand_units for c in cells],
        "Eligible supply": [c.eligible_supply_units for c in cells],
        "Surplus/deficit": [c.surplus_deficit_units for c in cells],
    })
    sc = demo_run.scenario_comparison
    if sc is not None:
        st.markdown("**What-if lever**")
        theme.render_badges("USER_SELECTED_ASSUMPTION_NOT_A_FORECAST")
        st.caption(f"Assumption label: {sc.label}")


def _panel_manager(demo_run: DemoRun) -> None:
    theme.render_badges("RECOMMENDATION_ONLY", "NOT_ASSESSED")
    st.caption(copy.DISPOSITION_NOTE)
    st.caption(copy.EXPORT_NOTE)
    st.caption(copy.PRODUCTION_READINESS_LINE)


_PANELS = {
    WalkStep.INTRO: _panel_intro,
    WalkStep.READINESS: _panel_readiness,
    WalkStep.PRIORITY: _panel_priority,
    WalkStep.ELIGIBLE: _panel_eligible,
    WalkStep.ASSIGNMENT: _panel_assignment,
    WalkStep.CAPACITY: _panel_capacity,
    WalkStep.MANAGER: _panel_manager,
}


def render_walkthrough(flow: FlowState, demo_run: DemoRun) -> None:
    # The live execution is the watch-it-work entry; the unchanged walkthrough
    # immediately below remains the study-at-your-own-pace path.
    demo_run = render_engine_run(demo_run)
    st.divider()

    step = flow.current_walk_step
    total = len(WALKTHROUGH_STEPS)
    st.header(copy.WALK_HEADING)
    st.caption(f"{copy.WALK_PROGRESS_PREFIX} {flow.walk_index + 1} of {total}")
    theme.render_progress_rail(flow.walk_index, total)

    title, body = _TITLE_BODY[step]
    st.subheader(title)
    st.write(body)

    _PANELS[step](demo_run)

    st.divider()
    cols = st.columns([1, 1, 2])
    with cols[0]:
        if st.button(copy.BTN_WALK_BACK, key="walk_back", disabled=flow.is_first_walk_step):
            flow.prev_walk()
            st.rerun()
    with cols[1]:
        # Stable label/key across stages (avoids widget-identity churn). On the
        # final stage, Next falls through to the full results view.
        if st.button(copy.BTN_WALK_NEXT, key="walk_next", type="primary"):
            flow.next_walk()
            st.rerun()
    with cols[2]:
        if st.button(copy.BTN_WALK_SKIP, key="skip_to_results"):
            flow.skip_to_results()
            st.rerun()
