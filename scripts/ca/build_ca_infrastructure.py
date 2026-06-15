#!/usr/bin/env python3
"""
Canada infrastructure layers for the CD-level BiCRS map.

Canada's facility GHG data (ECCC GHGRP) does not publish a clean biogenic-CO2 column and is
served behind signed/SPA endpoints, so — as in the global tool — Canadian biogenic point
sources are a CURATED set: the major operating pulp & paper mills, waste-to-energy plants,
fuel-ethanol plants, biomass-energy stations and biogas/AD clusters, seeded from the records
already in the global tool (data/processed/facilities.json) and extended for CD-scale
coverage. Each facility is reverse-geocoded to its province via point-in-CD.

  data/processed/facilities_ca_detailed.json   biogenic point sources (+ AD clusters for the gate)
  data/processed/wells_ca.json                 Canadian CCS projects / storage hubs (the "wells" layer)
  data/processed/wwtps_ca.json                 large municipal WWTPs (major urban POTWs)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/
from engine_core import _point_in_geometry  # noqa: E402
from build_cd_common import PRUID_TO_ABBR  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROC = os.path.join(ROOT, "data", "processed")
CD_GEO = os.path.join(ROOT, "data", "geo", "ca_cd.json")
GLOBAL_FAC = os.path.join(PROC, "facilities.json")

FAC_OUT = os.path.join(PROC, "facilities_ca_detailed.json")
WELLS_OUT = os.path.join(PROC, "wells_ca.json")
WWTP_OUT = os.path.join(PROC, "wwtps_ca.json")

# Rough biogenic-CO2 scale by type (Mtpa) when not otherwise known — for sizing/marker only.
DEFAULT_MT = {"pulp_paper": 0.45, "wte": 0.15, "ethanol": 0.12, "bioenergy": 0.20,
              "landfill": 0.05, "biogas_ad": 0.04}


def retrofit_score(ftype, mt):
    if ftype in ("pulp_paper", "ethanol", "wte"):
        return "high"
    if ftype == "bioenergy":
        return "high" if mt >= 0.2 else "medium"
    if ftype == "biogas_ad":
        return "medium"
    return "low"


# --- Curated additions (operating facilities; coordinates are site-approximate) ---
# (name, type, lat, lon, approx biogenic Mtpa or None)
CURATED_FAC = [
    # ---- Pulp & paper (additions beyond the global seed) ----
    ("Catalyst Powell River Mill (Paper Excellence)", "pulp_paper", 49.87, -124.55, 0.4),
    ("Harmac Pacific Pulp Mill (Nanaimo)", "pulp_paper", 49.13, -123.85, 0.4),
    ("Cariboo Pulp & Paper (Quesnel)", "pulp_paper", 52.97, -122.50, 0.5),
    ("West Fraser Quesnel River Pulp", "pulp_paper", 52.96, -122.46, 0.45),
    ("Howe Sound Pulp & Paper (Port Mellon)", "pulp_paper", 49.52, -123.48, 0.45),
    ("Prince George Pulp & Paper (Canfor)", "pulp_paper", 53.92, -122.72, 0.5),
    ("AV Group Nackawic Pulp Mill (NB)", "pulp_paper", 45.99, -67.24, 0.35),
    ("Twin Rivers Edmundston Mill (NB)", "pulp_paper", 47.37, -68.33, 0.3),
    ("Port Hawkesbury Paper (NS)", "pulp_paper", 45.61, -61.36, 0.35),
    ("Kruger Wayagamack / Trois-Rivières (QC)", "pulp_paper", 46.35, -72.55, 0.4),
    ("White Birch — Stadacona Mill (Québec City)", "pulp_paper", 46.83, -71.20, 0.3),
    ("Resolute Alma Pulp & Paper (QC)", "pulp_paper", 48.55, -71.65, 0.35),
    ("Domtar Dryden Pulp Mill (ON)", "pulp_paper", 49.78, -92.83, 0.4),
    ("Terrace Bay Pulp Mill (AV Terrace Bay, ON)", "pulp_paper", 48.78, -87.10, 0.35),
    # ---- Waste-to-energy ----
    ("Metro Vancouver Waste-to-Energy (Burnaby)", "wte", 49.21, -122.95, 0.18),
    ("Incinérateur de la Ville de Québec", "wte", 46.83, -71.27, 0.14),
    ("Charlottetown Energy-from-Waste (PEI)", "wte", 46.25, -63.13, 0.03),
    # ---- Fuel ethanol ----
    ("Greenfield Global Chatham Ethanol (ON)", "ethanol", 42.40, -82.19, 0.18),
    ("Greenfield Global Johnstown Ethanol (ON)", "ethanol", 44.75, -75.45, 0.18),
    ("Greenfield Global Varennes Ethanol (QC)", "ethanol", 45.68, -73.43, 0.16),
    ("IGPC Ethanol (Aylmer, ON)", "ethanol", 42.77, -80.98, 0.15),
    ("Suncor St. Clair Ethanol (Mooretown, ON)", "ethanol", 42.85, -82.40, 0.12),
    ("Cenovus Lloydminster Ethanol (SK)", "ethanol", 53.28, -110.00, 0.10),
    ("Husky Minnedosa Ethanol (MB)", "ethanol", 50.25, -99.84, 0.10),
    ("Permolex Red Deer (AB)", "ethanol", 52.27, -113.81, 0.10),
    ("Pound-Maker Ethanol (Lanigan, SK)", "ethanol", 51.85, -105.03, 0.08),
    # ---- Biomass energy ----
    ("Williams Lake Bioenergy (BC)", "bioenergy", 52.13, -122.14, 0.2),
    ("Fort St. James Green Energy (BC)", "bioenergy", 54.44, -124.25, 0.15),
    # ---- Biogas / AD clusters (cumulative; carry their own coverage radius) ----
    ("Saint-Hyacinthe Biométhanisation (QC)", "biogas_ad", 45.63, -72.95, 0.05),
    ("Ontario AD/RNG Cluster (Golden Horseshoe)", "biogas_ad", 43.55, -79.75, 0.07),
    ("Lethbridge Biogas / Southern AB AD Cluster", "biogas_ad", 49.70, -112.80, 0.04),
    ("Fraser Valley AD Cluster (BC)", "biogas_ad", 49.10, -122.30, 0.04),
]

# Curated Canadian CCS projects / storage hubs (the "wells" equivalent). Status mapped to
# the shared engine's vocabulary: operational; "issued" = under construction (near-available);
# "pending" = announced/appraisal. No US-style Class V/VI in Canada.
CURATED_WELLS = [
    {"name": "Quest CCS (Shell Scotford)", "status": "operational", "prov": "AB",
     "lat": 53.73, "lon": -113.07, "operator": "Shell Canada",
     "source": "Quest CCS — operational dedicated geologic storage"},
    {"name": "Alberta Carbon Trunk Line (ACTL)", "status": "operational", "prov": "AB",
     "lat": 53.95, "lon": -113.10, "operator": "Wolf Midstream",
     "source": "ACTL — operational CO2 transport & storage/EOR"},
    {"name": "Aquistore (Boundary Dam)", "status": "operational", "prov": "SK",
     "lat": 49.12, "lon": -103.00, "operator": "PTRC",
     "source": "Aquistore — operational deep saline storage"},
    {"name": "Boundary Dam CCS (SaskPower)", "status": "operational", "prov": "SK",
     "lat": 49.09, "lon": -103.02, "operator": "SaskPower",
     "source": "Boundary Dam Unit 3 — operational power-CCS"},
    {"name": "Weyburn-Midale CO2-EOR & Storage", "status": "operational", "prov": "SK",
     "lat": 49.66, "lon": -103.85, "operator": "Whitecap Resources",
     "source": "Weyburn-Midale — large CO2-EOR with monitored storage"},
    {"name": "Entropy Glacier Gas Plant CCS", "status": "operational", "prov": "AB",
     "lat": 56.20, "lon": -117.60, "operator": "Entropy Inc.",
     "source": "Glacier Phase 1 — operational CCS"},
    {"name": "Polaris CCS / Atlas Carbon Storage Hub (Scotford)", "status": "issued", "prov": "AB",
     "lat": 53.73, "lon": -113.05, "operator": "Shell Canada",
     "source": "Polaris/Atlas — under development at Scotford"},
    {"name": "Pathways Alliance CCS Hub (Cold Lake)", "status": "pending", "prov": "AB",
     "lat": 54.46, "lon": -110.18, "operator": "Pathways Alliance",
     "source": "Oil-sands CCS trunkline + Cold Lake storage hub (proposed)"},
    {"name": "Enbridge Wabamun Carbon Hub", "status": "pending", "prov": "AB",
     "lat": 53.55, "lon": -114.50, "operator": "Enbridge / Capital Power",
     "source": "Wabamun open-access carbon hub (proposed)"},
    {"name": "Bison Low Carbon Ventures (Whitecap)", "status": "pending", "prov": "SK",
     "lat": 50.40, "lon": -102.80, "operator": "Whitecap Resources",
     "source": "Saskatchewan saline storage hub (appraisal)"},
    {"name": "Meadowbrook / Carbon Connect (Strathcona)", "status": "pending", "prov": "AB",
     "lat": 53.52, "lon": -113.10, "operator": "various",
     "source": "Alberta industrial-heartland storage hub (appraisal)"},
    {"name": "Genesee Carbon Conversion / CCS (Capital Power)", "status": "pending", "prov": "AB",
     "lat": 53.30, "lon": -114.30, "operator": "Capital Power",
     "source": "Genesee CCS (appraisal)"},
]

# Curated large municipal WWTPs (major urban water-resource-recovery plants).
CURATED_WWTP = [
    ("Ashbridges Bay WWTP (Toronto)", 43.66, -79.31),
    ("Highland Creek WWTP (Toronto)", 43.78, -79.13),
    ("Station d'épuration Jean-R.-Marcotte (Montréal)", 45.66, -73.50),
    ("Annacis Island WWTP (Metro Vancouver)", 49.16, -122.95),
    ("Iona Island WWTP (Metro Vancouver)", 49.21, -123.21),
    ("Lou Romano WRRF (Windsor)", 42.30, -83.07),
    ("Bonnybrook WWTP (Calgary)", 51.02, -114.00),
    ("Gold Bar WWTP (Edmonton)", 53.55, -113.40),
    ("North End WWTP (Winnipeg)", 49.93, -97.10),
    ("Robert O. Pickard Centre (Ottawa)", 45.46, -75.50),
    ("Woodward WWTP (Hamilton)", 43.27, -79.78),
    ("Station d'épuration Est (Québec City)", 46.86, -71.18),
    ("Adelaide Pollution Control (London, ON)", 43.02, -81.22),
    ("Greenway WWTP (London, ON)", 42.95, -81.29),
    ("Regina WWTP (SK)", 50.50, -104.55),
    ("Halifax (Halifax Water) Dartmouth WWTF", 44.66, -63.55),
]


def annotate_prov(items, cds):
    cbb = []
    for c in cds:
        g = c["geometry"]
        xs, ys = [], []

        def walk(coords):
            if isinstance(coords[0], (int, float)):
                xs.append(coords[0]); ys.append(coords[1])
            else:
                for x in coords:
                    walk(x)
        walk(g["coordinates"])
        cbb.append((c["properties"]["prov"], g, (min(xs), min(ys), max(xs), max(ys))))
    for it in items:
        lon, lat = it.get("lon"), it.get("lat")
        it.setdefault("prov", "")
        if lon is None or lat is None or it.get("prov"):
            continue
        for prov, geom, (x0, y0, x1, y1) in cbb:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and _point_in_geometry(lon, lat, geom):
                it["prov"] = prov
                break


def seed_from_global():
    """Canadian facilities already in the global tool, normalised to the detailed schema."""
    out = []
    recs = json.load(open(GLOBAL_FAC))
    recs = recs if isinstance(recs, list) else list(recs.values())
    for r in recs:
        if r.get("country") not in ("CAN", "Canada"):
            continue
        ftype = r.get("type")
        mt = (r.get("est_biogenic_co2_mtpa") or {}).get("value") if isinstance(
            r.get("est_biogenic_co2_mtpa"), dict) else r.get("est_biogenic_co2_mtpa")
        mt = mt if mt else DEFAULT_MT.get(ftype, 0.1)
        fac = {
            "name": r["name"], "type": ftype, "country": "CAN",
            "lat": round(r["lat"], 4), "lon": round(r["lon"], 4),
            "capacity_note": r.get("capacity_note") or "estimated biogenic CO2 (curated)",
            "est_biogenic_co2_mtpa": {"value": round(mt, 4)},
            "retrofit_score": r.get("retrofit_score") or retrofit_score(ftype, mt),
            "existing": r.get("existing", True),
            "source": r.get("source") or "Global BiCRS tool (curated Canadian facility)",
        }
        if ftype == "biogas_ad":
            fac["proc_radius_km"] = r.get("proc_radius_km", 40)
        out.append(fac)
    return out


def main():
    cds = json.load(open(CD_GEO))["features"]

    facs = seed_from_global()
    seen = {(f["name"], round(f["lat"], 2), round(f["lon"], 2)) for f in facs}
    for name, ftype, lat, lon, mt in CURATED_FAC:
        key = (name, round(lat, 2), round(lon, 2))
        if key in seen:
            continue
        mt = mt if mt else DEFAULT_MT.get(ftype, 0.1)
        fac = {
            "name": name, "type": ftype, "country": "CAN",
            "lat": lat, "lon": lon,
            "capacity_note": "estimated biogenic CO2 (curated; capacity-based)",
            "est_biogenic_co2_mtpa": {"value": round(mt, 4)},
            "retrofit_score": retrofit_score(ftype, mt),
            "existing": True,
            "source": "Curated (industry registries / company reports)",
        }
        if ftype == "biogas_ad":
            fac["proc_radius_km"] = 40   # regional AD cluster coverage
        facs.append(fac)

    wells = []
    for w in CURATED_WELLS:
        w = dict(w)
        w["kind"] = "project"
        w["co2_mtpa"] = w.get("co2_mtpa")
        wells.append(w)

    wwtps = [{"name": n, "type": "wwtp", "lat": lat, "lon": lon,
              "source": "Curated (major Canadian municipal WWTP)"} for n, lat, lon in CURATED_WWTP]

    annotate_prov(facs, cds)
    annotate_prov(wwtps, cds)

    facs.sort(key=lambda f: -f["est_biogenic_co2_mtpa"]["value"])
    with open(FAC_OUT, "w") as f:
        json.dump(facs, f, ensure_ascii=False, indent=1)
    with open(WELLS_OUT, "w") as f:
        json.dump(wells, f, ensure_ascii=False, indent=1)
    with open(WWTP_OUT, "w") as f:
        json.dump(wwtps, f, ensure_ascii=False)

    from collections import Counter
    print(f"facilities: {len(facs)}  by type {dict(Counter(x['type'] for x in facs))}")
    print(f"wells/projects: {len(wells)}  by status {dict(Counter(x['status'] for x in wells))}")
    print(f"wwtps: {len(wwtps)}")


if __name__ == "__main__":
    main()
