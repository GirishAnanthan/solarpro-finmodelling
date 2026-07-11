import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import (
    CURRENCIES,
    DEFAULT_SPECIFIC_YIELD_P50, DEFAULT_CAPEX_PER_KWP,
    DEFAULT_OPEX_PER_KWP, DEFAULT_TARIFF, DEFAULT_DEBT_FRACTION,
    DEFAULT_INTEREST_RATE, DEFAULT_LOAN_TENURE, DEFAULT_TAX_RATE,
    DEFAULT_DISCOUNT_RATE, DEFAULT_OPEX_ESCALATION
)
from utils.i18n import t, is_rtl, get_rtl_class
from utils.currency import fmt, fmt_cr
from utils.financial_engine import run_sensitivity, DEFAULT_TOD_SLOTS, compute_blended_tariff

def render_financial_engine():
    lang = st.session_state.lang
    cur = st.session_state.currency

    rtl_div  = f'<div class="{get_rtl_class(lang)}">' if is_rtl(lang) else ""
    rtl_end  = "</div>" if is_rtl(lang) else ""

    if rtl_div: st.markdown(rtl_div, unsafe_allow_html=True)
    st.markdown(f"""<div class='hero-banner'>
        <h1>💳 {t('nav_financial_inputs', lang)}</h1>
        <p>Project financing, PPA rates, debt structure, and module selection weightages</p></div>""", unsafe_allow_html=True)

    proj = st.session_state.project
    if not proj:
        st.warning("⚠️ Save a project on the Customer & Project tab first.")
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

        # ── Parameter Weightage for Module Selection ────────────────────────
        st.markdown("---")
        st.markdown(f"### ⚖️ {t('weightage_title', lang) if 'weightage_title' in dir(t) else 'Parameter Weightage for Module Scoring'}")
        st.caption("Define importance of each parameter for module selection analysis. Sums to 100%.")
        
        wt_cols = st.columns(4)
        weight_params = [
            ("max_power",   "Max Power (Wp)",     25),
            ("efficiency",  "Efficiency (%)",     25),
            ("temp_coeff",  "Temp Coefficient",   15),
            ("warranty",    "Warranty (yrs)",     15),
            ("vmp",         "Vmp (V)",            10),
            ("degradation", "Degradation (%/yr)", 10),
        ]
        if "module_weights" not in st.session_state:
            st.session_state.module_weights = {k: v for k, _, v in weight_params}
        
        for i, (key, label, default) in enumerate(weight_params):
            with wt_cols[i % 4]:
                st.session_state.module_weights[key] = st.slider(
                    label, 0, 100, st.session_state.module_weights.get(key, default), step=5,
                    key=f"wt_{key}", help=f"Weight for {label} in module scoring")

        total_wt = sum(st.session_state.module_weights.values())
        if total_wt != 100:
            st.warning(f"Total weightage: {total_wt}% — should be 100%")

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

    # ── Parameter Weightages for Module Selection ─────────────────────────
    st.markdown("---")
    st.markdown("### ⚖️ Parameter Weightages for Module Selection Analysis")
    st.caption("Assign importance (%) to each parameter. Weights are used in the Generate Report tab to score and rank modules.")
    w = {}
    wc1, wc2 = st.columns(2)
    with wc1:
        w["Max Power"]     = st.slider("Max Power (Wp)", 0, 100, 25, 5, key="w_power")
        w["Efficiency"]    = st.slider("Efficiency (%)", 0, 100, 20, 5, key="w_eff")
        w["Temp Coeff"]    = st.slider("Temp Coefficient (Pmax)", 0, 100, 15, 5, key="w_temp")
        w["Warranty"]      = st.slider("Warranty (Product+Power)", 0, 100, 15, 5, key="w_warranty")
    with wc2:
        w["Voltage (Vmp)"] = st.slider("Voltage (Vmp)", 0, 100, 10, 5, key="w_vmp")
        w["Current (Imp)"] = st.slider("Current (Imp)", 0, 100, 5, 5, key="w_imp")
        w["Dimensions"]    = st.slider("Dimensions (W/mm)", 0, 100, 5, 5, key="w_dim")
        w["Weight"]        = st.slider("Weight (kg)", 0, 100, 5, 5, key="w_weight")
    total_w = sum(w.values())
    if total_w != 100:
        st.warning(f"⚠️ Total weightage is {total_w}%. Adjust to exactly 100% for accurate scoring.")
    else:
        st.success(f"✅ Total weightage: {total_w}% — balanced")
    st.session_state.module_weights = w
    if rtl_end: st.markdown(rtl_end, unsafe_allow_html=True)
