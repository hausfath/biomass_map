# AD + CCS + digestate injection: carbon partitioning, counterfactual soil carbon, nutrient debit, net CDR efficiency

Research date 2026-10-19. Verification labels: **V** = primary text read this session (quoted or table read); **A** = abstract / publisher abstract page only; **S** = secondary (slide deck, search-result summary, EC fiche, agency report); **K** = typical value from general knowledge, NOT checked against a source this session. Treat S and K as UNVERIFIED. Several primary sources (Thomsen 2013, Möller 2015, Hjorth 2010, Liu 2020) were paywalled or blocked (HTTP 403 / login redirect), so their numbers are S/A.

Bottom line first: the literature does not support a single "SOC-forgone" number. Estimates of how much digestate carbon would persist in soil differ by about 10x depending on definition and model (3-4% of applied C at 100 yr in Yasso07, versus 12-23% of feed C as a "stable" pool). The debit is also nearly the same for raw slurry and digestate when expressed per unit of feed carbon. A central case with a 50-yr horizon gives net CDR of roughly 0.55-0.70 of feed C for whole-digestate pathways, with a plausible 0.4-0.75 range, and about 0.72 (range 0.5-0.85) for raw slurry injection versus the tool's current 0.90.

---

## 1. Carbon partitioning in AD of slurry/manure

### 1.1 Feed C to biogas versus digestate

| Case | Biogas C (% feed C) | Digestate C (% feed C) | Source / status |
|---|---|---|---|
| Cattle manure + wheat straw (60/40 C), leach-bed pilot, 139 d | 23-27% | 53-63% (plus 2-3% percolate; 12-17% unaccounted) | Tampio et al. 2024, Sci Total Environ 927:172083 (V). Quote: "the digestates R1 and R2 contained 53 and 63 % of the total C fed to the pilot reactors. 27 % and 23 % of C was captured as biogas (CH4 and CO2)... there was 17 and 12 % loss in the C balance". Not slurry; straw-rich, dry-ish system. |
| Dairy cattle faeces, lab digestion | 46% gaseous C loss | 54% | Thomsen et al. 2013, Soil Biol Biochem 58:82-87, abstract via search summary (A/S): "gaseous C losses were 80 and 46% of the C in feed and faeces, respectively". |
| Slurry, German reactor data (Reinhold 1991) | 16.5% | ~83.5% | Möller slide deck (Hohenheim, ORC conf 2013), citing Reinhold et al. 1991 (S, German slide). 16.5% C degraded in reactor, then 20.5% in incubation, 63.0% left, versus 37.8% degraded in incubation and 62.2% left for raw slurry. Reactor conditions unknown. |
| Cattle slurry, typical full-scale | ~25-40% | 60-75% | K. Biogas yield per VS in cattle slurry is limited by the large share already degraded in the animal and in storage. |
| Pig slurry | ~35-55% | 45-65% | K. Slurry-pit data: degradable share VSd 0.51 (pig) vs 0.33 (cattle) kg/kg VS (S, PMC4986936, in-house storage study, not digesters). |
| Co-digestion with energy crops / fats | 40-60% | 40-60% | K. |

Central assumption used in section 5: **35% of feed C to biogas (range 20-50%)** for cattle slurry. This is a judgement call spanning the verified 23-27% (straw system) to 46% (faeces lab). Pig slurry is not verified here.

### 1.2 Biogas C split
Biogas ~55-60% CH4 / 40-45% CO2 by volume, which equals the molar and therefore carbon split (K, textbook). Central: CH4 57% / CO2 43% of biogas C. Hence **RNG vent CO2 = ~0.43 x biogas C**; at f_biogas=0.35 that is 0.15 of feed C.

### 1.3 Digestate composition
- Tampio et al. Table 2 (V), leach-bed digestate: TS 12.5-12.9%; VS 83.5-85.4% TS; C 46.0-46.1% TS; N 2.0% TS; ash 14.6-16.5% TS; lignin 155.8 / 133.1 g/kg TS (cattle manure feed 152.5; wheat straw 56.7); NH4-N 0.8-1.0 g/kg FM; P 0.3-0.4 g/kg FM; K 4.8-5.0 g/kg FM. C/N of this digestate = 23 (straw-rich; not representative of slurry digestate).
- Slurry digestate (K, not verified): DM 3-7%, C 35-42% of DM (~15-25 kg C/t), total N 3-5 kg/t with 55-70% as NH4-N, C/N ~5-10 (pig lower than cattle), P2O5 1-2 kg/t. **Implication for injection: whole digestate is ~95% water; ~20 kg C/t.** Separated solids reach DM ~20-25% (AFBI screw press 24.5% DM, S).
- Recalcitrance (V): AWEN fractionation, "the share of ethanol and non-soluble fractions increased from 26 % to 37-40 %" with digestion; "around 40 % of the digestate C was fairly recalcitrant toward further degradation in soils". Möller 2015 abstract (S): "The remaining organic fraction after anaerobic digestion is much more recalcitrant than the input feedstocks" (quoted as relayed by a search summary, not read directly). Residual methane potential of digestate was 34-51 L CH4/kg VS (V, Tampio), i.e. further digestion or storage CH4 is possible.

### 1.4 Mechanical separation: partition of C, N, P, K
Primary review: Hjorth, Christensen, Christensen, Sommer 2010, Agron Sustain Dev 30:153-180, doi 10.1051/agro/2009010. Full text blocked; only abstract seen (A): "separation efficiency... for the removal of dry matter and phosphorus (P)... centrifugation > sedimentation > non-pressurized filtration > pressurized filtration"; N and NH4+ separate less efficiently than DM and P.

| Fraction to solids | Mass | DM/TS | VS | N | P | K | Source / status |
|---|---|---|---|---|---|---|---|
| Screw press, digestate (AFBI commissioning) | - | 24.5% DM in solids | - | 15% | 25% | 10% (K2O) | AFBI report (S, not peer reviewed) |
| Screw press, raw slurry (3tres3 table, swine) | 10-25% | - | - | 15-30% | 20-80% | - | S |
| Centrifuge, raw swine slurry | 10-20% | - | - | 25-50% | 40-80% | - | S |
| Screw press + centrifuge, pig slurry (Pantelopoulos & Aronsson 2021) | - | 52.6% of TS | - | 14.4% | 73.8% | - | S (search summary) |
| Screw press, dairy slurry (Cornell DESP) | - | 40-70% of TS | 40-50% of VS | - | - | - | S |

**Carbon share to the solid fraction: no verified figure found.** Working assumption: **35% of digestate C to solids for a screw press (range 20-60%; centrifuge higher)**, scaled loosely from VS/TS capture. This is the weakest number in the (c) variants. Liquid fraction keeps 85-90% of N and K and 10-75% of P, and its C is the more labile part.

---

## 2. Counterfactual SOC from land-applied digestate

### 2.1 Retention versus time (modelled and incubation)

| Material / source | 1-2 yr | 5 yr | 10 yr | 20-25 yr | 50 yr | 100 yr | Status |
|---|---|---|---|---|---|---|---|
| Digestate (cattle manure + straw), Yasso07, S Finland, % of applied C | - | 48-50% | - | ~20-27% | - | 3-4% | Tampio 2024 (V). Quote: "after 25 years, only around 20-27 % of the added C was left in the soil and after 100 years, only 3-4 %". |
| Raw cattle manure / wheat straw, same model | - | 43% / 39% | - | lower than digestate | - | ~3-4% (all materials) | Tampio 2024 (V); "more C retained in soil when digested material was applied compared to undigested". Raw 25 y and 100 y values are in Fig 4 bars, not read. |
| Interpolated digestate (my interpolation, exponential between Yasso points) | - | 49% | ~40% | 24% | ~13% | 3.5% | derived; 15 yr ~34% |
| Digestate vs digested/raw faeces, incubation + kinetic model (Thomsen 2013), % of applied C | feed 14 / digested feed 58 / faeces 48 / digested faeces 76% | - | - | - | - | - | A/S (search summary of abstract) |
| Long-term retention per C originally in feed (Thomsen 2013) | - | - | - | "12-14% of the C initially present in the feed" | | | A/S. Authors conclude retention "over decades to centuries appears to be similar whether the initial turnover... occurs in the soil, in the digestive tract of ruminants, in an anaerobic reactor or in a combination" (A/S). |
| Digestate solids one- and two-step AD (Nyang'au et al. 2022, Sci Total Environ 851:158177) | - | - | - | "26-54 % of C applied is sequestered in the soil in the long-term"; "12-16%" of pre-digestion C | | | A (abstract read: orgprints). 212-d net C mineralisation: undigested solid biomass 68%, primary digestates 59-65%. |
| Cattle digestate vs manure vs biochar, 100-day-scale incubation C loss (Schouten et al. 2012, GCB Bioenergy 4:751) | - | - | - | - | - | - | A. C lost as CO2: manure 39% (loess)/32% (sand); digestate 31%/18%. Retention complement is my calculation. |
| Karki et al. 2013 (Daisy, 50-52 yr, loamy sand/sand) | - | - | - | - | "extra carbon retained... 41% non-digested, 35% digested (loamy sand); 37% / 29% (sand)" | - | S (SSSA poster abstract; poster text says digestion C loss 46%, inputs 1013 vs 543 kg C/ha/yr). Authors note result "did not match the incubation results" and warn that short-term calibration "might not be applicable for estimating the long-term response". Denominator of the percentages is ambiguous; if % of applied C, per unit feed C raw retains ~2x digested (0.41 vs 0.35 x 0.54 = 0.19). |
| Reinhold 1991 (S, slide) | - | - | - | - | - | - | C remaining after reactor + incubation 63.0% vs 62.2% for raw slurry (equivalent). |

### 2.2 Does digestion change SOC outcomes per unit of feed C?
Evidence is mixed but leans "little net difference":
1. Per unit **applied** C, digestate is more stable (Tampio, Thomsen, Schouten, Möller). Per unit **feed** C, digestion removes 20-50% of C first, so the advantage largely cancels. Tampio (V): "the conventional use of CM and WS would induce slightly higher share of stable C applied to soils (26 %) compared with the utilization of anaerobic co-digestion (21-23 %)", while Yasso07 shows longer retention of digestate C (Fig 4).
2. Thomsen conclusion (A/S, above): similar long-term retention regardless of where the first turnover happens.
3. Möller 2015 conclusions (S via search summaries, not read): "The direct effects of anaerobic digestion on long-term sustainability in terms of soil fertility and environmental impact at the field level are of minor relevance"; digestion allows SOM build-up similar to direct feedstock application or composting.
4. Meta-analytic: Liu et al. 2020 (Sci Total Environ 745:141003; 92 studies; via EC "Manure processing" fiche, S): composted/digested manure "induced a non-significant effect size on soil organic carbon" versus untreated manure. Ablieieva et al. 2024 (IJROWA 14(2), doi 10.57647/ijrowa-k96c-rj49; A/S) report 21 studies where digestate raised soil C for up to ~8 yr, mostly versus mineral fertilizer or no amendment, not versus raw manure.
5. Field: Barłóg, Hlisnikovský, Kunzová 2020, Agronomy 10(3):379 (A): "Fertilization did not have any significant influence on SOC, TN, and SOC/TN" over four years (digestate vs cattle slurry vs NPK). Abstract also says digestate is "characterized by relatively little organic matter."
6. Model disagreement: Karki/Daisy gives raw manure a higher long-term SOC gain than digested, opposite to the incubation-calibrated expectation.

### 2.3 Durability of the land-applied SOC credit
All modelled retention curves (Tampio, Yasso07) decay toward ~0; the "persistent" claim only holds if applications repeat annually. Tampio (V): "C in all the studied organic amendments (digestates, CM, and WS) was gradually degrading in soils... still a limited and relatively short-term impact on the SOC pools. However, as such organic amendments are often regularly applied each year, their application has the potential to gradually increase soil C stocks over the long term." SOC is subject to saturation and reversal (tillage, warming, land-use change). For a counterfactual debit this matters in the direction of **smaller** debit at long horizons: forgone SOC is less than the instantaneous "stable pool" views imply, and the credit forgone is largely transient. A farm already at SOC equilibrium would, however, lose stock if applications stop (the cohort integral at horizon H, as used below, is the consistent accounting).

### 2.4 How the Isometric module frames the horizon
Isometric Biomass Feedstock Accounting Module v1.3, https://registry.isometric.com/module/biomass-feedstock-accounting/1.3 (read via fetch tool, which summarised the page; exact wording below is the tool's quoted extraction, so confirm on the page):
- §3.3: "Biomass decay that would lead to additional carbon storage in the landscape is taken into account," including "soil organic carbon gains from biomass decay"; "Project Proponents can provide evidence of its negligibility at the feedstock removal rates."
- §3.3: "Biogenic carbon that would likely be stored in the biomass for the next 15 years" counts as counterfactually stored; counterfactual emissions use GWP100; if all stored carbon would be emitted within 15 yr counterfactual storage is zero, else the 50-year stored amount is the fallback (paraphrase of the extraction; verify exact logic).
Reading: a 15-50 yr horizon applies, which makes the relevant debit **~34% (15 yr) to ~13% (50 yr) of applied digestate C** per the interpolated curve above, or 0 if one argues digestate C is fully mineralised within 15 yr.

---

## 3. Nutrient counterfactual

### 3.1 Content and replacement
- Digestate keeps essentially all feed N, P, K (AD does not remove them; "concentrations of N, P, and K in both digestates... reflected the nutrient content of the feedstocks", Tampio V). Typical slurry digestate values are K (section 1.3). Feed N per feed C: cattle slurry C/N ~8-12 gives **~0.08-0.12 kg N per kg feed C** (K). Because C is lost to biogas but N stays, digestate N per digestate C is ~1.5x higher than in feed.
- Mineral fertilizer equivalence (MFE) of digestate N ~50-70% versus ~35-50% for raw slurry (K; Möller & Müller 2012 review is the usual source, not read). Central: 0.6 digestate, 0.45 raw.
- Isometric treats the displacement as synthetic fertilizer. Module v1.3 §4.3.2 (extraction): "The Project causes some displacement to the manure that would have been used for nutrient replenishment... it is generally assumed that the replacement material is synthetic fertilizer." §8.1: "The total fertilizer capacity previously provided by the feedstock must be calculated based on the feedstock's NPK content", sized by "the most limiting factor (either N, P, K)". §8.2: replacement emissions are zero if the manure procured does not exceed the Sustainable Usage Rate. Biomass Geological Storage protocol §5.0 item 3 (extraction): "to demonstrate impact on carbon and nutrient (nitrogen, phosphorus, potassium) removal"; §11.0: "fertilizer production to replace those nutrients need to be accounted for." Important: sized by the most limiting nutrient, not N alone.

### 3.2 Emission factors
| Quantity | Value | Source / status |
|---|---|---|
| N fertilizer production, EU average, ammonium nitrate | 3.32 kg CO2e/kg N (cradle to plant gate) | Hoxha & Christensen 2019, IFS Proc. 805, Table 7 (V) |
| N fertilizer production, CAN (EU avg) | 3.52 kg CO2e/kg N (Table 9) | V |
| Urea EU avg | 3.50 incl. 1.59 CO2 released on application (1.91 excl.) (Table 11) | V |
| AN, North America / Middle East / China coal | 6.71 / 7.15 / ~10+ (Table 7; China coal row not read) | V (first two) |
| Field N2O from synthetic N (IPCC default EF1 1% N2O-N) | 1% x 44/28 x GWP100 273 (AR6) = ~4.3 kg CO2e/kg N | K; check IPCC 2019 Refinement Table 11.1 and GWP version |
| P2O5 production | ~1.0-2.0 kg CO2e/kg P2O5 | K; related check (S): a Finnish LCA reports mineral P 2.3-4.5 kg CO2e per kg P (x0.436 = 1.0-2.0 per kg P2O5). No P2O5 value verified from ecoinvent/Fertilizers Europe |
| K2O production | ~0.5-0.7 kg CO2e/kg K2O | K |

Net-of-N2O point: if digestate N is replaced by synthetic N, the field N2O from the synthetic N is partly offset by N2O that the avoided digestate/manure N would have emitted (IPCC applies the same EF1 to organic N). The defensible debit is therefore **production emissions (3.3 EU to 6.7 global/NA) plus differences in NH3-driven indirect N2O**, with the full 4.3 as an upper-bound sensitivity.

### 3.3 Surplus regions and land-application emissions
- Land-application NH3 and N2O, digestate versus raw slurry: an EC "manure processing/application" synthesis cited by search results (S, authors and n=126 not confirmed) reports NH3 "not significantly different between digestates and raw slurry"; separated liquid fractions 18% lower; N2O 25% lower for digestate (P>0.05) and 46% lower for solid fraction (P<0.01). A different EC fiche (38 papers) reports a non-significant N2O increase with AD. Petrova, Pekrun, Möller 2021, Agronomy 11:2215 (A): separation lowered N2O in the order raw digestate > separated liquid > separated solid in 2016; "Digestate processing did not generally reduce emissions". Food-based digestate field trials (Bangor, S): NH3 ~40% of applied N versus ~30% for slurry. **Net: no robust digestate advantage or disadvantage; evidence is mixed.**
- Application technique matters more: median NH3 EF 48% (broadcast), 21% (band/incorporated), 11% (injected) of TAN (S, EC fiche).
- Surplus regions (NL, Flanders, Brittany, Po Valley, Denmark): removal of nutrients avoids nitrate leaching, NH3 and eutrophication, and fertilizer replacement may be zero (Isometric §8.2 logic). These are environmental co-benefits, not CDR; I found no quantified literature in this session on avoided-damage per kg N removed. Flag for a separate review.

---

## 4. Digestate injection in practice

- **Vaulted Deep**: Kansas (Hutchinson) permitted slurry-injection well, plus Terminal Island (Los Angeles) biosolids well. Isometric supplier page (V, https://registry.isometric.com/supplier/spl_1H43SYY631S0Z8YR): feedstocks "biosolids, livestock and agricultural waste, paper sludge, and others"; Great Plains Organic Waste Sequestration (Kansas) 74,920 certificates issued; TIRE 2,774.85; buffer pool 1,558.969, 0 used. For TIRE: "Vault only credits those volumes over the baseline." **Digestate is not named on Vaulted Deep's website or Isometric page.** Well class is not stated on any page I read (Class V was your premise; unconfirmed; one trade report says EPA permits wells 3,000-7,500 ft deep, S). The company site gives no efficiency figure; an aggregator claims ">95% carbon efficiency" and ">10,000 years" (S, UNVERIFIED); Isometric project page says "permanently (10,000+ years)". The Biomass Geological Storage protocol requires ">1000 yr estimated" storage (V extraction).
- **Isometric protocol**, Biomass Geological Storage (https://registry.isometric.com/protocol/biomass-geological-storage, extraction): feedstocks include "animal waste, biosolids, agricultural or forestry residues"; baseline §7.2: "The baseline scenario for biomass geological storage projects assumes the activities associated with The Project do not take place"; counterfactual: "The counterfactual is the CO2 stored in the biomass feedstock that would have remained durably stored in the biomass"; leakage §8.5.4: "For a biomass project, replacement emissions must be considered as a minimum"; permeable reservoir storage is Low Risk with a 5% buffer pool (Appendix 2). Soil carbon and digestate are not mentioned in the protocol page itself; they are handled in the Feedstock Accounting Module (section 2.4, 3.1). The module's §4.1 treats "post anaerobic digestion manure" as residues "that have fulfilled their purpose for energy generation", i.e. not prohibited. The module's pages were truncated in my reads (final ~10k characters of v1.3 not read).
- **Puro.earth**: Geologically Stored Carbon methodology (Edition 2024) covers CO2 from sustainably sourced biogenic material (BECCS, fermentation); I found no slurry-injection or manure-baseline rule in a Puro document (S). A Danish example (BioCarb Solution) captures CO2 from manure biogas plants for shipping (S, not injection).
- No project or protocol found that injects **digested** manure. All evidence for slurry injection is for raw/minimally processed waste.

---

## 5. Net CDR efficiency estimates (per unit feed C; feed C = 1.00)

### 5.1 Structure and assumptions (all judgement; to be replaced by tool parameters)
- f_bio = 0.35 of feed C to biogas (range 0.20-0.50); CO2 share of biogas C 0.43; digestate C = 0.65.
- Vent-CO2 capture 0.95; flue-gas capture after on-site combustion 0.90.
- Process, transport, compression and storage factor 0.90 on stored C (this is the tool's existing 90% injection efficiency, applied unchanged; I did not derive it; it was meant for raw slurry).
- Digestate retention from the interpolated Yasso07 curve: 15 yr 34%, 50 yr 13%, 100 yr 3.5%. **Central horizon 50 yr** (Isometric fallback); sensitivity 15 yr and 100 yr.
- Fertilizer: digestate N = 0.116 kg per kg feed C x MFE 0.6 (digestate) or 0.45 (raw); N production EF 3.3 (EU) to 6.7 (NA); P2O5 = 0.4 x N mass x 1.2 kg CO2e/kg; K ignored (<0.003). 1 kg C = 3.667 kg CO2, so debits in kg CO2e are divided by 3.667.
- Not counted: avoided storage CH4, avoided fossil gas from RNG (energy credit, not CDR), digestate fugitive CH4 and NH3, energy for capture. Digestate handling C loss (12-17% unaccounted in Tampio) is ignored; it would lower all digestate-based rows by up to ~0.1.

### 5.2 Results

| Pathway | Gross stored | After 0.90 | SOC debit (50 yr; 15 yr / 100 yr) | Fertilizer debit (central; EU-NA range) | **Net (central)** | Net range |
|---|---|---|---|---|---|---|
| (a) RNG vent CO2 + whole digestate | 0.15 + 0.65 = 0.79 | 0.71 | 0.08 (0.22 / 0.02) | 0.06 (0.04-0.11) | **0.57** | 0.38-0.67 |
| (b) All biogas C captured + whole digestate | 0.32 + 0.65 = 0.97 | 0.87 | 0.08 (0.22 / 0.02) | 0.06 (0.04-0.11) | **0.73** | 0.54-0.82 |
| (c1) RNG vent CO2 + solid fraction only (liquid to field) | 0.15 + 0.23 = 0.37 | 0.34 | 0.04 (solids ~1.3x more recalcitrant; 0.09 / 0.01) | 0.01 (0.01-0.02) | **0.29** | 0.22-0.32 |
| (c2) All biogas C + solid fraction only | 0.32 + 0.23 = 0.55 | 0.49 | 0.04 | 0.01 | **0.44** | 0.37-0.48 |
| Raw slurry injection, no AD (existing 90% pathway) | 1.00 | 0.90 | 0.10 (range 0.03-0.30; 15 yr ~0.30; 100 yr ~0.03) | 0.08 (0.06-0.12) | **0.72** | 0.50-0.85 |
| Raw slurry injection, tool's current assumption | 1.00 | 0.90 | 0 | 0 | 0.90 | - |

Show SOC-forgone and fertilizer debits as separate columns in the tool, as requested. In surplus regions (fertilizer replacement set to zero) add back the fertilizer column: (a) 0.63, (b) 0.79, raw 0.80.

Raw-slurry SOC debit basis: raw manure retains somewhat less than digestate per unit applied C (Tampio 43% vs 48-50% at 5 yr) but there is no AD C loss, so per feed C raw is ~equal at long horizons (Tampio, Thomsen) and up to ~2x digestate in the Karki/Daisy runs (S). Central 0.10 of feed C at 50 yr (about 13% x 0.8, rounded); the 0.30 upper end corresponds to the 15 yr horizon. This debit is not yet in the tool and shifts the raw-slurry pathway from 90% to roughly 70%.

Reading the table: the SOC debit is modest at 50-100 yr and dominated by the horizon choice; the fertilizer debit is smaller than SOC at long horizons but is more defensible (an observable market displacement under Isometric's own rules). Pathway (c) is limited by how little C the solids carry; the carbon-credit case for (c) rests on unverified C separation efficiency and on an assumption that liquid-fraction C (labile) causes no stored-C debit.

---

## 6. Parameter table

| Parameter | Value | Range | Source | Verified |
|---|---|---|---|---|
| Feed C to biogas, cattle manure+straw | 23-27% | - | Tampio 2024 | Y |
| Feed C to biogas, cattle faeces lab | 46% | - | Thomsen 2013 abstract | A/S |
| Feed C to biogas, cattle slurry (central) | 35% | 20-50% | judgement spanning above | N |
| Feed C to biogas, pig slurry | 45% | 30-60% | K | N |
| Biogas CH4 share of C | 57% | 55-60% | K | N |
| Digestate TS / C / N (leach-bed) | 12.5-12.9% / 46% TS / 2.0% TS | - | Tampio Table 2 | Y |
| Digestate lignin | 133-156 g/kg TS | - | Tampio Table 2 | Y |
| Slurry digestate DM / C/N | 3-7% / 5-10 | - | K | N |
| Recalcitrant (E+N) C share, digestate | 37-40% (feed 26%) | - | Tampio | Y |
| Digestate C retained, 5 yr | 48-50% | - | Tampio (Yasso07) | Y |
| Digestate C retained, 25 yr | 20-27% | - | Tampio | Y |
| Digestate C retained, 100 yr | 3-4% | - | Tampio | Y |
| Digested faeces C retained 1-2 yr | 76% (faeces 48%) | - | Thomsen abstract | A/S |
| Long-term retention per C originally in feed | 12-14% | - | Thomsen abstract | A/S |
| Long-term retention, digestate solids | 26-54% of applied; 12-16% of pre-AD C | - | Nyang'au 2022 abstract | A |
| Daisy 50 yr retention, digested / non-digested | 35% / 41% (loamy sand) | - | Karki 2013 poster | S |
| Digestion vs raw manure SOC, meta-analysis | non-significant | - | Liu 2020 via EC fiche | S |
| Reactor + incubation C remaining | 63.0% vs 62.2% raw | - | Reinhold 1991 via Möller slide | S |
| Solid fraction share of N / P / K (screw press, digestate) | 15% / 25% / 10% | - | AFBI | S |
| Solid fraction share of C (screw press, digestate) | 35% | 20-60% | judgement | N |
| N fertilizer production EU AN | 3.32 kg CO2e/kg N | NA 6.71 | Hoxha & Christensen 2019 | Y |
| N2O from synthetic N | ~4.3 kg CO2e/kg N | - | IPCC EF1 1%, AR6 GWP | N |
| P2O5 production | ~1.2 kg CO2e/kg | 1.0-2.0 | K / S cross-check | N |
| Digestate N MFE | 0.6 (raw 0.45) | 0.5-0.7 | K | N |
| Digestate vs raw slurry NH3 | no sig. difference | - | EC fiche | S |
| Isometric counterfactual horizon | 15 yr, 50 yr fallback | - | Feedstock module §3.3 | Y (tool-extracted text) |
| Isometric manure replacement | synthetic fertilizer, most limiting NPK | - | Feedstock module §4.3.2, §8.1 | Y (tool-extracted text) |
| Vaulted Deep durability / efficiency claim | >1000 yr (protocol); 10,000+ yr; >95% | - | Isometric; aggregator | Partly; efficiency S |

## 7. Open uncertainties

1. **SOC definition gap (largest).** Yasso07 gives 3-4% of applied C at 100 yr; "stable" or "long-term retention" in Thomsen / Tampio / Nyang'au gives 12-23% of feed C. These need reconciling with a fresh C-TOOL or RothC run for Danish/Dutch slurry digestate before the tool hardcodes a number.
2. **Horizon and Isometric reading.** Whether Isometric would accept a 15-yr, 50-yr or negligibility argument for digestate SOC. Confirm with Isometric/Frontier; read the full module text (my read lost the last ~10k characters, and the extraction summaries could mis-paraphrase §3.3).
3. **AD does or does not change SOC per feed C.** Daisy (raw better, ~2x), Yasso07 (digestate better per applied C, similar per feed C), Thomsen (similar), Liu meta-analysis (no difference). No field trial in hand that measures it.
4. **Slurry-specific C balance.** The only verified balance is a straw-rich leach-bed system, not slurry digesters. Need cattle and pig slurry C balance from full-scale plants (Danish/German), plus digestate residual methane and storage CH4.
5. **C partition on separation.** No verified C share in solids; should be measured or sourced (Hjorth 2010 full text, Møller et al. 2000 and 2004).
6. **Whether any registry will credit digested manure injection.** No project or protocol found; Vaulted Deep does not name digestate; well class (Class V vs other) unconfirmed; water-to-carbon ratio of whole digestate (~20 kg C/t) is a practical and cost problem that makes (c) the realistic variant.
7. **Fertilizer debit inputs.** MFE, P2O5 and K2O EFs, GWP convention and whether to include field N2O are not verified. Surplus-region zero-replacement rule is Isometric-specific (§8.2).
8. **Not in scope here but material:** avoided storage CH4 and avoided fossil gas credits (would lift net efficiency or be additional claims), double counting of RNG fossil displacement, digestate handling losses (12-17% unaccounted in Tampio), co-benefit quantification in surplus regions.
9. Paywalled primaries not read: Thomsen 2013, Möller 2015, Hjorth 2010, Liu 2020, Möller & Müller 2012, Schouten 2012 full text, Ablieieva 2024 full text.

## Links
- Tampio et al. 2024 (open access, read in full): https://doi.org/10.1016/j.scitotenv.2024.172083
- Thomsen et al. 2013: https://doi.org/10.1016/j.soilbio.2012.11.006 (abstract page blocked; figures from search summary)
- Möller 2015: https://doi.org/10.1007/s13593-015-0284-3 (not read)
- Nyang'au et al. 2022: https://doi.org/10.1016/j.scitotenv.2022.158177 (abstract read at https://orgprints.org/id/eprint/45692)
- Schouten et al. 2012: https://doi.org/10.1111/j.1757-1707.2012.01163.x
- Karki et al. 2013 poster: https://scisoc.confex.com/crops/2013am/webprogram/Paper79656.html
- Hjorth et al. 2010: https://doi.org/10.1051/agro/2009010
- Liu et al. 2020: https://doi.org/10.1016/j.scitotenv.2020.141003
- Barłóg et al. 2020: https://doi.org/10.3390/agronomy10030379
- Petrova et al. 2021: https://doi.org/10.3390/agronomy11112215
- Hoxha & Christensen 2019 (IFS 805): https://www.fertilizerseurope.com/wp-content/uploads/2020/01/The-carbon-footprint-of-fertilizer-production_Regional-reference-values.pdf
- Isometric Biomass Geological Storage protocol: https://registry.isometric.com/protocol/biomass-geological-storage
- Isometric Biomass Feedstock Accounting module v1.3: https://registry.isometric.com/module/biomass-feedstock-accounting/1.3
- Isometric Vaulted Deep supplier page: https://registry.isometric.com/supplier/spl_1H43SYY631S0Z8YR
- Möller slide deck (Reinhold 1991, Thomsen 2013 figure): https://www.organicresearchcentre.com/wp-content/uploads/2022/01/Moller-other-AD-ORC-Conf-2013.pdf
