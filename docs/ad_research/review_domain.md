# Domain review: EU/UK AD plant inventory plan (PLAN.md, draft 2026-09-25)

Reviewer role: AD / biogas / biomethane and CDR-accounting domain expert. Scope: the plan, the six
scoping reports, and how `scripts/engine_core.py`, `docs/METHODOLOGY.md` and
`docs/RECOMMENDATION_LOGIC.md` use AD. Nothing was edited except this file.

Evidence labels: **[file]** = read in this repo; **[primary]** = primary source opened this
session and quoted; **[search]** = search-result text or secondary summary, not verified against
the primary; **[domain]** = reviewer's own domain knowledge, not verified this session;
**[calc]** = my arithmetic from stated inputs. Anything marked [search] or [domain] is UNVERIFIED
for citation purposes.

---

## (a) Top 5 issues, ranked by impact

### 1. The pathway this inventory gates is RNG+CCS, and the written Frontier position on RNG+CCS conflicts with the tool

Three sources say three different things:

- **Frontier POV (docx) §3.4 [file]**, heading: "BiCRS projects involving RNG: a complex topic we're
  not pursuing right now", and: "We are working on a more detailed perspective on this, but are not
  pursuing biogas/RNG projects at this time (late 2024)." Its pathway table defines "RNG + CCS" as
  material "converted to biogas in an anaerobic digester (AD) and upgraded to RNG, with CO2 being
  captured", and lists Future Biogas as an example.
- **Engine [file]** `engine_core.py` ~L1064: "(RNG+CCS / AD+CCS is no longer flagged as excluded --
  Frontier is open to it as an offtake option ...)". `PATHWAYS["ad_ccs"]` has
  `co_product: "low-C fuel"`, and its cons say "Carbon is split between the RNG (fuel) and CDR
  streams". METHODOLOGY §Frontier exclusions: "RNG + CCS / AD + CCS — *no longer excluded.*"
- **The brief for this review** says RNG+CCS is "flagged/excluded in the current tool's pathway
  list". The code says the opposite.

Inside the tool the taxonomy is self-consistent: `ad_ccs` is RNG+CCS, meaning capture of the
upgrading vent CO₂ while the biomethane is sold. PLAN §5's option of "CHP flue capture (all
carbon)" is **not a pathway in the engine at all**. So the plan's framing only holds if the
inventory's gating quantity is the upgrading-stream CO₂. The larger problem is governance. The
entire AD gate and the `ad_maturity` switch exist to recommend a pathway that the only written
Frontier POV in the repo says Frontier is not buying.

**Fix:** before Phase A, get the user to confirm in writing which position is current: the
late-2024 POV, or the later "open to it as an offtake option" note, whose source the repo does not
record. Then record the decision and its source in METHODOLOGY. If RNG+CCS is still off the table,
the inventory is still worth building. Its job then becomes a *digestate / competing-feedstock*
layer, telling you where manure is already committed to AD and so cannot go to injection. It would
no longer be a gate that turns on a recommendation.

### 2. `ad_ccs` CDR efficiency (0.37) is applied to feedstock carbon, but it only makes physical sense on biogas carbon, so manure AD+CCS CDR is overstated about 2×

- `cdr_potential_mtpa` [file, L715–716]: for `manure_wet`, CDR = (manure + wwtp ODT) × 1.47 ×
  `eff`, which gives 0.37 of **total feedstock carbon**.
- The POV table [file] gives AD+CCS "(traditional)" "~30%, if there's no leakage of intentionally
  produced methane" and AD+CCS "(fuel cell)" "~44% (from Reverion)". 0.37 is the midpoint of two
  sub-pathways with *different CO₂ streams*: the traditional one captures only the upgrading vent,
  while the fuel cell captures essentially all biogas carbon. So it corresponds to neither.
- Physics [calc, KTBL cattle slurry values from search text: 8% DM, 80% oDM, 380 Nm³ biogas/t oDM
  = 24.3 Nm³/t FM, 55% CH₄]: biogas carbon ≈ 41% of slurry feed carbon (on the engine's own
  0.40 tC/t DM, i.e. 1.47 tCO₂/ODT). The upgrading-vent CO₂ is ≈ **18%** of feed carbon. For maize
  silage (30% DM, 590 Nm³/t oDM) the figures are ≈ 67% and ≈ 32%. A 0.37 multiplier on feedstock
  carbon is therefore reachable only for highly degradable feedstocks with full-carbon capture.
  For manure RNG+CCS it overstates the achievable removal by ~2× before any methane-leakage
  deduction.
- Denominator check [file]: `scripts/eu/build_nuts_feedstocks.py` uses ENSPRESO `MINBIOGAS1` (PJ)
  only as *spatial weights* ("Units cancel — only relative shares matter"). Country totals come
  from the global tool's manure stream, documented in METHODOLOGY as "FAO livestock heads ×
  excretion/dry-matter factors ... Dry-matter basis." So `animal_manure_odt_mt` is manure dry
  matter, not a biogas-energy equivalent, and the ~2× conclusion stands. (Residual uncertainty: I
  did not re-derive the global tool's DM factors.)
- Precedent in the same engine: the landfill pathways are already **bounded by the facility's gas**
  (`_lfg_co2_mtpa` × eff, L706–707), and `lfg_ccs` / `lfg_rng_ccs` are already split (0.52 / 0.33).

**Fix:** (i) Split `ad_ccs` into `ad_rng_ccs` (upgrading vent) and `ad_chp_ccs` / `ad_sofc_ccs`
(all biogas carbon), mirroring the LFG pair. (ii) Compute `ad_*` CDR from the inventory's physical
CO₂, the way LFG is computed: CDR = eligible upgrading CO₂ in reach × capture fraction (~0.9–0.95)
− CH₄-leakage debit. Do not compute it from ODT × 0.37. (iii) Leakage matters. Each 1% of produced
CH₄ lost (digester, digestate storage, upgrader slip) costs ≈ **12%** of the captured upgrading CO₂
[calc: 55/45 biogas, GWP100 non-fossil CH₄ = 27, IPCC AR6 WG1 Table 7.15; [domain] value, check
before citing]. The POV's own caveat "if there's no leakage" makes this decision-relevant. This is
a latent engine bug, flagged per instructions and not part of the plan itself, but the plan should
not wire new data into a formula that overstates by ~2×.

### 3. CHP-only plants have no capture-ready stream; `output` matters more than `ad_class`

Most of the European fleet is CHP. That covers roughly 9,315 of 9,605 German plants [file,
scoping_de, Fachverband Biogas 2025] and 496 of 630 UK plants CHP-only [file, scoping_uk, NNFCC].
For an RNG+CCS retrofit, a CHP plant needs an upgrader, a gas-grid (or bio-LNG) outlet and then
CO₂ liquefaction. That is a conversion project, not a capture retrofit. Post-combustion capture on
a 0.5 MWe engine exhaust (~5–8 vol% CO₂ [domain]) is a different and much costlier problem, and it
is not in the taxonomy. Summing CHP plants' "biogenic CO₂" into `AD_MIN_CAP_MTPA` therefore
overstates capture-ready capacity almost everywhere outside DK, NL, FR and IT biomethane.

**Fix:** gate on `co2_upgrading_t_yr` from plants with `output ∈ {upgrading, both}`. Carry CHP
plants as `conversion_candidate` with a hypothetical upgrading CO₂, reported but not
gate-enabling. The capture-readiness of the vent also depends on upgrading technology. Amine
scrubbing gives near-pure CO₂. Membranes give high-purity CO₂ with some CH₄. Water scrubbers that
air-strip give an air-diluted offgas [search: BioCycle / ScienceDirect summaries; the dilution
level is [domain], UNVERIFIED]. Add `upgrading_tech` where registries carry it (FR `procede`,
MaStR `EinheitenGasErzeuger.Technologie`).

### 4. Capacity factor 0.85 on installed kWe overstates German biogas and CO₂ by ~1.7×

Fachverband Biogas 2025 [file, scoping_de]: **6,816 MWel installed vs 3,316 MWel
Bemessungsleistung** ("overbuild factor ≈2.1×"), and 29 TWhel gross. That is 29,000 GWh ÷ 6,816 MW
= **4,255 full-load hours, CF 0.49 on installed** [calc]. German flexibilised plants have
deliberately oversized engines. PLAN §5 (η 0.38, CF 0.85 on `cap_kwe`) would put German biogas at
~1.7× reality. The same over-installation exists in Italy and Austria to a lesser degree [domain].

**Fix:** use the rated/average capacity where the register has it (MaStR EEG
`Hoechstbemessungsleistung` or equivalent [domain field name, verify in Katalog]). Otherwise use
**country-specific full-load hours** computed from national generation ÷ installed capacity
(DE: FvB 29 TWh / 6,816 MW; IT: Terna 2024 GWh / 1,473 MWe; UK: DUKES 6.4 AD row). Use CF
0.90–0.95 only for biomethane upgraders. Validate the German total as below (issue 5).

### 5. Energy-crop exclusion must be on a methane/energy basis, not a mass basis. Germany's eligible share is ~25%, not ~50%

DBFZ Report 50 [file, scoping_de]: "mass-based ≈45% animal excrement (manure), 49% NawaRo, 3%
municipal biowaste, 3% industrial/commercial/agricultural residues; energy-based the manure share
drops to ≈18% ..., NawaRo rising to ≈73%". My yield table (section c) reproduces this independently
[calc: 45×20 : 49×95 : 6×70 Nm³ CH₄ ⇒ 15% / 78% / 7%].

A concrete validation anchor [calc]: 80.6 TWh total German biogas + biomethane (FvB) ⇒ ~8.1 bn Nm³
CH₄ ⇒ **13–15 Mt CO₂/yr in the upgrading stream** (52–55% CH₄) and ~29–31 Mt if all biogas carbon
is counted. **Eligible (non-crop) upgrading-basis CO₂ is ≈ 3.5–4 Mt/yr**, and most of it currently
has no capture-ready stream (issue 3). The hand-placed German clusters in
`data/processed/facilities_ad.json` sum to **8.3 Mt** [file], a number that matches no physical
basis. The rewire will move German gate totals by large factors, so the before/after diff needs
to explain that.

**Fix:** eligible CO₂ = total × Σ_eligible(mᵢ·yᵢ) / Σ_all(mᵢ·yᵢ), with yᵢ = methane yield per t FM.
Ask the user whether Frontier would treat a mixed plant *pro rata*, or needs a plant-level
threshold (e.g. ≥ X% of methane from wastes/residues). Provide both. Section b(3) has the detail.

---

## (b) Answers to the 8 focus areas

### 1. What is the CDR in AD+CCS, and which stream to quantify?

- **Engine definition [file]:** `ad_ccs` = AD + upgrading to RNG + capture of the separated CO₂;
  co-product low-C fuel; eff 0.37 (see issue 2 for why 0.37 is mis-based). It *is* RNG+CCS.
  "CHP flue capture" is not an engine pathway. It would be a third pathway, "biogas BECCS", with a
  very different cost and scale. The fuel-cell variant (Reverion, POV ~44%) is the only all-carbon
  AD capture route Frontier's POV mentions.
- **Which stream to quantify:** the primary gating quantity is `co2_upgrading_t_yr`, the CO₂
  separated at the upgrader: ≈ 0.40–0.46 t per MWh of biogas-CH₄ electricity equivalent, or
  ≈ 1.5–1.7 kg per Nm³ biomethane [calc]. Keep `co2_total_biogenic_t_yr` as a secondary field for
  a possible `ad_sofc_ccs` pathway and for comparison with national totals. Also add a
  `co2_existing_offtake` flag. Some upgrading CO₂ is already sold to food/beverage or PtX users,
  e.g. the Tønder Biogas → Kassø e-methanol link [search: bioenergy-news.com headline]. That CO₂ is
  not available for CCS, and utilisation is not durable removal.
- **Is the plan coherent with the tool's taxonomy?** Yes on the stream, if §5 is resolved in
  favour of the upgrading CO₂. No on policy, because the pathway conflicts with the POV (issue 1).
  No on accounting, because the engine does not use the physical stream (issue 2).
- **What real projects capture:** the upgrading vent, liquefied on site and trucked. BioCirc
  Vesthimmerland is ~32,500 t CO₂/yr, liquefied and trucked to Esbjerg for Greensand/Nini West
  [search: carbonherald, worldbiomarketinsights; "first of five plants"]. Greensand started
  commercial operation in September 2026 [search: envirotecmagazine 2026-09-18]. DEA NECCS awards
  (2024-04-17): BioCirc CO2 ApS 130,700 t/yr, Bioman ApS 25,000 t/yr, Carbon Capture Scotland Ltd
  4,650 t/yr [file, scoping_dk_nl, primary press release].

### 2. Capacity → biogas → CO₂ conversion (PLAN §5), corrected

- **η_el 0.38 is fine as a central value but should depend on size.** FNR Faustzahlen [primary]
  "BHKW Wirkungsgrad el.: 28 - 47 %". Suggested defaults [domain]: <100 kWe 0.33; 100–500 kWe 0.37;
  0.5–1 MWe 0.40; >1 MWe 0.42.
- **CF 0.85 is wrong for flexibilised German plants** (issue 4). Use rated capacity or national
  full-load hours.
- **CH₄ fraction should depend on feedstock, not a flat 55%** [domain]: maize/crop-heavy 50–53%;
  manure-dominated 55–60%; food waste/biowaste 58–65%; sewage sludge 60–65%. KTBL gives 55% for
  cattle slurry [search].
- **Biomethane back-calculation:** raw biogas = product × x_CH4,product / (x_CH4,raw × (1 − slip)).
  Product 96–98% CH₄ for H-gas grids. **NL L-gas grids take lower-CH₄ biomethane (~88% CH₄-eq)**
  [domain, verify]. Upgrading CO₂ = raw × (1 − x_CH4,raw) × capture-ready fraction.
- **Unit traps.** (i) German "Rohgasaufbereitungskapazität" (FvB 309,239 Nm³/h, raw gas) and dena
  "Einspeisekapazität" (product) differ by ~1.5–2× [file, scoping_de]. (ii) French capacity in
  **GWh/an PCS (HHV)**: CH₄ HHV 11.06 vs LHV 9.97 kWh/Nm³, an 11% error if mixed [domain]. (iii) UK
  NNFCC Nm³/h is product biomethane [file].
- **Uncertainty:** low/high bounds are enough, but draw them from the distribution of per-plant
  parameters, and report the national-total check (DE ≈ 13–15 Mt upgrading basis) as the real
  constraint. A Monte Carlo adds little over a calibration to national generation.

### 3. Energy-crop eligibility, sewage sludge, biowaste, landfill gas

- **Rule:** methane-weighted share (issue 5). Mass basis badly understates crop dependence. An EEG
  "Güllekleinanlage" at 80% cattle slurry / 20% maize by mass gets **~59% of its methane from
  maize** [calc from FNR yields]. Even Denmark's **4% energy-crop cap by mass from 2025** ("Valid
  from 2025, the maximum input share of energy crops is set to 4%. The use of corn is prohibited",
  [search: ens.dk / EBA summaries]) implies ~10–15% of methane from crops under a typical DK mix
  [calc, illustrative mix].
- **Plant-level data where available:** NNFCC tonnages by feedstock (internal only); Arpae
  `TIPO_COMB` (categorical); SDE themes (Monomestvergisting ≈ manure-only); MaStR has no substrate
  field [domain]. Otherwise use country defaults: DE ≈ 25% eligible (DBFZ energy basis, manure 18%
  + residues/biowaste ~7–9%); DK ≈ 85–90%; IT crop-heavy (source: CIB/ISPRA, TBD). Sequential or
  "intermediate" crops (Italy "Biogasdoneright", RED II Annex IX intermediate crops), grass from
  permanent grassland (DE 91,456 ha in 2025 [file]) and straw/crop residues are a **grey
  category**. The POV names "anaerobically digesting crop residues that otherwise would have
  decayed aerobically" as a leakage concern [file]. Carry them as `grey`, excluded in the central
  case and included in a sensitivity run.
- **Sewage sludge:** eligible. The POV lists "human waste at wastewater treatment plants". But
  tag each sewage digester with its UWWTD id. The WWTP layer is display-only in the engine
  [file: `wwtps_eu.json`, no gate use], while biosolids enter CDR through `human_wwtp_odt_mt`.
  Sewage digesters should **not** enable the gate for manure (they do not take manure), but they
  can for the biosolids part of a `manure_wet` region. This is an attribution risk, not a
  double-count of CDR.
- **Biowaste / food waste / industrial residues:** eligible (wastes). Flag source-segregated food
  waste plants as the likely high-CH₄, high-degradability subset.
- **Landfill gas:** exclude from the AD inventory (it has its own `lfg_*` pathways, US-only today).
  Write MaStR Deponiegas, GRDF "ISDND" (26 sites) and Arpae landfill codes to a side file
  `landfill_gas_eu.json` for a future EU LFG layer. Do not drop them silently.

### 4. Classification scheme

`ad_class` is fine, but it is not what the engine's decision turns on. Ranked by decision value:

1. `output` ∈ {upgrading_grid, upgrading_bioLNG/CNG, chp, chp+upgrading, heat, satellite_chp}.
   This decides whether a capture-ready stream exists.
2. `eligible_ch4_share` (methane basis) + `eligibility_basis` ∈ {plant, class_default, country_default}.
3. `accepts_manure` (bool) and `manure_tpa`. These gate manure regions.
4. `upgrading_tech` (amine / membrane / water scrubber / PSA / cryogenic) and
   `co2_existing_offtake`.
5. `grid_connected` / distance to gas grid, needed for CHP→biomethane conversion candidates.
6. `rated_kwe` separate from `installed_kwe`; `eeg_end_year` / `tariff_end_year` (see 8).
7. `digestate_handling` (separation, drying, export). Digestate is a candidate injection feedstock
   and the POV notes injection "can use post-digestion waste" [file]. That makes AD and injection
   complementary for the same manure, which matters for focus 5.
8. `status_date` and `status_source`.

`manure_based` as a bool is too coarse. Use a threshold on `eligible_ch4_share` instead.

### 5. Manure-to-AD share as "AD maturity"

- **It measures the right concept for one question and the wrong one for another.** It tells you
  how much manure is *already committed* to AD. It does not tell you whether AD+CCS is
  capture-ready (see issue 3). The current threshold flips the *whole region* to AD+CCS once 15% of
  potential is realised, so 85% of undigested manure is sent to a pathway with ~⅕–⅖ of injection's
  CDR efficiency (the ratio depends on issue 2). Frontier's top KPI is CDR efficiency.
- **Suggested alternative: partition, don't switch.** Share s of managed manure is in AD →
  AD+CCS retrofit where upgrading exists (+ digestate injection as a complement); 1 − s →
  injection / HTL. If the engine must name one lead, AD+CCS should lead only where s ≥ 0.5 **and**
  capture-ready eligible CO₂ in reach ≥ the gate threshold.
- **Denominator:** use **managed (housed/collected) manure, excluding pasture**. Pasture-deposited
  N is available to neither AD nor injection. The plan's "% of N incl. pasture" deflates grazing
  countries (UK, IE, NL) for a reason that doesn't bear on the decision. N is conserved through
  digestion, so it works for allocation. VS is closer to biogas potential. Carry both where
  available.
- **Threshold consequence depends on the basis.** On the plan's *incl.-pasture* pilot values
  (DK 36% slurry mass, IT 13.1%, UK 4.9%, NL ~3.6%, FR 3–10%) [file], a 0.15 threshold leaves only
  DK above. IT, UK, NL and FR (currently 0.45 / 0.35 / 0.35 / 0.30) would flip to injection. On
  the **managed-manure basis I recommend**, the flips shrink. Italy is **16.8%** of N in managed
  systems [file, scoping_manure_to_ad], so it stays above 0.15. UK and NL rise by their grazing
  fractions. UK is plausibly ~8–10% if ~40–50% of N is deposited at pasture [calc on an assumed
  grazing share, UNVERIFIED], so it probably still flips. NL changes less, because more of its
  herd is housed. Recompute UK/NL/FR on the managed basis from CRT 3.B(b) before quoting a flip
  list. Either way, this is a large, visible change and must be surfaced in the before/after diff. Germany cannot
  be placed without a denominator. The DBFZ mass figure (~65 Mt FM manure in AD) against a total
  of ~150–200 Mt FM [domain, UNVERIFIED] would suggest ~30–40% on a mass basis, while the
  inventory's N basis may give much less. Reconcile the two before using either.

### 6. Gate design

- **15 km is a feedstock-procurement radius, not a capture-aggregation radius.** Farm digesters
  haul 0–5 km. Danish centralised plants haul slurry ~10–30 km (the brief's range; [domain],
  UNVERIFIED specific source). 15 km is a reasonable default reach for *manure → digester*. It is
  the wrong test for "is there capture-ready CO₂ this region can use", because captured CO₂ is
  liquefied and trucked 100+ km (BioCirc to Esbjerg).
- **Centroid distance is not meaningful at NUTS-2.** Replace the boolean with a quantity:
  eligible, capture-ready upgrading CO₂ from plants inside the region polygon (or within 15 km of
  its boundary, assigned once to avoid double counting). Use that quantity to cap `ad_*` CDR,
  mirroring LFG.
- **Minimum scale:** projects of 4.65 kt/yr (Carbon Capture Scotland, NECCS) to 32.5 kt/yr
  (BioCirc Vesthimmerland) exist with per-plant liquefaction and trucking. A **per-plant floor of
  ~5 kt/yr** is defensible, roughly a 400 Nm³/h biomethane plant [calc]. `AD_MIN_CAP_MTPA` =
  10 kt/yr is ≈ 1.5 × a 500 Nm³/h upgrader, or ≈ 5 MWe of *rated* CHP on the upgrading basis
  [calc]. It is a reasonable regional threshold if counted only from capture-ready plants.
- **Clusters: do not let single-linkage clusters drive the gate.** Germany has ~9,600 plants on
  357,000 km², ~37 km² per plant, so mean spacing is ~6 km [calc]. Single linkage at 25 km will
  percolate into one or a few national-scale clusters, which is meaningless for logistics. For
  display, aggregate per NUTS-3 or a hex grid. For economics, use per-plant CO₂ plus trucking
  distance to the nearest CO₂ terminal/hub. Where aggregation matters (small plants pooling one
  liquefier or one raw-biogas collection pipeline), use a fixed-radius (~10–15 km) density
  grouping with a minimum-sum criterion, not linkage chaining.

### 7. Source-specific pitfalls

- **MaStR (DE).** Confirm catalog codes for Biogas vs Biomethan vs Klärgas vs Deponiegas (and
  exclude Grubengas) before filtering [file, scoping_de flags this]. **Biomethane-fired CHPs**
  (units with `BiomethanErstmaligerEinsatz`) burn grid gas far from any digester. They are gas
  consumers, not CO₂-vent sites, so exclude them from the site inventory or they double-count the
  290 upgraders' gas. **Satellite CHPs** (raw biogas piped to a village CHP) belong to the
  *digester's* Lokation. The digester is the CO₂ site. Installed vs rated capacity: see issue 4.
  Stale records: FvB 11,419 → 9,315 [file].
- **UK.** REPD is a planning database. 163 operational AD+SSD vs NNFCC 630 [file] is a coverage
  failure, not a threshold effect, and the scoping analysis supports this. Sewage digesters by the
  ~10 water companies are essentially absent (REPD 12). Several large ones upgrade to grid
  [domain], so they matter for RNG+CCS. Use Ofwat/water company asset lists and the EA permit
  register. The NNFCC licence blocks redistribution, so gate on open sources only and report the
  NNFCC comparison as internal validation.
- **NL (SDE).** Rows are award instances. Use `gerealiseerd` = Ja and collapse rounds. Many awards
  are never built [domain]. "... ombouw naar gas" themes mark CHP→biomethane conversions, which is
  useful for `output`. Monomestvergisting rows are tiny farm units, well below any capture floor.
  RWZI themes are sewage (tag, link to UWWTD).
- **FR.** Injection registries (ODRÉ = GRDF, shared id) vs the electricity registre have no shared
  key. Sites doing both CHP and injection appear twice. Coordinates are deliberately approximated
  [file, quoting ODRÉ]. Capacity is in GWh PCS. The GRDF typology separates Station d'épuration
  (61) and ISDND (26, landfill: exclude). Units <36 kW exist only as IRIS aggregates, which is
  irrelevant at capture scale.
- **DK.** Centralised plants (fællesanlæg, large, mostly upgrading) vs farm plants. EPT lists
  combustion units, not digesters, so pure upgraders are absent [file]. The ENS list + Evida (57
  grid-connected) is the right backbone. BioCirc sites need primary confirmation [file].
- **IT.** CHP → biomethane conversions under DM 15/09/2022 (reconversion explicitly eligible
  [search: Bird & Bird / Cleary summaries]). PNRR graduatorie are *awards*, not operating plants.
  Many 2008–2012 agricultural CHP plants on 15-year all-inclusive tariffs are reaching tariff end
  [domain, UNVERIFIED dates]. Terna per-feedstock plant counts double-count multi-fuel plants
  [file]. Italy is crop-heavy, so the eligibility share matters a lot.
- **EEA IED.** Annex I 5.3(b): the recovery threshold is 75 t/day, raised to **100 t/day where
  the only activity is AD** [domain, verify against Directive 2010/75/EU text]. Manure-only farm
  AD is generally not "waste" treatment and is absent. Use IED only as a gap-filler for large
  waste AD, never for coverage claims.
- **WWTP double counting.** See 3. Link sewage digesters to UWWTD `uwwCode`, show them once on the
  map, and gate them only for biosolids.

### 8. Physically implausible or missing

- **Stock loss from German EEG tariff expiry: verified and material.** IEA Bioenergy Germany
  country report 2024 [primary, extracted PDF text]: "Until 2030 around 3000 biogas plants, around one third
  of the plants currently in operation, will no longer receive this guaranteed remuneration. Their
  future is uncertain ..." and "there is a fear that up to one third of the plants will stop
  operating by 2030. The biomethane option ... is only feasible for larger plants." Add
  `tariff_end_year` (EEG commissioning date + 20 years, from MaStR) and a `2030 at-risk` flag. The
  gate should not rest on plants likely to close before a Frontier offtake delivers (typically
  2027–2030+). The same issue applies to Italy's first-generation tariffs.
- **Conversions.** CHP → biomethane (DE post-EEG, IT DM 2022, NL "ombouw") is the main route by
  which today's CHP fleet becomes capture-ready. Model it explicitly as `conversion_candidate`.
  Don't treat it as present capacity.
- **Seasonality / operation.** Biomethane plants are baseload (8,000–8,400 h). Flexible CHPs run
  about half of hours but produce gas continuously into storage, so gas output is steadier than
  kWe suggests. Summer heat-demand curtailment affects heat-led plants [domain].
- **Methane leakage and digestate.** Open digestate storage on older plants, upgrader slip (0.1–2%
  by technology) and engine slip all debit removal (≈12% of captured CO₂ per 1% CH₄ lost, [calc]).
  Measured whole-plant losses in DK/UK campaigns are reported at roughly 1–5% of production with a
  heavy tail [domain, recalled from Scheutz & Fredenslund 2019 and Bakkaloglu et al. 2021,
  UNVERIFIED, check before citing]. Add a `leakage_debit` parameter with a sensitivity range.
- **Existing CO₂ offtake** (food-grade, PtX). See 1.
- **Construction status** must never enable the gate. Keep it as a separate layer.
- **Latent doc bug (unrelated but flagged):** METHODOLOGY's pathway table lists bio-oil
  (pyrolysis) at **45%**, while `PATHWAYS["bio_oil"]["cdr_efficiency"]` is **0.65** ("2026 update
  per Charm feedback (was 0.45)") [file]. The doc is stale. This affects every bio-oil CDR figure
  users read in METHODOLOGY, not the engine output.

---

## (c) Recommended parameter table

| Parameter | Central | Range | Source / status |
|---|---|---|---|
| CH₄ LHV | 9.97 kWh/Nm³ | — | physical constant |
| CH₄ HHV (FR PCS, DE Hs) | 11.06 kWh/Nm³ | — | physical constant; watch unit basis |
| CO₂ density (0 °C, 1 atm) | 1.977 kg/Nm³ | — | physical constant |
| η_el gas engine | size-dependent: 0.33 / 0.37 / 0.40 / 0.42 | 0.28–0.47 | FNR Faustzahlen "28 - 47 %" [primary]; size split [domain] |
| Full-load hours, DE CHP (on installed kWe) | 4,250 h (CF 0.49) | 3,800–4,700 | [calc] FvB 29 TWh / 6,816 MW [file]; use rated kWe × ~8,000 h if rated available |
| Full-load hours, biomethane upgrader | 8,200 h | 7,500–8,500 | [domain] |
| Full-load hours, other countries | national generation ÷ installed | — | compute from Terna / DUKES 6.4 / ENS; do not assume |
| CH₄ in raw biogas: crop-heavy | 0.52 | 0.50–0.54 | [domain]; KTBL maize ~52–55% [search] |
| CH₄: manure-dominated | 0.57 | 0.55–0.60 | KTBL cattle slurry 55% [search]; [domain] |
| CH₄: food/biowaste | 0.60 | 0.58–0.65 | [domain] |
| CH₄: sewage sludge | 0.63 | 0.60–0.65 | [domain] |
| Biomethane product CH₄ (H-gas) | 0.97 | 0.96–0.98 | [domain]; NL L-gas lower (~0.88 CH₄-eq) [domain, verify] |
| Upgrader CH₄ slip | 0.5% | 0.1–2% (amine low, membrane/water-scrubber higher) | [domain]; ScienceDirect summary "up to 8% of methane loss" [search] |
| Upgrading CO₂ per MWh_el (CHP-equivalent) | 0.41 t | 0.33–0.52 | [calc], η 0.35–0.42, CH₄ 52–60% |
| All-biogas-carbon CO₂ per MWh_el | 0.90 t | 0.79–1.09 | [calc] |
| Upgrading CO₂ per Nm³ biomethane (97%) | 1.57 kg | 1.28–1.77 (CH₄ 60→52%) | [calc]; 500 Nm³/h × 8,000 h ≈ 5.1–7.1 kt/yr |
| Methane yield, dairy cattle slurry | 17 Nm³ CH₄/t FM | 12–20 | FNR [primary]: 17 m³ slurry → 289 Nm³ CH₄/yr; KTBL 24.3 Nm³ biogas/t FM @55% [search] |
| Methane yield, pig slurry | 12 Nm³ CH₄/t FM | 8–15 | FNR [primary]: 1.6 m³ → 19 Nm³ CH₄ |
| Methane yield, solid (cattle) manure | 66 Nm³ CH₄/t FM | 40–70 | FNR [primary]: 2.8 t → 185 Nm³ CH₄ (upper end; KTBL-type values often ~45–55 [domain]) |
| Methane yield, poultry litter | 90 Nm³ CH₄/t FM | 60–120 | [domain], N-inhibition limits use |
| Methane yield, maize silage | 99 Nm³ CH₄/t FM | 90–110 | FNR [primary]: 40–60 t FM/ha → 3,956–5,934 Nm³ CH₄; KTBL 170 Nm³ biogas/t FM [search] |
| Methane yield, grass silage | 90 Nm³ CH₄/t FM | 60–110 | [domain] |
| Methane yield, food waste (source-segregated) | 75 Nm³ CH₄/t FM | 50–110 | [domain] (≈100–150 Nm³ biogas/t @ 60%) |
| Upgrading CO₂ as share of feed C, cattle slurry | 0.18 | 0.14–0.22 | [calc] from KTBL values [search] |
| Upgrading CO₂ as share of feed C, maize silage | 0.32 | 0.28–0.36 | [calc] |
| Capture fraction of vent CO₂ (amine/membrane) | 0.95 | 0.90–0.99 | [domain] |
| Leakage debit | 12% of captured CO₂ per 1% CH₄ lost | 1–5% loss ⇒ 12–60% | [calc], GWP100 non-fossil CH₄ 27 (AR6) [domain] |
| DE eligible (non-crop) methane share | 0.25 | 0.18–0.30 | DBFZ Report 50 energy basis 18% manure / 73% NawaRo [file] |
| DK energy-crop cap (2025) | 4% by mass | — | ens.dk / EBA [search]; ≈10–15% of methane [calc] |
| Per-plant capture floor | 5 kt CO₂/yr | 3–10 | Carbon Capture Scotland 4,650 t/yr NECCS award [file, primary via scoping] |
| Regional gate (`AD_MIN_CAP_MTPA`) | 0.01 Mt, capture-ready eligible only | 0.005–0.03 | keep, redefine basis |
| Manure feedstock reach | 15 km | 5 (farm)–30 (centralised) | [domain] / brief |
| DE national check: upgrading-basis CO₂ | 13–15 Mt/yr | — | [calc] from FvB 80.6 TWh [file] |
| DE national check: eligible upgrading CO₂ | 3.5–4 Mt/yr | — | [calc] |

---

## (d) Changes I would make to PLAN.md

- **§0 / new §0a (blocking):** state explicitly that `ad_ccs` = RNG+CCS (upgrading-vent capture).
  Quote the POV §3.4 "not pursuing ... (late 2024)" line next to the engine's "no longer excluded"
  note, and require the user to confirm which is current before Phase A. Record the source of the
  decision in METHODOLOGY.
- **§5:** resolve the "domain ruling" as follows. The gating/CDR stream is `co2_upgrading_t_yr` from
  capture-ready plants. `co2_total_biogenic_t_yr` is secondary. Replace flat η/CF/CH₄ with the
  section (c) table: size-dependent η, **rated capacity or national full-load hours**, CH₄ fraction
  by feedstock class, slip-aware biomethane back-calculation, and explicit HHV/LHV and raw/product
  unit handling.
- **§5 (new validation step):** reproduce national totals first. DE 80.6 TWh ⇒ 13–15 Mt upgrading
  basis; DE 29 TWh_el from the CHP subset; UK NNFCC 593.6 MWe / 75,813 Nm³/h. Report the match
  before building on the numbers (per the user's reproduce-first rule).
- **§2 schema:** add `output` (expanded enum incl. satellite_chp, bioLNG), `upgrading_tech`,
  `grid_connected`, `rated_kwe`, `tariff_end_year`, `conversion_candidate`, `accepts_manure`,
  `eligible_ch4_share` + `eligibility_basis` + `grey_feedstock_share`, `digestate_handling`,
  `co2_existing_offtake`, `uwwtd_id` (sewage), `leakage_class`. Demote `manure_based` bool.
- **§6:** replace "carbon share" with a **methane-yield-weighted** share. Add grey categories
  (sequential crops, permanent-grassland silage, straw). Ask the user for Frontier's rule on mixed
  plants (pro rata vs plant-level threshold). Run crop-inclusive and grey-inclusive sensitivities.
- **§4 gate:** gate on the *quantity* of eligible, capture-ready upgrading CO₂ within the region
  polygon (+15 km boundary buffer, each plant assigned once), not on centroid distance. Manure
  regions count only manure-accepting plants. Sewage digesters count only toward biosolids. Never
  count construction-stage plants or CHP-only conversion candidates. Add a per-plant floor of
  ~5 kt/yr.
- **§4 CDR (engine change to propose, out of scope for the build but blocking for meaning):** cap
  `ad_*` CDR at the inventory's eligible upgrading CO₂ × capture fraction − leakage debit,
  mirroring `lfg_*`. Split `ad_ccs` into RNG (vent) and all-carbon (CHP/SOFC) variants. Flag the
  current ODT × 0.37 formula as overstating manure AD+CCS about 2×.
- **§4 clusters:** drop single-linkage at 25 km. It will percolate across Germany (~6 km mean
  spacing). Use NUTS-3/hex aggregation for display and per-plant + trucking-to-hub for economics.
- **§4 maturity / §7:** harmonise on **managed manure (excluding pasture)**, N and VS where
  available. Replace the 0.15 whole-region switch with a partition (share s digested vs 1 − s
  undigested), or at least require s ≥ 0.5 **and** capture-ready CO₂. Pre-compute and show the
  country-level flips before adopting (on incl.-pasture pilot values IT/UK/NL/FR flip to injection; on the managed basis IT stays above 0.15).
  Treat digestate injection as complementary to AD+CCS, not an alternative.
- **§1 table:** add a landfill-gas side file (MaStR Deponiegas, GRDF ISDND, Arpae landfill codes)
  so LFG is excluded from AD but kept for a future EU LFG layer. Add UK water-company sewage
  digesters (Ofwat / company asset data) as a named gap. Note IED 5.3(b) 100 t/day AD-only
  threshold (verify) and that manure-only AD is structurally absent.
- **§3 dedup:** add explicit rules for MaStR biomethane-fired CHPs (exclude), satellite CHPs (fold
  into the digester Lokation), FR dual CHP+injection sites, and NL SDE `gerealiseerd` filtering and
  round collapse.
- **§8 phasing:** add a Phase A0: the POV decision plus the engine-formula reconciliation (issues
  1–2), because the UK two-pager numbers would otherwise be regenerated on the ~2× overstated
  basis.
- **Add a stock-loss note:** German EEG exits, "around 3000 biogas plants, around one third ... by
  2030" (IEA Bioenergy 2024 [primary]), and IT first-generation tariff ends. Add a `2030 at-risk`
  flag and a sensitivity run with at-risk CHP plants removed.
- **Housekeeping:** fix the METHODOLOGY bio-oil 45% vs code 0.65 mismatch when METHODOLOGY is next
  edited.

### Sources opened or cited this session

- FNR Faustzahlen (primary, fetched): https://biogas.fnr.de/daten-und-fakten/faustzahlen
- IEA Bioenergy, Implementation of bioenergy in Germany, 2024 update (primary, PDF text extracted):
  https://www.ieabioenergy.com/wp-content/uploads/2024/12/CountryReport2024_Germany_final.pdf
- KTBL yields (search-result text only, UNVERIFIED): https://www.ktbl.de/fileadmin/produkte/leseprobe/40107excerpt.pdf
- Danish Energy Agency, Biogas in Denmark (search text, UNVERIFIED): https://ens.dk/en/energy-sources/biogas-denmark ;
  EBA: https://www.europeanbiogas.eu/new-limitations-energy-crops-use-biogas-denmark/
- BioCirc Vesthimmerland (secondary, UNVERIFIED): https://carbonherald.com/biocirc-launches-worlds-largest-beccs-facility-in-denmark/ ;
  https://worldbiomarketinsights.com/biocirc-opens-worlds-largest-biogas-based-ccs-plant-in-denmark/
- Greensand operations start (secondary): https://envirotecmagazine.com/2026/09/18/eus-first-full-scale-co%E2%82%82-storage-site-begins-operations-in-danish-north-sea/
- Italian DM 15/09/2022 summaries (secondary): https://www.twobirds.com/en/insights/2022/italy/new-biomethane-decree-in-italy
- Upgrading off-gas purity (secondary summaries): https://www.biocycle.net/basics-biogas-upgrading/
- In-repo: Frontier POV docx §3.4 and CDR table; scoping_de/dk_nl/it_fr/uk/manure_to_ad/eu_wide;
  `engine_core.py` L25–120, L212–295, L692–720, L1044–1066; METHODOLOGY §5, §retrofit gating,
  §Frontier exclusions.
