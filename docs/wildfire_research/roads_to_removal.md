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
