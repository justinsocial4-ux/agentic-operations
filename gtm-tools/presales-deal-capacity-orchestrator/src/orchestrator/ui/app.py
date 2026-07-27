"""Loopback-only Streamlit review UI (Phase 7).

Recommendation-only. No CRM write, task, webhook, message, assignment, or
production mutation. No credentials, no live vendor calls, no remote LLM.
Run with:  streamlit run src/orchestrator/ui/app.py
"""
from __future__ import annotations

import streamlit as st

from orchestrator.ui import copy, theme
from orchestrator.ui.demo import build_demo_run
from orchestrator.ui.state import FlowState, Stage
from orchestrator.ui.views import render
from orchestrator.ui.views.walkthrough import render_walkthrough


def _flow() -> FlowState:
    if "flow" not in st.session_state:
        st.session_state["flow"] = FlowState()
    return st.session_state["flow"]


def main() -> None:
    st.set_page_config(page_title=copy.APP_TITLE, layout="wide")
    # Theme polish defers to Streamlit's native light/dark theming (Main menu →
    # Settings → Theme, or the system preference) so every surface is coherent.
    # The earlier custom dark-mode toggle clashed with Streamlit's startup theme
    # base and was removed.
    theme.inject_theme()
    st.title(copy.APP_TITLE)
    flow = _flow()

    if flow.stage is Stage.LANDING:
        render.render_landing(flow)
        return

    demo_run = build_demo_run(flow.lane) if flow.lane is not None else build_demo_run()

    if flow.stage is Stage.AUTHORITY:
        render.render_authority(flow)
    elif flow.stage is Stage.SETUP:
        render.render_setup(flow)
    elif flow.stage is Stage.MAPPING:
        render.render_mapping(flow)
    elif flow.stage is Stage.HEALTH:
        render.render_health(flow)
    elif flow.stage is Stage.EVIDENCE:
        render.render_evidence(flow, demo_run)
    elif flow.stage is Stage.WALKTHROUGH:
        render_walkthrough(flow, demo_run)
    elif flow.stage is Stage.RESULTS:
        render.render_results(flow, demo_run)


main()
