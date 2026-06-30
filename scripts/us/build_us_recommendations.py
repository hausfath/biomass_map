#!/usr/bin/env python3
"""
US county-level best-use-of-biomass engine.

Reuses the shared decision logic (scripts/engine_core.py: decide / kpi_score /
cdr_potential_mtpa / build_ranked / build_rationale / build_caveats_flags), so the county
map encodes the SAME Frontier framework as the global tool. What differs is the *inputs*,
computed at county granularity:

  storage access  — point-in-basin (county centroid inside a NATCARB saline formation =
                    storage on-site) else great-circle distance to the nearest basin
                    boundary AND the nearest Class VI / operational sequestration well.
                    County-scale thresholds (good < 100 km, moderate < 300 km).
  feedstock density — real residue density (tCO2/km^2) and an 80 km haul-radius supply sum
                    (county + neighbours) to judge whether enough biomass exists within a
                    draw radius to anchor a central BECCS/pulp-scale facility.
  retrofit anchor — biogenic point sources (GHGRP) matched to the county by point-in-polygon.
  low-supply guard — counties below a minimum recoverable supply are flagged (not forced).

Reads:  feedstocks_us_county.json, storage_us_basins.json, wells_us.json,
        facilities_us_detailed.json, data/geo/us_counties.json
Writes: data/processed/recommendations_us.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/
from engine_core import (
    PATHWAYS, ODT_TO_CO2, PROC_RADIUS_KM, AD_MIN_CAP_MTPA, NO_OPTION_RATIONALE,
    num, haversine_km, _point_in_geometry,
    decide, kpi_score, cdr_potential_mtpa, build_ranked, build_ranked_none,
    build_rationale, build_caveats_flags,
    storage_access_from_cost, apply_transport_cap, transport_band, transport_cost_for,
    permitted_storage_caveat, TRANSPORT_MAX_USD, TRANSPORT_KPI_PENALTY, PATHWAY_PAYLOAD,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROC = os.path.join(ROOT, "data", "processed")
GEO = os.path.join(ROOT, "data", "geo")

FEED = os.path.join(PROC, "feedstocks_us_county.json")
BASINS = os.path.join(PROC, "storage_us_basins.json")
WELLS = os.path.join(PROC, "wells_us.json")
FACS = os.path.join(PROC, "facilities_us_detailed.json")
COUNTIES = os.path.join(GEO, "us_counties.json")
TRANSPORT = os.path.join(PROC, "transport_us.json")   # multimodal delivered $/tCO2 (build_us_transport)
OUT = os.path.join(PROC, "recommendations_us.json")

# Cross-border storage: a US county is also scored against Canadian storage (the Western Canada
# Sedimentary Basin / Quest / ACTL across from the northern-tier states). Loaded if present.
WELLS_CA = os.path.join(PROC, "wells_ca.json")
BASINS_CA = os.path.join(PROC, "storage_ca_basins.json")


def _load_opt(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# --- tunable thresholds ---
GOOD_KM = 100.0        # within this of qualifying storage -> good
MOD_KM = 300.0         # within this -> moderate
HAUL_KM = 80.0         # biomass draw radius for a central facility
DENS_THRESH = 120.0    # residue density (tCO2/km^2) above which biomass is spatially "concentrated"
CONC_SUPPLY_MT = 0.75  # haul-radius dry-biomass CO2 (Mt/yr) needed to anchor a central facility
MIN_SUPPLY_MT = 0.02   # total recoverable CO2 (Mt/yr) below which a county is "low supply"

# Wells that represent available/near-available geologic storage.
STRONG_WELL = {"operational", "issued"}
ANY_WELL = {"operational", "issued", "draft", "pending"}

# --- Forestry-residue utilization flag (to_do item 2, Option A — qualitative, no tonnage change) ---
# We do NOT net forestry residue down (gross tonnage is anchored to DOE BT23, which is itself partly
# availability-conditioned — re-subtracting risks double-counting; pellet-plant *locations* are
# proprietary (Forisk), only regional EIA aggregates are public). Instead we FLAG forestry-dominant
# counties where existing wood-bioenergy and/or wood-pellet capacity already draws heavily on the
# residue/chip stream, so the strategist knows the *spare* stream is below the gross figure shown.
#   - bioenergy draw: cumulative biomass-power biogenic CO2 within the pulpwood-haul radius (we have
#     the plants from GHGRP); a real plant nearby competes for residue/chips.
#   - pellet density: EIA-63C "SOUTH" region — the Southeast pellet/export belt (Enviva/Drax) that
#     dominates US pellet capacity (EIA Monthly Densified Biomass Fuel Report). A coarse regional
#     fact (not plant-level), appropriate for a qualitative flag.
BIOENERGY_DRAW_FLOOR_MTPA = 0.10   # cumulative biomass-power biogenic CO2 (Mt/yr) in range to flag
EIA_PELLET_SOUTH = {  # USPS abbrevs in the EIA-63C SOUTH densified-biomass region (pellet/export belt)
    "AL", "AR", "DE", "DC", "FL", "GA", "KY", "LA", "MD", "MS", "NC", "OK",
    "SC", "TN", "TX", "VA", "WV",
}


def bbox_of_geom(geom):
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for x in c:
                walk(x)
    walk(geom["coordinates"])
    return (min(xs), min(ys), max(xs), max(ys))


def min_vertex_km(lon, lat, geom):
    """Approximate distance (km) from (lon,lat) to a polygon boundary via nearest vertex
    (polygons are simplified, so vertex distance ~ edge distance for screening)."""
    best = None

    def walk(c):
        nonlocal best
        if isinstance(c[0], (int, float)):
            d = haversine_km(lon, lat, c[0], c[1])
            if best is None or d < best:
                best = d
        else:
            for x in c:
                walk(x)
    walk(geom["coordinates"])
    return best


def co2_dry(region):
    """Dry-biomass (ag + forestry) CDR-relevant CO2 potential, Mt/yr (at 100% — a supply proxy)."""
    return (num(region.get("ag_residues_odt_mt")) +
            num(region.get("forestry_residues_odt_mt"))) * ODT_TO_CO2


def co2_total(region):
    """All-stream biogenic CO2 potential, Mt/yr (supply proxy for the low-supply guard)."""
    msw = num(region.get("msw_total_mt")) * num(region.get("msw_biogenic_frac"), 0.61)
    wet = (num(region.get("animal_manure_odt_mt")) +
           num(region.get("human_wwtp_odt_mt"))) * ODT_TO_CO2
    return co2_dry(region) + msw + wet


def annotate_facility_counties(facilities, counties):
    """Tag each facility with the county FIPS it sits in (point-in-polygon, bbox-prefiltered)."""
    cbb = [(c["properties"]["fips"], c["geometry"], bbox_of_geom(c["geometry"])) for c in counties]
    for f in facilities:
        f["_county"] = None
        lon, lat = f.get("lon"), f.get("lat")
        if lon is None or lat is None:
            continue
        for fips, geom, (x0, y0, x1, y1) in cbb:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and _point_in_geometry(lon, lat, geom):
                f["_county"] = fips
                break


def compute_avail_anchor(centroid, facilities):
    """Retrofit availability for the gated pathways, by procurement radius from the county
    centroid: beccs_pp <- a pulp & paper mill within ~150 km; wte_ccs <- a WtE plant within
    ~50 km; ad_ccs <- cumulative anaerobic-digestion capacity within ~15 km >= AD_MIN_CAP;
    lfg_* <- a qualifying gas-collecting landfill within ~40 km.
    Returns (avail, has_retrofit, anchor_name, anchor_type, lf_info, bioenergy_draw) where lf_info
    (or None) = {"name","co2","pref"} for the nearest qualifying landfill (for the LFG pathways) and
    bioenergy_draw = cumulative biomass-power biogenic CO2 (Mt/yr) within the pulpwood-haul radius
    (the forestry-residue utilization signal, item 2 Option A)."""
    lon, lat = centroid[0], centroid[1]
    avail = {"pp": False, "wte": False, "ad": False, "lf": False}
    ad_cap = 0.0
    bioenergy_draw = 0.0   # cumulative biomass-power biogenic CO2 (Mt/yr) in range -> residue draw
    cands = []   # (pref, dist, facility) within its type radius -> retrofit anchor
    lf_cands = []   # (co2, dist, facility) qualifying landfills in range
    for f in facilities:
        if not f.get("existing", True):
            continue
        flon, flat = f.get("lon"), f.get("lat")
        if flon is None or flat is None:
            continue
        t = f.get("type")
        d = haversine_km(lon, lat, flon, flat)
        if t == "pulp_paper":
            if d <= PROC_RADIUS_KM["pulp_paper"]:
                avail["pp"] = True; cands.append((0, d, f))
        elif t == "bioenergy":          # supports plain BECCS (ungated) -> anchor only
            if d <= PROC_RADIUS_KM["pulp_paper"]:
                cands.append((0, d, f))
                bioenergy_draw += (f.get("est_biogenic_co2_mtpa") or {}).get("value", 0) or 0
        elif t == "wte":
            if d <= PROC_RADIUS_KM["wte"]:
                avail["wte"] = True; cands.append((1, d, f))
        elif t == "biogas_ad":
            rad = f.get("proc_radius_km") or PROC_RADIUS_KM["biogas_ad"]
            if d <= rad:
                ad_cap += (f.get("est_biogenic_co2_mtpa") or {}).get("value", 0) or 0
                cands.append((2, d, f))
        elif t == "landfill" and f.get("gas_collection"):
            if d <= PROC_RADIUS_KM["landfill"]:
                lf_cands.append(((f.get("est_biogenic_co2_mtpa") or {}).get("value", 0) or 0, d, f))
    avail["ad"] = ad_cap >= AD_MIN_CAP_MTPA
    avail["lf"] = len(lf_cands) > 0
    lf_info = None
    if lf_cands:
        lf_cands.sort(key=lambda c: -c[0])     # largest collected-gas CO2 landfill is the anchor
        co2, _, best = lf_cands[0]
        lf_info = {"name": best.get("name"), "co2": co2, "pref": best.get("lfg_project", "ccs")}
        cands.append((3, lf_cands[0][1], best))   # also a candidate generic anchor (lowest priority)
    has_retrofit = len(cands) > 0
    anchor_name = anchor_type = None
    if cands:
        cands.sort(key=lambda c: (c[0], c[1]))   # prefer pp/bioenergy, then wte, ad, landfill; nearest
        best = cands[0][2]
        anchor_name, anchor_type = best.get("name"), best.get("type")
    return avail, has_retrofit, anchor_name, anchor_type, lf_info, bioenergy_draw


def compute_storage_access_county(centroid, basins, wells):
    """Returns (access, nearest_km, detail dict)."""
    lon, lat = centroid[0], centroid[1]

    # 1. inside a saline storage formation?
    in_basin = None
    for b in basins:
        x0, y0, x1, y1 = b["bbox"]
        if x0 <= lon <= x1 and y0 <= lat <= y1 and _point_in_geometry(lon, lat, b["geometry"]):
            in_basin = b["name"]
            break

    # 2. nearest basin boundary (skip far basins by bbox/centroid prefilter)
    nearest_basin_km = None
    nearest_basin = None
    for b in basins:
        cx, cy = b["centroid"]
        if abs(cx - lon) > 12 or abs(cy - lat) > 12:
            continue
        d = min_vertex_km(lon, lat, b["geometry"])
        if d is not None and (nearest_basin_km is None or d < nearest_basin_km):
            nearest_basin_km, nearest_basin = d, b["name"]

    # 3. nearest qualifying well
    def nearest_well(statuses):
        best_km, best = None, None
        for w in wells:
            if w.get("status") not in statuses:
                continue
            d = haversine_km(lon, lat, w["lon"], w["lat"])
            if best_km is None or d < best_km:
                best_km, best = d, w["name"]
        return best_km, best
    strong_km, strong_name = nearest_well(STRONG_WELL)
    any_km, any_name = nearest_well(ANY_WELL)

    # 4. grade
    if in_basin is not None:
        access = "good"
    elif (nearest_basin_km is not None and nearest_basin_km < GOOD_KM) or \
         (strong_km is not None and strong_km < GOOD_KM):
        access = "good"
    elif (nearest_basin_km is not None and nearest_basin_km < MOD_KM) or \
         (any_km is not None and any_km < MOD_KM):
        access = "moderate"
    else:
        access = "poor"

    candidates = [d for d in (0 if in_basin else nearest_basin_km, strong_km, any_km)
                  if d is not None]
    nearest_km = round(min(candidates)) if candidates else None
    detail = {
        "in_basin": in_basin,
        "nearest_basin": nearest_basin,
        "nearest_basin_km": round(nearest_basin_km) if nearest_basin_km is not None else None,
        "nearest_well": any_name,
        "nearest_well_km": round(any_km) if any_km is not None else None,
    }
    return access, nearest_km, detail


def main():
    feeds = json.load(open(FEED))
    basins = json.load(open(BASINS)) + _load_opt(BASINS_CA)
    wells = json.load(open(WELLS)) + _load_opt(WELLS_CA)
    facilities = json.load(open(FACS))
    counties = json.load(open(COUNTIES))["features"]
    transport = _load_opt(TRANSPORT) or {}   # county id -> {by_payload:{co2,bio_oil,slurry}, ...}
    # (retrofit availability is now radius-based from each county centroid — no point-in-polygon
    #  facility tagging needed.)

    # Precompute per-county dry-biomass CO2 + centroid for the haul-radius supply sum.
    cents = [(f["centroid"][0], f["centroid"][1], co2_dry(f)) for f in feeds]

    def haul_supply(lon, lat):
        s = 0.0
        for clon, clat, c in cents:
            if abs(clat - lat) > 0.8 or c <= 0:
                continue
            if haversine_km(lon, lat, clon, clat) <= HAUL_KM:
                s += c
        return s

    records = []
    for region in feeds:
        centroid = region["centroid"]
        lon, lat = centroid[0], centroid[1]

        access, nearest_km, sdetail = compute_storage_access_county(centroid, basins, wells)

        # Cost-based storage access: where a multimodal transport cost exists, the storage-access
        # grade comes from the CO₂ delivered $/tCO₂ to the chosen well, not great-circle distance.
        # Wells are tiered by status: a route to a PERMITTED (not-yet-operating) well is capped at
        # "moderate" (storage that exists only on paper can't earn "good"). Falls back to distance
        # when no transport record.
        tinfo = transport.get(region["id"])
        tcost = tinfo.get("by_payload") if tinfo else None
        dest_status = tinfo.get("dest_status", "operational") if tinfo else "operational"
        # issued is treated as firm storage; only draft/pending are flagged lower-confidence.
        permitted_storage = dest_status in ("draft", "pending")
        if tcost and tcost.get("co2") is not None:
            access = storage_access_from_cost(tcost["co2"], dest_status)

        # density from real area + haul-radius supply
        area = region.get("area_km2") or 1.0
        dens_tco2_km2 = round(co2_dry(region) * 1e6 / area, 2)
        supply_mt = round(haul_supply(lon, lat), 3)
        # Concentrated = spatially dense biomass AND enough total within a haul radius to
        # anchor a central plant; otherwise distributed/diffuse (favours injection/bio-oil).
        density = ("concentrated" if (dens_tco2_km2 >= DENS_THRESH and supply_mt >= CONC_SUPPLY_MT)
                   else "diffuse")
        region["feedstock_density"] = density   # feed into shared decide()

        avail, has_retrofit, anchor_name, anchor_type, lf_info, bioenergy_draw = compute_avail_anchor(
            region["centroid"], facilities)
        # Carry the anchor landfill's collected-gas CO2 + project type into the region so decide()
        # can pick the LFG variant and cdr_potential can size the LFG pathways.
        if lf_info:
            region["_lfg_co2_mtpa"] = lf_info["co2"]
            region["_lfg_pref"] = lf_info["pref"]

        rec_key, runner_key, eff_dom = decide(region, access, has_retrofit, avail)
        no_option = (rec_key == "none")
        # >$100/tCO₂ cutoff (carbon-density-correct, per payload): disqualify a storage-dependent
        # pathway that can't deliver its payload affordably -> bio-oil / burial / biochar.
        transport_capped = False
        if not no_option:
            rec_key, runner_key, transport_capped = apply_transport_cap(
                rec_key, runner_key, eff_dom, region, tcost)
        # When an LFG pathway is recommended, the retrofit anchor IS the landfill.
        if rec_key in ("lfg_ccs", "lfg_rng_ccs") and lf_info:
            anchor_name, anchor_type, has_retrofit = lf_info["name"], "landfill", True
        anchor_str = f"{anchor_name} ({anchor_type})" if anchor_name else None
        rregion = region if eff_dom == region.get("dominant_feedstock") else dict(region, dominant_feedstock=eff_dom)

        nutrient_alt = False
        if no_option:
            rec_label, runner_label = "No viable BiCRS pathway", None
            score = eff = cost = None
            cdr = 0.0
            rationale = NO_OPTION_RATIONALE
            ranked = build_ranked_none(region, access, nearest_km, avail, anchor_str)
        else:
            if (region.get("nutrient_status") == "excess"
                    and eff_dom != "manure_wet"          # wet biomass: burial needs solid feedstock
                    and rec_key in ("beccs", "beccs_pp", "bio_oil", "injection")
                    and runner_key != "burial"):
                runner_key, nutrient_alt = "burial", True
            score = kpi_score(rec_key, access)
            # soft KPI penalty scaled by transport-cost band (storage-dependent pathways only)
            if tcost and rec_key in PATHWAY_PAYLOAD:
                score = max(0, score - TRANSPORT_KPI_PENALTY.get(
                    transport_band(transport_cost_for(rec_key, tcost)), 0))
            eff = PATHWAYS[rec_key]["cdr_efficiency"]
            cost = PATHWAYS[rec_key]["cost_band"]
            cdr = cdr_potential_mtpa(rregion, rec_key)
            rec_label = PATHWAYS[rec_key]["label"]
            runner_label = PATHWAYS[runner_key]["label"]
            tdesc = {"usd": (transport_cost_for(rec_key, tcost)
                              if rec_key in PATHWAY_PAYLOAD else (tcost or {}).get("co2")),
                     "km": tinfo.get("total_km"), "well": tinfo.get("dest_well")} if tinfo else None
            rationale = build_rationale(rregion, rec_key, access, nearest_km,
                                        has_retrofit, anchor_name, anchor_type, tdesc)
            ranked = build_ranked(rregion, rec_key, runner_key, access, nearest_km,
                                  avail, anchor_str, tcost)
        caveats, flags = build_caveats_flags(region, rec_key, runner_key, False,
                                             anchor_type, nutrient_alt)

        low_supply = co2_total(region) < MIN_SUPPLY_MT
        if low_supply:
            caveats = ["Negligible recoverable biomass in this county — aggregate with "
                       "neighbouring counties; recommendation is indicative only."] + caveats

        if sdetail["in_basin"]:
            caveats = [f"Overlaps the {sdetail['in_basin']} saline storage basin (theoretical "
                       f"capacity — storage still needs a developed well + transport, not on-site)."
                       ] + caveats
        if transport_capped:
            caveats = [f"Transport to the nearest well exceeds ${TRANSPORT_MAX_USD:.0f}/tCO₂ "
                       f"for this pathway's payload — defaulted to a storage-independent option "
                       f"(burial/biochar) or densified bio-oil."] + caveats
        if permitted_storage and not no_option and rec_key in PATHWAY_PAYLOAD:
            cav = permitted_storage_caveat(dest_status, tinfo.get("dest_well"))
            if cav:
                caveats = [cav] + caveats

        # Forestry-residue utilization flag (item 2, Option A): where the recommendation rests on
        # woody forestry AND existing wood-bioenergy and/or Southeast pellet capacity already draws
        # on the residue/chip stream, note that the (gross) figure is NOT net of that competing use.
        # Qualitative only — no tonnage is subtracted (the BT23 basis is itself partly
        # availability-conditioned, so re-netting would double-count; pellet-plant locations are not
        # public). See METHODOLOGY §2/§8.
        forestry_util = False
        if not no_option and eff_dom == "forestry_woody":
            bio_flag = bioenergy_draw >= BIOENERGY_DRAW_FLOOR_MTPA
            pellet_flag = region.get("state") in EIA_PELLET_SOUTH
            if bio_flag or pellet_flag:
                forestry_util = True
                drivers = []
                if bio_flag:
                    drivers.append(f"existing wood-bioenergy capacity (~{bioenergy_draw:.1f} Mt "
                                   f"biogenic CO₂/yr within haul range)")
                if pellet_flag:
                    drivers.append("the Southeast wood-pellet / export industry (EIA-63C South region)")
                caveats = caveats + [
                    "Forestry residue here is already drawn on by " + " and ".join(drivers) +
                    "; the figure shown is gross recoverable residue, NOT net of this competing use, "
                    "so the spare stream available to new BiCRS is lower. (Utilization is flagged, not "
                    "subtracted — see methodology.)"]

        records.append({
            "id": region["id"],
            "name": region["name"],
            "state": region["state"],
            "fips": region["fips"],
            "level": "county",
            "recommended": rec_key,
            "recommended_label": rec_label,
            "runner_up": runner_key,
            "runner_up_label": runner_label,
            "kpi_score": score,
            "cdr_efficiency": eff,
            "cost_band": cost,
            "cdr_potential_mtpa": cdr,
            "no_option": no_option,
            "storage_access": access,
            "nearest_storage_km": nearest_km,
            "storage_detail": sdetail,
            "transport_usd_per_tco2": (round(transport_cost_for(rec_key, tcost), 1)
                                       if (tcost and rec_key in PATHWAY_PAYLOAD) else None),
            "transport_band": (transport_band(transport_cost_for(rec_key, tcost))
                               if (tcost and rec_key in PATHWAY_PAYLOAD) else None),
            "transport_by_payload": tcost,   # {co2,bio_oil,slurry} $/tCO2 — for ranked-list cons
            "transport_capped": transport_capped,
            "transport_dest_well": tinfo.get("dest_well") if tinfo else None,
            "transport_dest_status": dest_status,
            "permitted_storage": permitted_storage,
            "feedstock_density": density,
            "residue_density_tco2_km2": dens_tco2_km2,
            "haul_supply_mtco2": supply_mt,
            "has_retrofit": has_retrofit,
            "avail": avail,
            "anchor_facility": anchor_str,
            "low_supply": low_supply,
            "forestry_residue_utilized": forestry_util,   # item 2 Option A: gross not net of pellet/bioenergy draw
            "nutrient_status": region.get("nutrient_status"),
            "dominant_feedstock": region.get("dominant_feedstock"),
            "rationale": rationale,
            "caveats": caveats,
            "flags": flags,
            "ranked": ranked,
        })

    records.sort(key=lambda r: r["fips"])
    with open(OUT, "w") as f:
        json.dump(records, f, ensure_ascii=False)

    # summary
    from collections import Counter
    bypath = Counter(r["recommended"] for r in records)
    byacc = Counter(r["storage_access"] for r in records)
    nlow = sum(1 for r in records if r["low_supply"])
    nbasin = sum(1 for r in records if r["storage_detail"]["in_basin"])
    nconc = sum(1 for r in records if r["feedstock_density"] == "concentrated")
    print(f"wrote {len(records)} county recommendations -> {OUT}")
    print("  by pathway:", dict(bypath))
    print("  storage access:", dict(byacc), f"| in-basin {nbasin}")
    print(f"  concentrated {nconc} | low-supply {nlow}")


if __name__ == "__main__":
    main()
