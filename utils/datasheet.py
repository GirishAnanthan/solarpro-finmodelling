"""SolarPro — Module Datasheet Parser & Comparison Engine
Supports CSV/Excel uploads and basic PDF text extraction.
"""
from __future__ import annotations
import io
import re
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

REQUIRED_COLS = ["Manufacturer", "Model", "Max Power (W)"]
OPTIONAL_COLS = [
    "Module Efficiency (%)", "Vmp (V)", "Imp (A)", "Voc (V)", "Isc (A)",
    "Pmax Temp Coeff (%/C)", "Voc Temp Coeff (%/C)", "Isc Temp Coeff (%/C)",
    "NOCT (C)", "Length (mm)", "Width (mm)", "Weight (kg)",
    "Product Warranty (yrs)", "Power Warranty (yrs)", "Frame",
]

SAMPLE_DATA = [
    {"Manufacturer": "Longi", "Model": "HiMO7 LR7-72HGD 580W", "Max Power (W)": 580, "Module Efficiency (%)": 22.5, "Vmp (V)": 43.2, "Imp (A)": 13.43, "Voc (V)": 51.8, "Isc (A)": 14.12, "Pmax Temp Coeff (%/C)": -0.29, "Voc Temp Coeff (%/C)": -0.24, "Isc Temp Coeff (%/C)": 0.05, "NOCT (C)": 45, "Length (mm)": 2278, "Width (mm)": 1134, "Weight (kg)": 28.5, "Product Warranty (yrs)": 25, "Power Warranty (yrs)": 30, "Frame": "Anodized Aluminium"},
    {"Manufacturer": "JinkoSolar", "Model": "Tiger Neo N-type 585W", "Max Power (W)": 585, "Module Efficiency (%)": 22.9, "Vmp (V)": 43.8, "Imp (A)": 13.36, "Voc (V)": 52.1, "Isc (A)": 14.24, "Pmax Temp Coeff (%/C)": -0.30, "Voc Temp Coeff (%/C)": -0.25, "Isc Temp Coeff (%/C)": 0.06, "NOCT (C)": 44, "Length (mm)": 2278, "Width (mm)": 1134, "Weight (kg)": 27.8, "Product Warranty (yrs)": 25, "Power Warranty (yrs)": 30, "Frame": "Anodized Aluminium"},
    {"Manufacturer": "Trina Solar", "Model": "Vertex N EG-585N", "Max Power (W)": 585, "Module Efficiency (%)": 22.7, "Vmp (V)": 43.5, "Imp (A)": 13.45, "Voc (V)": 52.0, "Isc (A)": 14.18, "Pmax Temp Coeff (%/C)": -0.29, "Voc Temp Coeff (%/C)": -0.24, "Isc Temp Coeff (%/C)": 0.05, "NOCT (C)": 44, "Length (mm)": 2278, "Width (mm)": 1134, "Weight (kg)": 28.0, "Product Warranty (yrs)": 25, "Power Warranty (yrs)": 30, "Frame": "Anodized Aluminium"},
]

PDF_KEYWORDS: dict[str, list[str]] = {
    "Max Power (W)": [r"max(?:imum)?\s*pow(?:er)?\s*[Pp]?max\b", r"p(?:max|mp)\s*:?\s*(\d{3,4})\s*W"],
    "Module Efficiency (%)": [r"efficien(?:cy|t)\s*:?\s*(\d{2}\.\d)\s*%"],
    "Vmp (V)": [r"vmp\s*:?\s*(\d{2}\.\d+)\s*V"],
    "Imp (A)": [r"imp\s*:?\s*(\d{2}\.\d+)\s*A"],
    "Voc (V)": [r"voc\s*:?\s*(\d{2}\.\d+)\s*V"],
    "Isc (A)": [r"isc\s*:?\s*(\d{2}\.\d+)\s*A"],
    "NOCT (C)": [r"noct\s*:?\s*(\d{2,3})"],
    "Length (mm)": [r"length\s*:?\s*(\d{3,4})\s*mm"],
    "Width (mm)": [r"width\s*:?\s*(\d{3,4})\s*mm"],
    "Weight (kg)": [r"weight\s*:?\s*(\d{2,3}(?:\.\d)?)\s*kg"],
}


def build_sample_excel() -> bytes:
    buf = io.BytesIO()
    df = pd.DataFrame(SAMPLE_DATA)
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Modules")
        pd.DataFrame({
            "Column": REQUIRED_COLS + [c for c in OPTIONAL_COLS if c not in REQUIRED_COLS],
            "Required?": ["Yes"] * len(REQUIRED_COLS) + ["No"] * len(OPTIONAL_COLS),
        }).to_excel(writer, index=False, sheet_name="Instructions")
    return buf.getvalue()


def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "max power (w)": "Max Power (W)", "pmax": "Max Power (W)", "module efficiency (%)": "Module Efficiency (%)",
        "vmp (v)": "Vmp (V)", "imp (a)": "Imp (A)", "voc (v)": "Voc (V)", "isc (a)": "Isc (A)",
        "noct (c)": "NOCT (C)", "length (mm)": "Length (mm)", "width (mm)": "Width (mm)", "weight (kg)": "Weight (kg)",
        "product warranty (yrs)": "Product Warranty (yrs)", "power warranty (yrs)": "Power Warranty (yrs)",
    }
    df = df.rename(columns=str.strip).rename(columns=str.lower)
    return df.rename(columns=rename_map)


def parse_csv_excel(file_obj) -> tuple[bool, pd.DataFrame | str]:
    try:
        if file_obj.name.endswith(".csv"):
            df = pd.read_csv(file_obj)
        else:
            df = pd.read_excel(file_obj, engine="openpyxl")
    except Exception as e:
        return False, f"Could not read file: {e}"
    df = _standardise_columns(df)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        return False, f"Missing required columns: {missing}"
    for c in REQUIRED_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df[REQUIRED_COLS[0]].isnull().all():
        return False, "Max Power column has no valid numeric values."
    return True, df


def _try_extract_pdf_text(file_obj) -> str:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts)
    except Exception:
        try:
            import fitz
            doc = fitz.open(stream=file_obj.read(), filetype="pdf")
            text_parts = [page.get_text() for page in doc]
            return "\n".join(text_parts)
        except Exception:
            return ""


def parse_pdf(file_obj) -> tuple[bool, pd.DataFrame | str]:
    text = _try_extract_pdf_text(file_obj)
    if not text:
        return False, "Could not extract text from PDF. Try CSV/Excel instead."
    text_lower = text.lower()
    result: dict[str, str | float | None] = {
        "Manufacturer": None, "Model": None,
    }
    for col, patterns in PDF_KEYWORDS.items():
        for pat in patterns:
            m = re.search(pat, text_lower)
            if m:
                try:
                    result[col] = float(m.group(1))
                except (ValueError, IndexError):
                    pass
                break
    try:
        m_name = re.search(r"(longi|jinko|trina|canadian|hanwha|q\.?cells|risen|ja\s*solar|adani|waaree|vikram)", text_lower)
        if m_name:
            result["Manufacturer"] = m_name.group(1).title()
    except Exception:
        pass
    try:
        m_model = re.search(r"(?:model|type|part\s*no)\s*:?\s*([\w\-\.]+)", text, re.IGNORECASE)
        if m_model:
            result["Model"] = m_model.group(1).strip()
    except Exception:
        pass
    df = pd.DataFrame([result])
    return True, df


def compute_ranking(df: pd.DataFrame) -> pd.DataFrame:
    ranked = df.copy()
    numeric_cols = ["Max Power (W)", "Module Efficiency (%)"]
    for col in numeric_cols:
        if col in ranked.columns:
            ranked[f"{col} Rank"] = ranked[col].rank(ascending=False, method="min").astype(int)
    rank_cols = [c for c in ranked.columns if "Rank" in c]
    if rank_cols:
        ranked["Overall Rank"] = ranked[rank_cols].sum(axis=1).rank(method="min").astype(int)
    return ranked.sort_values("Overall Rank" if "Overall Rank" in ranked.columns else ranked.columns[0])


def plot_radar(df: pd.DataFrame) -> go.Figure:
    radar_cols = ["Max Power (W)", "Module Efficiency (%)", "Voc (V)", "Isc (A)"]
    available = [c for c in radar_cols if c in df.columns]
    if len(available) < 2:
        return None
    fig = go.Figure()
    norm = df[available].max()
    for _, row in df.iterrows():
        vals = (row[available] / norm).round(3).tolist()
        vals += vals[:1]
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=available + [available[0]],
            name=f"{row.get('Manufacturer','')} {row.get('Model','')}",
            line=dict(width=2.5),
        ))
    fig.update_layout(
        paper_bgcolor="#141828", plot_bgcolor="#141828",
        font_color="#E8EAF0", height=420,
        polar=dict(
            radialaxis=dict(visible=True, gridcolor="#252D45", color="#94A3B8"),
            bgcolor="#0A0E1A",
        ),
        margin=dict(l=60, r=60, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
    )
    return fig


def plot_parameter_bars(df: pd.DataFrame) -> go.Figure:
    show_cols = [c for c in OPTIONAL_COLS if c in df.columns and c != "Frame"]
    available = [c for c in show_cols if pd.api.types.is_numeric_dtype(df[c])]
    if not available:
        return None
    labels = [f"{r.get('Manufacturer','')} {r.get('Model','')[:20]}" for _, r in df.iterrows()]
    fig = make_subplots(rows=2, cols=2, subplot_titles=available[:4])
    for i, col in enumerate(available[:4]):
        row_idx = i // 2 + 1
        col_idx = i % 2 + 1
        fig.add_trace(go.Bar(
            name=col, x=labels, y=df[col],
            marker_color=px.colors.qualitative.Set2[i],
            text=df[col].round(1).astype(str),
            textposition="outside",
        ), row=row_idx, col=col_idx)
    fig.update_layout(
        paper_bgcolor="#141828", plot_bgcolor="#141828",
        font_color="#E8EAF0", height=500, showlegend=False,
        margin=dict(l=0, r=0, t=50, b=0),
    )
    fig.update_xaxes(gridcolor="#252D45", tickangle=25)
    fig.update_yaxes(gridcolor="#252D45")
    return fig
