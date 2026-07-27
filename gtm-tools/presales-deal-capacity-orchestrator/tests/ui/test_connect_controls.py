from __future__ import annotations

from orchestrator.ui import copy
from orchestrator.ui.state import CONNECT_TARGETS


def _reach_connect_setup(app):
    app.button(key="connect_path").click().run()
    app.checkbox(key="attest").check().run()
    app.button(key="attest_continue").click().run()
    return app


def test_connect_targets_are_the_four_scoped_sources() -> None:
    assert CONNECT_TARGETS == ("Salesforce", "ClickUp", "Fathom", "Gong")


def test_connect_buttons_are_neutral_ordinary_labels(app) -> None:
    _reach_connect_setup(app)
    labels = [b.label for b in app.button]
    for expected in (
        copy.BTN_CONNECT_SALESFORCE,
        copy.BTN_CONNECT_CLICKUP,
        copy.BTN_CONNECT_FATHOM,
        copy.BTN_CONNECT_GONG,
    ):
        assert expected in labels
        # No scary/alarming words on the button itself.
        low = expected.lower()
        for scary in ("warning", "danger", "risk", "caution", "unsafe", "not validated"):
            assert scary not in low


def test_live_validation_status_is_a_small_neutral_line_not_on_the_button(app) -> None:
    _reach_connect_setup(app)
    captions = [m.value for m in app.caption] if hasattr(app, "caption") else []
    joined = " ".join(m.value for m in app.markdown)
    assert copy.LIVE_VALIDATION_STATUS == "Live validation: Not yet validated"
    assert copy.LIVE_VALIDATION_STATUS in joined or copy.LIVE_VALIDATION_STATUS in " ".join(captions)


def test_file_import_is_presented_as_the_contract_validated_fallback(app) -> None:
    _reach_connect_setup(app)
    joined = " ".join(m.value for m in app.markdown)
    joined += " " + " ".join(m.value for m in app.caption)
    assert copy.CONNECT_FALLBACK in joined
    assert "contract-validated fallback" in copy.CONNECT_FALLBACK
