import streamlit as st
from utils.i18n import t, is_rtl, get_rtl_class
from utils.performance import (load_generation_excel, compute_variance,
                               summary_stats, plot_generation_chart,
                               plot_cumulative_chart, build_sample_excel)

def render_performance():
    lang = st.session_state.lang
    rtl_div  = f'<div class="{get_rtl_class(lang)}">' if is_rtl(lang) else ""
    rtl_end  = "</div>" if is_rtl(lang) else ""

    if rtl_div: st.markdown(rtl_div, unsafe_allow_html=True)
    st.markdown(f"""<div class='hero-banner'>
        <h1>📊 {t('nav_performance', lang)}</h1>
        <p>Actual vs Projected generation variance analysis</p></div>""", unsafe_allow_html=True)

    sample_xl = build_sample_excel()
    st.download_button("📥 Download Sample XLSX Template", sample_xl,
                       "sample_generation.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    xfile = st.file_uploader(t("upload_excel", lang), type=["xlsx","xls"],
                             help="Columns: Month, Projected_kWh, Actual_kWh")
    if xfile:
        ok, result = load_generation_excel(xfile)
        if not ok:
            st.error(result)
        else:
            df_var = compute_variance(result)
            st.session_state.perf_df = df_var
            stats  = summary_stats(df_var)

            # KPI row
            pk1, pk2, pk3, pk4 = st.columns(4)
            with pk1:
                st.markdown(f"""<div class='metric-card'>
                    <div class='card-icon'>☀️</div>
                    <div class='card-label'>{t('projected', lang)}</div>
                    <div class='card-value'>{stats['total_projected']/1e6:.2f}M</div>
                    <div class='card-delta'>kWh annual</div></div>""", unsafe_allow_html=True)
            with pk2:
                st.markdown(f"""<div class='metric-card'>
                    <div class='card-icon'>⚡</div>
                    <div class='card-label'>{t('actual', lang)}</div>
                    <div class='card-value'>{stats['total_actual']/1e6:.2f}M</div>
                    <div class='card-delta'>kWh annual</div></div>""", unsafe_allow_html=True)
            with pk3:
                vp = stats['total_variance_pct']
                col = "#10B981" if vp >= 0 else "#EF4444"
                st.markdown(f"""<div class='metric-card'>
                    <div class='card-icon'>📉</div>
                    <div class='card-label'>{t('variance', lang)}</div>
                    <div class='card-value' style='color:{col}'>{vp:+.2f}%</div>
                    <div class='card-delta'>vs projected</div></div>""", unsafe_allow_html=True)
            with pk4:
                pr = stats['pr_estimate']
                st.markdown(f"""<div class='metric-card'>
                    <div class='card-icon'>🎯</div>
                    <div class='card-label'>Performance Ratio</div>
                    <div class='card-value'>{pr*100:.1f}%</div>
                    <div class='card-delta'>Est. PR</div></div>""", unsafe_allow_html=True)

            st.markdown("### Monthly Generation Chart")
            st.plotly_chart(plot_generation_chart(df_var), width="stretch")
            st.markdown("### Cumulative Generation")
            st.plotly_chart(plot_cumulative_chart(df_var), width="stretch")
            st.markdown("### Variance Detail & Root Cause")
            st.dataframe(df_var[["Month","Projected_kWh","Actual_kWh",
                                  "Variance_kWh","Variance_pct","Root_Cause"]],
                         width="stretch", hide_index=True)
            st.download_button("📥 Download Variance CSV",
                               df_var.to_csv(index=False),
                               "variance_report.csv", "text/csv")
    if rtl_end: st.markdown(rtl_end, unsafe_allow_html=True)
