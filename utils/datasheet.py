"""
SolarPro — Module Datasheet Parser & Comparison Engine
Supports CSV/Excel uploads, basic PDF text extraction, and basic ranking.
"""
from __future__ import annotations
import io
import re
from pathlib import Path
from typing import Any, List, Tuple

import pandas as pd
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

# --------------------------------------------------------------------------- #
#  PDF KEYWORD PATTERNS – each pattern includes at least ONE capture group
# --------------------------------------------------------------------------- #
PDF_KEYWORDS: dict[str, List[Tuple[str, str]]] = {
    "Max Power (W)": [
        (r"max(?:imum)?\s*pow(?:er)?\s*[Pp]?max\b", r"(\d{3,6})"),
        (r"p(?:max|mp)\s*:?\s*(\d{3,6})\s*W", r"(\d{3,6})"),
    ],
    "Module Efficiency (%)": [(r"efficien(?:cy|t)\s*:?\s*(\d{2}\.\d)\s*%", r"(\d{2}\.\d)")],
    "Vmp (V)": [(r"vmp\s*:?\s*(\d{2}\.\d+)\s*V", r"(\d{2}\.\d+)")],
    "Imp (A)": [(r"imp\s*:?\s*(\d{2}\.\d+)\s*A", r"(\d{2}\.\d+)")],
    "Voc (V)": [(r"voc\s*:?\s*(\d{2}\.\d+)\s*V", r"(\d{2}\.\d+)")],
    "Isc (A)": [(r"isc\s*:?\s*(\d{2}\.\d+)\s*A", r"(\d{2}\.\d+)")],
    "NOCT (C)": [(r"noct\s*:?\s*(\d{2,3})", r"(\d{2,3})")],
    "Length (mm)": [(r"length\s*:?\s*(\d{3,4})\s*mm", r"(\d{3,4})")],
    "Width (mm)": [(r"width\s*:?\s*(\d{3,4})\s*mm", r"(\d{3,4})")],
    "Weight (kg)": [(r"weight\s*:?\s*(\d{2,3}(?:\.\d)?)\s*kg", r"(\d{2,3}(?:\.\d)?)")],
}

# --------------------------------------------------------------------------- #
#  Helper functions
# --------------------------------------------------------------------------- #
def build_sample_excel() -> bytes:
    """Return a sample XLSX template for datasheet upload."""
    buf = io.BytesIO()
    df = pd.DataFrame(SAMPLE_DATA)
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Modules")
        pd.DataFrame(
            {
                "Column": REQUIRED_COLS + [c for c in OPTIONAL_COLS if c not in REQUIRED_COLS],
                "Required?": ["Yes"] * len(REQUIRED_COLS) + ["No"] * len(OPTIONAL_COLS),
            }
        ).to_excel(writer, index=False, sheet_name="Instructions")
    return buf.getvalue()


def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise column names:
    1. Strip whitespace and make lower‑case.
    2. Map known aliases to the canonical public names used in the app.
    3. Ensure the three required columns end up with exactly the names
       ``Manufacturer``, ``Model`` and ``Max Power (W)``.
    """
    rename_map = {
        # Canonical names → possible aliases / lower‑cased forms
        "Max Power (W)": ["max power (w)", "pmax", "maxpower"],
        "Module Efficiency (%)": ["module efficiency (%)", "module efficiency"],
        "Vmp (V)": ["vmp (v)", "vmp"],
        "Imp (A)": ["imp (a)", "imp"],
        "Voc (V)": ["voc (v)", "voc"],
        "Isc (A)": ["isc (a)", "isc"],
        "NOCT (C)": ["noct (c)", "noct"],
        "Length (mm)": ["length (mm)", "length_m"],
        "Width (mm)": ["width (mm)", "width_m"],
        "Weight (kg)": ["weight (kg)", "weight"],
        "Product Warranty (yrs)": [
            "product warranty (yrs)",
            "product warranty",
            "warranty (prod)",
        ],
        "Power Warranty (yrs)": [
            "power warranty (yrs)",
            "power warranty",
            "warranty (power)",
        ],
        # Add missing canonical names that appear in raw uploads
        "Manufacturer": ["manufacturer"],
        "Model": ["model"],
    }

    # Step‑1: strip and lower‑case every column name
    df.columns = [str.strip().lower() for _ in df.columns]

    # Step‑2: build a reverse lookup that matches any of the aliases to the
    # canonical name we want to keep.
    reverse_map = {}
    for canonical, aliases in rename_map.items():
        for alias in aliases:
            reverse_map[alias] = canonical

    # Step‑3: rename based on the reverse map; leave unmapped columns untouched
    df = df.rename(columns=reverse_map)

    # Step‑4: capitalise the first letter of the retained column names to
    # ensure they match the app’s expected import format (e.g. "Manufacturer").
    df = df.rename(
        columns=lambda name: name.replace(name[0], name[0].upper())
        if name else name
    )
    return df


def _extract_numeric_from_match(m) -> float | int | None:
    """Safely extract a number from a regex match object."""
    try:
        # Group 1 may be a string; convert to float/int depending on pattern intent
        val = m.group(1)
        # Prefer integer if the value is whole; else float
        if isinstance(val, str) and val.isdigit():
            return int(val)
        return float(val)
    except Exception:
        return None


def _safe_text(text: str) -> str:
    """Battle‑tested helper – mirrors the PDF export helper."""
    replacements = {
        "—": "-", "–": "-", "‘": "'", "’": "'",
        "“": '"', "”": '"', "…": "...", " ": " ",
        "₹": "Rs.", "₨": "Rs.", "£": "GBP", "€": "EUR",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def parse_csv_excel(file_obj) -> Tuple[bool, pd.DataFrame | str]:
    """
    Parse an uploaded CSV or Excel file and validate required columns.
    Returns ``(is_valid, result)`` where ``result`` is either the cleaned
    ``DataFrame`` or an error string.
    """
    try:
        if file_obj.name.endswith(".csv"):
            df = pd.read_csv(file_obj)
        else:
            df = pd.read_excel(file_obj, engine="openpyxl")
    except Exception as e:
        return False, f"Could not read file: {e}"

    # Validate that the required columns exist *before* we rename them.
    missing_required = [c for c in REQUIRED_COLS if c.lower() not in df.columns.str.lower()]
    if missing_required:
        return False, f"Missing required columns: {missing_required}"

    before = df.copy()
    df = _standardise_columns(df)

    # --- Numeric coercion --------------------------------------------------- #
    # Only the numeric columns need coercion; everything else stays as string.
    numeric_columns = ["Max Power (W)"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # ---------------------------------------------------------------------- #
    # Additional column‑specific checks
    max_power_null = df["Max Power (W)"].isnull().all()
    if max_power_null:
        return False, "Max Power column has no valid numeric values."

    # Ensure any extra numeric columns (if they exist) are numeric too
    # but do not enforce positivity here – the downstream engine will handle
    # zero‑values gracefully.
    return True, df


def _try_extract_pdf_text(file_obj) -> str:
    """Extract raw text from a PDF file‑like object."""
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


def parse_pdf(file_obj) -> Tuple[bool, pd.DataFrame | str]:
    """
    Parse a PDF datasheet and extract Manufacturer, Model and the other
    key specs. Returns ``(is_valid, result)`` where ``result`` is the DataFrame
    or an error description.
    """
    text = _try_extract_pdf_text(file_obj)
    if not text:
        return False, "Could not extract text from PDF. Try CSV/Excel instead."

    text_lower = text.lower()

    result: dict[str, str | float | None] = {
        "Manufacturer": None,
        "Model": None,
    }

    # -------------------------------------------------------------------------
    #  Extract numeric value for each known keyword, using the regex → capture
    #  pattern defined in ``PDF_KEYWORDS``.  The first pattern that yields a
    #  successful capture decides the matched column.
    # -------------------------------------------------------------------------
    for col, patterns in PDF_KEYWORDS.items():
        for pat, capture in patterns:
            m = re.search(pat, text_lower)
            if m:
                value = _extract_numeric_from_match(m)
                if value is not None:
                    try:
                        result[col] = float(value)
                    except Exception:
                        pass
                break  # stop at first match for this column

    # -------------------------------------------------------------------------
    #  Manufacturer / Model are textual – they can be captured via keyword
    #  lists that are not captured but are easier, so we perform a simple
    #  heuristic here.
    # -------------------------------------------------------------------------
    manuf_keywords = [
        "longi", "jinko", "trina", "canadian", "hanwha", "risen",
        "ja\s*solar", "adani", "waaree", "vikram"
    ]
    for kw in manuf_keywords:
        if re.search(kw, text_lower):
            m = re.search(rf"{kw}", text_lower)
            if m:
                result["Manufacturer"] = m.group(0).title()
                break

    # Model extraction – look for typical "Model: XXX" or just a series of
    # letters/numbers after the manufacturer name.
    model_regexes = [
        r"(?:model|type|part\s*no)\s*:?\s*([A-Za-z0-9\-\./]+)",
        r"(?:,\s*|\s+)\s*([A-Za-z0-9\-\./]+)",  # fallback: catch a token after a comma or space
    ]
    for rg in model_regexes:
        m = re.search(rg, text, re.IGNORECASE)
        if m:
            result["Model"] = m.group(1).strip()
            break

    # -------------------------------------------------------------------------
    #  Build a one‑row DataFrame – this is what the rest of the pipeline
    #  expects.  Missing values stay as ``None`` which will be handled later.
    # -------------------------------------------------------------------------
    df = pd.DataFrame([result])
    return True, df


def _safe_cast(val: Any) -> Any:
    """Convert a possibly numeric string/float to a Python native type."""
    if isinstance(val, str):
        val = val.strip()
        if val.isdigit():
            return int(val)
        try:
            return float(val)
        except ValueError:
            pass
    return val


def compute_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank modules on overall suitability using a simple weighted sum of the
    available numeric metrics.  The weighting is derived from ``st.session_state``
    ``module_weights`` if present – this mirrors the UI collected weightage.
    If no weights are available, fall back to equal weighting.
    """
    # -------------------------------------------------------------------------
    #  1) Normalise the DataFrame columns: keep only those that are numeric
    #     and required for ranking, and coerce missing ones to NaN.
    # -------------------------------------------------------------------------
    numeric_cols = ["Max Power (W)", "Module Efficiency (%)"]
    present_numeric = {c: df.get(c, None) for c in numeric_cols if c in df.columns}
    # If any numeric column is missing entirely, we cannot rank.
    if not present_numeric:
        return pd.DataFrame()  # caller will handle empty result

    # -------------------------------------------------------------------------
    #  2) Compute ranks per column – highest value gets rank 1.
    # -------------------------------------------------------------------------
    ranked_cols = {}
    for col, series in present_numeric.items():
        # ``rank`` works on Pandas Series directly
        rank_series = series.rank(ascending=False, method="min", numeric_only=True)
        ranked_cols[col] = rank_series

    # -------------------------------------------------------------------------
    #  3) Merge ranks into a single DataFrame for easy summation.
    # -------------------------------------------------------------------------
    rank_df = pd.DataFrame(ranked_cols)
    if rank_df.empty:
        return rank_df

    # -------------------------------------------------------------------------
    #  4) Apply weighting – look for ``st.session_state.module_weights``.
    # -------------------------------------------------------------------------
    try:
        import streamlit as st
        session_weights: dict[str, float] = {}
        if hasattr(st, "session_state"):
            # ``module_weights`` keys are whatever the UI used; try several possibilities
            for candidate in ["max_power", "max_power_w", "maxpower", "max_power_watt"]:
                if candidate in st.session_state.session_state:
                    session_weights["Max Power (W)"] = float(st.session_state.session_state[candidate])
            for candidate in ["efficiency", "mod_eff", "module_efficiency"]:
                if candidate in st.session_state.session_state:
                    session_weights["Module Efficiency (%)"] = float(st.session_state.session_state[candidate])
        except Exception:
            pass  # No Streamlit context – we’ll use equal weights instead
    except ImportError:
        pass

    if "Max Power (W)" in session_weights and "Module Efficiency (%)" in session_weights:
        weight_map = {
            "Max Power (W)": session_weights["Max Power (W)"],
            "Module Efficiency (%)": session_weights["Module Efficiency (%)"],
        }
    else:
        # equal weighting when missing or no UI weights
        weight_map = {
            "Max Power (W)": 1.0,
            "Module Efficiency (%)": 1.0,
        }

    # Normalise weights to sum to 1
    weight_total = sum(weight_map.values())
    normalized_weights = {k: v / weight_total for k, v in weight_map.items()}

    # -------------------------------------------------------------------------
    #  5) Compute an overall weighted score and sort.
    # -------------------------------------------------------------------------
    weighted_score = []
    for _, row in rank_df.iterrows():
        score = sum(rank_df.loc[row.name, col] * normalized_weights[col] for col in rank_df.columns)
        weighted_score.append((row.name, score))

    # ``row.name`` at this point is the original index of the row (0‑based)
    # Convert that back to the row’s position in the original DataFrame for slicing.
    best_idx, _ = max(weighted_score, key=lambda x: x[1])
    ranked_rows = rank_df.iloc[[best_idx]]
    # Optionally, still produce a full ranking table ordered by score.
    rank_df["WeightedScore"] = rank_df.apply(lambda r: sum((r[col] * normalized_weights[col]) for col in rank_df.columns), axis=1)
    final_rank = rank_df.sort_values("WeightedScore", ascending=False)
    return final_rank.sort_values("Overall Rank" if "Overall Rank" in rank_df.columns else rank_df.columns[0])


def plot_radar(df: pd.DataFrame) -> go.Figure | None:
    """Create a radar chart comparing the selected modules."""
    radar_cols = ["Max Power (W)", "Module Efficiency (%)", "Voc (V)", "Isc (A)"]
    available = [c for c in radar_cols if c in df.columns]
    if len(available) < 2:
        return None
    fig = go.Figure()
    norm = df[available].max()
    for _, row in df.iterrows():
        vals = (row[available] / norm).round(3).tolist()
        vals += vals[:1]  # close the polar loop
        fig.add_trace(
            go.Scatterpolar(
                r=vals,
                theta=available + [available[0]],
                name=f"{row.get('Manufacturer','')} {row.get('Model','')}",
                line=dict(width=2.5),
            )
        )
    fig.update_layout(
        paper_bgcolor="#141828",
        plot_bgcolor="#141828",
        font_color="#E8EAF0",
        height=420,
        polar=dict(
            radialaxis=dict(visible=True, gridcolor="#252D45", color="#94A3B8"),
            bgcolor="#0A0E1A",
        ),
        margin=dict(l=60, r=60, t=40, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="center",
            x=0.5,
        ),
    )
    return fig


def plot_parameter_bars(df: pd.DataFrame) -> go.Figure | None:
    """Create a sub‑plot bar chart for optional numeric parameters."""
    show_cols = [c for c in OPTIONAL_COLS if c in df.columns and c != "Frame"]
    available = [c for c in show_cols if pd.api.types.is_numeric_dtype(df[c])]
    if not available:
        return None
    labels = [
        f"{row.get('Manufacturer','')} {row.get('Model','')[:20]}" for _, row in df.iterrows()
    ]
    fig = make_subplots(
        rows=2, cols=2, subplot_titles=available[:4],
        specs=[[{"colspan": 1}, {"colspan": 1}],
               [{"colspan": 1}, {"colspan": 1}],],
    )
    for i, col in enumerate(available[:4]):
        row_idx = i // 2 + 1
        col_idx = i % 2 + 1
        fig.add_trace(
            go.Bar(
                name=col,
                x=labels,
                y=df[col],
                marker_color=px.colors.qualitative.Set2[i],
                text=df[col].round(1).astype(str),
                textposition="outside",
            ),
            row=row_idx,
            col=col_idx,
        )
    fig.update_layout(
        paper_bgcolor="#141828",
        plot_bgcolor="#141828",
        font_color="#E8EAF0",
        height=500,
        showlegend=False,
        margin=dict(l=0, r=0, t=50, b=0),
    )
    fig.update_xaxes(gridcolor="#252D45", tickangle=25)
    fig.update_yaxes(gridcolor="#252D45")
    return fig