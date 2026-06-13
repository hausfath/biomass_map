#!/usr/bin/env python3
"""
Shared BiCRS recommendation core — pathway constants, the decision tree, KPI scoring,
CDR-potential math, ranking, rationale/caveat text, and geometry helpers.

Imported by both the global engine (scripts/build_recommendations.py) and the US
county engine (scripts/us/build_us_recommendations.py) so the two never diverge and
docs/RECOMMENDATION_LOGIC.md stays accurate for both. The *inputs* differ (each engine
computes storage_access / density its own way); the logic that turns those inputs into a
recommendation lives here.
"""

import math

# --------------------------------------------------------------------------
# Pathway constants (thesis sec 2.1 / ENGINE_SPEC.md)
# --------------------------------------------------------------------------
ODT_TO_CO2 = 1.47  # tCO2 per oven-dry-ton of biomass carbon basis

PATHWAYS = {
    "beccs": {
        "label": "BECCS (heat/electricity)",
        "cdr_efficiency": 0.80,
        "cost_band": "$200-225 (to <$100 at scale)",
        "co_product": "energy",
        "needs_geologic_storage": True,
    },
    "beccs_pp": {
        "label": "BECCS pulp & paper",
        "cdr_efficiency": 0.80,
        "cost_band": "$200-225",
        "co_product": "energy/none",
        "needs_geologic_storage": True,
    },
    "wte_ccs": {
        "label": "WtE + CCS",
        "cdr_efficiency": 0.55,
        "cost_band": "~$100-200",
        "co_product": "energy",
        "needs_geologic_storage": True,
    },
    "injection": {
        "label": "Biomass waste injection",
        "cdr_efficiency": 0.90,
        "cost_band": "$125-285",
        "co_product": "PFAS destruction",
        "needs_geologic_storage": True,
    },
    "bio_oil": {
        "label": "Bio-oil sequestration",
        "cdr_efficiency": 0.45,
        "cost_band": "$140-360",
        "co_product": "biochar/nutrients",
        "needs_geologic_storage": False,
    },
    "burial": {
        "label": "Biomass burial",
        "cdr_efficiency": 0.90,
        "cost_band": "<$100-150",
        "co_product": "none",
        "needs_geologic_storage": False,
    },
    "ad_ccs": {
        "label": "AD + CCS",
        "cdr_efficiency": 0.37,
        "cost_band": "$145-300",
        "co_product": "low-C fuel",
        "needs_geologic_storage": True,  # partial in spec; treat as needing storage
    },
    "biochar": {
        "label": "Biochar",
        "cdr_efficiency": 0.30,
        "cost_band": "~$100-200",
        "co_product": "nutrients",
        "needs_geologic_storage": False,
    },
}

# Static advantages / disadvantages per pathway (region-specific ones appended later).
PATHWAY_PROFILE = {
    "beccs": {
        "pros": ["High CDR efficiency (~80%)",
                 "Energy co-product (heat/electricity) displaces fossil emissions",
                 "Low durability risk; Frontier's most-preferred pathway"],
        "cons": ["Capital-intensive; works best at large scale",
                 "Not very modular — hard to deploy in distributed settings"],
    },
    "beccs_pp": {
        "pros": ["Retrofits an existing pulp & paper mill — low execution risk, near-term",
                 "High CDR efficiency (~80%) from concentrated recovery-boiler flue gas",
                 "Leverages existing biomass logistics + grid connection"],
        "cons": ["Requires an existing mill to retrofit",
                 "Capture capex on flue gas"],
    },
    "wte_ccs": {
        "pros": ["Captures biogenic CO2 from municipal waste already being combusted",
                 "Energy co-product; handles MSW at urban scale"],
        "cons": ["Only ~50-60% of flue-gas CO2 is biogenic (CDR efficiency ~55%)",
                 "Urban siting and public-acceptance hurdles"],
    },
    "injection": {
        "pros": ["Very high CDR efficiency (>90%)",
                 "Cheaper on balance than bio-oil where wells are near",
                 "PFAS destruction; disposes problematic wet wastes"],
        "cons": ["No emissions-avoiding co-product",
                 "Hauling bulky, less-carbon-dense biomass is costly if wells are far"],
    },
    "bio_oil": {
        "pros": ["Modular and distributed (Charm-style roving model)",
                 "Pyrolysis densifies the carbon, so it is cheap to haul to distant wells",
                 "Returns biochar and nutrients to fields",
                 "Low durability risk"],
        "cons": ["Lower CDR efficiency (~45%)",
                 "Higher $/t than injection where storage is proximate"],
    },
    "burial": {
        "pros": ["Very high CDR efficiency (>90%)",
                 "Simple and low-cost; needs no geologic CO2 storage",
                 "Works for distributed biomass"],
        "cons": ["Durability still being validated (Frontier prepurchase, not offtake)",
                 "No emissions-avoiding co-product; nutrient-export risk with ag residues"],
    },
    "ad_ccs": {
        "pros": ["Suits wet feedstock; mature technology",
                 "Returns nutrients to fields",
                 "RNG co-product displaces fossil gas; viable offtake option"],
        "cons": ["Low CDR efficiency (~30-44%)",
                 "Carbon is split between the RNG (fuel) and CDR streams, capping CDR"],
    },
    "biochar": {
        "pros": ["Returns nutrients to soils, improving yields",
                 "Distributed and storage-independent; simple and near-term"],
        "cons": ["Low CDR efficiency (~30%)",
                 "Durability and verification questions; Frontier's lower-preference pathway"],
    },
}

# Caveats / flags text (spec)
BURIAL_CAVEAT = (
    "Durability still being validated (Isometric 2024 protocol projects 1,000-yr); "
    "Frontier pursuing via prepurchase not offtake."
)

# Countries with mature anaerobic-digestion sectors, where most manure is already routed to
# digesters. There, AD+CCS retrofits existing biogas infrastructure and is preferred over
# biomass injection for wet-manure feedstock. (Elsewhere -- e.g. the US, where on-farm AD is
# uncommon -- injection remains the lead for manure.)
HIGH_AD_PENETRATION = {
    "DEU", "DNK", "NLD", "BEL", "ITA", "AUT", "FRA", "GBR", "IRL", "CZE",
    "SWE", "FIN", "CHE", "POL", "SVK", "HUN", "LUX", "ESP",
}

# Large, internally heterogeneous countries: a single national recommendation is a
# rollup and masks strong sub-national variation in feedstock, storage, and nutrients.
LARGE_HETEROGENEOUS = {"USA", "CHN", "IND", "RUS", "BRA", "CAN", "AUS"}
# Subset for which we actually map subnational cells (so the caveat can point users there).
HAS_SUBNATIONAL = {"USA", "CAN", "IND", "CHN"}

# --------------------------------------------------------------------------
# Retrofit-only pathways. BECCS pulp&paper, WtE+CCS, and AD+CCS only make sense as
# retrofits of existing facilities today, so they are recommendable (and only appear in
# the ranked options) where the region is within the typical feedstock-procurement radius
# of an existing facility of the matching type. Plain BECCS (heat/electricity) is NOT gated
# — it can be greenfield. Radii are scope inputs; the scope engines compute the per-region
# availability flags `avail = {"pp","wte","ad"}` and pass them to decide()/build_ranked().
#   pulp_paper ~150 km (pulpwood haul ~80-93 mi); wte ~50 km (local/regional MSW catchment);
#   biogas_ad ~15 km (wet-manure haul is short) for discrete digesters — regional AD clusters
#   carry their own coverage radius reflecting the area of dense capacity they aggregate.
PROC_RADIUS_KM = {"pulp_paper": 150.0, "wte": 50.0, "biogas_ad": 15.0}
AD_MIN_CAP_MTPA = 0.01   # cumulative AD biogenic-CO2 capacity within reach to enable AD+CCS
# pathway key -> avail flag it is gated on
RETROFIT_GATE = {"beccs_pp": "pp", "wte_ccs": "wte", "ad_ccs": "ad"}


def _avail(avail):
    """Normalize the per-region retrofit-availability flags (default all available)."""
    if avail is None:
        return {"pp": True, "wte": True, "ad": True}
    return {"pp": bool(avail.get("pp")), "wte": bool(avail.get("wte")), "ad": bool(avail.get("ad"))}


def manure_ad_preferred(region):
    """True where mature AD infrastructure makes AD+CCS the lead manure pathway."""
    return region_country(region) in HIGH_AD_PENETRATION


# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------
def haversine_km(lon1, lat1, lon2, lat2):
    """Great-circle distance in km between two (lon, lat) points."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def num(field, default=0.0):
    """Safely pull a numeric .value from a {value, low, high, ...} estimate block."""
    if not isinstance(field, dict):
        return default
    v = field.get("value")
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def region_country(region):
    """ISO3 country used to match facilities. US states carry parent='USA'."""
    if region.get("level") == "country":
        return region.get("id")
    return region.get("parent") or region.get("id")


# --------------------------------------------------------------------------
# Point-in-polygon (ray casting) — used to assign facilities to states/counties,
# and (US engine) to test county centroids against storage-basin polygons.
# --------------------------------------------------------------------------
def _point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-300) + xi):
            inside = not inside
        j = i
    return inside


def _point_in_polygon(x, y, rings):
    """rings = [exterior, hole1, ...]; inside exterior and outside all holes."""
    if not rings or not _point_in_ring(x, y, rings[0]):
        return False
    for hole in rings[1:]:
        if _point_in_ring(x, y, hole):
            return False
    return True


def _point_in_geometry(x, y, geom):
    t = geom.get("type")
    if t == "Polygon":
        return _point_in_polygon(x, y, geom["coordinates"])
    if t == "MultiPolygon":
        return any(_point_in_polygon(x, y, poly) for poly in geom["coordinates"])
    return False


# --------------------------------------------------------------------------
# Decision tree (first match wins)
# --------------------------------------------------------------------------
def decide(region, storage_access, has_retrofit, avail=None):
    dom = region.get("dominant_feedstock")
    density = region.get("feedstock_density")
    nutrient = region.get("nutrient_status")
    near = storage_access in ("good", "moderate")
    av = _avail(avail)  # {pp, wte, ad}: is a retrofittable facility of each type within reach?

    # Preferred distributed-removal pathway for DRY biomass, set by storage proximity.
    # Frontier is bullish on Vaulted-style slurry injection: it handles the same dry
    # residues as bio-oil, has higher CDR efficiency (>90% vs ~45%), and is cheaper on
    # balance -- so where geologic storage (injection wells) is PROXIMATE it beats bio-oil.
    # Bio-oil's edge is only at distance: pyrolysis densifies the carbon, making the
    # less-carbon-dense raw biomass cheaper to haul to far-off wells. So:
    #   good storage (proximate) -> injection ;  moderate/poor (distant) -> bio-oil.
    dry_removal = "injection" if storage_access == "good" else "bio_oil"

    # 1. wet manure. AD+CCS only where existing AD capacity is within reach (retrofit-only).
    if dom == "manure_wet":
        # Where manure already flows to anaerobic digesters (e.g. Europe) AND there is AD
        # capacity nearby to retrofit, AD+CCS retrofits that infrastructure and leads.
        if av["ad"] and manure_ad_preferred(region):
            return "ad_ccs", ("injection" if near else "biochar")
        # Otherwise injection leads near storage (US-style: on-farm AD uncommon / none nearby).
        if near:
            return "injection", ("ad_ccs" if av["ad"] else "biochar")
        # Far from storage: AD+CCS only if there is AD to retrofit; else distributed biochar.
        if av["ad"]:
            return "ad_ccs", "biochar"
        return "biochar", "injection"

    # 2. MSW. WtE+CCS only where an existing WtE plant is within reach (retrofit-only).
    if dom == "msw":
        if near and av["wte"]:
            return "wte_ccs", "burial"
        return "burial", "bio_oil"

    # 3. forestry_woody OR (ag_dry & concentrated)
    if dom == "forestry_woody" or (dom == "ag_dry" and density == "concentrated"):
        if storage_access == "good":
            # BECCS leads; pulp&paper retrofit only where an existing mill is within reach.
            if av["pp"]:
                return "beccs_pp", dry_removal
            return "beccs", dry_removal
        elif storage_access == "moderate":
            return "beccs", "bio_oil"
        else:  # poor
            if nutrient == "excess":
                return "burial", "bio_oil"
            return "bio_oil", "biochar"

    # 4. ag_dry & diffuse
    if dom == "ag_dry" and density != "concentrated":
        if storage_access == "good":
            # Diffuse crop residues with proximate wells -> injection over bio-oil.
            return dry_removal, "bio_oil"
        elif nutrient == "excess" and storage_access == "poor":
            return "burial", "bio_oil"
        return "bio_oil", "biochar"

    # 5. mixed / fallback
    if storage_access == "good" and has_retrofit:
        return "beccs", "injection"
    elif storage_access == "poor":
        return "burial", "bio_oil"
    return "beccs", "bio_oil"


# --------------------------------------------------------------------------
# KPI score
# --------------------------------------------------------------------------
def kpi_score(pathway_key, storage_access):
    p = PATHWAYS[pathway_key]
    eff = p["cdr_efficiency"]
    co = p["co_product"]

    # co-product term
    if co == "energy" or co == "energy/none":
        co_term = 1.0
    elif co in ("low-C fuel",):
        co_term = 0.5
    else:
        co_term = 0.0

    # co-benefit term: PFAS / nutrients / methane-avoidance present
    co_benefit = 0
    if co in ("PFAS destruction", "biochar/nutrients", "nutrients", "low-C fuel"):
        co_benefit = 1

    score = 60 * eff + 25 * co_term + 15 * co_benefit

    if p["needs_geologic_storage"] and storage_access == "poor":
        score -= 10

    return round(score)


# --------------------------------------------------------------------------
# CDR potential (Mtpa)
# --------------------------------------------------------------------------
def cdr_potential_mtpa(region, pathway_key):
    eff = PATHWAYS[pathway_key]["cdr_efficiency"]
    ag = num(region.get("ag_residues_odt_mt"))
    forestry = num(region.get("forestry_residues_odt_mt"))
    manure = num(region.get("animal_manure_odt_mt"))
    wwtp = num(region.get("human_wwtp_odt_mt"))
    msw = num(region.get("msw_total_mt"))
    biofrac = num(region.get("msw_biogenic_frac"), default=0.5)
    dom = region.get("dominant_feedstock")

    # Feedstock basis is set by the region's dominant feedstock, not the pathway:
    # injection now serves dry crop residues too, so it must draw on ag+forestry there
    # (not manure). WtE always operates on the biogenic MSW stream.
    if pathway_key == "wte_ccs" or dom == "msw":
        return round(msw * biofrac * 1.0 * eff, 1)

    if dom == "manure_wet":
        return round((manure + wwtp) * ODT_TO_CO2 * eff, 1)

    # dry biomass regions (ag / forestry / mixed) -> ag+forestry residues
    return round((ag + forestry) * ODT_TO_CO2 * eff, 1)


# --------------------------------------------------------------------------
# Ranked best->worst CDR options per region (with region-specific pros/cons)
# --------------------------------------------------------------------------
def applicable_pathways(dom, avail=None):
    """Pathways that physically suit the region's dominant feedstock. Retrofit-only pathways
    (beccs_pp / wte_ccs / ad_ccs) are included only where an existing facility of that type is
    within reach (avail flag set)."""
    av = _avail(avail)
    if dom == "manure_wet":                                # wet: never combustion
        lst = ["injection", "biochar"]
        if av["ad"]:
            lst.insert(1, "ad_ccs")
        return lst
    if dom == "msw":
        lst = ["burial", "biochar"]
        if av["wte"]:
            lst.insert(0, "wte_ccs")
        return lst
    # dry: ag_dry / forestry_woody / mixed
    dry = ["beccs", "injection", "bio_oil", "burial", "biochar"]
    if av["pp"]:
        dry.insert(1, "beccs_pp")
    return dry


def fit_score(region, pathway, storage_access, avail=None):
    """Region-fit score for ranking: intrinsic KPI score + local modifiers."""
    av = _avail(avail)
    p = PATHWAYS[pathway]
    score = kpi_score(pathway, storage_access)
    density = region.get("feedstock_density")
    nutrient = region.get("nutrient_status")
    centralized = pathway in ("beccs", "beccs_pp", "wte_ccs")
    distributed = pathway in ("bio_oil", "biochar", "burial")

    if density == "diffuse" and centralized:
        score -= 10
    if density == "diffuse" and distributed:
        score += 4
    if p["needs_geologic_storage"]:
        if storage_access == "good":
            score += 4
        elif storage_access == "moderate":
            score -= 5
    if nutrient == "excess":
        if pathway in ("bio_oil", "biochar", "ad_ccs"):
            score -= 8
        elif pathway in ("burial", "injection"):
            score += 4
    if pathway == "beccs_pp":
        score += 8 if av["pp"] else -50
    return score


def region_pros_cons(region, pathway, storage_access, nearest_km, avail, anchor):
    """Static profile pros/cons plus region-specific modifiers."""
    prof = PATHWAY_PROFILE[pathway]
    pros = list(prof["pros"])
    cons = list(prof["cons"])
    p = PATHWAYS[pathway]
    density = region.get("feedstock_density")
    nutrient = region.get("nutrient_status")

    if p["needs_geologic_storage"]:
        if storage_access == "good":
            pros.append("Proximate geologic storage here"
                        + (f" (~{nearest_km} km)" if nearest_km else ""))
        elif storage_access == "moderate":
            cons.append("Geologic storage only moderately accessible — transport adds cost")
        else:
            cons.append("Geologic storage is poor/absent here — a major constraint")

    if density == "diffuse":
        if pathway in ("beccs", "beccs_pp", "wte_ccs"):
            cons.append("Local biomass is diffuse — hauling to a central plant is costly")
        elif pathway in ("bio_oil", "biochar", "burial"):
            pros.append("Suits the region's diffuse, distributed biomass")
    elif density == "concentrated" and pathway in ("beccs", "beccs_pp", "wte_ccs"):
        pros.append("Biomass is concentrated — supports a central facility")

    if nutrient == "excess":
        if pathway in ("bio_oil", "biochar", "ad_ccs"):
            # Nutrient return is a liability here, not a benefit: drop any nutrient pro.
            pros = [x for x in pros if "nutrient" not in x.lower()]
            cons.append("Returns nutrients to soils already in surplus here")
        elif pathway in ("burial", "injection"):
            pros.append("Removes carbon and nutrients from an over-fertilized landscape")

    av = _avail(avail)
    if pathway == "beccs_pp":
        if av["pp"] and anchor:
            pros.append(f"Existing mill to retrofit: {anchor}")
        elif av["pp"]:
            pros.append("Existing pulp/bioenergy mill within procurement range to retrofit")
        else:
            cons.append("No existing pulp & paper mill within range to retrofit")
    if pathway == "wte_ccs":
        if av["wte"] and anchor:
            pros.append(f"Existing WtE plant to retrofit: {anchor}")
        elif not av["wte"]:
            cons.append("No existing waste-to-energy plant within range to retrofit")
    if pathway == "ad_ccs":
        if av["ad"] and manure_ad_preferred(region):
            pros.insert(0, "Manure is already digested here — AD+CCS retrofits existing biogas plants")
        elif av["ad"]:
            pros.append("Existing anaerobic-digestion capacity within range to retrofit")
        else:
            cons.append("No existing anaerobic-digestion capacity within range to retrofit")

    return pros[:4], cons[:4]


def build_ranked(region, rec_key, runner_key, storage_access, nearest_km,
                 avail, anchor):
    """Ordered best->worst list of applicable pathways with pros/cons + fit badge."""
    dom = region.get("dominant_feedstock")
    apps = applicable_pathways(dom, avail)
    for k in (rec_key, runner_key):          # always include the engine's picks
        if k not in apps:
            apps.append(k)

    scores = {a: fit_score(region, a, storage_access, avail) for a in apps}
    rest = sorted((a for a in apps if a not in (rec_key, runner_key)),
                  key=lambda a: -scores[a])
    order = [rec_key, runner_key] + rest

    ranked = []
    for a in order:
        if a == rec_key:
            badge = "Recommended"
        elif a == runner_key:
            badge = "Runner-up"
        else:
            sc = scores.get(a, 0)
            badge = "Strong fit" if sc >= 60 else ("Possible" if sc >= 45 else "Poor fit")
        pros, cons = region_pros_cons(region, a, storage_access, nearest_km,
                                      avail, anchor)
        ranked.append({
            "key": a,
            "label": PATHWAYS[a]["label"],
            "badge": badge,
            "cdr_efficiency": PATHWAYS[a]["cdr_efficiency"],
            "cost_band": PATHWAYS[a]["cost_band"],
            "pros": pros,
            "cons": cons,
        })
    return ranked


# --------------------------------------------------------------------------
# Rationale + caveats + flags
# --------------------------------------------------------------------------
def build_rationale(region, rec_key, storage_access, nearest_km,
                    has_retrofit, anchor_name, anchor_type):
    dom = region.get("dominant_feedstock")
    density = region.get("feedstock_density")
    nutrient = region.get("nutrient_status")
    p = PATHWAYS[rec_key]
    eff_pct = int(round(p["cdr_efficiency"] * 100))

    dist = f"{nearest_km} km" if nearest_km is not None else "no mapped"
    feed_desc = {
        "ag_dry": "dry agricultural residues",
        "forestry_woody": "woody forestry residues",
        "msw": "municipal solid waste",
        "manure_wet": "wet animal manure / biosolids",
        "mixed": "mixed biomass residues",
    }.get(dom, "biomass residues")

    storage_desc = {
        "good": f"good geologic storage access (nearest qualifying storage ~{dist})",
        "moderate": f"moderate geologic storage access (~{dist})",
        "poor": "poor/absent geologic storage access",
    }[storage_access]

    anchor_clip = ""
    if has_retrofit and anchor_name:
        anchor_clip = f" with a retrofittable {anchor_type} anchor ({anchor_name})"

    base = f"{density.capitalize()} {feed_desc}, {nutrient} nutrient status, {storage_desc}"

    if rec_key == "beccs_pp":
        return (f"{base}{anchor_clip} -> BECCS retrofit of existing pulp & paper / bioenergy "
                f"maximizes CDR efficiency ({eff_pct}%) plus energy co-product -- Frontier's "
                f"top-preferred use of biomass.")
    if rec_key == "beccs":
        return (f"{base}{anchor_clip} -> BECCS (combustion + capture) delivers {eff_pct}% CDR "
                f"efficiency with an energy co-product, Frontier's most-preferred pathway where "
                f"feedstock is concentrated near storage.")
    if rec_key == "wte_ccs":
        return (f"{base} -> WtE + CCS captures biogenic CO2 from municipal waste already being "
                f"combusted ({eff_pct}% CDR efficiency, energy co-product).")
    if rec_key == "injection":
        if dom == "manure_wet":
            return (f"{base} -> wet wastes are unsuited to combustion (thesis sec 2.2); Vaulted-style "
                    f"slurry injection delivers >{eff_pct - 1}% CDR efficiency with PFAS-destruction "
                    f"co-benefit.")
        return (f"{base} -> with proximate geologic storage, Vaulted-style slurry injection is "
                f"cheaper on balance than bio-oil for these residues and removes more carbon "
                f"(>{eff_pct - 1}% CDR efficiency): raw biomass is injected at nearby wells rather "
                f"than pyrolyzed to densify it for long-haul transport. Bio-oil overtakes only as "
                f"wells get more distant.")
    if rec_key == "ad_ccs":
        if manure_ad_preferred(region):
            return (f"{base} -> most manure here already flows to anaerobic digesters, so AD+CCS "
                    f"retrofits existing biogas infrastructure ({eff_pct}% CDR efficiency) and is "
                    f"preferred over injection; the RNG co-product displaces fossil gas. A viable "
                    f"offtake option (no longer a Frontier exclusion).")
        return (f"{base} -> wet feedstock favors anaerobic digestion + CCS ({eff_pct}% CDR "
                f"efficiency, RNG co-product that displaces fossil gas); never combustion.")
    if rec_key == "bio_oil":
        return (f"{base} -> diffuse residues distant from concentrated storage favor modular "
                f"bio-oil sequestration (Charm-style roving model, ~{eff_pct}% CDR efficiency) "
                f"returning biochar + nutrients.")
    if rec_key == "burial":
        return (f"{base} -> with excess nutrients and no viable geologic storage, biomass burial "
                f"offers >{eff_pct - 1}% CDR efficiency at low cost without needing CO2 storage "
                f"(Kodama/Graphyte model).")
    if rec_key == "biochar":
        return (f"{base} -> distributed biochar returns nutrients to soils ({eff_pct}% CDR "
                f"efficiency); lower preference but storage-independent.")
    return base


def build_caveats_flags(region, rec_key, runner_key, only_low_conf, anchor_type,
                        nutrient_alt=False):
    caveats = []
    flags = []
    dom = region.get("dominant_feedstock")

    # Note: burial-related explainer caveats (excess-nutrient rationale, burial durability)
    # are intentionally omitted -- the internal Frontier audience already knows them. The
    # durability trade-off still appears in the ranked-options pros/cons. Frontier-exclusion
    # flags (corn-ethanol, RNG, purpose-grown) are retained below.

    # National-rollup caveat for large heterogeneous countries
    if region.get("level") == "country" and region.get("id") in LARGE_HETEROGENEOUS:
        extra = (" See the subnational (state/province) cells for spatially-resolved recommendations."
                 if region.get("id") in HAS_SUBNATIONAL else "")
        caveats.append(
            "National rollup -- feedstock type/density, storage access, and nutrient status "
            "vary substantially sub-nationally; the optimal pathway is local." + extra
        )

    # Storage-confidence caveat
    if only_low_conf:
        caveats.append(
            "Only low-confidence geologic storage mapped nearby (e.g. cratonic / basalt "
            "settings); treated as no viable storage pending appraisal."
        )

    # (RNG+CCS / AD+CCS is no longer flagged as excluded -- Frontier is open to it as an
    #  offtake option. Its partial-CDR trade-off is surfaced in the ranked-options cons.)

    # Corn-ethanol exclusion: a US phenomenon. Scope to US regions so we do NOT mislabel
    # sugarcane ethanol (Brazil/Argentina/Colombia) or wheat ethanol (UK) -- which Frontier
    # does not exclude -- as corn ethanol.
    notes = (region.get("notes") or "").lower()
    country = region_country(region)
    if country == "USA" and (anchor_type == "ethanol" or "corn" in notes):
        flags.append(
            "Corn-ethanol+CCS excluded by Frontier (food/land competition, marginal "
            "additionality, thesis exclusions); not recommended despite local ethanol capacity."
        )

    # Never recommend purpose-grown crops -- guarded by construction, but flag if the
    # feedstock narrative leans on dedicated energy crops.
    if "energy crop" in notes or "purpose-grown" in notes or "miscanthus" in notes or "switchgrass" in notes:
        flags.append(
            "Purpose-grown energy crops excluded by Frontier (land-use competition, "
            "thesis exclusions); recommendation uses residues only."
        )

    return caveats, flags
