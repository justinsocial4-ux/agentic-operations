from __future__ import annotations

import pytest

from orchestrator.ui import copy
from orchestrator.ui.state import DISPOSITION_KINDS, FlowState, ManagerDisposition


def _run_demo(app):
    # Demo defaults to the guided walkthrough; skip to the full results view.
    app.button(key="run_demo").click().run()
    app.button(key="skip_to_results").click().run()
    return app


def test_disposition_kinds_are_accept_override_reject_defer() -> None:
    assert set(DISPOSITION_KINDS) == {"ACCEPT", "OVERRIDE", "REJECT", "DEFER"}


def test_manager_can_record_each_disposition(app) -> None:
    _run_demo(app)
    flow: FlowState = app.session_state["flow"]
    deal_ids = [p.deal_source_id for p in __import__(
        "orchestrator.ui.demo", fromlist=["build_demo_run"]
    ).build_demo_run().priority_queue]
    first = deal_ids[0]
    app.button(key=f"accept_{first}").click().run()
    flow = app.session_state["flow"]
    assert flow.dispositions[first].kind == "ACCEPT"
    app.button(key=f"reject_{first}").click().run()
    assert app.session_state["flow"].dispositions[first].kind == "REJECT"


def test_override_records_outside_model_when_flagged() -> None:
    flow = FlowState()
    flow.record_disposition(ManagerDisposition(
        "deal-x", "OVERRIDE", override_consultant_source_id="c-1", outside_model_review=True,
    ))
    assert flow.dispositions["deal-x"].outside_model_review is True


def test_unknown_disposition_is_rejected() -> None:
    flow = FlowState()
    with pytest.raises(ValueError):
        flow.record_disposition(ManagerDisposition("deal-x", "STAFF"))


def test_export_button_is_inert_and_says_create_recommendation_export(app) -> None:
    _run_demo(app)
    labels = [b.label for b in app.button]
    assert copy.BTN_EXPORT in labels
    assert copy.BTN_EXPORT == "Create recommendation export"
    app.button(key="export").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.export_created is True
    # Export note affirms no write / mutation.
    assert "no CRM write" in copy.EXPORT_NOTE


def test_export_bundle_is_recommendation_only_no_writes() -> None:
    from orchestrator.ui.demo import build_demo_run

    bundle = build_demo_run().export_bundle
    assert bundle.assignment_status == "RECOMMENDATION_ONLY"
    assert bundle.external_writes_attempted is False
    assert bundle.execution_authorized is False
    assert bundle.production_ready is False


def test_reset_clears_local_flow_state(app) -> None:
    _run_demo(app)
    app.button(key="reset").click().run()
    flow: FlowState = app.session_state["flow"]
    assert flow.stage.value == "LANDING"
    assert flow.dispositions == {}
    assert flow.export_created is False
