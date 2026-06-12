#!/usr/bin/env python3
"""
US infrastructure layers for the county BiCRS map:

  data/processed/facilities_us_detailed.json
    Granular biogenic point sources + large WWTPs, from EPA GHGRP 2023 (Direct Point
    Emitters): facility coordinates + reported biogenic CO2. Types via NAICS:
      pulp_paper (322x) · wte (562213) · landfill (562212) · ethanol (311221/3251x) ·
      bioenergy (2211x/321x/611310) · wwtp (221320, sized by total reported emissions).
    A facility is kept if biogenic CO2 >= 25 kt/yr, OR it is biomass-dominated
    (biogenic >= 50% of reported CO2), OR it is a reporting sewage plant.

  data/processed/wells_us.json
    CO2 storage / injection points:
      - Operational geologic sequestration (GHGRP Subpart RR reporters: real MRV sites).
      - Class VI wells (issued / draft / pending) — curated from the EPA Class VI Data
        Repository (current to 2026).
      - Class V projects — curated biomass-injection / bio-oil sequestration (Vaulted, Charm).

Input: data/geo/us_raw/ghgrp/ghgp_data_2023.xlsx
"""
import json
import os

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROC = os.path.join(ROOT, "data", "processed")
RAW = os.path.join(ROOT, "data", "geo", "us_raw")
XLSX = os.path.join(RAW, "ghgrp", "ghgp_data_2023.xlsx")
WWTP_RAW = os.path.join(RAW, "wwtp_major.ndjson")

FAC_OUT = os.path.join(PROC, "facilities_us_detailed.json")
WELLS_OUT = os.path.join(PROC, "wells_us.json")
WWTP_OUT = os.path.join(PROC, "wwtps_us.json")

BIO_MIN = 25000.0  # metric tons biogenic CO2/yr threshold for point sources


def naics_type(code):
    c = str(code)
    if c.startswith("322"):
        return "pulp_paper"
    if c == "562213":
        return "wte"
    if c == "562212":
        return "landfill"
    if c == "311221" or c.startswith("3251"):
        return "ethanol"
    if c == "221320":
        return "wwtp"
    if c.startswith("2211") or c.startswith("321") or c == "611310" or c == "221330":
        return "bioenergy"
    return None


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def title_case(s):
    s = (s or "").strip()
    # Many GHGRP names are ALL CAPS; title-case those, leave mixed-case alone.
    return s.title() if s.isupper() else s


def retrofit_score(ftype, bio_mt):
    if ftype in ("pulp_paper", "ethanol", "wte"):
        return "high"
    if ftype == "bioenergy":
        return "high" if bio_mt >= 0.2 else "medium"
    if ftype == "wwtp":
        return "medium"
    return "low"  # landfill — dilute biogenic, lower retrofit attractiveness


def build_facilities(wb):
    ws = wb["Direct Point Emitters"]
    it = ws.iter_rows(values_only=True)
    for _ in range(4):
        next(it)
    facs = []
    for r in it:
        name, state = r[2], r[4]
        lat, lon = fnum(r[8]), fnum(r[9])
        naics = r[10]
        total_nonbio = fnum(r[13]) or 0.0
        bio = fnum(r[25]) or 0.0
        if lat is None or lon is None:
            continue
        ftype = naics_type(naics)
        if ftype is None or ftype == "wwtp":
            continue  # WWTPs handled in the dedicated Major-POTW layer (build_wwtps)

        biofrac = bio / (bio + total_nonbio) if (bio + total_nonbio) > 0 else 0
        if bio < BIO_MIN and biofrac < 0.5:
            continue
        size_mt = round(bio / 1e6, 4)
        note = f"{int(bio):,} t biogenic CO2/yr (GHGRP 2023)"

        facs.append({
            "name": title_case(name),
            "type": ftype,
            "country": "USA",
            "state": state,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "capacity_note": note,
            "est_biogenic_co2_mtpa": {"value": size_mt},
            "retrofit_score": retrofit_score(ftype, size_mt),
            "existing": True,
            "source": "EPA GHGRP 2023 (Direct Point Emitters)",
            "naics": str(naics),
        })
    facs.sort(key=lambda f: -f["est_biogenic_co2_mtpa"]["value"])
    return facs


def build_sequestration_wells(wb):
    """Operational geologic-sequestration reporters (GHGRP Subpart RR) — real MRV sites."""
    ws = wb["Geologic Sequestration of CO2"]
    it = ws.iter_rows(values_only=True)
    for _ in range(4):
        next(it)
    wells = []
    for r in it:
        name = title_case(r[2])
        lat, lon = fnum(r[8]), fnum(r[9])
        stored = fnum(r[12]) or 0.0
        if lat is None or lon is None:
            continue
        wells.append({
            "name": name,
            "kind": "sequestration",     # operational geologic sequestration (Subpart RR)
            "well_class": "VI/RR",
            "status": "operational",
            "state": r[4],
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "co2_mtpa": round(stored / 1e6, 4),
            "source": "EPA GHGRP 2023 (Subpart RR geologic sequestration)",
        })
    wells.sort(key=lambda w: -w["co2_mtpa"])
    return wells


# --- Curated Class VI wells (EPA Class VI Data Repository, current to 2026) and Class V
#     biomass-injection / bio-oil projects. Coordinates are project-site approximate. ---
CURATED_WELLS = [
    # ----- Class VI: ISSUED permits -----
    {"name": "ADM Decatur (CCS#1/#2)", "well_class": "VI", "status": "issued",
     "state": "IL", "lat": 39.8675, "lon": -88.885, "operator": "Archer Daniels Midland",
     "source": "EPA Class VI permit (Decatur, IL)"},
    {"name": "Red Trail Energy", "well_class": "VI", "status": "issued",
     "state": "ND", "lat": 46.879, "lon": -102.318, "operator": "Red Trail Energy",
     "source": "ND DMR Class VI (primacy)"},
    {"name": "Blue Flint / Harvestone", "well_class": "VI", "status": "issued",
     "state": "ND", "lat": 47.34, "lon": -101.43, "operator": "Harvestone Low Carbon Partners",
     "source": "ND DMR Class VI (primacy)"},
    {"name": "Minnkota Project Tundra", "well_class": "VI", "status": "issued",
     "state": "ND", "lat": 47.36, "lon": -101.86, "operator": "Minnkota Power",
     "source": "ND DMR Class VI (primacy)"},
    {"name": "PureField Carbon Capture", "well_class": "VI", "status": "issued",
     "state": "KS", "lat": 38.89, "lon": -98.86, "operator": "PureField Ingredients",
     "source": "EPA Region 7 Class VI permit (2026)"},
    {"name": "Wabash Carbon Services", "well_class": "VI", "status": "issued",
     "state": "IN", "lat": 39.53, "lon": -87.43, "operator": "Wabash Valley Resources",
     "source": "EPA Region 5 Class VI permit"},
    # ----- Class VI: DRAFT / proposed (representative, 2026) -----
    {"name": "Hackberry Carbon Sequestration", "well_class": "VI", "status": "draft",
     "state": "LA", "lat": 29.99, "lon": -93.34, "operator": "Sempra / Hackberry",
     "source": "EPA/LA Class VI draft permit"},
    {"name": "CapturePoint Central Louisiana", "well_class": "VI", "status": "draft",
     "state": "LA", "lat": 31.3, "lon": -92.4, "operator": "CapturePoint Solutions",
     "source": "LA Class VI (primacy) draft"},
    {"name": "Bayou Bend CCS", "well_class": "VI", "status": "pending",
     "state": "TX", "lat": 29.76, "lon": -93.95, "operator": "Chevron/Talos/Equinor",
     "source": "EPA Region 6 Class VI application"},
    {"name": "Tenaska Bison Lasso", "well_class": "VI", "status": "pending",
     "state": "TX", "lat": 32.5, "lon": -97.0, "operator": "Tenaska",
     "source": "EPA Region 6 Class VI application"},
    {"name": "Heartland Greenway (Navigator)", "well_class": "VI", "status": "pending",
     "state": "IL", "lat": 39.9, "lon": -89.6, "operator": "Navigator CO2",
     "source": "EPA Region 5 Class VI application"},
    {"name": "Wyoming Frontier CarbonSAFE", "well_class": "VI", "status": "pending",
     "state": "WY", "lat": 41.79, "lon": -107.2, "operator": "Frontier/CarbonSAFE",
     "source": "WY DEQ Class VI (primacy)"},
    # ----- Class V: biomass injection / bio-oil sequestration -----
    {"name": "Vaulted Deep (Kansas)", "well_class": "V", "status": "operational",
     "state": "KS", "lat": 37.7, "lon": -97.9, "operator": "Vaulted Deep",
     "source": "Vaulted Deep — biomass/organic-waste slurry injection (Class V)"},
    {"name": "Vaulted Deep (Los Angeles)", "well_class": "V", "status": "operational",
     "state": "CA", "lat": 33.9, "lon": -118.2, "operator": "Vaulted Deep",
     "source": "Vaulted Deep — biosolids slurry injection (Class V)"},
    {"name": "Charm Industrial (Permian)", "well_class": "V", "status": "operational",
     "state": "TX", "lat": 31.9, "lon": -102.1, "operator": "Charm Industrial",
     "source": "Charm Industrial — bio-oil injection into EOR/saltwater-disposal wells"},
    {"name": "Charm Industrial (Central Valley)", "well_class": "V", "status": "operational",
     "state": "CA", "lat": 36.3, "lon": -119.8, "operator": "Charm Industrial",
     "source": "Charm Industrial — bio-oil injection"},
]


def build_wwtps():
    """Major NPDES POTWs (design flow >= 1 MGD) from EPA FRS — large WWTP point sources."""
    out = []
    if not os.path.exists(WWTP_RAW):
        return out
    with open(WWTP_RAW) as f:
        for line in f:
            a = json.loads(line)
            lat, lon = fnum(a.get("FAC_LAT")), fnum(a.get("FAC_LONG"))
            if lat is None or lon is None:
                continue
            out.append({
                "name": title_case(a.get("CWP_NAME") or ""),
                "type": "wwtp",
                "state": a.get("CWP_STATE"),
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "source": "EPA FRS / NPDES — Major POTW (>=1 MGD)",
            })
    return out


def main():
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    facs = build_facilities(wb)
    seq = build_sequestration_wells(wb)
    wwtps = build_wwtps()

    # Merge operational sequestration + curated Class VI/V into one wells layer.
    wells = list(seq)
    for w in CURATED_WELLS:
        w = dict(w)
        w.setdefault("kind", "class6" if w["well_class"] in ("VI", "VI/RR") else "class5")
        w.setdefault("co2_mtpa", None)
        wells.append(w)

    with open(FAC_OUT, "w") as f:
        json.dump(facs, f, ensure_ascii=False, indent=1)
    with open(WELLS_OUT, "w") as f:
        json.dump(wells, f, ensure_ascii=False, indent=1)
    with open(WWTP_OUT, "w") as f:
        json.dump(wwtps, f, ensure_ascii=False)

    from collections import Counter
    print(f"facilities: {len(facs)}  by type {dict(Counter(x['type'] for x in facs))}")
    print(f"wells: {len(wells)}  "
          f"(RR operational {len(seq)}, curated {len(CURATED_WELLS)})  "
          f"by class {dict(Counter(x['well_class'] for x in wells))}")
    print(f"wwtps (Major POTWs): {len(wwtps)}")


if __name__ == "__main__":
    main()
