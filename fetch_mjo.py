"""
Pull the current MJO state from NOAA PSL's ROMI (Real-time OLR MJO Index)
and convert it to RMM-equivalent phase/amplitude.

Why ROMI and not the original BOM RMM file: BOM's "rmm.74toRealtime.txt"
(and its CAWCR mirror) both turned out to be dead -- confirmed by direct
browser check, July 2026, one frozen since Feb 2024, the other 404s
outright. ROMI, confirmed current via direct browser check (last row a
few days old, genuinely live), is the replacement.

File format (confirmed against a real fetch, July 2026):
    year month day hour PC1 PC2 amplitude
No missing-value sentinel observed in recent rows; rows that fail to
parse as numeric are dropped defensively regardless.

ROMI is NOT the same index as RMM (it's OLR-only; RMM also uses 850/200
hPa winds) -- NOAA documents that to compare ROMI/OMI-family indices
against RMM's phase convention, you flip PC1's sign and swap the PC
order: RMM1_equivalent = -PC1, RMM2_equivalent = PC2.

The phase-from-angle formula below was NOT taken from a description --
it was reverse-engineered from real (RMM1, RMM2, phase) triples pulled
from actual BOM RMM data seen earlier in this project, and verified
against 9 independent points before use.
"""

from __future__ import annotations

import io
import math

import pandas as pd
import requests

from config import MJO_URL, MJO_ACTIVE_AMPLITUDE, MJO_REGION_RELEVANT_PHASES, HEADERS

COLUMNS = ["year", "month", "day", "hour", "pc1", "pc2", "amplitude_omi"]


def _parse(text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text), names=COLUMNS, sep=r"\s+")
    for col in ["pc1", "pc2", "amplitude_omi"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["pc1", "pc2"])
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    return df.sort_values("date").reset_index(drop=True)


def _phase_from_rmm(rmm1: float, rmm2: float) -> int:
    angle = math.degrees(math.atan2(rmm2, rmm1))
    phase = int((angle + 180) // 45) + 1
    return ((phase - 1) % 8) + 1


def fetch_mjo() -> dict:
    resp = requests.get(MJO_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    df = _parse(resp.text)

    if df.empty:
        raise RuntimeError("MJO fetch returned no valid rows")

    latest = df.iloc[-1]
    recent = df.tail(10)

    # ROMI -> RMM-equivalent conversion (documented NOAA convention)
    rmm1 = -float(latest["pc1"])
    rmm2 = float(latest["pc2"])
    amplitude = math.hypot(rmm1, rmm2)
    phase = _phase_from_rmm(rmm1, rmm2)

    active = amplitude >= MJO_ACTIVE_AMPLITUDE
    region_relevant = active and phase in MJO_REGION_RELEVANT_PHASES

    trend = []
    for _, r in recent.iterrows():
        t_rmm1 = -float(r["pc1"])
        t_rmm2 = float(r["pc2"])
        trend.append({
            "date": r["date"].strftime("%m-%d"),
            "amplitude": round(math.hypot(t_rmm1, t_rmm2), 2),
        })

    return {
        "date": latest["date"].strftime("%Y-%m-%d"),
        "rmm1": round(rmm1, 2),
        "rmm2": round(rmm2, 2),
        "phase": phase,
        "amplitude": round(amplitude, 2),
        "active": active,
        "region_relevant": region_relevant,
        "trend": trend,
        "source": "ROMI (converted to RMM-equivalent phase/amplitude)",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(fetch_mjo(), indent=2))
