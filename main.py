"""SolarPro Financial Modelling — Main Streamlit App (Part 1 of 1)"""
import io
import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import LANGUAGES, CURRENCIES, STRIPE_PLANS, COMPLIANCE_CATEGORIES
from config import (DEFAULT_SPECIFIC_YIELD_P50, DEFAULT_CAPEX_PER_KWP,
                    DEFAULT_OPEX_PER_KWP, DEFAULT_TARIFF, DEFAULT_DEBT_FRACTION,
                    DEFAULT_INTEREST_RATE, DEFAULT_LOAN_TENURE, DEFAULT_TAX_RATE,
                    DEFAULT_DISCOUNT_RATE, DEFAULT_OPEX_ESCALATION)
from assets.style import CSS
from utils.i18n import t, is_rtl, get_rtl_class
from utils.currency import fmt, fmt_cr, get_rates
from utils.ingestion import parse_autolisp_json, build_sample_json, summarise
from utils.financial_engine import (run_sensitivity, build_cashflows, compute_metrics,
                                     DEFAULT_TOD_SLOTS, compute_blended_tariff)
from utils.performance import (load_generation_excel, compute_variance,
                                summary_stats, plot_generation_chart,
                                plot_cumulative_chart, build_sample_excel)
from utils.compliance import (CHECKLIST, STATUS_OPTIONS, STATUS_EMOJI,
                               STATUS_CLASS, init_compliance_state,
                               get_item_status, set_item_status,
                               get_item_due, category_progress,
                               overall_progress, export_checklist_csv)
from utils.billing import create_checkout_session, get_plan_features, is_demo_mode
from utils.pdf_export import generate_report
from utils.datasheet import (parse_csv_excel, parse_pdf, build_sample_excel as ds_sample_excel,
                             compute_ranking, plot_radar, plot_parameter_bars)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SolarPro Financial",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── Session State Defaults ────────────────────────────────────────────────────
if "lang"     not in st.session_state: st.session_state.lang     = "en"
if "currency" not in st.session_state: st.session_state.currency = "INR"
if "project"  not in st.session_state: st.session_state.project  = None
if "sens"     not in st.session_state: st.session_state.sens     = None
if "perf_df"  not in st.session_state: st.session_state.perf_df  = None
init_compliance_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────
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
    lang = lang_choice

    st.markdown("<div class='sidebar-section'>CURRENCY</div>", unsafe_allow_html=True)
    cur_choice = st.selectbox("", list(CURRENCIES.keys()),
        format_func=lambda k: f"{CURRENCIES[k]['flag']} {k} — {CURRENCIES[k]['symbol']}",
        index=list(CURRENCIES.keys()).index(st.session_state.currency),
        label_visibility="collapsed", key="cur_select")
    st.session_state.currency = cur_choice
    cur = cur_choice

    st.divider()
    if st.session_state.project:
        st.success(f"✅ {st.session_state.project.get('project_name','Project')[:28]}")
        st.caption(f"{st.session_state.project['dc_capacity_kwp']:.0f} kWp | {st.session_state.project['module_count']:,} modules")
    else:
        st.info("No project loaded. Upload JSON on the Ingestion tab.")

    st.divider()
    comp_done, comp_total, comp_pct = overall_progress()
    st.caption(f"Compliance: {comp_done}/{comp_total}")
    st.progress(comp_pct)

# ── RTL wrapper ───────────────────────────────────────────────────────────────
rtl_div  = f'<div class="{get_rtl_class(lang)}">' if is_rtl(lang) else ""
rtl_end  = "</div>" if is_rtl(lang) else ""

# ── Tab Navigation ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    t("nav_ingestion",  lang), t("nav_financial", lang),
    t("nav_performance",lang), t("nav_compliance",lang),
    t("nav_reports",    lang), t("nav_datasheet", lang),
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PROJECT INGESTION
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    if rtl_div: st.markdown(rtl_div, unsafe_allow_html=True)
    st.markdown(f"""<div class='hero-banner'>
        <h1>☀️ {t('nav_ingestion', lang)}</h1>
        <p>{t('app_tagline', lang)}</p></div>""", unsafe_allow_html=True)

    col_up, col_demo = st.columns([3, 1])
    with col_up:
        uploaded = st.file_uploader(t("upload_json", lang), type=["json"],
                                    help="Export JSON from SolarPro AutoLISP tool")
    with col_demo:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Load Demo Project", key="demo_btn"):
            st.session_state.project = build_sample_json()
            st.success("Demo project loaded!")

    if uploaded:
        try:
            data = parse_autolisp_json(uploaded)
            st.session_state.project = data
            st.success(f"✅ {summarise(data)}")
        except ValueError as e:
            st.error(str(e))

    proj = st.session_state.project
    if proj:
        st.markdown("### Project Details")
        c1, c2, c3, c4 = st.columns(4)
        sym = CURRENCIES[cur]["symbol"]
        capex_total = proj["dc_capacity_kwp"] * DEFAULT_CAPEX_PER_KWP
        with c1:
            st.markdown(f"""<div class='metric-card'>
                <div class='card-icon'>⚡</div>
                <div class='card-label'>{t('dc_capacity', lang)}</div>
                <div class='card-value'>{proj['dc_capacity_kwp']:.0f}</div>
                <div class='card-delta'>kWp DC</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='metric-card'>
                <div class='card-icon'>🔲</div>
                <div class='card-label'>{t('module_count', lang)}</div>
                <div class='card-value'>{proj['module_count']:,}</div>
                <div class='card-delta'>{proj.get('module_watt', '—')} Wp/module</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class='metric-card'>
                <div class='card-icon'>📐</div>
                <div class='card-label'>{t('tilt_angle', lang)}</div>
                <div class='card-value'>{proj['tilt']:.0f}°</div>
                <div class='card-delta'>Fixed tilt</div></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class='metric-card'>
                <div class='card-icon'>💰</div>
                <div class='card-label'>Est. CAPEX</div>
                <div class='card-value'>{fmt_cr(capex_total, cur)}</div>
                <div class='card-delta'>@ {fmt(DEFAULT_CAPEX_PER_KWP, cur)}/kWp</div></div>""", unsafe_allow_html=True)

        with st.expander("Raw JSON Data"):
            st.json(proj)
    if rtl_end: st.markdown(rtl_end, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — FINANCIAL ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    if rtl_div: st.markdown(rtl_div, unsafe_allow_html=True)
    st.markdown(f"""<div class='hero-banner'>
        <h1>💰 {t('nav_financial', lang)}</h1>
        <p>{t('sensitivity', lang)}</p></div>""", unsafe_allow_html=True)

    proj = st.session_state.project
    if not proj:
        st.warning("⚠️ Please upload a project on the Ingestion tab first.")
    else:
        dc_kwp = proj["dc_capacity_kwp"]
        with st.expander("⚙️ " + t("assumptions", lang), expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                sy   = st.number_input("Specific Yield P50 (kWh/kWp)", 800, 2500, DEFAULT_SPECIFIC_YIELD_P50, step=10)
                tar  = st.number_input("Tariff (₹/kWh)", 1.0, 10.0, DEFAULT_TARIFF, step=0.05, format="%.2f")
                cpx  = st.number_input("CAPEX/kWp (₹)", 15000, 80000, DEFAULT_CAPEX_PER_KWP, step=500)
            with col2:
                opx  = st.number_input("OPEX/kWp/yr (₹)", 200, 3000, DEFAULT_OPEX_PER_KWP, step=50)
                df_  = st.slider("Debt Fraction (%)", 40, 90, int(DEFAULT_DEBT_FRACTION*100)) / 100
                ir   = st.slider("Interest Rate (%)", 5.0, 16.0, DEFAULT_INTEREST_RATE*100, step=0.25) / 100
            with col3:
                lt   = st.slider("Loan Tenure (yrs)", 5, 20, DEFAULT_LOAN_TENURE)
                tr   = st.slider("Tax Rate (%)", 0, 40, int(DEFAULT_TAX_RATE*100)) / 100
                dr   = st.slider("Discount Rate (%)", 5.0, 20.0, DEFAULT_DISCOUNT_RATE*100, step=0.5) / 100
                oe   = st.slider("OPEX Escalation (%)", 0.0, 8.0, DEFAULT_OPEX_ESCALATION*100, step=0.25) / 100

        # ── Time-of-Day Tariff ─────────────────────────────────────────────
        tod_enabled = st.toggle("🕒 Enable Time-of-Day (ToD) Tariff",
                                value=False, key="tod_toggle",
                                help="Weights peak/off-peak tariff rates by % of solar generation in each period")
        tod_slots = None
        if tod_enabled:
            import copy
            slots = copy.deepcopy(DEFAULT_TOD_SLOTS)
            st.markdown("**Configure ToD Slots** — adjust multipliers and generation share per period:")
            tod_cols = st.columns(3)
            slot_colors = {"Peak": "#F59E0B", "Normal": "#00D4AA", "Off-Peak": "#6C63FF"}
            for idx, (slot_name, slot_cfg) in enumerate(slots.items()):
                with tod_cols[idx]:
                    scolor = slot_colors[slot_name]
                    st.markdown(f"<div style='border-left:3px solid {scolor};padding-left:10px'>"
                                f"<b style='color:{scolor}'>{slot_name}</b><br>"
                                f"<small style='color:#94A3B8'>{slot_cfg['hours']}</small></div>",
                                unsafe_allow_html=True)
                    slot_cfg["tariff_mult"] = st.number_input(
                        f"Tariff Mult ({slot_name})", 0.5, 3.0,
                        float(slot_cfg["tariff_mult"]), step=0.05,
                        key=f"tod_mult_{slot_name}", label_visibility="collapsed",
                        help="Multiplier applied to base tariff in this period")
                    slot_cfg["gen_pct"] = st.slider(
                        f"Gen % ({slot_name})", 0, 100,
                        int(slot_cfg["gen_pct"] * 100),
                        key=f"tod_pct_{slot_name}",
                        label_visibility="collapsed") / 100
            tod_slots = slots
            blended = compute_blended_tariff(tar, tod_slots)
            st.markdown(
                f"""<div class='metric-card' style='margin-top:12px'>
                <div class='card-icon'>📊</div>
                <div class='card-label'>Blended Effective Tariff</div>
                <div class='card-value'>₹{blended:.4f}</div>
                <div class='card-delta'>vs flat ₹{tar:.2f}/kWh | uplift: {(blended/tar-1)*100:+.2f}%</div>
                </div>""", unsafe_allow_html=True)

        if st.button("🚀 " + t("calculate", lang), key="calc_btn"):
            with st.spinner("Running financial model..."):
                sens = run_sensitivity(dc_kwp, sy, cpx, opx, tar, df_, ir, lt, tr, oe, dr,
                                       tod_slots=tod_slots)
                st.session_state.sens = sens
                st.session_state.fin_params = dict(
                    dc_kwp=dc_kwp, specific_yield=sy, capex_per_kwp=cpx,
                    opex_per_kwp=opx, tariff=tar, debt_fraction=df_,
                    interest_rate=ir, loan_tenure=lt, tax_rate=tr,
                    opex_escalation=oe, discount_rate=dr,
                    tod_enabled=tod_enabled,
                    blended_tariff=compute_blended_tariff(tar, tod_slots) if tod_slots else tar)
            st.success("✅ Calculation complete!")

        if st.session_state.sens:
            sens = st.session_state.sens
            sym = CURRENCIES[cur]["symbol"]

            # ── KPI Cards P50 ─────────────────────────────────────────────
            m50 = sens["P50"]
            st.markdown(f"### {t('results', lang)} — P50 Base Case")
            kc1, kc2, kc3, kc4, kc5 = st.columns(5)
            cards = [
                (kc1, t("equity_irr",lang), f"{m50['equity_irr']*100:.2f}%", "📈"),
                (kc2, t("lcoe",lang),       f"{m50['lcoe']:.3f}", "⚡"),
                (kc3, t("npv",lang),        fmt_cr(m50["npv"], cur), "💹"),
                (kc4, t("payback",lang),    f"{m50['payback']} yrs", "📅"),
                (kc5, t("dscr",lang),       f"{m50['min_dscr']:.2f}x", "🏦"),
            ]
            for col, lbl, val, icon in cards:
                with col:
                    st.markdown(f"""<div class='metric-card'>
                        <div class='card-icon'>{icon}</div>
                        <div class='card-label'>{lbl}</div>
                        <div class='card-value'>{val}</div></div>""", unsafe_allow_html=True)

            # ── Sensitivity Table ─────────────────────────────────────────
            st.markdown(f"### {t('sensitivity', lang)}")
            rows = []
            for sc, m in sens.items():
                rows.append({
                    "Scenario": sc,
                    "Equity IRR (%)":  f"{m['equity_irr']*100:.2f}",
                    "Project IRR (%)": f"{m['project_irr']*100:.2f}",
                    "LCOE (₹/kWh)":   f"{m['lcoe']:.3f}",
                    "NPV":             fmt_cr(m["npv"], cur),
                    "Payback (yrs)":   str(m.get("payback","N/A")),
                    "Min DSCR":        f"{m['min_dscr']:.2f}x",
                })
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

            # ── IRR Bar Chart ─────────────────────────────────────────────
            fig = go.Figure()
            scenarios = list(sens.keys())
            colors = ["#00D4AA","#6C63FF","#F59E0B"]
            fig.add_trace(go.Bar(
                name="Equity IRR", x=scenarios,
                y=[sens[s]["equity_irr"]*100 for s in scenarios],
                marker_color=colors, text=[f"{sens[s]['equity_irr']*100:.2f}%" for s in scenarios],
                textposition="outside"))
            fig.update_layout(
                paper_bgcolor="#141828", plot_bgcolor="#141828",
                font_color="#E8EAF0", height=320,
                yaxis_title="IRR (%)", margin=dict(l=0,r=0,t=30,b=0),
                yaxis=dict(gridcolor="#252D45"))
            st.plotly_chart(fig, width="stretch")

            # ── 25-Year Cash Flow Table ───────────────────────────────────
            st.markdown(f"### {t('cash_flows', lang)}")
            df_cf = sens["P50"]["cashflow_df"].copy()
            df_display = df_cf[["Year","Generation_kWh","Revenue_INR","OPEX_INR",
                                  "EBITDA_INR","Equity_FCF_INR","DSCR"]].copy()
            for col in ["Revenue_INR","OPEX_INR","EBITDA_INR","Equity_FCF_INR"]:
                df_display[col] = df_display[col].apply(
                    lambda x: fmt(x, cur, decimals=0))
            st.dataframe(df_display, width="stretch", hide_index=True, height=420)

            # Download button
            csv_cf = sens["P50"]["cashflow_df"].to_csv(index=False)
            st.download_button("📥 Download Cash Flow CSV", csv_cf,
                               "cashflow_p50.csv", "text/csv")
    if rtl_end: st.markdown(rtl_end, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
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

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    if rtl_div: st.markdown(rtl_div, unsafe_allow_html=True)
    st.markdown(f"""<div class='hero-banner'>
        <h1>✅ {t('nav_compliance', lang)}</h1>
        <p>Statutory approval tracker — Nodal Agencies, DISCOM, CEIG, Financial Institutions</p></div>""",
        unsafe_allow_html=True)

    done, total, pct = overall_progress()
    st.markdown(f"**Overall Progress: {done}/{total} items completed**")
    st.progress(pct)
    st.markdown("---")

    for category, items in CHECKLIST.items():
        cat_done, cat_total, cat_pct = category_progress(category)
        with st.expander(f"{category}  —  {cat_done}/{cat_total} ✅", expanded=(cat_pct < 1.0)):
            st.progress(cat_pct)
            for item in items:
                iid = item["id"]
                cur_status = get_item_status(iid)
                c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                with c1:
                    st.markdown(f"**{item['item']}**  \n`Owner: {item['owner']}`")
                with c2:
                    new_status = st.selectbox("Status", STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(cur_status),
                        key=f"status_{iid}", label_visibility="collapsed")
                    if new_status != cur_status:
                        set_item_status(iid, new_status)
                with c3:
                    st.date_input("Due", value=get_item_due(iid),
                                  key=f"due_{iid}", label_visibility="collapsed")
                with c4:
                    badge_cls = STATUS_CLASS[new_status]
                    st.markdown(f"<span class='badge-base {badge_cls}'>{STATUS_EMOJI[new_status]}</span>",
                                unsafe_allow_html=True)
                st.divider()

    st.download_button("📥 Export Checklist CSV",
                       export_checklist_csv(),
                       "compliance_checklist.csv", "text/csv")
    if rtl_end: st.markdown(rtl_end, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — REPORTS & BILLING
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    if rtl_div: st.markdown(rtl_div, unsafe_allow_html=True)
    st.markdown(f"""<div class='hero-banner'>
        <h1>📄 {t('nav_reports', lang)}</h1>
        <p>Generate investor-grade PDF reports and manage your subscription</p></div>""",
        unsafe_allow_html=True)

    # ── PDF Export ────────────────────────────────────────────────────────────
    st.markdown("### 📄 PDF Report Generator")
    if not st.session_state.project:
        st.info("Load a project on the Ingestion tab to enable PDF export.")
    elif not st.session_state.sens:
        st.info("Run financial calculations on the Financial Engine tab first.")
    else:
        report_lang = st.selectbox("Report Language", list(LANGUAGES.keys()),
            format_func=lambda k: LANGUAGES[k],
            index=list(LANGUAGES.keys()).index(lang), key="pdf_lang")
        if st.button("🖨️ " + t("download_pdf", lang), key="pdf_btn"):
            with st.spinner("Generating PDF..."):
                params_display = {
                    "DC Capacity":    f"{st.session_state.project['dc_capacity_kwp']:.0f} kWp",
                    "Specific Yield": f"{st.session_state.fin_params.get('specific_yield', DEFAULT_SPECIFIC_YIELD_P50)} kWh/kWp",
                    "Tariff":         f"₹{st.session_state.fin_params.get('tariff', DEFAULT_TARIFF)}/kWh",
                    "CAPEX/kWp":      f"₹{st.session_state.fin_params.get('capex_per_kwp', DEFAULT_CAPEX_PER_KWP):,}",
                    "Debt Fraction":  f"{st.session_state.fin_params.get('debt_fraction', DEFAULT_DEBT_FRACTION)*100:.0f}%",
                    "Interest Rate":  f"{st.session_state.fin_params.get('interest_rate', DEFAULT_INTEREST_RATE)*100:.2f}%",
                    "Discount Rate":  f"{st.session_state.fin_params.get('discount_rate', DEFAULT_DISCOUNT_RATE)*100:.2f}%",
                }
                pdf_bytes = generate_report(
                    project=st.session_state.project,
                    metrics_p50=st.session_state.sens["P50"],
                    sensitivity=st.session_state.sens,
                    df_cashflows=st.session_state.sens["P50"]["cashflow_df"],
                    params=params_display,
                    lang=report_lang,
                    currency=cur,
                )
            st.download_button("📥 Download PDF",
                               pdf_bytes,
                               f"SolarPro_Report_{st.session_state.project.get('project_name','Project').replace(' ','_')}.pdf",
                               "application/pdf")

    st.markdown("---")

    # ── Billing Plans ─────────────────────────────────────────────────────────
    st.markdown("### 💳 Subscription Plans")

    # Demo mode banner
    if is_demo_mode():
        st.markdown("""
<div style='background:linear-gradient(135deg,#F59E0B18,#EF444418);border:1px solid #F59E0B44;
border-radius:12px;padding:16px 20px;margin-bottom:20px'>
<div style='display:flex;align-items:center;gap:12px'>
<span style='font-size:28px'>🔶</span>
<div>
<div style='font-weight:700;color:#F59E0B;font-size:14px'>Demo Mode — Stripe Not Connected</div>
<div style='color:#94A3B8;font-size:12px;margin-top:4px'>
Billing UI is fully functional in preview mode. To enable real payments, add your
<code style='color:#00D4AA'>STRIPE_SECRET_KEY</code> to the <code style='color:#00D4AA'>.env</code> file.
See the <b>Stripe Activation Guide</b> below.
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

    # Plan cards
    bc1, bc2, bc3 = st.columns(3)
    plan_cols    = {"free": bc1, "pro": bc2, "enterprise": bc3}
    plan_featured = {"free": False, "pro": True, "enterprise": False}

    for plan_id, col in plan_cols.items():
        plan_info    = STRIPE_PLANS[plan_id]
        featured_cls = "featured" if plan_featured[plan_id] else ""
        price_str    = f"₹{plan_info['price_inr']:,}" if plan_info["price_inr"] > 0 else "Free"
        proj_str     = (f"{plan_info['projects']} project"
                        f"{'s' if plan_info['projects'] != 1 else ''}"
                        if plan_info["projects"] > 0 else "Unlimited projects")
        features     = get_plan_features(plan_id)
        feat_html    = "".join(
            f"<div style='font-size:12px;color:#94A3B8;margin:4px 0'>{f}</div>"
            for f in features)
        with col:
            st.markdown(f"""<div class='plan-card {featured_cls}'>
                <div class='plan-label'>{plan_info['label']}</div>
                <div class='plan-price'>{price_str}</div>
                <div class='plan-sub'>/month · {proj_str}</div>
                <hr style='border-color:#252D45;margin:12px 0'>
                {feat_html}</div>""", unsafe_allow_html=True)

            if plan_id != "free":
                email = st.text_input("📧 Email", key=f"email_{plan_id}",
                                      placeholder="you@company.com")
                gstin = st.text_input("🏢 GSTIN (optional)", key=f"gstin_{plan_id}",
                                      placeholder="22AAAAA0000A1Z5",
                                      help="18-character GST Identification Number for B2B invoicing")

                if st.button(f"{'🔒 ' if not is_demo_mode() else '🎮 Demo '}{t('subscribe', lang)}",
                             key=f"sub_{plan_id}"):
                    if not email:
                        st.warning("⚠️ Enter your email first.")
                    elif is_demo_mode():
                        # ── Mock checkout receipt ─────────────────────────
                        price     = plan_info["price_inr"]
                        gst_rate  = 0.18  # 18% GST
                        gst_amt   = price * gst_rate
                        total     = price + gst_amt
                        gstin_str = gstin if gstin else "Not provided (B2C)"
                        st.success("✅ Demo Checkout Simulated Successfully!")
                        st.markdown(f"""
<div style='background:#141828;border:1px solid #00D4AA44;border-radius:12px;
padding:20px 24px;margin-top:12px'>
<div style='color:#00D4AA;font-weight:800;font-size:14px;margin-bottom:12px'>
🧾 DEMO RECEIPT — SolarPro Financial</div>
<table style='width:100%;font-size:12px;color:#94A3B8;border-collapse:collapse'>
<tr><td style='padding:4px 0'>Plan</td>
    <td style='text-align:right;color:#E8EAF0;font-weight:600'>{plan_info['label']}</td></tr>
<tr><td style='padding:4px 0'>Customer</td>
    <td style='text-align:right;color:#E8EAF0'>{email}</td></tr>
<tr><td style='padding:4px 0'>GSTIN</td>
    <td style='text-align:right;color:#E8EAF0'>{gstin_str}</td></tr>
<tr><td style='padding:4px 0'>Base Amount</td>
    <td style='text-align:right;color:#E8EAF0'>₹{price:,.0f}</td></tr>
<tr><td style='padding:4px 0'>GST @ 18%</td>
    <td style='text-align:right;color:#F59E0B'>₹{gst_amt:,.0f}</td></tr>
<tr style='border-top:1px solid #252D45'>
<td style='padding:8px 0;font-weight:700;color:#E8EAF0'>Total Payable</td>
<td style='text-align:right;font-weight:800;color:#00D4AA;font-size:14px'>₹{total:,.0f}/mo</td></tr>
</table>
<div style='margin-top:12px;padding:8px;background:#0A0E1A;border-radius:8px;
font-size:11px;color:#4A5568;text-align:center'>
⚠️ This is a DEMO receipt. Add STRIPE_SECRET_KEY to .env for real billing.
</div></div>""", unsafe_allow_html=True)
                    else:
                        # ── Live Stripe checkout ──────────────────────────
                        url = create_checkout_session(plan_id, email, gstin=gstin or None)
                        if url.startswith("ERROR"):
                            st.error(url)
                        else:
                            st.markdown(
                                f"<a href='{url}' target='_blank' style='display:block;"
                                f"background:linear-gradient(135deg,#00D4AA,#6C63FF);"
                                f"color:#fff;padding:12px;border-radius:8px;text-align:center;"
                                f"font-weight:700;text-decoration:none;margin-top:8px'>"
                                f"🔒 Complete Secure Payment →</a>",
                                unsafe_allow_html=True)

    # ── Stripe Activation Guide ───────────────────────────────────────────────
    st.markdown("---")
    with st.expander("⚡ How to Activate Stripe Live Payments", expanded=False):
        st.markdown("""
**3-step setup to enable real billing:**

**Step 1 — Get your Stripe keys**
1. Go to [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys)
2. Copy your **Secret key** (`sk_test_...` for testing, `sk_live_...` for production)

**Step 2 — Create Products & Prices in Stripe**
1. In Stripe Dashboard → Products → Add Product
2. Create **SolarPro Pro** (₹999/month recurring) → copy the Price ID (`price_...`)
3. Create **SolarPro Enterprise** (₹4,999/month recurring) → copy its Price ID

**Step 3 — Fill in `.env` file** (copy from `.env.example`):
```
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET
STRIPE_PRICE_PRO=price_YOUR_PRO_PRICE_ID
STRIPE_PRICE_ENTERPRISE=price_YOUR_ENT_PRICE_ID
```

Then restart the app — billing switches to live mode automatically. 🎉

> **GST Note:** Stripe's `automatic_tax=True` + `tax_id_collection` are already configured.
> Indian customers with a GSTIN will receive GST-compliant B2B invoices automatically.
""")
    if rtl_end: st.markdown(rtl_end, unsafe_allow_html=True)
