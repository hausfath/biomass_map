# Scoping: pan-European AD/biogas/biomethane plant-level data sources

**Scope:** EU-27 + UK + Norway, focused on the countries NOT covered by national deep-dives (UK, Germany, Italy, France, Denmark, Netherlands are handled separately). Target countries here: Austria, Belgium, Czechia, Poland, Sweden, Spain, Ireland, Finland, Hungary, Norway, Portugal, Slovakia, plus smaller EU states (Croatia, Slovenia, Baltics, Bulgaria, Romania, Greece, Luxembourg, Cyprus, Malta).

**Purpose:** identify real plant-level AD/biogas/biomethane locations (all types: agricultural/manure, biowaste, industrial, sewage sludge; CHP and biomethane) to replace hand-placed national points on the BiCRS AD layer, and to estimate manure-to-AD share.

**Session date:** 2026-09-25. All sources below were actually opened (WebFetch/WebSearch/curl) in this session unless flagged UNVERIFIED. Anything drawn only from a search-result snippet or secondary summary (not the primary document/page itself) is explicitly labeled **UNVERIFIED**.

---

## 1. Pan-European source table

| Source | URL | Publisher | Licence | Latest edition/date | Format / size | Records | Key fields | Coords? | Verified |
|---|---|---|---|---|---|---|---|---|---|
| **EBA/GIE European Biomethane Map** | gie.eu/publications/maps/european-biomethane-map/ ; europeanbiogas.eu/publication/european-biomethane-map-2026/ | EBA + GIE | Not stated on either page | 2026 ed. (7th), data as of June 2026 | **Printed A0 poster / PDF poster only**, free digital copy on request; an "open-access interactive map" is referenced (3rd year running) but no working embed/export URL was found in this session (europeanbiogas.eu/european-biomethane-map-2024/ and -2025/ both 404'd) | 1,975 biomethane plants, 26 countries | Plant existence, capacity (aggregated); underlying per-plant CSV/GIS not found | Interactive map shows points, but **no confirmed bulk download with coordinates** | Y (page content) / **N for underlying dataset access** |
| **EBA Statistical Report** (annual) | europeanbiogas.eu/wp-content/uploads/2024/12/EBA_stats_report_complete_241204_preview.pdf | EBA | Not stated; PDF free to download | 2024 ed. (Dec 2024), 15th ed. announced Dec 2025 | PDF, 1.7 MB (free preview) | Preview = 17 pages total: intro chapters + **one sample country (Austria)** only. Full report has per-country chapters for 28 countries (ch.6, pp.87–182 per TOC) but is **paywalled/purchase-only** (per publisher and secondary press) | National plant counts by feedstock type (agri/sewage/landfill/MSW/other), production GWh, biomethane grid-connection share | No coordinates (national/aggregate only) | Y (preview content directly read); full report content **N — not accessed, paywalled** |
| **EEA Industrial Reporting database** (EU Registry + E-PRTR/LCP) | eea.europa.eu/en/datahub/datahubitem-view/9405f714-8015-4b5b-a63c-280b82861b3d ; download via sdi.eea.europa.eu/datashare/s/sptXqwkQr5g7Bp5/download | EEA (under IED 2010/75/EU + E-PRTR Reg. 166/2006) | **CC BY 4.0** (confirmed in metadata JSON) | v10.0, Dec 2023 (dataset id `eea_t_ied-eprtr_p_2007-2022_v10_r00`); note one search result cited "2007–2023" elsewhere — **date range discrepancy not resolved** | xls/xlsx/mdb/accdb/csv/txt/sql; **exact file size could not be determined** — the download link is a Nextcloud share that streams a dynamically-built archive rather than a static file with a Content-Length; HEAD request returned an HTML wrapper, not size info | All EU IED Annex I facilities (tens of thousands, all activities, not just AD) | Facility ID, name, activity code (Annex I, incl. 5.3(b)(i) biological treatment), location, energy/emissions data | Facility-level EU Registry is documented elsewhere as including coordinates, but **field-level confirmation was not obtained in this session** | Partial — metadata/licence Y, actual file structure/size **N** |
| **E-PRTR (legacy standalone)** | eea.europa.eu/data-and-maps/data/member-states-reporting-art-7-...e-prtr-database | EEA | Not directly re-confirmed this session | v18, covers 2007–2017 | CSV ZIP, **56.9 MB** (per search snippet — UNVERIFIED, not independently re-confirmed by HEAD in this session; superseded by the v10 combined IED-EPRTR dataset above) | — | — | — | **UNVERIFIED** (secondary snippet only) |
| **JRC — spatial biogas potential from manure** | publications.jrc.ec.europa.eu/repository/handle/JRC104329 | JRC | Ambiguous — page shows a note that in some contexts the doc is Commission-internal, in others public | 2020 | PDF report; 1km-resolution gridded **modeled potential**, NOT a plant inventory | Estimated 13,866–19,482 *possible* plant sites (theoretical), not existing plants | None — potential map, not facility list | No plant coordinates (grid-cell potential only) | Y (confirmed not plant-level) |
| **JRC "biomethane initiatives" database** (referenced in JRC bioenergy reports) | publications.jrc.ec.europa.eu (JRC135079 and related) | JRC | Unknown | Unclear/not dated in this session | Unknown | Referenced as compiled from "project websites, association datasets, literature" | Unknown | Unknown | **UNVERIFIED — not located/opened this session**, flagged as follow-up |
| **Global Energy Monitor — Global Bioenergy Power Tracker** | globalenergymonitor.org/projects/global-bioenergy-power-tracker/download-data/ | GEM | **CC BY 4.0** | Released Sept 2025 | CSV/XLSX (typical GEM format) | >4,500 units worldwide, but **threshold ≥30 MW** | Name, capacity, fuel type, status, operator, lat/lon | **Y**, but only for units ≥30 MW | Semi-verified (search-synthesis; licence/threshold cross-checked but download page not directly opened) — **gap: excludes ~all farm/industrial-scale AD, which are almost always <5 MW** |
| **Open Power System Data — renewable_power_plants** | github.com/Open-Power-System-Data/renewable_power_plants | OPSD (academic/NGO consortium) | Open (per OPSD project terms) | Data package last updated **2020-08-25**; GitHub repo confirmed **not archived** but **last pushed 2020-08-26** (stale ~6 years) | CSV + JSON metadata, Excel/SQLite variants | Covers **DE, DK, FR, PL only** among our target list | Plant name, capacity, fuel, coordinates (where available) | Y for DE/DK/FR; PL coverage/coord completeness not confirmed | Y (repo status verified via GitHub API) — **stale, pre-dates Poland's Oct-2023 agricultural-biogas registry** |
| **OpenStreetMap via Overpass API** (`man_made=digester`, `generator:source=biogas`, `generator:method=anaerobic_digestion`) | overpass.kumi.systems/api/interpreter (public mirror; overpass-api.de itself returned HTTP 406 to this session's requests) | OSM contributors | **ODbL** | Live snapshot ~2026-06-01 | Query API, live | See live counts below | Whatever tags mappers added (highly inconsistent — capacity, operator rarely present) | Y (lat/lon inherent to OSM) | **Y for the counts obtained** — but counts are known/expected severe undercounts vs. true plant numbers |

### Live OSM Overpass counts obtained this session (`man_made=digester` + `generator:source=biogas` + `generator:method=anaerobic_digestion`, combined, deduplicated within query)

Run via `overpass.kumi.systems` (a community mirror; the canonical `overpass-api.de` endpoint rejected every request from this environment with HTTP 406, including the standard OSM-wiki example query — an environment/networking issue, not a query bug).

| Country | Total tagged features | nodes | ways |
|---|---|---|---|
| Poland (PL) | 20 | 1 | 19 |
| Spain (ES) | 44 | 36 | 8 |
| Ireland (IE) | 17 | 6 | 11 |
| Hungary (HU) | 33 | 9 | 24 |
| Austria, Belgium, Czechia, Sweden, Finland | query errors (rate-limited by the free mirror; requests returned non-JSON/empty bodies) | — | — |
| Norway, Portugal, Slovakia, Croatia, Slovenia, Lithuania, Latvia, Estonia, Bulgaria, Romania, Greece, Luxembourg, Cyprus, Malta | queued but not confirmed complete before this report was finalized — full log at `/private/tmp/.../scratchpad/ad_eu/overpass_counts.txt` | — | — |

**Interpretation:** these counts (e.g. 20 for Poland, which independently has a national agricultural-biogas registry implying well over 100 operating plants) are clearly **large undercounts** relative to true plant numbers. OSM tagging of digesters/biogas generators is incomplete and inconsistent across Europe. Treat OSM as a **supplementary geolocation cross-check for already-known plants**, not a standalone census source.

---

## 2. Per-country table (non-deep-dive countries)

| Country | Best available source found | Record count | Coords Y/N | Notes |
|---|---|---|---|---|
| **Austria** | EBA Statistical Report 2024 (verified, read directly) + E-Control Anlagenregister + Biomethanregister Austria (biomethanregister.at) | **343 biogas plants + 16 biomethane plants (2023)** — VERIFIED primary; a separate secondary source (2021 Biomethane Fiche) cites 15 biomethane plants for 2021, consistent trend | National register (E-Control) likely plant-level but coordinate field not confirmed this session | Best-documented of the twelve; feedstock split given (agri ~49% of plants, sewage 24%, MSW 28% — approximate, read from chart) |
| **Belgium** | No single national register found. Fragmented: Biogas-E (Flanders knowledge platform), VREG (Flemish GO register), greenGasRegister.be, Fluxys (federal production registrar for green gas) | Not obtained; "6th Belgian biomethane plant" as of Aug 2022 (UNVERIFIED, dated, secondary) | Unknown | IEA Bioenergy Belgium 2024 country report (opened directly, PDF read) gives bioenergy energy shares (biogas ~10% of bioelectricity from biomass, 2022) but **no plant count or coordinates** |
| **Czechia** | ERÚ (Energy Regulatory Office) licence register (eru.gov.cz, Czech-language licence finder) + Czech Biogas Association map (czba.cz/en/map-of-biogas-plants.html — **not yet opened, flagged as a promising direct follow-up**) | ~540 biogas plants, ~2,560 GWh/yr electricity (UNVERIFIED, secondary/press synthesis) | CZBA map likely has coordinates — unconfirmed | Highest Eurostat biogas production of the target group (see validation table) |
| **Poland** | KOWR (Krajowy Ośrodek Wsparcia Rolnictwa) Rejestr wytwórców biogazu rolniczego (gov.pl/web/kowr) | Public list of registered agricultural biogas producers; ~583 million m³/yr registered capacity (UNVERIFIED figure, secondary synthesis); register only in force since Oct 2023 amendment | Register is publicly viewable but coordinate/format unconfirmed this session | Register covers **agricultural biogas only** — excludes municipal/industrial/sewage AD, which would need a separate source (URE, GUS, or Eurostat) |
| **Sweden** | Energimyndigheten official statistics ("Produktion och användning av biogas", downloadable Excel) + Energigas Sverige interactive map | **Contradictory secondary figures**: one snippet says 284 biogas facilities on the Energigas Sverige map, another says "76 biogasanläggningar" — likely different definitions (e.g. all producing plants vs. upgrading/injection plants only) — **UNVERIFIED, unresolved, needs direct site visit** | Energigas Sverige map is interactive/plant-level, likely has locations — unconfirmed | Official government Excel stats exist and are the more trustworthy validation source; not opened directly this session |
| **Spain** | RAIPRE (Registro administrativo de instalaciones de producción de energía eléctrica), MITECO | Registry "downloadable via an application with permanent updates," exportable to Excel by province/autonomous community | Likely province/municipality-level location at minimum; plant-level coordinates unconfirmed | Best formal candidate for Spain; not directly queried/downloaded this session — needs a follow-up visit to the actual RAIPRE application |
| **Ireland** | National Biomethane Strategy (June 2024) figures, SEAI, Gas Networks Ireland Renewable Gas Registry | **43 biogas-producing facilities + 2 biomethane grid-injection facilities** (UNVERIFIED, secondary synthesis); target of 200 AD plants by 2030 stated in the Strategy | Registry is for GO certificates, not necessarily an open plant-location list | Small absolute numbers make this one of the more tractable countries for manual verification |
| **Finland** | Historical "Suomen biokaasulaitosrekisteri" (Finnish national biogas register), compiled periodically by University of Eastern Finland / LUKE | Last confirmed edition found: no. 21 (2019 publication, data year 2017); earlier editions (e.g. no.15, data year 2011) broke down 16 municipal WWTP digesters + 10 farm-scale + 8 MSW-treating plants | Unknown — historical PDF reports, not obviously geocoded | **Currency gap**: no 2023/2024 edition located this session — may be discontinued or succeeded by a different LUKE product; needs follow-up |
| **Hungary** | Not researched this session beyond the EBA report TOC listing (ch. 6.13, p.132, inaccessible — paywalled) | — | — | **Gap — no country-specific search performed**; flagged for next session |
| **Norway** | Miljødirektoratet report M-1652 (2020, policy-focused) + Enova SF (grant-recipient list only) | Not a comprehensive plant register; Enova funding announcements name a handful of supported plants (e.g. Hardanger Biogass, Lista Biogass, RENEVO, Sømna Biogass) | Unknown | No consolidated national register identified |
| **Portugal** | Not researched this session beyond noting Portugal joined biomethane production in 2022 (per EBA Statistical Report press coverage) | — | — | **Gap** |
| **Slovakia** | Not researched this session beyond EBA TOC listing (ch. 6.26, p.169, paywalled) | — | — | **Gap** |
| **Croatia, Slovenia, Baltics (LT/LV/EE), Bulgaria, Romania, Greece, Luxembourg, Cyprus, Malta** | Not individually researched this session | — | — | **Gap** — only Eurostat aggregate production figures available (Section 4) |

---

## 3. Recommended approach (backbone + gap-fillers + dedup)

Given what was actually verified this session, no single pan-European source gives an open, plant-level, coordinate-bearing dataset for the twelve target countries. Recommended layered approach:

1. **Backbone — none of the candidate pan-European datasets qualify outright.** The EBA Biomethane Map/Statistical Report is the most authoritative aggregator, but its plant-level detail is paywalled (Statistical Report) or not bulk-exportable (Biomethane Map interactive view). **Before building anything, it is worth directly emailing EBA (contacts on the report: decorte@europeanbiogas.eu) to ask whether a research/NGO licence for the underlying database is available** — this is the single highest-value ask given the ~1,975-plant biomethane coverage and the more detailed (but paywalled) Statistical Report country chapters covering biogas CHP plants too.
2. **Large/industrial-scale facilities (biomethane upgrading, large CHP, sewage AD ≥100 t/day):** EEA Industrial Reporting database (EU Registry + E-PRTR/LCP), CC BY 4.0, filtered to IED Annex I activity 5.3(b)(i). This requires downloading the full IED dataset (size TBD — likely well over 50 MB given it's all EU industrial activities) and filtering locally to the relevant activity code and facility-name/NACE text matching to separate AD from plain composting. **This is the most legally clean, genuinely-coordinate-bearing source identified**, but needs a dedicated follow-up session to actually pull and filter it (do NOT bulk-download without confirming size first, per the working rules — the Nextcloud share didn't return a size on HEAD, so a browser-based or `curl -o` streaming test with an early abort/size-check is needed).
3. **Country-by-country gap-filling for small/farm-scale AD:** national registers are the only route, and quality varies enormously:
   - Poland (KOWR), Spain (RAIPRE), Austria (E-Control/Biomethanregister), Czechia (ERÚ + CZBA map) look most promising for actual plant-level records and should be prioritized for direct download/scraping next.
   - Sweden, Ireland, Finland have data but of uncertain currency/granularity.
   - Belgium, Norway, Hungary, Portugal, Slovakia, and the smaller EU states have no consolidated register identified yet — will likely require the EBA Statistical Report's paywalled country chapters, or direct outreach to national biogas associations (IEA Bioenergy Task 37 has member-country contacts).
4. **Manure-to-AD share:** see Section 5 — no ready cross-country figure obtained; needs a dedicated CRF-table extraction effort.
5. **Dedup strategy (once multiple sources are combined):** match on (a) name + municipality/postcode fuzzy match, (b) coordinate proximity (<500 m) where multiple sources give coordinates, (c) capacity as a tie-breaker. Given the poor coordinate coverage found so far, expect this to be a smaller problem than usual — the bigger problem is **coverage gaps**, not duplicate records.

---

## 4. Validation totals (Eurostat, verified via direct API pull)

**Source:** Eurostat `nrg_bal_c` ("Complete energy balances"), SIEC code **R5300 "Biogases"** (note: this Eurostat code is itself an aggregate of landfill gas + sewage sludge gas + other AD-derived biogas — it is **not** an AD-only cut; a follow-up query on the sub-codes R5210/R5220/R5290 would isolate AD specifically), `nrg_bal` code **PPRD "Primary production"**, unit KTOE, dataset last updated 2026-08-27, **latest year available: 2024**. Pulled directly via `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c` — genuinely verified, not a secondary summary.

| Country | Biogases primary production, 2024 (ktoe) |
|---|---|
| Austria | 191.7 |
| Belgium | 270.6 |
| Czechia | 627.9 |
| Poland | 408.5 |
| Sweden | 189.9 |
| Spain | 374.7 |
| Ireland | 51.7 |
| Finland | 179.8 |
| Hungary | 103.0 |
| Norway | 84.8 |
| Portugal | 94.6 |
| Slovakia | 143.9 |
| Croatia | 75.0 |
| Slovenia | 21.1 |
| Lithuania | 38.3 |
| Latvia | 39.0 |
| Estonia | 24.1 |
| Bulgaria | 48.4 |
| Romania | 15.3 |
| Greece | 184.7 |
| Luxembourg | 16.1 |
| Cyprus | 12.3 |
| Malta | 2.8 |
| **EU-27 total** | **16,415.7** |

**Austria plant-count validation (EBA Statistical Report 2024, primary/verified):** 343 operational biogas plants + 16 biomethane plants in 2023, combined biogas+biomethane production 1,675 + 131 GWh. Roughly consistent in scale with the Eurostat Austria figure above (191.7 ktoe in 2024 ≈ 2,230 GWh — note this is a different year and Eurostat's figure likely includes non-EBA-tracked biogas uses, so treat as order-of-magnitude consistency, not an exact reconciliation).

---

## 5. Manure-to-AD share findings

**Bottom line: no ready-made, harmonised, cross-country figure was obtained this session.** The user's hypothesis — that UNFCCC/EEA national GHG inventory CRF Table 3.B(a) reporting includes "Anaerobic digester" as one of several manure-management-system (MMS) categories, with country-specific percentage shares of manure nitrogen/volatile solids managed this way — is **methodologically correct** (this is standard IPCC AFOLU reporting structure, and "Anaerobic digester" is one of the defined MMS categories alongside pasture/range/paddock, solid storage, liquid/slurry, anaerobic lagoon, pit storage, etc.). However:

- This data lives in each country's **CRF (Common Reporting Format) tables**, submitted individually to UNFCCC as part of each National Inventory Report — there is **no single consolidated EU-wide CSV of "% manure to AD by country"** that this session located.
- The UNFCCC's own flexible query interface (`di.unfccc.int/detailed_data_by_party`) is JavaScript-rendered and returned empty content to a direct fetch in this session — **could not confirm whether it exposes MMS-level (sub-3.B) granularity or only aggregate 3.B emissions**. This needs a browser-based check or the underlying API to be found.
- EEA's own GHG data viewer documentation (read directly) describes sectoral groupings down to CRF-category level (e.g. "3 Agriculture") but its stated documentation did **not** confirm MMS sub-type breakdown is exposed in the bulk download.
- **Recommended next step:** pull individual countries' latest CRF table 3.B(a)s1–s4 (cattle, swine, other) directly from the UNFCCC national inventory submissions (2026 submission round, 2024 inventory year) for the 12 target countries — this is a well-defined but multi-file extraction task (per-country XML or Excel CRF tables), not a single download, and should be scoped as its own follow-up task rather than attempted within this scoping session's budget.

No manure-to-AD percentage figures — verified or unverified — are reported here, to avoid fabricating numbers. This section should be treated as **open and unresolved**, not answered.

---

## 6. Open questions / risks

1. **EBA data licensing is the single biggest unresolved lever.** If EBA will license the underlying Biomethane Map / Statistical Report database (even at a fee, or for research use), that likely beats stitching together twelve heterogeneous national registers. Worth a direct email before committing engineering time to the EEA/OSM/national-register patchwork.
2. **EEA Industrial Reporting file size and exact download mechanics are unresolved** — the share link streams through a Nextcloud app rather than serving a static file with Content-Length, so "check size before downloading" (per working rules) could not be completed by HEAD request alone this session. A follow-up needs either a browser session or to hit the underlying WebDAV/API path directly.
3. **AD vs. composting cannot currently be distinguished** in the EEA Industrial Reporting dataset without either a NACE-code cross-reference or text-matching on facility names/descriptions — this needs to be resolved before the EEA source can be trusted as an "AD" layer rather than a "biological treatment" layer (composting-only sites would need to be excluded).
4. **OSM severely undercounts** AD facilities (e.g., 20 tagged features for Poland vs. an implied 100+ registered agricultural biogas producers) and should not be treated as a census source — only as a coordinate cross-check for facilities already identified by name elsewhere.
5. **Sweden's plant-count sources conflict** (76 vs. 284) and need direct resolution before use.
6. **Six of the twelve target countries (Hungary, Norway, Portugal, Slovakia, and the smaller states) have no register identified yet** — this scoping session ran out of budget before reaching them individually; only Eurostat aggregate production figures exist for them so far.
7. **The Eurostat R5300 "Biogases" figures used for validation are an aggregate of landfill gas + sewage sludge gas + other AD-derived biogas** — not an AD-only cut. A follow-up pull of sub-codes R5210 (landfill gas) and R5290 ("other biogases," closest to AD) would tighten the validation denominator; this was not done in this session.
8. **Manure-to-AD share is entirely unresolved** (Section 5) — do not use any number for this until the CRF-table extraction task is actually done.
9. **Global Energy Monitor's 30 MW threshold excludes nearly all AD facilities** — noted so it isn't mistakenly used as an AD source later.
10. **JRC's manure-biogas-potential dataset (JRC104329) is a theoretical model, not an inventory** — flagged so it isn't confused with an actual plant list if it resurfaces in a later search.
11. Licence terms for the EBA Biomethane Map itself were **not found stated anywhere** (GIE order page, EBA publication pages) — if any use of map-derived plant locations is contemplated, this needs to be clarified directly with EBA/GIE before use, not assumed to be open.

---

*Prepared by a research subagent; all "verified" claims above reflect sources actually opened via WebFetch/WebSearch/curl in this session on 2026-09-25. Raw Eurostat JSON and Overpass query logs retained at `/private/tmp/claude-501/-Users-hausfath-Desktop-Climate-Science-BiCRS-Map/36ce493b-82b8-47dd-b0cc-937ec866f26e/scratchpad/ad_eu/` for this session only (scratchpad, not persisted).*
