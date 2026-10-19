# US wildfire-risk-reduction residues: data-source scoping (county level)

Scoped 2026-10-19. Nothing was built. Scratch files (PDFs, queries) in
`/private/tmp/claude-501/-Users-hausfath-Desktop-Climate-Science-BiCRS-Map/36ce493b-82b8-47dd-b0cc-937ec866f26e/scratchpad/wf_us/`.
"Verified" = I opened the primary page/file or ran the query myself this session. Anything from a search snippet or
summary is marked UNVERIFIED. No raw data >50 MB was downloaded (HEAD only for the 1.3 GB TWIG zip).

## Headline

1. **TWIG (Treatment and Wildfire Interagency Geodatabase / SWERI "Treatment Index")** is the right backbone extension. It already merges
   FACTS (USFS), NFPORS + IFPRS (DOI: BLM, NPS, FWS, BIA), a CAL FIRE/CARB interagency tracker snapshot, and ~two dozen state forestry agencies,
   with a live ArcGIS REST endpoint that answers server-side statistics queries. No need to scrape NFPORS directly (the old host is gone).
2. **There is no published county-level fuel-treatment residue dataset to validate against.** BT23's "fire reduction thinnings" is
   only 69 county rows in two landscapes (AZ 4FRI, WA Central Washington) plus a national extrapolation of 1.8-2.9 Mdt/yr that is not county-resolved.
3. **Per-acre yield is the dominant uncertainty** (published numbers span ~0.6 to ~19 dry t/ac depending on what is counted). The tool's 6-12 odt/ac is defensible
   only for treated acres that are actually piled/removed in dry western forest. It is too high as an average over all "mechanical" acres.

---

## 1. Source table

| # | Source | URL | Publisher | Licence | Date / version | Format / size | Coverage | Unit | Key fields | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **TWIG / Treatment Index, live REST** | https://gis.reshapewildfire.org/arcgis/rest/services/Hosted/Treatment_Index_View/FeatureServer/0 | SWERI (NAU/CSU et al.) + Innovate Inc. | Data CC BY 4.0; code GPLv3 (per reshapewildfire.org resource page) | Live; metadata dated Oct 2025; `returnCountOnly` run 2026-10-19 = **1,559,750** records | ArcGIS FeatureServer, maxRecordCount 1000, supports outStatistics | USFS (FACTS HFT + FACTS Common Attributes), DOI (NFPORS + IFPRS), CAL FIRE tracker, ~25 state agencies; 1984+ | polygon | `acres, treatment_date, status (Completed/Planned/Started/Other), agency, state, type, activity, method, equipment, category, twig_category, identifier_database, total_cost, error, fund_source` | Y (queried) |
| 1b | TWIG full download | https://sweri-treatment-index.s3.us-west-2.amazonaws.com/treatment_index.zip | same | CC BY 4.0 | Last-Modified 2026-10-19 | zipped file geodatabase, **1,302,557,768 bytes (1.3 GB)** HEAD only; not downloaded | same | polygon | same | Y (HEAD) |
| 1c | TWIG static archive (Scientific Data paper) | https://doi.org/10.5281/zenodo.15851622 ; paper https://doi.org/10.1038/s41597-025-05859-z | Call et al. 2025 | CC BY 4.0 | v1, 10 Jul 2025 | `TWIG_treatment_index_20250709.zip`, 1.4 GB | FACTS + NFPORS only; federal | polygon | as above | Y (Zenodo page, paper text) |
| 2 | **FACTS Hazardous Fuel Treatment Reduction (current backbone)** | https://data.fs.usda.gov/geodata/edw/ (e.g. `Actv_CommonAttribute_PL_Region0X.zip` for Common Attributes) | USFS EDW | public domain / CC (Data.gov lists CC Attribution - UNVERIFIED for exact layer) | n/a | file geodatabases by region | NFS only | polygon | as in current pipeline | Y (URLs from Call et al. Table 1; not re-opened) |
| 3 | **NFPORS REST** `usgs.nfpors.gov/arcgis/rest/services/treatmentPoly/FeatureServer/0` | (cited in Call et al. Table 1) | DOI | n/a | **Host no longer resolves** (`getaddrinfo ENOTFOUND` via WebFetch; curl HTTP 000) on 2026-10-19 | n/a | n/a | n/a | n/a | Y (dead) |
| 4 | **IFPRS / InFORM open data MapServer** `gis.inform-fuel-post-fire.firenet.gov/server/rest/services/OpenData/InFORM_Fuels_Treatments_and_Activities/MapServer` | (surfaced in search) | DOI OWF | "not subject to copyright constraints" (search snippet, UNVERIFIED) | TLS cert expired 2026-01-17; all layer queries return `Service not found` (404) | n/a | n/a | n/a | n/a | Y (unavailable today). IFPRS is already inside TWIG (44.4 M ac, 30,766 records), so use TWIG. |
| 5 | **CA Interagency Treatment Dashboard** | https://wildfiretaskforce.org/treatment-dashboard/ | CA Wildfire & Forest Resilience Task Force / CAL FIRE / CARB | not stated on page | v2.0 "now includes data from 2024" (page text) | ESRI feature services (points/lines/polygons) + geodatabase on `portal.sparcal.sdsc.edu`; portal returned HTTP 403 to curl | CA, all ownerships except local/tribal; ~60 activities; acres tracked by ownership to avoid double counting | polygon | n/a | Partly: page read; data host 403. Its 2021-22 content is already in TWIG (row 1). |
| 6 | **BT23 forestry download** | https://bioenergykdf.ornl.gov/bt23-forestry-download | ORNL / DOE BETO | not stated; login required | BT23 (2023; chapter PDF posted 2024-03) | CSV after login; 88,885 rows | CONUS counties; scenarios near-term / mature-market low-med-high / Emerging; subclasses incl. **"Fire reduction thinnings"** (69 rows, resource "Mixedwood thinning residues", owner "Public") | county | dt, BTU, acres | Y (page); data not downloaded (login) |
| 7 | **BT23 forestry chapter** | https://www.energy.gov/sites/default/files/2024-03/beto-2023-billion-ton-report_4-forestry.pdf | DOE | public | 2024-03 | PDF 3.5 MB | CONUS | national + case studies | Table 4.1-4.4, text | Y (read) |
| 8 | **LLNL Getting to Neutral (2020)** | https://www.bioenergy.org.nz/documents/resource/Getting_to_Neutral.pdf (mirror; official LLNL URL guessed from search result returned 404) | Baker et al., LLNL-TR-796100 | n/a | Jan/Aug 2020 | PDF 8.4 MB | California counties; "Forest Management" residue 15.1 M BDMT/yr (county in Appendix B Table S4) | county | BDT/yr | Y (text read; Table S4 not extracted) |
| 9 | **LLNL Roads to Removal (2023)** | https://roads2removal.org | LLNL et al. | n/a | Dec 2023 fact sheets | PDF fact sheets; report on Google Drive | national, 3,143 counties on interactive maps | county | n/a | N for county residue: site lists no data download; fire-reduction not identified as a distinct biomass source. Method and data NOT verified. |
| 10 | **Rummer et al. 2005, RMRS-GTR-149** | https://www.fs.usda.gov/rm/pubs/rmrs_gtr149.pdf | USFS RMRS | public | Mar 2005 | PDF 316 KB | 15 western states, state-level | state | Table 5/6 yields by forest type | Y (read) |
| 11 | **CA Forest Biomass Pile Data Collection Report** | https://gaftp.epa.gov/Air/aqmg/baker/info/california-forest-biomass-pile-data-collection-report.pdf (mirror; bof.fire.ca.gov link returns 403 to curl) | CLERE Inc. for CA Board of Forestry JIWPI, 2023 | n/a | 2023 (data 2017-2021) | PDF 3.9 MB, 99 pp | CA | statewide / air district | PFIRS tons/ac | Y (read key passages) |
| 12 | **Barker, Voorhis, Crotty 2024/25** | https://doi.org/10.3389/ffgc.2024.1496190 | Frontiers For. Glob. Change 7 | CC BY | pub. 23 Jan 2025 | HTML | 11 NFs in CA/OR/WA, FACTS 2019-2023 | forest | BDT/ac, $/ac | Y (first 100k chars of page read) |
| 13 | USFS post-fire salvage report (2018) | https://www.fs.usda.gov/sites/default/files/media_wysiwyg/final_post-fire_treatment_salvage_report.pdf | USFS | public | May 2018 | PDF | NFS 2007-2016 | national | salvage acres | UNVERIFIED (search snippet only) |
| 14 | WCS Progress Summary FS-1187e | https://www.fs.usda.gov/sites/default/files/fs_media/fs_document/WCS-Progress-Summary.pdf | USFS | public | Nov 2022 | PDF 7.1 MB | NFS + others | national | targets | Y (text extracted) |

### What is not available
- **DOI NFPORS bulk download via NIFC Open Data:** not found. The NFPORS app is restricted; the REST host is dead; IFPRS open-data service is down (expired cert, 404). TWIG is the practical access route.
- **LANDFIRE / USGS "Public Events Geodatabase" and NIFC "Interagency Fuel Treatment" layers:** NOT investigated individually (search returned nothing); TWIG supersedes them for treatments. Open item.
- **Oregon/Washington trackers:** WA DNR (11,682 records, 360,712 ac) and Oregon Dept. of Forestry (390 records, 2,895 ac, "2025 Update") are already in TWIG. Standalone trackers not opened.
- **Roads to Removal county-level residue data and FIA BioSum/Fuel Treatment Evaluator outputs:** not located as downloadable.

## 2. TWIG contents (my queries, 2026-10-19, `outStatistics`, live endpoint)

Total 1,559,750 records. By `status`: Completed 1,312,019 records / 126.7 M ac; Planned 245,425 / 49.7 M ac; Other 2,141 / 1.15 M ac; Started 165 / 0.05 M ac.
By `identifier_database` (acres): FACTS Hazardous Fuels 64.5 M; IFPRS 44.4 M; FACTS Common Attributes 35.9 M; NFPORS 24.0 M; NASF (state) 8.7 M; NGO 0.14 M.
By `agency` (all years, all statuses, M ac): USFS 100.5; BLM 22.8; NPS 8.0; FWS 6.6; CAL FIRE tracker 5.2; BIA 2.9 (+2.9 BIA Tribal); Virginia DoF 1.1; Colorado SFS 0.61; DOD 0.54; WA DNR 0.36.
By `twig_category` (M ac): Mechanical 81.9; Planned Ignition 71.4; Unplanned Ignition 9.1; Chemical 8.8; Biological 6.1.

**Completed, `twig_category = Mechanical`, acres by calendar year of `treatment_date` (M ac; top agencies, k ac):**

| Year | Total | USFS | BLM | Other notable |
|---|---|---|---|---|
| 2018 | 1.53 | 1,047 | 261 | Virginia 107 |
| 2019 | 1.94 | 1,159 | 397 | Colorado SFS 133 |
| 2020 | 1.69 | 1,155 | 301 | |
| 2021 | 1.50 | 928 | 282 | FWS 27 |
| 2022 | 6.52 | 1,027 | 414 | **CAL FIRE tracker 4,716 (artifact, see below)** |
| 2023 | 2.04 | 1,146 | 382 | FWS 152 |
| 2024 | 2.35 | 1,118 | 701 | FWS 167 |
| 2025 (partial) | 2.09 | 1,012 | 596 | |

Caveats on these numbers (all verified from my queries, interpretation mine):
- The CAL FIRE/CARB tracker records all carry dates 2021-05-28 to 2022-12-31 (24,939 records, 5.22 M ac). Its acres include herbicide (1.6 M ac), mowing (1.4 M ac), chipping (0.83 M ac), grazing, etc., and it is a multi-agency compilation that very likely duplicates FACTS/NFPORS records. Do not add it to USFS/BLM without geometry-level dedup.
- `twig_category = Mechanical` includes mowing, lop-and-scatter, crushing, mastication. These do not remove material. By `type`, completed USFS mechanical 2018-2024 (k ac): Thinning 3,148; Biomass Removal 1,482; Machine Pile 1,075; None 876; Lop and Scatter 661; Crushing 199; Chipping 110. BLM: Lop and Scatter 1,225; Thinning 486; Mastication 322; Mowing 235; Hand Pile 173; Fuel Compaction 90; Chipping 57; Machine Pile 35; Biomass Removal 31.
- Rough check against the existing stream: USFS Thinning + Biomass Removal + Machine Pile + Chipping completed 2018-2024 = ~5.8 M ac, ~0.83 M ac/yr; at 6-12 odt/ac that is 5-10 Mt/yr, same order as the tool's 10.45 Mt/yr (the tool's type list and year window differ, so this is a consistency check, not a reproduction).
- Of USFS completed acres, ~50.1 M are from FACTS HFT and 33.1 M from FACTS Common Attributes; Call et al. state that FACTS CA adds ~1 M records (+156%) beyond FACTS HFT and that all FACTS HFT records are also in FACTS CA but only HFT is kept in duplicate. TWIG flags (does not remove) duplicates: same Activity + Completion Date with geometries within 10 m.
- 22.5 M "Planned" acres are agency "N/A" with dates up to 2030; USFS planned acres have dates to year 2121. Planned records need filtering before use.
- DOI completion dates: Call et al. note IFPRS/NFPORS often enter a fiscal-year-end placeholder date (30 Sep).

## 3. Recommended approach

**Backbone and additions**
1. Keep FACTS HFT as is for USFS (it is the system of record; matches TWIG's `FACTS Hazardous Fuels`).
2. Add **BLM, NPS, FWS, BIA** from TWIG filtered to `status='Completed'`, `identifier_database IN ('NFPORS','IFPRS')`, removal-type `type` values (Thinning, Biomass Removal, Machine/Hand Pile, Chipping; treat Lop and Scatter, Mowing, Crushing, Fuel Compaction, Mastication as zero removal). BLM completed mechanical in 2024 alone is 0.70 M ac, so this is not small relative to USFS 1.1 M ac.
3. Add **state agencies** (CO SFS, WA DNR, UT, AZ, NV, etc.) from TWIG's `NASF` records after the same type filter. Virginia's "Mechanical" acres (~110-130 k ac/yr) are likely mowing/firebreak; check `type` before including.
4. **CA all-ownership:** use the CAL FIRE tracker only for non-federal CA ownership (state, private timber); this requires the dashboard ownership field, which TWIG's `agency` field does not carry. Pull from the Dashboard geodatabase directly if SPARCAL access works (403 to curl; browser access not tested). Do not use the TWIG CAL FIRE rows wholesale.
5. **Dedup:** (a) prefer the single-agency record where `identifier_database` differs but activity+date+geometry (tolerance 10 m, as TWIG) match; (b) intersect state/tracker polygons with USFS/DOI polygons and keep only the non-overlapping area; (c) use TWIG's `error`/duplicate flags; (d) do not double-count FACTS CA and FACTS HFT.
6. Assign counties by polygon centroid or area-weighted overlay (existing method presumably; keep consistent). Private-land treatments (NRCS/EQIP, industrial timber) are not in any open national dataset I found.

**Scenarios**
- **Historical-rate (A):** completed removal-type acres, multi-year average (suggest FY2018-2024 or 2019-2024 to match existing stream), all agencies. This is the defensible baseline.
- **Needed/planned (B):** supply scenario sized to WCS targets: up to 20 M ac NFS + up to 30 M ac other over 10 years, and 5.6-11.2 M ac NFS needing immediate treatment (WCS Progress Summary, FS-1187e, Nov 2022, verified quote above). BT23 explicitly bounds this: ~28.2 M forested ac in all 21 PILs, 556,000 ac/yr initial goal, yielding 1.8-2.9 Mdt/yr ("rough extrapolation"). Use TWIG `Planned` acres only as a sensitivity (data quality poor, see above).
- Present B as a potential, not an estimate, and apply a "fraction mechanical vs prescribed fire" parameter: BT23 notes that "nearly all, in some PILs" acres are burned and yield no biomass.

## 4. Yield-factor evidence

| Source | Metric | Value | Basis | Verified |
|---|---|---|---|---|
| Barker et al. 2025 (11 NFs CA/OR/WA, dry mixed conifer/ponderosa) | cut, piled and burned biomass | **13.5 +/- 2.0 BDT/ac** (33.3 +/- 5.0 bone-dry MT/ha); total 1,151,046 MT/yr; CONSUME 3.0 algorithm | modeled from literature + FACTS + interviews, on acres that are actually piled | Y |
| CA Pile Data Collection Report (PFIRS, 1,775 burns 2017-2021) | biomass burned | **12.9 tons/ac** statewide average, "interpreted cautiously", wide variation from user-entry bias; tons unspecified (short vs BDT) | air-district burn permits | Y |
| Rummer 2005, Table 5 | total cut and removed to roadside, bdt/ac | 4.6 (Great Basin ponderosa) to 38.6 (Great Basin lodgepole); SW ponderosa 12.2, Sierra ponderosa 13.4, Rockies lodgepole 22.9 | ST Harvest model, **includes merchantable trees >7 in.** | Y |
| Rummer 2005, Table 5 minus Table 6 (my subtraction) | non-merchantable (<7 in.) component | ~0.9-1.7 bdt/ac in ponderosa types; 3.4-7.1 in lodgepole | derived; only this part is true "residue" if logs go to sawmills | derived |
| Rummer 2005 exec summary | western total | 28 M ac benefit, ~60% accessible, **345 M bdt** (~20 bdt/ac over ~16.8 M ac; my division) | | Y (quote) |
| BT23 forestry ch. | extrapolated all-PIL yield | 1.8-2.9 Mdt/yr on 556,000 ac/yr; "mean biomass yield (5.2 dry tons per acre)" at high end, "low because ... treatment acres are accomplished via burning operations" | BioSum on 4FRI and CWI | Y |
| BT23 | two-PIL case study | "about 700,000 [ac] could be treated ... annually delivering up to 0.4 million dry tons" (= ~0.6 dt/ac as written; internally inconsistent with the 1.8-2.9 Mdt on 556k ac line, likely different bases, flag) | BioSum | Y (quote); inconsistency is my reading |
| Getting to Neutral 2020 | CAL FIRE projects | assumed **15 BDT/ac** (source ref [90]); model output 15.1 M BDMT/yr from >800,000 ac/yr = ~19 BDMT/ac (my division); chips only | Sanchez and Cabiyo BioSum + FVS | Y |
| CARB Scoping Plan modeling (via forest-industry comment) | assumed | ~2 t/ac; contrasted with 10-15 t/ac for G2N | | UNVERIFIED (secondary) |

Read-across to the tool's 6-12 odt/ac: it sits inside Barker (13.5) and PFIRS (12.9) for piled acres in dry western forest, but is 1-2 orders higher than BT23's all-treatment mean (0.6-5.2 dt/ac) and ~3-10x higher than Rummer's non-merchantable component in ponderosa. The gap is explained by (i) fraction of acres that yield material at all (prescribed fire, lop-and-scatter, mastication yield none for bioenergy), (ii) merchantable vs unmerchantable, and (iii) pile vs. delivered recovery (BT23 and G2N recover only roadside material at a price). Recommend yield by `type` (pile/biomass removal at ~10-13; thinning without piling lower; others zero) with a low case around the BT23 5.2 dt/ac mean, and an explicit "available at roadside" vs "piled in-stand" distinction. Wet vs dry basis: Barker and G2N use bone-dry; confirm the existing tool uses oven-dry.

## 5. Counterfactual and utilization

- Barker et al. 2025: "most residues are burned and bioenergy is uneconomical without subsidy" (page statement as summarized by my fetch; the first 100k chars of 143k were read). Pile burning CDR efficiency 8% (their metric) vs BECCS 82%. Of the 13.5 BDT/ac, CONSUME assumes 90% combusted. Suggested removal subsidy $30-54/BDMT.
- CA Board of Forestry report: goal of 1 M ac/yr "will require removal and subsequent disposal of an estimated 5 - 15 million bone dry tons of forest biomass waste annually"; mapping estimates "potentially 150,000 acres of piles representing approximately 1,000,000 tons of material currently on the landscape"; 76% forest biomass, 24% chaparral (the 76/24 split is from search summary, UNVERIFIED). PFIRS: five air districts account for >50% of burned acres (UNVERIFIED snippet).
- BT23: fuel-treatment biomass outside priority landscapes "may be left unharvested or be consumed via prescribed fire or wildfire unless its value ... is recognized"; BT23 treats roadside delivery as avoiding disposal cost (air curtain destruction example).
- RMRS-GTR-439 (UNVERIFIED snippet): residues from WCS harvest are "routinely piled and burned"; centralized collection absent in many locations.
- **No national piled/utilized split found.** For additionality, the defensible default is that non-merchantable residue on mechanical treatments is currently pile-burned or masticated/left, with utilization as a minor share in regions with a plant (e.g., Sierra biomass plants). A quantitative national fraction is an open item; FACTS "Machine Pile" and "Hand Pile" acres (USFS completed 2018-2024: Machine Pile 1,075 k ac, ~18% of removal-type acres by my sum above) give an upper bound on explicitly piled acres.

## 6. Validation totals

- TWIG completed mechanical acres (all types) 2018-2024: 1.5-2.4 M ac/yr (excluding the 2022 CAL FIRE artifact: 1.3-2.0 M). USFS ~0.93-1.16 M ac/yr; BLM 0.26-0.70 M ac/yr; FWS 0.03-0.17 M ac/yr.
- USFS programmatic: "completed treatments on 3.2 million acres nationally in 2022" and FY2025 goal "4 million acres" (search summary of House hearing memo, UNVERIFIED). Those are all-treatment (incl. burning) acres, consistent with TWIG USFS planned ignition being larger than mechanical.
- WCS: 50 M ac target (20 M NFS, 30 M other), 5.6-11.2 M NFS acres needing immediate treatment (verified, FS-1187e).
- Residue tonnages: BT23 fire-reduction thinnings 0.4 Mdt/yr (two PILs) and 1.8-2.9 Mdt/yr (all PILs, extrapolated); BT23 total near-term 30.3 Mdt/yr, mature 62.7 Mdt/yr, with "Other forest waste" 7.5 (land conversion, not fuel treatment); G2N CA forest-management residue 15.1 M BDMT/yr (at ~800k ac/yr; CA counties); Barker 1.15 M BDMT/yr piled-and-burned on 11 western NFs; CA 5-15 M BDT/yr for 1 M ac/yr (CLERE).
- **Cross-check for the current 10.45 Mt odt/yr:** it is 3.6-5.8x BT23's all-PIL extrapolation (1.8-2.9 Mdt/yr) and ~0.7x of G2N CA alone (if CA is ~1/3 of the tool's total this is plausible). The tool's number is not a BT23-comparable (BT23 is economically available roadside, ours is gross treated). State this difference in the docs.
- State-level validation: CA via G2N Table S4 / CAL FIRE dashboard; AZ and WA counties via the 69 BT23 fire-reduction rows (login needed).

## 7. Post-fire salvage / hazard trees (separate stream, scoping only)

- USFS 2018 report (UNVERIFIED snippet): 2007-2016, 707 large fires, ~12.2 M ac burned on NFS; ~99,896 ac salvage accomplished (~10,000 ac/yr) and FACTS may undercount salvage. Small relative to fuels treatments.
- Hazard-tree removal along roads/trails is not captured by FACTS HFT; NFPORS/IFPRS "key point 2" (post-fire rehabilitation) records exist in TWIG but are rehabilitation (seeding, planting), not removal.
- Candidate method: MTBS or NIFC perimeters x salvage acres from FACTS timber-sale activity codes; yields are merchantable-dominated, so BiCRS-relevant residue is small. Recommend deferring.

## 8. Open questions and risks

1. **Acre-to-ton yield** is unresolved (0.6 to 19 t/ac in published sources). Need a per-`type` factor and a pile/removal vs. burned/left fraction; consider a sensitivity band, not a point value.
2. **Overlap/double counting** between FACTS, NFPORS/IFPRS, state trackers, and the CAL FIRE tracker is not fully resolved by TWIG (flags only; Call et al. state "57,000 records encompassing 1.2 M ha (3% of all records, 2.3% of total record area)" were identified as potential errors in FACTS HFT).
3. **Date quality:** IFPRS/NFPORS fiscal-year placeholders; CAL FIRE tracker only 2021-22; planned records have dates to 2121/2222.
4. **Private and tribal lands:** TWIG says "does not yet fully incorporate state, private, or NGO data"; state NFT data update expected "Q1 or Q2 of 2026" (not confirmed arrived). Private industrial treatment (largest CA share) is essentially absent.
5. **BT23 county data** needs an ORNL login; its fire-reduction rows cover only AZ and WA PILs. Roads to Removal county data not located. LLNL official PDF URL not verified (used a third-party mirror).
6. **Licences:** TWIG CC BY 4.0 (verified for Zenodo; REST page claim from reshapewildfire.org resource page). BT23 and G2N licences not stated.
7. **Not investigated:** USGS/LANDFIRE Public Events, NIFC "Interagency Fuel Treatment" layers, FIA BioSum outputs, Oregon/Washington state tracker portals, Sanchez & Cabiyo primary paper, UC ANR/CAL FIRE fuel reduction viewer.
8. Ownership-specific treatment of **Wildfire Crisis Strategy**: scale-up scenario depends on funding (BIL) that may lapse; BT23 also notes extrapolation "almost certainly overstate[s]" yield.
9. `usgs.nfpors.gov` decommissioned and `inform` service cert expired: TWIG's pipeline (github.com/Innovate-Inc/sweri-data-tools) is the single point of dependence for DOI data; archive a dated copy.
