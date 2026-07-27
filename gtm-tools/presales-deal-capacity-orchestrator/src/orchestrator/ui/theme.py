"""Custom Streamlit theming + neutral proof/status badges (Phase 7 polish).

This defers to Streamlit's NATIVE light/dark theming for every app and widget
surface by using Streamlit's runtime CSS variables (``--background-color``,
``--secondary-background-color``, ``--text-color``, ``--primary-color``). The
polish is therefore coherent in BOTH light and dark themes.

Why this replaced the earlier custom dark-mode toggle: Streamlit reads its
``[theme] base`` (light/dark) at startup from ``.streamlit/config.toml`` and
cannot be flipped per-session. A custom runtime toggle could only restyle the
page background, which left every native widget (buttons, tables, inputs,
sidebar) on the opposite base — a clashing, "strange" dark mode. Deferring to
Streamlit's native theme (Main menu → Settings → Theme, or the system
preference) makes light AND dark coherent because one system owns every
surface.

Loopback-only; this is purely presentational and never transmits anything.
Badges reuse the EXACT proof tokens — no overclaim wording (scanned by the
terminology test).
"""
from __future__ import annotations

import streamlit as st


# --- Semantic accent per proof token ------------------------------------------
# Only a subtle left-border tint carries semantics; the chip itself is adaptive
# (Streamlit secondary background + text color) so it reads on both themes.
_AMBER = {
    "NOT_LIVE_VALIDATED",
    "USER_SELECTED_ASSUMPTION_NOT_A_FORECAST",
    "TRANSCRIPT",
}
_POSITIVE = {"OPTIMAL", "SUPPORTED"}


def _semantic(token: str) -> str:
    if token in _AMBER:
        return "amber"
    if token in _POSITIVE:
        return "positive"
    return "neutral"


# --- Badges --------------------------------------------------------------------
def badge(token: str) -> str:
    """Return HTML for one small, neutral status chip using the exact token."""
    return f"<span class='po-badge po-badge--{_semantic(token)}'>{token}</span>"


def badges(*tokens: str) -> str:
    return " ".join(badge(t) for t in tokens)


def render_badges(*tokens: str) -> None:
    st.markdown(badges(*tokens), unsafe_allow_html=True)


# --- Cards ---------------------------------------------------------------------
def card_open(title: str | None = None, subtitle: str | None = None) -> None:
    """Open a styled card container header (paired with card_close)."""
    html = "<div class='po-card'>"
    if title:
        html += f"<div class='po-card-title'>{title}</div>"
    if subtitle:
        html += f"<div class='po-card-sub'>{subtitle}</div>"
    st.markdown(html, unsafe_allow_html=True)


def card_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


# --- Theme CSS -----------------------------------------------------------------
# Genuinely theme-agnostic: uses semi-transparent rgba() overlays + color:inherit
# so cards/badges/rails read correctly on Streamlit's NATIVE light AND dark
# surfaces. It does NOT depend on Streamlit CSS variables (1.60 does not expose
# --background-color etc. on the DOM) and does NOT override .stApp's background
# (that override was the dark-mode clash source: dark page + light widgets).
_THEME_CSS = """
<style>
.block-container { padding-top: 2.2rem; max-width: 1180px; }
h1 { font-size: 1.9rem; }
h2 { font-size: 1.35rem; margin-top: 0.4rem; }
h3 { font-size: 1.1rem; opacity: 0.85; }
.stCaption, .stMarkdown small { opacity: 0.72; }

/* Cards: translucent overlay + soft border/shadow — legible on light or dark */
.po-card {
  background: rgba(128, 128, 142, 0.08);
  border: 1px solid rgba(128, 128, 142, 0.28);
  border-radius: 14px;
  padding: 1.1rem 1.3rem;
  margin: 0.6rem 0 1.0rem 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.10);
  color: inherit;
}
.po-card-title { font-size: 1.15rem; font-weight: 700; color: inherit; margin-bottom: 0.15rem; }
.po-card-sub { font-size: 0.9rem; opacity: 0.7; }

/* Badges: translucent chip + subtle semantic left border (readable on both themes) */
.po-badge {
  display: inline-block;
  padding: 2px 9px;
  margin: 2px 4px 2px 0;
  border-radius: 999px;
  border-left: 3px solid rgba(128, 128, 142, 0.45);
  background: rgba(128, 128, 142, 0.12);
  color: inherit;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.po-badge--amber    { border-left-color: #c9931f; }
.po-badge--positive { border-left-color: #3a8a4a; }
.po-badge--neutral  { border-left-color: rgba(128, 128, 142, 0.45); }

/* Progress rail */
.po-rail { display: flex; gap: 6px; margin: 0.2rem 0 1.0rem 0; flex-wrap: wrap; }
.po-rail-step { flex: 1 1 0; min-width: 44px; height: 6px; border-radius: 999px; background: rgba(128, 128, 142, 0.30); }
.po-rail-step.done, .po-rail-step.active { background: var(--primary-color, #2f5d8a); }
.po-rail-step.active { opacity: 0.6; }

/* Buttons follow Streamlit's native theme; just round the corners */
.stButton > button { border-radius: 9px; }
</style>
"""


def inject_theme() -> None:
    """Inject the palette + typography + card/badge CSS once per render."""
    st.markdown(_THEME_CSS, unsafe_allow_html=True)


def render_progress_rail(current_index: int, total: int) -> None:
    """A slim segmented progress rail for the walkthrough."""
    segs = []
    for i in range(total):
        cls = "po-rail-step"
        if i < current_index:
            cls += " done"
        elif i == current_index:
            cls += " active"
        segs.append(f"<div class='{cls}'></div>")
    st.markdown(f"<div class='po-rail'>{''.join(segs)}</div>", unsafe_allow_html=True)
