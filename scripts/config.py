"""
Shared config for gapu-synoptic.

This is the 24-36h regime-outlook layer -- separate from cloudwatch
(Himawari nowcasting, 0-2h) and separate from Gapu Floodwatch (the
community-facing app). Answers "which risk regime is favoured for
tomorrow", not "what's happening right now".
"""

from __future__ import annotations

# --- Location ----------------------------------------------------------
# Point used for GFS extraction. Kolopis/Penampang area.
LAT = 5.93
LON = 116.13

# --- MJO ----------------------------------------------------------------
# BOM's own "real-time" RMM file (and its CAWCR mirror) turned out to be
# stale -- confirmed dead by direct browser check, July 2026. Using
# NOAA PSL's ROMI (Real-time OLR MJO Index) instead -- confirmed current
# via direct browser check (last row: 2026-07-22, days old, actually live).
# ROMI is NOT the same index as RMM (OLR-only vs. OLR+winds), so its PC1/
# PC2 need a documented sign/order flip before phase math -- see
# fetch_mjo.py for the conversion and how it was verified.
MJO_URL = "https://psl.noaa.gov/mjo/mjoindex/romi.cpcolr.1x.txt"
MJO_ACTIVE_AMPLITUDE = 1.0
# Phases where the enhanced-convection envelope sits over the Maritime
# Continent (Indonesia/Malaysia/Philippines longitude band) -- this is
# the "does an active MJO actually matter for Sabah" filter. Phase alone
# or amplitude alone is not enough; both conditions must hold.
MJO_REGION_RELEVANT_PHASES = {3, 4, 5, 6}

# For display -- what each phase actually means geographically. Phases 4-5
# are the Maritime Continent core; 3 and 6 are included as approach/exit
# since the envelope is ~45 degrees wide and doesn't switch on and off
# cleanly at a phase boundary.
MJO_PHASE_GEOGRAPHY = {
    1: "Africa / western Indian Ocean",
    2: "Indian Ocean (approaching)",
    3: "Indian Ocean (approaching Maritime Continent)",
    4: "Maritime Continent (core -- Indonesia/Malaysia/Philippines)",
    5: "Maritime Continent (core, eastern side)",
    6: "Western Pacific (still-relevant exit)",
    7: "Western Pacific (departed)",
    8: "Atlantic / Africa (departed)",
}

# --- Tropical cyclone / depression watch --------------------------------
# JTWC (Western Pacific/Indian Ocean AOR) is the primary source. The
# exact "list all active systems in one file" URL was not confirmed
# against a live fetch when this was built (network-restricted sandbox)
# -- see fetch_tc.py docstring for what IS confirmed vs. best-guess.
TC_WATCH_RADIUS_KM = 1200

# --- GFS / Herbie ---------------------------------------------------------
GFS_PRODUCT = "pgrb2.0p25"
GFS_FORECAST_HOURS = (24, 36)  # the window we actually care about

# --- Fair-weather reference bands ----------------------------------------
# Rough climatological bands for this coast, NOT a computed baseline yet.
# CAPE and PWAT are persistently substantial in the deep tropics -- these
# bands are deliberately generous, meant to catch genuinely anomalous
# readings, not flag every ordinary day. Replace with an empirical
# baseline (mean CAPE/PWAT/steering on logged dry vs. flood days) once
# the observation log has enough entries -- see fetch_observations.py.
CAPE_REFERENCE = {"quiet_max": 1000, "typical_max": 2000, "unit": "J/kg"}
PWAT_REFERENCE = {"quiet_max": 45, "typical_max": 55, "unit": "mm"}
# Steering wind band is NOT generic -- it's your own documented range
# from OCR'd Ventusky readings during a confirmed quasi-stationary event
# (July 21 2026: 2-14 mph / roughly 3-22 km/h across 700-850 hPa).
STEERING_REFERENCE = {"weak_max_kmh": 22, "moderate_max_kmh": 40, "unit": "km/h"}

# --- Chart embeds ---------------------------------------------------------
# BOM Darwin/Asia MSLP analysis (00Z) -- confirmed working direct image
# URL as of build time (fetched and verified live).
BOM_MSLP_CHART_URL = "https://www.bom.gov.au/fwo/IDD80100.png"
# JMA ASAS Asia-Pacific surface chart -- the monthly PDF archive path
# structure is confirmed, but the *current/latest* chart's direct URL
# was not confirmed against a live fetch. Verify at first deploy and
# fill in, or drop this embed if no stable current-chart URL exists.
JMA_ASAS_CHART_URL = None

# --- GitHub (for the observation log) --------------------------------------
GITHUB_REPO = "mae-climate/gapu-synoptic"
OBSERVATION_LABEL = "observation"

# --- HTTP headers -----------------------------------------------------------
# Several sources (confirmed: BOM, and GitHub's API is documented to require
# this) reject requests with no identifying User-Agent, treating a bare
# Python requests-library header as a bot. A normal browser-style UA clears
# this everywhere it's been an issue so far.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
