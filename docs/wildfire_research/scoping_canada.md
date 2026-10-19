# Canada wildfire-related woody residues: data-source scoping (CD level)

Scoping date: 2026-10-19. Nothing built. Verified = Y means I opened the endpoint/document myself this session (curl/pdftotext/WebFetch); N = only seen in search-result text (UNVERIFIED).

## Bottom line
- There is **no national fuel-treatment inventory** I could find (CFS, FireSmart Canada, WRFI). Only **BC** publishes an open treatment-polygon layer, and it is small (15,242 ha total, 792 polygons).
- The **largest additional stream is BC harvest-slash pile burning** (hazard abatement), but **no spatial, annual, primary-source pile volume exists**. Only an emissions figure (3.9 Mt CO2, 2019, via a UBC policy brief) and advocacy volume estimates.
- Post-fire salvage: national/provincial totals exist in fragments only; burned area (NBAC) is clean and open and can allocate totals to CDs.
- Recommendation: treat fuel treatments as a small BC-only stream; model slash piles from existing harvest-residue data (BIMAT/NFD) times a burned fraction; model salvage as NBAC burned area x salvage fraction. Flag all as low confidence.

## 1. Source table

| # | Name | URL | Publisher | Licence | Date / vintage | Format / size | Coverage / unit | Key fields | Verified |
|---|---|---|---|---|---|---|---|---|---|
| 1 | BC Wildfire CRI Fuel Treatments (PROT_FUEL_TREATMENTS_SP) | https://delivery.maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_land_and_natural_resource/MapServer/19 ; catalogue https://catalogue.data.gov.bc.ca/dataset/7b142d77-d7ba-41be-b589-e31ea96f9927 | BC Wildfire Service / Ministry of Forests | **"Access Only"** (BC catalogue licence id 22), NOT OGL-BC. Licence page: "reproduction is not permitted without written permission"; derived use unaddressed. Need written permission before publishing derived products. | Catalogue metadata_modified 2026-08-12; intake years 2013-2023 | ArcGIS REST polygons, maxRecordCount 1000, **792 records**; WMS/KML; BCGW custom download | Provincial polygons, local-government/First Nation attribution | PROJECT_ID, PROJECT_TYPE (Operational 420 polys / 5,974 ha; Prescription 370 / 9,256 ha; Demonstration 2 / 12 ha), INTAKE_YEAR, LOCAL_GOVERNMENT, BAND_NUMBER, STATUS (Completed 422, Prescribed 370), DATA_SOURCE (all "SWPI/CRI"), HECTARES (sum 15,242), PROJECT_COMPLETION_DATE | Y (count, stats, fields queried live) |
| 2 | Fibre Utilization Forest Carbon Initiative Projects | https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/FibreUtil_FCIwebmap20190611/FeatureServer/5 ; catalogue 45ef09f9-c38e-41fa-b283-e4fa51795c26 | BC Ministry of Environment / FESBC | Access Only | 2019 (FCI webmap, layer FibreUtil_20190911) | ArcGIS points, **24 records** | BC points, no volumes | Project_ID, Project_Title, Location, Primary_Region, Management_Unit, Lat/Long, Year, Delivery_Agent. **No tonnes/m3 field.** | Y |
| 3 | BC Wildfire OFTS Burn Registration Locations (Active) | catalogue 0cf7a53f-d91a-42a0-aa40-158f37cbaca3 | BC Wildfire Service | Access Only | 2022-08-03 metadata | Catalogue text: "not available for download at this time" | Active Category 3 burns only, no history | Registrants state "number of piles/size of area" (per catalogue notes) | Y (metadata only); pile counts not obtainable |
| 4 | NBAC (National Burned Area Composite) | https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/ | NRCan CFS | Open Government Licence - Canada (CWFIS data; licence text not re-checked) | Files NBAC_2020..2025_20260513.zip; MRB 1972-2025 rasters; NBAC_summarystats_1972_to_2025_20260513.xlsx | Zips/rasters/xlsx (sizes not HEAD-checked; MRB 30 m rasters are likely large) | National fire polygons 1972-2025 | burn area, year, agency | Y (directory listing); licence and sizes N |
| 5 | BIMAT Business Data, Biomass Forestry Inventory | https://open.canada.ca/data/en/dataset/1a759d95-3008-4078-87af-5bb1bdf657b3 ; spec PDF at agriculture.canada.ca/atlas/data_donnees/bimat/supportdocument_documentdesupport/en/ISO_19131_...Data_Product_Specification.pdf | AAFC (data supplied by CFS-NRCan) | ca-ogl-lgo (OGL-Canada) | Record modified 2025-10-15; **forestry data based on 2013-2014 activity**; spec ref date 2019-10-04 | FGDB 11.5 MB (BIOMASS_INV_CT_FGDB.zip, Last-Modified 2024-06-12); GeoJSON 222 MB (too big); CSV dir lists AG and MSW only | **10 km x 10 km grid** | Gross softwood/hardwood **roadside harvest residue** (odt/yr), full-tree and cut-to-length variants, mill residue, urban wood waste, forest area ha | Y (listing, HEAD, spec); FGDB contents not opened |
| 6 | NRCan CERP "Forestry wood residues and waste wood (tonnes per year)" | https://geoappext.nrcan.gc.ca/arcgis/rest/services/Energy/CERP_EN/MapServer/26 | NRCan | not checked | n/a | ArcGIS polygons, **24,288 records**, field TOTAL only | National grid | TOTAL | Y (count, fields); same underlying data as #5 |
| 7 | FESBC Special Report 2025 | https://fesbc.ca/wp-content/uploads/2025/09/2025-Special-Report.pdf | FESBC | n/a | "current as of March 31, 2025" | PDF 3.2 MB | BC | 426 projects; $336 M approved; 18 thousand ha wildfire-risk-reduction treated; 12 thousand ha prescribed/surveyed; 24 thousand ha rehabilitated; ~2.7 M t CO2e avoided; "wood waste utilized" million m3 (leading digit is separated from label in PDF text, likely 9; read the PDF image before citing) | Y (pdftotext) |
| 8 | BC Ministry of Forests utilization workshop 2021 (Interior) | https://www2.gov.bc.ca/assets/gov/farming-natural-resources-and-industry/forestry/timber-tenures/fibre-recovery/utilization_workshop_2021_interior.pdf | BC MoF | n/a | 2021 | PDF 3.5 MB | BC | FESBC carbon-eligible enhanced residual fibre utilization: 233,610 m3 (2018/19 actual), 864,660 m3 (2019/20 actual), 1,436,000 m3 (2020/21 forecast); CRHS 737,210 m3 S. Interior + 596,378 m3 N. Interior delivered since 1 Apr 2019 | Y |
| 9 | FPInnovations biomass availability by TSA (e.g. Bulkley TR52) | https://www2.gov.bc.ca/assets/gov/farming-natural-resources-and-industry/forestry/timber-tenures/fibre-recovery/tr2017n52.pdf (other TSAs under .../forestry/supporting-innovation/<tsa>.pdf) | FPInnovations for BC Timber Sales / MoF | n/a | 2017 (Bulkley); 2021 (others) | PDFs | Per TSA, Crown land only, **harvest-residue** | Bulkley: 25.2 odt/ha, biomass ratio 16.7%, 3.48 M odt/50 yr (~70,000 odt/yr), ~4,600 odt/yr economic at $60/odt | Y (Bulkley read); other TSA values (Fort Nelson 23.2, Pacific 33.9, Okanagan 16.2, Dawson Creek 32.3, Invermere 30.6, Fort St John 31.5 odt/ha) are search-snippet only, UNVERIFIED |
| 10 | BC Impacts of 2023 / 2021 Fires on Timber Supply | https://www2.gov.bc.ca/assets/gov/farming-natural-resources-and-industry/forestry/stewardship/forest-analysis-inventory/tsr-annual-allowable-cut/wildfire_report_2023v1.pdf (and impacts_of_2021_fires_final.pdf) | BC FAIB | n/a | March 2024 | PDF | By TSA | 2023: 2,842,000 ha burned; THLB within perimeters 687,000 ha; 92 M m3 THLB volume within perimeters, ~39 M m3 (43%) unburned. THLB in perimeters: 2017 700,000 ha; 2018 300,000 ha; 2021 420,000 ha. Burned-volume bar chart by TSA exists (not extractable as text). | Y |
| 11 | UBC policy brief, Biomass Brief 1 (June 2022) | https://forestry-2022.sites.olt.ubc.ca/files/2023/03/Biomass-Brief-1.pdf | UBC Forestry | n/a | 2022 | PDF | BC | "In 2019 alone, CO2 emissions from this practice totalled 3.9 megatonnes (Mt), representing nearly 6% of BC's provincial total"; "roughly 64 million m3 of logs are harvested annually"; no underlying volume or primary citation given in text I extracted | Y (document); the 3.9 Mt is secondary |
| 12 | Forestier en chef release, 29 Nov 2023 | https://newswire.ca/fr/news-releases/feux-de-foret-de-l-ete-2023-811330307.html | Bureau du forestier en chef (Quebec) | n/a | 2023-11-29 | HTML | Quebec | fires "un peu plus de 1,3 million d'hectares de forêt", 44 management units; 920,000 ha under forest management; AAC cut 619,400 m3/yr (34,916,800 -> 34,297,400). **No salvage volume given.** | Y |
| 13 | NRCan presentation (Boulanger, NCASI Apr 2024) | https://www.ncasi.org/wp-content/uploads/2024/04/2-Boulanger.pdf | NCASI/NRCan | n/a | 2024 | PDF | Canada | claims "~5.2M m3 salvaged in 2023" and "only 10-15% of burned areas can be salvaged" | **N**: PDF would not download as PDF (returned HTML); search-snippet only, UNVERIFIED |
| 14 | FPInnovations "Summary of stand level fuel treatment productivity studies" | https://wildfire.fpinnovations.ca/summary-of-stand-level-fuel-treatment-productivity-studies/ | FPInnovations (Hvenegaard, 2021) | n/a | 2021 | Project page | AB / Canada | Page has no numbers; full report must be requested (wildfire_operations_incendies@fpinnovations.ca) | Y (page); content N |
| 15 | National Forestry Database (NFD) | https://nfdp.ccfm.org | CCFM | n/a | n/a | Connection refused from this environment | Provincial harvest tables | Could not open; whether a salvage category exists is **unknown** | N |
| 16 | FESBC project listing | https://fesbc.ca/projects/ | FESBC | n/a | n/a | Not opened | BC | Possible project-level hectares/m3; not checked | N |

### Not found (searched, no result; not proof of absence)
- Any national fuel-treatment inventory (CFS, FireSmart Canada, WRFI): none surfaced.
- Alberta: only municipal tenders and FRIAA project abstracts (e.g. Whitecourt 26.9 ha; Wabasca 36.1 ha; Fox Creek 14.2 ha); no provincial open layer found.
- Ontario, Quebec (SOPFEU), Saskatchewan, Manitoba fuel-treatment spatial layers: nothing surfaced. Not exhaustively searched on each provincial portal.
- BC CLWRR (Crown land) treatment polygons: catalogue search for "fuel treatment/management", "wildfire risk reduction", "FESBC" returned only layer #1 (DATA_SOURCE = "SWPI/CRI"). Whether CLWRR/FESBC Crown treatments are in it is unconfirmed.
- BC RESULTS and any open provincial slash-pile inventory: not found; catalogue "slash pile" returns only #2.
- Official provincial annual m3 of residue piled/burned: none found.

## 2. Recommended approach

**Stream A: fuel-management treatments (small).**
- BC only. Pull layer #1 (792 records, one paged query, <1 MB), spatially join polygon centroids to the 293-CD (or BC's 27 regional district CDs). Use Completed + Operational as the base; do not sum Prescription (planned, overlaps Operational; the layer metadata itself says "Polygons in this data may overlap"). Dissolve before area summing.
- Annualise over intake years 2013-2023 (~11 yr). Operational 5,974 ha / 11 yr ~ 540 ha/yr; even at 90 odt/ha this is ~50,000 odt/yr. FESBC's 18 k ha cumulative WRR (to Mar 2025, #7) is consistent in order of magnitude. Expected ceiling: tens of kodt/yr nationally. Worth including mainly for completeness.
- Licence gate: "Access Only" means ask BC IP Program (QPIPPCopyright@gov.bc.ca per the licence page) before shipping derived CD totals, or publish only CD aggregates and ask for confirmation.
- Other provinces: no data; leave zero with an explicit "no data" flag, not a zero estimate.

**Stream B: harvest slash piled and burned for hazard abatement (probably the largest).**
- No spatial or annual primary volume. Proposed modelled estimate: harvest-residue availability (BIMAT roadside residue, odt/yr on a 10 km grid, 2013-14 vintage, aggregated to CDs; or reuse whatever the map already has as "general forestry residues") x fraction piled-and-burned (BC) with provincial scalar calibrated to a validation total (Sect. 5). Caution: this likely **double counts** the existing general forestry-residue stream. Define Stream B as a subset/reallocation of it (the portion currently burned), not an addition.
- Allocation of any provincial total to CDs: weight by harvest-residue (BIMAT) or by NFD/BC harvest volume. For BC, TSA-level odt/ha from FPInnovations (#9) gives a spatial pattern, but only some TSAs published and Crown land only.
- Outside BC, pile burning is not documented in anything I opened; treat as zero/unknown.

**Stream C: post-fire salvage / fire-killed timber.**
- Allocate by NBAC burned area (open, current to 2025) x forest/THLB fraction x salvage fraction, per province, calibrated to provincial totals where available. Salvage is a one-off pulse tied to fire years, so use a multi-year average (e.g. 2016-2025) or fire-year-specific, and note it is mostly merchantable sawlog/pulp, so the residue fraction (tops, unmerchantable) is the biomass-relevant part, not the whole salvage volume.
- BC: FAIB reports give burned THLB volume by TSA/fire year (figures, partly chart-only). Quebec: MRNF special salvage plans (PAS Feu 2023-2024) list gross volumes per fire per unit (e.g. 476,913 m3 across several fires in one SLSJ unit; 381,550 m3 for fire 314 in Nord-du-Quebec; both from search results, UNVERIFIED) and could be summed. Alberta: Alberta rules require use within two years (search result).

## 3. Yield and conversion factors

| Factor | Value | Source / status |
|---|---|---|
| BC harvest residue yield, Bulkley TSA | 25.2 odt/ha; biomass ratio 16.7% (odt biomass per odt roundwood); 3.48 M odt over 50 yr | Verified (FPInnovations TR52, 2017) |
| Other BC TSAs | 16.2 (Okanagan) to 33.9 (Pacific) odt/ha | UNVERIFIED (search snippet) |
| Interior BC stand thinning study | 61.6 (500 stems/ha retained) to 93.7 odt/ha (200 stems/ha retained), 12 ha stand | UNVERIFIED (ScienceDirect 2026 snippet, single stand) |
| BC fuel-treatment biomass potential | "2.5 million oven-dry tonnes per year" in BC | UNVERIFIED (Nature Comms Earth Environ. snippet; Nature page blocked; likely a potential, not actual, and my treated-area arithmetic above suggests actual is ~1-2 orders smaller) |
| Pile size and emissions | 50 m3 slash pile releases "about 45 tonnes of greenhouse gases, including 240 kilograms of ... particulate matter" | Verified in FESBC Special Report 2025 text |
| m3 to odt | Not given in sources I opened. Do not assume. Needs a basic-density/bulking assumption (piles are loose-stacked; 50 m3 pile is pile volume, not solid wood). | Open question |
| Implied scale check (my arithmetic, not sourced) | 3.9 Mt CO2 / (45 t GHG per 50 m3 pile = 0.9 t/m3) ~ 4.3 M m3 pile volume per year | Derived; mixes CO2 and GHG basis and pile vs solid volume; indicative only |
| BC annual harvest | ~64 M m3 of logs | UBC brief (secondary) |

## 4. Counterfactual evidence (burned vs left vs utilized)
- Burned: UBC brief states residuals "are amassed into slash piles and burned every autumn for hazard abatement" because the Wildfire Act treats them as a fire risk (secondary, 2022). CleanBC Roadmap 2030 goal: "near elimination of slash pile burning by 2030" (quoted in UBC brief and FESBC); the UBC brief says there are no benchmarks.
- Utilized (additionality evidence): FESBC reports fibre "that would otherwise be burned": 4.8 M m3 cumulative since 2017 (search-snippet of BC news text, UNVERIFIED); FESBC letter Jan 2024: ~67,765 truckloads (UNVERIFIED snippet; also on fesbc.ca homepage, verified there); MoF slides (#8) give verified annual figures 233,610 -> 864,660 m3.
- Fuel-treatment piles: FESBC special report notes biomass from treatments is "burned on-site" in some projects and now being recovered (qualitative).
- Left: unburned residue remaining after treatment/harvest is not quantified in sources; Bulkley TR52 says 2,962,000 odt of 3.48 M odt of residue would be left on the landbase and 614,000 odt reaches roadside but is not economically accessible (verified in my grep of TR52 lines 454-461). Ties to economic availability: only ~4,600 odt/yr of ~70,000 odt/yr is available at $60/odt in Bulkley. This is the key constraint for a BiCRS screening map: physical vs economic availability.
- Post-fire: burned timber may be salvaged for lumber, left, or unsalvageable; BC states "Not all of the timber within a fire perimeter is consumed by the fire" (verified). Alberta: Alpac expected >2 M m3 from the 2016 Fort McMurray fire but projected <700,000 m3 (Global News 2017, UNVERIFIED snippet).

## 5. Validation totals (candidates)
| Total | Value | Status |
|---|---|---|
| BC CRI polygons | 792 records, 15,241.9 ha; Operational 5,973.6 ha (420); Completed 422 | Verified (live query 2026-10-19) |
| FESBC cumulative WRR hectares treated | ~18 thousand ha (to 2025-03-31) | Verified (FESBC report, rounded) |
| BC slash-burn CO2, 2019 | 3.9 Mt | UBC brief; secondary; primary source not identified (candidate: Canada NIR/BC inventory, not checked) |
| BC fibre diverted by FESBC | 233,610 / 864,660 m3 (2018/19, 2019/20) | Verified |
| Burned area 2023 BC | 2.84 M ha (THLB 687,000 ha); Quebec ~1.3 M ha of forest | Verified |
| Quebec AAC reduction | 619,400 m3/yr | Verified |
| National salvage 2023 | ~5.2 M m3 | UNVERIFIED |
| Province slash burned (advocacy) | ~5 M tonnes (CBC), >=10 Mt 2017 (Chipeniuk via Narwhal), ~1 M m3/yr Bulkley region (Vanderstar, 50 m3/pile assumption) | UNVERIFIED/advocacy; use only as bounds |

## 6. Open questions and risks
1. Layer #1 licence is "Access Only": confirm derived-product permission with BC IP Program before publication.
2. Layer #1 lacks yield or volume fields; contains planned polygons that overlap; coverage ends at intake year 2023 and may omit CLWRR Crown-land and FESBC-only treatments. Completeness unknown.
3. No primary annual pile-burn volume for BC. Possible routes (not tried): FOI/ask BC MoF Fibre Supply or FESBC; BC GHG inventory slash-burning line; Canada NIR (CRF tables) for slash burning by province; BC RESULTS/Waste & Residue Survey. A call to FESBC (Jason Fisher is named as Executive Director in the report) may be fastest.
4. Double counting with the existing general forestry-residue stream is the main modelling risk.
5. BIMAT forestry layer is 2013-14 vintage, 10 km grid; spec says roadside residue is "not utilized by industry" odt/yr, so it may already exclude piles that are utilized and partially include piles that are burned.
6. Boundary mismatch: BC TSAs and CRI local governments (cities, First Nations bands, regional districts) vs CDs; centroid join needed, First Nations records may not sit inside their band's CD.
7. Salvage is episodic; 2023 volumes are not representative. Salvage volumes are mostly merchantable wood, not residues.
8. NFD (nfdp.ccfm.org) was unreachable; check whether salvage harvest is a reported category.
9. Not verified: NBAC licence/sizes, BIMAT FGDB contents, FESBC project database, Alberta/Ontario/SOPFEU/Sask/Manitoba portals, CWFIS National Fire Database, BIMAT roadside residue totals for BC.
10. Search-derived claims here (flagged UNVERIFIED) must be checked against primaries before any public use.
