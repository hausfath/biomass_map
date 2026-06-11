# Best-Use-of-Biomass Recommendation Engine — Spec

Implement as a deterministic Python script `scripts/build_recommendations.py` that reads
`data/processed/{feedstocks,storage,facilities}.json` and writes
`data/processed/recommendations.json` (one record per feedstock region).

The logic must faithfully encode Frontier's framework (PLAN.md §4 and the BiCRS thesis).
This is decision-support, not a black box — every output carries a transparent rationale.

## Pathway constants (from thesis §2.1)

| pathway | key | cdr_efficiency | cost_band ($/tCO2) | co_product | needs_geologic_storage |
|---|---|---|---|---|---|
| BECCS (heat/elec) | `beccs` | 0.80 | "$200–225 (→<$100 at scale)" | energy | yes |
| BECCS pulp & paper | `beccs_pp` | 0.80 | "$200–225" | energy/none | yes |
| WtE + CCS | `wte_ccs` | 0.55 | "~$100–200" | energy | yes |
| Biomass waste injection | `injection` | 0.90 | "$125–285" | PFAS destruction | yes |
| Bio-oil sequestration | `bio_oil` | 0.45 | "$140–360" | biochar/nutrients | no |
| Biomass burial | `burial` | 0.90 | "<$100–150" | none | no |
| AD + CCS | `ad_ccs` | 0.37 | "$145–300" | low-C fuel | partial |
| Biochar | `biochar` | 0.30 | "~$100–200" | nutrients | no |

CDR efficiency = fraction of feedstock carbon durably stored. 1 odt biomass ≈ 1.47 tCO2.

## Step 1 — storage proximity
For each region compute `nearest_storage_km` = min haversine distance from the region
`centroid` (lon,lat) to: (a) any `kind:"site"` with status operational/construction, and
(b) any `kind:"basin"` with confidence in {high, medium} and capacity_gt ≥ 1.
Classify `storage_access`:
- "good" if nearest_storage_km < 500 to a high/medium basin OR operational site
- "moderate" if < 1000
- "poor" otherwise
Also set `storage_access = "poor"` regardless of distance if the only nearby basins are
low-confidence (this captures Sub-Saharan Africa cratons, Deccan basalts, etc.).

## Step 2 — retrofit availability
For each region, find facilities in the same country (match facility.country to region
country: for US states, country="USA"). `has_retrofit` = any facility with retrofit_score
in {high, medium}. Capture the best matching facility name + type for the rationale.

## Step 3 — decision tree (apply in order; first match wins)
Use region fields: `dominant_feedstock` (ag_dry|forestry_woody|msw|manure_wet|mixed),
`feedstock_density` (concentrated|diffuse), `nutrient_status` (low|moderate|excess),
plus `storage_access` and `has_retrofit`.

```
1. dominant_feedstock == "manure_wet"  → injection if storage_access in (good,moderate)
                                          else ad_ccs
2. dominant_feedstock == "msw"         → wte_ccs if storage_access in (good,moderate)
                                          else burial
3. dominant_feedstock in (forestry_woody) OR (ag_dry & concentrated):
     IF storage_access == "good":
         recommended = beccs_pp if has_retrofit and a pulp_paper/bioenergy facility exists
                       else beccs
         runner_up   = bio_oil
     ELIF storage_access == "moderate":
         recommended = beccs ; runner_up = bio_oil
     ELSE (poor storage):
         IF nutrient_status == "excess": recommended = burial ; runner_up = bio_oil
         ELSE:                           recommended = bio_oil ; runner_up = biochar
4. dominant_feedstock == "ag_dry" & diffuse:
     IF storage_access == "good": recommended = bio_oil ; runner_up = beccs
     ELIF nutrient_status == "excess" and storage_access=="poor":
                                   recommended = burial ; runner_up = bio_oil
     ELSE:                         recommended = bio_oil ; runner_up = biochar
5. mixed / fallback:
     IF storage_access == "good" and has_retrofit: recommended = beccs ; runner_up = injection
     ELIF storage_access == "poor": recommended = burial ; runner_up = bio_oil
     ELSE: recommended = beccs ; runner_up = bio_oil
```

## Step 4 — KPI score (for ranking/coloring; 0–100)
Encode the thesis KPI priority: CDR efficiency FIRST, then emissions-avoiding co-product,
then other co-benefits.
```
score = 60 * cdr_efficiency
      + 25 * (1 if co_product == energy else 0.5 if co_product in (low-C fuel,) else 0)
      + 15 * (co_benefit_factor: 1 if PFAS/nutrients/methane-avoidance else 0)
      − storage_penalty (10 if recommended needs storage but storage_access=="poor")
```
Round to integer.

## Step 5 — CDR potential
`cdr_potential_mtpa` for the recommended pathway:
- For ag/forestry/mixed dry pathways: (ag_residues + forestry_residues, Mt odt) × 1.47 × cdr_efficiency
- For msw/wte: msw_total × msw_biogenic_frac × ~1.0 tCO2/t × cdr_efficiency
- For manure/injection: animal_manure (+human_wwtp) odt × 1.47 × cdr_efficiency
Give value only (best estimate); note assumptions in rationale.

## Output record
```json
{
  "id": "USA", "name": "United States",
  "recommended": "beccs", "recommended_label": "BECCS (heat/electricity)",
  "runner_up": "bio_oil", "runner_up_label": "Bio-oil sequestration",
  "kpi_score": 78,
  "cdr_efficiency": 0.80,
  "cost_band": "$200–225 (→<$100 at scale)",
  "cdr_potential_mtpa": 265.0,
  "storage_access": "good", "nearest_storage_km": 120,
  "has_retrofit": true, "anchor_facility": "ADM Decatur (ethanol)",
  "rationale": "Concentrated woody+ag residues near high-confidence Gulf Coast/Illinois saline storage with existing retrofittable pulp & paper and bioenergy facilities → BECCS retrofit maximizes CDR efficiency (80%) plus energy co-product, Frontier's top-preferred use of biomass.",
  "caveats": ["..."],
  "flags": []   // e.g. ["RNG concern"], ["corn-ethanol excluded"] where relevant
}
```

## Frontier exclusions (set in `flags`, never recommend)
- Never recommend purpose-grown crops, RNG+CCS, or corn-ethanol+CCS.
- If a region's biomass story leans on these, add a flag noting the exclusion + thesis reason.
- For burial recommendations, ALWAYS add caveat: "Durability still being validated (Isometric 2024 protocol projects 1,000-yr); Frontier pursuing via prepurchase not offtake."
- For AD/biogas-heavy regions, add flag "RNG+CCS is complex; Frontier not pursuing offtakes (thesis §3.4)".

The script must print a summary: count of regions per recommended pathway, and global
CDR potential summed across recommended pathways. Validate output is parseable JSON.
