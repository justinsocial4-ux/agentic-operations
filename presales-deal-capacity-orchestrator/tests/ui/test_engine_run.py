"""Real fictional-pipeline execution and live receipt narration."""
from __future__ import annotations

from orchestrator.ui import copy
from orchestrator.ui.demo import run_demo_pipeline
from orchestrator.ui.state import FlowState, Stage
from orchestrator.ui.views.engine_run import build_run_narration


def test_run_engine_button_exists_on_fictional_demo(app) -> None:
    app.button(key="run_demo").click().run()
    button = app.button(key="run_engine")
    assert button.label == copy.BTN_RUN_ENGINE
    assert button.disabled is False


def test_run_engine_click_surfaces_real_reasoning_and_keeps_walkthrough(app) -> None:
    app.button(key="run_demo").click().run()
    app.button(key="run_engine").click().run()

    assert list(app.exception) == []
    assert any(status.state == "complete" for status in app.status)
    rendered = " ".join(item.value for item in app.markdown)
    for actual_receipt_token in (
        "deal-emea-bravo",
        "citation-business-problem-1",
        "citation-success-criteria-1",
        "9898 bp",
        "8470 bp",
        "REGION, SKILLS, LANGUAGE, TIME_ZONE",
        "OR_TOOLS_CP_SAT",
        "OPTIMAL",
        "18368",
        "7420",
        "consultant-lyra",
        "surplus 50",
        "surplus 44",
        "USER_SELECTED_ASSUMPTION_NOT_A_FORECAST",
        "RECOMMENDATION_ONLY",
        "NOT_LIVE_VALIDATED",
        "Manager decides",
    ):
        assert actual_receipt_token in rendered

    flow: FlowState = app.session_state["flow"]
    assert flow.stage is Stage.WALKTHROUGH
    assert app.button(key="walk_next").label == copy.BTN_WALK_NEXT
    app.button(key="walk_next").click().run()
    assert app.session_state["flow"].walk_index == 1
    assert copy.WALK_READINESS_TITLE in [item.value for item in app.subheader]
    assert "engine_run_result" in app.session_state


def test_two_fresh_engine_runs_are_identical() -> None:
    first_events = []
    second_events = []
    first = run_demo_pipeline(observer=first_events.append)
    second = run_demo_pipeline(observer=second_events.append)

    assert first == second
    assert build_run_narration(first) == build_run_narration(second)
    assert [event.stage for event in first_events] == [event.stage for event in second_events]
    assert [event.stage for event in first_events] == [
        "fixtures",
        "readiness", "priority",
        "readiness", "priority",
        "eligibility", "eligibility", "eligibility", "eligibility",
        "solver", "scenario", "done",
    ]
