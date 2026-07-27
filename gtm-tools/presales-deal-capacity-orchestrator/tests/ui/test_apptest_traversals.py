"""Headless AppTest traversals of the fictional and import paths.

These are the automated stand-in for the manual browser walkthrough required by
the Phase 7 gate; they exercise the same script the browser renders.
"""
from __future__ import annotations

from orchestrator.ui import copy
from orchestrator.ui.state import FlowState, Stage


def test_fictional_demo_full_traversal_renders_every_view(app) -> None:
    # The demo now opens the guided walkthrough by default; skip to full results
    # to exercise the compact one-shot view this test asserts.
    app.button(key="run_demo").click().run()
    app.button(key="skip_to_results").click().run()
    assert list(app.exception) == []
    headers = [h.value for h in app.header]
    subs = [s.value for s in app.subheader]
    assert "Results" in headers
    assert copy.PRIORITY_HEADING in subs
    assert copy.ASSIGNMENT_HEADING in subs
    assert copy.CAPACITY_HEADING in subs
    assert copy.PROOF_HEADING in headers
    assert copy.DISPOSITION_HEADING in headers
    assert copy.EXPORT_HEADING in headers
    assert copy.RESET_HEADING in headers
    # Proof + conservative summary present.
    joined = " ".join(m.value for m in app.markdown)
    assert "WEAKEST_DECISION_BEARING_SOURCE" in joined


def test_import_full_traversal_reaches_results_without_exception(app) -> None:
    app.button(key="import_path").click().run()
    app.checkbox(key="attest").check().run()
    app.button(key="attest_continue").click().run()
    app.radio(key="lane").set_value(copy.LANE_ASSIGNMENT).run()
    app.button(key="confirm_core").click().run()
    app.button(key="confirm_advanced").click().run()
    app.button(key="to_mapping").click().run()
    assert any(h.value == copy.MAPPING_HEADING for h in app.header)
    app.button(key="to_health").click().run()
    assert any(h.value == copy.HEALTH_HEADING for h in app.header)
    app.button(key="to_evidence").click().run()
    assert any(h.value == copy.EVIDENCE_HEADING for h in app.header)
    app.button(key="to_results").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.stage is Stage.RESULTS
    assert list(app.exception) == []
    assert "Results" in [h.value for h in app.header]


def test_import_traversal_blocks_mapping_until_both_confirmations(app) -> None:
    app.button(key="import_path").click().run()
    app.checkbox(key="attest").check().run()
    app.button(key="attest_continue").click().run()
    app.radio(key="lane").set_value(copy.LANE_DEAL).run()
    app.button(key="confirm_core").click().run()
    # Advanced not confirmed yet: continue button is disabled, stage stays SETUP.
    flow: FlowState = app.session_state["flow"]
    assert flow.setup_complete is False
    to_mapping = app.button(key="to_mapping")
    assert to_mapping.disabled is True
