#!/usr/bin/env python3
"""
EU NUTS-2 best-use-of-biomass engine.

Reuses the shared decision logic (scripts/engine_core.py: decide / kpi_score /
cdr_potential_mtpa / build_ranked / build_rationale / build_caveats_flags) — the SAME
Frontier framework as the global tool and the US county map. Inputs are computed at NUTS-2
granularity, mirroring the US county engine but retuned for European geography:

  storage access  — region centroid inside a CO2StoP storage formation = on-site (good);
                    else great-circle distance to the nearest formation boundary AND the
                    nearest CO2 storage project/hub. NUTS-2 + offshore-storage thresholds
                    (good < 150 km, moderate < 400 km). Much EU storage is offshore, so
                    inland regions legitimately read 'poor'.
  feedstock density — residue density (tCO2/km^2) from ENSPRESO biomass / NUTS-2 area
                    (regions are large, so no cross-region haul-radius sum).
  retrofit anchor — biogenic point sources (curated EU facilities) in the region (point-in-poly).
  low-supply guard — regions below a minimum recoverable supply are flagged (not forced).

Reads:  feedstocks_eu_nuts.json, storage_eu_formations.json, storage_projects_eu.json,
        facilities_eu.json, data/geo/eu_nuts.json
Writes: data/processed/recommendations_eu.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/
from engine_core import (
    PATHWAYS, ODT_TO_CO2, PROC_RADIUS_KM, AD_MIN_CAP_MTPA, num, haversine_km, _point_in_geometry,
    decide, kpi_score, cdr_potential_mtpa, build_ranked,
    build_rationale, build_caveats_flags,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROC = os.path.join(ROOT, "data", "processed")
GEO = os.path.join(ROOT, "data", "geo")

FEED = os.path.join(PROC, "feedstocks_eu_nuts.json")
FORMATIONS = os.path.join(PROC, "storage_eu_formations.json")
PROJECTS = os.path.join(PROC, "storage_projects_eu.json")
FACS = os.path.join(PROC, "facilities_eu.json")
NUTS = os.path.join(GEO, "eu_nuts.json")
OUT = os.path.join(PROC, "recommendations_eu.json")

# --- tunable thresholds (NUTS-2 scale; EU storage often offshore/clustered) ---
GOOD_KM = 150.0        # within this of qualifying storage -> good
MOD_KM = 400.0         # within this -> moderate
DENS_THRESH = 90.0     # residue density (tCO2/km^2) above which biomass is "concentrated"
MIN_SUPPLY_MT = 0.05   # total recoverable CO2 (Mt/yr) below which a region is "low supply"

STRONG_PROJ = {"operational", "construction"}
ANY_PROJ = {"operational", "construction", "planned"}


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
    """Distance (km) from (lon,lat) to a polygon boundary via nearest vertex (screening)."""
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
    return (num(region.get("ag_residues_odt_mt")) +
            num(region.get("forestry_residues_odt_mt"))) * ODT_TO_CO2


def co2_total(region):
    msw = num(region.get("msw_total_mt")) * num(region.get("msw_biogenic_frac"), 0.5)
    wet = (num(region.get("animal_manure_odt_mt")) +
           num(region.get("human_wwtp_odt_mt"))) * ODT_TO_CO2
    return co2_dry(region) + msw + wet


def annotate_facility_nuts(facilities, regions):
    """Tag each facility with the NUTS-2 id it sits in (point-in-polygon, bbox-prefiltered)."""
    rbb = [(r["properties"]["id"], r["geometry"], bbox_of_geom(r["geometry"])) for r in regions]
    for f in facilities:
        f["_nuts"] = None
        lon, lat = f.get("lon"), f.get("lat")
        if lon is None or lat is None:
            continue
        for rid, geom, (x0, y0, x1, y1) in rbb:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and _point_in_geometry(lon, lat, geom):
                f["_nuts"] = rid
                break


def compute_avail_anchor(centroid, facilities):
    """Retrofit availability for the gated pathways, by procurement radius from the NUTS-2
    centroid: beccs_pp <- pulp & paper mill within ~150 km; wte_ccs <- WtE plant within ~50 km;
    ad_ccs <- cumulative AD capacity within reach (discrete digesters ~15 km; regional AD
    clusters carry their own coverage radius) >= AD_MIN_CAP. Returns
    (avail, has_retrofit, anchor_name, anchor_type)."""
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


def compute_storage_access_nuts(centroid, formations, projects):
    """Returns (access, nearest_km, detail dict)."""
    lon, lat = centroid[0], centroid[1]

    # 1. inside a CO2StoP storage formation?
    in_form = None
    for b in formations:
        x0, y0, x1, y1 = b["bbox"]
        if x0 <= lon <= x1 and y0 <= lat <= y1 and _point_in_geometry(lon, lat, b["geometry"]):
            in_form = b["name"]
            break

    # 2. nearest formation boundary (prefilter by centroid proximity)
    nearest_form_km = nearest_form = None
    for b in formations:
        cx, cy = b["centroid"]
        if abs(cx - lon) > 12 or abs(cy - lat) > 12:
            continue
        d = min_vertex_km(lon, lat, b["geometry"])
        if d is not None and (nearest_form_km is None or d < nearest_form_km):
            nearest_form_km, nearest_form = d, b["name"]

    # 3. nearest storage project/hub
    def nearest_proj(statuses):
        best_km, best = None, None
        for p in projects:
            if p.get("status") not in statuses:
                continue
            d = haversine_km(lon, lat, p["lon"], p["lat"])
            if best_km is None or d < best_km:
                best_km, best = d, p["name"]
        return best_km, best
    strong_km, strong_name = nearest_proj(STRONG_PROJ)
    any_km, any_name = nearest_proj(ANY_PROJ)

    # 4. grade
    if in_form is not None:
        access = "good"
    elif (nearest_form_km is not None and nearest_form_km < GOOD_KM) or \
         (strong_km is not None and strong_km < GOOD_KM):
        access = "good"
    elif (nearest_form_km is not None and nearest_form_km < MOD_KM) or \
         (any_km is not None and any_km < MOD_KM):
        access = "moderate"
    else:
        access = "poor"

    candidates = [d for d in (0 if in_form else nearest_form_km, strong_km, any_km) if d is not None]
    nearest_km = round(min(candidates)) if candidates else None
    detail = {
        "in_formation": in_form,
        "nearest_formation": nearest_form,
        "nearest_formation_km": round(nearest_form_km) if nearest_form_km is not None else None,
        "nearest_project": any_name,
        "nearest_project_km": round(any_km) if any_km is not None else None,
    }
    return access, nearest_km, detail


def main():
    feeds = json.load(open(FEED))
    formations = json.load(open(FORMATIONS))
    projects = json.load(open(PROJECTS))
    facilities = json.load(open(FACS))
    regions = json.load(open(NUTS))["features"]

    # (retrofit availability is radius-based from each NUTS-2 centroid — no point-in-polygon.)

    records = []
    for region in feeds:
        centroid = region["centroid"]
        access, nearest_km, sdetail = compute_storage_access_nuts(centroid, formations, projects)

        area = region.get("area_km2") or 1.0
        dens_tco2_km2 = round(co2_dry(region) * 1e6 / area, 2)
        density = "concentrated" if dens_tco2_km2 >= DENS_THRESH else "diffuse"
        region["feedstock_density"] = density

        avail, has_retrofit, anchor_name, anchor_type = compute_avail_anchor(
            region["centroid"], facilities)

        rec_key, runner_key = decide(region, access, has_retrofit, avail)

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
                              avail, anchor_str)

        low_supply = co2_total(region) < MIN_SUPPLY_MT
        if low_supply:
            caveats = ["Negligible recoverable biomass in this region — recommendation is "
                       "indicative only."] + caveats
        if sdetail["in_formation"]:
            caveats = [f"Storage on-site: region overlaps the {sdetail['in_formation']} "
                       f"storage formation."] + caveats

        records.append({
            "id": region["id"],
            "name": region["name"],
            "country": region["parent"],
            "cntr": region["cntr"],
            "nuts_id": region["nuts_id"],
            "level": "nuts2",
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
            "has_retrofit": has_retrofit,
            "avail": avail,
            "anchor_facility": anchor_str,
            "low_supply": low_supply,
            "nutrient_status": region.get("nutrient_status"),
            "dominant_feedstock": region.get("dominant_feedstock"),
            "rationale": rationale,
            "caveats": caveats,
            "flags": flags,
            "ranked": ranked,
        })

    records.sort(key=lambda r: r["nuts_id"])
    with open(OUT, "w") as f:
        json.dump(records, f, ensure_ascii=False)

    from collections import Counter
    bypath = Counter(r["recommended"] for r in records)
    byacc = Counter(r["storage_access"] for r in records)
    print(f"wrote {len(records)} NUTS-2 recommendations -> {OUT}")
    print("  by pathway:", dict(bypath))
    print("  storage access:", dict(byacc),
          f"| in-formation {sum(1 for r in records if r['storage_detail']['in_formation'])}")
    print(f"  concentrated {sum(1 for r in records if r['feedstock_density']=='concentrated')}"
          f" | low-supply {sum(1 for r in records if r['low_supply'])}")


if __name__ == "__main__":
    main()
