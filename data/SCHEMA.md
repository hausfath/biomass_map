# Data Schema — BiCRS Map (authoritative; all data subagents MUST conform)

All quantities in **metric tons (t)** or **million tonnes (Mt)** as specified per field.
Oven-dry-tons abbreviated **odt**. CO₂ quantities in **Mt CO₂/yr** unless noted.

Every numeric estimate MUST carry an uncertainty range and a source. Prefer the sources
named in PLAN.md §6. If you must estimate, say so and give the method.

---

## 1. feedstocks — array of region objects

Write to the file path given in your task prompt. Top-level = JSON array of objects:

```json
{
  "id": "USA",                      // ISO3 for countries; "US-California" for US states
  "name": "United States",
  "level": "country",               // "country" | "subnational"
  "parent": null,                   // null for countries; "USA" for US states
  "centroid": [lon, lat],           // approx, for point fallback / labels

  "ag_residues_odt_mt": {           // agricultural residues, Mt oven-dry-tons/yr (recoverable)
    "value": 180.0, "low": 120.0, "high": 240.0,
    "source": "FAOSTAT 2022 crop production × residue ratios (Slade et al. 2014 recoverable fraction)",
    "notes": "cereal straw + corn stover + sugarcane bagasse, 40% sustainable removal cap"
  },
  "forestry_residues_odt_mt": { "value": ..., "low": ..., "high": ..., "source": "...", "notes": "..." },

  "msw_total_mt": { "value": ..., "low": ..., "high": ..., "source": "World Bank What a Waste 2.0 (2018)", "notes": "" },
  "msw_biogenic_frac": { "value": 0.61, "source": "EIA/Kaplan (US); thesis §1.3", "notes": "US ~0.61, EU ~0.50" },
  "msw_treatment": { "wte_pct": 12, "landfill_pct": 54, "dump_pct": 20, "recycle_compost_pct": 14, "source": "World Bank What a Waste 2.0" },

  "animal_manure_odt_mt": { "value": ..., "low": ..., "high": ..., "source": "FAO livestock × manure factors / IEA biogas 2020", "notes": "dry-matter basis" },
  "human_wwtp_odt_mt":   { "value": ..., "low": ..., "high": ..., "source": "IEA biogas outlook 2020", "notes": "sewage sludge dry solids" },

  "nutrient_status": "moderate",    // "low" | "moderate" | "excess"  (excess = high fertilizer use, e.g. China, NL — favors burial/removal-tolerant pathways)
  "nutrient_status_source": "FAO fertilizer use per ha; thesis §2.2 (China excess example)",

  "dominant_feedstock": "ag_dry",   // "ag_dry" | "forestry_woody" | "msw" | "manure_wet" | "mixed"
  "feedstock_density": "diffuse",   // "concentrated" | "diffuse"  (diffuse ag favors bio-oil/biochar)

  "notes": "free text caveats"
}
```

### CDR potential is DERIVED later (not stored here)
Do NOT compute CDR potential — the engine derives it from these tonnages × pathway efficiency.
Just give accurate biomass tonnages.

### Methodology hints
- **Ag residues:** FAOSTAT production of major crops → residue-to-product ratio (RPR) → recoverable fraction (~40% sustainable, leave rest for soil). Major: wheat/rice/maize straw, corn stover, sugarcane bagasse/tops, soy, cotton. Slade et al. 2014 / IEA 2022 give country/region totals to cross-check; global recoverable ~2.8–4.0 Gt odt.
- **Forestry residues:** roundwood + processing residues (FAO FRA). Slade et al. 2014 country/region totals.
- **MSW:** World Bank What a Waste 2.0 has per-country total generation + treatment shares + composition. Biogenic fraction: US 0.61, EU ~0.50, varies elsewhere (more organic in LMICs → higher biogenic).
- **Manure/human:** IEA Outlook for Biogas (2020) gives regional biogas potential; convert or cite tonnage. FAO livestock heads × excretion factors as fallback.

---

## 2. storage — array of objects (two kinds, distinguished by `kind`)

```json
// Existing/operational CO2 storage or injection site
{ "kind": "site", "name": "Sleipner", "country": "NOR", "lat": 58.4, "lon": 1.9,
  "status": "operational",            // "operational" | "construction" | "planned"
  "storage_type": "saline",           // "saline" | "depleted_og" | "basalt" | "eor"
  "capacity_mtpa": 1.0, "source": "Global CCS Institute Facilities Database 2023", "notes": "" }

// Basin-level theoretical storage potential
{ "kind": "basin", "name": "US Gulf Coast saline aquifers", "country": "USA",
  "lat": 29.0, "lon": -94.0,          // centroid
  "storage_type": "saline",
  "capacity_gt": 500, "confidence": "high",   // "high" | "medium" | "low"
  "source": "US DOE NATCARB / NETL Carbon Storage Atlas", "notes": "P50 estimate" }
```

Cover at minimum: North America (NATCARB), Europe (CO2StoP), China, Australia, Brazil,
India, Japan, Middle East, plus all operational CCS storage sites globally.

---

## 3. facilities — array of retrofit-candidate point objects

```json
{ "name": "Drax Power Station", "type": "bioenergy",   // "pulp_paper" | "ethanol" | "wte" | "bioenergy" | "biogas_ad"
  "country": "GBR", "lat": 53.7, "lon": -0.99,
  "capacity_note": "2.6 GW biomass",
  "est_biogenic_co2_mtpa": { "value": 12.0, "low": 10.0, "high": 14.0 },
  "retrofit_score": "high",           // "high" | "medium" | "low" — ease/attractiveness of CCS retrofit
  "operator": "Drax Group",
  "source": "company reports / IEA Bioenergy",
  "notes": "" }
```

Prioritize the largest biogenic-CO₂ point sources and existing BiCRS projects named in the
thesis (Stockholm Exergi, Orsted, CO280, Celsio, Charm, Vaulted, Arbor, ADM, Super6, etc.),
then large pulp & paper mills, WtE plants, ethanol plants, and bioenergy stations by region.
Aim for breadth across regions, not exhaustive within one.

---

## Citation rules
- `source` is REQUIRED on every estimate object. Name the dataset + year.
- If a value is your own calculation, source = "calc: <method>" and add `notes`.
- Never invent a precise number you can't ground — give a range and label it an estimate.
