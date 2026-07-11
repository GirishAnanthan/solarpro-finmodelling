import streamlit as st
from config import (LANGUAGES, STRIPE_PLANS, DEFAULT_SPECIFIC_YIELD_P50,
                    DEFAULT_CAPEX_PER_KWP, DEFAULT_TARIFF, DEFAULT_DEBT_FRACTION,
                    DEFAULT_INTEREST_RATE, DEFAULT_DISCOUNT_RATE)
from utils.i18n import t, is_rtl, get_rtl_class
from utils.pdf_export import generate_report
from utils.billing import is_demo_mode, get_plan_features, create_checkout_session

def render_reports_billing():
    lang = st.session_state.lang
    cur = st.session_state.currency
    rtl_div  = f'<div class="{get_rtl_class(lang)}">' if is_rtl(lang) else ""
    rtl_end  = "</div>" if is_rtl(lang) else ""

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
