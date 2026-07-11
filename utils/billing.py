"""
SolarPro — Stripe Billing Integration
Supports Free / Pro / Enterprise plans with automatic GST/VAT tax collection.
Runs in DEMO mode if STRIPE_SECRET_KEY is not set.
"""
from __future__ import annotations
import os
from dotenv import load_dotenv
from config import STRIPE_PLANS

load_dotenv()

STRIPE_SECRET_KEY  = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Stripe Price IDs — set these in your .env after creating products in Stripe dashboard
PRICE_IDS: dict[str, str] = {
    "pro":        os.getenv("STRIPE_PRICE_PRO", "price_demo_pro"),
    "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_demo_enterprise"),
}

DEMO_MODE = not bool(STRIPE_SECRET_KEY)


def create_checkout_session(
    plan: str,
    user_email: str,
    success_url: str = "http://localhost:8501/?payment=success",
    cancel_url:  str = "http://localhost:8501/?payment=cancel",
    gstin: str | None = None,
) -> str:
    """
    Create a Stripe Checkout Session and return the checkout URL.
    Returns a demo URL if running in DEMO mode.
    """
    if plan == "free":
        return success_url

    if DEMO_MODE:
        return (
            f"https://checkout.stripe.com/demo?plan={plan}"
            f"&email={user_email}"
            f"{'&gstin=' + gstin if gstin else ''}"
        )

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        price_id = PRICE_IDS.get(plan)
        if not price_id:
            raise ValueError(f"Unknown plan: {plan}")

        session_params: dict = {
            "mode":                "subscription",
            "payment_method_types":["card"],
            "customer_email":      user_email,
            "line_items":          [{"price": price_id, "quantity": 1}],
            "success_url":         success_url,
            "cancel_url":          cancel_url,
            "automatic_tax":       {"enabled": True},
            "customer_update":     {"address": "auto"},
            "tax_id_collection":   {"enabled": True},
            "metadata":            {"plan": plan},
        }
        if gstin:
            session_params["metadata"]["gstin"] = gstin

        session = stripe.checkout.Session.create(**session_params)
        return session.url
    except Exception as e:
        return f"ERROR: {e}"


def get_plan_features(plan: str) -> list[str]:
    """Return feature list for display in billing UI."""
    features = {
        "free": [
            "✅ 1 project analysis",
            "✅ Basic IRR / LCOE",
            "✅ PDF export (watermarked)",
            "❌ P50/P75/P90 sensitivity",
            "❌ Multi-currency",
            "❌ Compliance tracker",
        ],
        "pro": [
            "✅ 10 projects",
            "✅ Full sensitivity analysis",
            "✅ Performance variance module",
            "✅ Multi-currency + live FX",
            "✅ Statutory compliance tracker",
            "✅ Branded PDF export",
            "❌ API access",
        ],
        "enterprise": [
            "✅ Unlimited projects",
            "✅ All Pro features",
            "✅ REST API access",
            "✅ White-label PDF",
            "✅ Priority support",
            "✅ Custom language packs",
        ],
    }
    return features.get(plan, [])


def is_demo_mode() -> bool:
    return DEMO_MODE
