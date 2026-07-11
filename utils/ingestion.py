"""
SolarPro — AutoLISP JSON Ingestion Module
Parses and validates JSON files exported from AutoLISP/SolarPro CAD.
"""
import json
from pathlib import Path
from typing import Any

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

    # Normalise keys to lowercase
    data = {k.lower(): v for k, v in raw.items()}

    valid, errors = validate_project_data(data)
    if not valid:
        raise ValueError(f"Invalid project JSON: {'; '.join(errors)}")

    # Fill optional fields with defaults
    for field, default in OPTIONAL_FIELDS.items():
        data.setdefault(field, default)

    # Derived fields
    if data.get("module_watt") is None and data["module_count"] > 0:
        data["module_watt"] = round(data["dc_capacity_kwp"] * 1000 / data["module_count"], 1)

    data["dc_capacity_kwp"] = float(data["dc_capacity_kwp"])
    data["module_count"]    = int(data["module_count"])
    data["tilt"]            = float(data["tilt"])

    return data


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
        "project_name":    "Rajkot Solar Phase 1",
        "location":        "Gujarat, India",
        "dc_capacity_kwp": 2500.0,
        "module_count":    5952,
        "tilt":            25,
        "gcr":             0.40,
        "module_watt":     420,
        "latitude":        22.3039,
        "longitude":       70.8022,
        "notes":           "Ground-mounted fixed-tilt, mono PERC modules",
    }


def summarise(data: dict) -> str:
    """Return a one-line project summary string."""
    return (
        f"{data.get('project_name','Project')} | "
        f"{data['dc_capacity_kwp']:.0f} kWp | "
        f"{data['module_count']:,} modules | "
        f"{data['tilt']}° tilt"
    )
