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
    PATHWAYS, ODT_TO_CO2, num, haversine_km, _point_in_geometry,
    decide, kpi_score, cdr_potential_mtpa, build_ranked,
    build_rationale, build_caveats_flags,
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
OUT = os.path.join(PROC, "recommendations_us.json")

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


def compute_retrofit_county(fips, facilities):
    """Biogenic point sources physically in the county -> retrofit anchor (mirrors the
    global compute_retrofit, matched by _county)."""
    in_region = [f for f in facilities if f.get("_county") == fips and f.get("existing", True)]
    qualifying = [f for f in in_region if f.get("retrofit_score") in ("high", "medium")]
    has_retrofit = len(qualifying) > 0
    has_pp_be = any(f.get("type") in ("pulp_paper", "bioenergy") for f in qualifying)
    anchor_name = anchor_type = None
    if in_region:
        rank = {"high": 0, "medium": 1, "low": 2}

        def keyfn(f):
            pref = 0 if f.get("type") in ("pulp_paper", "bioenergy") else 1
            return (pref, rank.get(f.get("retrofit_score"), 3))
        best = sorted(in_region, key=keyfn)[0]
        anchor_name, anchor_type = best.get("name"), best.get("type")
    return has_retrofit, anchor_name, anchor_type, has_pp_be


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
    basins = json.load(open(BASINS))
    wells = json.load(open(WELLS))
    facilities = json.load(open(FACS))
    counties = json.load(open(COUNTIES))["features"]

    annotate_facility_counties(facilities, counties)

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

        # density from real area + haul-radius supply
        area = region.get("area_km2") or 1.0
        dens_tco2_km2 = round(co2_dry(region) * 1e6 / area, 2)
        supply_mt = round(haul_supply(lon, lat), 3)
        # Concentrated = spatially dense biomass AND enough total within a haul radius to
        # anchor a central plant; otherwise distributed/diffuse (favours injection/bio-oil).
        density = ("concentrated" if (dens_tco2_km2 >= DENS_THRESH and supply_mt >= CONC_SUPPLY_MT)
                   else "diffuse")
        region["feedstock_density"] = density   # feed into shared decide()

        has_retrofit, anchor_name, anchor_type, has_pp_be = compute_retrofit_county(
            region["fips"], facilities)

        rec_key, runner_key = decide(region, access, has_retrofit, has_pp_be)

        nutrient_alt = False
        if (region.get("nutrient_status") == "excess"
                and rec_key in ("beccs", "beccs_pp", "bio_oil", "injection")
                and runner_key != "burial"):
            runner_key, nutrient_alt = "burial", True

        score = kpi_score(rec_key, access)
        cdr = cdr_potential_mtpa(region, rec_key)
        rationale = build_rationale(region, rec_key, access, nearest_km,
                                    has_retrofit, anchor_name, anchor_type)
        caveats, flags = build_caveats_flags(region, rec_key, runner_key, False,
                                             anchor_type, nutrient_alt)
        anchor_str = f"{anchor_name} ({anchor_type})" if anchor_name else None
        ranked = build_ranked(region, rec_key, runner_key, access, nearest_km,
                              has_pp_be, anchor_str)

        low_supply = co2_total(region) < MIN_SUPPLY_MT
        if low_supply:
            caveats = ["Negligible recoverable biomass in this county — aggregate with "
                       "neighbouring counties; recommendation is indicative only."] + caveats

        if sdetail["in_basin"]:
            caveats = [f"Storage on-site: county overlaps the {sdetail['in_basin']} saline "
                       f"storage formation."] + caveats

        records.append({
            "id": region["id"],
            "name": region["name"],
            "state": region["state"],
            "fips": region["fips"],
            "level": "county",
            "recommended": rec_key,
            "recommended_label": PATHWAYS[rec_key]["label"],
            "runner_up": runner_key,
            "runner_up_label": PATHWAYS[runner_key]["label"],
            "kpi_score": score,
            "cdr_efficiency": PATHWAYS[rec_key]["cdr_efficiency"],
            "cost_band": PATHWAYS[rec_key]["cost_band"],
            "cdr_potential_mtpa": cdr,
            "storage_access": access,
            "nearest_storage_km": nearest_km,
            "storage_detail": sdetail,
            "feedstock_density": density,
            "residue_density_tco2_km2": dens_tco2_km2,
            "haul_supply_mtco2": supply_mt,
            "has_retrofit": has_retrofit,
            "has_pp_be": has_pp_be,
            "anchor_facility": anchor_str,
            "low_supply": low_supply,
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
