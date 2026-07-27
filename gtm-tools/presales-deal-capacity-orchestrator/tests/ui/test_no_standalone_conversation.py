from __future__ import annotations

from orchestrator.contracts.enums import LaneV1
from orchestrator.ui import copy
from orchestrator.ui.demo import build_demo_run
from orchestrator.ui.state import SELECTABLE_LANES


def test_selectable_lanes_are_exactly_three_and_exclude_conversation() -> None:
    assert SELECTABLE_LANES == (
        LaneV1.DEAL_PRIORITIZATION,
        LaneV1.ASSIGNMENT_RECOMMENDATION,
        LaneV1.CAPACITY_HEATMAP,
    )
    # No conversation lane exists in the enum or the selectable set.
    assert all("CONVERSATION" not in lane.value for lane in SELECTABLE_LANES)


def test_setup_radio_never_offers_a_conversation_lane(app) -> None:
    app.button(key="import_path").click().run()
    app.checkbox(key="attest").check().run()
    app.button(key="attest_continue").click().run()
    options = app.radio(key="lane").options
    assert options == [copy.LANE_DEAL, copy.LANE_ASSIGNMENT, copy.LANE_CAPACITY]
    assert not any("conversation" in o.lower() for o in options)


def test_conversation_evidence_is_additive_only() -> None:
    attachment = build_demo_run().conversation_attachment
    assert attachment is not None
    assert attachment.is_standalone_lane is False
    # It attaches to a specific deal via exact crosswalk, affecting only coverage.
    assert attachment.deal_source_id
    assert attachment.provenance == "TRANSCRIPT"


def test_evidence_view_copy_states_additive_and_never_picks_a_consultant() -> None:
    body = copy.EVIDENCE_BODY.lower()
    assert "additive only" in body
    assert "never a standalone output lane" in body
    assert "never picks or scores a consultant" in body
