# BiCRS Atlas

An interactive map overlaying **biomass feedstock supply**, **CO₂ storage options**, and a
**best-use-of-biomass recommendation** per region — grounded in Frontier's BiCRS purchasing POV.

## Open it

Double-click **`src/index.html`** (or open it in any browser). No server, no build step, works
offline — all data is bundled as JavaScript.

## What you can do

- **Region scope** switcher — one map, three resolutions: **Global** (countries, with
  US/Canada/India/China at state-province level), **US** (~3,140 counties), and **Europe**
  (~290 NUTS-2 regions, EU-27 + UK + Norway). The US/Europe data load on demand when you first
  switch; the map, overlays, legend, and stat all adapt to the active scope.
- **Feedstock supply** mode — choropleth switchable across agricultural residues, forestry
  residues, biogenic MSW, animal manure, and human/WWTP biosolids (Mt/yr).
- **Best-use recommendation** mode — each region colored by its recommended BiCRS pathway
  (BECCS, WtE+CCS, biomass injection, bio-oil, burial, AD+CCS, biochar), per Frontier's KPI ranking.
- **Overlays** (scope-specific) — retrofit-candidate / biogenic point sources, large WWTPs, and the
  region-appropriate storage layers: global storage projects + basins; US **Class VI/V wells** +
  NATCARB basin polygons; Europe **CO₂ storage projects/hubs** (Northern Lights, Porthos, …) +
  CO2StoP formation polygons.
- **Click any region** for the full detail: feedstock breakdown (with sources & uncertainty at the
  global scope), and the recommendation with rationale, ranked options, storage/density metrics,
  caveats, and Frontier-exclusion flags.
- **Methodology & sources** button in the sidebar — adapts to the active scope.

Deep-link views via URL hash, e.g.
`index.html#scope=us&mode=recommendation&region=US-06037` or
`index.html#scope=eu&mode=recommendation&ov=projects,formations&region=EU-DE21`.

## The three scopes share one engine

All three scopes are driven by the same recommendation engine (`scripts/engine_core.py`); only the
*inputs* differ in resolution. The frontend is a single app (`src/app.js`) parameterized by a
per-scope config, so the chrome (modes, detail panel, legend, hover) is written once.

- **US scope** — counties from US Census TIGER; biomass disaggregates DOE Billion-Ton state totals
  via USDA Census of Agriculture; storage = NATCARB saline formation polygons + Class VI/V wells +
  EPA GHGRP point sources + EPA FRS WWTPs. Storage access uses distance-to-basin-edge / nearest well;
  density uses tCO₂/km² + an 80 km haul-radius supply. Build: `scripts/us/download_raw.sh` then
  `scripts/us/build_all.sh`; see `docs/METHODOLOGY.md` §8.
- **Europe scope** — NUTS-2 from Eurostat GISCO; biomass from JRC ENSPRESO scaled to country totals;
  storage = CO2StoP formation polygons + named projects/hubs + curated biogenic facilities + EEA
  UWWTD WWTPs. Build: `scripts/eu/download_raw.sh` then `scripts/eu/build_all.sh`; see
  `docs/METHODOLOGY.md` §9.

## Layout

```
src/index.html, styles.css, app.js    # the single application (all three scopes)
src/vendor/                            # Leaflet (vendored)
src/data_bundle.js                     # global datasets, preloaded (generated)
src/data_bundle_us.js, _eu.js          # US / EU datasets, lazy-loaded on scope switch (generated)
data/geo/geometry.js                   # global map geometry, preloaded (generated)
data/geo/geometry_us_*.js, _eu_*.js    # US counties / EU NUTS-2 + storage geometry (generated)
data/processed/*.json                  # feedstocks, storage, facilities, recommendations (all scopes)
data/SCHEMA.md, data/ENGINE_SPEC.md    # data + engine specs
scripts/engine_core.py                 # shared decision engine (all scopes)
scripts/*.py, scripts/us/, scripts/eu/ # build pipelines (see docs/METHODOLOGY.md §7–§9)
docs/METHODOLOGY.md                    # sources, assumptions, formulas, caveats
docs/RECOMMENDATION_LOGIC.md           # flow chart of the decision tree (Mermaid)
PLAN.md                                # project plan
```

See `docs/METHODOLOGY.md` for data sources and caveats, and
[`docs/RECOMMENDATION_LOGIC.md`](docs/RECOMMENDATION_LOGIC.md) for a flow chart of the
best-use decision tree.
