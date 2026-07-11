import streamlit as st
from utils.compliance import init_compliance_state

def init_session():
    """Initialize Streamlit session state variables."""
    if "lang"     not in st.session_state: st.session_state.lang     = "en"
    if "currency" not in st.session_state: st.session_state.currency = "INR"
    if "project"  not in st.session_state: st.session_state.project  = None
    if "sens"     not in st.session_state: st.session_state.sens     = None
    if "perf_df"  not in st.session_state: st.session_state.perf_df  = None
    init_compliance_state()
