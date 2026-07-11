"""
SolarPro — Real-time Multi-Currency FX Engine
Base currency: INR. Rates cached in st.session_state for 1 hour.
"""
import time
import requests
import streamlit as st
from config import CURRENCIES

# Fallback hardcoded rates (INR base, updated periodically)
FALLBACK_RATES: dict[str, float] = {
    "INR": 1.0,
    "USD": 0.01202,
    "EUR": 0.01105,
    "GBP": 0.00948,
    "AED": 0.04414,
    "CNY": 0.08717,
    "SGD": 0.01621,
    "JPY": 1.8120,
}

FX_API_URL = "https://api.exchangerate.host/latest?base=INR"
CACHE_TTL_SECONDS = 3600  # 1 hour


def _fetch_rates() -> dict[str, float]:
    """Fetch live rates from exchangerate.host. Returns fallback on failure."""
    try:
        resp = requests.get(FX_API_URL, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            rates = data.get("rates", {})
            rates["INR"] = 1.0
            return rates
    except Exception:
        pass
    return FALLBACK_RATES.copy()


def get_rates() -> dict[str, float]:
    """Return exchange rates, using session_state cache."""
    now = time.time()
    if "fx_rates" not in st.session_state or (now - st.session_state.get("fx_ts", 0)) > CACHE_TTL_SECONDS:
        st.session_state["fx_rates"] = _fetch_rates()
        st.session_state["fx_ts"] = now
    return st.session_state["fx_rates"]


def convert(amount_inr: float, target: str) -> float:
    """Convert an INR amount to the target currency."""
    if target == "INR":
        return amount_inr
    rates = get_rates()
    rate = rates.get(target, FALLBACK_RATES.get(target, 1.0))
    return amount_inr * rate


def fmt(amount_inr: float, currency: str, decimals: int = 2) -> str:
    """Format a converted amount with currency symbol."""
    value = convert(amount_inr, currency)
    sym = CURRENCIES.get(currency, {}).get("symbol", currency)
    if abs(value) >= 1_000_000:
        return f"{sym}{value/1_000_000:.{decimals}f}M"
    if abs(value) >= 1_000:
        return f"{sym}{value/1_000:.{decimals}f}K"
    return f"{sym}{value:,.{decimals}f}"


def fmt_cr(amount_inr: float, currency: str) -> str:
    """Format large INR amounts in Crores, or foreign equivalent in Millions."""
    sym = CURRENCIES.get(currency, {}).get("symbol", currency)
    if currency == "INR":
        cr = amount_inr / 1_00_00_000
        return f"₹{cr:.2f} Cr"
    value = convert(amount_inr, currency)
    return f"{sym}{value/1_000_000:.2f}M"
