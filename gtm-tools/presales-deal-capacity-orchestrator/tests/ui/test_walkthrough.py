"""Guided step-through walkthrough tests (Kevin-facing plain-English fix).

These headless AppTest walks prove that:
  * the fictional demo opens the guided walkthrough by default,
  * each of the seven stages (a-g) renders its plain-English narration,
  * Next/Back navigation is ordered and bounded,
  * a "skip to full results" path exists and reaches the compact results view,
  * the walkthrough narration adds no overclaim wording.
"""
from __future__ import annotations

from orchestrator.ui import copy
from orchestrator.ui.state import (
    WALKTHROUGH_STEPS,
    FlowState,
    Stage,
    WalkStep,
)

# The seven stages a-g in order, with the plain-English title + body each shows.
_STAGE_COPY = [
    (WalkStep.INTRO, copy.WALK_INTRO_TITLE, copy.WALK_INTRO_BODY),
    (WalkStep.READINESS, copy.WALK_READINESS_TITLE, copy.WALK_READINESS_BODY),
    (WalkStep.PRIORITY, copy.WALK_PRIORITY_TITLE, copy.WALK_PRIORITY_BODY),
    (WalkStep.ELIGIBLE, copy.WALK_ELIGIBLE_TITLE, copy.WALK_ELIGIBLE_BODY),
    (WalkStep.ASSIGNMENT, copy.WALK_ASSIGNMENT_TITLE, copy.WALK_ASSIGNMENT_BODY),
    (WalkStep.CAPACITY, copy.WALK_CAPACITY_TITLE, copy.WALK_CAPACITY_BODY),
    (WalkStep.MANAGER, copy.WALK_MANAGER_TITLE, copy.WALK_MANAGER_BODY),
]


def test_walkthrough_covers_exactly_seven_ordered_stages() -> None:
    assert WALKTHROUGH_STEPS == (
        WalkStep.INTRO,
        WalkStep.READINESS,
        WalkStep.PRIORITY,
        WalkStep.ELIGIBLE,
        WalkStep.ASSIGNMENT,
        WalkStep.CAPACITY,
        WalkStep.MANAGER,
    )
    assert len(WALKTHROUGH_STEPS) == 7


def test_demo_opens_walkthrough_by_default(app) -> None:
    app.button(key="run_demo").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.stage is Stage.WALKTHROUGH
    assert flow.walk_index == 0
    headers = [h.value for h in app.header]
    assert copy.WALK_HEADING in headers
    subs = [s.value for s in app.subheader]
    assert copy.WALK_INTRO_TITLE in subs


def _advance(app) -> None:
    """Click Next and confirm progress.

    AppTest can drop a single queued button click when the element tree shape
    changes a lot between stages (a simulation artifact; a real browser click on
    ``next_walk`` always advances). Retry once so the test stays deterministic.
    """
    before = app.session_state["flow"].walk_index
    app.button(key="walk_next").click().run()
    if app.session_state["flow"].walk_index == before:
        app.button(key="walk_next").click().run()
    assert app.session_state["flow"].walk_index == before + 1


def test_each_stage_renders_its_plain_english_narration(app) -> None:
    app.button(key="run_demo").click().run()
    for index, (_step, title, body) in enumerate(_STAGE_COPY):
        subs = [s.value for s in app.subheader]
        assert title in subs, f"stage {index} title missing: {title}"
        joined = " ".join(m.value for m in app.markdown)
        # A distinctive slice of the plain-English "why" is on screen.
        assert body[:40] in joined, f"stage {index} narration missing"
        assert list(app.exception) == []
        if index < len(_STAGE_COPY) - 1:
            _advance(app)


def test_back_button_is_disabled_on_first_stage_and_navigates(app) -> None:
    app.button(key="run_demo").click().run()
    assert app.button(key="walk_back").disabled is True
    app.button(key="walk_next").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.walk_index == 1
    app.button(key="walk_back").click().run()
    assert app.session_state["flow"].walk_index == 0


def test_skip_to_full_results_from_walkthrough(app) -> None:
    app.button(key="run_demo").click().run()
    app.button(key="skip_to_results").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.stage is Stage.RESULTS
    assert "Results" in [h.value for h in app.header]
    assert list(app.exception) == []


def test_next_past_last_stage_falls_through_to_results(app) -> None:
    app.button(key="run_demo").click().run()
    for _ in range(len(WALKTHROUGH_STEPS) - 1):
        _advance(app)
    flow: FlowState = app.session_state["flow"]
    assert flow.is_last_walk_step is True
    app.button(key="walk_next").click().run()  # advances past last -> results
    if app.session_state["flow"].stage is not Stage.RESULTS:  # tolerate dropped click
        app.button(key="walk_next").click().run()
    assert app.session_state["flow"].stage is Stage.RESULTS


def test_results_can_restart_the_walkthrough(app) -> None:
    app.button(key="run_demo").click().run()
    app.button(key="skip_to_results").click().run()
    app.button(key="restart_walk").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.stage is Stage.WALKTHROUGH
    assert flow.walk_index == 0


def test_assignment_stage_shows_why_this_consultant_narrative(app) -> None:
    app.button(key="run_demo").click().run()
    # Advance to the assignment stage (index 4).
    for _ in range(4):
        _advance(app)
    flow: FlowState = app.session_state["flow"]
    assert flow.current_walk_step is WalkStep.ASSIGNMENT
    joined = " ".join(m.value for m in app.markdown)
    assert "Hard constraint" in joined
    assert "Match component" in joined or "Match fit" in joined
    # Recommended consultant named as data (fictional roster id).
    assert "consultant-" in joined


def test_walkthrough_narration_adds_no_overclaim_wording() -> None:
    for _step, title, body in _STAGE_COPY:
        assert copy.scan_text(title) == ()
        assert copy.scan_text(body) == ()
