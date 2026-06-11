# BiCRS / BECCS Feedstock & Storage Site Map — Project Plan

**Owner:** Zeke Hausfather (Berkeley Earth / Frontier context)
**Created:** 2026-06-11
**Status:** Planning complete → ready for `/goal` build loop

---

## 1. Goal

An interactive, browser-openable map that overlays **biomass feedstock supply** with
**CO₂ storage options** (existing + potential) and computes a **"best use of biomass"
recommendation** per region, grounded in Frontier's BiCRS purchasing POV.

The map operationalizes the thesis doc's central claim: *the optimal BiCRS pathway is
local.* It depends on (a) feedstock type — wet vs. dry, woody vs. herbaceous; (b)
feedstock density — concentrated vs. diffuse; (c) proximity to geologic CO₂ storage;
(d) nutrient status of the local ecosystem; (e) presence of retrofittable facilities.

## 2. Confirmed decisions (from user)

| Decision | Choice |
|---|---|
| **Scope / resolution** | Global country-level everywhere; subnational where rich open data exists (US states, EU/NUTS countries, key provinces of China/Brazil/Canada/India). |
| **Audience** | Internal Frontier strategy / diligence tool. Prioritize data transparency, source citations, uncertainty ranges, and explicit recommendation rationale. |
| **Data sourcing** | Exhaustive, but stage authoritative datasets locally (hardcode known sources rather than scrape everything live). Live web research used to compile + cite. |

## 3. Pathways covered (from thesis §1.1 / §2.1)

Ranked roughly most→least preferred per Frontier KPIs:

1. **BECCS** (heat/electricity, hydrogen, pulp & paper) — CDR eff >80%, energy co-product, low durability risk. Best when feedstock concentrated + near storage + retrofit available.
2. **WtE + CCS** — flue gas ~50–60% biogenic. For concentrated MSW.
3. **Biomass waste injection** (Vaulted) — CDR eff >90%, for wet wastes (manure, human/WWTP). PFAS destruction co-benefit.
4. **Bio-oil sequestration** (Charm) — CDR eff ~45%, distributed/modular, returns biochar+nutrients. For diffuse ag residues far from storage.
5. **Biomass burial** (Kodama, Graphyte) — CDR eff >90%, simple/low-cost, no storage needed. For regions w/o geologic storage + ample/excess nutrients. Durability still open.
6. **Anaerobic digestion + CCS** — ~30–44%, wet/distributed. (RNG variant explicitly *not* pursued by Frontier — flag, don't recommend.)
7. **Biochar** — CDR eff ~30%, returns nutrients. Distributed. Lower preference.

## 4. KPI / recommendation framework (encode the thesis logic)

Ranked KPIs (thesis §1.4):
1. **CDR efficiency** = [CO₂stored − CO₂emitted] / CO₂stored (1,000-yr durability).
2. **Emissions-avoiding co-products** — prefer non-hydrocarbon (electricity > fuels).
3. **Other co-benefits** — nutrient return, methane avoidance, PFAS destruction.

### Recommendation rules (transparent, per region)
Inputs per region: dominant feedstock type & moisture, feedstock density, distance to
nearest viable geologic storage, nutrient status, count/size of retrofittable facilities.

```
IF feedstock is predominantly WET (manure, human/WWTP, food waste):
    → Biomass waste injection (if storage near) ELSE AD+CCS
    (never combustion — thesis §2.2)
ELIF feedstock is dry & woody & CONCENTRATED & storage near:
    IF retrofittable pulp&paper / bioenergy facility present → BECCS retrofit (top)
    ELSE → BECCS greenfield
ELIF feedstock is dry ag residue & DIFFUSE:
    IF storage far → Bio-oil sequestration (Charm roving model) OR Biochar
    ELSE → consider BECCS vs bio-oil on transport cost
ELIF MSW CONCENTRATED (urban):
    → WtE + CCS
ELIF no viable geologic storage AND excess nutrients:
    → Biomass burial (flag durability caveat)
```
Each region returns: recommended pathway, runner-up, numeric KPI score, and a
plain-language rationale citing which inputs drove the choice. Cost band shown per
pathway from thesis §2.1 ($/tCO₂).

## 5. Data model

### `data/processed/feedstocks.json` — keyed by ISO3 (+ subnational id where available)
Per region, annual quantities (Mt oven-dry-tons/yr) + derived CDR potential:
- `ag_residues_odt` — crop residues (cereal straw, corn stover, bagasse, etc.)
- `forestry_residues_odt` — logging + processing residues
- `msw_total_t`, `msw_biogenic_frac` (US ~0.61, EU ~0.50), `msw_treatment` (% WtE/landfill/dump)
- `animal_manure_odt` (or biogas Mtoe), `human_wwtp_odt`
- `cdr_potential_gt` at configurable efficiency (default 90% for woody/ag, pathway-specific in engine)
- `nutrient_status` (low / moderate / excess) — for burial vs. removal logic
- `sources[]` — citation + year + uncertainty range per field

### `data/processed/facilities.json` — point features
- pulp & paper mills, ethanol plants, WtE incinerators, large bioenergy, biogas/AD
- fields: `lat`, `lon`, `type`, `capacity`, `est_biogenic_co2_tpa`, `retrofit_score`, `operator`, `source`

### `data/processed/storage.json`
- existing CCS / CO₂ injection sites (points) — Global CCS Institute facility db
- basin-level geologic storage potential (polygons or centroids): `type` (saline / depleted O&G / basalt), `capacity_gt`, `confidence`, `source`

### `data/processed/recommendations.json` — keyed by region
- output of §4 engine: `recommended`, `runner_up`, `kpi_score`, `cost_band`, `rationale`, `caveats[]`

### Geometry
- Country polygons: Natural Earth `ne_110m_admin_0_countries` (vendored GeoJSON).
- Subnational: US states, EU NUTS-0/1 where used. Simplified for web payload.

## 6. Primary data sources (stage locally, cite each)

| Layer | Source |
|---|---|
| Ag residues | FAOSTAT crop production × residue ratios (Slade et al. 2014; IEA 2022; Tripathi 2019 — referenced in thesis) |
| Forestry residues | FAO FRA / roundwood production; Slade et al. 2014 |
| MSW | World Bank *What a Waste 2.0* (country-level, treatment shares) |
| Animal/human waste | IEA biogas outlook; FAO livestock |
| Geologic storage | Global CCS Institute facilities db; regional storage atlases (US NATCARB, EU CO2StoP, etc.) |
| Facilities | Industry databases per type (pulp & paper, ethanol, WtE, biogas registries) |

## 7. Tech stack

- **Single self-contained `src/index.html`** + **Leaflet** (vendored, no API key).
- Vanilla JS modules in `src/`; data loaded from `data/processed/*.json`.
- Layer control (toggle feedstock type, facilities, storage, recommendation overlay).
- Choropleth for feedstocks; graduated/categorical point markers; popups with
  citations + uncertainty; legend + methodology panel.
- Opens by double-clicking the HTML file — no server required (use relative fetch or
  inline data if `file://` fetch is blocked; fallback: bundle data into a JS file).

## 8. Model orchestration

- **Fable (me):** orchestrate, evaluate data quality/consistency, design map UI/UX, assemble + verify final deliverable.
- **Sonnet / Haiku subagents:** parallel per-region/per-layer data compilation + web research + JSON generation against the schema in §5.
- **Opus subagent:** encode/validate the §4 recommendation engine and heavier regional synthesis where judgment is needed.

## 9. Build phases (for `/goal`)

1. **Scaffold + geometry** — vendored Leaflet, country GeoJSON, base map shell that opens in browser. ✅ structure created.
2. **Feedstock data** — compile `feedstocks.json` globally (country) + subnational for rich regions, with citations + uncertainty.
3. **Storage data** — `storage.json`: existing CCS sites + basin potential.
4. **Facilities data** — `facilities.json`: retrofit candidates.
5. **Recommendation engine** — implement §4, produce `recommendations.json`.
6. **Map UI** — all layers, toggles, popups, legend, methodology/citations panel, recommendation overlay.
7. **QA pass** — data sanity checks, totals vs. thesis Gtpa figures, cross-source consistency, browser test.
8. **Docs** — `docs/METHODOLOGY.md` (sources, assumptions, formulas, caveats).

## 10. Sanity checks (tie back to thesis)

- Global ag + forestry residue CDR potential should land ~2–5 Gtpa (thesis §1.3).
- MSW CDR potential ~500–700 Mtpa midcentury.
- Most accessible waste biomass concentrated in US, Europe, China, SE Asia.
- Flag, don't recommend: purpose-grown crops, RNG+CCS, corn ethanol (Frontier exclusions).
