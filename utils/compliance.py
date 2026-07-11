"""
SolarPro — Statutory Compliance Checklist State Machine
Tracks 4 approval categories with item-level status, due dates, and owners.
"""
from __future__ import annotations
import streamlit as st
from datetime import date, timedelta

# ── Checklist Master Data ──────────────────────────────────────────────────────
CHECKLIST: dict[str, list[dict]] = {
    "Nodal Agencies (SECI/MNRE)": [
        {"id": "na_01", "item": "Letter of Award (LOA)",                "owner": "Developer",       "doc_required": True},
        {"id": "na_02", "item": "Power Purchase Agreement (PPA)",        "owner": "Developer / SECI","doc_required": True},
        {"id": "na_03", "item": "Land Lease / Ownership Documents",      "owner": "Developer",       "doc_required": True},
        {"id": "na_04", "item": "Grid Connectivity Approval (CTU/STU)",  "owner": "Developer / CTU", "doc_required": True},
        {"id": "na_05", "item": "Environmental Clearance (if >5 MW)",    "owner": "Developer / MoEF","doc_required": True},
    ],
    "DISCOM / SLDC": [
        {"id": "dc_01", "item": "Interconnection Agreement",             "owner": "DISCOM",          "doc_required": True},
        {"id": "dc_02", "item": "Metering & Billing Agreement",          "owner": "DISCOM",          "doc_required": True},
        {"id": "dc_03", "item": "Synchronisation Approval",              "owner": "SLDC",            "doc_required": False},
        {"id": "dc_04", "item": "Net Metering / Banking Application",    "owner": "DISCOM",          "doc_required": True},
    ],
    "CEIG / Electrical Inspector": [
        {"id": "ce_01", "item": "High Voltage (HV) Test Certificate",    "owner": "EPC Contractor",  "doc_required": True},
        {"id": "ce_02", "item": "Protection Relay Settings Approval",    "owner": "EPC / CEIG",      "doc_required": True},
        {"id": "ce_03", "item": "Commissioning Test Report",             "owner": "EPC Contractor",  "doc_required": True},
        {"id": "ce_04", "item": "Final Electrical Inspector Clearance",  "owner": "CEIG",            "doc_required": True},
    ],
    "Financial Institutions": [
        {"id": "fi_01", "item": "Lender's Engineer Report (LER)",        "owner": "Lender's Engineer","doc_required": True},
        {"id": "fi_02", "item": "Insurance Policies (ALOP/EAR/BI)",     "owner": "Developer / EPC", "doc_required": True},
        {"id": "fi_03", "item": "DSRA Account Funding",                  "owner": "Developer",       "doc_required": False},
        {"id": "fi_04", "item": "Financial Close Conditions Fulfilled",  "owner": "Developer / Bank","doc_required": True},
    ],
}

STATUS_OPTIONS = ["Pending", "In Progress", "Completed"]
STATUS_EMOJI   = {"Pending": "🟡", "In Progress": "🔵", "Completed": "🟢"}
STATUS_CLASS   = {"Pending": "badge-pending", "In Progress": "badge-progress", "Completed": "badge-completed"}


def _state_key(item_id: str, field: str) -> str:
    return f"compliance_{item_id}_{field}"


def init_compliance_state() -> None:
    """Initialise session state for all checklist items."""
    for _cat, items in CHECKLIST.items():
        for item in items:
            sk_status = _state_key(item["id"], "status")
            sk_due    = _state_key(item["id"], "due")
            if sk_status not in st.session_state:
                st.session_state[sk_status] = "Pending"
            if sk_due not in st.session_state:
                st.session_state[sk_due] = date.today() + timedelta(days=30)


def get_item_status(item_id: str) -> str:
    return st.session_state.get(_state_key(item_id, "status"), "Pending")


def get_item_due(item_id: str) -> date:
    return st.session_state.get(_state_key(item_id, "due"), date.today())


def set_item_status(item_id: str, status: str) -> None:
    st.session_state[_state_key(item_id, "status")] = status


def category_progress(category: str) -> tuple[int, int, float]:
    """Return (completed, total, pct) for a category."""
    items = CHECKLIST.get(category, [])
    total = len(items)
    completed = sum(1 for it in items if get_item_status(it["id"]) == "Completed")
    pct = completed / total if total > 0 else 0.0
    return completed, total, pct


def overall_progress() -> tuple[int, int, float]:
    """Return overall (completed, total, pct) across all categories."""
    total, completed = 0, 0
    for cat in CHECKLIST:
        c, t, _ = category_progress(cat)
        completed += c
        total += t
    pct = completed / total if total > 0 else 0.0
    return completed, total, pct


def export_checklist_csv() -> str:
    """Export checklist as CSV string."""
    import io, csv
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Category", "Item", "Owner", "Status", "Due Date"])
    for cat, items in CHECKLIST.items():
        for item in items:
            writer.writerow([
                cat, item["item"], item["owner"],
                get_item_status(item["id"]),
                get_item_due(item["id"]).isoformat(),
            ])
    return buf.getvalue()
