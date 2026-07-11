"""
SolarPro — Financial Engine
Computes 25-year cash flows, Equity IRR, Project IRR, LCOE, NPV, DSCR, Payback.
Runs P50 / P75 / P90 sensitivity scenarios using numpy-financial.
"""
from __future__ import annotations
import numpy as np
import numpy_financial as npf
import pandas as pd
from config import (
    DEGRADATION_YEAR_1, DEGRADATION_ANNUAL, P_FACTORS, DEFAULT_PROJECT_LIFE,
    DEFAULT_SPECIFIC_YIELD_P50, DEFAULT_CAPEX_PER_KWP, DEFAULT_OPEX_PER_KWP,
    DEFAULT_TARIFF, DEFAULT_DEBT_FRACTION, DEFAULT_INTEREST_RATE,
    DEFAULT_LOAN_TENURE, DEFAULT_TAX_RATE, DEFAULT_DISCOUNT_RATE, DEFAULT_OPEX_ESCALATION,
)

YEARS = list(range(1, DEFAULT_PROJECT_LIFE + 1))

# ── ToD Default Slot Definition ───────────────────────────────────────────────
# Solar generation typically falls: ~80% in normal/shoulder, ~5% in peak (evening),
# ~15% in off-peak (early morning). Adjust per project location / state SERC order.
DEFAULT_TOD_SLOTS: dict[str, dict] = {
    "Peak"      : {"hours": "18:00–22:00", "tariff_mult": 1.40, "gen_pct": 0.05},
    "Normal"    : {"hours": "08:00–18:00", "tariff_mult": 1.00, "gen_pct": 0.80},
    "Off-Peak"  : {"hours": "22:00–08:00", "tariff_mult": 0.75, "gen_pct": 0.15},
}


def compute_blended_tariff(base_tariff: float, tod_slots: dict | None) -> float:
    """
    Compute a generation-weighted blended tariff from ToD slots.
    Each slot: {tariff_mult: float, gen_pct: float}
    If tod_slots is None, returns base_tariff unchanged.
    """
    if not tod_slots:
        return base_tariff
    blended = sum(
        base_tariff * slot["tariff_mult"] * slot["gen_pct"]
        for slot in tod_slots.values()
    )
    # Normalise in case gen_pct values don't sum to exactly 1.0
    total_pct = sum(s["gen_pct"] for s in tod_slots.values())
    return blended / total_pct if total_pct > 0 else base_tariff


def _generation_profile(dc_kwp: float, specific_yield_p50: float, p_factor: float) -> list[float]:
    """Annual generation kWh for 25 years with degradation."""
    gen = []
    yield_base = specific_yield_p50 * p_factor
    for yr in YEARS:
        if yr == 1:
            factor = 1 - DEGRADATION_YEAR_1
        else:
            factor = (1 - DEGRADATION_YEAR_1) * ((1 - DEGRADATION_ANNUAL) ** (yr - 1))
        gen.append(dc_kwp * yield_base * factor)
    return gen


def _debt_schedule(capex: float, debt_fraction: float, interest_rate: float, tenure: int) -> tuple[list, list, list]:
    """Simple annuity debt schedule. Returns (principal_repaid, interest_paid, outstanding)."""
    principal = capex * debt_fraction
    annual_payment = npf.pmt(interest_rate, tenure, -principal)
    outstanding = []
    interest_paid = []
    principal_repaid = []
    bal = principal
    for yr in YEARS:
        if yr <= tenure:
            int_pay = bal * interest_rate
            prin_pay = annual_payment - int_pay
            bal -= prin_pay
            bal = max(bal, 0.0)
        else:
            int_pay = 0.0
            prin_pay = 0.0
        outstanding.append(max(bal, 0.0))
        interest_paid.append(int_pay)
        principal_repaid.append(prin_pay)
    return principal_repaid, interest_paid, outstanding


def build_cashflows(
    dc_kwp:          float = 2500.0,
    specific_yield:  float = DEFAULT_SPECIFIC_YIELD_P50,
    p_factor:        float = 1.0,
    capex_per_kwp:   float = DEFAULT_CAPEX_PER_KWP,
    opex_per_kwp:    float = DEFAULT_OPEX_PER_KWP,
    tariff:          float = DEFAULT_TARIFF,
    debt_fraction:   float = DEFAULT_DEBT_FRACTION,
    interest_rate:   float = DEFAULT_INTEREST_RATE,
    loan_tenure:     int   = DEFAULT_LOAN_TENURE,
    tax_rate:        float = DEFAULT_TAX_RATE,
    opex_escalation: float = DEFAULT_OPEX_ESCALATION,
    discount_rate:   float = DEFAULT_DISCOUNT_RATE,
    tod_slots:       dict | None = None,
) -> pd.DataFrame:
    """Return a 25-row DataFrame with full annual cash flow model."""
    # Apply ToD blending to effective tariff
    effective_tariff = compute_blended_tariff(tariff, tod_slots)
    capex = dc_kwp * capex_per_kwp  # total ₹
    equity = capex * (1 - debt_fraction)

    gen = _generation_profile(dc_kwp, specific_yield, p_factor)
    prin_repaid, int_paid, outstanding = _debt_schedule(capex, debt_fraction, interest_rate, loan_tenure)

    rows = []
    for i, yr in enumerate(YEARS):
        revenue = gen[i] * effective_tariff
        opex    = dc_kwp * opex_per_kwp * ((1 + opex_escalation) ** (yr - 1))
        ebitda  = revenue - opex
        ebit    = ebitda - int_paid[i]
        tax     = max(ebit * tax_rate, 0.0)
        pat     = ebit - tax
        # Project-level FCF (pre-financing)
        project_fcf = ebitda - tax
        # Equity FCF
        equity_fcf = pat - prin_repaid[i]
        # DSCR
        dscr = ebitda / (prin_repaid[i] + int_paid[i]) if (prin_repaid[i] + int_paid[i]) > 0 else 99.0
        # Discounted equity FCF
        pv_factor = 1 / ((1 + discount_rate) ** yr)
        rows.append({
            "Year":            yr,
            "Generation_kWh":  round(gen[i], 0),
            "Revenue_INR":     round(revenue, 0),
            "OPEX_INR":        round(opex, 0),
            "EBITDA_INR":      round(ebitda, 0),
            "Interest_INR":    round(int_paid[i], 0),
            "Tax_INR":         round(tax, 0),
            "PAT_INR":         round(pat, 0),
            "Debt_Repaid_INR": round(prin_repaid[i], 0),
            "Equity_FCF_INR":  round(equity_fcf, 0),
            "Project_FCF_INR": round(project_fcf, 0),
            "DSCR":            round(dscr, 2),
            "PV_Equity_FCF":   round(equity_fcf * pv_factor, 0),
            "Debt_Outstanding":round(outstanding[i], 0),
        })
    return pd.DataFrame(rows)


def compute_metrics(df: pd.DataFrame, capex: float, dc_kwp: float, debt_fraction: float, discount_rate: float) -> dict:
    """Compute scalar KPIs from a cash flow DataFrame."""
    equity = capex * (1 - debt_fraction)

    # Equity IRR: initial outflow = equity, then annual equity FCF
    equity_flows = [-equity] + df["Equity_FCF_INR"].tolist()
    eq_irr = npf.irr(equity_flows)

    # Project IRR: initial outflow = total CAPEX, then project FCF
    project_flows = [-capex] + df["Project_FCF_INR"].tolist()
    proj_irr = npf.irr(project_flows)

    # NPV of equity cash flows
    npv_val = npf.npv(discount_rate, equity_flows)

    # LCOE = Total PV of costs / Total PV of generation
    total_pv_costs = capex  # year-0 capex
    total_pv_gen   = 0.0
    for _, row in df.iterrows():
        pv = 1 / ((1 + discount_rate) ** row["Year"])
        total_pv_costs += (row["OPEX_INR"] + row["Interest_INR"] + row["Tax_INR"] + row["Debt_Repaid_INR"]) * pv
        total_pv_gen   += row["Generation_kWh"] * pv
    lcoe = total_pv_costs / total_pv_gen if total_pv_gen > 0 else 0.0

    # Simple payback (cumulative undiscounted equity FCF)
    cumulative = 0.0
    payback_yr = None
    for _, row in df.iterrows():
        cumulative += row["Equity_FCF_INR"]
        if cumulative >= equity and payback_yr is None:
            payback_yr = row["Year"]

    # Min DSCR
    min_dscr = df["DSCR"].replace(99.0, np.nan).min()

    return {
        "equity_irr":   eq_irr,
        "project_irr":  proj_irr,
        "npv":          npv_val,
        "lcoe":         lcoe,
        "payback":      payback_yr,
        "min_dscr":     min_dscr,
        "capex":        capex,
        "equity":       equity,
        "debt":         capex * debt_fraction,
    }


def run_sensitivity(
    dc_kwp: float,
    specific_yield: float,
    capex_per_kwp: float,
    opex_per_kwp: float,
    tariff: float,
    debt_fraction: float,
    interest_rate: float,
    loan_tenure: int,
    tax_rate: float,
    opex_escalation: float,
    discount_rate: float,
    tod_slots: dict | None = None,
) -> dict[str, dict]:
    """Run P50, P75, P90 scenarios. Returns dict of {scenario: metrics}."""
    results = {}
    for scenario, pf in P_FACTORS.items():
        df = build_cashflows(
            dc_kwp=dc_kwp, specific_yield=specific_yield, p_factor=pf,
            capex_per_kwp=capex_per_kwp, opex_per_kwp=opex_per_kwp,
            tariff=tariff, debt_fraction=debt_fraction, interest_rate=interest_rate,
            loan_tenure=loan_tenure, tax_rate=tax_rate, opex_escalation=opex_escalation,
            discount_rate=discount_rate, tod_slots=tod_slots,
        )
        capex = dc_kwp * capex_per_kwp
        metrics = compute_metrics(df, capex, dc_kwp, debt_fraction, discount_rate)
        metrics["cashflow_df"] = df
        results[scenario] = metrics
    return results
