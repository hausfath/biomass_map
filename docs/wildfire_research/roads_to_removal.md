# Roads to Removal (R2R) forestry data: wildfire-fuel-treatment biomass potential

**Source.** County-level forestry data from the LLNL-led *Roads to Removal: Options for Carbon Dioxide
Removal in the United States* (Pett-Ridge et al., December 2023;
[LLNL announcement](https://www.llnl.gov/article/50686/new-analysis-outlines-national-opportunities-remove-co2-gigaton-scale)),
shared by Sinead Crotty of the R2R team (personal communication, October 2026), together with the
acquisition costs below. Raw workbook kept out of git: `data/geo/us_raw/r2r/Roads to Removal Forestry Data.xlsx`.
Ingested by `scripts/us/build_fuels_r2r.py` → `data/processed/fuels_r2r_us.json`.

## Scenario (from the workbook's notes)
- 70 M acres of priority wildfire-hazard areas: 40 M USFS + 30 M other ownership, thinned once over
  10 years (~7 M ac/yr). "For 2050, we are assuming that the USFS achieves their desired thinning rate
  of 7 million acres per year."
- Selection: all states; trees < 12 in diameter and tops; treatment to 80% of full stocking; slope and
  distance-to-road classes (for costing); reserved land removed; national wildfire hazard.
- Caveats in the workbook: does not account for re-treatment at 3–10 year intervals; may be
  conservative because a first thinning likely goes to 60% stocking or less, not 80%.
- Totals: 1.214 billion short BDT over 10 yr → 121.4 M short BDT/yr → **110.1 Mt dry/yr** (×0.9072)
  → 55.0 Mt C/yr → 202 Mt CO₂e/yr (workbook's own conversion, 0.5 C per dry ton). 182 counties in
  12 western states (AK, AZ, CA, CO, ID, MT, NM, NV, OR, UT, WA, WY); 174 with non-zero biomass.
  Mean 17.3 short BDT/acre (whole small trees + tops, not just slash).

## Acquisition cost by accessibility class (R2R team, personal communication)
"we divided into different accessibility classes (by slope and distance to road) so that we could
assign a different cost to acquiring each … These cost estimates were built off of Pan et al. 2007 and
Petitmermet et al. 2019." Also in `data/processed/r2r_accessibility_costs.csv`.

| Accessibility | Short BDT/yr | Cost |
|---|---|---|
| 0–500 ft from roads, 0–20% slope | 24,334,182.6 | $77.80/BDT |
| 500–1,000 ft from roads, 0–20% | 13,652,321.9 | $81.98/BDT |
| 1,000 ft–0.5 mi from roads, 0–20% | 23,909,273.1 | $99.85/BDT |
| 0–500 ft from roads, 20–40% | 22,460,307.1 | $98.52/BDT |
| 500–1,000 ft from roads, 20–40% | 13,077,805.7 | $102.70/BDT |
| 1,000 ft–0.5 mi from roads, 20–40% | 23,928,559.4 | $120.57/BDT |

The per-class tonnages are the workbook's annual ("BDT/10 years") totals; `build_fuels_r2r.py`
reproduces them exactly. BDT-weighted mean: **$97.56/short BDT**. Costs are not yet used by the engine
(saved for later; shown per county in the detail panel).

## How the Atlas uses it
- A North-America-scope map layer, **"Wildfire-fuels residue (R2R potential)"**, replacing the earlier
  Wildfire Crisis Strategy scale-up layer (today's treatment pattern ×1.90 → 13.1 Mt dry/yr, now kept
  only as a documented low bound). Not added to forestry totals or recommendations.
- Comparison in the 176 counties both cover: R2R 109.5 Mt dry/yr vs our completed-treatment stream
  4.2 Mt and the WCS scale-up 8.1 Mt; county correlation with the completed stream r = 0.34. R2R
  weights productive coastal forests (Lane OR, Humboldt and Mendocino CA) far more than where
  treatments happen today. The gap reflects (i) whole small trees + tops (17.3 BDT/ac) vs slash on
  treated units (6–13), and (ii) all 70 M acres mechanically thinned vs today's mostly-burn mix.

## Scenario test: R2R in the recommendation engine (2026-10-22)
Each county's wildfire-fuels component set to max(current completed-treatment stream, R2R tranche) — not
the sum, since R2R's priority-area thinning would subsume today's treatments — then US transport and
recommendations rerun (committed files untouched). Baseline: US recommended-pathway CDR 349.7 Mt CO₂/yr;
western 12 states 52.3 (444 counties); the 174 R2R counties 27.3.

| Scenario | Forestry added (Mt dry/yr) | Counties changing recommendation | US CDR (Mt CO₂/yr) | Western-12 CDR |
|---|---|---|---|---|
| A: full R2R (all 6 cost classes) | +106.0 | 27 | 349.7 → 469.5 (+119.8) | 52.3 → 172.1 |
| B: classes ≤ $100/short BDT (1–4) | +72.5 | 26 | → 432.0 (+82.3) | → 134.6 |
| C: classes ≤ $82/short BDT (1–2) | +30.5 | 19 | → 383.2 (+33.5) | → 85.8 |

All changes are in R2R counties. Main transitions (A): HTL → BECCS 8, HTL → bio-oil 5, no-option → BECCS 4,
HTL → burial 3, injection → BECCS 2. About 95% of the added CDR (113 of 120 Mt in A) is in counties whose
recommendation does not change — mostly forestry-dominant counties already on burial / bio-oil / BECCS,
which simply get more biomass. CDR gain by pathway (A): burial +53, bio-oil +45, BECCS +17, BECCS p&p +6.
Caveats: engine uses 1.47 tCO₂/odt (40% C) vs R2R's 0.5 C; possible overlap with BT23 forestry (small-tree /
thinning material) not netted; R2R is a 10-yr technical potential, not current supply.

**Adopted as a map toggle (2026-10-22):** scenario B is the "R2R thinning (≤$100/BDT)" option of the North
America scope's *Supply scenario* control; the map opens on "Today". `scripts/us/build_r2r_scenario.py`
(build_all.sh step 11) builds it with the unchanged engine and writes only an overlay of the records that
differ from today (`src/data_bundle_us_r2r.js`, ~0.6 MB, lazy-loaded): 264 recommendation records, 169
feedstock and 26 transport overrides. Full scenario outputs stay in `data/processed/_scenarios/`
(gitignored). Deep link: `#scope=na&scen=r2r`.
