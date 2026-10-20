# Europe wildfire-management biomass residues: data-source scoping

Scoped 2026-10-19. Scope: EU-27 + UK + NO, NUTS-2 target, Mediterranean priority. This is a scoping note, nothing was built.
Verification labels: **V** = opened and read the primary source (PDF/xlsx/API) this session; **S** = search-result snippet or fetch-tool summary only, UNVERIFIED; **N** = not found.
Raw downloads (AGIF PDFs, MITECO PDFs, ENSPRESO xlsx, EFFIS xlsx) were processed in scratch and the large ones deleted.

## Bottom line

1. There is **no pan-European, spatially explicit or regionally tabulated dataset of fuel-treatment area** (EFFIS, JRC, FirEUrisk, FIRE-RES and SILVANUS searches turned up fuel *maps* and burned-area products, no treatment records). A US-style "treatment polygons x yield" build is not possible for Europe as a whole.
2. **Portugal is the only country with a national, annual, published fuel-management hectare series** (AGIF/SGIFR reports, 2019-2024; V), but it is national or by entity, not by NUTS-2, and it excludes most private and municipal work. A satellite product (DGT "Cortes de Vegetação em Áreas Lineares", 10 m raster, 2025 edition, open WMS; V) is the only open spatial layer of actual treatment-like events and could regionalise Portugal.
3. Spain: no national treated-area statistic found in MITECO fire reports (V; only one state brigade programme, 958 ha in 2024). Regional administrations (Galicia, Catalonia, Andalucia, CyL) hold the data but none was obtained here.
4. Greece, Italy, France, Croatia, Cyprus: no usable treatment-area statistics found (N).
5. Recommended stream is therefore a **burned-area-and-fuel-load driven proxy for Mediterranean NUTS-2, calibrated to the Portuguese series**, plus a separate post-fire salvage stream. Full caveats in section 7.

## 1. Source table

| # | Name | URL | Publisher | Licence | Date / version | Format, size | Coverage / unit | Key fields | Verified |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AGIF SGIFR Relatorio de Atividades 2024 | https://www.agif.pt/app/uploads/2025/07/SGIFR-RelatorioActividades2024.pdf | AGIF (PT) | Not stated on file (public report) | Jul 2025 (rectified version exists) | PDF 7.4 MB, 133 pp | PT national, by entity and intervention type; no NUTS | ha fuel management 2019-2024, by ICNF / utilities / infrastructures; primary-network ha | V |
| 2 | AGIF SGIFR Relatorio 2023 | https://www.agif.pt/app/uploads/2024/06/Relatorio-de-Atividades-SGIFR-2023_19jun.pdf | AGIF | as above | Jun 2024 | PDF 4.7 MB | PT national | 2023 ha | V |
| 3 | DGT Mapa de Cortes de Vegetacao em Areas Lineares | https://dados.gov.pt/datasets/mapa-de-cortes-de-vegetacao-em-areas-lineares (WMS: https://geo2.dgterritorio.gov.pt/geoserver/DRFloresta/wms) | Direcao-Geral do Territorio (PT), PRR transForm P1.5 | "notspecified" on dados.gov.pt | 2025 edition, listed updated 2026-06-23 (WMS resource 2026-09-29); 2024 edition on request | Raster, 10 m, annual; WMS. Download size not checked | Primary fuel-management-strip network, continental PT; pixel = month of vegetation loss detected by Sentinel-2 | month (1-12) of loss; cause undefined (manual, mechanical, fire, grazing) | V (metadata only; raster not opened) |
| 4 | dados.gov.pt "Faixas de gestao de combustivel - PMDFCI" | https://dados.gov.pt/datasets/faixas-de-gestao-de-combustivel-pmdfci | Camara Municipal de Agueda | cc-by | 2020-11-13 | vector | One municipality only | FGC polygons | V (API listing; 4 hits for query, no national ICNF layer found) |
| 5 | MITECO "Avance informativo" annual fire reports | e.g. https://www.miteco.gob.es/content/dam/miteco/es/biodiversidad/temas/incendios-forestales/Avance_1_enero_31_diciembre_2024.pdf | MITECO (ES) | Not checked | Year-end 2016-2025 | PDF ~4.6 MB each | ES by CCAA/province: fires, burned area; BLP (state preventive brigades) table | BLP 2024: the 'Tratamientos selvicolas' column sums to 958.2 ha (my sum of 10 bases); the table's TOTAL cell also reads 958.2; text says '>960 ha' including 814 ha of fajas work. Column semantics ambiguous; treat as ~1,000 ha | V |
| 6 | MITECO interactive fire report | https://www.miteco.gob.es/es/biodiversidad/temas/incendios-forestales/estadisticas-avances.html | MITECO | n/s | Sept 2026 | Web dashboard; no download mentioned | ES burned area, GIF | no prevention data | S (news page) |
| 7 | EFFIS country totals report_2024.xlsx | https://data.effis.emergency.copernicus.eu/effis/applications/data-and-services/report_2024.xlsx (old forest-fire.emergency... path 301-redirects here) | JRC/Copernicus EFFIS | EU content CC BY 4.0 per EFFIS data-license page (V); NUTS/third-party carve-outs apply | 1980-2024 | XLSX 31 KB | Country-level burned ha and fire counts (sheets: burnt area, number of fires) | PT, ES, FR, IT, GR, HR, CY, etc. | V |
| 8 | EFFIS burnt-area polygons | https://forest-fire.emergency.copernicus.eu/applications/data-and-services | JRC | CC BY 4.0 (as above) | real-time updated | Shapefile / SpatiaLite; size not checked (HEAD not run) | Fire perimeters >= ~30 ha (smaller since Sentinel-2 2018) | start/last-update dates, may not equal ignition | V (page); S for min mapped size |
| 9 | EFFIS NUTS2/NUTS3 summaries | JRC dataset page (https://data.jrc.ec.europa.eu/dataset/678deb39-e35f-4236-a984-42d69bf95dec; page returned "Request Rejected" to the fetch tool) | JRC | n/s | n/s | On request via point of contact | Custom annual/monthly burnt area by country, NUTS2, NUTS3 | | S only. "Request" mechanism is search-snippet claim, UNVERIFIED. Computing NUTS-2 from polygons ourselves is an alternative |
| 10 | EFFIS Fuel Map | https://forest-fire.emergency.copernicus.eu/effis/applications/data-and-services/FuelMap_LAEA.zip | JRC | CC BY 4.0 (EFFIS) | n/s | ZIP; size not checked | Europe fuel-type map | fuel class only, no loads | V (link exists) |
| 11 | FirEUrisk European fuel map v2.0 | https://cis2.eea.europa.eu/data/873 ; https://portalcientifico.uah.es/documentos/668fc479b9e7c03b01bde80d | Univ. Alcala (Chuvieco group) / EEA | CC BY 4.0 (S) | v2.0 | 1 km raster | Europe, 20 of 24 fuel types | fuel type; 88% accuracy (S) | S |
| 12 | JRC ENSPRESO-BIOMASS | https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/ENSPRESO/ENSPRESO_BIOMASS.xlsx | JRC (Ruiz et al.) | JRC open data policy (CC BY 4.0 typical, not re-checked) | v1.3, 2021-04-19 changelog | XLSX 15.8 MB | NUTS0 and NUTS2 energy potentials 2010-2050 | commodity codes, PJ | V (workbook opened) |
| 13 | Ruiz et al. 2019, ENSPRESO paper | doi:10.1016/j.esr.2019.100379 | Energy Strategy Reviews 26 | | 2019 | | | | S (DOI from DLR repository record in search; paper not read) |
| 14 | DFDE (Database on Forest Disturbances in Europe), salvage-logged volume | https://forest.eea.europa.eu/data/visualizations/vis_management_dfde_salvage_volume_eu ; dfde.efi.int | EFI / EEA FISE (Schelhaas, Patacca, Lindner, Zudin 2020) | n/s | 2004-2019 | Chart; data download not found | 10 EU27 countries incl. PT, GR | salvage m3 by year | V (page) but no numbers or licence visible |
| 15 | Patacca et al. 2023, Global Change Biology 29:1359 | doi:10.1111/gcb.16531 | | | 2023 | | 34 countries, 1950-2019 | | S (snippets) |
| 16 | Xunta de Galicia fajas secundarias viewer | https://mapas.xunta.gal/es/utilidades-y-publicaciones/actualidad/visor-de-fajas-secundarias | Xunta | n/s | | web viewer | Galicia parcels, 50 m secondary strips | inspection status | S (search listing only) |

## 2. Per-country assessment

| Country | Best source | Treated area per yr | Spatial unit | Open? |
|---|---|---|---|---|
| **PT** | AGIF SGIFR annual report (V) + DGT linear-cuts raster (V metadata) | 2019: 65,693; 2020: 70,387; 2021: 88,058; 2022: 77,867; 2023: 85,365 (restated; 2023 report itself printed 85,536); 2024: 75,559 ha, as read from the Fig. 26 chart text in the 2024 report (V). Target 2024: 81,456 ha. 2024 by entity: ICNF 27,929; utilities ~21.8-26.2k and infrastructures ~19.7-21.8k (chart labels, assignment to series not fully resolved). 2024 mix (Fig. 28): FGC infrastructures/utilities 63%, mosaics and parks 21%, primary-network FGC 8%, grazing 5%, controlled fire 3% (V). Controlled fire 2,153 ha in 2024 (V) | National and by entity; no NUTS. Report footnote: figures exclude "a maioria das entidades privadas ... e autarquias" (V), so they undercount the legally mandatory private/municipal strips | Reports public; no licence text seen. DGT raster open via WMS, licence unspecified |
| **ES** | MITECO Avance PDFs (V) show only BLP: 958.2 ha 2024. Regional bodies not obtained | National not found. Galicia: 2021-24 inspected 2,337,790 parcels (~171,389 ha) and 1,471.75 ha under management contracts (S, DOG snippet) | CCAA/province for fires only | PDFs public; treatment data N |
| **GR** | None found | "Minimal levels of fuel treatments" and no prescribed fire outside a Chios pilot (S, from a review snippet) | n/a | N |
| **IT** | None found (regional AIB plans, RaF report are the likely places; not opened) | N | Regions | N |
| **FR** | None found (OLD = legal duty of 50 m clearing around buildings, annual; no national ha series in search) | N | Departments | N |
| **HR** | Hrvatske sume (state forest company) reports; only road-building figures seen (60 km new fire roads, EUR 16.3m, 2023; S) | N | | N |
| **CY** | None found | N | | N |

## 3. Recommended approach for a NUTS-2 stream

1. **Do not attempt polygon x yield for Europe.** No treatment polygon database exists outside Portugal's DGT raster (and even that is vegetation loss of undefined cause).
2. **Mediterranean proxy for fuel-management biomass**: regional treated area T_r = national treated area (PT series; other countries need a stated assumption) allocated to NUTS-2 by a fire-risk weight (e.g. EFFIS 2012-2024 mean burned area share, optionally times shrub/forest fuel area from CORINE or the FirEUrisk fuel map), then multiplied by a collectible-biomass yield and a recoverability fraction (section 4). Present as order-of-magnitude with wide bands, not as measured treatment.
3. **Portugal**: use AGIF national total with the DGT cuts raster for within-country distribution (NUTS-2: Norte, Centro, AML, Alentejo, Algarve) and keep the "reported only" undercount as an explicit sensitivity (the true private/municipal total is unknown).
4. **Post-fire salvage as a separate stream**: NUTS-2 EFFIS burned area (compute from polygons, since the NUTS-2 tabulation is on-request/UNVERIFIED) x forest share from CORINE x salvage fraction. Calibrate salvage fraction on DFDE salvage volumes (get numbers from dfde.efi.int, not obtained here). Treat as merchantable roundwood plus residues; most value goes to panel/pulp, so only the tops/branches/slash are BiCRS-relevant.
5. **ENSPRESO double counting** (checked in the workbook): glossary describes MINBIOFRSR1 as "Fuelwood residues" (Forestry; "Not used in BaU forestry scenarios"), MINBIOWOO as "FuelwoodRW" (stem and other wood from harvesting), and MINBIOWOOW1 as "Secondary Forestry residues - woodchips" (sawmill-type, "From GFTM in BaU"). Forestry inputs are EFISCEN inventory-based. **No fire-prevention or fuel-management category exists.** Overlap with a fuel-management stream is therefore expected to be small: fuel clearing is shrub/understory and linear-infrastructure clearing, not harvest-derived. Two caveats. (a) MINBIOFRSR1**a** "Residues from landscape care" (glossary group: Agriculture and landscape residues) is the plausible overlap with roadside, utility and verge clearing; the user's stated code filter "MINBIOFRSR" would match it by prefix if applied as a prefix, so confirm whether 1a is in the current Europe build. The definition of landscape care in Ruiz et al. 2019 was not read (UNVERIFIED). (b) Thinning for fire prevention in managed forest could be partly inside FRSR1 if the model treats thinning residues as harvest residues. ENS_Med 2020 values from the workbook, NUTS0, PJ: PT FRSR1 53.4, FRSR1a 5.5, WOO 0.8, WOOW1 4.4; ES 144.4, 24.3, 8.0, 13.8; FR 193.7, 48.5, 78.5, 25.1; IT 134.9, 12.6, 14.6, 10.6; GR (code EL) 9.1, 5.8, 2.5, 1.4; HR 21.8, 1.8, 3.7, 0.5; CY all 0. Cyprus zeros look like missing data rather than zero potential (the workbook itself notes zero rows were removed at NUTS2 and NUTS0 should be used to check; not diagnosed further).

## 4. Yield / conversion factors

| Value | Context | Source | Status |
|---|---|---|---|
| 2.3 t DM/ha collected (mean), 1.6 tDM per productive machine hour, 0.7 ha/PMH, 37.2% moisture | Harvester-baler on rockrose (Cistus laurifolius) shrubland, 21 ha, central Spain. Collected biomass only, uncollected remainder not counted | Bados, Tolosana, Esteban, Croat. J. For. Eng. 41(2), doi 10.5552/crojfe.2020.688 | V (abstract via fetch; moisture from fetch summary of results) |
| Standing shrub biomass by years since fire, N Portugal (Erica, Cytisus, Chamaespartium, Ulex), 30% moisture: 1 y 0.12; 3 y 2.6; 5 y 6.7; 8 y 13.8; 10 y 19.4; 15 y 28.9 Mg/ha (range 0.12-28.88; RMSE 3.31) | Fuel load, i.e. an upper bound on what a clearing could generate, not the harvested yield. 161 plots, 1.9 Mha area | Enes et al. 2020, Life 10(4):33, PMC7236011 | V (fetch summary of Table 2; verify table before use, a typo was noted at 15 y) |
| ~2.5 t of residual biomass per ha | Opinion article on plant supply | DN (dn.pt archive) | S, opinion, not specific to fuel strips |
| 0.37 t/ha/yr residue availability | Maritime pine management unit ~940 ha, SW Portugal, 2004-2015 (harvest residues, not shrub) | UEvora (rdpc.uevora.pt/handle/10174/20907) | S |
| 26,322 t dry/yr (27.2% of 96,905 t dry/yr) scrubland residue | Algarve GIS assessment | UEvora | S |
| Only about one third of cleared area could be harvested for biomass (hilly, stony terrain) | French Mediterranean biomass-harvesting project | search snippet | S, UNVERIFIED |

Implication: harvested yields from shrub clearing are of order 2-3 t DM/ha (one Spanish trial), well below both standing fuel load at fuel-break maintenance intervals (plausibly several t/ha at 3-5 y regrowth, from Enes) and the US 13 odt/ac (about 32 odt/ha) piled/removed forest-slash value used in the US build. Do not port the US yield. Fuel-break maintenance is also on short cycles, so a legal-minimum clearing frequency matters. Fuel-load-minus-stubble is a defensible upper bound, the baler trial a lower/realistic one.

**Illustrative magnitude (my arithmetic, not a sourced result)**: PT 75,559 ha x 2.3-6.7 t/ha is 0.17-0.51 Mt DM/yr before any recoverability haircut, compared with PT ENSPRESO FRSR1 of 53.4 PJ (about 2.9 Mt DM at an assumed 18.5 GJ/t). So the fuel-management stream would be a modest add-on, not a rival to the forestry-residue stream.

## 5. Counterfactual evidence

- Portugal: Nunes et al. 2021, Fire 4(3):33 (Serra da Estrela), file read (V): residues are commonly burned in place or left; "the combustion of residual materials in the forest or in the pasture without any use for energy"; "The possibility of valuing these residues in biomass power plants has never effectively materialized, since the logistical difficulties associated with the low density and dispersion of the materials almost always make the feasibility of the task impossible"; high ash and low heating value. Decree-Law 124/2006 obliges landowners to clear by 30 April each year (as quoted in that paper). No quantitative split of burned/left/used was found.
- AGIF 2024 (V): treatment mix includes grazing (5%) and controlled fire (3%), which produce no removable biomass; 63% is linear infrastructure strips (mostly utility and road/rail operators), where residue is typically chipped/mulched or left (assertion about operator practice is UNVERIFIED).
- Catalonia (Land 2021, 10(10):1104; abstract and text V): treatments were 88% manual prescribed fire and 12% mechanical mastication; authors "dismissed the use of machinery to extract thinning due to the problematic access to SMPs and the lack of commercial interest". Fuel-treatment emission reduction >0.06 t CO2/ha/yr in hotspots; landscape mean emissions 0.003-0.070 t CO2/ha/yr. This is evidence that removal for bioenergy is the exception in Mediterranean practice and that avoided-wildfire carbon is small per ha.
- Greece: prescribed fire effectively not used (S).
- No Mediterranean study comparing pile-burn vs mulch vs bioenergy carbon balance was found (N).

## 6. Validation totals

- PT fuel management reported (AGIF): see section 2 (V). Total cumulative 2020-2024 about 400,000 ha vs ~1 Mha planned in the national programme (V).
- PT primary network: new effectively managed area 6,200 ha in 2024 (target 12,000); 315 segments, 16,458 ha in processing; 70 DUPs covering 2,931 ha (V).
- UNVERIFIED snippet claims: AGIF summary page says ~196,000 ha fuel management executed in 2025 (inconsistent with the 2019-2024 range of 65-88k; if real, a definition or scope change; check before use).
- EFFIS country burned area, ha (V, xlsx): PT 2017 539,921; 2022 110,097; 2024 137,651. ES 2017 178,234; 2022 267,947; 2024 47,711. HR 2017 48,543. (Column assignment for GR/IT in recent years was not re-checked; use PT/ES only until confirmed.)
- PT 2017 salvage: Leiria national forest, 558,000 m3 sold at auction, EUR 11.4 m of EUR 15.5 m (Sabado 2018 quoting ICNF president; S, UNVERIFIED). No national salvage total found.
- Spain BLP 2024: 958.2 ha (V). Fire-prevention recommendation of 1% of forest area = 260,000 ha/yr (Pau Costa statement; S) is a target, not execution.
- ENSPRESO NUTS0 values above (V).

## 7. Open questions and risks

1. Portugal's reported hectares are mostly linear, repeat-annual maintenance and omit most private and municipal work; treated hectares are not unique hectares, so they are an activity measure and cannot be summed as area.
2. How much treatment actually yields removable biomass is unknown. Harvester-baler trial (2.3 t DM/ha) and one French note (one third harvestable) suggest low recoverability; slopes and logistics dominate.
3. No NUTS-2 treatment data except what we reconstruct. The DGT raster has undefined cause (can include fire and grazing) and covers only the primary network. Need to open raster, size and licence (marked "notspecified").
4. EFFIS NUTS-2 tables "on request" is a search-snippet claim; EFFIS polygons are CC BY 4.0 by the site licence but check the data-request terms.
5. ENSPRESO FRSR1a landscape-care overlap and Cyprus zeros need resolving before adding any stream.
6. Not searched in depth: regional Spanish agencies (Galicia/SEAGA, Catalonia Bombers/Forestal Catalana, Andalucia INFOCA/AMAYA, CyL), Italian regional AIB plans and Rapporto sullo stato delle foreste, French ONF/ministry data, Greek forest service, Croatian Hrvatske sume, Cypriot Dept of Forests. Language-specific searches (ES/IT/FR/EL/HR) would likely find more. FIRE-RES and SILVANUS deliverables were not read; no treatment dataset surfaced.
7. EU Commission Communication on integrated wildfire risk management (25 March 2026; S) and 2025 EU burned area above 1 Mha (S): UNVERIFIED, read the Commission text if cited. The "EU Wildfire Prevention Action Plan" (2022) was not found as such.
8. Post-fire salvage: no national volumes; DFDE data download not located; salvage fraction by country unquantified. Burned area x forest fraction is plausible only with an assumed, country-specific salvage fraction (large in PT eucalypt/pine, low in Spain/Greece protected or steep terrain: UNVERIFIED generalisation).
9. Counterfactual: if residues would have been burned or left, removal avoids little CO2 relative to a mulch baseline; BiCRS credit logic should be confirmed with the project's counterfactual rules.
