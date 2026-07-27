"""
Pull the relevant GFS fields for the local-convective-outlook panel:
CAPE, precipitable water, 700/850 hPa steering wind, and MSLP -- at the
Kolopis/Penampang point, for the 24-36h forecast window.

Uses Herbie (https://herbie.readthedocs.io) against NOAA's public GFS
mirror. Not tested against a live download in this sandbox (network
restricted to a package-index allowlist) -- the GRIB search strings
below follow standard NCEP GFS pgrb2 field naming, which is stable and
well documented, but worth a first-run check regardless.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from config import LAT, LON, GFS_PRODUCT, GFS_FORECAST_HOURS


def _latest_gfs_cycle(now: datetime | None = None) -> datetime:
    """GFS runs at 00/06/12/18Z; pick the most recent complete cycle,
    with a couple hours of buffer for the model to actually finish.

    Returns a naive datetime (no tzinfo) -- Herbie expects this and
    implicitly treats it as UTC. Passing a timezone-aware datetime
    causes an internal TypeError inside Herbie's own date-comparison
    code (confirmed against a real run, not a guess)."""
    now = (now or datetime.now(timezone.utc)).replace(
        minute=0, second=0, microsecond=0, tzinfo=None
    )
    buffered = now - timedelta(hours=3)
    cycle_hour = (buffered.hour // 6) * 6
    return buffered.replace(hour=cycle_hour)


def _nearest_point(ds, lat: float, lon: float):
    lon_0_360 = lon % 360  # GFS longitude grid is 0-360, not -180/180
    return ds.sel(latitude=lat, longitude=lon_0_360, method="nearest")


def _fetch_field(cycle, fxx: int, search: str, var: str) -> float:
    from herbie import Herbie

    H = Herbie(cycle, model="gfs", product=GFS_PRODUCT, fxx=fxx)
    ds = H.xarray(search)
    point = _nearest_point(ds, LAT, LON)
    return float(point[var].values)


def fetch_gfs() -> dict:
    cycle = _latest_gfs_cycle()
    fxx = GFS_FORECAST_HOURS[0]  # lead time in hours for the snapshot below
    valid = cycle + timedelta(hours=fxx)

    cape = _fetch_field(cycle, fxx, ":CAPE:surface", "cape")
    pwat = _fetch_field(cycle, fxx, ":PWAT:entire atmosphere", "pwat")
    u850 = _fetch_field(cycle, fxx, ":UGRD:850 mb", "u")
    v850 = _fetch_field(cycle, fxx, ":VGRD:850 mb", "v")
    u700 = _fetch_field(cycle, fxx, ":UGRD:700 mb", "u")
    v700 = _fetch_field(cycle, fxx, ":VGRD:700 mb", "v")
    mslp_pa = _fetch_field(cycle, fxx, ":PRMSL:mean sea level", "prmsl")

    speed_850_ms = float(np.hypot(u850, v850))
    speed_700_ms = float(np.hypot(u700, v700))
    steering_kmh = round((speed_850_ms + speed_700_ms) / 2 * 3.6, 1)

    myt_offset = timedelta(hours=8)

    return {
        "cycle": cycle.strftime("%Y-%m-%d %HZ"),
        "cycle_myt": (cycle + myt_offset).strftime("%Y-%m-%d %H:%M MYT"),
        "forecast_hour": fxx,
        "valid_time": valid.strftime("%Y-%m-%d %HZ"),
        "valid_time_myt": (valid + myt_offset).strftime("%Y-%m-%d %H:%M MYT"),
        "cape_jkg": round(cape, 0),
        "pwat_mm": round(pwat, 1),
        "steering_kmh": steering_kmh,
        "mslp_hpa": round(mslp_pa / 100, 1),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(fetch_gfs(), indent=2))
