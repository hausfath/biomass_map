# Scoping: manure-to-anaerobic-digester share from national GHG inventories (UNFCCC CRF/CRT)

**Session date:** 2026-09-25. Scope: EU-27 + UK + Norway. Goal: determine whether a harmonised,
primary-source "% of livestock manure managed via anaerobic digestion" can be extracted per
country from national GHG inventory submissions to UNFCCC, and pilot it for UK, Germany,
Denmark, Netherlands, Italy, France.

**Status: complete** (pilot extraction done for all 6 target countries: UK, Denmark, France,
Italy, Netherlands, Germany; EU-aggregate document checked; scalability assessment and
recommended pipeline below).

All figures below were either (a) extracted directly by this session from a downloaded
primary file (marked VERIFIED, with exact source/table/page), or (b) reported back by a
delegated subagent that was instructed to open and quote primary sources directly, with the
same verification discipline (also marked VERIFIED where the subagent confirms it opened the
document itself). Anything from a press article or search-snippet synthesis only is marked
UNVERIFIED. Nothing is fabricated.

---

## 0. Key structural finding: UNFCCC's own site needs a real browser, not curl/instant-fetch

`unfccc.int` (the National Inventory Submissions pages, `/documents/*` pages, and even static
`/sites/default/files/resource/*.pdf` links) sits behind Incapsula bot-protection. `curl` (with
and without a browser user-agent) and an instant `WebFetch`/browser-tab-then-immediately-read
all returned only the Incapsula JS-challenge shell (tiny HTML, no content) — this matches a
prior scoping session's finding that `di.unfccc.int/detailed_data_by_party` also returned empty
content. **However, re-tested properly this session: navigating in a real Chrome tab
(`claude-in-chrome`) and then waiting ~6 seconds before reading the page (giving the Incapsula
JS challenge time to resolve) succeeds** — `unfccc.int/documents/646508` (UK's 2025 CRT) loaded
correctly and exposed a direct download link ("English zip 44.01 MB", published/submitted
15 Apr 2025). **So unfccc.int is not actually blocked — it just cannot be fetched instantly or
via `curl`; it requires browser automation with a short wait for the bot-challenge.** This
changes the recommended pipeline (Section 11): a working direct-from-UNFCCC route exists and
should be preferred over hunting for national-agency mirrors, once a workflow tolerates the
few-second JS-challenge delay per document.

For this session's actual pilot extraction (done before this correction was made), the practical
workaround used instead was to go directly to each Party's own national inventory compiler
(environment agency / statistics institute), which independently mirrors its own NIR, NID, and
(for some countries) the underlying CRT spreadsheet files, on its own domain. This worked well
for the UK and Italy (both mirror a ready-made CRT workbook) and, with progressively more effort,
for Denmark, France, the Netherlands and Germany (Sections 2–3, 5–8), none of which mirror the
CRT itself but do publish the underlying methodology reports. **Both routes are now confirmed
viable** — which one is more efficient at scale (29 countries) depends on how well a pipeline can
automate the browser-wait-then-download pattern versus doing 29 separate national-agency
discovery tasks; this is worth a small follow-up test before committing to either at scale.

---

## 1. Source/format table

| Source | Publisher | What it is | Format | Size | Contains MMS/"digester" %? | Verified this session |
|---|---|---|---|---|---|---|
| UNFCCC National Inventory Submissions pages (`unfccc.int/ghg-inventories-annex-i-parties/2025`, `/2026`, `/documents/*`) | UNFCCC Secretariat | Landing pages + per-country CRF/CRT/NIR/NID files | zip (CRT ≈ 40–100 MB per country per year, e.g. Germany 2025 CRT = 100.54 MB per search snippet, UK 2026 CRT = 47.4 MB confirmed) | — | Yes, structurally (Table 3.B(a)/3.B(b) "Manure Management Systems", incl. "Digesters" column) | **Blocked — Incapsula bot protection, confirmed via curl, WebFetch, and a real Chrome session** |
| UK — NAEI (naei.energysecurity.gov.uk), DESNZ | National mirror | NID (PDF), full CRT workbook-per-year zip, small supplementary EF spreadsheet | PDF (9.9–16.3 MB); CRT zip 47.4 MB (35 yearly .xlsx, ~4.6 MB each); supplementary EF xlsx 103 KB | as above | **Yes — confirmed, extracted (Section 2)** | Y — downloaded and parsed directly |
| Denmark — DCE, Aarhus University (dce.au.dk) | National mirror | Sectoral background report "Danish Emission Inventories for Agriculture" (SR696, 2026) | PDF, 6.3 MB | Yes, but as **mass** (kt slurry), not a CRT-style %N/%VS table; no CRT xlsx mirror found on this domain | Y — downloaded, quoted, deleted after extraction (subagent) |
| EU aggregate — EEA (eea.europa.eu), on behalf of the EU as a Party | EU-wide NID | "Annual European Union greenhouse gas inventory 1990-2024 and inventory document 2026" | PDF, 47.4 MB | **No** — confirmed. Chapter 5 (Agriculture) gives country-by-country CH4/N2O *emissions* tables (e.g. Table 5.9, 5.12) per source category, but does **not** publish a cross-country manure-management-system allocation/percentage table anywhere in the agriculture chapter | Y — downloaded, full-text searched, confirmed absence |
| France — CITEPA (citepa.org) | National mirror | OMINEA methodology report (23rd ed., 2026) — this **is** the primary source behind CRT Table 3.B | zip 42.4 MB (per-chapter PDFs); Agriculture chapter 5.1 MB | Yes, but as a "theoretical herd" (head-count) allocation, not %N/%VS/%mass directly | Y — downloaded, quoted (subagent) |
| Italy — ISPRA (isprambiente.it) | National mirror | Full CRT workbook-per-year zip + NID (PDF) | CRT zip 38.16 MB (35 yearly .xlsx); NID 12.96 MB | Yes — same `Table3.B(a)`/`Table3.B(b)` template as UK, confirmed | Y — downloaded, parsed (subagent) |
| Netherlands — RIVM/WUR (rivm.nl, edepot.wur.nl) | National mirror | NEMA model results + methodology reports (not a CRT mirror) | 6.5 MB + 3.3 MB PDFs | Yes, as absolute N and VS tables, not %; CBS StatLine confirmed to NOT have this breakdown | Y — downloaded, quoted, deleted (subagent) |
| Germany — Thünen Institute (git-dmz.thuenen.de wiki; formerly PDF "Thünen-Report" series) | National mirror | "Report on methods and data" (RMD) wiki, Submission 2026 — this **is** the primary source behind CRT Table 3.B(a) | GitLab wiki pages (~476 KB total text/images retrieved) | Yes, but as an **absolute Gg N figure**, not a %; no national manure-N denominator obtained this session | Y — opened directly, quoted (subagent) |

---

## 2. Verified deep-dive: United Kingdom (pilot country #1)

**Primary source:** UK NAEI (naei.energysecurity.gov.uk), which independently hosts the exact
files submitted to UNFCCC (this bypassed the unfccc.int block entirely). Downloaded:
- `NID_90-24.pdf` (main National Inventory Document, 9.9 MB) and `NID_90-24_Annex.pdf` (16.3 MB) — both "UK NID 2026 (Issue 1)", covering inventory years 1990–2024, submission dated 30 April 2026 / 12 March 2026.
- `UK_2026_UNFCCC_CRT_Output.zip` (47.4 MB) — 35 per-year CRT workbooks (`GBRJ-CRT-2026-V1.0-<year>.xlsx`), one per inventory year 1990–2024. Extracted only the 2024 file (4.66 MB) and deleted the zip immediately after.

**CRT structure (this is the actual machine-readable MMS table the user asked about):**
Sheet `Table3.B(a)` ("CH4 Emissions from Manure Management") and `Table3.B(b)` ("N2O Emissions
from Manure Management") both carry a "Manure Management Systems" block with one column per
system: Anaerobic lagoon, Liquid system, Daily spread, Solid storage, Pit storage, Dry lot, Deep
bedding, Pasture/range/paddock, Composting, **Digesters**, Burned for fuel/waste, Other. Table
3.B(b) additionally gives the **absolute nitrogen excretion** (kg N/yr) handled by each MMS per
livestock category — this is the basis: **% of N excreted, per IPCC Table 3.B(b) methodology**
(confirmed identical percentages appear in both the CH4 table's % column and are computable
directly from the N2O table's absolute kg-N figures). **The UK's "Total N excreted" denominator
(column 17, used throughout) includes pasture/range/paddock-deposited N** — i.e. it is total N
excreted, not just N handled in managed storage systems (see Section 9 for why this matters when
comparing to Italy's figures, which report both bases separately).

**UK 2024 inventory year, % of manure N managed via "Digesters", by livestock category (verified,
computed directly from `Table3.B(b)`, cross-checked against `Table3.B(a)`'s own % column):**

| Livestock category | Total N excreted (kg N/yr) | N to Digesters (kg N/yr) | % to Digesters |
|---|---:|---:|---:|
| Dairy cattle | 217,324,142 | 5,956,581 | **2.74%** |
| Non-dairy cattle | 329,941,224 | 6,219,048 | **1.88%** |
| Swine | 43,701,795 | 3,094,227 | **7.08%** |
| Poultry | 86,618,700 | 17,659,420 | **20.39%** |
| Sheep, deer, goats, horses | (population) | — | **0% — "Digesters" column is blank/NO for these categories in the UK table** |

(Note: earlier in this session I mis-mapped the sheet's two side-by-side tables — an internal
"Additional information" block sharing rows with the main CRT category rows — and initially
reported Swine = 1.88%; that number is actually **Non-dairy cattle**. Swine's own figure, 7.08%,
only appears in the `Table3.B(b)` N2O table's absolute-N columns, not in the `Table3.B(a)` CH4
table's disaggregated "Additional information" block, which omits swine entirely. This
cross-table reconciliation requirement is itself a scalability caveat — see Section 10.)

**Methodological quotes (verbatim, from `NID_90-24_Main.pdf` / `NID_90-24_Annex.pdf`, both "UK
NID 2026 (Issue 1)"):**
- "Quantities of livestock manure being used in anaerobic digestion (Table 5-7) are estimated
  from data provided by the National Non-Food Crops Centre (https://www.nnfcc.co.uk/) annual
  deployment report, a database listing operational, under-construction and proposed anaerobic
  digestion plants in the UK... Manure as a feedstock is further categorised as cattle, pig,
  poultry, equine and miscellaneous animal." (Annex, p.907 — text following the "Page 906" footer)
- "For inventory calculations, the categories of equine and miscellaneous animal... are summed
  and reallocated to cattle, pig and poultry based on the relative proportions of total manure
  (leaving housing) for those livestock types... the same proportions are applied to manure
  quantity going to anaerobic digestion as are applied to that sector as a whole." (Annex, p.907)
- Table3.B(b) documentation box: "Estimates of N excretion for each MMS are estimated to match
  the CRT reporting approach of grouping housing and storage as 'manure management' which
  doesn't fit well with the N flow approach used in the UK inventory. N excreted to each MMS has
  been estimated based on the initial total N excreted to grazing and housing systems adjusted
  by the N allocated to 'daily spread' and 'digesters', which are introduced as management
  options at the storage phase."
- Country-specific methane conversion factors for AD are explicitly borrowed from Germany:
  "Country-specific MCF values are used for the anaerobic digestion of livestock manures based
  on the values used in the German inventory." (Main text, p.368 — text following the "Page 367"
  footer) — MCF-cattle=3%, MCF-pigs=4%, MCF-poultry=1.5% (Table A5.1.9).

**Critical caveat (methodological circularity):** the UK's manure-to-AD activity data is **not an
independent measurement** — it is derived entirely from the NNFCC "Anaerobic Digestion
Deployment in the United Kingdom" annual database (the same licence-restricted plant-level
dataset already flagged in `docs/ad_research/scoping_uk.md` as unusable for redistribution
without NNFCC's permission). So the UK's CRT "Digesters" % is a transform of NNFCC's own
feedstock tonnage figures, not a ground-truth national census. A rough consistency check: NNFCC
reported (per `scoping_uk.md`) 2.71 Mt/yr manure & slurry fed to UK AD plants (March 2024); this
is broadly consistent in order of magnitude with the N-excretion-weighted figures above, but an
exact reconciliation was not attempted (different bases: mass vs. N; different vintages, Mar
2024 database vs. 2024 inventory year).

**Table "5-7" referenced in the Annex text (the actual national manure tonnage table) was not
located under that exact number in this edition of the PDF** — table numbering appears to have
drifted between report revisions. The N-excretion totals in the table above substitute as the
"national manure total" the task asked for (basis: N, not mass).

**National manure-N-weighted average, 2024 (own calculation from the verified per-category
figures above, dairy+non-dairy cattle+swine+poultry only — sheep/deer/goats/horses excluded
since their "Digesters" column is blank/NO):** total N excreted across these four categories =
677,585,861 kg N/yr; N routed to Digesters = 32,929,276 kg N/yr → **4.86% of this N pool is
managed via anaerobic digestion nationally.** This is a derived figure (own arithmetic, not a
number printed anywhere in the CRT itself) and should be labelled as such downstream.

---

## 3. Denmark (pilot country #2) — verified via delegated subagent

**Primary source:** DCE, Aarhus University — "Danish Emission Inventories for Agriculture —
Inventories 1985-2023," Scientific Report No. 696 (Albrektsen & Mikkelsen, 2026), published Feb
2026. `https://dce.au.dk/fileadmin/dce.au.dk/Udgivelser/Videnskabelige_rapporter_600-699/SR696.pdf`
(6.3 MB, HEAD-confirmed, downloaded, quoted, then deleted per data-retention practice). This is
DCE's own detailed sectoral background report underlying Denmark's NIR/NID; its activity data run
to **inventory year 2023** (one year behind the 2026 NID's 1990–2024 headline coverage — flagged,
not glossed over). No CRT Table 3.B(a)-equivalent spreadsheet was found mirrored on `dce.au.dk`
itself (unlike the UK's NAEI, DCE appears to publish only PDF narrative/report content).

**Verified, quoted directly (Section 11.2.5 "Biogas treatment of slurry," p.110–111):**
> "In 2023, around 36 % of total amount of slurry is delivered to biogas production, 46 % of the
> total amount of cattle slurry and 26 % for swine slurry."

Table 11.17 ("Biogas production, 1990-2023") gives the full time series of "% of total produced
slurry" digested: 1990=1%, 1995=2%, 2000=4%, 2005=6%, 2010=6%, 2015=7%, 2020=21%, 2021=25%,
2022=27%, **2023=36%**.

| Livestock category | % of slurry to biogas, 2023 | Basis |
|---|---:|---|
| Cattle slurry | **46%** | Mass (kt slurry) |
| Swine slurry | **26%** | Mass (kt slurry) |
| All slurry (cattle+swine+mixed) | **36%** | Mass (kt slurry) |
| Poultry | **not applicable — no "Biogas" MMS pathway exists for poultry** in Denmark's barn-type-to-MMS mapping (Annex G) | — |
| Solid manure/deep litter (all species) | **0% — no "Biogas" pathway exists for solid manure at all** in the DCE mapping; solid manure was 11% of total manure in 2023 (down from 24% in 1985), so this share never enters the AD-share denominator | — |

**Basis is explicitly MASS** ("Percent of total produced slurry"), a genuinely different basis
from the UK's %-of-N-excreted CRT figures — **do not average these across countries without
flagging the basis difference.**

**Reconciliation with prior secondary press claims** (see `docs/ad_research/scoping_dk_nl.md`
§1.4): the verified 36% (2023, mass basis, slurry only) is close to the previously-flagged
UNVERIFIED "~35% as of June 2024" (LandbrugsAvisen) figure — plausibly the same underlying
statistic, now primary-confirmed in direction and magnitude, though the press piece itself was
never traced to this exact DCE table. This is **not** the same metric as the already-verified
"manure = ~75-77% of feedstock mix at existing biogas plants" (Energistyrelsen) — that is a
plant-feedstock-mix share, not a share of national manure production, and the two must not be
conflated (a mistake made in casual public discussion of Danish biogas statistics).

**Scalability note from this pilot:** getting Denmark's number required a full PDF
download+text-extraction+targeted-read pass (~30 min of subagent time) and yielded a coarser,
mass-basis, cattle/swine-only (no dairy-vs-beef, no poultry) breakdown — a genuinely different
shape of answer than the UK's ready-made, finely disaggregated, N-basis CRT spreadsheet. Expect
this narrative-PDF-digging pattern, not spreadsheet-parsing, to be the norm for most of the
remaining ~27 countries.

---

## 4. EU aggregate NID — does NOT solve this in one step (verified negative finding)

Checked directly: EEA's "Annual European Union greenhouse gas inventory 1990-2024 and inventory
document 2026" (`eea.europa.eu`, 47.4 MB PDF, downloaded, full-text searched, then deleted).
**Chapter 5 (Agriculture) gives country-by-country tables of CH4/N2O *emissions* by source
category** (e.g. Table 5.9 "3.B.3 – Swine: Countries' contributions to total EU-GHG and CH4
emissions", Table 5.12 similarly for N2O) — useful for cross-country emissions comparison, but
**these are emissions totals in kt CO2-eq, not manure-management-system allocation percentages.**
No "Digesters"/anaerobic-digester mention appears anywhere in the agriculture chapter of this
document (the only two "anaerobic digestion" mentions in the whole 47 MB PDF are in the Waste
sector, category 5.B.2, unrelated to manure management). **The EU aggregate document does not
contain the cross-country MMS table hoped for — each Party's own CRT/NIR must be opened
individually.**

---

## 5. France (pilot country #3) — verified via delegated subagent

**Primary source:** CITEPA's **OMINEA report** ("Organisation et Méthodes des Inventaires
Nationaux des Émissions Atmosphériques"), édition 2026 (23rd edition), published 30 Apr 2026,
the official methodology report underlying France's NID/CRT — this **is** the primary-source
basis for CRT Table 3.B, explicitly cross-referenced in the document itself ("CCNUCC / CRT 3B",
p.78). Downloaded as `OMINEA_2026_v1-1.zip` (42.4 MB, HEAD-checked), extracted only the
"3. Agriculture.pdf" chapter (5.1 MB), deleted everything after extracting the numbers below.
CITEPA's own CRT xlsx download links exist but are JS-rendered placeholders and were not
retrievable by direct fetch — flagged as a scalability friction point, not attempted further.

**Basis of the %: neither straightforwardly %N, %VS, nor %mass** — CITEPA derives it as a share
of a **"theoretical herd" (head-count equivalent)**: methanised manure tonnage is divided by
manure N-content, then by per-head N excretion, to back out an equivalent number of animal
places whose manure is treated as "entirely digested," which are then reallocated out of the
classical MMS categories. Verbatim (p.30–31): *"La méthode consiste à estimer un cheptel
(théorique) dont les déjections seraient entièrement dirigées vers la méthanisation."*

**Inventory year 2024 (submission 2026), from Tableau 13 (cattle, p.33) and Tableau 14 (pigs,
p.35), "périmètre UE," columns "Méthanisation liquide" + "Méthanisation solide":**

| Livestock category | Liquid digestion | Solid digestion | Total to AD |
|---|---:|---:|---:|
| Dairy cattle (vaches laitières) | 2.4% | 2.3% | **4.7%** |
| Other cattle (autres bovins) | 0.5% | 2.5% | **3.0%** |
| Breeding sows (truies) | 9.5% | 0.4% | **9.9%** |
| Other pigs (autres porcins) | 9.8% | 0.3% | **10.1%** |

Figure 18 (p.36) gives approximate 2024 values for all species read directly off a chart (no
underlying data table, so these are chart-reading estimates, not exact): poultry (volailles)
~5.2%, sheep (ovins) ~0.7%, goats (caprins) ~3.5%, horses (equins) ~1.8%, rabbits (lapins)
~11.5% — all near 0% as recently as 2010. **AD allocation is not restricted to cattle/pigs in
France's actual MMS allocation**, unlike a separate, narrower restriction elsewhere in the same
report (p.81, Table 39: a CH4-reduction factor of 2.27% restricted to "cheptels bovins et
porcins uniquement") — these are two different things and should not be conflated.

**National manure total:** no national manure-production or N-excretion denominator was found in
this chapter; the closest available figure is a feedstock **numerator** only: *"En 2023 on
dénombre ainsi 1412 méthaniseurs agricoles en activité valorisant 20,8 millions de tonnes de
matière brute à 49% constituée d'effluents d'élevage"* (p.30) → ≈10.2 Mt raw-mass livestock
effluent digested nationally in 2023. No national manure-production total was located, so no
independently-computed weighted share is possible from this chapter alone (the % figures in the
table above are CITEPA's own allocation fractions, not something we derived).

**Scalability note:** moderate-hard. No French CRT mirror as clean as the UK's per-year xlsx
zip; required finding the OMINEA methodology PDF, locating the right tables by keyword search,
and reading percentages off both a data table (cattle/pigs) and a chart with no table (other
species — approximate only). Roughly 2–3x the UK's effort, and precision for non-cattle/pig
species is limited to chart-reading.

---

## 6. Italy (pilot country #4) — verified via delegated subagent

**Primary sources (both ISPRA-hosted, unfccc.int never touched):**
- CRT spreadsheet zip: `emissioni.sina.isprambiente.it/wp-content/uploads/2026/04/Emissioni-GHG-CRT-2026.zip` (38.16 MB; HEAD was blocked by the site's WAF but a ranged GET returned the size). One `.xlsx` per inventory year 1990–2024; file used: `ITA-CRT-2026-V0.1-2024-...xlsx` (591 KB), sheets `Table3.B(a)` and `Table3.B(b)` — same template/naming as the UK's, confirming the cross-Party structural consistency predicted in Section 0.
- NID 2026, "Italian Greenhouse Gas Inventory 1990-2024": `isprambiente.gov.it` (12.96 MB PDF, 533pp, English text, submission year 2026).

**Basis confirmed as nitrogen (N)**, quoted directly from the NID (p.225, "Direct N2O emissions
from manure management"): *"As regards the anaerobic digesters, another management system used
in the country, the nitrogen quantities in livestock manure sent to anaerobic digestion were
calculated. Based on CRPA data (CRPA, 2018; CRPA, 2006[a]) on manure production and the amount
of N excreted by animal category and type of housing, the coefficients expressed in g N/kg
manure were calculated... N2O emissions of anaerobic digesters are reported as 0.0006 kg
N2O-N (kg nitrogen excreted)⁻¹."*

**Inventory year 2024, from `Table3.B(b)` (Digesters kg N/yr ÷ Total N excreted kg N/yr):**

| Livestock category | % to Digesters |
|---|---:|
| Dairy cattle | **20.94%** |
| Non-dairy cattle | **20.43%** |
| All cattle (combined) | **20.68%** |
| Swine | **3.02%** |
| Poultry | **18.00%** |
| Sheep, buffalo, goats, horses, mules, rabbit, ostrich, fur-bearing | **"NA" (0) — no digester allocation reported for these species** |

**National weighted figures (subagent's own arithmetic, both bases quoted so they aren't
conflated):** total N "handled per MMS" (managed systems only, excludes pasture-deposited N) =
542,921,842.8 kg N/yr, of which 91,320,759.1 kg N/yr → Digesters → **16.82% of N in managed
systems**. Against total N excreted nationally including pasture (695,351,588.8 kg N/yr) →
**13.13%**. These are two different, valid denominators — flag which one is used wherever this
figure is cited.

**Important internal caveat flagged by the subagent:** `Table3.B(a)` (the % allocation table,
by climate region) appears to use a blanket "Option A" allocation for aggregated groups (e.g.
"Cattle", "Other livestock") rather than genuine per-species disaggregation, and shows "NA" for
several species that clearly have nonzero AD allocation in `Table3.B(b)`. **`Table3.B(b)`'s
absolute kg-N figures are the reliable extraction path for Italy — the same lesson as the UK's
own cross-table reconciliation problem in Section 2.**

**Separate mass-basis figure, NOT the same metric — do not conflate:** NID text (~p.220):
*"...the percentages of the different substrates feeding the anaerobic digesters and data on
the average content of volatile solids by type of substrates have been changed resulting in a
decrease of the estimated amount of manure feeding anaerobic digesters. For the year 2024 this
amount is equal to about 17 million tons and that is 46% of the total amount of feed treated in
anaerobic digesters."* This 46% is manure's share of AD-plant feedstock (the other 54% being
energy crops/agro-industrial residues) — the same "feedstock-mix" metric already flagged for
Denmark and the UK as distinct from "share of national manure production digested." No national
total-manure-production tonnage was found to pair with the 17 Mt AD-manure figure.

**Secondary press figure, UNVERIFIED:** trade press (assosuini.it, carnisostenibili.it,
summarising an ISPRA report, not independently confirmed against a primary ISPRA sentence) cites
"~16% of total annual cattle/pig/poultry manure production" digested (2021, TERNA data). This is
close to, but not confirmed to be, the same metric as the 16.82% N-handled figure computed above
— the coincidence should not be treated as corroboration.

**Scalability note:** moderate-to-hard. ISPRA mirrors the CRT as a per-year xlsx zip like the
UK's NAEI (avoiding the UNFCCC block) and the template is in English — but the %-allocation
table (`3.B(a)`) is error-prone to parse automatically due to blanket Option-A allocation and
missing per-species rows; `Table3.B(b)`'s absolute kg N/yr figures are far easier and should be
the standard extraction target across countries where available.

---

## 7. Netherlands (pilot country #5) — verified via delegated subagent

**Primary source:** not CBS StatLine (confirmed negative again — table 83981NED also has no
digestion breakdown) but the RIVM/WUR **NEMA** ("Nationaal Emissiemodel voor Ammoniak")
agricultural-emissions model report series, the actual compiler feeding the Dutch CRT/NIR:
- van der Most, C. & van Bruggen, C. et al. (2025), *"Emissies naar lucht uit de landbouw
  berekend met NEMA voor 1990-2023,"* WOt-technical report 283, Wageningen
  (`edepot.wur.nl/699440`, 6.5 MB, downloaded/extracted/deleted per data-retention rule).
- van der Zee, T.C. et al. (2026), RIVM report 2026-0020, *"Methodology for the calculation of
  emissions from agriculture"* (`rivm.nl/bibliotheek/rapporten/2026-0020.pdf`, 3.3 MB).

Both hosted on `rivm.nl`/`edepot.wur.nl`, avoiding the unfccc.int block entirely. **Latest
inventory year with full result tables: 2023** (a newer "NEMA 1990-2024" edition is referenced
by title elsewhere but its PDF was not located within budget — flagged as a follow-up, not
fabricated).

**Basis: reported in BOTH N and VS/organic-matter (OS) terms, never as a pre-computed % and
never as fresh-weight tonnes.** The underlying allocation key is actually **P2O5 (phosphate)**
ratios at the farm level, applied separately to the N and VS streams — quoted: *"Ingaande OS
naar vergisting = OS-excretie in de stal x (P2O5 naar covergisting / P2O5-excretie in de
stal)."* This is a fourth distinct basis-methodology among the five pilot countries (UK/Italy:
N-fraction from NNFCC/CRPA activity data; Denmark: mass; France: theoretical-herd/head-count;
Netherlands: P2O5-derived allocation applied to N and VS).

**Key verified figures, inventory year 2023:**
- **National total livestock N-excretion (excl. hobby animals), 2023:** *"De N-excretie van de
  totale veestapel (excl. hobbydieren) daalde in 2023 ten opzichte van 2022 met 3,6 miljoen kg
  tot 463,5 miljoen kg N."* → **463.5 million kg N** (national denominator).
- **Table B15.1 "N-supply per manure treatment technique," row group "Mestvergisting" (manure
  digestion), 2023:** dairy cow slurry 5.070 Mkg N; young stock slurry 0.919 Mkg N; fattening
  pig slurry 7.069 Mkg N; breeding pig slurry 3.623 Mkg N → **sum = 16.68 million kg N to
  digestion.** Only cattle and pig manure are modelled as eligible for digestion at all in NEMA
  — **poultry manure is structurally excluded, routed only to drying/pelleting/incineration.**
- **Table B31.1, VS/OS basis, same four categories, 2023:** 89.0 + 14.8 + 117.8 + 58.0 =
  **279.6 million kg OS (volatile solids) to digestion.**

**Own arithmetic (subagent's, flagged as such, not a NEMA-stated %):** 16.68 / 463.5 = **3.6% of
all livestock N-excretion nationally** — but this denominator includes poultry/sheep/veal calves
that are structurally ineligible for digestion in this model, so restricting to only the four
eligible cattle/pig categories would give a noticeably higher %, plausibly nearer the
previously-flagged UNVERIFIED "~5% in 2022" press figure — **this reconciliation is incomplete
(the category-specific N-excretion denominators for just dairy/young-stock/fattening-pig/
breeding-pig were not pulled), so the 5% figure is neither confirmed nor debunked, only bounded
as plausible.**

**Scalability note:** moderate-hard. Unlike the UK's/Italy's clean per-year CRT-mirror xlsx with
a ready "Digesters %" column, the Dutch data required locating the right report out of a long
annual series (methodology report ≠ results report ≠ CRT itself), extracting two separate
absolute-mass tables (N and VS) buried in numbered annexes with no MMS metadata, and manually
computing any percentage — there is no single number to lift. Budget materially more time per
country where the national compiler isn't a "one file per year" register like the UK's/Italy's.

---

## 8. Germany (pilot country #6) — verified via delegated subagent

**Top finding: Germany's methodology does NOT report AD allocation as a percentage of manure at
all.** It reports an absolute national quantity of manure N sent to anaerobic digestion, by
manure category, and states that the identical share is applied to VS. There is no % figure to
lift directly — one would have to be computed from a separate national manure-N-excretion
denominator, which was not obtained this session (a well-defined, tractable follow-up: the
report gives per-animal-place excretion rates by category, which would need multiplying by
national animal-place counts, both published in the same report but in different chapters).

**Primary source (opened directly — not a PDF, a live GitLab wiki):** Germany's PDF "Thünen
Report" series (Rösemann et al.) ended after Report 91/Submission 2022; from Submission 2023
onward the Report on Methods and Data (RMD) moved to a GitLab wiki: *"Calculations of gaseous
and particulate emissions from German agriculture 1990–2024: Report on methods and data (RMD),
Submission 2026"* — Vos, Rösemann, Haenel, Dämmgen, Döring, Wulf, Eurich-Menden, Döhler, Steuer,
Osterburg, Fuß (2026), Thünen Institute.
`https://git-dmz.thuenen.de/vos/emissionsagriculture2026/-/wikis/2-Input-data/2.6-Data-on-the-digestion-of-animal-manures-and-energy-crops`
(Chapter 2.6, "Digestion of animal manures"; appending `.md` to any wiki URL returns raw text,
bypassing the site's slow client-side renderer — the access method that worked).

**Basis and methodology, quoted verbatim:** *"Table 1 shows the animal manure N of the different
manure categories that were digested after transports... The data are Gg of N entering anaerobic
digestion. The same shares were used for VS entering digestion as well."* Cattle slurry, cattle
farmyard manure, pig slurry and poultry manure are digested; *"Data for pig farmyard manure were
too unreliable due to its low occurrence"* (excluded from the model entirely).

**Verified numbers — Table 1, "Digestion of manures, animal manure N used as feedstock (Gg N)",
2024 (latest year, submission 2026; the subagent notes 2023 values appear carried forward to
2024 for cattle slurry/cattle solid manure, consistent with the report's stated practice
elsewhere of carrying forward a value when "no value is available for the last year of the time
series yet"):**

| Manure category | Gg N to digestion, 2024 |
|---|---:|
| Cattle slurry | 107.0 |
| Cattle solid manure | 8.9 |
| Pig slurry | 42.4 |
| Poultry manure | 24.7 |
| **Total** | **183.0** |
| Pig solid manure | **excluded from the model — "too unreliable due to its low occurrence"** |

Table 2 additionally gives digestate gastight-storage share, 2024: 79.8% gastight / 20.2% not —
**this is a digestate-storage metric, not a manure-to-AD share, and must not be conflated with
it.**

**UNVERIFIED press claim, now traced to its likely (still unsourced) origin:** FNR's own page
(`biogas.fnr.de/wirtschaftsduenger/wirtschaftsduengervergaerung`) states *"Nur ein Drittel dieser
Mengen wird aktuell energetisch in Biogasanlagen genutzt"* (roughly one third of ~150–190 Mt/yr
manure currently digested) **with no citation given on the page itself** — this is very likely
the source of the "~30% of German manure digested" figure that circulates in press coverage, and
it remains an unsourced secondary claim on Germany's own renewable-resources agency's page, not
a number traceable to the Thünen RMD or CRT.

**Scalability note:** hard, and the slowest of the six pilots. `thuenen.de` and `openagrar.de`
both sit behind proof-of-work bot-challenges that did not resolve in reasonable time even in a
real Chrome tab. The route that worked — a GitLab-hosted wiki, with an undocumented
"append-`.md`-for-raw-text" trick — is Germany-specific and not transferable to other countries.
Germany took a multi-hour, multi-fallback effort even using the UK method as a template, and
even then produced only a numerator (Gg N to digestion), not a ready percentage.

---

## 9. Consolidated pilot results table

| Country | Livestock category | % to AD | Basis | Inventory yr | Submission yr | Source (location) | Verified |
|---|---|---:|---|---|---|---|---|
| UK | Dairy cattle | 2.74% | % N excreted | 2024 | 2026 | NAEI CRT `Table3.B(b)`, GBRJ-CRT-2026-V1.0-2024.xlsx | Y |
| UK | Non-dairy cattle | 1.88% | % N excreted | 2024 | 2026 | ″ | Y |
| UK | Swine | 7.08% | % N excreted | 2024 | 2026 | ″ | Y |
| UK | Poultry | 20.39% | % N excreted | 2024 | 2026 | ″ | Y |
| UK | (weighted, 4 categories above) | 4.86% | % N excreted (derived) | 2024 | 2026 | own calculation from above | Y (derived) |
| Denmark | Cattle slurry | 46% | % of slurry mass | 2023 | 2026(NID)/2026(SR696) | DCE SR696, Table 11.17/§11.2.5, p.110–111 | Y |
| Denmark | Swine slurry | 26% | % of slurry mass | 2023 | ″ | ″ | Y |
| Denmark | All slurry | 36% | % of slurry mass | 2023 | ″ | ″ | Y |
| Denmark | Poultry / solid manure | 0% (no AD pathway modelled) | — | 2023 | ″ | DCE Annex G barn-type→MMS mapping | Y |
| France | Dairy cattle | 4.7% (2.4% liquid + 2.3% solid) | "theoretical herd" (head-count) | 2024 | 2026 | CITEPA OMINEA 2026, Tableau 13, p.33 | Y |
| France | Other cattle | 3.0% (0.5%+2.5%) | ″ | 2024 | 2026 | ″ | Y |
| France | Breeding sows | 9.9% (9.5%+0.4%) | ″ | 2024 | 2026 | OMINEA 2026, Tableau 14, p.35 | Y |
| France | Other pigs | 10.1% (9.8%+0.3%) | ″ | 2024 | 2026 | ″ | Y |
| France | Poultry, sheep, goats, horses, rabbits | ~5.2%/0.7%/3.5%/1.8%/11.5% | ″ | 2024 | 2026 | OMINEA 2026, Figure 18, p.36 (chart-read, approximate) | Partial (chart, not table) |
| Italy | Dairy cattle | 20.94% | % N excreted | 2024 | 2026 | ISPRA CRT `Table3.B(b)` | Y |
| Italy | Non-dairy cattle | 20.43% | % N excreted | 2024 | 2026 | ″ | Y |
| Italy | Swine | 3.02% | % N excreted | 2024 | 2026 | ″ | Y |
| Italy | Poultry | 18.00% | % N excreted | 2024 | 2026 | ″ | Y |
| Italy | Other species | 0% ("NA" in table) | — | 2024 | 2026 | ″ | Y |
| Italy | (national, managed-MMS basis, excl. pasture) | 16.82% | % N excreted (derived) | 2024 | 2026 | own calc. from `Table3.B(b)` totals | Y (derived) |
| Italy | (national, all N excreted, incl. pasture) | 13.13% | % N excreted (derived) | 2024 | 2026 | ″ | Y (derived) |
| Netherlands | Dairy cow slurry | 5.070 Mkg N (absolute) | N (absolute, not %) | 2023 | 2025 (assumed, not confirmed) | RIVM/WUR WOt-283, Table B15.1 | Y |
| Netherlands | Fattening pig slurry | 7.069 Mkg N (absolute) | N (absolute) | 2023 | ″ | ″ | Y |
| Netherlands | (national, all eligible categories) | ~3.6% of all N excreted (16.68/463.5 Mkg N) | % N excreted (derived, denominator includes ineligible species) | 2023 | 2025 (assumed t+2 cycle, not confirmed) | own calc.; NEMA WOt-283 | Y (derived, bounded) |
| Germany | Cattle slurry | 107.0 Gg N (absolute) | N (absolute, not %) | 2024 | 2026 | Thünen RMD wiki, Ch.2.6, Table 1 | Y |
| Germany | Pig slurry | 42.4 Gg N (absolute) | N (absolute) | 2024 | 2026 | ″ | Y |
| Germany | Poultry manure | 24.7 Gg N (absolute) | N (absolute) | 2024 | 2026 | ″ | Y |
| Germany | (% share) | **not computed — no national N-excretion denominator obtained this session** | — | 2024 | 2026 | — | N (open item) |

**Basis is genuinely inconsistent across all six countries** — UK and Italy: % of N excreted
(directly comparable to each other, but check the denominator: **UK's per-category % and its
4.86% weighted average use "total N excreted including pasture-deposited N"; Italy's headline
16.82% excludes pasture (managed-MMS N only) while its 13.13% figure includes pasture and is the
directly comparable one to the UK's numbers**); Denmark: % of slurry mass; France:
theoretical-herd head-count equivalent; Netherlands and Germany: absolute N (and, for NL, also
VS) quantities with no ready-made % at all. **Do not average or rank these six numbers against
each other as if they were the same metric without first converting to a common basis and a
common denominator.**

---

## 10. Scalability assessment

**What scales well:** the post-2024 CRT template itself is generated by UNFCCC's own Enhanced
Transparency Framework reporting tool, so sheet names (`Table3.B(a)`, `Table3.B(b)`) and column
structure are identical **by construction** across every Annex I Party — confirmed directly by
finding the same template in the UK's and Italy's CRT workbooks. Where a country's CRT workbook
is in hand, parsing is close to mechanical.

**What does not scale well — and this pilot shows it's the dominant cost, not an edge case:**

1. **`unfccc.int` itself is blocked in this sandbox** (Section 0) — the primary, canonical,
   single source for all ~29 countries' CRTs in one consistent place is currently unusable here.
   This should be re-tested outside this sandbox before assuming it's a hard blocker for the
   project, since it would otherwise be by far the most efficient single access point.
2. **Only 2 of 6 pilot countries (UK, Italy) mirror their own ready-made CRT workbook** on their
   national agency's site. Denmark publishes only narrative PDF reports; France's CRT xlsx links
   are JS-rendered and unreachable by direct fetch (had to fall back to the OMINEA methodology
   PDF instead); the Netherlands' compiler (RIVM/WUR NEMA) publishes only absolute-mass annex
   tables, no CRT mirror at all; Germany's underlying methodology now lives in a GitLab wiki
   behind a Germany-specific bot-challenge, with the actual CRT still only reachable via the
   blocked unfccc.int. **Effort ranged from "minutes" (UK/Italy, once the file was found) to
   "multi-hour, multi-fallback" (Germany)** — this is not a small variance and should be budgeted
   per-country, not averaged.
3. **Basis inconsistency is real and confirmed across all six countries, not hypothetical**
   (Section 9): N-excreted (UK, Italy), mass (Denmark), theoretical-herd head-count (France),
   absolute N/VS with no % at all (Netherlands, Germany). Any cross-country comparison or
   manure-weighted EU-wide aggregate must carry an explicit basis flag per country and cannot
   silently average across these.
4. **Even within one country's own CRT, extraction has traps.** The UK sheet contains two
   independently-structured sub-tables sharing row numbers (a population/allocation table and a
   disaggregated "Additional information" block) — naive column-position reading produced an
   incorrect Swine figure on first pass in this very session (Section 2 caveat). Italy's
   `Table3.B(a)` uses a blanket "Option A" allocation for aggregated groups that hides real
   per-species AD shares visible only in `Table3.B(b)`'s absolute figures. **The lesson,
   confirmed twice independently: always cross-check `Table3.B(a)`'s % against `Table3.B(b)`'s
   absolute kg-N figures, never trust either table alone.**
5. **"Hidden" AD shares are a real, now-multiply-confirmed risk**, exactly as the task
   anticipated: Denmark has no MMS pathway for AD at all for poultry or solid manure (11–24% of
   total manure, entirely invisible to this style of national share); the Netherlands' NEMA model
   structurally excludes poultry from digestion entirely (routed only to
   drying/pelleting/incineration); Germany excludes pig solid manure as "too unreliable." Any
   manure processed by a real-world poultry-litter or solid-manure co-digestion plant in these
   countries is, by construction of the national inventory model, invisible to the official
   manure-to-AD share and must be sourced (if at all) from plant-level data instead (see the
   parallel `docs/ad_research/scoping_*.md` plant-inventory work).
6. **Language and institutional fragmentation.** Five different national compilers were needed
   for five different countries (NAEI/DESNZ, DCE/Aarhus, CITEPA, ISPRA, RIVM/WUR, Thünen), in
   four languages (English, Danish, French, Italian, Dutch/German), each with its own document
   structure, numbering, and access quirks (bot-challenges, JS-rendered download links, WAFs
   blocking HEAD but not ranged GET). There is no shortcut that avoids this per-country
   discovery cost at present.

**Bottom line on scalability to ~29 countries:** feasible, but **not a uniform, quick,
spreadsheet-parsing exercise** — it is a per-country research task whose effort varies roughly
5–10x between the easiest cases (UK/Italy: ready-made CRT mirror, English-language, minutes to
hours) and the hardest (Germany: multi-hour, bot-challenge-blocked, numerator-only result).
Budget accordingly; do not assume the UK's clean result generalises.

---

## 11. Recommended extraction pipeline

1. **Per country, first try unfccc.int directly** (re-test outside this sandbox — it may not be
   blocked elsewhere) for the post-2024 CRT `.xlsx`/JSON bundle. This is the single most
   consistent format across Parties when reachable.
2. **If blocked or unavailable, search for a national-agency mirror** of the same CRT workbook
   (pattern: `<agency>.<country-tld> "Common Reporting Table" <year>` or `site:<agency-domain>
   CRT zip`) — this worked for UK (NAEI) and Italy (ISPRA) and should be tried first for every
   new country before falling back to narrative-PDF digging.
3. **Standardise on `Table3.B(b)` (N2O table, absolute kg N/yr per MMS) as the primary
   extraction target**, not `Table3.B(a)`'s % column — confirmed twice (UK, Italy) that
   `Table3.B(a)` can have structural gaps or blanket-allocation artifacts that `Table3.B(b)`'s
   absolute figures reveal and correct. Compute % as (Digesters kg N) / (Total N excreted or
   Total N handled — state which denominator).
4. **If no CRT mirror exists, fall back to the country's own NIR methodology annex/report**
   (DCE for Denmark, OMINEA for France, NEMA/RIVM for Netherlands, Thünen RMD for Germany) and
   extract the manure-management narrative section by keyword search (`anaerobic digest*`,
   `digester`, `vergisting`/`méthanisation`/`digestione anaerobica`/`Vergärung`) — expect a
   multi-hour, human-judgment-heavy task per country at this tier, not a mechanical parse.
5. **Record the basis (N/VS/mass/head-count/absolute-only) explicitly for every country** as a
   first-class field, not an afterthought — this pilot shows five different bases across six
   countries, and any downstream weighted EU average must convert to a common basis (N is
   recommended, since IPCC's own MMS methodology is fundamentally N-flow-based and it's the
   basis obtained for 3 of 6 pilot countries) or clearly present each country's own native basis
   unconverted.
6. **Always keep the small derived numbers/quotes, delete the source PDFs/spreadsheets**
   (all six pilots followed the standing rule: downloads under 50 MB, raw files deleted after
   extraction, only small text/derived files retained in scratch).
7. **Cross-check every country's extracted figure against the plant-level AD-inventory work**
   already underway in the parallel `docs/ad_research/scoping_*.md` files (UK: NNFCC feedstock
   tonnages; Denmark/Netherlands: SDE/plant registers) — the UK case shows the inventory number
   is itself often *derived from* the same plant-level database, so these are not independent
   cross-checks but the same underlying data seen through two different reporting pipelines; say
   so explicitly wherever both are cited together.

---

## 12. Caveats (consolidated)

1. **Basis inconsistency (Section 9/10)** — N (UK, Italy) vs. mass (Denmark) vs. theoretical-herd
   head-count (France) vs. absolute-only, no % (Netherlands, Germany). The single biggest risk to
   a naive cross-country comparison.
2. **"NO"/"IE"/"NA"/blank notation keys differ by country and table** — the UK uses "NO" (not
   occurring) for categories with zero AD allocation; Italy uses "NA"; France and Germany have no
   equivalent explicit non-occurrence flag in the sources checked (absence just means the
   pathway isn't modelled at all for that species). Any pipeline must handle all of these as
   equivalent to zero, not as missing data.
3. **Structurally invisible AD manure** — confirmed for poultry and/or solid manure in Denmark,
   Netherlands, and (pig solid manure) Germany. National MMS-share figures for these
   country/species combinations will always read as 0%, even where real co-digestion of these
   materials occurs, because the national model doesn't have an AD pathway defined for them at
   all. This is not a data gap that better extraction can fix — it's a structural feature of how
   these countries build their inventories.
4. **Feedstock-mix share vs. manure-production share — a real, repeated conflation risk.** Denmark
   (manure ≈75–77% of biogas-plant feedstock mix), Italy (46% of AD-feedstock is manure), and the
   UK's NNFCC data (manure ≈15% of AD feedstock by tonnage, per `scoping_uk.md`) are all
   "feedstock-mix" numbers — the reverse fraction from "% of national manure production that goes
   to AD." These have been confused in public discussion of Danish and Dutch biogas statistics
   already, per the prior scoping sessions, and must be kept clearly separated in any
   user-facing copy.
5. **Energy-crop and non-manure co-digestion inputs are entirely out of scope of this
   manure-share figure** — none of the six countries' manure-to-AD % includes or nets out
   co-digested energy crops, food waste, or industrial residues; the % is specifically the share
   of *manure* (by whichever basis) sent to AD, not the composition of what AD plants process.
6. **Methodological circularity in at least one country (UK), and likely more.** The UK's
   inventory activity data for manure-to-AD is itself derived from the NNFCC plant-level
   database (the same licence-restricted dataset flagged in `scoping_uk.md`) — meaning the
   "primary" inventory figure and a plant-level cross-check are not actually independent
   evidence for the UK. This should be checked for each additional country before treating an
   inventory figure as ground truth independent of plant-level data.
7. **Vintage/lag mismatches.** Not every country's manure-management data is as current as its
   headline NID: Denmark's detailed manure/biogas tables (SR696) run to inventory year 2023 even
   though the 2026 NID headline covers through 2024; France's 2024 digester-count input for some
   species was carried forward unchanged from 2023 SINOE data; Germany's 2024 cattle-slurry/
   solid-manure figures also appear carried forward from 2023. Always state both the inventory
   year *of the specific table cited* and the submission year, since they can differ within the
   same document.
8. **EU aggregate document is not a shortcut** (Section 4, verified negative finding) — the EU's
   own NID gives only cross-country emissions totals by source category, never MMS allocation
   percentages; every country must be opened individually.
9. **`unfccc.int` access is unresolved, not conclusively blocked everywhere** (Section 0/10) —
   this session's finding is sandbox-specific; re-test before designing a pipeline around
   national-agency mirrors as a permanent necessity, since a working direct UNFCCC route would
   be materially more efficient and consistent than the five-different-national-agencies pattern
   found here.
10. **Several of the figures above are derived arithmetic, not numbers printed verbatim in any
    source** (UK's 4.86% weighted average, computed directly in this session; Italy's
    16.82%/13.13% and Netherlands' 3.6%, computed by the respective delegated subagents) — these
    are clearly labelled as such in Sections 2/6/7/9 and should carry that same label wherever
    they are reused downstream.
