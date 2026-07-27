"""Custom Streamlit theming tests (adaptive light/dark, badges).

The polish defers to Streamlit's NATIVE light/dark theming via runtime CSS
variables (``--background-color``, ``--secondary-background-color``,
``--text-color``, ``--primary-color``), so it is coherent in BOTH themes. The
earlier custom dark-mode toggle clashed with Streamlit's startup theme base
(which cannot be flipped per-session) and was removed.

Proof/status badges reuse the EXACT proof tokens — no overclaim wording (scanned
by the terminology suite).
"""
from __future__ import annotations

from orchestrator.ui import copy, theme


def test_badges_map_proof_vocabulary_to_neutral_chips() -> None:
    # Badge text IS the exact proof token; chip styling is theme-adaptive.
    for token in ("RECOMMENDATION_ONLY", "NOT_LIVE_VALIDATED", "NOT_ASSESSED", "OPTIMAL"):
        html = theme.badge(token)
        assert token in html
        assert "po-badge" in html
        # Badge text never smuggles a forbidden claim phrase.
        assert copy.scan_text(html) == ()


def test_inject_theme_is_theme_agnostic_and_does_not_clash() -> None:
    # The CSS must work on Streamlit's NATIVE light AND dark surfaces without
    # depending on CSS variables (Streamlit 1.60 does not expose
    # --background-color on the DOM) and must NOT override .stApp's background
    # (that was the dark-mode clash source: dark page + light widgets).
    css = theme._THEME_CSS
    assert "rgba(" in css                      # translucent overlays = theme-agnostic
    assert "color: inherit" in css             # text follows Streamlit's native text color
    for forbidden in ("#ffffff", "#f4f6f9", "#1f2733", "#12161d", "#1b2029"):
        assert forbidden not in css            # no hardcoded light/dark surfaces
    assert ".stApp" not in css                 # no app-background override


def test_inject_theme_and_rail_produce_scoped_css(app) -> None:
    # The demo render path injects theme CSS + progress rail without error.
    app.button(key="run_demo").click().run()
    joined = " ".join(m.value for m in app.markdown)
    assert "po-card" in joined or "po-badge" in joined
    assert list(app.exception) == []
