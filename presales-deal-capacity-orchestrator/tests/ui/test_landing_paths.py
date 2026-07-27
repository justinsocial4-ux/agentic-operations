from __future__ import annotations

from orchestrator.ui import copy
from orchestrator.ui.state import LANDING_PATHS, FlowState, LandingPath, Stage


def test_three_landing_paths_are_the_only_entry_points() -> None:
    assert LANDING_PATHS == (
        LandingPath.FICTIONAL_DEMO,
        LandingPath.IMPORT,
        LandingPath.CONNECT,
    )


def test_landing_page_renders_three_equal_choices(app) -> None:
    labels = [b.label for b in app.button]
    assert copy.BTN_RUN_DEMO in labels
    assert copy.BTN_IMPORT in labels
    assert copy.BTN_CONNECT in labels


def test_fictional_demo_is_zero_credential_and_skips_authority(app) -> None:
    app.button(key="run_demo").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.path is LandingPath.FICTIONAL_DEMO
    # Demo opens the guided walkthrough by default (still zero-credential).
    assert flow.stage is Stage.WALKTHROUGH
    assert flow.authority_attested is False  # demo requires no attestation
    assert list(app.exception) == []


def test_fictional_demo_can_skip_to_full_results(app) -> None:
    app.button(key="run_demo").click().run()
    app.button(key="skip_to_results").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.stage is Stage.RESULTS
    assert list(app.exception) == []


def test_import_path_requires_authority_first(app) -> None:
    app.button(key="import_path").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.path is LandingPath.IMPORT
    assert flow.stage is Stage.AUTHORITY
    assert any(h.value == copy.AUTHORITY_HEADING for h in app.header)


def test_connect_path_requires_authority_first(app) -> None:
    app.button(key="connect_path").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.path is LandingPath.CONNECT
    assert flow.stage is Stage.AUTHORITY
