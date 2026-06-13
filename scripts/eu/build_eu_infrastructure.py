#!/usr/bin/env python3
"""
EU infrastructure layers for the NUTS-2 BiCRS map:

  data/processed/facilities_eu.json
    Biogenic point sources (pulp & paper, WtE, bioenergy, biogas/AD) — the curated European
    facilities already in the global tool (data/processed/facilities.json), which carry
    coordinates, type, biogenic-CO2 estimates and retrofit scores (compiled from company
    reports / E-PRTR / IEA Bioenergy). Filtered to EU-27 + UK + Norway.

  data/processed/storage_projects_eu.json
    CO2 storage projects / hubs (the "wells" equivalent — Europe has no Class V/VI). The
    operational/planned storage SITE records already in the global tool (Northern Lights,
    Porthos, Aramis, Greensand, Acorn, Ravenna, Endurance, HyNet, Sleipner, Snohvit, ...),
    plus a few curated additions, each with status.

  data/processed/wwtps_eu.json
    Large urban waste-water treatment plants (>= 150,000 PE) from the EEA/EMODnet UWWTD
    dataset (Waterbase), deduplicated.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROC = os.path.join(ROOT, "data", "processed")
RAW = os.path.join(ROOT, "data", "geo", "eu_raw")

FAC_IN = os.path.join(PROC, "facilities.json")
STORAGE_IN = os.path.join(PROC, "storage.json")
UWWTD_IN = os.path.join(RAW, "uwwtd_large.ndjson")

FAC_OUT = os.path.join(PROC, "facilities_eu.json")
PROJ_OUT = os.path.join(PROC, "storage_projects_eu.json")
WWTP_OUT = os.path.join(PROC, "wwtps_eu.json")

EU = {"AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC",
      "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK",
      "SVN", "ESP", "SWE", "GBR", "NOR"}

# A few curated storage projects/hubs to supplement the global tool's EU site records.
CURATED_PROJECTS = [
    {"name": "Bifrost / Project Greensand expansion", "country": "DNK", "status": "planned",
     "lat": 56.0, "lon": 4.8, "storage_type": "depleted_og",
     "source": "INEOS/Wintershall — Danish North Sea"},
    {"name": "Callisto Mediterranean CCS (Ravenna cluster)", "country": "ITA", "status": "planned",
     "lat": 44.4, "lon": 12.4, "storage_type": "depleted_og", "source": "Eni/Snam"},
    {"name": "Prinos CO2 Storage (Greece)", "country": "GRC", "status": "construction",
     "lat": 40.85, "lon": 24.3, "storage_type": "depleted_og", "source": "Energean — North Aegean"},
    {"name": "Pycasso (SW France/Spain)", "country": "FRA", "status": "planned",
     "lat": 43.4, "lon": -0.8, "storage_type": "depleted_og", "source": "Teréga/regional CCS"},
]


def build_facilities():
    fac = json.load(open(FAC_IN))
    out = []
    for f in fac:
        if f.get("country") not in EU:
            continue
        if f.get("lat") is None or f.get("lon") is None:
            continue
        if not f.get("existing", True):
            continue   # drop greenfield/developer/hub entries (not retrofit anchors)
        rec = {
            "name": f.get("name"),
            "type": f.get("type"),
            "country": f.get("country"),
            "lat": round(f["lat"], 4),
            "lon": round(f["lon"], 4),
            "capacity_note": f.get("capacity_note", ""),
            "est_biogenic_co2_mtpa": f.get("est_biogenic_co2_mtpa", {}),
            "retrofit_score": f.get("retrofit_score", "medium"),
            "existing": True,
            "operator": f.get("operator", ""),
            "source": f.get("source", "global tool (company reports / E-PRTR / IEA Bioenergy)"),
        }
        # Preserve the AD-cluster coverage radius (regional clusters reach beyond the default).
        if f.get("proc_radius_km"):
            rec["proc_radius_km"] = f["proc_radius_km"]
        out.append(rec)
    out.sort(key=lambda f: -((f.get("est_biogenic_co2_mtpa") or {}).get("value") or 0))
    return out


def build_storage_projects():
    st = json.load(open(STORAGE_IN))
    out = []
    for s in st:
        if s.get("country") not in EU or s.get("kind") != "site":
            continue
        if s.get("lat") is None or s.get("lon") is None:
            continue
        out.append({
            "name": s.get("name"),
            "country": s.get("country"),
            "status": s.get("status", "planned"),
            "storage_type": s.get("storage_type", "saline"),
            "capacity_mtpa": s.get("capacity_mtpa"),
            "lat": round(s["lat"], 4),
            "lon": round(s["lon"], 4),
            "source": s.get("source", ""),
        })
    for c in CURATED_PROJECTS:
        out.append(dict(c, capacity_mtpa=c.get("capacity_mtpa")))
    # dedup by name
    seen, dedup = set(), []
    for s in out:
        key = (s["name"] or "").lower()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(s)
    dedup.sort(key=lambda s: (s["status"] != "operational", s["name"]))
    return dedup


def build_wwtps():
    if not os.path.exists(UWWTD_IN):
        return []
    seen, out = set(), []
    with open(UWWTD_IN) as f:
        for line in f:
            r = json.loads(line)
            lat, lon = r.get("lat"), r.get("lon")
            if lat is None or lon is None:
                continue
            key = (round(lat, 3), round(lon, 3))
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "name": (r.get("name") or "WWTP").strip(),
                "type": "wwtp",
                "country": r.get("country"),
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "pe": r.get("pe"),
                "source": "EEA/EMODnet UWWTD (Waterbase) — large agglomeration (>=150k PE)",
            })
    out.sort(key=lambda w: -(w.get("pe") or 0))
    return out


def main():
    facs = build_facilities()
    projs = build_storage_projects()
    wwtps = build_wwtps()

    json.dump(facs, open(FAC_OUT, "w"), ensure_ascii=False, indent=1)
    json.dump(projs, open(PROJ_OUT, "w"), ensure_ascii=False, indent=1)
    json.dump(wwtps, open(WWTP_OUT, "w"), ensure_ascii=False)

    from collections import Counter
    print(f"facilities: {len(facs)}  by type {dict(Counter(f['type'] for f in facs))}")
    print(f"storage projects/hubs: {len(projs)}  by status {dict(Counter(p['status'] for p in projs))}")
    print(f"large WWTPs (>=150k PE): {len(wwtps)}")


if __name__ == "__main__":
    main()
