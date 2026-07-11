"""
SolarPro Financial Modelling — Global Configuration
"""
from pathlib import Path

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"

# ── App Identity ──────────────────────────────────────────────────────────────
APP_NAME = "SolarPro Financial"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Ground-Mounted Solar Financial Intelligence Platform"

# ── Supported Languages ───────────────────────────────────────────────────────
LANGUAGES: dict[str, str] = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिन्दी",
    "gu": "🇮🇳 ગુજરાતી",
    "zh": "🇨🇳 中文",
    "ar": "🇸🇦 العربية",
    "de": "🇩🇪 Deutsch",
    "es": "🇪🇸 Español",
    "el": "🇬🇷 Ελληνικά",
    "la": "🏛️ Latina",
}
RTL_LANGUAGES: set[str] = {"ar"}

# ── Supported Currencies ──────────────────────────────────────────────────────
CURRENCIES: dict[str, dict] = {
    "INR": {"symbol": "₹",  "name": "Indian Rupee",      "flag": "🇮🇳"},
    "USD": {"symbol": "$",  "name": "US Dollar",          "flag": "🇺🇸"},
    "EUR": {"symbol": "€",  "name": "Euro",               "flag": "🇪🇺"},
    "GBP": {"symbol": "£",  "name": "British Pound",      "flag": "🇬🇧"},
    "AED": {"symbol": "د.إ","name": "UAE Dirham",         "flag": "🇦🇪"},
    "CNY": {"symbol": "¥",  "name": "Chinese Yuan",       "flag": "🇨🇳"},
    "SGD": {"symbol": "S$", "name": "Singapore Dollar",   "flag": "🇸🇬"},
    "JPY": {"symbol": "¥",  "name": "Japanese Yen",       "flag": "🇯🇵"},
}

# ── Financial Model Defaults ──────────────────────────────────────────────────
DEFAULT_SPECIFIC_YIELD_P50  = 1550        # kWh/kWp/year  (typical Gujarat)
DEFAULT_CAPEX_PER_KWP       = 35_000      # ₹/kWp         (~₹3.5 Cr/MW)
DEFAULT_OPEX_PER_KWP        = 700         # ₹/kWp/year
DEFAULT_TARIFF              = 2.85        # ₹/kWh
DEFAULT_DEBT_FRACTION       = 0.70        # 70 % debt
DEFAULT_INTEREST_RATE       = 0.095       # 9.5 % p.a.
DEFAULT_LOAN_TENURE         = 15          # years
DEFAULT_TAX_RATE            = 0.25        # 25 %
DEFAULT_DISCOUNT_RATE       = 0.10        # 10 % WACC / equity hurdle
DEFAULT_OPEX_ESCALATION     = 0.03        # 3 % p.a.
DEFAULT_PROJECT_LIFE        = 25          # years

# ── Solar Performance ─────────────────────────────────────────────────────────
DEGRADATION_YEAR_1  = 0.02    # 2 % first-year degradation (Mono PERC)
DEGRADATION_ANNUAL  = 0.005   # 0.5 % subsequent years

P_FACTORS: dict[str, float] = {
    "P50": 1.000,
    "P75": 0.955,
    "P90": 0.910,
}

# ── Stripe Billing Plans ──────────────────────────────────────────────────────
STRIPE_PLANS: dict[str, dict] = {
    "free":       {"price_inr": 0,        "projects": 1,   "label": "Free"},
    "pro":        {"price_inr": 999,      "projects": 10,  "label": "Pro"},
    "enterprise": {"price_inr": 4_999,    "projects": -1,  "label": "Enterprise"},
}

# ── Compliance Categories ─────────────────────────────────────────────────────
COMPLIANCE_CATEGORIES = [
    "Nodal Agencies (SECI/MNRE)",
    "DISCOM / SLDC",
    "CEIG / Electrical Inspector",
    "Financial Institutions",
]
