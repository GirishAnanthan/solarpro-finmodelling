import streamlit as st

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SolarPro Financial",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from assets.style import CSS
st.markdown(CSS, unsafe_allow_html=True)

from state.session import init_session
from components.sidebar import render_sidebar
from utils.i18n import t

# Initialize state
init_session()

# Render sidebar
render_sidebar()

# Get current language
lang = st.session_state.lang

# ── Tab Navigation ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    t("nav_customer_project", lang),
    t("nav_financial_inputs", lang),
    t("nav_module_compare", lang) if "nav_module_compare" in dir(t) else "Module Compare",
    t("nav_performance", lang),
    t("nav_compliance", lang),
    t("nav_reports", lang),
])

# ── Views ─────────────────────────────────────────────────────────────────────
with tab1:
    from views.project_ingestion import render_project_ingestion
    render_project_ingestion()

with tab2:
    from views.financial_engine import render_financial_engine
    render_financial_engine()

with tab3:
    from views.module_compare import render_module_compare
    render_module_compare()

with tab4:
    from views.performance import render_performance
    render_performance()

with tab5:
    from views.compliance import render_compliance
    render_compliance()

with tab6:
    from views.reports_billing import render_reports_billing
    render_reports_billing()
