# gapu-synoptic

24-36h regime outlook for the Moyog catchment (Penampang/Kota Kinabalu,
Sabah) -- separate from `cloudwatch` (Himawari nowcasting, 0-2h) and
from Gapu Floodwatch (the community-facing app).

Answers one question: **is tomorrow more likely to bring locally-forced
diurnal convection (your Jun 16/30-type flash-flood risk), an organized
regional system (your Sept 2025-type risk), or neither?** These aren't
collapsed into one number on purpose -- your own documented events show
local risk is highest exactly when organized-system forcing is weakest,
so blending them into a single score would hide the distinction that
actually matters.

## One-time setup

1. Push this repo to GitHub as `gapu-synoptic`.
2. Settings -> Pages -> Source: "GitHub Actions".
3. That's it. The workflow runs on its own schedule from here on --
   nothing else needs your hands after this first push.

## What's verified vs. not

Built without live network access to most of these sources (sandboxed
dev environment), so treat this list as what to actually check on first
run rather than assume works:

- **MJO fetch** -- URL and column format confirmed against BOM's
  documented structure; parsing logic not run against a live download.
- **GFS/Herbie** -- `herbie-data` installs cleanly and its API matches
  what's used here; the actual GRIB field pulls were not run against a
  live GFS file. `cfgrib`/`eccodes` import with no extra system
  packages needed (confirmed) -- no `apt-get` step required in the
  workflow.
- **TC/TD (JTWC)** -- confirmed the per-storm URL pattern is real; the
  consolidated "all active systems" bulletin URL is a best guess with a
  fallback path, not a confirmed working link. Check `fetch_tc.py`'s
  docstring before trusting this panel.
- **BOM MSLP chart** -- confirmed working, fetched live during build:
  `https://www.bom.gov.au/fwo/IDD80100.png`
- **JMA ASAS chart** -- archive structure confirmed, current/live chart
  URL not confirmed. `JMA_ASAS_CHART_URL` is `None` in config.py until
  that's found and filled in.

First run: check the Action's log for each fetch step, fix whichever of
the above turns out wrong, re-run.

## Fair-weather reference bands

CAPE/PWAT/steering bands in `config.py` are rough climatological
placeholders, not a computed baseline -- deep-tropical CAPE and PWAT are
substantial most days, so these are set to catch genuinely anomalous
readings rather than flag every ordinary afternoon. The steering-wind
band is the one exception: it's drawn directly from your own documented
Ventusky readings during a confirmed quasi-stationary event, not a
textbook number.

Once the observation log (see below) has a few months of entries,
replace these bands with an actual computed baseline: mean CAPE/PWAT/
steering on your logged dry days vs. logged flood days. The log is the
training data for that upgrade.

## Observation log

The "log today's observation" link on the page opens a pre-filled
GitHub issue (labelled `observation`) -- no backend, no login beyond
GitHub itself. Each build reads recent issues with that label back in
and shows them under "recent outlook log", so over time you get a real
verdict-vs-actual track record.

## Next

- Extend `synthesize.py`'s local-diurnal check with moisture convergence,
  not just CAPE + steering, once that field's confirmed working.
- ITCZ (OLR-based visual check) and IOD (slow-moving seasonal context) --
  deliberately left out of this first pass; add once MJO/TC/GFS are
  confirmed working end to end.
