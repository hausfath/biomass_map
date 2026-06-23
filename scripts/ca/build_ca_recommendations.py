#!/usr/bin/env python3
"""
Canada census-division best-use-of-biomass engine.

Reuses the shared decision logic (scripts/engine_core.py) exactly like the US county scope,
so Canada encodes the SAME Frontier framework. Only the *inputs* are computed at CD
granularity:

  storage access  — point-in-basin (CD centroid inside a curated Canadian storage basin =
                    storage on-site) else great-circle distance to the nearest basin boundary
                    AND the nearest operational/under-construction CCS project. CD-scale
                    thresholds (good < 100 km, moderate < 300 km), matching the US scope.
  feedstock density — residue density (tCO2/km^2) + an 80 km haul-radius supply sum.
  retrofit anchor — biogenic point sources within procurement radius of the CD centroid.
  low-supply guard — CDs below a minimum recoverable supply are flagged (not forced).

Reads:  feedstocks_ca_cd.json, storage_ca_basins.json, wells_ca.json,
        facilities_ca_detailed.json, data/geo/ca_cd.json
Writes: data/processed/recommendations_ca.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/
from engine_core import (  # noqa: E402
    PATHWAYS, ODT_TO_CO2, NO_OPTION_RATIONALE,
    num, haversine_km, _point_in_geometry,
    decide, kpi_score, cdr_potential_mtpa, build_ranked, build_ranked_none,
    build_rationale, build_caveats_flags,
)
from build_ca_recommendations_helpers import (  # noqa: E402
    compute_avail_anchor, compute_storage_access_cd, co2_dry, co2_total,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROC = os.path.join(ROOT, "data", "processed")
GEO = os.path.join(ROOT, "data", "geo")

FEED = os.path.join(PROC, "feedstocks_ca_cd.json")
BASINS = os.path.join(PROC, "storage_ca_basins.json")
WELLS = os.path.join(PROC, "wells_ca.json")
FACS = os.path.join(PROC, "facilities_ca_detailed.json")
OUT = os.path.join(PROC, "recommendations_ca.json")

# Cross-border storage: CO2 storage doesn't stop at the border, so a Canadian CD is also scored
# against US storage (e.g. the North Dakota Class VI wells just across from southern Saskatchewan,
# and the US side of the Williston Basin). Loaded if present (US pipeline must have run).
WELLS_US = os.path.join(PROC, "wells_us.json")
BASINS_US = os.path.join(PROC, "storage_us_basins.json")


def _load_opt(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []

HAUL_KM = 80.0
DENS_THRESH = 120.0
CONC_SUPPLY_MT = 0.75
MIN_SUPPLY_MT = 0.02


def main():
    feeds = json.load(open(FEED))
    basins = json.load(open(BASINS)) + _load_opt(BASINS_US)
    wells = json.load(open(WELLS)) + _load_opt(WELLS_US)
    facilities = json.load(open(FACS))

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

        access, nearest_km, sdetail = compute_storage_access_cd(centroid, basins, wells)

        area = region.get("area_km2") or 1.0
        dens_tco2_km2 = round(co2_dry(region) * 1e6 / area, 2)
        supply_mt = round(haul_supply(lon, lat), 3)
        density = ("concentrated" if (dens_tco2_km2 >= DENS_THRESH and supply_mt >= CONC_SUPPLY_MT)
                   else "diffuse")
        region["feedstock_density"] = density

        avail, has_retrofit, anchor_name, anchor_type = compute_avail_anchor(centroid, facilities)

        rec_key, runner_key, eff_dom = decide(region, access, has_retrofit, avail)
        no_option = (rec_key == "none")
        anchor_str = f"{anchor_name} ({anchor_type})" if anchor_name else None
        rregion = region if eff_dom == region.get("dominant_feedstock") else dict(
            region, dominant_feedstock=eff_dom)

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
            eff = PATHWAYS[rec_key]["cdr_efficiency"]
            cost = PATHWAYS[rec_key]["cost_band"]
            cdr = cdr_potential_mtpa(rregion, rec_key)
            rec_label = PATHWAYS[rec_key]["label"]
            runner_label = PATHWAYS[runner_key]["label"]
            rationale = build_rationale(rregion, rec_key, access, nearest_km,
                                        has_retrofit, anchor_name, anchor_type)
            ranked = build_ranked(rregion, rec_key, runner_key, access, nearest_km,
                                  avail, anchor_str)
        caveats, flags = build_caveats_flags(region, rec_key, runner_key, False,
                                             anchor_type, nutrient_alt)

        low_supply = co2_total(region) < MIN_SUPPLY_MT
        if low_supply:
            caveats = ["Negligible recoverable biomass in this census division — aggregate "
                       "with neighbours; recommendation is indicative only."] + caveats
        if sdetail["in_basin"]:
            caveats = [f"Storage on-site: CD overlaps the {sdetail['in_basin']} basin."] + caveats

        records.append({
            "id": region["id"],
            "name": region["name"],
            "prov": region["prov"],
            "cduid": region["cduid"],
            "level": "census_division",
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
            "feedstock_density": density,
            "residue_density_tco2_km2": dens_tco2_km2,
            "haul_supply_mtco2": supply_mt,
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

    records.sort(key=lambda r: r["cduid"])
    with open(OUT, "w") as f:
        json.dump(records, f, ensure_ascii=False)

    from collections import Counter
    bypath = Counter(r["recommended"] for r in records)
    byacc = Counter(r["storage_access"] for r in records)
    nlow = sum(1 for r in records if r["low_supply"])
    nbasin = sum(1 for r in records if r["storage_detail"]["in_basin"])
    nconc = sum(1 for r in records if r["feedstock_density"] == "concentrated")
    print(f"wrote {len(records)} CD recommendations -> {OUT}")
    print("  by pathway:", dict(bypath))
    print("  storage access:", dict(byacc), f"| in-basin {nbasin}")
    print(f"  concentrated {nconc} | low-supply {nlow}")


if __name__ == "__main__":
    main()
