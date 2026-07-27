"""
Assemble everything into index.html. Run as the last step of the
GitHub Action, after the fetch scripts have produced their dicts.

Kept as plain string formatting rather than a templating engine --
one file, easy to read top to bottom, no extra dependency.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from config import (
    CAPE_REFERENCE, PWAT_REFERENCE, STEERING_REFERENCE,
    BOM_MSLP_CHART_URL, MJO_PHASE_GEOGRAPHY, MJO_REGION_RELEVANT_PHASES,
)
from fetch_mjo import fetch_mjo
from fetch_gfs import fetch_gfs
from fetch_tc import fetch_tc
from fetch_observations import fetch_observations, observation_submit_url
from synthesize import synthesize

LEVEL_STYLE = {
    "elevated": ("#fdf0e0", "#8a5a10", "Elevated"),
    "watch":    ("#fdf6d8", "#8a7a10", "Watch"),
    "low":      ("#e3f3e9", "#1e6b3e", "Low"),
}


def badge(level: str) -> str:
    bg, fg, label = LEVEL_STYLE.get(level, LEVEL_STYLE["watch"])
    return f'<span style="background:{bg};color:{fg};font-size:13px;padding:4px 10px;border-radius:6px">{label}</span>'


def reference_line(value, ref: dict, unit_label: str, higher_is_notable: bool = True) -> str:
    quiet = ref.get("quiet_max", ref.get("weak_max_kmh"))
    typical = ref.get("typical_max", ref.get("moderate_max_kmh"))
    return (f'<span style="color:#888;font-size:12px"> '
            f'(fair-weather ref: below {quiet} {unit_label} quiet, '
            f'{quiet}-{typical} {unit_label} typical)</span>')


def mjo_watch_list() -> str:
    """Small explanatory line: which phases are actually watched, and why."""
    parts = []
    for phase in sorted(MJO_REGION_RELEVANT_PHASES):
        parts.append(f"{phase} ({MJO_PHASE_GEOGRAPHY[phase]})")
    return "; ".join(parts)


def chart_block() -> str:
    return (
        f'<div>'
        f'<p style="font-size:13px;color:#888;margin:0 0 6px">'
        f'BOM Asia MSL pressure analysis (00Z) '
        f'<span style="color:#aaa">-- source: Bureau of Meteorology (Australia)</span></p>'
        f'<img src="{BOM_MSLP_CHART_URL}" alt="BOM Darwin MSLP analysis" '
        f'style="width:100%;max-width:640px;border:1px solid #ddd;border-radius:8px">'
        f'</div>'
    )


def observation_log_block(observations: list[dict]) -> str:
    if not observations:
        return '<p style="font-size:13px;color:#888">No observations logged yet.</p>'
    rows = []
    for obs in observations[:8]:
        rows.append(
            f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
            f'border-bottom:1px solid #eee;font-size:13px">'
            f'<span>{obs["date"]}</span>'
            f'<span style="color:#888">{obs["body"][:60] or obs["title"]}</span>'
            f'</div>'
        )
    return "\n".join(rows)


def build_html() -> str:
    mjo = fetch_mjo()
    tc = fetch_tc()
    gfs = fetch_gfs()
    verdict = synthesize(mjo, tc, gfs)
    observations = fetch_observations()

    now = datetime.now(timezone.utc)
    now_str = f'{now.strftime("%Y-%m-%d %H:%M")} UTC / {(now + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")} MYT'
    submit_url = observation_submit_url(now.strftime("%Y-%m-%d"))

    local = verdict["local"]
    organized = verdict["organized"]
    mjo_phase_desc = MJO_PHASE_GEOGRAPHY.get(mjo["phase"], "unknown")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>gapu-synoptic</title>
</head>
<body style="font-family:-apple-system,sans-serif;max-width:680px;margin:0 auto;padding:16px;color:#222">

<p style="font-size:12px;color:#888;margin:0 0 16px">Generated {now_str}</p>

<h1 style="font-size:20px;font-weight:600;margin:0 0 10px">{verdict["regime"]}</h1>

<div style="background:#f0f5fb;border-left:3px solid #1a6fc4;border-radius:6px;padding:12px 14px;margin:0 0 20px">
  <p style="font-size:14px;color:#123;margin:0;font-weight:500">{verdict["recommendation"]}</p>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0">
  <div style="border:1px solid #eee;border-radius:10px;padding:14px">
    <p style="font-size:13px;color:#888;margin:0 0 8px">Local diurnal risk</p>
    {badge(local["level"])}
    <p style="font-size:13px;color:#555;margin:10px 0 0">{local["note"]}</p>
  </div>
  <div style="border:1px solid #eee;border-radius:10px;padding:14px">
    <p style="font-size:13px;color:#888;margin:0 0 8px">Organized system risk</p>
    {badge(organized["level"])}
    <p style="font-size:13px;color:#555;margin:10px 0 0">{organized["note"]}</p>
  </div>
</div>

<details style="margin:20px 0">
  <summary style="cursor:pointer;font-size:13px;color:#888">Show the numbers behind this</summary>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0">
    <div style="background:#fafafa;border-radius:10px;padding:14px">
      <p style="font-size:13px;color:#888;margin:0 0 2px">Local convective outlook</p>
      <p style="font-size:11px;color:#aaa;margin:0 0 10px">source: NOAA GFS via Herbie -- cycle {gfs["cycle_myt"]} ({gfs["cycle"]}), valid {gfs["valid_time_myt"]} ({gfs["valid_time"]})</p>
      <table style="width:100%;font-size:13px;border-collapse:collapse">
        <tr><td style="color:#888;padding:4px 0">CAPE</td><td style="text-align:right">{gfs["cape_jkg"]:.0f} J/kg{reference_line(gfs["cape_jkg"], CAPE_REFERENCE, "J/kg")}</td></tr>
        <tr><td style="color:#888;padding:4px 0">Precipitable water</td><td style="text-align:right">{gfs["pwat_mm"]:.1f} mm{reference_line(gfs["pwat_mm"], PWAT_REFERENCE, "mm")}</td></tr>
        <tr><td style="color:#888;padding:4px 0">700-850hPa steering</td><td style="text-align:right">{gfs["steering_kmh"]:.0f} km/h{reference_line(gfs["steering_kmh"], STEERING_REFERENCE, "km/h")}</td></tr>
        <tr><td style="color:#888;padding:4px 0">MSLP</td><td style="text-align:right">{gfs["mslp_hpa"]:.1f} hPa</td></tr>
      </table>
    </div>
    <div style="background:#fafafa;border-radius:10px;padding:14px">
      <p style="font-size:13px;color:#888;margin:0 0 2px">Organized system outlook</p>
      <p style="font-size:11px;color:#aaa;margin:0 0 10px">source: MJO -- NOAA PSL ROMI ({mjo["date"]}) &middot; TC/TD -- GDACS</p>
      <table style="width:100%;font-size:13px;border-collapse:collapse">
        <tr><td style="color:#888;padding:4px 0">MJO phase</td><td style="text-align:right">{mjo["phase"]} -- {mjo_phase_desc}</td></tr>
        <tr><td style="color:#888;padding:4px 0">MJO amplitude</td><td style="text-align:right">{mjo["amplitude"]} (active if &ge;1.0)</td></tr>
        <tr><td style="color:#888;padding:4px 0">MJO region-relevant</td><td style="text-align:right">{"yes" if mjo["region_relevant"] else "no"}</td></tr>
        <tr><td style="color:#888;padding:4px 0">TC/TD status</td><td style="text-align:right">{tc["status"]}</td></tr>
      </table>
      <p style="font-size:11px;color:#aaa;margin:10px 0 0">Watched phases: {mjo_watch_list()}. Region-relevant needs BOTH an active amplitude (&ge;1.0) AND one of these phases -- an active MJO elsewhere on the globe doesn't count.</p>
    </div>
  </div>
</details>

<details style="margin:20px 0">
  <summary style="cursor:pointer;font-size:13px;color:#888">Synoptic chart</summary>
  <div style="margin-top:12px">{chart_block()}</div>
</details>

<div style="margin:20px 0">
  <p style="font-size:14px;font-weight:600;margin:0 0 2px">Recent outlook log</p>
  <p style="font-size:11px;color:#aaa;margin:0 0 10px">source: GitHub issues on this repo, labelled "observation"</p>
  {observation_log_block(observations)}
  <a href="{submit_url}" style="display:inline-block;margin-top:10px;font-size:13px;color:#1a6fc4">Log today's observation &#8599;</a>
</div>

<p style="font-size:11px;color:#aaa;margin-top:24px">
  GFS {gfs["cycle_myt"]} ({gfs["cycle"]}) &middot; MJO {mjo["date"]} &middot; TC/TD checked {now_str}
</p>

</body>
</html>
"""


if __name__ == "__main__":
    html = build_html()
    with open("index.html", "w") as f:
        f.write(html)
    print("wrote index.html")
