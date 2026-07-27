from __future__ import annotations

from pathlib import Path

from orchestrator.ui import copy

UI_DIR = Path(__file__).resolve().parents[2] / "src" / "orchestrator" / "ui"
# Files whose authored wording must never overclaim. copy.py is excluded from the
# raw-source scan because it *defines* the forbidden-term list; its string values
# are scanned separately below.
AUTHORED_SOURCE_FILES = (
    UI_DIR / "app.py",
    UI_DIR / "state.py",
    UI_DIR / "theme.py",
    UI_DIR / "views" / "render.py",
    UI_DIR / "views" / "walkthrough.py",
    UI_DIR / "views" / "engine_run.py",
)


def test_authored_copy_constants_never_overclaim() -> None:
    offenders: dict[str, tuple[str, ...]] = {}
    for name, value in copy.all_authored_copy().items():
        hits = copy.scan_text(value)
        if hits:
            offenders[name] = hits
    assert offenders == {}, f"overclaim wording in authored copy: {offenders}"


def test_button_labels_have_no_write_or_action_verbs() -> None:
    offenders: dict[str, tuple[str, ...]] = {}
    for name, label in copy.all_button_labels().items():
        hits = copy.scan_button_label(label)
        if hits:
            offenders[name] = hits
    assert offenders == {}, f"action verbs on buttons: {offenders}"


def test_ui_source_files_contain_no_overclaim_phrases() -> None:
    offenders: dict[str, tuple[str, ...]] = {}
    for path in AUTHORED_SOURCE_FILES:
        text = path.read_text()
        hits = copy.scan_text(text)
        if hits:
            offenders[str(path)] = hits
    assert offenders == {}, f"overclaim wording in UI source: {offenders}"


def test_status_line_uses_exact_proof_qualified_vocabulary() -> None:
    # The connector status line is exactly the plan's neutral wording.
    assert copy.LIVE_VALIDATION_STATUS == "Live validation: Not yet validated"
    # Production readiness stays NOT_ASSESSED.
    assert "NOT_ASSESSED" in copy.PRODUCTION_READINESS_LINE
    # No forbidden phrase hides in the neutral status/fallback copy.
    assert copy.scan_text(copy.LIVE_VALIDATION_STATUS) == ()
    assert copy.scan_text(copy.CONNECT_FALLBACK) == ()


def test_rendered_demo_status_tokens_are_allowed_vocabulary(app) -> None:
    app.button(key="run_demo").click().run()
    app.button(key="skip_to_results").click().run()
    joined = " ".join(m.value for m in app.markdown)
    # The forbidden marketing claims never appear in rendered proof/status text.
    for term in ("live validated", "production-ready", "works with", "recommended by"):
        assert term not in joined.lower()
    # The exact proof vocabulary is present.
    assert "NOT_LIVE_VALIDATED" in joined
    assert "FULLY_IMPLEMENTED_CONTRACT_TESTED" in joined
