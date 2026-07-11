"""SolarPro — Project Ingestion Module
Parses AutoLISP JSON and provides form-based project builder.
"""
import json
from pathlib import Path
from typing import Any
from config import DEFAULT_PROJECT

REQUIRED_FIELDS: dict[str, type] = {
    "dc_capacity_kwp": (int, float),
    "module_count":    (int,),
    "tilt":            (int, float),
}

OPTIONAL_FIELDS: dict[str, Any] = {
    "project_name": "Unnamed Project",
    "location":     "Unknown Location",
    "latitude":     None,
    "longitude":    None,
    "gcr":          0.40,
    "module_watt":  None,
    "row_spacing_m": None,
    "notes":        "",
}


def _to_float(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def build_project_from_form(form: dict) -> dict:
    """Build a project dict from form inputs, computing derived fields."""
    proj = DEFAULT_PROJECT.copy()
    for k, v in form.items():
        if v is not None and v != "":
            proj[k] = v
    dc_mw = _to_float(form.get("dc_capacity_mw", 0))
    ac_mw = _to_float(form.get("ac_capacity_mw", 0))
    proj["dc_capacity_mw"] = dc_mw
    proj["ac_capacity_mw"] = ac_mw
    proj["dc_capacity_kwp"] = dc_mw * 1000
    proj["dc_ac_ratio"] = round(dc_mw / ac_mw, 3) if ac_mw > 0 else 0.0
    module_w = _to_float(form.get("module_watt", 0))
    if module_w > 0 and proj["dc_capacity_kwp"] > 0:
        proj["module_count"] = int(round(proj["dc_capacity_kwp"] * 1000 / module_w))
    for lat_field in ("latitude", "longitude"):
        if isinstance(proj.get(lat_field), str):
            try:
                proj[lat_field] = float(proj[lat_field])
            except (ValueError, TypeError):
                proj[lat_field] = None
    return proj


def parse_autolisp_json(file_obj) -> dict:
    """
    Parse an AutoLISP-exported JSON file object (or path).
    Returns a cleaned, typed dict.
    Raises ValueError on schema failures.
    """
    if isinstance(file_obj, (str, Path)):
        with open(file_obj, "r", encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = json.load(file_obj)

    data = {k.lower(): v for k, v in raw.items()}

    valid, errors = validate_project_data(data)
    if not valid:
        raise ValueError(f"Invalid project JSON: {'; '.join(errors)}")

    for field, default in OPTIONAL_FIELDS.items():
        data.setdefault(field, default)

    if data.get("module_watt") is None and data["module_count"] > 0:
        data["module_watt"] = round(data["dc_capacity_kwp"] * 1000 / data["module_count"], 1)

    data["dc_capacity_kwp"] = float(data["dc_capacity_kwp"])
    data["module_count"]    = int(data["module_count"])
    data["tilt"]            = float(data["tilt"])

    proj = DEFAULT_PROJECT.copy()
    proj.update(data)
    proj["dc_capacity_mw"] = proj["dc_capacity_kwp"] / 1000
    return proj


def validate_project_data(data: dict) -> tuple[bool, list[str]]:
    """Return (is_valid, list_of_errors)."""
    errors: list[str] = []
    for field, expected_types in REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"Missing field: '{field}'")
        elif not isinstance(data[field], expected_types):
            errors.append(f"'{field}' must be {expected_types}, got {type(data[field]).__name__}")
        elif isinstance(data[field], (int, float)) and data[field] <= 0:
            errors.append(f"'{field}' must be positive, got {data[field]}")

    if "tilt" in data and isinstance(data["tilt"], (int, float)):
        if not (0 <= data["tilt"] <= 90):
            errors.append(f"'tilt' must be 0-90°, got {data['tilt']}")

    return (len(errors) == 0, errors)


def build_sample_json() -> dict:
    """Return a sample project dict for demo purposes."""
    return {
        "customer_name":     "Gujarat Solar Development Corp",
        "project_name":      "Rajkot Solar Phase 1",
        "location":          "Rajkot, Gujarat, India",
        "latitude":          22.3039,
        "longitude":         70.8022,
        "ac_capacity_mw":    2.0,
        "dc_capacity_mw":    2.5,
        "dc_capacity_kwp":   2500.0,
        "dc_ac_ratio":       1.25,
        "mounting_structure":"Fixed Tilt",
        "tilt":              25,
        "azimuth":           180,
        "gcr":               0.40,
        "module_technology": "Mono PERC (p-type)",
        "module_manufacturer": "Longi",
        "module_model":      "HiMO7 LR7-72HGD 580W",
        "module_watt":       420,
        "module_count":      5952,
        "specific_yield_estimate": 1550,
        "estimated_tariff":  2.85,
        "notes":             "Ground-mounted fixed-tilt, mono PERC modules",
    }


def summarise(data: dict) -> str:
    """Return a one-line project summary string."""
    return (
        f"{data.get('project_name','Project')} | "
        f"{data['dc_capacity_kwp']:.0f} kWp | "
        f"{data.get('module_count', 0):,} modules | "
        f"{data.get('mounting_structure', '—')}"
    )
