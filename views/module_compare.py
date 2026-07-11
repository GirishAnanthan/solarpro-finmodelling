import streamlit as st
from utils.i18n import t, is_rtl, get_rtl_class
from utils.datasheet import (parse_csv_excel, parse_pdf, build_sample_excel,
                             compute_ranking, plot_radar, plot_parameter_bars)
import pandas as pd

def render_module_compare():
    lang = st.session_state.lang
    rtl_div  = f'<div class="{get_rtl_class(lang)}">' if is_rtl(lang) else ""
    rtl_end  = "</div>" if is_rtl(lang) else ""

    if rtl_div: st.markdown(rtl_div, unsafe_allow_html=True)
    st.markdown(f"""<div class='hero-banner'>
        <h1>📊 {t('nav_module_compare', lang) if 'nav_module_compare' in dir(t) else 'Module Datasheet Compare'}</h1>
        <p>Compare solar module specifications and rank them based on key performance indicators</p></div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📤 Upload Datasheets")
        sample_xl = build_sample_excel()
        st.download_button("📥 Download Sample Template (Excel)", sample_xl,
                           "module_template.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        uploaded_file = st.file_uploader("Upload CSV, Excel, or PDF", type=["csv", "xlsx", "xls", "pdf"])

    if uploaded_file:
        if uploaded_file.name.endswith(".pdf"):
            ok, result = parse_pdf(uploaded_file)
        else:
            ok, result = parse_csv_excel(uploaded_file)

        if not ok:
            st.error(result)
        else:
            if "ds_df" not in st.session_state or st.session_state.ds_df is None:
                st.session_state.ds_df = result
            else:
                # Append new data to existing dataframe
                st.session_state.ds_df = pd.concat([st.session_state.ds_df, result], ignore_index=True).drop_duplicates()
            
            st.success("✅ Datasheet successfully parsed and added!")

    if "ds_df" in st.session_state and st.session_state.ds_df is not None and len(st.session_state.ds_df) > 0:
        df = st.session_state.ds_df
        st.markdown("---")
        st.markdown("### 🏆 Module Rankings")
        
        # Action button to clear comparison
        if st.button("🗑️ Clear Comparison"):
            st.session_state.ds_df = None
            st.rerun()

        ranked_df = compute_ranking(df)
        st.dataframe(ranked_df, use_container_width=True, hide_index=True)

        if len(df) > 1:
            st.markdown("---")
            st.markdown("### 📈 Visual Comparison")
            
            radar_fig = plot_radar(df)
            if radar_fig:
                st.markdown("#### Radar Chart")
                st.plotly_chart(radar_fig, use_container_width=True)

            bars_fig = plot_parameter_bars(df)
            if bars_fig:
                st.markdown("#### Parameter Bars")
                st.plotly_chart(bars_fig, use_container_width=True)

    if rtl_end: st.markdown(rtl_end, unsafe_allow_html=True)
