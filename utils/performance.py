"""
SolarPro — Performance Variance Module
Uploads monthly XLSX, computes actual vs projected variance and performance metrics.
"""
from __future__ import annotations
import io
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


REQUIRED_COLUMNS = {"Month", "Projected_kWh", "Actual_kWh"}
MONTHS_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

ROOT_CAUSE_RULES = {
    "Soiling Loss":      lambda v: v < -5.0,
    "Grid Curtailment":  lambda v: v < -8.0,
    "Inverter Trip":     lambda v: v < -12.0,
    "Excellent Output":  lambda v: v > 5.0,
}


def load_generation_excel(file_obj) -> tuple[bool, pd.DataFrame | str]:
    """Load and validate monthly generation XLSX. Returns (ok, df_or_error_str)."""
    try:
        df = pd.read_excel(file_obj, engine="openpyxl")
    except Exception as e:
        return False, f"Could not read file: {e}"

    df.columns = df.columns.str.strip()
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return False, f"Missing columns: {missing}. Expected: {REQUIRED_COLUMNS}"

    df["Projected_kWh"] = pd.to_numeric(df["Projected_kWh"], errors="coerce")
    df["Actual_kWh"]    = pd.to_numeric(df["Actual_kWh"],    errors="coerce")
    if df[["Projected_kWh","Actual_kWh"]].isnull().any().any():
        return False, "Non-numeric values found in Projected_kWh or Actual_kWh columns."

    return True, df


def compute_variance(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich DataFrame with variance and root-cause flag columns."""
    df = df.copy()
    df["Variance_kWh"]  = df["Actual_kWh"] - df["Projected_kWh"]
    df["Variance_pct"]  = (df["Variance_kWh"] / df["Projected_kWh"].replace(0, np.nan)) * 100
    df["Cumul_Actual"]  = df["Actual_kWh"].cumsum()
    df["Cumul_Project"] = df["Projected_kWh"].cumsum()

    flags = []
    for _, row in df.iterrows():
        v = row["Variance_pct"]
        flagged = [name for name, fn in ROOT_CAUSE_RULES.items() if fn(v)]
        flags.append(", ".join(flagged) if flagged else "—")
    df["Root_Cause"] = flags
    return df


def summary_stats(df: pd.DataFrame) -> dict:
    """Return aggregate performance statistics."""
    total_proj   = df["Projected_kWh"].sum()
    total_actual = df["Actual_kWh"].sum()
    variance_pct = ((total_actual - total_proj) / total_proj * 100) if total_proj > 0 else 0.0
    pr_estimate  = min(total_actual / total_proj, 1.0) if total_proj > 0 else 0.0
    best_month   = df.loc[df["Variance_pct"].idxmax(), "Month"]
    worst_month  = df.loc[df["Variance_pct"].idxmin(), "Month"]
    return {
        "total_projected":   total_proj,
        "total_actual":      total_actual,
        "total_variance_pct":variance_pct,
        "pr_estimate":       pr_estimate,
        "best_month":        best_month,
        "worst_month":       worst_month,
    }


def plot_generation_chart(df: pd.DataFrame) -> go.Figure:
    """Dual-bar chart: Projected vs Actual generation with variance line."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        name="Projected", x=df["Month"], y=df["Projected_kWh"],
        marker_color="#6C63FF", opacity=0.8,
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        name="Actual", x=df["Month"], y=df["Actual_kWh"],
        marker_color="#00D4AA", opacity=0.9,
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        name="Variance %", x=df["Month"], y=df["Variance_pct"],
        mode="lines+markers", line=dict(color="#F59E0B", width=2.5),
        marker=dict(size=7),
    ), secondary_y=True)
    fig.update_layout(
        paper_bgcolor="#141828", plot_bgcolor="#141828",
        font_color="#E8EAF0", barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=40, b=0),
        height=380,
    )
    fig.update_yaxes(title_text="Generation (kWh)", secondary_y=False, gridcolor="#252D45")
    fig.update_yaxes(title_text="Variance (%)", secondary_y=True, gridcolor="#252D45")
    return fig


def plot_cumulative_chart(df: pd.DataFrame) -> go.Figure:
    """Cumulative actual vs projected generation."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name="Cumulative Projected", x=df["Month"], y=df["Cumul_Project"],
        line=dict(color="#6C63FF", width=2, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        name="Cumulative Actual", x=df["Month"], y=df["Cumul_Actual"],
        line=dict(color="#00D4AA", width=2.5),
        fill="tonexty", fillcolor="rgba(0,212,170,0.08)",
    ))
    fig.update_layout(
        paper_bgcolor="#141828", plot_bgcolor="#141828",
        font_color="#E8EAF0", height=300,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    fig.update_xaxes(gridcolor="#252D45")
    fig.update_yaxes(gridcolor="#252D45")
    return fig


def build_sample_excel() -> bytes:
    """Return a sample XLSX as bytes for demo download."""
    months = MONTHS_ORDER
    proj   = [220000, 180000, 210000, 240000, 260000, 230000, 215000, 225000, 210000, 235000, 200000, 215000]
    actual = [218000, 172000, 208000, 237000, 258000, 219000, 202000, 223000, 211000, 236000, 198000, 216000]
    df = pd.DataFrame({"Month": months, "Projected_kWh": proj, "Actual_kWh": actual})
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()
