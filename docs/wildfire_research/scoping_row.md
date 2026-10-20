# Wildfire / fuel-management residue: scoping for Rest-of-World (outside North America and Europe)

Date: 2026-10-19. Scoping only; nothing built, no data downloaded.

## Verification caveat (read first)

Many primary publishers returned HTTP 403 to automated fetch (rfs.nsw.gov.au, ffm.vic.gov.au, mdpi.com, openknowledge.fao.org). The search tool returns model-summarised snippets, not raw pages. Hence "Verified = Y" below means: the number was seen on a page I could open and I quote it. Everything else is labelled UNVERIFIED (snippet/secondary) and must be re-checked against the primary document before use. Verbatim quotes below are copied from the fetched text, except where marked "snippet".

Pages actually opened and read:
- arr.news / volunteerfirefighters.org.au (John O'Donnell commentary, a SECONDARY advocacy source quoting NSW RFS annual reports): fetched OK via curl.
- vic.gov.au report-card page (cross-tenure burn table).
- discover.data.vic.gov.au dataset page (licence/format).
- globalfiredata.org/data.html (GFED).

## 1. Global sources

| Source | What it offers | Spatial unit | Open? | Usable for | Status |
|---|---|---|---|---|---|
| FAO FRA 2025 (fra-data.fao.org; platform at fao.org/forest-resources-assessment/data/en; API listed on FRA page) | Country-reported forest area affected by fire, plus disturbances. A FAO-hosted "what has changed and why" doc (via search snippet) lists Section 5 as 5a disturbances, 5b area affected by fire, 5c degraded forest. FAO summary (snippet): fire affects "an average of 261 million hectares of land annually, nearly half of which is forested" | Country, 236 countries/areas | Yes (platform, spreadsheets) | Burned-area salvage proxy; NOT treated area | Table structure UNVERIFIED (FAO PDF 403). FRA page itself did not mention fire. Country values not retrieved |
| GFED5.1 (globalfiredata.org/data.html) | Gridded burned area and emissions, 1997-2022 (5.1) plus NRT 2023+; NetCDF4 via SFTP with login; summary tables for 14 basis regions only | 0.25 deg grid; regions, not countries | Free, login required | Burned area by country requires our own overlay with country polygons | Page read directly. Licence terms not checked |
| GFED4s | 1997-2025 per page, 0.25 deg; page recommends GFED5 | same | same | same | Read directly |
| MODIS MCD64A1 / FireCCI burned area | Burned area, 500 m | grid | Open (not opened in this pass) | Country burned area | Not checked |
| GFMC (gfmc.online) | Country fire notes, FAO FFM/15 working paper has "Annex 2: Fuel Treatment Statistics" (snippet) | Country | Yes | Possible historic fuel-treatment stats (old, c. 2006) | Only table of contents seen via snippet. UNVERIFIED |
| Global estimate of biomass from fuel treatments | None found. Searches returned US-only (DOE BETO Billion-Ton 2023) and Canada items | n/a | n/a | n/a | No global source exists in what I found. Treat as a gap |

Conclusion: no global treated-area or fuel-treatment-biomass dataset was found. FRA gives fire-affected area (country), which supports at most a salvage proxy. Fuel-treatment tonnage has to come from national sources.

## 2. Per-country table

"Verified" = Y only where I read the number myself on an opened page. Even then, many are secondary.

| Country | Best source found | Stream type | Annual figure | Spatial unit | Open? | Verified |
|---|---|---|---|---|---|---|
| Australia: NSW | NSW RFS Annual Report 2023-24, Appendix pp. 98-99 (primary, 403 to me). Read via O'Donnell commentary (secondary): "Hazard reduction burning and mechanical removal totalled 139,927 hectares for NSW (Appendix pages 98 and 99)" with "13,840 ha mechanical" (126,087 ha burning by subtraction); 2022-23: 90,089 ha (82,393 burn, 7,696 mech, snippet) | Mechanical fuel treatment (10%) vs burning (90%) | 13,840 ha mechanical (2023-24), 7,696 ha (2022-23, UNVERIFIED snippet) | State; annual report tables; NSW RFS also publishes spatial data (not checked) | PDF reports | Secondary Y (arithmetic and numbers read); primary N |
| Australia: Victoria | FFMVic Bushfire Risk Mitigation Update 2024-25 (403 to me; figures via search snippet, UNVERIFIED): 270 planned burns 92,473 ha; 951 non-burn treatments 17,465 ha (3,939 ha mulching, 10,498 ha slashing/mowing, 3,028 ha other) | Mechanical (mulching, slashing, mowing; mostly low-biomass slashing/mowing on roadsides and grass) vs burning (84%) | 17,465 ha non-burn on public land | Polygons: Joint Fuel Management Program dataset, data.vic.gov.au, CC BY 4.0, formats SHP/GDB/TAB/WFS; page says it includes "prescribed burns planned for ignition and associated mechanical and vegetation works", attributes not inspected | Yes, CC BY 4.0 (read) | Dataset Y; hectares N |
| Australia: other states, national | No national mechanical-vs-burn dataset found. WA DFES reports planned burning only (snippet: 4.5 Mha burned 2018-19, mostly rangeland/savanna) | Burning dominant | n/a | State | n/a | N |
| Australia: Black Summer salvage | Forestry Corporation NSW / NSW DPI: salvage 2.4 Mt by end 2019-20 and more than 2.7 Mt later (snippets; also "close to five million tonnes" in one snippet, inconsistent) | Salvage, mostly softwood plantation sawlogs | One-off event 2019-20 | State | Press/Gov | N, and one-off, mostly merchantable roundwood, mostly not residue |
| South Africa | DFFE Natural Resource Management Programmes (Working for Water). No national annual figure retrieved. Snippets: early pace 33,000 to 221,000 ha/yr (1995/96 to 1999/00, parliamentary reply); 238,823 ha in one year (c. 2000 ministerial speech); R2.67bn five-year programme from Nov 2023; SANParks 431,237 ha over 5 yrs; Gauteng 74,781 ha over 5 yrs; Western Cape 39,089 ha in 2022/23 (Western Cape Provincial Parliament Q&A) | Invasive alien plant (IAP) clearing; includes initial and follow-up clearing, so hectares double-count the same land | Order 10^5 ha/yr gross (UNVERIFIED); initial-clearing share unknown | Provincial tables exist (Western Cape example) | Reports/parliamentary replies | N |
| Chile | CONAF / MOP Plan Nacional de Cortafuegos: 3,361.1 km (2023-24), 3,775.1 km (2024-25), 102% delivered per Emol Jan 2025 (snippets). Season 2022-23 burned about 440,000 ha, 231,914 ha plantations (CONAF director, snippet) | Linear fuel breaks, mostly bare-soil/vegetation-free strips by machine; litter and shrubs, little wood | Kilometres, not ha or t. At an assumed 20-30 m width 3,775 km is about 7,500-11,000 ha, my arithmetic, width not sourced | Region | Press / gov | N |
| Brazil | Prevfogo/ICMBio integrated fire management plans (documents found, no national hectares). Law 14.944/2024 (UNVERIFIED) | Prescribed/early burning, aceiros (bare firebreaks) in Cerrado/Pantanal; savanna grass | Not found | Unit/territory | Partly | N. Expect nothing collectable |
| Argentina | SNMF; audit reports say Law 26.815 largely unimplemented, 25% of 2025 budget unexecuted (snippets) | Fire-lines, minimal | Not found | Province | n/a | N |
| Israel | KKL-JNF: thinned about 32,000 dunams (about 3,200 ha) in 2024 (snippet, KKL self-reported, conversion mine); more than 200 firebreaks; grazing used | Thinning of pine plantations + grazing | about 3,200 ha/yr, single year | National | PDF | N |
| Turkey | OGM: about 16,500 km forest-road corridors and 2,500 km around 2,247 settlements cleared (Jul 2026 AA report, snippet) | Linear fuel reduction, km | km only | National | Press | N |
| Morocco | HCEFLCD: 182.7 MDH 2018 budget includes firebreak maintenance (snippet) | Firebreaks | No ha/km found | National | n/a | N |
| Indonesia | BRGM / BRG: peat rewetting (canal blocks, wells); 5,936 canals blocked / 679,901 ha by 2018 (snippet) | Hydrological, no woody residue | n/a | n/a | n/a | Confirmed not a woody-residue stream (by nature of the intervention) |
| China | No national firebreak/fuel-break statistic found. Only county-level plan (Jiangle, Fujian: 3,591.67 km biological fuelbreaks needed, snippet) and modelling studies (Great Xing'an). Policy: prescribed burning curtailed after a 2004 incident (snippet) | Firebreak belts, prescribed burning | Not found | n/a | n/a | N |
| India | Uttarakhand pine needles: gross 1.9 Mt/yr, net 1.33 Mt/yr (research paper, snippet); 1.97 Mt gross (snippet); 15 lakh t (Drishti IAS explainer, secondary). Only six 250 kW units installed vs 58 planned (Drishti, snippet). Himachal: chir pine about 125,885 ha at about 1.2 t/ha/yr needles (Tribune/FRI, snippet) so about 150,000 t/yr (my arithmetic); Hamirpur scheme 600 t/season (2012) | Pine needles (litter, not wood). A fire-prevention biomass stream, but off-take is tiny vs potential | Potential about 1.3-2 Mt/yr Uttarakhand; realised collection about 10^2-10^3 t scale in cited schemes | State/forest division | Reports | N |
| Japan | Nothing found on fuel management programmes | n/a | n/a | n/a | n/a | N |
| South Korea | KFS (via snippet): 2025 Yeongnam fires affected 103,876 ha of forest vs 10-yr average 4,003 ha; damaged pine to public timber buildings; Korean report (civil-society, UNVERIFIED) claims 63% of 2022-2025.9 large-fire damaged trees felled were sold as unused forest biomass | Salvage (one-off, 2025) | No official removal volume found | National / province | KFS press releases | N |
| New Zealand | National Wilding Conifer Control Programme: more than 1.5 Mha under management (Landcare Research, snippet); Mid Dome Trust 2023-24: 3,617 ha aerial basal bark, 506.5 ha ground control (snippet) | Wilding conifer control. Mostly herbicide/standing-dead, not harvested | ha treated yes; biomass no | Region/trust | Reports | N. Mostly not extracted |

## 3. Recommended approach for the Global scope

1. Do not build a generic ROW "wildfire" stream from treated-area x yield. The data do not exist at country level outside the US, Canada and Europe. Say so in the map.
2. Quantified stream (low-moderate effort): Australia only, mechanical fraction. Use state data (NSW annual-report appendix, Victoria JFMP polygons, CC BY 4.0). The collectable fraction is small: NSW mechanical about 14,000 ha/yr, Victoria non-burn about 17,000 ha/yr, of which the majority is slashing/mowing (grass/shrub, low collectable mass). Only mulching (about 4,000 ha/yr Vic) and some forest thinning produce woody material, and mulching typically leaves it on site. Expect an order of magnitude of 10^4-10^5 odt/yr nationally at most, UNVERIFIED and uncomputed. Treat as caveat-level until yields are sourced.
3. Separate stream, not "wildfire residue": South Africa IAP clearing and NZ wilding conifers. Rationale: the driver is biodiversity and water security, treatment is hectare-based with follow-up, material is largely left on site or burned, and counting it as fire-risk reduction would overstate the additionality claim. If included, label "Invasive-plant clearing biomass". South Africa is the only credible candidate, since the programme has documented hectares, provincial data and a bioenergy literature (Mugido et al. 2014, SAJS; Sustainability 2024 review, abstract-level only). NZ: do not quantify, since wildings are mostly killed standing and not harvested (snippets).
4. India: pine needles are a distinct "fire-prevention litter" stream with a modelled potential (about 1.3 Mt net/yr Uttarakhand) but realised collection is tiny. Show as a caveat/potential layer for Uttarakhand and Himachal only, flagged low confidence. Needles are litter, not woody residue, and removal also has ecological effects.
5. Caveat only: Chile (km of fuel breaks, no biomass), Israel, Turkey, Morocco (km or unit-less), Korea (2025 salvage, one-off), Australia Black Summer salvage (one-off, mostly merchantable).
6. Nothing: Brazil, Argentina, Indonesia, China, Japan.
7. Salvage proxy: Salvage after fire is distinct from fuel management. A FRA/GFED burned-area proxy would be a different stream and would need a salvage fraction and merchantability screen. Not recommended for screening without evidence.

## 4. Yield / conversion factors

Few sourced values were obtained. Do not use any of these without verifying.
- Chir pine needles: about 1.2 t/ha/yr litterfall (Himachal forest-department figure via Tribune/FRI notice, snippet, UNVERIFIED) times about 125,885 ha. Gross 1.9 Mt, net 1.33 Mt Uttarakhand (research paper snippet; the paper itself not opened).
- South Africa IAP t/ha: NOT FOUND. Mugido et al. 2014 sampled 31 sites in Nelson Mandela Bay but the abstract has no t/ha. Full text at sajs.co.za/article/view/4040 (DOI 10.1590/sajs.2014/20130397) should be read. The 2024 Sustainability review (doi 10.3390/su16051876) and van Wilgen et al. work are the places to look.
- Australia mechanical-treatment yields: NOT FOUND. Use US analogue only as a labelled placeholder (e.g. BETO).
- Chile fuel-break width, kg/m2: NOT FOUND.

## 5. Counterfactual evidence

- Australia: burning dominates (NSW about 90% of hazard-reduction hectares in 2023-24 is burning, computed from the O'Donnell figures; Victoria FFMVic about 84% planned burns in 2024-25, computed from snippet figures). Burned fuel yields nothing collectable. Mechanical slashing/mowing residue stays in place.
- South Africa: a 2019 commentary (via snippet) says use of biomass from invasive trees "remains the exception" and wood is most often left on site to decay or burn. UNVERIFIED. Coega Biomass Centre makes pellets from IAP (Engineering News, 2025, snippet), so a real but small utilisation exists.
- India: UREDA pine-needle power projects described as "unsuccessful" (Drishti IAS, 2024, snippet, secondary). Needles are mostly burned in uncontrolled fires or left.
- Korea: civil-society analysis claims most salvage went to unused-biomass fuel (UNVERIFIED).
- China: prescribed burning has been curtailed since 2004 (snippet).
- Brazil: fire management is burning-based (early/prescribed burns), so no biomass.

## 6. Open questions and risks

1. Primary documents behind 403s must be retrieved manually by the user (NSW RFS annual report 2023-24 Appendix; FFMVic 2024-25 Bushfire Risk Mitigation Update; FRA 2025 guidelines and country tables; DFFE Working for Water annual report).
2. Does FRA 2025 actually report area burned by country with usable coverage for our 82 countries? Structure per snippet only.
3. Hectares of IAP clearing double-count follow-ups. Initial-clearing hectares and condition class (density) are needed to estimate tonnes. Biomass t/ha unsourced.
4. Additionality: IAP clearing is already funded. Whether the residue is stranded or left in situ is unknown. Risk of presenting a biodiversity programme as wildfire management.
5. For Victoria, the JFMP polygons are "planned" activities for the next three years, not delivered. Delivered totals are in the annual update. Attribute fields distinguishing burn vs mechanical were not inspected.
6. Mulching leaves biomass in place. Collectable fraction of mechanical treatment is unknown, probably well below 100%.
7. All fuel-management hectares vary by year by a factor of 2-4 (NSW 44,642 ha in 2021/22 to 199,248 ha in 2018/19, all treatments, from O'Donnell). Use multi-year means.
8. Global-scale outcome: for the Global scope, the honest answer for most countries is "no stream". Recommend an explicit note in the UI rather than a zero.
