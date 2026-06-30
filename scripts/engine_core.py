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

import json
import math
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data", "processed")

# --------------------------------------------------------------------------
# Pathway constants (thesis sec 2.1 / ENGINE_SPEC.md)
# --------------------------------------------------------------------------
ODT_TO_CO2 = 1.47  # tCO2 per oven-dry-ton of biomass carbon basis

PATHWAYS = {
    "beccs": {
        "label": "BECCS (heat/electricity)",
        "cdr_efficiency": 0.80,
        "cost_band": "$200-225",
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
    "lfg_ccs": {
        # Combust collected landfill gas (or its tail gas) and capture the ~100%-biogenic CO2.
        # Efficiency is expressed as the share of the COLLECTED-gas biogenic carbon captured &
        # stored; uncollected fugitive methane (collection ~75%) is outside it and is the big
        # asterisk on the removal claim. Methane avoidance is a co-benefit, NOT counted as CDR.
        "label": "Landfill gas + CCS",
        # Conservative: capture of the collected gas is high (~90%), but only a fraction of the
        # landfill's lifetime biogenic carbon is ever collected (collection ~75%, and much carbon
        # never becomes gas) and additionality vs flaring is a question — so we credit ~0.52 of the
        # collected-gas CO2 as durable removal. This keeps it BELOW WtE+CCS (0.55, which combusts the
        # whole waste stream), so a WtE retrofit leads where one exists; LFG+CCS leads the (common)
        # no-WtE-but-large-landfill case.
        "cdr_efficiency": 0.52,
        "cost_band": "$100-200",
        "co_product": "energy",
        "needs_geologic_storage": True,
    },
    "lfg_rng_ccs": {
        # Upgrade landfill gas to pipeline RNG and capture the near-pure CO2 the upgrading already
        # vents (cheap capture). Only that separated CO2 is removal; the RNG carbon is combusted
        # downstream (avoidance), so the CDR share is capped — like AD+CCS.
        "label": "Landfill-gas RNG + CCS",
        "cdr_efficiency": 0.33,
        "cost_band": "$80-180",
        "co_product": "low-C fuel",
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
        "label": "Bio-oil (pyrolysis)",
        "cdr_efficiency": 0.45,
        "cost_band": "$140-360",
        "co_product": "biochar/nutrients",
        "needs_geologic_storage": False,
    },
    "bio_oil_htl": {
        # Hydrothermal liquefaction — for WET biomass (manure/biosolids). Handles wet feedstock
        # without drying; densifies it into a stable bio-crude that is injected into a well.
        "label": "Bio-oil (hydrothermal liquefaction)",
        "cdr_efficiency": 0.50,
        "cost_band": "$200-400",
        "co_product": "nutrients",
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
    "lfg_ccs": {
        "pros": ["Retrofits an existing landfill gas-collection system — near-term, low execution risk",
                 "Captures concentrated, ~100%-biogenic CO2 from combusted landfill gas",
                 "Energy co-product (electricity) and avoids fugitive methane (co-benefit)"],
        "cons": ["Only the captured biogenic CO2 counts as removal — uncollected fugitive methane "
                 "(gas collection ~75%) is a large asterisk on the claim",
                 "Dilute, variable gas stream; capture capex on a modest flue volume"],
    },
    "lfg_rng_ccs": {
        "pros": ["Captures the near-pure CO2 already vented by landfill-gas-to-RNG upgrading — cheap capture",
                 "RNG co-product displaces fossil pipeline gas; retrofits an existing/planned RNG project",
                 "Avoids fugitive landfill methane (co-benefit)"],
        "cons": ["Only the separated CO2 is removal; the RNG carbon is combusted downstream "
                 "(avoidance, not CDR) — caps CDR efficiency",
                 "Depends on a gas-upgrading / RNG project being present or viable"],
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
                 "Needs dry/solid biomass — not for wet feedstocks",
                 "Higher $/t than injection where storage is proximate"],
    },
    "bio_oil_htl": {
        "pros": ["Handles WET biomass (manure/biosolids) directly — no drying needed",
                 "Hydrothermal liquefaction densifies the carbon into a stable bio-crude, cheap to haul to distant wells",
                 "Viable where wet-slurry injection/AD would need nearby geologic storage"],
        "cons": ["Higher cost and earlier-stage than pyrolysis or direct injection",
                 "Lower CDR efficiency than slurry injection (~50% vs >90%)"],
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

# --------------------------------------------------------------------------
# AD maturity (data-driven; replaces the former hardcoded HIGH_AD_PENETRATION binary).
# ad_maturity in [0,1] = the fraction of a region's organic/manure AD potential already
# realized as biogas/biomethane ("utilization", IEA framing). Where it is high, a large
# existing AD industry exists to retrofit, so AD+CCS leads over injection for wet manure;
# where low, on-farm/industrial AD is too sparse and Vaulted-style injection leads.
# Built by scripts/build_ad_maturity.py -> data/processed/ad_maturity.json (country scores
# from IEA Outlook 2025 / FAOSTAT / IRENA / EBA; sub-national from AgSTAR (US), Canadian
# Biogas Association (CA), and AD-facility density vs ENSPRESO manure potential (EU)).
AD_MATURITY_THRESHOLD = 0.15   # score >= this => AD+CCS leads over injection (tunable)
AD_MATURITY_DEFAULT = 0.05     # nascent-AD economies with no compiled score
_AD_MATURITY = None


def _load_ad_maturity():
    global _AD_MATURITY
    if _AD_MATURITY is None:
        try:
            with open(os.path.join(_DATA_DIR, "ad_maturity.json")) as f:
                _AD_MATURITY = json.load(f)
        except (FileNotFoundError, ValueError):
            _AD_MATURITY = {"_meta": {}, "countries": {}, "regions": {}}
    return _AD_MATURITY


def ad_maturity_score(region):
    """Continuous AD-maturity [0,1] for a region: a sub-national override if one exists
    (by region id, or by US state / Canada province), else the country score, else default."""
    d = _load_ad_maturity()
    regions = d.get("regions", {})
    rid = region.get("id")
    if rid in regions:                                   # EU NUTS-2 (and any exact override)
        return regions[rid]
    st = region.get("state")
    if st and ("US-" + st) in regions:                   # US county inherits its state score
        return regions["US-" + st]
    pv = region.get("prov")
    if pv and ("CA-" + pv) in regions:                   # Canada CD inherits its province score
        return regions["CA-" + pv]
    return d.get("countries", {}).get(region_country(region), AD_MATURITY_DEFAULT)

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
#   landfill ~40 km: a large gas-collecting landfill within the MSW catchment anchors LFG+CCS.
PROC_RADIUS_KM = {"pulp_paper": 150.0, "wte": 50.0, "biogas_ad": 15.0, "landfill": 40.0}
AD_MIN_CAP_MTPA = 0.01   # cumulative AD biogenic-CO2 capacity within reach to enable AD+CCS
LFG_MIN_CO2_MTPA = 0.05  # collected-gas biogenic CO2 (full-combustion basis) to qualify a landfill
# pathway key -> avail flag it is gated on
RETROFIT_GATE = {"beccs_pp": "pp", "wte_ccs": "wte", "ad_ccs": "ad",
                 "lfg_ccs": "lf", "lfg_rng_ccs": "lf"}

# --------------------------------------------------------------------------
# Cost-based storage access (to_do item 4, Phase C). Where a multimodal transport cost is
# available (currently the US scope; transport_us.json), storage access is derived from the
# carbon-density-weighted DELIVERED COST ($/tCO₂) to the nearest operating well instead of from
# great-circle distance, and storage-dependent pathways are disqualified above a max cost.
#   low  $0–33  -> good        medium $33–66 ┐
#   high $66–100 -> moderate (viable, costly) ┘ (both map to "moderate": storage reachable)
#   over $100   -> poor (storage not viable) -> falls back to burial / biochar (no transport)
# The delivered cost depends on WHAT is moved, so each pathway is gated on its own payload:
#   capture pathways move CO₂ (~1.0 t/tCO₂); bio-oil ~0.45; wet slurry (injection) ~2.0;
#   burial/biochar move nothing (stored locally) -> never gated.
TRANSPORT_BANDS = (33.0, 66.0, 100.0)   # $/tCO₂ thresholds: low | medium | high | over
TRANSPORT_MAX_USD = 100.0               # storage-dependent pathway disqualified above this
TRANSPORT_KPI_PENALTY = {"low": 0, "medium": 4, "high": 8, "over": 0}  # soft KPI nudge by band

# pathway -> transport payload class (None = storage-independent, no transport-to-well cost).
# bio_oil (pyrolysis) and bio_oil_htl (HTL bio-crude) have different carbon densities, so distinct.
PATHWAY_PAYLOAD = {
    "beccs": "co2", "beccs_pp": "co2", "wte_ccs": "co2", "ad_ccs": "co2",
    "lfg_ccs": "co2", "lfg_rng_ccs": "co2",
    "bio_oil": "bio_oil", "bio_oil_htl": "bio_oil_htl", "injection": "slurry",
}


def transport_band(usd):
    """4-band label for a delivered $/tCO₂ (low / medium / high / over $100)."""
    if usd is None:
        return None
    if usd < TRANSPORT_BANDS[0]:
        return "low"
    if usd < TRANSPORT_BANDS[1]:
        return "medium"
    if usd <= TRANSPORT_BANDS[2]:
        return "high"
    return "over"


# Well statuses treated as FIRM storage (operational or issued Class VI): high odds of being
# operational in time for a project starting today, so they can earn full "good" storage access.
# Draft / pending permits are lower-confidence and capped at "moderate" no matter how cheap.
FIRM_STORAGE_STATUS = {"operational", "issued"}


def permitted_storage_caveat(dest_status, dest_well):
    """Lower-confidence caveat text for a draft/pending storage destination (None if firm)."""
    if dest_status == "draft":
        return (f"Nearest affordable storage is a draft-permit well ({dest_well}) at the "
                f"public-comment stage (~55-70% reach injection) — storage access capped at "
                f"'moderate' (lower confidence).")
    if dest_status == "pending":
        return (f"Nearest affordable storage is a pending Class VI application ({dest_well}), "
                f"speculative (~30-50% reach injection, multi-year) — counted only as a fallback; "
                f"storage access capped at 'moderate'.")
    return None


def storage_access_from_cost(co2_usd, dest_status="operational"):
    """Map the CO₂ delivered cost to the engine's storage_access tiers:
      good     ≤ $66/tCO₂  (clearly cheap — prefer geologic pathways: BECCS / injection)
      moderate ≤ $100      (viable but marginal — bio-oil competitive)
      poor     > $100      (CO₂ cannot be moved to a well affordably → storage-independent)
    Tiered by well-permit confidence: a FIRM destination (operational or issued Class VI) can earn
    "good"; a DRAFT or PENDING permit is capped at "moderate" however cheap (storage not yet assured).
    The finer 4-band label (low/medium/high/over at 33/66/100) is kept separately for display +
    soft KPI penalty."""
    if co2_usd is None:
        return None
    if co2_usd > TRANSPORT_MAX_USD:        # > $100
        return "poor"
    if co2_usd <= TRANSPORT_BANDS[1] and dest_status in FIRM_STORAGE_STATUS:   # ≤ $66 to a firm well
        return "good"
    return "moderate"                      # ≤ $100, or any draft/pending destination


def transport_cost_for(pathway, tcost):
    """Delivered $/tCO₂ for a pathway's payload (None for storage-independent / no data)."""
    pay = PATHWAY_PAYLOAD.get(pathway)
    if pay is None or not tcost:
        return None
    return tcost.get(pay)


def apply_transport_cap(rec, runner, dom, region, tcost):
    """Carbon-density-correct >$100 cutoff. If the recommended storage-dependent pathway's payload
    delivered cost exceeds TRANSPORT_MAX_USD, fall back to the cheapest still-affordable option.
    The fallback differs by feedstock: WET manure has no solid-biomass options (no biochar/burial),
    so it falls to HTL bio-oil (densified, haulable); DRY biomass falls to densified bio-oil, else a
    storage-independent pathway (burial in excess-nutrient regions, else biochar). Returns
    (rec, runner, capped)."""
    if not tcost:
        return rec, runner, False
    nutrient = region.get("nutrient_status")
    wet = (dom == "manure_wet")
    if wet:                                # wet manure: HTL bio-oil is the densified fallback
        indep, indep_alt = "bio_oil_htl", "injection"
    else:
        indep = "burial" if nutrient == "excess" else "biochar"
        indep_alt = "biochar" if indep == "burial" else "burial"

    def affordable(p):
        c = transport_cost_for(p, tcost)
        return c is None or c <= TRANSPORT_MAX_USD

    if affordable(rec):
        if not affordable(runner):
            runner = indep if indep != rec else indep_alt   # never duplicate the recommendation
        return rec, runner, False
    # recommended pathway can't deliver its payload affordably -> fall back by feedstock type
    if wet:
        # injection / AD+CCS priced out -> HTL bio-oil (densified). Least-bad even if itself costly.
        return "bio_oil_htl", "injection", True
    if dom == "msw":
        return "burial", "biochar", True
    if affordable("bio_oil"):              # dry biomass: densify and haul
        return "bio_oil", indep, True
    return indep, indep_alt, True


def _avail(avail):
    """Normalize the per-region retrofit-availability flags. pp/wte/ad default available (the global
    scope passes None and assumes facilities may exist); `lf` (landfill LFG+CCS) defaults OFF — it is
    opt-in for scopes that actually compute a gas-collecting-landfill gate (currently US only), so
    scopes without landfill data never recommend the LFG pathways."""
    if avail is None:
        return {"pp": True, "wte": True, "ad": True, "lf": False}
    return {"pp": bool(avail.get("pp")), "wte": bool(avail.get("wte")),
            "ad": bool(avail.get("ad")), "lf": bool(avail.get("lf"))}


def manure_ad_preferred(region):
    """True where realized AD maturity is high enough that AD+CCS leads over injection."""
    thr = _load_ad_maturity().get("_meta", {}).get("threshold", AD_MATURITY_THRESHOLD)
    return ad_maturity_score(region) >= thr


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
# A non-MSW feedstock counts as "significant" (worth re-routing an MSW region to) if its CDR-
# relevant CO2 potential is at least this fraction of the region's biogenic-MSW potential, OR
# clears an absolute floor. The absolute floor matters for big cities: e.g. Los Angeles' MSW
# dwarfs its human biosolids relatively (~5%), but ~0.3 Mt CO2/yr of biosolids is an ample
# injection feedstock in absolute terms (this is exactly what Vaulted Deep injects in LA).
SECONDARY_FRAC = 0.25
SECONDARY_ABS_MTPA = 0.05   # CO2/yr — a feedstock this large is worth a pathway on its own


def _secondary_dom(region):
    """For an MSW-dominant region with no WtE to retrofit: the next-significant feedstock to
    recommend on (wet biosolids/manure or dry residues), or None if MSW overwhelmingly
    dominates AND no non-MSW stream clears the absolute floor -> no good BiCRS option."""
    ag = num(region.get("ag_residues_odt_mt"))
    forestry = num(region.get("forestry_residues_odt_mt"))
    dry = (ag + forestry) * ODT_TO_CO2
    wet = (num(region.get("animal_manure_odt_mt")) + num(region.get("human_wwtp_odt_mt"))) * ODT_TO_CO2
    msw = num(region.get("msw_total_mt")) * num(region.get("msw_biogenic_frac"), 0.5)
    best = max(dry, wet)
    if best <= 0 or (best < SECONDARY_FRAC * msw and best < SECONDARY_ABS_MTPA):
        return None
    if dry >= wet:
        return "forestry_woody" if forestry > ag else "ag_dry"
    return "manure_wet"


def _decide_msw_capture(region, storage_access, av):
    """MSW with storage near and at least one retrofittable capture anchor (a WtE plant and/or a
    qualifying gas-collecting landfill). Returns (rec, runner). Candidates are WtE+CCS (where a WtE
    plant exists) and LFG+CCS (where a large gas-collecting landfill exists), ordered by KPI — so a
    WtE retrofit leads where present (it combusts the whole MSW stream) and LFG+CCS leads the common
    no-WtE-but-landfill case. LFG-RNG+CCS is always a runner, not the lead: combusting all collected
    gas (LFG+CCS) removes more carbon than capturing only the RNG-upgrading vent, so Frontier's
    CDR-first KPI prefers it; RNG+CCS surfaces as the lower-CDR / cheaper-capture alternative."""
    opts = []
    if av["wte"]:
        opts.append("wte_ccs")
    if av["lf"]:
        opts.append("lfg_ccs")
    opts.sort(key=lambda p: -kpi_score(p, storage_access))
    rec = opts[0]
    if len(opts) > 1:
        runner = opts[1]
    elif av["lf"]:
        runner = "lfg_rng_ccs"      # only a landfill: RNG+CCS is the alternative
    else:
        runner = "burial"
    return rec, runner


def decide(region, storage_access, has_retrofit, avail=None):
    """Returns (recommended, runner_up, effective_dom). `effective_dom` is the feedstock the
    decision was actually made on; it differs from the region's dominant feedstock when an
    MSW region with no WtE is re-routed to its next-significant feedstock (e.g. urban biosolids
    -> injection). Downstream CDR/rationale/ranked should use effective_dom."""
    dom = region.get("dominant_feedstock")
    av = _avail(avail)
    near = storage_access in ("good", "moderate")

    # MSW: capture the biogenic CO2 from waste already being managed. Near storage, this means a
    # WtE+CCS retrofit OR — where there is a large gas-collecting landfill — LFG+CCS / LFG-RNG+CCS
    # (ordered by KPI). With neither capture anchor in range (or no storage), municipal waste is
    # merely landfilled here, not a standalone removal feedstock: re-evaluate on the region's
    # next-significant feedstock; if there is no other significant biomass, there is no good
    # BiCRS option ("none").
    if dom == "msw":
        if near and (av["wte"] or av["lf"]):
            rec, runner = _decide_msw_capture(region, storage_access, av)
            return rec, runner, "msw"
        alt = _secondary_dom(region)
        if alt is None:
            return "none", None, "msw"
        dom = alt  # decide on the secondary feedstock instead

    rec, runner = _decide_for(region, storage_access, has_retrofit, av, dom)
    return rec, runner, dom


def _decide_for(region, storage_access, has_retrofit, av, dom):
    density = region.get("feedstock_density")
    nutrient = region.get("nutrient_status")
    near = storage_access in ("good", "moderate")

    # Preferred distributed-removal pathway for DRY biomass, set by storage proximity.
    # Frontier is bullish on Vaulted-style slurry injection: it handles the same dry
    # residues as bio-oil, has higher CDR efficiency (>90% vs ~45%), and is cheaper on
    # balance -- so where geologic storage (injection wells) is PROXIMATE it beats bio-oil.
    # Bio-oil's edge is only at distance: pyrolysis densifies the carbon, making the
    # less-carbon-dense raw biomass cheaper to haul to far-off wells. So:
    #   good storage (proximate) -> injection ;  moderate/poor (distant) -> bio-oil.
    dry_removal = "injection" if storage_access == "good" else "bio_oil"

    # 1. wet manure. Wet biomass has NO solid-feedstock options — biochar and burial both need
    #    dry/solid biomass, so they are never used here. The wet pathways are: AD+CCS and
    #    Vaulted-style slurry injection (both place CO2/slurry into geologic storage, so — like
    #    BECCS/WtE+CCS — both require storage proximity; AD+CCS also needs AD capacity to retrofit),
    #    and HTL bio-oil (hydrothermal liquefaction densifies the wet feedstock so it can be hauled).
    #    Bio-oil is pricier / less preferred than direct injection, so it leads only where storage is
    #    poor or injection transport is too costly (the transport cap handles the latter downstream).
    if dom == "manure_wet":
        if near:
            # Storage proximate. In mature-AD regions with AD capacity nearby, AD+CCS retrofits
            # existing digesters and leads; otherwise direct injection leads (US-style: on-farm AD rare).
            if av["ad"] and manure_ad_preferred(region):
                return "ad_ccs", "injection"
            return "injection", ("ad_ccs" if av["ad"] else "bio_oil_htl")
        # Storage poor: injection / AD+CCS cannot place their carbon here -> HTL bio-oil (densified,
        # haulable). Never biochar/burial (wet feedstock).
        return "bio_oil_htl", ("ad_ccs" if av["ad"] else "injection")

    # 2. MSW. Only reached when an existing WtE plant is within reach (else re-routed above).
    if dom == "msw":
        return "wte_ccs", "burial"

    # 3. forestry_woody OR (ag_dry & concentrated)
    if dom == "forestry_woody" or (dom == "ag_dry" and density == "concentrated"):
        if storage_access in ("good", "moderate"):
            # BECCS leads; the pulp&paper RETROFIT leads over greenfield BECCS wherever an existing
            # mill is within reach (av["pp"]) — both need the same geologic storage, but the retrofit
            # leverages existing biomass logistics + lower execution risk, so it is preferred at good
            # AND moderate storage alike. Runner-up: injection where storage is proximate (good),
            # else bio-oil (densified carbon hauls cheaper when wells are farther).
            runner = dry_removal if storage_access == "good" else "bio_oil"
            if av["pp"]:
                return "beccs_pp", runner
            return "beccs", runner
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

    # Landfill-gas pathways draw on the ANCHOR LANDFILL's collected-gas biogenic CO2 (full-
    # combustion basis, set by the scope builder as region["_lfg_co2_mtpa"]), not the region's
    # whole MSW stream — the removal is bounded by the gas the landfill actually collects.
    if pathway_key in ("lfg_ccs", "lfg_rng_ccs"):
        return round((region.get("_lfg_co2_mtpa") or 0.0) * eff, 2)

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
    if dom == "manure_wet":         # wet: never combustion, never solid-biomass (no biochar/burial)
        lst = ["injection", "bio_oil_htl"]   # direct injection, else HTL bio-oil (densified, haulable)
        if av["ad"]:
            lst.insert(1, "ad_ccs")
        return lst
    if dom == "msw":
        lst = ["burial", "biochar"]
        if av["wte"]:
            lst.insert(0, "wte_ccs")
        if av["lf"]:               # gas-collecting landfill in range: both LFG pathways apply
            lst = ["lfg_ccs", "lfg_rng_ccs"] + lst
        return lst
    # dry: ag_dry / forestry_woody / mixed
    dry = ["beccs", "injection", "bio_oil", "burial", "biochar"]
    if av["pp"]:
        dry.insert(1, "beccs_pp")
    return dry


def fit_score(region, pathway, storage_access, avail=None, tcost=None):
    """Region-fit score for ranking: intrinsic KPI score + local modifiers. When a transport
    cost is supplied (`tcost` = per-payload delivered $/tCO₂), a storage-dependent pathway whose
    payload cannot be delivered under TRANSPORT_MAX_USD is hard-demoted (it is not viable here),
    and one below the cap takes the same graduated soft penalty the headline KPI uses."""
    av = _avail(avail)
    p = PATHWAYS[pathway]
    score = kpi_score(pathway, storage_access)
    density = region.get("feedstock_density")
    nutrient = region.get("nutrient_status")
    centralized = pathway in ("beccs", "beccs_pp", "wte_ccs")
    distributed = pathway in ("bio_oil", "bio_oil_htl", "biochar", "burial")

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
        if pathway in ("bio_oil", "bio_oil_htl", "biochar", "ad_ccs"):
            score -= 8
        elif pathway in ("burial", "injection"):
            score += 4
    if pathway == "beccs_pp":
        score += 8 if av["pp"] else -50
    if pathway in ("lfg_ccs", "lfg_rng_ccs"):
        score += 6 if av["lf"] else -50
    # transport-cost demotion (storage-dependent pathways only, where a cost is known)
    tc = transport_cost_for(pathway, tcost)
    if tc is not None:
        if tc > TRANSPORT_MAX_USD:
            score -= 50               # cannot deliver its payload affordably -> not viable here
        else:
            score -= TRANSPORT_KPI_PENALTY.get(transport_band(tc), 0)
    return score


def region_pros_cons(region, pathway, storage_access, nearest_km, avail, anchor, tcost=None):
    """Static profile pros/cons plus region-specific modifiers."""
    prof = PATHWAY_PROFILE[pathway]
    pros = list(prof["pros"])
    cons = list(prof["cons"])
    p = PATHWAYS[pathway]
    density = region.get("feedstock_density")
    nutrient = region.get("nutrient_status")

    # transport-cost note (storage-dependent pathways where a delivered cost is known)
    tc = transport_cost_for(pathway, tcost)
    if tc is not None:
        if tc > TRANSPORT_MAX_USD:
            cons.insert(0, f"Transport to the nearest operating well ~${tc:.0f}/tCO₂ — exceeds the "
                           f"${TRANSPORT_MAX_USD:.0f}/tCO₂ viability cap, so this pathway is not viable here")
        elif tc >= TRANSPORT_BANDS[1]:   # >= $66 (high band, still under cap)
            cons.append(f"Transport to the nearest operating well is costly (~${tc:.0f}/tCO₂)")

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
        elif pathway in ("bio_oil", "bio_oil_htl", "biochar", "burial"):
            pros.append("Suits the region's diffuse, distributed biomass")
    elif density == "concentrated" and pathway in ("beccs", "beccs_pp", "wte_ccs"):
        pros.append("Biomass is concentrated — supports a central facility")

    if nutrient == "excess":
        if pathway in ("bio_oil", "bio_oil_htl", "biochar", "ad_ccs"):
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
    if pathway in ("lfg_ccs", "lfg_rng_ccs"):
        if av["lf"] and anchor:
            pros.append(f"Large gas-collecting landfill to retrofit: {anchor}")
        elif av["lf"]:
            pros.append("Large gas-collecting landfill within range to retrofit")
        else:
            cons.append("No qualifying gas-collecting landfill within range to retrofit")
    if pathway == "lfg_rng_ccs" and region.get("_lfg_pref") == "rng":
        pros.append("Landfill already runs a gas-to-RNG project — the upgrading CO2 vent is cheap to capture")

    return pros[:4], cons[:4]


def build_ranked(region, rec_key, runner_key, storage_access, nearest_km,
                 avail, anchor, tcost=None):
    """Ordered best->worst list of applicable pathways with pros/cons + fit badge. `tcost`
    (per-payload delivered $/tCO₂) demotes storage-dependent pathways priced out of transport."""
    dom = region.get("dominant_feedstock")
    apps = applicable_pathways(dom, avail)
    for k in (rec_key, runner_key):          # always include the engine's picks
        if k not in apps:
            apps.append(k)

    scores = {a: fit_score(region, a, storage_access, avail, tcost) for a in apps}
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
                                      avail, anchor, tcost)
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


NO_OPTION_RATIONALE = (
    "No strong near-term BiCRS pathway here: municipal waste is the only significant feedstock "
    "but there is no waste-to-energy plant within range to retrofit with capture (and MSW is "
    "landfilled, not a removal feedstock), while other biomass — agricultural and forestry "
    "residues, manure — is limited. The options below are marginal at best."
)


def build_ranked_none(region, storage_access, nearest_km, avail, anchor):
    """Ranked list for a 'no good BiCRS option' region: the technically-applicable pathways,
    scored and badged honestly (no pinned recommendation)."""
    dom = region.get("dominant_feedstock")
    apps = applicable_pathways(dom, avail)
    scores = {a: fit_score(region, a, storage_access, avail) for a in apps}
    ranked = []
    for a in sorted(apps, key=lambda a: -scores[a]):
        sc = scores[a]
        badge = "Possible" if sc >= 45 else "Poor fit"
        pros, cons = region_pros_cons(region, a, storage_access, nearest_km, avail, anchor)
        ranked.append({
            "key": a, "label": PATHWAYS[a]["label"], "badge": badge,
            "cdr_efficiency": PATHWAYS[a]["cdr_efficiency"], "cost_band": PATHWAYS[a]["cost_band"],
            "pros": pros, "cons": cons,
        })
    return ranked


# --------------------------------------------------------------------------
# Rationale + caveats + flags
# --------------------------------------------------------------------------
def build_rationale(region, rec_key, storage_access, nearest_km,
                    has_retrofit, anchor_name, anchor_type, transport=None):
    """`transport` (optional) = {"usd": delivered $/tCO₂ for the recommended pathway, "km": routed
    transport distance, "well": destination name}. When present (US/CA/EU cost-based scopes), the
    storage description is framed in transport-cost terms rather than great-circle distance."""
    dom = region.get("dominant_feedstock")
    density = region.get("feedstock_density")
    nutrient = region.get("nutrient_status")
    p = PATHWAYS[rec_key]
    eff_pct = int(round(p["cdr_efficiency"] * 100))

    feed_desc = {
        "ag_dry": "dry agricultural residues",
        "forestry_woody": "woody forestry residues",
        "msw": "municipal solid waste",
        "manure_wet": "wet animal manure / biosolids",
        "mixed": "mixed biomass residues",
    }.get(dom, "biomass residues")

    if transport and transport.get("usd") is not None:
        # cost-based scopes: describe the delivered route to the chosen storage well
        km = transport.get("km")
        well = transport.get("well")
        det = f"~${round(transport['usd'])}/tCO₂ delivered" + (f" over ~{km} km" if km else "") \
            + (f" to {well}" if well else "")
        storage_desc = {
            "good": f"good (low-cost) geologic storage access ({det})",
            "moderate": f"moderate geologic storage access ({det})",
            "poor": "poor geologic storage access (no affordable route to a storage well)",
        }[storage_access]
    else:
        dist = f"{nearest_km} km" if nearest_km is not None else "no mapped"
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
    if rec_key == "lfg_ccs":
        return (f"{base}{anchor_clip} -> no WtE plant in range, but a large gas-collecting landfill "
                f"is: combusting its collected landfill gas and capturing the ~100%-biogenic CO2 "
                f"(LFG+CCS, ~{eff_pct}% of the collected-gas carbon) turns a fugitive-methane source "
                f"into removal. Only the captured CO2 is counted as CDR; avoided methane is a "
                f"co-benefit.")
    if rec_key == "lfg_rng_ccs":
        return (f"{base}{anchor_clip} -> the landfill runs/plans a gas-to-RNG project, whose "
                f"upgrading step already vents a near-pure CO2 stream that is cheap to capture "
                f"(LFG-RNG+CCS). The RNG displaces fossil gas; only the separated CO2 is removal "
                f"(~{eff_pct}% CDR efficiency), the RNG carbon being avoidance, not CDR.")
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
                f"bio-oil sequestration via pyrolysis (Charm-style roving model, ~{eff_pct}% CDR "
                f"efficiency) returning biochar + nutrients.")
    if rec_key == "bio_oil_htl":
        return (f"{base} -> wet feedstock far from affordable geologic storage favors hydrothermal "
                f"liquefaction (HTL) to a stable bio-crude (~{eff_pct}% CDR efficiency): it handles "
                f"the wet biomass without drying and densifies the carbon for haulage to a distant "
                f"well. Pricier than direct injection, so used only where storage is distant.")
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
