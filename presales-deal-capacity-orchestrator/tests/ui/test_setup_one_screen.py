from __future__ import annotations

from datetime import datetime, timezone

from orchestrator.contracts.enums import LaneV1, SourceModeV1
from orchestrator.contracts.setup import (
    ADVANCED_POLICY_FIELDS_BY_LANE,
    CORE_POLICY_FIELDS_BY_LANE,
    REQUIRED_AUTHORITY_ROLES_BY_LANE,
    SourceSlotSelectionV1,
)
from orchestrator.setup_gate import build_run_setup_acceptance
from orchestrator.ui import copy
from orchestrator.ui.demo import demo_policy
from orchestrator.ui.state import SELECTABLE_LANES, FlowState, Stage

NOW = datetime(2026, 8, 3, tzinfo=timezone.utc)


def _reach_setup(app):
    app.button(key="import_path").click().run()
    app.checkbox(key="attest").check().run()
    app.button(key="attest_continue").click().run()
    return app


def test_setup_is_a_single_screen_with_three_lanes(app) -> None:
    _reach_setup(app)
    assert any(h.value == copy.SETUP_HEADING for h in app.header)
    assert app.radio(key="lane").options == [
        copy.LANE_DEAL, copy.LANE_ASSIGNMENT, copy.LANE_CAPACITY,
    ]
    # No second setup screen: there is one radio and two confirmation actions only.
    assert len(app.radio) == 1


def test_setup_uses_at_most_two_confirmation_actions_including_authority(app) -> None:
    _reach_setup(app)
    app.radio(key="lane").set_value(copy.LANE_ASSIGNMENT).run()
    app.button(key="confirm_core").click().run()
    app.button(key="confirm_advanced").click().run()
    flow: FlowState = app.session_state["flow"]
    # One core-group action (folds authority) + one Advanced action == 2 total.
    assert flow.setup_actions_used == 2
    assert flow.setup_complete is True
    app.button(key="to_mapping").click().run()
    assert flow.stage is Stage.MAPPING


def test_fixed_horizon_is_confirm_only_and_has_no_editor(app) -> None:
    _reach_setup(app)
    # The horizon appears as an info line, never as a number/select editor.
    assert any("4 weeks" in i.value for i in app.info)
    assert len(app.number_input) == 0
    # Nothing in the setup screen lets the user change the horizon value.
    assert copy.HORIZON_LINE == "Planning horizon: 4 weeks (fixed in v1; confirm-only, not editable)"


def test_no_per_field_grilling_only_two_confirm_buttons_gate_the_run(app) -> None:
    _reach_setup(app)
    confirm_keys = {"confirm_core", "confirm_advanced"}
    gating = [b for b in app.button if b.proto.id and (b.key in confirm_keys)]
    assert len(gating) == 2  # exactly the two group confirmations, no per-field buttons


def _slots(lane: LaneV1) -> tuple[SourceSlotSelectionV1, ...]:
    roles = sorted(REQUIRED_AUTHORITY_ROLES_BY_LANE[lane])
    return tuple(SourceSlotSelectionV1(
        source_slot_id=f"slot-{role.lower()}",
        authority_role=role,
        adapter_id="fictional-adapter",
        source_mode=SourceModeV1.FICTIONAL,
    ) for role in roles)


def test_each_lane_builds_a_two_action_acceptance_with_fixed_horizon() -> None:
    policy = demo_policy()
    for lane in SELECTABLE_LANES:
        receipt = build_run_setup_acceptance(
            run_id="run-ui-setup",
            lane=lane,
            actor="kevin",
            accepted_at=NOW,
            policy=policy,
            source_slots=_slots(lane),
            authority_and_core_confirmed=True,
            advanced_confirmed=True,
        )
        assert len(receipt.actions) == 2
        assert receipt.second_setup_screen is False
        assert policy.horizon_weeks == 4
        assert {a.field_name for a in receipt.core_field_acceptances} == CORE_POLICY_FIELDS_BY_LANE[lane]
        assert {a.field_name for a in receipt.advanced_field_acceptances} == ADVANCED_POLICY_FIELDS_BY_LANE[lane]
        # Core acceptances are DIRECT (one action), Advanced are GROUPED (one action).
        assert all(a.acceptance == "DIRECT" for a in receipt.core_field_acceptances)
        assert all(a.acceptance == "GROUPED" for a in receipt.advanced_field_acceptances)
        # horizon_weeks is a confirm-only core field, present in the inventory.
        assert "horizon_weeks" in {a.field_name for a in receipt.core_field_acceptances}
