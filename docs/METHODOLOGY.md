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
- **Subnational (US states)** where rich open data exists, via the DOE Billion-Ton Report.
- Regions without compiled data render grey ("no data"); the long tail of small economies is
  not yet populated. This is deliberate — coverage follows data availability, and the thesis
  concentrates accessible waste biomass in the US, Europe, China, and Southeast Asia.

Geometry: Natural Earth 1:110m admin-0 countries + US states GeoJSON, slimmed to
`{id, name}` and bundled as JS (`data/geo/geometry.js`) so the page runs offline.

---

## 2. Feedstock supply

All tonnages are **recoverable** biomass in million tonnes oven-dry per year (Mt odt/yr),
except MSW which is wet tonnes. Estimates are modelled, not measured inventories; ranges
reflect cross-source spread.

| Feedstock | Method & primary sources |
|---|---|
| **Agricultural residues** | Crop production (FAOSTAT; USDA NASS for US; Eurostat for EU) × residue-to-product ratios × **~40% sustainable removal cap** (rest left for soil carbon/nutrients). Cross-checked against Slade et al. 2014, IEA 2022, Tripathi et al. 2019, JRC-S2BIOM (EU), DOE 2023 Billion-Ton Report (US, incl. state level). |
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
Country-level sums: **ag residues 2.31 Gt + forestry 0.60 Gt = 2.91 Gt odt/yr**, within the
thesis range of 2.8–4.0 Gt odt. At ~1.47 tCO₂/odt and ~90% efficiency that is ~3.85 Gt CO₂/yr
of gross potential — consistent with the thesis 2–5 Gtpa. Global MSW ≈ 1.7 Gt/yr (World Bank
global ≈ 2.0 Gt; we cover the major producers).

---

## 3. CO₂ storage

Proximity to viable storage is the key factor distinguishing geologic pathways (BECCS,
injection, WtE+CCS) from storage-independent ones (bio-oil, burial, biochar).

- **Projects** (`kind: site`): operational/under-construction/planned dedicated geologic
  storage and large CCS-with-storage projects — Sleipner, Snøhvit, Northern Lights, Quest,
  ADM Decatur (Illinois), Gorgon, Sinopec Qilu, Tomakomai, Porthos, Greensand, etc.
  Source: Global CCS Institute Facilities Database / Status Report (2023–24).
- **Basins** (`kind: basin`): basin-level theoretical capacity (Gt) graded by confidence
  (high/medium/low). Sources: US DOE NATCARB / NETL Carbon Storage Atlas, EU CO2StoP,
  CO2CRC (Australia), and regional storage assessments.

Basin capacities are theoretical and require site appraisal before they can be relied upon.
Large-biomass regions with **poor** storage — Sub-Saharan Africa (cratons), interior India
(low-permeability Deccan basalts), much of Southeast Asia — are deliberately represented with
low-confidence/low-capacity entries so the map surfaces the storage gap that pushes those
regions toward burial / bio-oil.

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
| Bio-oil sequestration | 45% | $140–360 | biochar/nutrients |
| Biomass burial | 90% | <$100–150 | none |
| Anaerobic digestion + CCS | 37% | $145–300 | low-C fuel |
| Biochar | 30% | ~$100–200 | nutrients |

### Logic (first match wins)
1. **Wet manure** → injection (storage near) else AD+CCS — *never combustion*.
2. **MSW** → WtE+CCS (storage near) else burial.
3. **Woody / concentrated dry ag** → BECCS (pulp & paper retrofit if anchor present) where
   storage is good/moderate; if storage poor → burial (excess nutrients) or bio-oil. Where
   storage is proximate, **injection** is the runner-up (it beats bio-oil there — see below).
4. **Diffuse dry ag** → **injection where geologic storage is proximate** (good access), else
   bio-oil (Charm roving model) where wells are distant, or biochar; burial if poor storage +
   excess nutrients.
5. **Mixed / fallback** → BECCS (good storage + retrofit), burial (poor storage), else BECCS.

#### Injection vs. bio-oil for dry residues
Frontier is bullish on Vaulted-style slurry injection: it handles the same dry crop residues
as bio-oil, has higher CDR efficiency (>90% vs. ~45%), and is cheaper on balance — so where
geologic storage (injection wells) is **proximate** it is preferred over bio-oil. Bio-oil's
advantage is only at distance: pyrolysis densifies the carbon (less-carbon-dense raw biomass is
expensive to haul), so it wins when wells are far. The engine therefore routes dry-residue
removal to **injection at good storage access** and **bio-oil at moderate/poor access**. In
excess-nutrient regions where injection leads, **burial** is surfaced as the alternative rather
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

### Frontier exclusions (flagged, never recommended)
- **Purpose-grown energy crops** — land-use competition; thesis sourcing principles.
- **RNG + CCS** — complex; Frontier not pursuing offtakes (thesis §3.4). AD/manure regions flagged.
- **Corn-ethanol + CCS** — food/land competition, marginal additionality; flagged where local
  ethanol capacity exists (US corn belt). (Brazilian sugarcane ethanol is *not* excluded.)
- **Burial** carries a mandatory durability caveat (Isometric 2024 protocol projects 1,000-yr;
  Frontier pursuing via prepurchase, not offtake).

---

## 6. Caveats

- Tonnages are modelled estimates, not measured inventories. Ranges reflect cross-source spread,
  not formal confidence intervals.
- **Country-level analysis cannot capture sub-national feedstock/storage mismatch** (e.g. interior
  vs. coastal China; corn belt vs. the rest of the US). National recommendations for large,
  heterogeneous countries (US, China, India, Russia, Brazil, Canada, Australia) are rollups and
  carry a caveat to that effect; the US is shown at state resolution to mitigate this.
- Storage basin capacities are theoretical and require site appraisal.
- The tool informs strategy; it does not substitute for project-level diligence (biomass sourcing
  verification, LCA boundaries, additionality, execution risk).

---

## 7. Reproducing the data pipeline

```
scripts/build_geo.py             # slim Natural Earth geometry -> data/geo/geometry.js
                                 # (regional feedstock + storage + facilities JSON compiled by subagents)
scripts/merge_validate.py        # merge regional feedstock files -> feedstocks.json; sanity checks
scripts/build_recommendations.py # run the recommendation engine -> recommendations.json
scripts/bundle_data.py           # bundle processed JSON -> src/data_bundle.js (file:// safe)
```

Then open `src/index.html` directly in any browser.
Data schema: `data/SCHEMA.md`. Engine spec: `data/ENGINE_SPEC.md`.
