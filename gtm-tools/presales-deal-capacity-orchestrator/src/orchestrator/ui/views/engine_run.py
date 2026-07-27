"""Live, receipt-derived narration for the fictional pipeline execution.

The button executes ``run_demo_pipeline`` rather than replaying prepared text.
Every displayed ID, check, score, objective, assignment, scenario delta, and
proof token is read from the event artifact that the deterministic composition
just produced. Observation is UI-only and cannot affect an engine decision.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

import streamlit as st

from orchestrator.ui import copy
from orchestrator.ui.demo import DemoPipelineEvent, DemoRun, run_demo_pipeline

_NARRATION_DELAY_SECONDS = 0.20
# Per-line reveal timing (the "watch it think" feel). Slow enough that each
# line reads as it appears, not as a data dump.
_LINE_REVEAL_SECONDS = 1.3
# Pause when a new stage badge appears, so the eye registers the step change.
_STAGE_INTRO_SECONDS = 0.9
# Brief pause between stages so the run doesn't feel rushed.
_STAGE_GAP_SECONDS = 0.7

# Per-stage pacing — natural variation so the run doesn't feel like a tick-tock
# automated demo. Some stages (readiness, eligibility, solving) get more
# deliberation; quick stages (load, hand-off) feel snappy. The big solve holds
# its title beat longer for suspense before OPTIMAL lands.
_STAGE_PACING: dict[int, tuple[float, float, float]] = {
    # stage_number -> (intro_seconds, line_reveal_seconds, gap_seconds)
    1: (0.7, 0.9, 0.5),   # Gather — snappy load, short hold
    2: (1.1, 1.7, 0.8),   # Readiness — careful, slowly verifying each dimension
    3: (0.9, 1.4, 0.7),   # Priority — the math, deliberate
    4: (1.0, 1.5, 0.8),   # Eligibility — checking many constraint pairs
    5: (1.6, 1.4, 0.9),   # Solver — big hold before OPTIMAL, breathe on the result
    6: (1.0, 1.4, 0.7),   # Capacity — moderate
    7: (0.7, 1.1, 0.4),   # Hand-off — brisk closing
}


def _stage_pacing(title: str) -> tuple[float, float, float]:
    """Return (intro, line_reveal, gap) seconds for the stage, by its number."""
    import re as _re
    m = _re.match(r"^(\d+)\s*·", title)
    if not m:
        return (_STAGE_INTRO_SECONDS, _LINE_REVEAL_SECONDS, _STAGE_GAP_SECONDS)
    return _STAGE_PACING.get(int(m.group(1)), (_STAGE_INTRO_SECONDS, _LINE_REVEAL_SECONDS, _STAGE_GAP_SECONDS))
_ENGINE_SESSION_KEYS = (
    "engine_run_complete", "engine_run_narration", "engine_run_result",
)


@dataclass(frozen=True)
class NarrationBeat:
    """One skimmable reasoning stage, containing only receipt-derived lines."""

    title: str
    lines: tuple[str, ...]
    caption: str = ""


def _format_readiness(receipt: object) -> tuple[str, ...]:
    dimensions = receipt.dimensions
    supported = sum(d.state == "SUPPORTED" for d in dimensions)
    citations = ", ".join(
        f"`{dimension.dimension_id}` → "
        + "/".join(f"`{citation_id}`" for citation_id in dimension.citation_ids)
        for dimension in dimensions
    )
    lines = [copy.RUN_READINESS_TEMPLATE.format(
        deal_id=receipt.deal_source_id,
        supported_count=supported,
        dimension_count=len(dimensions),
        required_count=len(receipt.required_dimension_ids),
        citations=citations,
    )]
    transcript_dimensions = tuple(
        dimension.dimension_id
        for dimension in dimensions
        if "TRANSCRIPT" in dimension.provenance
    )
    if transcript_dimensions:
        lines.append(copy.RUN_TRANSCRIPT_BOUNDARY_TEMPLATE.format(
            deal_id=receipt.deal_source_id,
            dimensions="`, `".join(transcript_dimensions),
        ))
    return tuple(lines)


def _format_priority(receipt: object) -> str:
    formula = " + ".join(
        f"`{feature.feature_id}` {feature.feature_bp} bp × {feature.weight_bp} bp"
        for feature in receipt.features
    )
    return copy.RUN_PRIORITY_TEMPLATE.format(
        deal_id=receipt.deal_source_id,
        formula=formula,
        weighted_total=sum(feature.weighted_numerator for feature in receipt.features),
        priority_bp=receipt.priority_bp,
        rounding=receipt.rounding,
    )


def _format_eligibility(receipt: object) -> str:
    checks = ", ".join(check.check_id for check in receipt.checks)
    utilization = receipt.projected_utilization_bp
    return copy.RUN_ELIGIBILITY_TEMPLATE.format(
        deal_id=receipt.deal_source_id,
        consultant_id=receipt.consultant_source_id,
        check_count=len(receipt.checks),
        checks=checks,
        result="ELIGIBLE" if receipt.eligible else "INELIGIBLE",
        utilization_bp=utilization if utilization is not None else "not available",
    )


def _eligible_summary(problem: object) -> tuple[str, ...]:
    by_deal: dict[str, list[str]] = {}
    roster_ids: set[str] = set()
    for pair in problem.pairs:
        receipt = pair.eligibility
        roster_ids.add(receipt.consultant_source_id)
        if receipt.eligible:
            by_deal.setdefault(receipt.deal_source_id, []).append(receipt.consultant_source_id)
    return tuple(
        copy.RUN_ELIGIBILITY_SUMMARY_TEMPLATE.format(
            deal_id=deal_id,
            eligible_count=len(consultant_ids),
            roster_count=len(roster_ids),
            eligible_ids=", ".join(f"`{item}`" for item in sorted(consultant_ids)),
        )
        for deal_id, consultant_ids in sorted(by_deal.items())
    )


def _format_solver(problem: object, receipt: object, recommendation: object) -> tuple[str, ...]:
    eligible_pairs = sum(pair.eligibility.eligible for pair in problem.pairs)
    objectives = ", ".join(
        f"`{phase.phase}` {phase.objective_value}" for phase in receipt.phases
    )
    lines = list(_eligible_summary(problem))
    lines.append(copy.RUN_SOLVER_TEMPLATE.format(
        engine=receipt.engine,
        deal_count=len(problem.deals),
        eligible_pair_count=eligible_pairs,
        status=receipt.status,
        objectives=objectives,
    ))
    assignment_by_deal = {item.deal_source_id: item for item in receipt.assignments}
    for deal in recommendation.deals:
        assignment = assignment_by_deal[deal.deal_source_id]
        alternatives = ", ".join(
            f"`{alternative.consultant_source_id}` {alternative.disposition} "
            f"(priority Δ {alternative.serviced_priority_delta}, "
            f"match Δ {alternative.portfolio_match_delta})"
            for alternative in deal.rejected_eligible_alternatives
        ) or "none"
        lines.append(copy.RUN_ASSIGNMENT_TEMPLATE.format(
            deal_id=assignment.deal_source_id,
            consultant_id=assignment.consultant_source_id,
            priority_bp=assignment.priority_bp,
            fit_bp=assignment.fit_bp,
            alternatives=alternatives,
        ))
    return tuple(lines)


def _position(value: int) -> str:
    return f"surplus {value} units" if value >= 0 else f"deficit {abs(value)} units"


def _format_scenario(comparison: object) -> tuple[str, ...]:
    lines = [copy.RUN_SCENARIO_CHANGE_TEMPLATE.format(
        deal_id=change.deal_source_id,
        base_units=change.base_effort_units,
        scenario_units=change.scenario_effort_units,
        multiplier=change.multiplier,
    ) for change in comparison.changes]
    scenario_by_key = {
        (cell.region_id, cell.skill_id, cell.week_bucket): cell
        for cell in comparison.scenario_cells
    }
    for base in comparison.base_cells:
        scenario = scenario_by_key[(base.region_id, base.skill_id, base.week_bucket)]
        if base.surplus_deficit_units == scenario.surplus_deficit_units:
            continue
        lines.append(copy.RUN_SCENARIO_CELL_TEMPLATE.format(
            week=base.week_bucket,
            skill_id=base.skill_id,
            base_position=_position(base.surplus_deficit_units),
            scenario_position=_position(scenario.surplus_deficit_units),
            supply_units=scenario.eligible_supply_units,
        ))
    lines.append(copy.RUN_SCENARIO_LABEL_TEMPLATE.format(label=comparison.label))
    return tuple(lines)


def _format_done(demo_run: DemoRun) -> tuple[str, ...]:
    recommendation = demo_run.assignment_recommendation
    summary = demo_run.export_bundle.run_proof_summary
    execution_modes = sorted({
        proof.execution_mode.value
        for proof in demo_run.export_bundle.source_proof_by_instance.values()
    })
    return (
        copy.RUN_DONE_TEMPLATE.format(
            assignment_status=recommendation.assignment_status,
            solver_status=recommendation.solver_status,
            external_writes_attempted=recommendation.external_writes_attempted,
        ),
        copy.RUN_PROOF_TEMPLATE.format(
            execution_modes=", ".join(execution_modes),
            implementation_proof=summary.implementation_proof.value,
            live_validation_proof=summary.live_validation_proof.value,
            derivation=summary.derivation,
        ),
    )


def _fixture_line(deals: Iterable[object], consultants: Iterable[object]) -> str:
    deals = tuple(deals)
    consultants = tuple(consultants)
    conversation_count = sum(len(deal.conversation_ids) for deal in deals)
    return copy.RUN_FIXTURE_TEMPLATE.format(
        deal_count=len(deals),
        deal_ids=", ".join(f"`{deal.deal_source_id}`" for deal in deals),
        consultant_count=len(consultants),
        consultant_ids=", ".join(
            f"`{consultant.consultant_source_id}`" for consultant in consultants
        ),
        conversation_count=conversation_count,
    )


def _event_beat(event: DemoPipelineEvent) -> NarrationBeat:
    if event.stage == "fixtures":
        return NarrationBeat(copy.RUN_BEAT_FIXTURES, (_fixture_line(*event.artifacts),), copy.RUN_BEAT_FIXTURES_CAPTION)
    if event.stage == "readiness":
        return NarrationBeat(copy.RUN_BEAT_READINESS, _format_readiness(event.artifacts[0]), copy.RUN_BEAT_READINESS_CAPTION)
    if event.stage == "priority":
        return NarrationBeat(copy.RUN_BEAT_PRIORITY, (_format_priority(event.artifacts[0]),), copy.RUN_BEAT_PRIORITY_CAPTION)
    if event.stage == "eligibility":
        return NarrationBeat(copy.RUN_BEAT_ELIGIBILITY, (_format_eligibility(event.artifacts[0]),), copy.RUN_BEAT_ELIGIBILITY_CAPTION)
    if event.stage == "solver":
        return NarrationBeat(copy.RUN_BEAT_SOLVER, _format_solver(*event.artifacts), copy.RUN_BEAT_SOLVER_CAPTION)
    if event.stage == "scenario":
        return NarrationBeat(copy.RUN_BEAT_CAPACITY, _format_scenario(event.artifacts[0]), copy.RUN_BEAT_CAPACITY_CAPTION)
    return NarrationBeat(copy.RUN_BEAT_DONE, _format_done(event.artifacts[0]), copy.RUN_BEAT_DONE_CAPTION)


def build_run_narration(demo_run: DemoRun) -> tuple[NarrationBeat, ...]:
    """Build the persistent narration exclusively from a completed DemoRun."""
    deal_ids = [receipt.deal_source_id for receipt in demo_run.priority_queue]
    fixture_line = copy.RUN_FIXTURE_TEMPLATE.format(
        deal_count=len(deal_ids),
        deal_ids=", ".join(f"`{item}`" for item in deal_ids),
        consultant_count=len(demo_run.roster),
        consultant_ids=", ".join(f"`{item.consultant_source_id}`" for item in demo_run.roster),
        conversation_count=int(demo_run.conversation_attachment is not None),
    )
    readiness_lines = tuple(
        line
        for deal_id in sorted(demo_run.readiness_by_deal)
        for line in _format_readiness(demo_run.readiness_by_deal[deal_id])
    )
    priority_lines = tuple(_format_priority(item) for item in demo_run.priority_queue)

    eligibility_lines: list[str] = []
    recommendation = demo_run.assignment_recommendation
    for deal in recommendation.deals:
        proofs = [
            (deal.recommended_consultant_source_id, deal.recommended_hard_constraint_proof),
            *((item.consultant_source_id, item.hard_constraint_proof)
              for item in deal.rejected_eligible_alternatives),
            *((item.consultant_source_id, item.hard_constraint_proof)
              for item in deal.ineligible_alternatives),
        ]
        eligible_ids = [consultant_id for consultant_id, proof in proofs if proof.eligible]
        checks = ", ".join(check.check_id for check in proofs[0][1].checks)
        eligibility_lines.append(copy.RUN_ELIGIBILITY_SUMMARY_TEMPLATE.format(
            deal_id=deal.deal_source_id,
            eligible_count=len(eligible_ids),
            roster_count=len(proofs),
            eligible_ids=", ".join(f"`{item}`" for item in sorted(eligible_ids)),
        ))
        eligibility_lines.append(copy.RUN_CONSTRAINTS_TEMPLATE.format(
            check_count=len(proofs[0][1].checks),
            checks=checks,
        ))

    scenario_lines = (
        _format_scenario(demo_run.scenario_comparison)
        if demo_run.scenario_comparison is not None else ()
    )
    return (
        NarrationBeat(copy.RUN_BEAT_FIXTURES, (fixture_line,), copy.RUN_BEAT_FIXTURES_CAPTION),
        NarrationBeat(copy.RUN_BEAT_READINESS, readiness_lines, copy.RUN_BEAT_READINESS_CAPTION),
        NarrationBeat(copy.RUN_BEAT_PRIORITY, priority_lines, copy.RUN_BEAT_PRIORITY_CAPTION),
        NarrationBeat(copy.RUN_BEAT_ELIGIBILITY, tuple(eligibility_lines), copy.RUN_BEAT_ELIGIBILITY_CAPTION),
        NarrationBeat(
            copy.RUN_BEAT_SOLVER,
            _format_solver_from_run(demo_run),
            copy.RUN_BEAT_SOLVER_CAPTION,
        ),
        NarrationBeat(copy.RUN_BEAT_CAPACITY, scenario_lines, copy.RUN_BEAT_CAPACITY_CAPTION),
        NarrationBeat(copy.RUN_BEAT_DONE, _format_done(demo_run), copy.RUN_BEAT_DONE_CAPTION),
    )


def _format_solver_from_run(demo_run: DemoRun) -> tuple[str, ...]:
    receipt = demo_run.solver_receipt
    recommendation = demo_run.assignment_recommendation
    eligible_pair_count = sum(
        1 + len(deal.rejected_eligible_alternatives)
        for deal in recommendation.deals
    )
    objectives = ", ".join(
        f"`{phase.phase}` {phase.objective_value}" for phase in receipt.phases
    )
    lines = [copy.RUN_SOLVER_TEMPLATE.format(
        engine=receipt.engine,
        deal_count=len(receipt.assignments),
        eligible_pair_count=eligible_pair_count,
        status=receipt.status,
        objectives=objectives,
    )]
    assignment_by_deal = {item.deal_source_id: item for item in receipt.assignments}
    for deal in recommendation.deals:
        assignment = assignment_by_deal[deal.deal_source_id]
        alternatives = ", ".join(
            f"`{item.consultant_source_id}` {item.disposition} "
            f"(priority Δ {item.serviced_priority_delta}, match Δ {item.portfolio_match_delta})"
            for item in deal.rejected_eligible_alternatives
        ) or "none"
        lines.append(copy.RUN_ASSIGNMENT_TEMPLATE.format(
            deal_id=assignment.deal_source_id,
            consultant_id=assignment.consultant_source_id,
            priority_bp=assignment.priority_bp,
            fit_bp=assignment.fit_bp,
            alternatives=alternatives,
        ))
    return tuple(lines)


def _render_beat_markdown(beat: NarrationBeat) -> str:
    """Render one beat as a single atomic markdown block (title + caption + lines)."""
    parts = [f"### {beat.title}"]
    if beat.caption:
        parts.append(f"*{beat.caption}*")
    parts.extend(beat.lines)
    return "\n\n".join(parts)


def _render_beat(beat: NarrationBeat, *, show_title: bool) -> None:
    # Atomic single-markdown write so nothing lingers between renders.
    st.markdown(_render_beat_markdown(beat))


def clear_engine_run_state() -> None:
    """Purge app-controlled live-run state during the existing local reset."""
    for key in _ENGINE_SESSION_KEYS:
        st.session_state.pop(key, None)


def _streamed_run(demo_run: DemoRun) -> DemoRun:
    """Execute the real pipeline with a pinned live view + final list view.

    UX (Jay's spec):
    - The progress bar + 'currently on stage N' header are PINNED at the top —
      they never get pushed below the fold by accumulated output.
    - While a stage runs, ONLY that stage's reasoning is shown in the live pane.
      Each reveal re-renders the current stage's accumulated lines (a 'typing'
      effect), and a NEW stage clears the pane so prior stages do NOT stack
      above and bury the indicator. The active region stays in view throughout.
    - When the whole run completes, the live pane is replaced with the FULL
      list view — every stage's reasoning, top to bottom — for review.
    No value is faked — every line is read from the real receipt the pipeline
    just produced (via the observer callback).
    """
    # Pinned header: progress bar + current stage label. Rendered first, so it
    # sits above the live pane and never moves as stages update below it.
    header_progress = st.progress(0.0, text=copy.RUN_START)
    header_status = st.status(copy.RUN_STATUS_EXECUTING, expanded=False)

    # Live pane: a single clearable placeholder. We clear-and-redraw it on each
    # revealed line so the current stage stays in view; a NEW stage starts fresh.
    live_slot = st.empty()

    produced_beats: list[NarrationBeat] = []
    seen_titles: set[str] = set()
    total_stages_estimate = 7  # fixed 7-stage flow

    # Current-stage accumulator (lines stay across continuation beats for the
    # same stage; reset when a new stage begins).
    cur_title: list[str] = []      # one-element holder (mutable for closure)
    cur_caption: list[str] = []   # one-element holder for the stage's explainer
    cur_lines: list[str] = []

    def _render_live() -> None:
        if not cur_title:
            live_slot.empty()
            return
        # Single atomic markdown write: the placeholder fully replaces its
        # prior content on each call, so prior-stage lines never linger as the
        # next stage populates (the previous 'piece-by-piece replacement'
        # glitch is gone).
        parts = [f"### {cur_title[0]}"]
        if cur_caption[0]:
            parts.append(f"*{cur_caption[0]}*")
        parts.extend(cur_lines)
        live_slot.markdown("\n\n".join(parts))

    def narrate(event: DemoPipelineEvent) -> None:
        beat = _event_beat(event)
        is_new_stage = beat.title not in seen_titles
        if is_new_stage:
            seen_titles.add(beat.title)
            intro_s, _, _ = _stage_pacing(beat.title)
            cur_title.clear()
            cur_title.append(beat.title)
            cur_caption.clear()
            cur_caption.append(beat.caption)
            cur_lines.clear()
            header_progress.progress(
                min(len(seen_titles) / total_stages_estimate, 1.0),
                text=f"{beat.title} — stage {len(seen_titles)} of {total_stages_estimate}",
            )
            _render_live()  # show the new stage's title + caption first, no prior lines
            time.sleep(intro_s)
        # Reveal each line with a pause; redraw the current stage so far.
        _, line_reveal_s, _ = _stage_pacing(beat.title)
        for line in beat.lines:
            cur_lines.append(line)
            _render_live()
            time.sleep(line_reveal_s)
        produced_beats.append(beat)
        if is_new_stage:
            _, _, gap_s = _stage_pacing(beat.title)
            time.sleep(gap_s)

    completed_run = run_demo_pipeline(demo_run.lane, observer=narrate)
    header_progress.progress(1.0, text=copy.RUN_STATUS_COMPLETE)
    header_status.update(label=copy.RUN_STATUS_COMPLETE, state="complete", expanded=False)

    # Swap the live pane for the FULL list view (every stage, top to bottom).
    live_slot.empty()
    with live_slot.container():
        st.success(copy.RUN_STATUS_COMPLETE)
        st.caption(copy.RUN_LIST_VIEW_HELP)
        for beat in produced_beats:
            _render_beat(beat, show_title=True)

    st.session_state["engine_run_complete"] = True
    st.session_state["engine_run_result"] = completed_run
    st.session_state["engine_run_narration"] = tuple(produced_beats)
    return completed_run


def render_engine_run(demo_run: DemoRun) -> DemoRun:
    """Render execution, returning the exact run the walkthrough should study."""
    st.subheader(copy.RUN_HEADING)
    st.caption(copy.RUN_HELP)
    if st.button(copy.BTN_RUN_ENGINE, key="run_engine", type="primary"):
        completed_run = _streamed_run(demo_run)
    elif st.session_state.get("engine_run_complete"):
        with st.status(copy.RUN_STATUS_PREVIOUS, state="complete", expanded=False):
            for beat in st.session_state["engine_run_narration"]:
                _render_beat(beat, show_title=True)
    return st.session_state.get("engine_run_result", demo_run)
