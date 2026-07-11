"""SolarPro — Geocoding via OpenStreetMap Nominatim API
Provides location search and reverse geocoding.
"""
from __future__ import annotations
import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "SolarProFinancial/1.0"


def search_location(query: str, limit: int = 5) -> list[dict]:
    """Search for a location and return list of {display_name, lat, lon}."""
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": limit, "addressdetails": 0},
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            return [
                {
                    "display_name": item.get("display_name", query),
                    "lat": float(item["lat"]),
                    "lon": float(item["lon"]),
                }
                for item in data
                if "lat" in item and "lon" in item
            ]
    except Exception:
        pass
    return []


def reverse_geocode(lat: float, lon: float) -> str:
    """Return a display name for a lat/lon pair."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        if resp.status_code == 200:
            return resp.json().get("display_name", f"{lat:.4f}, {lon:.4f}")
    except Exception:
        pass
    return f"{lat:.4f}, {lon:.4f}"
