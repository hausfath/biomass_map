# BiCRS Atlas

An interactive map overlaying **biomass feedstock supply**, **CO₂ storage options**, and a
**best-use-of-biomass recommendation** per region — grounded in Frontier's BiCRS purchasing POV.

## Open it

Double-click **`src/index.html`** (or open it in any browser). No server, no build step, works
offline — all data is bundled as JavaScript.

## What you can do

- **Feedstock supply** mode — choropleth switchable across agricultural residues, forestry
  residues, biogenic MSW, animal manure, and human/WWTP biosolids (Mt/yr).
- **Best-use recommendation** mode — each region colored by its recommended BiCRS pathway
  (BECCS, WtE+CCS, biomass injection, bio-oil, burial, AD+CCS, biochar), per Frontier's KPI ranking.
- **Overlays** — toggle retrofit-candidate facilities, operational CO₂ storage projects, and
  basin-level storage potential.
- **Click any region** for the full detail: feedstock breakdown with sources & uncertainty, and
  the recommendation with rationale, caveats, and Frontier-exclusion flags.
- **Methodology & sources** button in the sidebar for the full reference.

Deep-link views via URL hash, e.g.
`index.html#mode=recommendation&ov=sites,basins&region=USA`.

## Layout

```
src/index.html, styles.css, app.js   # the application
src/vendor/                           # Leaflet (vendored)
src/data_bundle.js                    # bundled datasets (generated)
data/geo/geometry.js                  # bundled map geometry (generated)
data/processed/*.json                 # feedstocks, storage, facilities, recommendations
data/SCHEMA.md, data/ENGINE_SPEC.md   # data + engine specs
scripts/*.py                          # build pipeline (see docs/METHODOLOGY.md §7)
docs/METHODOLOGY.md                   # sources, assumptions, formulas, caveats
PLAN.md                               # project plan
```

See `docs/METHODOLOGY.md` for data sources, the recommendation logic, and caveats.
