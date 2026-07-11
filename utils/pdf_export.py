"""
SolarPro — FPDF2 PDF Report Generator
Produces a branded, multi-language, multi-section PDF report.
Arabic uses arabic-reshaper + python-bidi for proper RTL rendering.
"""
from __future__ import annotations
import io
from pathlib import Path
from datetime import date
from fpdf import FPDF
import pandas as pd
from config import APP_NAME, APP_VERSION
from utils.i18n import t, is_rtl

# ── Color Palette ────────────────────────────────────────────────────────────
C_DARK   = (10,  14,  26)
C_CARD   = (20,  24,  40)
C_TEAL   = (0,   212, 170)
C_PURPLE = (108, 99,  255)
C_TEXT   = (232, 234, 240)
C_MUTED  = (148, 163, 184)
C_WHITE  = (255, 255, 255)


def _reshape_arabic(text: str) -> str:
    """Reshape and apply BiDi algorithm for Arabic text."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except ImportError:
        return text


def _safe_text(text: str, lang: str) -> str:
    if lang == "ar":
        return _reshape_arabic(str(text))
    return str(text)


class SolarReport(FPDF):
    def __init__(self, lang: str = "en"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.lang = lang
        self.rtl = is_rtl(lang)
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(18, 18, 18)
        self._load_fonts()

    def _load_fonts(self):
        """Use built-in Helvetica (ASCII) — DejaVu for full Unicode if available."""
        self.set_font("Helvetica", size=10)

    # ── Header / Footer ──────────────────────────────────────────────────────
    def header(self):
        self.set_fill_color(*C_DARK)
        self.rect(0, 0, 210, 18, "F")
        self.set_y(4)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*C_TEAL)
        self.cell(0, 10, f"{APP_NAME} v{APP_VERSION}", align="L")
        self.set_text_color(*C_MUTED)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 10, f"Generated {date.today().isoformat()}", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-14)
        self.set_fill_color(*C_DARK)
        self.rect(0, 283, 210, 14, "F")
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*C_MUTED)
        self.cell(0, 10, f"Page {self.page_no()} | Confidential — {APP_NAME}", align="C")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _h1(self, text: str):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*C_TEAL)
        self.cell(0, 10, _safe_text(text, self.lang), ln=True)
        self.set_draw_color(*C_TEAL)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), 195, self.get_y())
        self.ln(4)

    def _h2(self, text: str):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*C_PURPLE)
        self.cell(0, 8, _safe_text(text, self.lang), ln=True)
        self.ln(2)

    def _body(self, text: str, size: int = 10):
        self.set_font("Helvetica", "", size)
        self.set_text_color(*C_TEXT)
        self.multi_cell(0, 6, _safe_text(text, self.lang))
        self.ln(2)

    def _metric_row(self, label: str, value: str, color=None):
        self.set_fill_color(*C_CARD)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*C_MUTED)
        self.cell(90, 8, _safe_text(label, self.lang), fill=True, border=0)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*(color or C_TEAL))
        self.cell(80, 8, _safe_text(value, self.lang), fill=True, border=0, ln=True)
        self.ln(1)

    # ── Sections ──────────────────────────────────────────────────────────────
    def cover_page(self, project: dict):
        self.add_page()
        self.set_fill_color(*C_DARK)
        self.rect(0, 0, 210, 297, "F")
        # Logo image (if available)
        logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
        if logo_path.exists():
            self.image(str(logo_path), x=65, y=28, w=80)
            self.set_y(70)
        else:
            self.set_y(60)
        # Big title
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*C_TEAL)
        self.cell(0, 14, APP_NAME, align="C", ln=True)
        self.set_font("Helvetica", "", 13)
        self.set_text_color(*C_MUTED)
        self.cell(0, 8, "Financial Modelling Report", align="C", ln=True)
        self.ln(12)
        # Project box
        self.set_fill_color(*C_CARD)
        self.rect(30, self.get_y(), 150, 60, "F")
        self.set_y(self.get_y() + 8)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*C_WHITE)
        self.cell(0, 8, project.get("project_name", "Solar Project"), align="C", ln=True)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*C_MUTED)
        self.cell(0, 7, f"Capacity: {project.get('dc_capacity_kwp', 0):.0f} kWp", align="C", ln=True)
        self.cell(0, 7, f"Location: {project.get('location', 'India')}", align="C", ln=True)
        self.cell(0, 7, f"Modules: {project.get('module_count', 0):,}  |  Tilt: {project.get('tilt', 0)}deg", align="C", ln=True)
        self.cell(0, 7, f"Report Date: {date.today().strftime('%d %B %Y')}", align="C", ln=True)
        self.set_y(240)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*C_MUTED)
        self.cell(0, 6, "CONFIDENTIAL — For investment decision purposes only.", align="C", ln=True)

    def executive_summary(self, metrics: dict, currency: str = "INR"):
        self.add_page()
        self._h1("Executive Summary")
        self._h2("Key Financial Metrics")
        irr   = metrics.get("equity_irr", 0)
        lcoe  = metrics.get("lcoe", 0)
        npv   = metrics.get("npv", 0)
        payback = metrics.get("payback", "N/A")
        dscr  = metrics.get("min_dscr", 0)
        self._metric_row("Equity IRR",       f"{irr*100:.2f}%" if irr else "N/A")
        self._metric_row("Project IRR",      f"{metrics.get('project_irr',0)*100:.2f}%")
        self._metric_row("LCOE",             f"{lcoe:.3f} INR/kWh")
        self._metric_row("NPV (Equity)",     f"INR {npv/1e7:.2f} Cr")
        self._metric_row("Payback Period",   f"{payback} years" if payback else "N/A")
        self._metric_row("Min DSCR",         f"{dscr:.2f}x" if dscr else "N/A")
        self._metric_row("Total CAPEX",      f"INR {metrics.get('capex',0)/1e7:.2f} Cr")
        self._metric_row("Equity Component", f"INR {metrics.get('equity',0)/1e7:.2f} Cr")
        self._metric_row("Debt Component",   f"INR {metrics.get('debt',0)/1e7:.2f} Cr")

    def sensitivity_table(self, sensitivity: dict):
        self.add_page()
        self._h1("P50 / P75 / P90 Sensitivity Analysis")
        self._body("The following table shows financial performance under three probabilistic yield scenarios.")
        # Header row
        self.set_fill_color(*C_CARD)
        self.set_text_color(*C_TEAL)
        self.set_font("Helvetica", "B", 10)
        for col in ["Scenario", "Equity IRR", "Project IRR", "LCOE (INR/kWh)", "NPV (Cr)", "Payback (yr)"]:
            self.cell(32, 8, col, border=1, fill=True)
        self.ln()
        self.set_text_color(*C_TEXT)
        self.set_font("Helvetica", "", 10)
        for scenario, m in sensitivity.items():
            irr  = f"{m['equity_irr']*100:.2f}%" if m.get("equity_irr") else "N/A"
            pirr = f"{m['project_irr']*100:.2f}%" if m.get("project_irr") else "N/A"
            lcoe = f"{m['lcoe']:.3f}"             if m.get("lcoe") else "N/A"
            npv  = f"{m['npv']/1e7:.2f}"          if m.get("npv") else "N/A"
            pb   = str(m.get("payback") or "N/A")
            row_color = C_CARD if scenario == "P50" else C_DARK
            self.set_fill_color(*row_color)
            for val in [scenario, irr, pirr, lcoe, npv, pb]:
                self.cell(32, 7, val, border=1, fill=True)
            self.ln()

    def cashflow_table(self, df: pd.DataFrame):
        self.add_page()
        self._h1("25-Year Cash Flow Summary")
        cols = ["Year", "Revenue_INR", "OPEX_INR", "EBITDA_INR", "Equity_FCF_INR", "DSCR"]
        labels = ["Yr", "Revenue (INR)", "OPEX (INR)", "EBITDA (INR)", "Equity FCF (INR)", "DSCR"]
        widths = [12, 34, 30, 34, 36, 22]
        # Header
        self.set_fill_color(*C_CARD)
        self.set_text_color(*C_TEAL)
        self.set_font("Helvetica", "B", 8)
        for lbl, w in zip(labels, widths):
            self.cell(w, 7, lbl, border=1, fill=True)
        self.ln()
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*C_TEXT)
        for _, row in df.iterrows():
            fill = row["Year"] % 2 == 0
            self.set_fill_color(*(C_CARD if fill else C_DARK))
            vals = [
                str(int(row["Year"])),
                f"{row['Revenue_INR']/1e5:.1f}L",
                f"{row['OPEX_INR']/1e5:.1f}L",
                f"{row['EBITDA_INR']/1e5:.1f}L",
                f"{row['Equity_FCF_INR']/1e5:.1f}L",
                f"{row['DSCR']:.2f}",
            ]
            for val, w in zip(vals, widths):
                self.cell(w, 6, val, border=1, fill=True)
            self.ln()

    def assumptions_page(self, params: dict):
        self.add_page()
        self._h1("Model Assumptions")
        self._body("All financial projections are based on the following assumptions:")
        for k, v in params.items():
            self._metric_row(k, str(v), C_MUTED)
        self.ln(4)
        self._body(
            "DISCLAIMER: This report is generated by SolarPro Financial and is intended for "
            "informational purposes only. It does not constitute financial advice. Actual results "
            "may vary materially from projections due to changes in tariff, yield, and market conditions.",
            size=8,
        )


def generate_report(
    project: dict,
    metrics_p50: dict,
    sensitivity: dict,
    df_cashflows: pd.DataFrame,
    params: dict,
    lang: str = "en",
    currency: str = "INR",
) -> bytes:
    """Generate a complete PDF report and return as bytes."""
    pdf = SolarReport(lang=lang)
    pdf.cover_page(project)
    pdf.executive_summary(metrics_p50, currency)
    pdf.sensitivity_table(sensitivity)
    pdf.cashflow_table(df_cashflows)
    pdf.assumptions_page(params)
    return bytes(pdf.output())
