# EU/UK AD plant inventory: pipeline plan (draft for review)

Status: DRAFT, 2026-09-25. Synthesised from the six scoping reports in this folder
(`scoping_uk.md`, `scoping_de.md`, `scoping_it_fr.md`, `scoping_dk_nl.md`, `scoping_eu_wide.md`,
`scoping_manure_to_ad.md`). To be reviewed by a statistics reviewer and an AD/biogas domain
reviewer before any build work.

## 0. Why

The Atlas's Europe scope decides whether AD+CCS is available in a NUTS-2 region (the "AD gate") and
whether it leads over slurry injection for wet manure (the `ad_maturity` score). Today both rest on
22 hand-placed cluster centroids in `data/processed/facilities_ad.json` with no traceable source,
plus 5 named plants. The UK is a single point (52.6N, -1.2E, r = 200 km) that gates 28/41 UK regions;
Scotland, NI, NE and SW England are excluded by circle geometry, not data. The NUTS-2 maturity
refinement is circular (built from the same hand-placed points). Country maturity scores are a
hardcoded dict with no per-country numbers behind them.

Goal: replace both with a documented, reproducible pipeline built from plant-level registers, with
explicit coverage and location-precision flags, validated against published national totals. Nice
to have: a primary-source manure-to-AD share per country (and per region where plant feedstock data
allow).

## 1. Source selection (from scoping)

| Country | Backbone (plant-level) | Coords | Gap-fillers | Known coverage issue | Validation total |
|---|---|---|---|---|---|
| UK | DESNZ REPD Q2-2026 (OGL) | OSGB, exact | EA Waste Data Interrogator / permits (England), Ofgem RER (RO accreditation), SEPA/NRW registers, OSM | REPD has 163 operational AD+SSD vs NNFCC 630 (NI: 8 vs 80). Sewage digesters: REPD has 12 | NNFCC Mar-2024 (630 plants, 593.6 MWe), DUKES |
| UK (enrichment) | NNFCC biogas-info operational xlsx (Mar 2024, postcode, feedstock tonnes) | postcode | — | **Licence forbids redistribution**; internal validation only unless NNFCC grants permission | — |
| Germany | MaStR Gesamtdatenexport (DL-DE-BY-2.0), tables EinheitenBiomasse, AnlagenEegBiomasse, EinheitenGasErzeuger, Lokationen, Katalog* | lat/lon (small private units may be withheld; to verify) | DBFZ Report 50 (substrate mix), LfL Bayern | Raw 11,419 EEG-Anlagen vs ~9,605 real plants: must dedup by Lokation/site and drop stale records | Fachverband Biogas Branchenzahlen 2025: 9,605 plants, 6,816 MWel, 290 biomethane |
| France | ODRÉ biomethane injection points (855, approx coords) + ODRÉ electricity registre (1,116 biogas, INSEE commune, 34.5% names "Confidentiel") | approx / commune centroid | Géorisques ICPE rubrique 2781 (exact coords, off-grid digesters; currently unreachable by script), AILE Bretagne CSV | Off-grid farm digesters (CITEPA: 1,412 agri methanisers in 2024) partly invisible without ICPE | SDES Mar-2026: 1,121 installations / 583 MW; CITEPA 1,412 agri |
| Italy | **No national source accessible yet**: GSE Atlaimpianti (403 WAF). Interim: regional ARPA "Impianti a bioenergia" (Emilia-Romagna verified: 268 biogas, WGS84, feedstock, ID_GSE) | exact (regional) | ARPA Lombardia / Veneto / Piemonte (to check), provincial RNDT layers | Po Valley coverage depends on GSE or other regional ARPAs | Terna 2024: 2,304 biogas plants / 1,473 MWe |
| Denmark | ENS "Liste over biogasanlæg 2025" (~150 plants, name only) | none; geocode | ENS Energiproducenttælling stamdata (184 biogas units, postcode, capacity), Evida grid-injection list (57), CVR business registry for addresses | Pure upgraders absent from EPT; manual geocoding required | ENS list count; Biogas Danmark |
| Netherlands | RVO SDE(+)(+) "Projecten in beheer" (651 AD rows) | address; 48% anonymised → PC4/town | CBS StatLine, Netbeheer groengas injectors (108), Emissieregistratie | Non-subsidised plants invisible; anonymised farm digesters imprecise | CBS: ~95 manure-digestion locations (2020), ~70 WWTP w/ biogas, ~40 other |
| Rest of EU+NO | EEA Industrial Reporting DB (CC-BY 4.0), IED activity 5.3(b)(i), filter AD vs composting | exact | National registers: PL KOWR (agri biogas), ES RAIPRE, AT E-Control/Biomethanregister, CZ ERÚ + CZBA map, SE Energimyndigheten | IED threshold ≥100 t/day misses farm AD; BE/NO/HU/PT/SK/small states unresolved | Eurostat nrg_bal_c R5300 (includes landfill+sewage gas: upper bound); EBA Stat Report (paywalled) |

Outreach (parallel, needs user): NNFCC/Alder BioInsights (redistribution permission), EBA (research
licence for plant database), GSE (bulk Atlaimpianti extract). Browser-assisted access (user's Chrome)
for GSE Atlaimpianti, Géorisques, UNFCCC CRT zips (works with ~6 s bot-challenge wait).

## 2. Common plant schema (`data/processed/ad_plants_eu.json`)

One record per physical site:

- `id` (stable: `<cc>-<source>-<source_id>`), `name`, `country`, `nuts2` (point-in-polygon)
- `lat`, `lon`, `loc_precision` ∈ {exact, address, postcode, commune, region}, `loc_uncertainty_km`
- `status` ∈ {operational, construction, decommissioned}; keep operational (+construction flagged)
- `ad_class` ∈ {agricultural, co_digestion, biowaste, industrial, sewage_sludge}; `manure_based` bool
  where knowable; `energy_crop_share` if known (DE/IT matter for Frontier eligibility, see §6)
- `output` ∈ {chp, upgrading, both, heat, unknown}
- capacity fields as reported: `cap_kwe`, `cap_biomethane_nm3h`, `cap_raw_biogas_nm3h`,
  `feedstock_tpa` and `manure_tpa` when reported
- derived: `biogas_nm3_yr` (with low/high), `co2_upgrading_t_yr` (concentrated stream, if upgrading),
  `co2_total_biogenic_t_yr` (all biogas carbon, if combusted), each with low/high
- provenance: `sources[]` (source key, source record id, source date, licence), `dedup_group`

## 3. Pipeline (`scripts/eu/ad/`)

1. `ingest_<source>.py` per source → `data/raw/ad/<source>/` (gitignored), stream-process to a
   standardised per-source parquet/JSON; delete raw where >50 MB (MaStR: extract ~5 XML members from
   the 3 GB zip via `zipfile`, then delete the zip).
2. `geocode.py`: OSGB→WGS84 (REPD); UK postcodes via ONS Postcode Directory (OGL); FR INSEE commune
   centroids; NL PC4 centroids; DK via CVR/DAWA address API. Never geocode from plant name alone.
3. `merge_dedup.py`: within-source site collapse (MaStR Lokation; SDE multiple rounds per site;
   EPT multiple engines), then cross-source matching (shared IDs where present: ODRÉ/GRDF id, ID_GSE;
   else distance ≤500 m + fuzzy name + capacity tie-break; FR "Confidentiel": commune + capacity +
   commissioning date). Unmatched ambiguous pairs written to a review CSV, not auto-merged.
4. `estimate_co2.py`: capacity → biogas → CO₂ (parameters in §5), with low/high.
5. `validate.py`: per-country plant counts / MWe / biomethane capacity vs national totals → coverage
   ratio table (written to METHODOLOGY and README). Hard fail if a country's cleaned count deviates
   >25% from its validation total without a documented reason.
6. `build_clusters.py`: data-derived clusters for display and gating (§4).
7. Rewire: `build_eu_infrastructure.py` reads the plant file instead of `facilities_ad.json` EU rows;
   `build_ad_maturity.py` EU branch recomputed (§4); regenerate Europe scope; before/after diff of
   recommendations per region; UK spinoff + two-pager flagged for regeneration.

## 4. How the plants feed the engine

**AD gate (avail.ad):** a region is AD-available if cumulative operational AD capacity (CO₂-stream
t/yr) within `PROC_RADIUS_KM["biogas_ad"]` (currently 15 km, i.e. the plant's own feedstock reach)
of any point in the region (not just the centroid) exceeds `AD_MIN_CAP_MTPA`. Question for review:
use region-polygon-to-plant distance rather than centroid distance, since NUTS-2 regions are large;
and whether manure regions should require a manure-accepting (agricultural/co-digestion) plant.

**Clusters (display + aggregation for CCS economics):** single-linkage clustering of plants with a
linkage distance (proposal 25 km) → cluster record with summed CO₂, plant count, dominant class,
convex hull. Replaces the hand-placed cluster points. Clusters matter because individual plants
are 1–30 kt CO₂/yr and CCS logistics need aggregation.

**AD maturity:** proposal to redefine the index directly as the **share of manure going to AD**
(from §7) where available, else plant-derived capacity density vs ENSPRESO manure potential,
normalised per country to the national inventory share. Removes the hardcoded COUNTRIES dict for
European countries. The threshold (0.15) needs re-deriving on the new basis.

**Coverage gaps:** where the cleaned register covers substantially less than the validation total
(e.g., UK REPD 163 vs 630), options: (a) no imputation, flag region as "coverage-limited"; (b)
impute missing plants spatially using manure density × national shortfall. Default proposal: (a)
for the gate (never invent a plant that enables a recommendation), (b) only as a sensitivity test.

## 5. CO₂ estimation parameters (to review)

- CHP plants: kWe → biogas via electrical efficiency η_el 0.38 (0.35–0.42), capacity factor
  0.85 (0.75–0.92), biogas CH₄ 55% (50–60%).
- Biogenic CO₂ in raw biogas (upgrading offgas, concentrated): CO₂ vol fraction ≈ 1 − CH₄ fraction.
- Total biogenic CO₂ if the CH₄ is also combusted on site: CH₄ + CO₂ carbon.
- Biomethane plants: from Nm³/h biomethane (97% CH₄) back to raw biogas.
- Which stream counts as the AD+CCS CDR: capture of upgrading CO₂ only (the biomethane is sold and
  its combustion CO₂ is not removed) vs CHP flue capture (all carbon). Needs a domain ruling.

## 6. Feedstock eligibility (Frontier)

Frontier excludes purpose-grown crops. German fleet substrate mass is ~49% energy crops / ~45%
manure (DBFZ Report 50 survey, not census); Italy is also crop-heavy. The carbon share from crops is
higher than their mass share (silage >> slurry dry matter). Need a rule: e.g. eligible CO₂ =
total × (1 − crop carbon share), with country-level crop shares from DBFZ / ISPRA / NNFCC tonnage
where plant-level data are missing.

## 7. Manure-to-AD share (nice to have)

Source: national GHG inventories, CRT Table 3.B(b) absolute N to "anaerobic digesters" by livestock
category (preferred over 3.B(a) % column, which has structural traps), fallback to NIR methodology
annexes. Pilot (see `scoping_manure_to_ad.md`): UK 4.86% of N excreted incl. pasture (2024); Italy
13.1% incl. pasture; Denmark 36% of slurry mass (2023, no AD modelled for solid/poultry); France
3–10% by category (head-count basis); NL ~3.6% of N (derived); Germany numerator only (174 Gg N) —
denominator needed. Harmonise to **% of total N excreted incl. pasture** where possible and carry the
native basis as a field. Scale to all ~29 countries via UNFCCC CRT zips (browser-assisted).
Regional shares: bottom-up only where plant manure tonnage exists (UK NNFCC internal; NL SDE themes;
DE via DBFZ class averages), clearly flagged as modelled.

Caveats: inventory shares are sometimes derived from the same plant databases (UK) so they are not
independent validation; poultry/solid-manure AD structurally invisible in DK/NL; basis differs.

## 8. Phasing

- **Phase A: UK** (highest exposure). REPD + EA permits + Ofgem RER + SEPA/NRW; NI strategy
  (NNFCC internal + FOI/EIR to NIEA/DAERA). Validate vs NNFCC counts. Rewire gate; regenerate UK
  spinoff and two-pager numbers.
- **Phase B: DE, NL, FR, DK, IT** (in that order, by data readiness).
- **Phase C: rest of EU+NO** via EEA IED + PL/ES/AT/CZ/SE registers.
- **Phase D: manure-to-AD** CRT extraction for all countries; maturity index redefinition.
- Throughout: METHODOLOGY.md §AD section, README sources table with licences, before/after diffs.

## 9. Open questions for reviewers

1. Coverage-gap handling (§4): no imputation for gating vs spatial imputation. Bias direction?
2. Dedup thresholds and false-merge risk (500 m, fuzzy names, FR confidential rows).
3. CO₂ basis (§5) and which stream counts as CDR; uncertainty propagation (low/high vs Monte Carlo).
4. Energy-crop eligibility rule (§6).
5. Redefining ad_maturity as manure-to-AD share; how to set the new threshold defensibly.
6. Gate geometry: centroid vs polygon distance; manure-accepting plants only?
7. Clustering linkage distance and whether clusters or plants should drive the gate.
8. Validation pass/fail criterion (25%?) and how to present coverage on the map.
