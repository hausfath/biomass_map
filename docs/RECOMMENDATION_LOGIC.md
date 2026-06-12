# Best-Use-of-Biomass Recommendation Logic

A flow chart of the deterministic decision tree in `scripts/build_recommendations.py`
(`decide()` plus the storage-access pre-step and the excess-nutrient post-step). The tree is
**first-match-wins** on the region's dominant feedstock. It encodes Frontier's KPI priority —
**CDR efficiency › emissions-avoiding co-product › other co-benefits** — modulated by storage
proximity, feedstock density, nutrient status, retrofit availability, and AD maturity.

Each teal leaf shows the **recommended** pathway (first line) and the *runner-up* (second line).
After the tree, a post-step can swap the runner-up to biomass burial in excess-nutrient regions.

## Inputs (per region)

| Input | Values | Source |
|---|---|---|
| `dominant_feedstock` | manure_wet · msw · forestry_woody · ag_dry · mixed | feedstock data |
| `feedstock_density` | concentrated · diffuse | feedstock data |
| `storage_access` | good · moderate · poor | computed (see pre-step) |
| `nutrient_status` | low · moderate · excess | feedstock data |
| `has_pp_or_bioenergy` | true / false — an existing, retrofittable pulp-&-paper or bioenergy mill physically in the region | facilities (point-in-polygon) |
| `manure_ad_preferred` | true / false — region is in a mature anaerobic-digestion country (e.g. Europe) | country list |

### Pre-step — storage access
Take the **more favourable** of (a) great-circle distance from the region centroid to the
nearest operational CCS site or high/medium-confidence basin, and (b) the best in-country
qualifying storage (handles large-country centroid bias). Then:

```
good      = within 500 km of qualifying storage  (or a high-confidence in-country basin / operational site)
moderate  = within 1000 km
poor      = otherwise, or only low-confidence storage nearby
```
`dry_removal` (the preferred distributed dry-biomass pathway) = **injection** if `storage = good`,
else **bio-oil** (pyrolysis densifies carbon, so bio-oil wins only when wells are far).

## Flow chart

```mermaid
flowchart TD
    Start([Region]) --> DOM{dominant<br/>feedstock?}

    %% ---------- 1. WET MANURE ----------
    DOM -->|manure_wet| M{mature-AD<br/>country?}
    M -->|yes e.g. Europe| Mad["AD + CCS<br/>runner: injection near / biochar"]
    M -->|no| Mnear{storage<br/>near?}
    Mnear -->|good or moderate| Minj["Injection<br/>runner: AD + CCS"]
    Mnear -->|poor| Mad2["AD + CCS<br/>runner: biochar"]

    %% ---------- 2. MSW ----------
    DOM -->|msw| Wnear{storage<br/>near?}
    Wnear -->|good or moderate| Wwte["WtE + CCS<br/>runner: burial"]
    Wnear -->|poor| Wbur["Biomass burial<br/>runner: bio-oil"]

    %% ---------- 3. WOODY  OR  DRY-AG & CONCENTRATED ----------
    DOM -->|forestry_woody<br/>OR ag_dry & concentrated| Csa{storage<br/>access?}
    Csa -->|good| Cmill{existing pulp/<br/>bioenergy mill?}
    Cmill -->|yes| Cpp["BECCS pulp & paper<br/>runner: injection"]
    Cmill -->|no| Cbe["BECCS<br/>runner: injection"]
    Csa -->|moderate| Cbe2["BECCS<br/>runner: bio-oil"]
    Csa -->|poor| Cnut{nutrient<br/>status?}
    Cnut -->|excess| Cbur["Biomass burial<br/>runner: bio-oil"]
    Cnut -->|else| Cbo["Bio-oil<br/>runner: biochar"]

    %% ---------- 4. DRY-AG & DIFFUSE ----------
    DOM -->|ag_dry & diffuse| Dsa{storage<br/>access?}
    Dsa -->|good| Dinj["Injection<br/>runner: bio-oil"]
    Dsa -->|poor & excess<br/>nutrients| Dbur["Biomass burial<br/>runner: bio-oil"]
    Dsa -->|else<br/>moderate / poor| Dbo["Bio-oil<br/>runner: biochar"]

    %% ---------- 5. MIXED / FALLBACK ----------
    DOM -->|mixed| Fsa{storage &<br/>retrofit?}
    Fsa -->|good + retrofit| Fbe["BECCS<br/>runner: injection"]
    Fsa -->|poor| Fbur["Biomass burial<br/>runner: bio-oil"]
    Fsa -->|else| Fbe2["BECCS<br/>runner: bio-oil"]

    %% ---------- POST-STEP ----------
    Mad & Minj & Mad2 & Wwte & Wbur & Cpp & Cbe & Cbe2 & Cbur & Cbo & Dinj & Dbur & Dbo & Fbe & Fbur & Fbe2 --> NUT{recommended is<br/>BECCS / bio-oil / injection<br/>AND nutrient = excess?}
    NUT -->|yes| Swap["swap runner-up to Biomass burial<br/>removal-consistent; bio-oil would<br/>return nutrients to surplus soils"]
    NUT -->|no| Keep["keep runner-up"]
    Swap --> Done([Recommended + runner-up])
    Keep --> Done

    classDef rec fill:#15967f,stroke:#0d5530,color:#eafffb;
    classDef q fill:#1c2730,stroke:#2a3742,color:#e8edf1;
    class Mad,Minj,Mad2,Wwte,Wbur,Cpp,Cbe,Cbe2,Cbur,Cbo,Dinj,Dbur,Dbo,Fbe,Fbur,Fbe2,Swap rec;
    class DOM,M,Mnear,Wnear,Csa,Cmill,Cnut,Dsa,Fsa,NUT q;
```

## Notes & exclusions

- **Wet feedstocks never combust** — manure/biosolids route to injection or AD+CCS only.
- **Injection vs bio-oil** for dry residues turns on storage proximity: injection (>90% efficiency,
  cheaper on balance) wins where wells are near; bio-oil (~45%) wins at distance because
  pyrolysis densifies the carbon for cheaper transport.
- **AD+CCS** is preferred over injection for manure in mature-AD regions (Europe), where it
  retrofits existing biogas plants. RNG+CCS is **not** excluded — it is a viable offtake option.
- **Never recommended** (flagged): purpose-grown energy crops; corn-ethanol+CCS (US-scoped flag).
- The KPI score that orders the ranked list (and colours the map) is
  `60·CDR-efficiency + 25·(energy co-product) + 15·(co-benefit) − 10·(needs storage but poor access)`.

> Keep this chart in sync with `decide()` in `scripts/build_recommendations.py` if the logic changes.
