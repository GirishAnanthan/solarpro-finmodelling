import streamlit as st
from config import LANGUAGES, CURRENCIES
from utils.compliance import overall_progress

def render_sidebar():
    with st.sidebar:
        st.markdown("""<div class='sidebar-logo'>
            <span style='font-size:28px'>☀️</span>
            <div><div class='app-name'>SolarPro</div>
            <div class='app-ver'>Financial v1.0</div></div></div>""", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-section'>LANGUAGE</div>", unsafe_allow_html=True)
        lang_choice = st.selectbox("", list(LANGUAGES.keys()),
            format_func=lambda k: LANGUAGES[k],
            index=list(LANGUAGES.keys()).index(st.session_state.lang),
            label_visibility="collapsed", key="lang_select")
        st.session_state.lang = lang_choice

        st.markdown("<div class='sidebar-section'>CURRENCY</div>", unsafe_allow_html=True)
        cur_choice = st.selectbox("", list(CURRENCIES.keys()),
            format_func=lambda k: f"{CURRENCIES[k]['flag']} {k} — {CURRENCIES[k]['symbol']}",
            index=list(CURRENCIES.keys()).index(st.session_state.currency),
            label_visibility="collapsed", key="cur_select")
        st.session_state.currency = cur_choice

        st.divider()
        if st.session_state.project:
            p = st.session_state.project
            kwp = p.get("dc_capacity_kwp", 0)
            mods = p.get("module_count", 0)
            st.success(f"✅ {p.get('project_name','Project')[:28]}")
            st.caption(f"{kwp:.0f} kWp | {mods:,} modules | {p.get('module_manufacturer','')}")
        else:
            st.info("No project loaded. Create one on the Ingestion tab.")

        st.divider()
        comp_done, comp_total, comp_pct = overall_progress()
        st.caption(f"Compliance: {comp_done}/{comp_total}")
        st.progress(comp_pct)
