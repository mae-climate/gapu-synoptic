"""
Check for active tropical cyclones/depressions within TC_WATCH_RADIUS_KM
of the catchment, using GDACS (Global Disaster Alert and Coordination
System) rather than scraping a JTWC text bulletin.

Why the switch: the original JTWC-based version guessed at a bulletin
URL that was never confirmed working. GDACS is built for exactly this
kind of automated polling -- a real documented API returning structured
GeoJSON (actual lat/lon per event, not text to regex against), actively
maintained (confirmed live files updated within the last month at
gdacs.org/contentdata/xml/), and it's EU/JRC-run infrastructure, not a
single research group's personal webpage -- less likely to quietly go
stale the way the BOM/CAWCR MJO mirrors did.

Uses the `gdacs-api` package. Endpoint confirmed by reading the
package's own source (not guessed): 
    https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP

Caveat: the exact property key names GDACS uses for event name/alert
level (e.g. "eventname" vs "name") were inferred from GDACS's own
public RSS/KML examples, not confirmed against a live JSON response --
this sandbox can't reach gdacs.org. Extraction below tries several
plausible key names defensively and never crashes on an unexpected
schema; verify the "name"/"alert_level" fields look sane on first
real run.
"""

from __future__ import annotations

import math

from config import LAT, LON, TC_WATCH_RADIUS_KM


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _extract_system(feature: dict) -> dict | None:
    try:
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}
        coords = geom.get("coordinates")
        if not coords or len(coords) < 2:
            return None
        lon, lat = coords[0], coords[1]  # GeoJSON order is [lon, lat]
        distance_km = haversine_km(LAT, LON, lat, lon)

        name = (props.get("eventname") or props.get("name")
                or props.get("title") or props.get("htmldescription") or "unnamed")
        alert_level = props.get("alertlevel", "unknown")

        return {
            "name": str(name)[:80],
            "alert_level": alert_level,
            "distance_km": round(distance_km),
            "lat": lat,
            "lon": lon,
        }
    except Exception:
        return None


def fetch_tc() -> dict:
    try:
        from gdacs.api import GDACSAPIReader
        reader = GDACSAPIReader()
        result = reader.latest_events(event_type="TC")
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "unknown",
            "note": f"GDACS fetch failed ({exc}) -- check https://www.gdacs.org manually.",
            "systems": [],
        }

    nearby = []
    for feature in result.features:
        system = _extract_system(feature)
        if system and system["distance_km"] <= TC_WATCH_RADIUS_KM:
            nearby.append(system)

    if nearby:
        return {
            "status": "active_nearby",
            "note": f"{len(nearby)} system(s) within {TC_WATCH_RADIUS_KM} km -- verify against gdacs.org before treating as confirmed.",
            "systems": nearby,
        }
    return {"status": "clear", "note": "No active TC/TD within watch radius.", "systems": []}


if __name__ == "__main__":
    import json

    print(json.dumps(fetch_tc(), indent=2))
