# BiCRS Atlas — Methodology & Sources

Internal Frontier strategy tool. Every estimate in the map carries an uncertainty range
and a cited source, surfaced in each region's detail panel. This document records the
data sources, assumptions, formulas, and caveats behind those numbers.

The atlas operationalizes the central claim of Frontier's BiCRS purchasing POV:
**the optimal BiCRS pathway is local** — it depends on feedstock type (wet vs. dry, woody
vs. herbaceous), feedstock density (concentrated vs. diffuse), proximity to geologic CO₂
storage, nutrient status, and the presence of retrofittable facilities.

---

## 1. Coverage & resolution

- **Global, country-level** for all layers (82 countries carry feedstock data — every major
  biomass-producing economy).
- **Subnational** resolution for the four largest, most internally heterogeneous biomass
  countries: **US states** (DOE Billion-Ton Report), **Canadian provinces** (StatCan / NRCan),
  **Indian states** (MNRE biomass atlas / Hiloidhari et al.), and **Chinese provinces** (NBS
  Statistical Yearbook / Guo et al. 2023). These are drawn as province/state cells instead of a
  single national polygon, since the optimal pathway varies strongly within them (e.g. coastal
  vs. interior China, the Punjab stubble belt vs. southern India, BC forestry vs. Prairie ag).
- The national rollup record for these four still exists (reachable by deep-link) but is flagged
  `superseded_by_subnational` and excluded from the global CDR total to avoid double-counting.
- Regions without compiled data render grey ("no data"); the long tail of small economies is
  not yet populated. This is deliberate — coverage follows data availability, and the thesis
  concentrates accessible waste biomass in the US, Europe, China, and Southeast Asia.

Geometry: Natural Earth 1:50m admin-0 countries + admin-1 provinces/states (US, Canada, India,
China), slimmed to `{id, name}` and bundled as JS (`data/geo/geometry.js`) so the page runs
offline.

---

## 2. Feedstock supply

All tonnages are **recoverable** biomass in million tonnes oven-dry per year (Mt odt/yr),
except MSW which is wet tonnes. Estimates are modelled, not measured inventories; ranges
reflect cross-source spread.

| Feedstock | Method & primary sources |
|---|---|
| **Agricultural residues** | Crop production (FAOSTAT; USDA NASS for US; Eurostat for EU) × residue-to-product ratios × **~30% sustainable removal cap** (the conservative end; rest left for soil carbon/erosion/nutrients). Applied where we compute recoverable from gross; regions taken from a published net/technical potential (e.g. EU JRC-S2BIOM, Australia Crawford 2016) retain that source's own removal assumption. Cross-checked against Slade et al. 2014, IEA 2022, Tripathi et al. 2019, DOE 2023 Billion-Ton Report (US, incl. state level). |
| **Forestry residues** | Logging + processing residues from FAO FRA, DOE Billion-Ton (US), JRC-S2BIOM (EU), NRCan (Canada). |
| **MSW** | World Bank *What a Waste 2.0* (2018) country totals + treatment shares; EPA (US), Eurostat (EU). Biogenic fraction applied: **US ≈ 0.61, EU ≈ 0.50**, higher (~0.55–0.70) in LMICs due to greater organic content. Only the biogenic share counts toward CDR. |
| **Animal manure** | FAO livestock heads × excretion/dry-matter factors; IEA *Outlook for Biogas and Biomethane* (2020). Dry-matter basis. |
| **Human / WWTP biosolids** | IEA biogas outlook; sewage sludge dry solids ≈ population × treatment coverage × solids factor. |

### Derived classifications (drive the recommendation engine)
- `dominant_feedstock` ∈ {ag_dry, forestry_woody, msw, manure_wet, mixed}
- `feedstock_density` ∈ {concentrated, diffuse} — diffuse ag favors distributed pathways (bio-oil, biochar)
- `nutrient_status` ∈ {low, moderate, excess} — *excess* (e.g. China, Netherlands, Denmark; high
  fertilizer use / intensive livestock) makes high-removal pathways (incl. burial) tolerable or
  favored, since nutrient export is less of a constraint (thesis §2.2).

### Sanity check vs. thesis
Country-level sums: **ag residues 1.84 Gt + forestry 0.60 Gt = 2.45 Gt odt/yr**. This sits just
**below** the thesis biomass range of 2.8–4.0 Gt odt **by design** — that range reflects a higher
(~40%) residue-removal assumption, whereas we apply a more conservative **~30%** sustainable-removal
cap (see Feedstock supply, above), which alone lowers the ag stream ~25%. At ~1.47 tCO₂/odt and ~90%
efficiency that is ~3.2 Gt CO₂/yr of gross potential — still within the thesis 2–5 Gtpa. Global MSW
≈ 1.7 Gt/yr (World Bank global ≈ 2.0 Gt; we cover the major producers).

---

## 3. CO₂ storage

Proximity to viable storage is the key factor distinguishing geologic pathways (BECCS,
injection, WtE+CCS) from storage-independent ones (bio-oil, burial, biochar).

- **Projects** (`kind: site`): operational/under-construction/planned dedicated geologic
  storage and large CCS-with-storage projects — Sleipner, Snøhvit, Northern Lights, Quest,
  ADM Decatur (Illinois), Gorgon, Sinopec Qilu, Tomakomai, Porthos, Greensand, Ravenna (Eni,
  Italy), Petrobras Santos pre-salt (Brazil — the world's largest CO₂ injection), the UK North
  Sea clusters (Endurance, HyNet/Liverpool Bay, Viking), Kasawari (Malaysia), Tangguh
  (Indonesia), Ras Laffan (Qatar), and more. Source: Global CCS Institute Status Report (2024),
  IEA CCUS database, company announcements.
- **Basins** (`kind: basin`): basin-level theoretical capacity (Gt) graded by confidence
  (high/medium/low). Sources: US DOE NATCARB / NETL Carbon Storage Atlas, EU CO2StoP,
  CO2CRC (Australia), and regional storage assessments.

Basin capacities are theoretical and require site appraisal before they can be relied upon.
Storage access is still **poor** in large-biomass regions such as Sub-Saharan Africa (cratons)
and interior India (low-permeability Deccan basalts), pushing them toward burial / bio-oil.
Parts of Southeast Asia and offshore Brazil that once looked storage-limited now host real
offshore CCS projects (e.g. Tangguh, Kasawari, Santos pre-salt), so those regions shift toward
geologic pathways where the biomass is also accessible.

---

## 4. Retrofit-candidate facilities

Existing biogenic-CO₂ point sources that could be retrofitted with capture — pulp & paper
mills, waste-to-energy plants, bioenergy stations, ethanol plants, biogas/AD. Includes the
BiCRS projects named in the thesis (Stockholm Exergi, Ørsted, CO280, Hafslund Celsio, Drax,
ADM, etc.). `est_biogenic_co2_mtpa` and a `retrofit_score` (high/medium/low) capture scale and
retrofit attractiveness. Sources: IEA Bioenergy, company reports, Global CCS Institute, CEWEP
(European WtE), industry registries.

Retrofits are "low-hanging fruit" for near-term BECCS (thesis §2.3): existing biomass logistics
and combustion/grid infrastructure reduce execution risk.

**Retrofit anchors** shown in a region's recommendation are matched by actual location — US
states use point-in-polygon, so a state shows an anchor only if a facility physically sits in it
(most show "none mapped"). Greenfield developers and aggregation hubs (e.g. Arbor, a greenfield
new-build; Super6, a CO₂ aggregation platform) are flagged `existing: false` and never serve as
anchors, since they are not existing facilities one can retrofit.

---

## 5. Best-use-of-biomass recommendation engine

A deterministic, transparent rule set (`scripts/build_recommendations.py`) encoding Frontier's
KPI priority — **CDR efficiency › emissions-avoiding co-product › other co-benefits** — modulated
by storage proximity, retrofit availability, feedstock moisture/density, and nutrient status.

### Pathway constants (thesis §2.1)
| Pathway | CDR efficiency | Cost band ($/tCO₂) | Co-product |
|---|---|---|---|
| BECCS (heat/elec) | 80% | $200–225 (→<$100 at scale) | energy |
| BECCS pulp & paper | 80% | $200–225 | energy |
| WtE + CCS | 55% | ~$100–200 | energy |
| Biomass waste injection | 90% | $125–285 | PFAS destruction |
| Bio-oil (pyrolysis) | 45% | $140–360 | biochar/nutrients |
| Bio-oil (hydrothermal liquefaction) | 50% | $200–400 | nutrients |
| Biomass burial | 90% | <$100–150 | none |
| Anaerobic digestion + CCS | 37% | $145–300 | low-C fuel |
| Biochar | 30% | ~$100–200 | nutrients |

### Logic (first match wins)
1. **Wet manure** → wet biomass has **no solid-feedstock options** — biochar and burial both need
   dry/solid biomass and are never used here. AD+CCS and slurry injection both place CO₂ (or the
   slurry) into geologic storage, so — like BECCS and WtE+CCS — **both require storage proximity**.
   With storage near: AD+CCS where the region's **AD maturity** is high enough that a large existing
   digester industry can be retrofitted (see below), otherwise direct **injection**. With storage
   **poor** (or where injection's wet-slurry transport exceeds the $100/tCO₂ cap), → **HTL bio-oil**:
   hydrothermal liquefaction densifies the wet feedstock so it can be hauled. Bio-oil is pricier and
   less preferred than direct injection, so it leads only when storage is distant/expensive.
   *Never combustion, biochar, or burial.*

   **AD maturity (data-driven).** Whether AD+CCS leads over injection is set by a continuous
   `ad_maturity` index ∈ [0,1] — *the share of a region's organic/manure AD potential already
   realized as biogas/biomethane* (the IEA "utilization" framing: EU avg ~40%, US/China/India <5%).
   AD+CCS leads where `ad_maturity ≥ 0.15` (a tunable threshold). This replaces a former hardcoded
   list of "mature-AD countries". **Country scores** are transcribed from IEA *Outlook for Biogas
   and Biomethane* (2025, the potential denominator + utilization framing), FAOSTAT bioenergy
   (biogas production), IRENA (capacity cross-check) and the EBA Statistical Report — e.g. Germany
   0.85, Denmark 0.70, Italy 0.45, Netherlands/UK 0.35, France/Sweden/Belgium 0.30; USA 0.03,
   Canada 0.14, China 0.07, India 0.04. Notably the *data* places Spain (0.10), Poland (0.08) and
   Ireland (0.06) **below** threshold despite large potential — their AD industries are barely
   built out — so they lead with injection, a correction over the old subjective list.
   **Sub-national** scores override the country value where real facility data exists: US states
   from EPA AgSTAR digester capacity ÷ state manure potential (California 0.26 — the Central-Valley
   dairy-digester cluster — Vermont, Arizona above threshold); Canada provinces from Canadian Biogas
   Association fleet shares ÷ provincial manure (**Ontario 0.41 and BC 0.49 lead with AD+CCS**;
   Quebec 0.11, Alberta 0.03 lead with injection); EU NUTS-2 refined by AD-facility density within
   each country. Built by `scripts/build_ad_maturity.py` → `data/processed/ad_maturity.json`.
2. **MSW** → WtE+CCS (storage near) else burial.
3. **Woody / concentrated dry ag** → BECCS where storage is good/moderate, as the **pulp & paper
   retrofit (`beccs_pp`) whenever an existing mill is within reach** (good *and* moderate storage
   alike — the retrofit leverages existing logistics and lower execution risk, and needs the same
   geologic storage as greenfield BECCS), else greenfield BECCS. If storage poor → burial (excess
   nutrients) or bio-oil. Runner-up is **injection** at good storage (it beats bio-oil there — see
   below), **bio-oil** at moderate (densified carbon hauls cheaper when wells are farther).
4. **Diffuse dry ag** → **injection where geologic storage is proximate** (good access), else
   bio-oil (Charm roving model) where wells are distant, or biochar; burial if poor storage +
   excess nutrients.
5. **Mixed / fallback** → BECCS (good storage + retrofit), burial (poor storage), else BECCS.

#### Two bio-oil routes: pyrolysis (dry) vs. HTL (wet)
Bio-oil is split into two pathways by feedstock moisture: **`bio_oil` — pyrolysis** densifies *dry*
biomass (crop/forestry residues; the Charm-style roving model), and **`bio_oil_htl` — hydrothermal
liquefaction** processes *wet* biomass (manure/biosolids) directly without drying. Both densify the
carbon into a haulable bio-crude injected at a well, so both win over direct injection only at
distance; HTL is the costlier, earlier-stage route. The engine never crosses them — dry feedstocks
use pyrolysis, wet feedstocks use HTL.

#### Injection vs. bio-oil for dry residues
Frontier is bullish on Vaulted-style slurry injection: it handles the same dry crop residues
as bio-oil, has higher CDR efficiency (>90% vs. ~45%), and is cheaper on balance — so where
geologic storage (injection wells) is **proximate** it is preferred over bio-oil. Bio-oil's
advantage is only at distance: pyrolysis densifies the carbon (less-carbon-dense raw biomass is
expensive to haul), so it wins when wells are far. The engine therefore routes dry-residue
removal to **injection at good storage access** and **bio-oil (pyrolysis) at moderate/poor access**.
In excess-nutrient regions where injection leads, **burial** is surfaced as the alternative rather
than bio-oil, since bio-oil returns nutrients to soils that are already in surplus.

### Storage proximity
Combines two signals and takes the more favorable: (a) haversine distance from region centroid
to the nearest qualifying project or high/medium basin (good <500 km, moderate <1000 km), and
(b) qualifying storage **within the same country**, graded by confidence. The in-country signal
corrects centroid bias for large countries (e.g. the US, whose Kansas centroid is >500 km from
Gulf Coast / Illinois basins despite world-class in-country storage).

### KPI score (0–100, for coloring/ranking)
`60·efficiency + 25·(energy co-product) + 15·(co-benefit) − 10·(needs storage but poor access)`.

### CDR potential
- Dry pathways: (ag + forestry residues, Mt odt) × 1.47 tCO₂/odt × efficiency
- WtE: MSW × biogenic fraction × ~1.0 tCO₂/t × efficiency
- Injection/AD: (manure + biosolids, Mt odt) × 1.47 × efficiency

Global summed CDR potential across recommended pathways ≈ **2.9 Gtpa**, within the thesis range.

### Per-region ranked options
Each region also carries a full **best-to-worst ranking** of the pathways applicable to its
dominant feedstock (wet feedstocks exclude combustion, etc.), with region-specific advantages
and disadvantages generated from storage access, feedstock density, nutrient status, and
retrofit availability. The recommended and runner-up pathways are pinned at the top; the rest
are ordered by a fit score (intrinsic KPI score plus local modifiers). This drives the ranked
list shown in the "Best use" layer's detail panel.

### Retrofit-only pathway gating
**BECCS pulp & paper, WtE+CCS, and AD+CCS only make sense as retrofits of existing facilities
today**, so each is recommendable — and only appears in a region's ranked options — where the region
is within the typical **feedstock-procurement radius** of an existing facility of that type:
- **pulp & paper → `beccs_pp`**: a pulp & paper mill within **~150 km** (pulpwood haul averages
  ~80–93 mi). Bioenergy plants anchor plain BECCS (ungated), not `beccs_pp`.
- **waste-to-energy → `wte_ccs`**: a WtE plant within **~50 km** (local/regional MSW catchment).
- **anaerobic digestion → `ad_ccs`**: cumulative AD capacity within reach (**~15 km** for discrete
  digesters; regional clusters carry their own coverage radius) above a small threshold — ADs are
  individually small, so *cumulative regional capacity* is what matters for a retrofit.

Outside the radius the engine falls back to a non-retrofit pathway (no mill → plain BECCS/injection;
no AD → injection or biochar). For **MSW with no WtE plant in range**, municipal waste is landfilled
rather than a removal feedstock, so the region is re-evaluated on its next-significant biomass —
agricultural / forestry residues or **wet manure + human biosolids** — counted significant if it is
≥ 25% of the MSW potential **or** clears an absolute floor (~0.05 Mt CO₂/yr). The absolute floor
matters for big cities: e.g. Los Angeles' MSW dwarfs its biosolids relatively (~5%), but ~0.3 Mt
CO₂/yr of biosolids is an ample injection feedstock (what Vaulted Deep injects in LA) → injection.
Only if there is no other significant feedstock is the result **"no viable BiCRS pathway"** rather
than a forced burial. The CDR potential, rationale, and ranked options then reflect that effective
feedstock (e.g. biosolids), not the dominant MSW.
Plain BECCS (heat/electricity) is **not**
gated. At country scope (global view) "within radius" reduces to "a facility of that type exists in
the country". **Facility coverage for the gate:** pulp & paper and WtE from the global + EPA
GHGRP / E-PRTR datasets; AD from **EPA AgSTAR** (US livestock digester database, mapped to counties
and aggregated) and **EBA-based regional cumulative clusters** (EU & global biogas regions — German
states, Po Valley, Denmark, France, etc.). Radii are tunable constants (`PROC_RADIUS_KM`) in
`scripts/engine_core.py`.

### Frontier exclusions (flagged, never recommended)
- **Purpose-grown energy crops** — land-use competition; thesis sourcing principles.
- **RNG + CCS / AD + CCS** — *no longer excluded.* Frontier is open to it as an offtake option,
  and it is preferred over injection for manure in regions of high measured AD maturity (§5). Its partial
  CDR (carbon split between RNG fuel and storage) is surfaced in the ranked-options cons.
- **Corn-ethanol + CCS** — food/land competition, marginal additionality; flagged where local
  ethanol capacity exists (US corn belt). (Brazilian sugarcane ethanol is *not* excluded.)
- **Burial** carries a mandatory durability caveat (Isometric 2024 protocol projects 1,000-yr;
  Frontier pursuing via prepurchase, not offtake).

---

## 6. Key uncertainties, assumptions & limitations

Everything here is a screening model, not a measured inventory. The items below are ordered by how
much they could change a recommendation if revisited — the top ones are the most worth re-addressing.

### Highest-leverage uncertainties (could flip a recommendation)
1. **Storage proximity is great-circle, not routed, and basin capacities are theoretical.** We screen
   on straight-line distance to the nearest project or assessed basin/formation *boundary* (and an
   in-country/in-basin override). Real CO₂ transport follows pipelines/rail and real injectability
   needs site appraisal — a region we call "good" could be infeasible, and vice-versa. This is the
   single biggest driver of the geologic-vs-storage-independent split (BECCS/injection vs. bio-oil/
   burial/biochar), so it deserves the most scrutiny.
2. **Retrofit-gate radii (`PROC_RADIUS_KM`: pulp&paper 150 km, WtE 50 km, AD 15 km) and the AD
   capacity floor (`AD_MIN_CAP_MTPA = 0.01`) are tunable single-point assumptions.** They decide
   whether `beccs_pp`, `wte_ccs`, and `ad_ccs` are even *offered*. Procurement radii vary widely by
   facility and region; the chosen values are literature midpoints. Widening/narrowing them shifts how
   many regions get a retrofit pathway vs. fall back to greenfield injection/burial.
3. **Centroid artifacts in large/irregular regions.** Distance and facility-presence tests use the
   region centroid. For big or oddly-shaped polygons this misfires — e.g. **Los Angeles County's
   centroid sits in the San Gabriel mountains**, far from its coastal population and the SERRF WtE
   plant, so LA registers *no* WtE in range and re-routes to biosolids injection. The outcome is
   defensible but the mechanism is a geometry artifact; population-weighted centroids would be a fix.
4. **The MSW-fallback significance thresholds** (`SECONDARY_FRAC = 0.25` relative **or**
   `SECONDARY_ABS_MTPA = 0.05` absolute Mt CO₂/yr) decide when a no-WtE city re-routes to its
   secondary feedstock vs. reads "no viable BiCRS pathway." The absolute floor is what lets big-city
   biosolids count (LA case); both constants are judgment calls, not derived.

### Feedstock-supply assumptions (affect magnitudes more than pathway choice)
5. **~30% sustainable-removal cap on agricultural residues** and crop-specific residue-to-product
   ratios. The cap is a single conservative global default standing in for soil-carbon/erosion limits
   that truly vary by soil, climate, and tillage. Drives all dry-residue tonnages. (Applied where we
   compute recoverable from gross; regions taken directly from a published net/technical potential
   keep that source's own removal assumption, so the effective cap is not perfectly uniform.)
6. **MSW biogenic fractions** (US ≈ 0.61, EU ≈ 0.50, ~0.55–0.70 LMIC) applied uniformly within a
   region. Real biogenic share varies by waste stream and season.
7. **CO₂ yield factor ~1.47 tCO₂/odt** applied to all dry biomass, and ~1.0 tCO₂/t to MSW. A
   carbon-content midpoint; herbaceous vs. woody and ash content shift it.
8. **Forestry county/region placement is the weakest spatial layer.** US within-state forestry is
   allocated by *farm-woodland acreage* (Census of Ag), which under-represents national forests and
   industrial timberland; EU uses ENSPRESO. State/country totals are always preserved, but
   *within*-area forestry geography is approximate.
9. **Manure & WWTP biosolids** rest on livestock-head excretion factors and population × treatment-
   coverage × solids factors — order-of-magnitude reasonable, not facility-metered (except where US
   AgSTAR digester capacity is used for the AD gate).

### Coverage & resolution limits
10. **Country-level scope cannot capture sub-national feedstock/storage mismatch** (interior vs.
    coastal China; corn belt vs. the rest of the US). Large heterogeneous countries (US, China, India,
    Russia, Brazil, Canada, Australia) are rollups carrying a caveat; US/EU detail scopes mitigate this
    for two of them, and China/India/Canada have province/state feedstocks but not the full county-level
    storage/facility overlays.
11. **The long tail of small economies is unpopulated** (renders grey). Coverage follows data
    availability and the thesis focus (US, Europe, China, SE Asia).
12. **EU facility biogenic-CO₂ is estimated from capacity**, since EU ETS zero-rates sustainable
    biomass and there is no clean reported biogenic column — the weakest EU layer, expandable via
    E-PRTR. The US has reported biogenic CO₂ (GHGRP Subpart) and is more reliable.
13. **ENSPRESO is NUTS v2013**; ~33 regions recoded since (mainly France's 2016 reform) fall back to
    population allocation of their country total (flagged per-record).

### Scope of the tool
- Ranges shown in detail panels reflect **cross-source spread, not formal confidence intervals**.
- The tool informs *strategy*; it does not substitute for project-level diligence (biomass sourcing
  verification, LCA boundaries, additionality, durability, execution risk). Burial in particular
  carries a mandatory durability caveat.

---

## 7. Reproducing the data pipeline

```
scripts/engine_core.py           # SHARED decision logic (pathways, decide(), kpi_score,
                                 # ranking, rationale) — imported by both engines below
scripts/build_geo.py             # slim Natural Earth geometry -> data/geo/geometry.js
                                 # (regional feedstock + storage + facilities JSON compiled by subagents)
scripts/merge_validate.py        # merge regional feedstock files -> feedstocks.json; sanity checks
scripts/build_recommendations.py # run the recommendation engine -> recommendations.json
scripts/bundle_data.py           # bundle processed JSON -> src/data_bundle.js (file:// safe)
```

Then open `src/index.html` directly in any browser.
Data schema: `data/SCHEMA.md`. Engine spec: `data/ENGINE_SPEC.md`.

---

## 8. US county-level data

The US county data resolves the United States to ~3,140 counties. It shares the decision framework
via `scripts/engine_core.py`; only the *inputs* are recomputed at county granularity. In the app it
is surfaced together with the Canadian census-division data (§10) as the single **North America**
scope (`src/index.html` → Region scope: **North America**) — the two datasets are built by separate
pipelines but merged into one view, so the US and Canada are seen and compared together. (Originally
a standalone `us.html`; now lazy-loaded within the single app.)

**Pipeline** (`scripts/us/`): `download_raw.sh` stages the public sources, then `build_all.sh` runs
`build_county_geo.py` → `build_basin_geo.py` → `build_county_feedstocks.py` →
`build_us_infrastructure.py` → `build_us_recommendations.py` → `bundle_us.py`. View via the US scope
in `src/index.html`.

**County feedstocks** — "Billion-Ton state totals, spatially disaggregated to counties." Each
feedstock's within-state distribution comes from authoritative county data, then is scaled so a
state's counties sum to that state's existing global-tool total (anchored to the DOE 2023
Billion-Ton Report + USDA NASS):
- *Ag residues*: USDA Census of Agriculture 2022 county crop production (corn, wheat, soy, sorghum,
  barley, oats, rice, cotton, sugarcane) × residue-to-product ratios × ~30% recoverable fraction.
- *Manure*: USDA Census of Ag 2022 county livestock inventory × relative manure (volatile-solids) weights.
- *MSW & WWTP biosolids*: Census Vintage-2023 county population × per-capita allocation of state totals.
- *Forestry*: state forestry-residue total allocated to counties by woodland acreage (Census of Ag).
  This is the weakest layer — farm-woodland under-represents non-farm timberland (national forests,
  industrial timberland), so within-state county placement of forestry is approximate; ag and manure
  are the high-confidence county layers. State totals are always preserved.

**Storage basins (actual polygons)** — NETL NATCARB Atlas assessed saline storage formations
(`NATCARB_Saline_Poly_v1502`, 349 assessed/non-duplicate formations), reprojected from Lambert
Azimuthal Equal-Area to WGS84, simplified, and rounded. A county whose centroid falls inside a
formation has storage on-site.

**Wells** — operational geologic sequestration (EPA GHGRP 2023 Subpart RR reporters), Class VI
permits (issued / draft / pending, curated from the EPA Class VI Data Repository, current to 2026),
and curated Class V biomass-injection / bio-oil projects (Vaulted Deep, Charm Industrial).

**Biogenic point sources & WWTPs** — facility-level biogenic CO₂ from EPA GHGRP 2023 (pulp & paper,
bioenergy, waste-to-energy, landfill gas, ethanol), kept where biogenic CO₂ ≥ 25 kt/yr or biomass
dominates; large WWTPs are NPDES "major" POTWs (≥ 1 MGD) from EPA FRS.

**County engine upgrades** (`build_us_recommendations.py`) over the global inputs:
- *Transport distance*: inside-a-basin = storage on-site (good); else great-circle to the nearest
  basin boundary AND nearest Class VI / operational well; graded good < 100 km, moderate < 300 km
  (tighter than the global 500/1000 km). These are great-circle screening distances, not routed.
  **Cross-border:** storage proximity ignores the border — US counties are also scored against
  Canadian basins/CCS projects (the WCSB / Quest / ACTL across from the northern-tier states), just
  as Canadian CDs are scored against US wells/basins.
- *Feedstock density*: real residue density (tCO₂/km²) **and** an 80 km haul-radius supply sum decide
  whether biomass is concentrated enough (density ≥ 120 tCO₂/km² and ≥ 0.75 Mt CO₂/yr within reach)
  to anchor a central BECCS/pulp plant; otherwise diffuse → favours injection/bio-oil.
- *Low-supply guard*: counties below ~0.02 Mt CO₂/yr total recoverable supply are flagged (rendered
  muted, recommendation indicative only) rather than forced into a pathway.

**Sanity**: county ag + forestry + manure totals reconcile to the global tool's US state sums
(ag ≈ 257 Mt, forestry ≈ 99 Mt, manure ≈ 143 Mt odt/yr). Raw source files live under
`data/geo/us_raw/` (gitignored; re-fetch with `download_raw.sh`).

---

## 9. EU subnational (NUTS-2) scope

The **Europe scope** of the integrated Atlas (`src/index.html` → Region scope: **Europe**) resolves
to ~290 NUTS-2 regions (EU-27 + UK + Norway). It shares the decision framework via
`scripts/engine_core.py` (imported unchanged); only the inputs are computed at NUTS-2 granularity.
(Originally a standalone `eu.html`; now a lazy-loaded scope within the single app.)

**Pipeline** (`scripts/eu/`): `download_raw.sh` stages the public sources, then `build_all.sh` runs
`build_nuts_geo.py` → `build_storage_geo.py` → `build_nuts_feedstocks.py` → `build_eu_infrastructure.py`
→ `build_eu_recommendations.py` → `bundle_eu.py`. View via the Europe scope in `src/index.html`.

**NUTS-2 feedstocks** — "ENSPRESO NUTS-2 distribution, scaled to country totals." Each feedstock's
within-country distribution comes from the JRC **ENSPRESO** NUTS-2 biomass database (ag residues =
`MINBIOAGRW`; forestry = forest-residue `MINBIOFRSR` + secondary-wood `MINBIOWOOW`; manure = biogas
feedstock `MINBIOGAS`); MSW & biosolids are allocated by NUTS-2 population (Eurostat
`demo_r_pjanaggr3`, 2023 with 2019 fallback for the UK). Each region is then scaled so a country's
NUTS-2 regions sum **exactly** to that country's total already in the global tool (all 29 countries
present). Purpose-grown energy/biofuel crops (`MINBIOCRP*`, `MINBIOLIQ*`, `MINBIORPS*`) are excluded
(Frontier exclusions). ENSPRESO is NUTS v2013; regions recoded since (mainly France's 2016 reform) are
remapped via ENSPRESO's own "NUTS2 conversion" sheet; ~33 still-unmatched regions fall back to
population allocation of their country total (documented per-record in the `source` field).

**CO₂ storage (actual polygons)** — the EU **CO2StoP** database (JRC/SETIS) open-format KML
`StorageUnits_March13.kml`: 325 assessed saline-aquifer / hydrocarbon-field storage units, parsed to
WGS84 polygons. A region whose centroid falls inside a unit has storage on-site.

**Storage projects / hubs** (the "wells" equivalent — Europe has no Class V/VI) — the operational and
planned named projects already in the global tool (Northern Lights, Porthos, Aramis, Greensand, Acorn,
Ravenna, Endurance, HyNet, Sleipner, Snøhvit, …) plus a few curated additions, each with status.

**Biogenic point sources & WWTPs** — the curated European biogenic-CO₂ facilities already in the global
tool (126: pulp & paper, WtE, bioenergy, biogas/AD), with biogenic-CO₂ estimated from capacity (EU ETS
zero-rates sustainable biomass, so there is no clean reported biogenic column — the weakest layer,
expandable via E-PRTR). Large WWTPs are ≥150,000-PE plants from the EEA/EMODnet **UWWTD** (Waterbase).

**NUTS-2 engine upgrades** (`build_eu_recommendations.py`): storage access — inside-a-formation =
on-site, else great-circle to the nearest CO2StoP formation boundary AND nearest storage project,
graded **good < 150 km, moderate < 400 km** (wider than the US, for NUTS-2 scale + offshore-dominant
storage); feedstock density from residue tCO₂/km² (≥ 90 → concentrated; no haul-radius sum, as NUTS-2
regions are large). The manure → AD+CCS preference fires via the data-driven `ad_maturity` index
(§5): most European countries score above the 0.15 threshold (Germany 0.85, Denmark 0.70, …) so their
manure regions lead with AD+CCS where storage is near, while Spain/Poland/Ireland — low realized AD —
lead with injection. NUTS-2 scores are refined within each country by AD-facility density.

**Sanity**: all 29 countries × 4 streams reconcile exactly to the global tool's totals; pathway mix is
geographically coherent (Scandinavia/forestry → BECCS; Po Valley/NL manure → AD+CCS; urban → WtE+CCS;
remote N. Sweden far from storage → bio-oil). Much EU storage is offshore, so inland regions read
`poor` legitimately. Raw sources live under `data/geo/eu_raw/` (gitignored; re-fetch with
`download_raw.sh`).

---

## 10. Canada census-division (CD) data

The Canada data resolves the country to its **293 census divisions** (CDs, the Canadian
county-equivalent). It shares the decision framework via `scripts/engine_core.py` (imported
unchanged); only the inputs are computed at CD granularity, exactly mirroring the US county pipeline.
In the app it is surfaced together with the US county data (§8) as the single **North America** scope
(`src/index.html` → Region scope: **North America**) — one merged view spanning ~3,440 US counties +
Canadian census divisions, summing to ~533 Mt CO₂/yr of CDR potential.

**Pipeline** (`scripts/ca/`): `download_raw.sh` stages the public sources, then `build_all.sh` runs
`build_cd_geo.py` → `build_basin_geo.py` → `build_cd_feedstocks.py` → `build_ca_infrastructure.py` →
`build_ca_recommendations.py` → `bundle_ca.py`. View via the Canada scope in `src/index.html`.

**CD feedstocks** — "province totals, spatially disaggregated to census divisions." Each feedstock's
within-province distribution comes from authoritative CD-level StatCan data, then is scaled so a
province's CDs sum **exactly** to that province's total already in the global tool (the 13 `CA-<Province>`
records in `feedstocks_can_sub.json`, anchored to StatCan / NRCan / IEA):
- *Ag residues*: StatCan **Census of Agriculture 2021** CD field-crop area (table 32-10-0309, hectares of
  residue-producing cereals/oilseeds/pulses; hay, forage and silage excluded) × per-hectare residue
  weights.
- *Manure*: StatCan Census of Ag 2021 CD inventories — cattle (table 32-10-0370, dairy-weighted),
  pigs (32-10-0372) and poultry (32-10-0374) × relative manure volatile-solids weights.
- *MSW & biosolids*: StatCan **2021 Census** CD population (table 98-10-0002) × per-capita allocation
  of province totals.
- *Forestry*: province forestry-residue total allocated to CDs by **land area** (the weakest layer —
  Canada has no clean CD-level timberland inventory; province totals are always preserved).

**Storage basins (curated polygons)** — Canada has no NATCARB/CO2StoP-style open polygon atlas, so the
basins are **curated** simplified extents of the fairways that actually host or are appraised for CO₂
storage: chiefly the **Western Canada Sedimentary Basin** (Alberta, much of Saskatchewan, NE British
Columbia, SW Manitoba — a world-class resource already hosting Quest, ACTL, Aquistore and the Weyburn
complex) and the **Williston Basin** (SE Saskatchewan / SW Manitoba). A CD whose centroid falls inside a
basin has storage on-site. These are first-order, province-scale extents for screening, not site
appraisal.

**CCS projects (the "wells" equivalent)** — Canada has no US-style Class V/VI well system, so the wells
layer is a curated set of Canadian CCS projects and storage hubs with status: operational (Quest, ACTL,
Aquistore, Boundary Dam, Weyburn-Midale, Entropy Glacier), under construction (Polaris/Atlas), and
proposed/appraisal (Pathways Alliance, Enbridge Wabamun, Bison, Meadowbrook, Genesee).

**Biogenic point sources & WWTPs** — curated Canadian biogenic-CO₂ facilities (53: pulp & paper, WtE,
fuel-ethanol, biomass energy, biogas/AD), seeded from the records already in the global tool — ECCC's
GHGRP does not publish a clean biogenic-CO₂ column and is served behind signed/SPA endpoints, so (as for
the EU) biogenic CO₂ is capacity-estimated (the weakest layer, expandable via ECCC GHGRP). Large WWTPs
are curated major urban water-resource-recovery plants. Each facility is reverse-geocoded to its province
via point-in-CD.

**CD engine** (`build_ca_recommendations.py`): storage access — inside-a-basin = on-site, else
great-circle to the nearest basin boundary AND nearest operational/under-construction CCS project, graded
**good < 100 km, moderate < 300 km** (same as the US); feedstock density from residue tCO₂/km² + an 80 km
haul-radius supply sum; CDs below a minimum recoverable supply flagged "low supply". **Cross-border:**
a Canadian CD is also scored against US storage — the North Dakota Class VI wells just across from
southern Saskatchewan, and the US side of the Williston Basin — since CO₂ storage doesn't stop at the
border. (This is what pulls much of the southern prairies and southern Ontario into good/moderate
access.)

**Sanity**: all 13 provinces × 5 streams reconcile exactly to the global tool's province totals; the
pathway mix is geographically coherent and strategically telling — Canada's appraised storage is
concentrated in the prairie WCSB, so the **prairies (AB/SK/MB) enable injection / BECCS / AD+CCS** while
biomass-rich but storage-distant **BC, Ontario, Québec and the Atlantic legitimately read `poor` →
bio-oil / biochar / burial**. (A consequence worth noting: southern-Ontario depleted-reservoir storage is
*not* in the curated basin set, so urban Ontario/Québec read poor and several dense urban CDs fall to "no
viable pathway".) Raw sources live under `data/geo/ca_raw/` (gitignored; re-fetch with `download_raw.sh`).

---

## 11. Multimodal transport cost & route (US scope; drives storage access)

For each subnational unit the Atlas estimates the **least-cost combination of truck + rail + ship/barge**
to move material from the region centroid to the **nearest operating** geologic-storage well, the
**carbon-density-weighted delivered cost** ($/tCO₂), and a drawable route. Live for the **US** today
(toggle *CO₂ transport route* in Map layers; cost shown in the detail panel).

**Now an engine input (US).** For the US scope, this delivered cost **replaces great-circle distance as
the storage-access signal**: `storage_access` is derived from the CO₂ delivered cost (good ≤ $66/tCO₂,
moderate ≤ $100, poor > $100), and each storage-dependent pathway is **disqualified above $100/tCO₂ for
its own payload** (carbon-density-correct — wet slurry hits the cap far sooner than densified bio-oil),
falling back to bio-oil or a storage-independent pathway (burial/biochar). A soft KPI penalty scales with
the cost band below the cap. Because only ~24 *operating* wells anchor the US today (vs the generous
basin-polygon proximity used before), this pushes ~40% of counties past $100/tCO₂ → storage-independent,
and mid-distance counties toward **bio-oil** (densify-to-haul) rather than moving CO₂ or wet slurry — an
economically grounded shift. Other scopes (global, Canada, EU) still use distance-based access until the
transport model is extended to them.

**Delivered cost** = `mass_per_tCO₂(payload) × Σ_legs[mode $/t·km × routed-km] + per-mode handling +
CO₂ liquefaction (for gaseous CO₂ only)`. The **payload carbon density** is the crux — what's hauled
differs by pathway, so the same distance costs very differently:

| Pathway | Moves to the well | ~t per tCO₂ stored |
|---|---|---|
| BECCS · BECCS-pp · WtE+CCS · AD+CCS | captured CO₂ (liquefied) | ~1.0 |
| Bio-oil sequestration | pyrolysis-densified bio-oil | ~0.45 |
| Biomass waste injection | wet biomass slurry | ~2.0 |
| Biomass burial · biochar | nothing — stored locally | 0 (no transport-to-well) |

So a long haul leaves **bio-oil viable but prices slurry-injection out**, and is irrelevant to
burial/biochar — the current qualitative injection-vs-bio-oil-vs-burial logic, now quantified. Example:
*Polk Co, IA* (corn belt) routes truck→rail→truck 849 km to Vaulted Deep (Kansas) — **bio-oil ≈ $30,
slurry ≈ $135 /tCO₂**; coastal/long routes (e.g. NYC → ADM Decatur, 1,900 km) push slurry past $200.

**Mode model** (country-level $/t·km, tunable in `scripts/transport_common.py`): truck ~$0.12, rail
~$0.035, ship/barge ~$0.015, plus per-mode handling and a one-off ~$25/t CO₂ liquefaction; great-circle
× mode detour factors. **Routing:** a sparse multimodal graph over curated **rail terminals + ports**
(`data/geo/transport_nodes_us.json`; basins let Mississippi/Ohio barge reach Gulf storage), solved with a
small Dijkstra per region (`scripts/us/build_us_transport.py` → `transport_us.json`). The cost-minimising
*path* is payload-independent (carbon density is a scalar multiplier), so one path is solved per region
and costs are scaled per payload. **v1 caveats:** distances are **great-circle screening × detour, not
network-routed**; transfer nodes are a curated subset (expandable to BTS NTAD / NGA World Port Index);
drawn legs are straight (stylised). Restricted to **operating** wells (US: 24).

*Planned:* extend the transport model (and thus cost-based storage access) to Canada and the EU, and
upgrade v1's schematic routing to real network geometry (NTAD/World Port Index, `searoute`).

---

## 12. Consolidated data sources

Every layer, with its source and resolution. "Scope" = which view consumes it
(**G** global country-level; **US** county data + **CA** Canada census-division data, which
together form the combined **North America** scope; **EU** NUTS-2 scope).

### 12.1 Feedstock supply

| Layer | Scope | Source(s) | Resolution / method |
|---|---|---|---|
| Ag residues | G | FAOSTAT crop production × residue-to-product ratios × ~30% removal cap (published net/technical-potential sources keep their own); cross-checked Slade et al. 2014, IEA 2022, Tripathi et al. 2019 | Country |
| Ag residues | G (sub) | **US** DOE 2023 Billion-Ton + USDA NASS; **EU** JRC-S2BIOM; **Canada** StatCan crop production (Nov 2023); **China** NBS 2022 output + Liu et al. 2013 RPR; **India** MNRE atlas / Hiloidhari et al. + Agriculture Census | State / province |
| Ag residues | US | USDA **Census of Agriculture 2022** county crop production (corn, wheat, soy, sorghum, barley, oats, rice, cotton, sugarcane) × RPR × ~30% | County, scaled to BT23 state totals |
| Ag residues | EU | JRC **ENSPRESO** `MINBIOAGRW` | NUTS-2, scaled to country totals |
| Ag residues | CA | StatCan **Census of Agriculture 2021** CD residue-crop area (32-10-0309) × per-ha residue weight | Census division, scaled to province totals |
| Forestry residues | G | FAO FRA; **US** Billion-Ton; **EU** JRC-S2BIOM; **Canada** NRCan | Country / state |
| Forestry residues | US | State BT total allocated by Census-of-Ag woodland acreage *(weakest spatial layer)* | County, scaled to state |
| Forestry residues | EU | ENSPRESO `MINBIOFRSR` (forest residue) + `MINBIOWOOW` (secondary wood) | NUTS-2, scaled |
| Forestry residues | CA | Province total allocated by CD land area *(weakest spatial layer — no CD timberland inventory)* | Census division, scaled |
| MSW | G | World Bank *What a Waste 2.0* (2018) totals + treatment shares; EPA (US); Eurostat (EU); biogenic fraction US≈0.61 / EU≈0.50 / LMIC 0.55–0.70 | Country |
| MSW & biosolids | US | Census **Vintage-2023** county population × per-capita allocation of state totals | County |
| MSW & biosolids | EU | Eurostat `demo_r_pjanaggr3` (2023; 2019 fallback UK) population allocation | NUTS-2 |
| MSW & biosolids | CA | StatCan **2021 Census** CD population (98-10-0002) × per-capita allocation of province totals | Census division |
| Animal manure | G | FAO livestock heads × excretion/dry-matter factors; IEA *Outlook for Biogas and Biomethane* (2020) | Country |
| Animal manure | US | USDA Census of Ag 2022 county livestock × volatile-solids weights | County, scaled to state |
| Animal manure | EU | ENSPRESO `MINBIOGAS` | NUTS-2, scaled |
| Animal manure | CA | StatCan Census of Ag 2021 CD cattle/pigs/poultry (32-10-0370/0372/0374) × manure-VS weights | Census division, scaled |
| Human / WWTP biosolids | G | IEA biogas outlook; population × treatment coverage × solids factor | Country |
| Nutrient status | G/sub | FAO FAOSTAT fertilizer use per ha 2022; Zhang et al. 2015 (China); AAFC (Canada) | Country / province |

### 12.2 CO₂ storage

| Layer | Scope | Source(s) | Form |
|---|---|---|---|
| Storage projects / hubs | G/EU | Global CCS Institute Status Report (2024), IEA CCUS database, company announcements | Points (operational / construction / planned) |
| Storage basins (capacity) | G | US DOE NATCARB / NETL Carbon Storage Atlas, EU CO2StoP, CO2CRC (Australia), regional assessments | Basin points, graded high/med/low |
| Saline storage formations | US | NETL **NATCARB** `NATCARB_Saline_Poly_v1502` (349 assessed formations), reprojected LAEA→WGS84 | **Polygons** |
| Storage formations | EU | JRC/SETIS **CO2StoP** `StorageUnits_March13.kml` (325 units) | **Polygons** |
| Wells — operational | US | EPA **GHGRP 2023 Subpart RR** reporters | Points |
| Wells — Class VI | US | EPA **Class VI Data Repository** (issued / draft / pending, to 2026) | Points |
| Wells — Class V | US | Curated biomass-injection / bio-oil (Vaulted Deep, Charm Industrial) | Points |
| Storage basins | CA | **Curated** simplified extents — Western Canada Sedimentary Basin (WCSB) + Williston (no open Canadian polygon atlas) | **Polygons** |
| CCS projects / hubs | CA | Curated (Quest, ACTL, Aquistore, Boundary Dam, Weyburn, Polaris/Atlas, Pathways, Wabamun, …); status operational / construction / proposed | Points (the "wells" layer) |

### 12.3 Retrofit-candidate facilities (and the gate)

| Layer | Scope | Source(s) | Notes |
|---|---|---|---|
| Biogenic point sources | G | IEA Bioenergy, company reports, Global CCS Institute, CEWEP (European WtE), industry registries | pulp&paper, WtE, bioenergy, ethanol, AD |
| Biogenic point sources | US | EPA **GHGRP 2023** (pulp&paper, bioenergy, WtE, landfill gas, ethanol), kept where biogenic CO₂ ≥ 25 kt/yr | Facility-level, reported biogenic CO₂ |
| Biogenic point sources | EU | Curated European facilities (126); biogenic CO₂ estimated from capacity *(weakest EU layer)* | Expandable via E-PRTR |
| Biogenic point sources | CA | Curated (53: pulp&paper, WtE, fuel-ethanol, biomass energy, biogas/AD), seeded from the global tool; biogenic CO₂ capacity-estimated *(ECCC GHGRP has no clean biogenic column)* | Expandable via ECCC GHGRP |
| Anaerobic digesters (AD gate) | US | EPA **AgSTAR** livestock digester database, mapped to counties & aggregated | 459 matched → 191 county nodes |
| Anaerobic digesters (AD gate) | EU/G | **EBA-based regional cumulative clusters** (German states, Po Valley, Denmark, France, …) | `facilities_ad.json`, each with `proc_radius_km` |
| Anaerobic digesters (AD gate) | CA | Curated regional AD/RNG clusters (ON Golden Horseshoe, QC, S. Alberta, Fraser Valley) | each with `proc_radius_km` |
| Large WWTPs | US | EPA **FRS / NPDES** "major" POTWs (≥ 1 MGD) | Points |
| Large WWTPs | EU | EEA/EMODnet **UWWTD** (Waterbase), ≥ 150,000-PE plants | Points |
| Large WWTPs | CA | Curated major urban water-resource-recovery plants | Points |

### 12.3a AD maturity (AD+CCS-vs-injection for wet manure)

The continuous `ad_maturity` index (§5) — *biogas/biomethane actually produced ÷ sustainable
biomethane potential* — built by `scripts/build_ad_maturity.py` → `data/processed/ad_maturity.json`.

| Role | Scope | Source(s) |
|---|---|---|
| Potential (denominator) | G | **IEA *Outlook for Biogas and Biomethane*** (2025) — sustainable biomethane potential + utilization framing |
| Production (numerator) | G | **FAOSTAT** bioenergy (biogas production, bulk CSV); **IEA** production for biomethane-led markets; **IRENA** capacity cross-check |
| Manure share / EU detail | EU | **EBA Statistical Report** (feedstock-mix shares, plant counts) |
| Sub-national | US | **EPA AgSTAR** operating-digester capacity ÷ state manure potential (e.g. California 0.26) |
| Sub-national | CA | **Canadian Biogas Association** provincial fleet shares ÷ provincial manure (Ontario 0.41, BC 0.49) |
| Sub-national | EU | AD-facility density vs **JRC ENSPRESO** `MINBIOGAS` per NUTS-2 (within-country refinement) |

### 12.4 Geometry

| Layer | Scope | Source |
|---|---|---|
| Country + admin-1 polygons | G | Natural Earth 1:50m admin-0 + admin-1 (US, Canada, India, China), slimmed to `{id,name}` |
| County polygons | US | US Census TIGER/cartographic boundaries (~3,140 counties) |
| Census-division polygons | CA | StatCan **2021 Cartographic Boundary File** (ArcGIS GeoJSON), 293 census divisions |
| NUTS-2 polygons | EU | Eurostat **GISCO** NUTS-2 geojson (EU-27 + UK + Norway, ~290 regions) |

### 12.5 Key model constants (all tunable, in `scripts/engine_core.py`)

| Constant | Value | Role |
|---|---|---|
| `ODT_TO_CO2` | 1.47 tCO₂/odt | Dry-biomass → CO₂ yield |
| `PROC_RADIUS_KM` | pulp&paper 150 / WtE 50 / AD 15 km | Retrofit-gate procurement radii |
| `AD_MIN_CAP_MTPA` | 0.01 Mt CO₂/yr | Cumulative AD capacity to enable `ad_ccs` |
| `AD_MATURITY_THRESHOLD` | 0.15 | `ad_maturity` score at/above which AD+CCS leads over injection for wet manure |
| `SECONDARY_FRAC` / `SECONDARY_ABS_MTPA` | 0.25 / 0.05 | MSW-fallback significance (relative OR absolute) |
| Storage grading (G) | good < 500 km / moderate < 1000 km | Centroid → nearest storage |
| Storage grading (US) | **cost-based**: good ≤ $66 / moderate ≤ $100 / poor > $100 (per tCO₂) | §11 transport cost replaces distance |
| Storage grading (CA) | good < 100 km / moderate < 300 km | distance (transport model not yet extended) |
| Storage grading (EU) | good < 150 km / moderate < 400 km | NUTS-2 scale, offshore-dominant |
| `TRANSPORT_BANDS` / `TRANSPORT_MAX_USD` | 33 / 66 / 100 ; cap 100 ($/tCO₂) | cost-band labels + storage-dependent cutoff |
| `TRANSPORT_KPI_PENALTY` | low 0 / medium 4 / high 8 | soft KPI penalty by cost band |

**Current coverage:** global 214 regions (2 "no viable pathway"); US 3,144 counties (266 "no viable
pathway" under cost-based access); Canada 293 census divisions (17 "no viable pathway"); EU 290 NUTS-2
regions (0). Raw source
files for the detail scopes live under `data/geo/us_raw/`, `data/geo/ca_raw/`, and `data/geo/eu_raw/`
(gitignored; re-fetch via each scope's `download_raw.sh`).
