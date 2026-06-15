#!/usr/bin/env python3
"""Storage-access + retrofit-anchor helpers for the Canada CD engine (mirror of the US scope).

Canada's "wells" layer is curated CCS projects/hubs rather than EPA Class V/VI wells, but the
status vocabulary maps onto the shared grading: operational / "issued" (under construction) are
strong (near-available) storage; draft / pending are weaker signals.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/
from engine_core import num, haversine_km, _point_in_geometry, PROC_RADIUS_KM, AD_MIN_CAP_MTPA, ODT_TO_CO2  # noqa: E402

GOOD_KM = 100.0
MOD_KM = 300.0
STRONG_WELL = {"operational", "issued"}
ANY_WELL = {"operational", "issued", "draft", "pending"}


def co2_dry(region):
    return (num(region.get("ag_residues_odt_mt")) +
            num(region.get("forestry_residues_odt_mt"))) * ODT_TO_CO2


def co2_total(region):
    msw = num(region.get("msw_total_mt")) * num(region.get("msw_biogenic_frac"), 0.55)
    wet = (num(region.get("animal_manure_odt_mt")) +
           num(region.get("human_wwtp_odt_mt"))) * ODT_TO_CO2
    return co2_dry(region) + msw + wet


def min_vertex_km(lon, lat, geom):
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


def compute_avail_anchor(centroid, facilities):
    """Radius-based retrofit availability from the CD centroid (same rules/radii as the US)."""
    lon, lat = centroid[0], centroid[1]
    avail = {"pp": False, "wte": False, "ad": False}
    ad_cap = 0.0
    cands = []
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
        elif t == "bioenergy":
            if d <= PROC_RADIUS_KM["pulp_paper"]:
                cands.append((0, d, f))
        elif t == "wte":
            if d <= PROC_RADIUS_KM["wte"]:
                avail["wte"] = True; cands.append((1, d, f))
        elif t == "biogas_ad":
            rad = f.get("proc_radius_km") or PROC_RADIUS_KM["biogas_ad"]
            if d <= rad:
                ad_cap += (f.get("est_biogenic_co2_mtpa") or {}).get("value", 0) or 0
                cands.append((2, d, f))
    avail["ad"] = ad_cap >= AD_MIN_CAP_MTPA
    has_retrofit = len(cands) > 0
    anchor_name = anchor_type = None
    if cands:
        cands.sort(key=lambda c: (c[0], c[1]))
        best = cands[0][2]
        anchor_name, anchor_type = best.get("name"), best.get("type")
    return avail, has_retrofit, anchor_name, anchor_type


def compute_storage_access_cd(centroid, basins, wells):
    """Returns (access, nearest_km, detail dict). `nearest_well` here = nearest CCS project."""
    lon, lat = centroid[0], centroid[1]

    in_basin = None
    for b in basins:
        x0, y0, x1, y1 = b["bbox"]
        if x0 <= lon <= x1 and y0 <= lat <= y1 and _point_in_geometry(lon, lat, b["geometry"]):
            in_basin = b["name"]
            break

    nearest_basin_km = None
    nearest_basin = None
    for b in basins:
        cx, cy = b["centroid"]
        if abs(cx - lon) > 16 or abs(cy - lat) > 16:
            continue
        d = min_vertex_km(lon, lat, b["geometry"])
        if d is not None and (nearest_basin_km is None or d < nearest_basin_km):
            nearest_basin_km, nearest_basin = d, b["name"]

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
