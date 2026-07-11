import streamlit as st
from config import DEFAULT_PROJECT, MOUNTING_STRUCTURES, MODULE_TECHNOLOGIES, DEFAULT_CAPEX_PER_KWP
from utils.i18n import t, is_rtl, get_rtl_class
from utils.currency import fmt, fmt_cr
from utils.ingestion import parse_autolisp_json, build_sample_json, build_project_from_form, summarise
from utils.geocode import search_location

def render_project_ingestion():
    lang = st.session_state.lang
    cur = st.session_state.currency

    rtl_div  = f'<div class="{get_rtl_class(lang)}">' if is_rtl(lang) else ""
    rtl_end  = "</div>" if is_rtl(lang) else ""

    if rtl_div: st.markdown(rtl_div, unsafe_allow_html=True)
    st.markdown(f"""<div class='hero-banner'>
        <h1>👤 {t('nav_customer_project', lang)}</h1>
        <p>Define customer, project site, plant parameters, and module selection</p></div>""", unsafe_allow_html=True)

    # ── Quick actions ──────────────────────────────────────────────────────────
    act_cols = st.columns([1, 1, 2])
    with act_cols[0]:
        if st.button("🚀 Load Demo Project", key="demo_btn", use_container_width=True):
            st.session_state.project = build_sample_json()
            st.success("Demo project loaded!")
    with act_cols[1]:
        uploaded = st.file_uploader("Or import AutoLISP JSON", type=["json"],
                                    label_visibility="collapsed",
                                    help="Export JSON from SolarPro AutoLISP CAD tool")
    if uploaded:
        try:
            data = parse_autolisp_json(uploaded)
            st.session_state.form_initialized = False
            st.session_state.project = data
            st.success(f"✅ {summarise(data)}")
        except ValueError as e:
            st.error(str(e))

    st.markdown("---")

    # ── Location Search (with live suggestions) ────────────────────────────────
    p = st.session_state.project or DEFAULT_PROJECT.copy()

    def _on_loc_change():
        q = st.session_state.loc_query.strip()
        if len(q) >= 3:
            st.session_state.geo_results = search_location(q)
        else:
            st.session_state.geo_results = []

    def _on_geo_select():
        idx = st.session_state.geo_sel
        results = st.session_state.get("geo_results", [])
        if 0 <= idx < len(results):
            chosen = results[idx]
            st.session_state["loc_lat"] = chosen["lat"]
            st.session_state["loc_lon"] = chosen["lon"]
            st.session_state["loc_display"] = chosen["display_name"]

    st.markdown("### 2. Site Location")
    loc_query = st.text_input("Search location",
        key="loc_query", on_change=_on_loc_change,
        placeholder="Type a location (min 3 chars), then press Enter...",
        help="Type a city/site name, press Enter, then select from the suggestions below")

    geo_results = st.session_state.get("geo_results", [])
    if geo_results:
        loc_labels = [f"{r['display_name'][:90]}  ({r['lat']:.4f}, {r['lon']:.4f})" for r in geo_results]
        sel_idx = st.selectbox("Suggestions", range(len(loc_labels)),
            format_func=lambda i: loc_labels[i],
            key="geo_sel", on_change=_on_geo_select,
            label_visibility="collapsed")

    loc_lat = st.session_state.get("loc_lat")
    loc_lon = st.session_state.get("loc_lon")
    loc_display = st.session_state.get("loc_display", "")

    # ── Project Form ───────────────────────────────────────────────────────────
    with st.form("project_form", clear_on_submit=False, border=False):
        form_vals = {}
        st.markdown("### 1. Customer & Project")
        c1, c2 = st.columns(2)
        with c1:
            form_vals["customer_name"] = st.text_input("Customer Name",
                value=p.get("customer_name", ""), placeholder="e.g. Gujarat Solar Dev Corp")
        with c2:
            form_vals["project_name"] = st.text_input("Project Name",
                value=p.get("project_name", ""), placeholder="e.g. Rajkot Solar Phase 1")

        # Show selected location, fall back to manual lat/lon entry
        if loc_lat is not None:
            st.success(f"📍 {loc_display[:80]}")
            form_vals["location"] = loc_display
            form_vals["latitude"] = loc_lat
            form_vals["longitude"] = loc_lon
        else:
            form_vals["location"] = p.get("location", "")
            loc2, loc3 = st.columns(2)
            with loc2:
                form_vals["latitude"] = st.text_input("Latitude",
                    value=str(p.get("latitude", "")) if p.get("latitude") else "",
                    placeholder="e.g. 22.3039")
            with loc3:
                form_vals["longitude"] = st.text_input("Longitude",
                    value=str(p.get("longitude", "")) if p.get("longitude") else "",
                    placeholder="e.g. 70.8022")

        st.markdown("### 3. Plant Parameters")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            dc_mw = st.number_input("DC Capacity (MW)", 0.0, 500.0,
                value=float(p.get("dc_capacity_mw", p.get("dc_capacity_kwp", 0) / 1000) or 0),
                step=0.1, format="%.2f")
            form_vals["dc_capacity_mw"] = dc_mw
        with pc2:
            ac_mw = st.number_input("AC Capacity (MW)", 0.0, 500.0,
                value=float(p.get("ac_capacity_mw", 0) or 0),
                step=0.1, format="%.2f")
            form_vals["ac_capacity_mw"] = ac_mw
        with pc3:
            dc_ac = dc_mw / ac_mw if ac_mw > 0 else 0
            st.markdown(f"""<div style='background:#141828;border:1px solid #252D45;border-radius:12px;
                padding:24px 20px 10px;margin-top:2px;text-align:center'>
                <div style='font-size:11px;color:#94A3B8;text-transform:uppercase;letter-spacing:.08em'>DC/AC Ratio</div>
                <div style='font-size:28px;font-weight:800;color:#00D4AA;font-family:JetBrains Mono,monospace'>
                {dc_ac:.2f}</div></div>""", unsafe_allow_html=True)

        ps1, ps2 = st.columns(2)
        with ps1:
            form_vals["mounting_structure"] = st.selectbox("Mounting Structure",
                MOUNTING_STRUCTURES,
                index=MOUNTING_STRUCTURES.index(p.get("mounting_structure", "Fixed Tilt"))
                if p.get("mounting_structure") in MOUNTING_STRUCTURES else 0)
        with ps2:
            form_vals["gcr"] = st.number_input("Ground Coverage Ratio (GCR)", 0.1, 0.9,
                value=float(p.get("gcr", 0.40) or 0.40), step=0.05, format="%.2f")

        pt1, pt2 = st.columns(2)
        with pt1:
            form_vals["tilt"] = st.number_input("Tilt Angle (°)", 0, 90,
                value=int(p.get("tilt", 25) or 25), step=1)
        with pt2:
            form_vals["azimuth"] = st.number_input("Azimuth Angle (°)", 0, 360,
                value=int(p.get("azimuth", 180) or 180), step=5,
                help="180° = South (northern hemisphere), 0° = North")

        st.markdown("### 4. Module Selection & Configuration")
        mc1, mc2 = st.columns(2)
        with mc1:
            form_vals["module_technology"] = st.selectbox("Module Technology",
                MODULE_TECHNOLOGIES,
                index=MODULE_TECHNOLOGIES.index(p.get("module_technology", "Mono PERC (p-type)"))
                if p.get("module_technology") in MODULE_TECHNOLOGIES else 0)

        # Show available modules from Tab 6 if any were uploaded
        ds_df = st.session_state.get("ds_df")
        if ds_df is not None and len(ds_df) > 0:
            module_options = ds_df.apply(
                lambda r: f"{r.get('Manufacturer','')} {r.get('Model','')} ({r.get('Max Power (W)',0)}W)",
                axis=1).tolist()
            mod_sel = st.selectbox("Select Module from Datasheet Compare",
                [""] + module_options, key="mod_from_ds")
            if mod_sel:
                idx = module_options.index(mod_sel)
                row = ds_df.iloc[idx]
                form_vals["module_manufacturer"] = row.get("Manufacturer", "")
                form_vals["module_model"] = row.get("Model", "")
                try:
                    form_vals["module_watt"] = float(row.get("Max Power (W)", 0))
                except (ValueError, TypeError):
                    pass
        else:
            st.caption("No modules uploaded yet — go to the Module Compare tab to add datasheets, or enter manually below.")

        with mc2:
            form_vals["module_manufacturer"] = st.text_input("Manufacturer",
                value=p.get("module_manufacturer", ""), placeholder="e.g. Longi")
            form_vals["module_model"] = st.text_input("Module Model",
                value=p.get("module_model", ""), placeholder="e.g. HiMO7 580W")

        mw1, mw2 = st.columns(2)
        with mw1:
            default_mw = int(p.get("module_watt", 0) or 0)
            form_vals["module_watt"] = st.number_input("Module Wattage (Wp)", 0, 1000,
                value=default_mw if default_mw > 0 else 580, step=5)
        with mw2:
            form_vals["module_count"] = st.number_input("Module Count",
                value=int(p.get("module_count", 0) or 0), step=1,
                help="Auto-calculated from DC Capacity / Module Wattage. Override manually.",
                disabled=False)

        st.markdown("### 5. Preliminary Financial Context")
        fc1, fc2 = st.columns(2)
        with fc1:
            form_vals["specific_yield_estimate"] = st.number_input("Specific Yield Estimate (kWh/kWp)",
                800, 2500, value=int(p.get("specific_yield_estimate", 1550) or 1550), step=10)
        with fc2:
            form_vals["estimated_tariff"] = st.number_input("Estimated Tariff (₹/kWh)",
                1.0, 10.0, value=float(p.get("estimated_tariff", 2.85) or 2.85), step=0.05, format="%.2f")

        form_vals["notes"] = st.text_area("Notes",
            value=p.get("notes", ""), placeholder="Any additional notes about the project...")

        # ── Submit ─────────────────────────────────────────────────────────
        st.markdown("---")
        sub1, sub2 = st.columns([1, 1])
        with sub1:
            saved = st.form_submit_button("💾 Save Project", use_container_width=True, type="primary")
        with sub2:
            cleared = st.form_submit_button("🗑️ Clear Project", use_container_width=True)

        if saved:
            proj = build_project_from_form(form_vals)
            st.session_state.project = proj
            st.success(f"✅ Project '{proj.get('project_name','Untitled')}' saved!")
            st.rerun()
        if cleared:
            st.session_state.project = None
            st.rerun()

    # ── Project Summary Cards ─────────────────────────────────────────────────
    proj = st.session_state.project
    if proj:
        st.markdown("---")
        st.markdown("### Project Summary")
        capex_total = proj["dc_capacity_kwp"] * DEFAULT_CAPEX_PER_KWP
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.markdown(f"""<div class='metric-card'>
                <div class='card-icon'>⚡</div>
                <div class='card-label'>DC Capacity</div>
                <div class='card-value'>{proj['dc_capacity_kwp']:.0f}</div>
                <div class='card-delta'>kWp DC | AC: {proj.get('ac_capacity_mw',0):.1f} MW</div></div>""", unsafe_allow_html=True)
        with sc2:
            mod_label = f"{proj.get('module_manufacturer','')} {proj.get('module_watt',0):.0f}Wp" if proj.get('module_watt') else "—"
            st.markdown(f"""<div class='metric-card'>
                <div class='card-icon'>🔲</div>
                <div class='card-label'>Modules</div>
                <div class='card-value'>{proj.get('module_count', 0):,}</div>
                <div class='card-delta'>{mod_label}</div></div>""", unsafe_allow_html=True)
        with sc3:
            ms = proj.get('mounting_structure', '—')
            t_angle = proj.get('tilt', '—')
            st.markdown(f"""<div class='metric-card'>
                <div class='card-icon'>📐</div>
                <div class='card-label'>Mounting</div>
                <div class='card-value'>{t_angle}°</div>
                <div class='card-delta'>{ms[:28]}</div></div>""", unsafe_allow_html=True)
        with sc4:
            st.markdown(f"""<div class='metric-card'>
                <div class='card-icon'>💰</div>
                <div class='card-label'>Est. CAPEX</div>
                <div class='card-value'>{fmt_cr(capex_total, cur)}</div>
                <div class='card-delta'>@ {fmt(DEFAULT_CAPEX_PER_KWP, cur)}/kWp</div></div>""", unsafe_allow_html=True)

        with st.expander("All Project Data"):
            st.json(proj)
    if rtl_end: st.markdown(rtl_end, unsafe_allow_html=True)
