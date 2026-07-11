import streamlit as st
from utils.i18n import t, is_rtl, get_rtl_class
from utils.compliance import (CHECKLIST, STATUS_OPTIONS, STATUS_EMOJI,
                               STATUS_CLASS, get_item_status, set_item_status,
                               get_item_due, category_progress,
                               overall_progress, export_checklist_csv)

def render_compliance():
    lang = st.session_state.lang
    rtl_div  = f'<div class="{get_rtl_class(lang)}">' if is_rtl(lang) else ""
    rtl_end  = "</div>" if is_rtl(lang) else ""

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
