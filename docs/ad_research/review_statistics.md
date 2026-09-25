# Statistics / data-methods review of PLAN.md (AD plant inventory, EU-27 + UK + NO)

Reviewer role: statistics and data methods. Date: 2026-09-25. Object of review: `PLAN.md` (draft of
the same date), with the six scoping reports as evidence and the engine code as the consumer.
Nothing in PLAN.md or the code was edited.

Conventions in this review:
- **[computed]** = arithmetic I ran on numbers from the scoping reports or the repo (reproducible from
  the stated inputs).
- **[repo]** = read from the current code or data files.
- **[outside knowledge]** = not in the files; from my general knowledge, to be verified before use.

Baseline engine state that any rebuild should be diffed against **[repo]**: `recommendations_eu.json`
has 290 NUTS-2 regions; `avail.ad` is true in 114; `ad_ccs` is the recommendation in 31 and the
runner-up in 0; 62 regions are `manure_wet`-dominant. The gate in
`scripts/eu/build_eu_recommendations.py::compute_avail_anchor` is **centroid-based** today, sums
`est_biogenic_co2_mtpa.value` of every `biogas_ad` facility within its own `proc_radius_km` (hand
clusters carry 80–250 km) and passes at `AD_MIN_CAP_MTPA = 0.01` Mt. Median NUTS-2 area is
~9,860 km² (equivalent radius ~56 km); a 15 km disk is ~7% of the median region **[computed from
`data/geo/eu_nuts.json`]**.

---

## (a) Top 5 issues, ranked by impact on the outputs

### 1. The quantity the gate sums is undefined, and every candidate definition is biased or unstable by a factor of 2 to 7

§4 gates on "cumulative operational AD capacity (CO₂-stream t/yr)", but §5 produces two different
streams and leaves the choice to "a domain ruling". The two differ a lot:

| Typical 500 kWe CHP plant, §5 central parameters | Upgrading-stream CO₂ | Total biogenic CO₂ |
|---|---|---|
| η_el 0.38, CF 0.85, CH₄ 55% | 1.6 kt/yr | 3.5 kt/yr |
| Plants needed to reach 10 kt | ~6 | ~3 |
| Same, CF 0.49 (DE observed, see below) | 0.9 kt/yr (~11 plants) | 2.0 kt/yr (~5 plants) |

**[computed; CH₄ LHV 9.97 kWh/Nm³, 1.977 kg/Nm³ CO₂, 1.964 kg CO₂/Nm³ CH₄ burned]**

Three things compound here:

- **Basis.** If the ruling is "upgrading CO₂ only", a CHP-only plant has no concentrated stream and
  adds **zero**. NNFCC has 496 of 630 UK plants as CHP-only (scoping_uk §3). Under that ruling the
  gate becomes "is there a biomethane plant nearby", a completely different map. The §5 low/high
  ranges alone give a 2.2× spread on the upgrading stream and 1.8× on the total **[computed]**.
- **Capacity factor is biased high.** CF 0.85 (0.75–0.92) applied to nameplate kWe does not fit the
  national totals in the scoping reports: DE 29 TWh_el / 6,816 MW installed → **CF 0.49**
  (Fachverband Biogas: 6,816 MW installed vs 3,316 MW Bemessungsleistung, a 2.1× flexibility
  overbuild); IT 7,496 GWh / 1,473 MW → **0.58**; FR 718 GWh in Q1 2026 × 4 / 583 MW → **~0.56**
  **[computed]**. The plan's *low* bound (0.75) sits above every observed value. On installed kWe,
  DE CHP CO₂ comes out ~1.75× too high (0.85/0.49). The same arithmetic suggests biomethane plants
  do run near 0.85–0.9 (DE: 12.8 TWh produced vs 14.5 TWh at full utilisation), so the bias applies
  to CHP only.
- **Crop exclusion (§6) is a large multiplier on the mass basis.** §6 says carbon share > mass share,
  then proposes mass-based national shares. scoping_de already gives the energy-basis split from
  DBFZ (from a 10%-response operator survey, n = 413, not a census): NawaRo ~73%, manure ~18% by energy (vs 49%/45% by mass). Biogas carbon scales roughly with
  energy, so Frontier-eligible German CO₂ is ~27% of total, not ~51%. Applying one national average
  to every plant is also an ecological fallacy where plant class is known (DE Güllekleinanlagen ≥80%
  manure; ARPAE `TIPO_COMB`; SDE `thema`; NNFCC tonnages).

**Fix.** (i) Get the domain ruling on basis *before* building. Carry both streams, and run the gate on
each as a named scenario. (ii) Calibrate CF per country × output type against metered generation
(FvB TWh, Terna GWh, SDES GWh, ODRÉ annual production by site, CBS PJ) and don't use a fleet-wide
0.85. For DE use Bemessungsleistung, or per-plant EEG settlement generation if accessible
**[outside knowledge: the TSOs publish per-installation EEG annual data at netztransparenz.de; verify
field coverage]**. (iii) Base the eligible fraction on energy (or VS/biogas yield), apply it at plant
or class level where class is known, and fall back to the national value only where it isn't.
(iv) Only then re-derive `AD_MIN_CAP_MTPA`, in the units of the chosen basis. 0.01 Mt was set against
hand-placed 0.1–2.4 Mt clusters and has no meaning at plant level.

### 2. With no imputation, the gate and maturity index map register quality, and that quality varies systematically by country and within countries

"No imputation" is not neutral. In a `manure_wet` region with good storage, a missing digester
flips the call from `ad_ccs` to `injection`, or to `bio_oil_htl` when storage is poor (engine_core
`decide()`, the wet-manure branch). So "never invent a plant that enables a recommendation" is
conservative toward AD+CCS but liberal toward injection. Under the user's rule (be conservative
toward the claim being critiqued), the direction depends on which claim is under test, and the
plan needs to say which one.

Coverage is also not uniform. That makes cross-country comparison unfair, and it also creates
spurious *within*-country patterns:

| Case | Coverage evidence (from scoping) | Effect without imputation |
|---|---|---|
| UK, REPD only | 163/630 plants (26%) but 386.5/593.6 MWe (**65% by capacity**). By nation (count): England 31%, Scotland 18%, Wales 16%, **NI 10%** **[computed]** | UK gate fails widely. NI, which has the densest farm AD, looks the least mature: an inverted pattern |
| Italy, ARPAE Emilia-Romagna only | 268 of Terna's 2,304 plants (~12%). **Lombardy: 0** (verified negative). The current Lombardy cluster is 1.3 Mt | Italy's largest biogas region fails the gate. Worse than the hand-placed map |
| France, ODRÉ only | 855 injection + 1,116 electricity vs CITEPA 1,412 agricultural methanisers. Off-grid farm AD missing | Moderate undercount, concentrated in farm AD, i.e. in manure regions |
| Netherlands, SDE | 651 award rows vs CBS ~205 locations. Includes `gerealiseerd = Nee` (never built) | **Over-count risk**, opposite sign to the UK |
| Germany (MaStR), Denmark (ENS list) | Near-census, but MaStR has stale records and satellite units | Roughly complete. Error is in count, not capacity |

So bias runs negative in UK/IT/FR and possibly positive in NL, and it is concentrated in exactly
the small, manure-heavy farm plants that the wet-manure decision is about. Option (b) (manure
density × national shortfall) assumes missing-at-random in proportion to manure. The evidence says
missingness depends on plant type and sub-region (NI, Lombardy). It also leaks the maturity
denominator (manure) into the numerator, which pulls regional maturity toward the national mean.

**Fix.** (1) Treat the big gaps as data acquisition, not statistics: UK EA permits, Ofgem RER and
NNFCC permission; IT GSE Atlaimpianti through the browser; FR Géorisques 2781. Don't ship a country
whose scope-matched **capacity** coverage is below ~0.5. Note that the phasing puts the UK first
while its REPD-only coverage is the worst. (2) Use a **three-state gate**: *available* (observed ≥ T);
*unavailable* (observed < T **and** the region's coverage tier is good); *coverage-limited* (observed
< T, coverage poor, expected capacity with imputation ≥ T). The engine should show coverage-limited
regions as unresolved (AD+CCS and injection side by side, flagged), not default to injection.
(3) Use imputation only to define the coverage-limited set (below).

### 3. The gate geometry and 25 km single-linkage clusters don't measure what CCS aggregation needs

- **Polygon distance turns the gate into a count.** For the median region, "within 15 km of any
  point" covers the region plus a 15 km buffer, ~1.6× the region's area **[computed]**. With
  per-plant CO₂ from issue 1, T = 10 kt becomes "≥ 3 to 11 typical plants anywhere in or near the
  region", which almost any region in DE/NL/DK/N. Italy passes. The centroid rule has the opposite
  problem: it tests 7% of the region. Neither is "a viable capture project exists". There is also
  an ambiguity in the text: "cumulative capacity within 15 km of any point" can mean the sum over
  the whole buffered region, or **the maximum over points x in the region of the capacity within
  15 km of x**. The second is a real local-catchment test. They give very different answers, and
  the plan must pick one.
- **Single-linkage at 25 km will percolate.** Mean neighbour count λπr² at r = 25 km (uniform
  density): **DE ≈ 53, IT ≈ 15, NL ≈ 14, FR ≈ 7, DK ≈ 7, UK ≈ 5** **[computed from FvB 9,605, Terna
  2,304, NNFCC 630, ENS ~150, CBS/SDE ~300, ODRÉ 855+1,116 (overlapping, upper bound)]**.
  Continuum-percolation theory puts the critical mean degree at ~4.5 **[outside knowledge]**, so
  every one of these is at or above threshold. Real plants cluster, which makes it worse. Germany
  would form a single component, and the convex hull and summed CO₂ of that "cluster" mean nothing.
  The uniform-density critical radius is only ~7 km for DE and ~14 km for IT/NL.

**Fix.** Define gating and clusters as **hub catchments**. Candidate hubs are plants, or grid cells
(preferably upgrading plants, which have a concentrated stream). A hub's pooled CO₂ is the eligible
CO₂ within a gathering radius r_g, and the result is capped at a maximum diameter (or uses
complete-linkage / DBSCAN with a diameter constraint). A region is AD-available if some hub with
pooled CO₂ ≥ T has a catchment that intersects the region's manure-bearing area. Test sensitivity
to r_g and T (section c). For display, keep plant points, and draw hub catchments as circles rather
than convex hulls of chained points.

### 4. Redefining `ad_maturity` as manure-to-AD share changes its scale, and the 0.15 threshold (or any hand-picked one) then drives the result

- On the new basis the pilot values are UK 4.9%, NL ~3.6%, FR ~3–10%, IT 13.1% (incl. pasture) /
  16.8% (excl. pasture), DK 36% (slurry mass). With 0.15 kept, UK/NL/FR drop below the threshold.
  Every current UK (9), NL (3) and FR (2) `ad_ccs` recommendation, 14 of 31, sits in a `manure_wet`
  region, so they would switch to injection, or to HTL where the slurry transport cap binds **[repo: decide() wet branch requires
  `manure_ad_preferred`]**. **Italy crosses the threshold depending only on the pasture denominator.**
  So the threshold, not the data, sets the outcome.
- The bases are inconsistent in more ways than the plan lists. The UK 4.86% keeps pasture N but
  **excludes sheep/goats/horses** from the denominator. The NL 3.6% **includes** species with no
  AD pathway. DK/NL poultry and DK solid manure have structural zeros.

**Fix.** Extract CRT Table 3.B(b) for *all* Parties. The template is identical by construction
(scoping_manure_to_ad §10), so there is nothing to harmonise, only extraction work. National reports
(DCE, OMINEA, NEMA, Thünen) become cross-checks. Fix a common species set {cattle, swine} for the
cross-country index, with poultry as a sensitivity. Make **managed N (excluding pasture)** the primary
denominator, because that is the collectable pool that AD or injection can use. Including pasture
penalises grazing systems (UK, IE) for N that neither pathway can reach. Carry incl.-pasture as a
sensitivity. Choose the threshold **before** looking at which countries flip, record that decision,
and publish the threshold curve (number of regions AD-preferred vs threshold). Add an indeterminate
band of ± the index uncertainty and flag regions inside it rather than forcing a call.

### 5. The validation design is partly circular, uses the least robust metric, and its pass/fail rule can't fail

- **Circular sources beyond the UK.** SDES "draws on the ODRÉ electricity registre" (scoping_it_fr).
  FvB's 9,605 is a MaStR-derived correction (scoping_de). The UK CRT manure-to-AD share comes from
  NNFCC. Comparing a MaStR-derived count with another MaStR-derived count tests whether two dedup
  methods agree, not coverage.
- **Count is the wrong primary metric.** Registers systematically miss small plants: REPD 26% by
  count vs 65% by MWe. The MaStR count is inflated by satellite CHPs, yet each unit's MWe is real.
  CO₂ and CCS relevance track capacity and output, not count.
- **A symmetric 25% hard fail with a "documented reason" escape hatch** can't fail in practice (UK REPD
  would deviate 74%, and the reason is documented). It is also meaningless where the reference is
  itself uncertain by ±50% (NI: 46–132) or covers a different universe (FR 855 / 1,116 / 1,412).

**Fix.** Separate two kinds of check. **Ingest-fidelity checks** compare against the same source's
own published total at a matched date and should agree to ~2% (e.g. ODRÉ 31-Dec-2024 = 576.6 MW vs
SDES 576 MW, already shown). **Coverage checks** compare against an independent universe: CITEPA,
Terna, CBS locations, NNFCC internally. Report capacity coverage as primary, output coverage second
and count as a diagnostic, each with the reference's own range. Use tiers (≥0.8 good, 0.5–0.8 partial,
<0.5 poor) to drive the three-state gate rather than a hard fail. Make **over-coverage (>1.1 on
capacity)** the hard-fail condition, because it signals duplicates, unrealised SDE awards or undeleted
MaStR records. Use regional censuses as hold-outs to measure within-country coverage and location
error: AILE Brittany CSV (285 rows), LfL Bayern district totals, ARPAE ER, NNFCC by UK nation.

---

## (b) Answers to the eight focus areas

### 1. Coverage-gap handling

- **(a) No imputation.** The gate has false negatives (P(miss) rises with coverage shortfall). The
  maturity numerator is biased low only in the fallback that uses plant density. The CRT-based
  index doesn't depend on the register, *except* in the UK, where the CRT share is derived from
  NNFCC (which has better coverage than REPD). Errors are correlated between gate and maturity
  whenever both use plant density, so undercovered regions are penalised twice.
- **(b) Manure-density imputation.** This removes the country-level bias only if missing plants are
  distributed like manure. It creates false positives in manure-rich regions with genuinely little
  AD (e.g. Ireland: ~43 biogas facilities, UNVERIFIED secondary figure in scoping_eu_wide). It shrinks within-country contrasts.
  Fractional imputed plants also interact badly with a threshold gate: summed fractional capacity
  can cross T where no real facility could.
- **Is the bias different across countries?** Yes, clearly (issue 2 table). Negative in UK/IT/FR,
  roughly neutral in DE/DK, possibly positive in NL. Any cross-country comparison of `avail.ad` or
  plant-density maturity is confounded by register quality until capacity coverage is equalised.
- **Recommended approach.**
  1. Acquire data to push capacity coverage to ≥0.8 before shipping a country.
  2. Build the imputation model where coverage is near-complete: DE, DK, and the UK with NNFCC
     internally (licence permitting). Regress plant capacity density on manure N, food-waste
     proxies (population), crop area and WWTP load. Validate it by masking known plants in a
     complete country and checking the recovered gate calls.
  3. Apply it only to regions in the partial/poor tiers.
  4. Use the three-state gate.
- **What to do with the sensitivity test.** Run gate/decide under (a) and (b). The output that
  matters is not a total but the **flip set**: the per-region list whose recommendation changes.
  Publish the flip set as a map flag ("recommendation depends on unobserved AD capacity"), and report
  its size by country. If the flip set is large in a country, the country isn't ready.

### 2. Dedup / record linkage

- **False splits vs false merges.** Where both records are exact (REPD OSGB, MaStR, ARPAE, EEA),
  500 m is reasonable. When either record is commune/PC4/postcode precision, true duplicates can be
  kilometres apart, so a fixed 500 m rule produces **false splits**: duplicated capacity, which biases
  the gate toward passing. This is the mirror image of "inventing a plant", so it should count as the
  more serious error under the plan's own principle. In dense areas (Bavaria, Po valley, NL dairy
  PC4s), loosening the threshold produces **false merges**, which lose real capacity if the merge
  keeps one record's capacity.
- **Rules to specify.** (i) Distance threshold as a function of both uncertainties, e.g.
  d ≤ k·√(u₁² + u₂²) with a floor of 500 m. Block on admin code (INSEE, PC4, gemeente, ISTAT
  `COD_COM`) when either record is coarse. (ii) Score candidate pairs (name similarity after stripping
  generic tokens like "Biogas", "AD", "Farm"; capacity ratio; commissioning-year difference; output
  type). Set explicit auto-merge / review / auto-reject thresholds instead of a single cut-off.
  (iii) **Capacity merge rule.** Sum complementary outputs (CHP kWe from the electricity registre +
  injection Nm³/h from ODRÉ, or CHP + upgrading at the same site), but take the max (or the
  highest-priority source) for the same output reported twice. Without this, a merge silently drops
  the injection stream or double-counts the biogas. (iv) **MaStR.** Collapse by Lokation, but check
  whether satellite CHPs have their own Stromerzeugungslokation **[outside knowledge: they usually
  have their own grid connection point, so Lokation collapse may not remove them]**. Their
  generation capacity is real, so this matters for counts, not CO₂. Keep them as units linked to a
  parent digester if MaStR's `EinheitenGasErzeuger` linkage allows. (v) **FR "Confidentiel" (34.5% of
  B.MET rows).** Before relying on commune + capacity + date, compute the collision rate: the share of
  communes with ≥2 biogas installations in the registre. Mark matches in those communes as ambiguous.
  (vi) **NL anonymised rows (48%).** Rows in the **same SDE round** and the same PC4 + theme are
  **distinct** plants. Rows in different rounds are candidate same-plant renewals (match on capacity,
  start year). Drop `gerealiseerd = Nee`.
- **Measuring it.** Draw a stratified random sample of candidate pairs (blocked within ~5 km or the
  same admin unit), stratified by score band × source pair × country, e.g. 30–50 pairs per stratum,
  ~300–400 total. Have two people label a 20% subset (report Cohen's κ). Adjudicate with aerial
  imagery and planning or permit records. Estimate **precision** (auto-merged pairs that are true
  matches) and **recall** (true matches found), weighted back to the pair population, with Wilson
  95% CIs. Report the **capacity-weighted net error** (duplicated MWe retained − real MWe lost),
  because that is what moves the gate. Also report within-source collapse results against
  independent location counts (MaStR sites vs FvB 9,315 + 290; SDE sites vs CBS ~205; EPT units vs
  the ENS list).
- **Reproducibility.** The review CSV decisions need a version-controlled `dedup_decisions.csv` (pair
  ids, decision, reviewer, date, evidence) that the pipeline reads, so re-runs are deterministic.
  Pin the fuzzy-matching library version and use deterministic tie-breaking.

### 3. Validation design

See issue 5. In short: use capacity as the primary metric, output second, count as a diagnostic.
Scope-match every comparison (AD classes, including or excluding sewage and landfill; operational
only; same reference date). Separate ingest-fidelity from coverage checks. Report the reference's
own range. Use tiers, not a symmetric 25% rule, and hard-fail on over-coverage. The UK is circular
twice: NNFCC is both the validation total and (via NAEI) the source of the UK CRT manure share, so
neither can check the other. Say so in the coverage table. The validation table should report, per
country: backbone source + date; reference source + date + universe; coverage by capacity, output
and count; tier; the flip-set size from the imputation sensitivity; and dedup precision/recall.

### 4. CO₂ estimation uncertainty

- **Parameters.** Calibrate CF per country × output type to metered output (issue 1). After that,
  the dominant remaining parametric uncertainties are η_el and CH₄ fraction. η_el depends on size
  **[outside knowledge: small engines <100 kWe are typically ~0.30–0.35]**, so make η a function of
  kWe, not a constant. CH₄ fraction depends on feedstock (manure-heavy biogas tends toward the lower
  end, fat/food waste higher) **[outside knowledge]**. The upgrading-CO₂ stream is sensitive to CH₄
  fraction through (1−f)/f: 1.0 at 50%, 0.82 at 55%, 0.67 at 60% (±22%) **[computed]**. Biomethane →
  raw biogas also needs a methane-slip / upgrading-efficiency term (small).
- **Correlation.** CF, η and CH₄ errors are *systematic*: shared across a country's fleet and plant
  class. They don't average out when summed. Summing plant lows and highs (comonotonic) is the
  correct bound for fully correlated errors. Summing in quadrature would understate the uncertainty
  of cluster and regional totals by roughly √n.
- **Monte Carlo or intervals.** Use a hierarchical Monte Carlo. Each iteration draws fleet-level
  parameters once per country × class (calibrated distributions) and plant-level idiosyncratic noise
  independently. Push each draw through the gate and `decide()` and report **P(avail.ad)** and
  **P(ad_ccs recommended)** per region. Intervals on sums can't give that, because the gate is a
  non-linear threshold. Keep structural choices (CO₂ basis, crop rule, coverage handling, geometry)
  as named **scenarios**, not MC draws. They dominate the parametric spread, and mixing them into
  one distribution would hide which choice is doing the work.

### 5. Location precision

- **Magnitude.** Commune centroids in France are typically ~1–3 km from the true site **[outside
  knowledge: ~35k communes over ~550k km² ≈ 16 km² mean area]**. NL PC4 is similar. DK postcodes are
  coarser (~5 km equivalent radius) **[outside knowledge]**. So for a 15 km reach, commune/PC4 error
  is second-order. It matters for DK postcodes, "region"-precision records, ODRÉ's *deliberately
  approximated* injection coordinates (displacement unknown, so measure it against AILE and
  Géorisques), and whenever the gate uses a small r_g.
- **NUTS assignment.** Assign NUTS-2 by admin-code nesting (INSEE commune → département → NUTS-2;
  gemeente → province = NUTS-2; ISTAT → region), which is exact, instead of point-in-polygon of a
  centroid.
- **Reach rule.** Represent each coarse record as uniform over its admin polygon (the polygons are
  available, which is better than an isotropic Gaussian with σ from `loc_uncertainty_km`). Compute
  p_i = the fraction of the polygon within reach of the test point or hub. Evaluate the gate on
  expected capacity Σ cap_i · p_i and report two bounds: **robust-pass** (the gate passes counting
  only p_i = 1 plants) and **robust-fail** (it fails even counting every p_i > 0 plant). Regions
  between the bounds are "precision-dependent" and get a flag. This slots into the Monte Carlo by
  sampling each coarse location from its polygon.
- Don't include centroid-precision points in any displayed hull or catchment geometry as if they
  were exact.

### 6. Maturity as manure-to-AD share

- **Harmonisation.** See issue 4: CRT 3.B(b) for all Parties; N basis; species set {cattle, swine}
  (poultry as a sensitivity, given structural zeros in DK/NL and absence in the DK solid-manure
  pathway); managed N (excl. pasture) as primary, incl. pasture as a sensitivity. Store the numerator,
  both denominators, inventory year and submission year as fields. Treat NO/NA/IE as zero only where
  the category exists but has no AD, and record structural absence separately. Flag carried-forward
  values (IT 19% dairy held constant since 2020 from a 2018 CRPA study; DE and FR 2024 carried from
  2023) as having wider uncertainty.
- **Threshold.** Choose it in advance using an external rationale. Candidates: (a) a decision-relevant
  level, e.g. the share at which existing digester intake capacity could absorb a meaningful
  fraction of incremental regional wet manure; (b) a natural break in the cross-country
  distribution, stated before the flips are computed. Don't tune it to reproduce the old
  hardcoded map (circular) or a desired one. Publish the threshold curve and an indeterminate band.
  Given the pilot spread (4–36%), the call will be robust for DK (above) and UK/NL (below) under most
  thresholds, and fragile for IT and FR. Say that explicitly.
- **Within-country regionalisation.** Only regionalise where within-country register coverage is
  demonstrably uniform (from the regional hold-outs). The UK REPD nation split (10–31%) and Italy (one
  region) fail that test. Use empirical-Bayes shrinkage of regional plant-derived manure intake toward
  the national share, with the weight set by the number of plants and the precision of their manure
  tonnage. This replaces the current ad hoc clamp [0.6, 1.4] in `build_ad_maturity.py`. Flip a region
  relative to its country only if its interval excludes the threshold. Where regional manure tonnage
  is imputed from class averages (DBFZ for DE), regional variation is just plant count × class
  average, so label it "modelled". The ENSPRESO denominator isn't the CRT N basis. Ratio-scaling to
  the national share cancels that at national level but assumes proportionality between the two
  across regions, which is a caveat to state.

### 7. Gate design

- **Centroid vs polygon.** Neither, on its own (issue 3). Use the hub-catchment test: does any hub
  with pooled eligible CO₂ ≥ T, gathered within r_g, overlap the region's manure-bearing area. If a
  simpler rule is needed for phase A, use "max over points in region of capacity within r"
  (a grid-evaluated local catchment), not "sum within the buffered polygon".
- **Cluster vs plant threshold.** `AD_MIN_CAP_MTPA = 0.01` has to be re-derived in the chosen basis.
  Anchor it to a real minimum viable capture scale. The scoping evidence has Danish NECCS awards at
  4.65 kt, 25 kt and 130.7 kt/yr, so 5–25 kt is a plausible range for the test. Should manure regions
  require a manure-accepting plant? Yes as the primary rule, since the wet-manure decision is about
  where manure goes. Class labels are uncertain, though, so run "all classes" as a sensitivity.
- **Sensitivity.** See section (c). The output to report is not only the number of `ad_ccs`
  recommendations but the per-country flip counts vs the baseline (31 `ad_ccs`; 114 `avail.ad`;
  62 `manure_wet`), shown as a tornado (one at a time) plus a small factorial over the three
  structural switches (basis × crop rule × coverage handling).

### 8. Other reproducibility and misleading-result risks

- **Vintage.** Sources span 2021/22 (DBFZ survey), 2022 (EEA IED v10, whose latest reporting year
  may be 2022), Mar-2024 (NNFCC), 2024 (Terna, Eurostat, CRT inventory year), 2025 (FvB, SDE) and
  Jul/Aug-2026 (ODRÉ, REPD). Declare one reference date (e.g. 2025-12-31). Filter records by
  commissioning and decommissioning date where available. Compare validation totals at matched dates
  (the ODRÉ/SDES 31-Dec-2024 match is the model to follow). Label mixed-vintage outputs.
- **Status staleness.** Add `status_confidence` and `last_evidence_of_operation` (e.g. ODRÉ metered
  production > 0 in the latest year; MaStR last update; SDE `gerealiseerd = Ja`; EEG settlement
  generation). MaStR has missing deregistrations (FvB); EEA IED records may be several years old;
  REPD status can lag. Treat "operational" with no recent evidence as a separate category in
  sensitivity.
- **MaStR faulty records.** Validate `Hauptbrennstoff`/`Biomasseart` against `Katalogwerte`. Flag
  implausible coordinates (outside Germany, (0,0), or a Gemeinde mismatch) and implausible capacity
  (kWe outliers relative to Gas-Erzeuger capacity). Report counts dropped per rule.
- **Pinning.** Use a dated MaStR Stichtag export (not the daily file) with a checksum. ODRÉ, REPD and
  SDE: record the fetch date and hash the derived file. Browser-assisted manual downloads (GSE,
  Géorisques, UNFCCC CRT) can't be scripted, so commit checksums and derived extracts and document
  the manual steps.
- **NNFCC dependence.** Any published number that depends on NNFCC (UK validation, imputation
  calibration, the UK maturity regionalisation) can't be reproduced by a third party. The public
  pipeline needs an NNFCC-free path, and the README should state the difference between the paths.
  Whether a published gate boolean derived from NNFCC counts as redistribution is a licensing
  question for the user, not a statistical one.
- **Stable IDs after merges.** Define the merged record's `id` deterministically (e.g. from the
  highest-priority source), and keep all source ids so upstream id changes can be traced.
- **Display.** Current hand clusters for DE sum to ~8.3 Mt **[repo]**. An order-of-magnitude check
  from FvB's 80.6 TWh biogas energy gives ~13 Mt upgrading-stream + ~16 Mt combustion CO₂ (~29 Mt
  total) before any crop exclusion **[computed; rough]**. The rebuilt totals will move a lot, and the
  before/after diff should explain the change by component (basis, CF, crop share, coverage).

---

## (c) Recommended sensitivity tests (report per-country flip counts vs the new baseline and vs the current map)

Structural scenarios (factorial, 2×2×2 = 8 runs):
1. CO₂ basis: upgrading-stream only vs total biogenic.
2. Crop exclusion: none vs energy-basis eligible fraction (class-level where known).
3. Coverage handling: no imputation vs model-based imputation, producing the **flip set**.

One-at-a-time (tornado), around the chosen baseline:

4. Gate threshold T: 5 / 10 / 25 / 50 kt (in the chosen basis).
5. Reach / gathering radius: 10 / 15 / 25 / 40 km.
6. Gate geometry: centroid disk / buffered polygon sum / max-over-points local catchment / hub-catchment.
7. Plant class filter for manure regions: all vs manure-accepting only.
8. CF: calibrated per country vs the plan's fixed 0.85 (shows the size of the bias).
9. DE capacity basis: installed vs Bemessungsleistung.
10. Status: operational only vs operational + construction vs dropping records with no recent evidence.
11. Dedup: strict vs loose thresholds (report capacity change and flips).
12. Location: robust-pass vs robust-fail bounds for coarse-precision records.
13. Cluster/hub: r_g 5 / 10 / 20 km and max diameter; single-linkage 25 km included only to show the percolation failure.
14. Maturity denominator: managed N vs incl. pasture; species set {cattle, swine} vs + poultry.
15. Maturity threshold: full sweep (threshold curve), plus the pre-registered value ± index uncertainty.
16. Source exclusions (UK): with and without NNFCC-derived inputs; (IT) ARPAE-only vs + GSE when obtained.

Probabilistic:

17. Hierarchical Monte Carlo (≥1,000 draws) giving P(avail.ad) and P(ad_ccs) per region. Map regions
    with 0.2 < P < 0.8 as uncertain.

Report for each: # regions `avail.ad`; # `ad_ccs` recommended and as runner-up; # manure_wet regions
changing call; broken down by country; and the list of flipped region ids (committed as CSV).

---

## (d) Changes I would make to PLAN.md

- §4: Define the gate quantity precisely (which CO₂ stream, whether it is eligible after crop
  exclusion, and in which units), and block the build on the domain ruling. Carry both streams in
  the schema and name the gate scenario.
- §4: Replace "within 15 km of any point in the region" with an explicit hub-catchment (or
  max-over-points) rule. Remove single-linkage 25 km, and state the percolation reason.
- §4: Replace coverage options (a)/(b) with the three-state gate (available / unavailable-good-coverage
  / coverage-limited), plus model-based imputation used only to define the flip set. Add a
  "don't ship a country below 0.5 capacity coverage" rule.
- §4 / §7: Maturity uses CRT 3.B(b) for all Parties, species {cattle, swine}, managed-N primary,
  incl.-pasture as a sensitivity. Choose the threshold in advance with a written rationale and an
  indeterminate band. Regionalise only where coverage is shown to be uniform, using shrinkage
  (retire the [0.6, 1.4] clamp).
- §5: Replace fixed CF 0.85 with CF calibrated per country × output type to metered generation. Use
  Bemessungsleistung (or EEG settlement kWh) for DE. Make η_el size-dependent. Add upgrading
  slip/efficiency. Specify hierarchical Monte Carlo with fleet-level correlated parameters.
  Output P(avail) and P(ad_ccs).
- §6: Base crop exclusion on energy (or carbon) shares (DBFZ energy split), applied at plant or class
  level where known, with national fallback flagged.
- §3.3: Make dedup thresholds uncertainty-aware with admin-code blocking. Add scored matching with
  three bands, the capacity merge rule (sum complementary, max duplicated), the NL same-round rule,
  the FR confidential collision-rate check, and a versioned `dedup_decisions.csv`.
- §3.3: Add a dedup evaluation step: a stratified hand-labelled pair sample, precision/recall with
  Wilson CIs, κ on the double-labelled subset, and capacity-weighted net error in the validation
  report.
- §3.5: Split validation into ingest-fidelity (same source, ~2%) and coverage (independent universe)
  checks. Use capacity as primary, output second, count as a diagnostic. Use tiers instead of the 25%
  rule, and hard-fail on >1.1 over-coverage. Add regional hold-outs (AILE, LfL Bayern, ARPAE, NNFCC
  by nation). List known circular pairs (UK NNFCC ↔ CRT; FR SDES ↔ ODRÉ; DE FvB ↔ MaStR).
- §2 schema: add `status_confidence`, `last_evidence_of_operation`, `ref_date`, `admin_code` (for
  exact NUTS nesting), `eligible_fraction` (+ basis), `cap_kwe_rated` (DE), and a `parent_site` link
  for satellite units.
- §3.2: Assign NUTS-2 by admin-code nesting, not centroid point-in-polygon. For reach, treat coarse
  locations as uniform over their polygon, and report robust-pass / robust-fail bounds.
- §8 phasing: Don't rewire the UK gate on REPD alone. Phase A should first reach ≥0.5 capacity
  coverage (EA permits, Ofgem RER, NNFCC permission), or ship the UK as coverage-limited. Move GSE
  browser extraction ahead of the IT build.
- New §: a reproducibility block. Declare the reference date; use a MaStR Stichtag export plus
  checksums; hash all derived files; document the manual browser steps; provide an NNFCC-free public
  path, with the difference reported; use deterministic merged ids.
- New §: a sensitivity-reporting spec (section c above). Commit the per-region flip lists, and state
  which results are robust across all structural scenarios.
