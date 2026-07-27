"""
Turn the three raw fetches (MJO, TC/TD, GFS) into the two independent
verdicts the page actually shows: local diurnal risk, and organized
system risk. Deliberately kept as two axes, not one blended score --
see README for why (local risk peaks exactly when organized risk is
lowest, per the documented June 2026 events).
"""

from __future__ import annotations

from config import CAPE_REFERENCE, PWAT_REFERENCE, STEERING_REFERENCE


def local_diurnal_verdict(gfs: dict) -> dict:
    cape = gfs["cape_jkg"]
    steering = gfs["steering_kmh"]

    weak_steering = steering <= STEERING_REFERENCE["weak_max_kmh"]
    decent_instability = cape >= CAPE_REFERENCE["quiet_max"]

    if weak_steering and decent_instability:
        level = "elevated"
        note = (f"Steering {steering:.0f} km/h (weak, cells could anchor) with "
                 f"CAPE {cape:.0f} J/kg -- matches your Jun 16 / Jun 30 setup.")
    elif weak_steering and not decent_instability:
        level = "watch"
        note = f"Steering weak ({steering:.0f} km/h) but CAPE low ({cape:.0f} J/kg) -- limited fuel even if something tries to form."
    elif not weak_steering and decent_instability:
        level = "watch"
        note = f"CAPE supportive ({cape:.0f} J/kg) but steering {steering:.0f} km/h -- anything that forms likely moves through rather than sits."
    else:
        level = "low"
        note = f"Steering {steering:.0f} km/h, CAPE {cape:.0f} J/kg -- neither ingredient favours a locally-anchored cell."

    return {"level": level, "note": note}


def organized_system_verdict(mjo: dict, tc: dict) -> dict:
    tc_active = tc["status"] == "active_nearby"
    mjo_relevant = mjo["region_relevant"]

    if tc_active:
        level = "elevated"
        note = "Active system flagged near the region -- read the JTWC advisory directly, this needs a human look."
    elif mjo_relevant:
        level = "elevated"
        note = f"MJO active (amplitude {mjo['amplitude']}) in phase {mjo['phase']} -- enhanced-convection envelope over the Maritime Continent."
    elif mjo["active"]:
        level = "low"
        note = f"MJO active (amplitude {mjo['amplitude']}) but phase {mjo['phase']} -- envelope elsewhere, not over this region right now."
    else:
        level = "low"
        note = f"MJO amplitude {mjo['amplitude']} (below 1.0, considered inactive), no active TC/TD nearby."

    return {"level": level, "note": note}


def regime_label(local: dict, organized: dict) -> str:
    if organized["level"] == "elevated" and local["level"] == "elevated":
        return "Compound setup -- both locally-forced and organized-system ingredients present"
    if organized["level"] == "elevated":
        return "Organized/regional system favoured -- September 2025-type risk profile"
    if local["level"] == "elevated":
        return "Locally-forced diurnal convection favoured -- Jun 16/30-type risk profile"
    if local["level"] == "watch":
        return "Marginal local convective setup -- worth a closer look, not a clear signal either way"
    return "Quiet -- neither regime strongly favoured"


def recommendation(local: dict, organized: dict) -> str:
    """The actual 'so what do I do' sentence -- this is what most days
    should only need reading, with everything else as backup evidence."""
    if organized["level"] == "elevated" and local["level"] == "elevated":
        return ("Two independent drivers pointing the same way today -- worth checking "
                "both this page and Himawari more than once through the day.")
    if organized["level"] == "elevated":
        return ("Regional signal, not a local-catchment one -- this is about wider "
                "basin/landslide risk more than a sharp flash flood at your gate. "
                "Check back as the day develops.")
    if local["level"] == "elevated":
        return ("Ingredients match your Jun 16/30 setup -- treat afternoon onward as an "
                "active watch window, keep Himawari/radar open once cloud starts building.")
    if local["level"] == "watch":
        return ("No strong signal either way right now -- nothing demanding attention yet, "
                "but check again in a few hours rather than writing today off.")
    return "Nothing elevated on either axis -- no action needed based on this page alone."


def synthesize(mjo: dict, tc: dict, gfs: dict) -> dict:
    local = local_diurnal_verdict(gfs)
    organized = organized_system_verdict(mjo, tc)
    return {
        "local": local,
        "organized": organized,
        "regime": regime_label(local, organized),
        "recommendation": recommendation(local, organized),
    }
