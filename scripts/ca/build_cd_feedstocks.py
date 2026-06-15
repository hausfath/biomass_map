#!/usr/bin/env python3
"""
Census-division feedstock supply for the Canada BiCRS map (293 CDs).

Method — "province totals, spatially disaggregated to census divisions" (mirrors the US
county pipeline). Each feedstock's *within-province distribution* comes from authoritative
CD-level data; each CD is then scaled so the CDs of a province sum exactly to that province's
total already in the global tool (data/processed/feedstocks_can_sub.json, CA-<Province>
records, anchored to StatCan / NRCan / IEA). Real CD geography AND exact consistency with the
province numbers; per-CD factors only need to be RELATIVELY correct within a province.

CD distribution signals (StatCan 2021 Census of Agriculture + Census of Population, by DGUID):
  ag residues  <- area (ha) of residue-producing field crops x per-ha residue weight   [32100309]
  manure       <- cattle (dairy-weighted) + pigs + poultry, by relative manure-VS weights
                  [32100370 cattle, 32100372 pigs, 32100374 poultry]
  MSW & WWTP   <- CD population, 2021 Census                                            [98100002]
  forestry     <- CD land area (proxy within province; weakest layer, like the US woodland proxy)

Output: data/processed/feedstocks_ca_cd.json
"""
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/
from engine_core import ODT_TO_CO2  # noqa: E402
from build_cd_common import PRUID_TO_NAME, PRUID_TO_ABBR, cduid_from_dguid  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(ROOT, "data", "geo", "ca_raw")
PROC = os.path.join(ROOT, "data", "processed")

CROPS_CSV = os.path.join(RAW, "32100309.csv")
CATTLE_CSV = os.path.join(RAW, "32100370.csv")
PIGS_CSV = os.path.join(RAW, "32100372.csv")
POULTRY_CSV = os.path.join(RAW, "32100374.csv")
POP_CSV = os.path.join(RAW, "98100002.csv")
CD_GEO = os.path.join(ROOT, "data", "geo", "ca_cd.json")
PROV_FEED = os.path.join(PROC, "feedstocks_can_sub.json")
OUT = os.path.join(PROC, "feedstocks_ca_cd.json")

# Residue-producing field crops -> relative recoverable-residue weight per hectare
# (~ national yield x residue-to-product ratio x recoverable fraction, RELATIVE units;
#  only within-province relative weighting matters since we scale to province totals).
# "Corn for grain" (not silage), top-level "*, total" rows only (no double counting).
RESIDUE_CROPS = {
    "Wheat, total": 1.3, "Oats": 1.0, "Barley": 1.2, "Mixed grains": 1.1,
    "Corn for grain": 3.0, "Rye, total": 1.2, "Canola (rapeseed)": 1.5,
    "Soybeans": 1.0, "Flaxseed": 1.1, "Dry field peas": 0.7, "Chick peas": 0.6,
    "Lentils": 0.6, "Faba beans": 0.8, "Triticale": 1.2, "Buckwheat": 0.7,
    "Mustard seed": 0.9, "Sunflower seed": 1.5, "Canary seed": 0.8,
}

# Relative manure (collectable volatile-solids) weights, per head/yr.
W_CATTLE_OTHER = 0.35   # calves/steers/heifers/beef cows/bulls
W_DAIRY_EXTRA = 2.35    # dairy cows carry 2.7 total (0.35 + 2.35)
W_PIG = 0.18
W_HENS = 0.013
W_TURKEY = 0.05


def num(s):
    s = (s or "").strip().replace(",", "")
    if not s or s in ("..", "...", "x", "X", "F", "E", ":", "-"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def cd_value(path, catcol, want_cats, uom_filter=None):
    """Sum VALUE per CDUID across the wanted categories (optionally filtered to a UOM).
    `want_cats` may be a dict cat->weight (weighted sum) or a set (unit sum)."""
    weighted = isinstance(want_cats, dict)
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            cd = cduid_from_dguid(row["DGUID"])
            if cd is None:
                continue
            cat = row[catcol]
            if cat not in want_cats:
                continue
            if uom_filter is not None and row.get("Unit of measure") != uom_filter:
                continue
            w = want_cats[cat] if weighted else 1.0
            out[cd] = out.get(cd, 0.0) + num(row["VALUE"]) * w
    return out


def load_population():
    """CDUID -> 2021 population (Census 98-10-0002)."""
    out = {}
    with open(POP_CSV, encoding="utf-8-sig") as f:
        r = csv.reader(f)
        hdr = next(r)
        i_dg = hdr.index("DGUID")
        i_pop = [i for i, h in enumerate(hdr) if h.startswith(
            "Population and dwelling counts") and "Population, 2021" in h][0]
        for row in r:
            if len(row) <= max(i_dg, i_pop):
                continue
            cd = cduid_from_dguid(row[i_dg])
            if cd is None:
                continue
            out[cd] = num(row[i_pop])
    return out


def est(value, lo=0.6, hi=1.5, source="", notes=""):
    value = round(value, 5)
    return {"value": value, "low": round(value * lo, 5), "high": round(value * hi, 5),
            "source": source, "notes": notes}


def dominant(ag, forestry, manure, msw, biofrac):
    co2 = {"dry": (ag + forestry) * ODT_TO_CO2, "manure_wet": manure * ODT_TO_CO2,
           "msw": msw * biofrac}
    top = max(co2, key=co2.get)
    if co2[top] <= 0:
        return "mixed"
    if top == "dry":
        return "forestry_woody" if forestry > ag else "ag_dry"
    return top


def main():
    # --- CD-level raw signals ---
    ag_sig = cd_value(CROPS_CSV, "Field crops and hay", RESIDUE_CROPS, uom_filter="Hectares")
    cattle_total = cd_value(CATTLE_CSV, "Cattle", {"Total cattle": 1.0})
    cattle_dairy = cd_value(CATTLE_CSV, "Cattle", {"Cows, dairy": 1.0})
    pigs = cd_value(PIGS_CSV, "Pigs", {"Total pigs": 1.0})
    poultry = cd_value(POULTRY_CSV, "Poultry inventory",
                       {"Total hens and chickens": W_HENS, "Turkeys": W_TURKEY})
    pop = load_population()

    def manure_sig(cd):
        tot = cattle_total.get(cd, 0.0)
        dairy = cattle_dairy.get(cd, 0.0)
        cattle_vs = tot * W_CATTLE_OTHER + dairy * W_DAIRY_EXTRA
        return cattle_vs + pigs.get(cd, 0.0) * W_PIG + poultry.get(cd, 0.0)

    cds = {f["properties"]["cduid"]: f["properties"]
           for f in json.load(open(CD_GEO))["features"]}

    prov_recs = {r["name"]: r for r in json.load(open(PROV_FEED))}

    def sv(rec, key):
        v = rec.get(key)
        return (v or {}).get("value", 0.0) if isinstance(v, dict) else 0.0

    # group CDs by province (CDUID first 2 digits == PRUID)
    by_prov = {}
    for cduid in cds:
        by_prov.setdefault(cduid[:2], []).append(cduid)

    records = []
    for pruid, cd_list in by_prov.items():
        pname = PRUID_TO_NAME.get(pruid)
        prec = prov_recs.get(pname)
        if not prec:
            continue

        tot_ag = sv(prec, "ag_residues_odt_mt")
        tot_for = sv(prec, "forestry_residues_odt_mt")
        tot_man = sv(prec, "animal_manure_odt_mt")
        tot_msw = sv(prec, "msw_total_mt")
        tot_wwtp = sv(prec, "human_wwtp_odt_mt")
        biofrac = sv(prec, "msw_biogenic_frac") or 0.55
        nutrient = prec.get("nutrient_status", "moderate")

        # raw within-province shares
        sig_ag = {cd: ag_sig.get(cd, 0.0) for cd in cd_list}
        sig_man = {cd: manure_sig(cd) for cd in cd_list}
        sig_pop = {cd: pop.get(cd, 0.0) for cd in cd_list}
        sig_for = {cd: cds[cd]["area_km2"] for cd in cd_list}   # land-area proxy
        sum_ag = sum(sig_ag.values()) or 1.0
        sum_man = sum(sig_man.values()) or 1.0
        sum_pop = sum(sig_pop.values()) or 1.0
        sum_for = sum(sig_for.values()) or 1.0

        for cd in cd_list:
            p = cds[cd]
            ag = tot_ag * sig_ag[cd] / sum_ag
            forestry = tot_for * sig_for[cd] / sum_for
            manure = tot_man * sig_man[cd] / sum_man
            msw = tot_msw * sig_pop[cd] / sum_pop
            wwtp = tot_wwtp * sig_pop[cd] / sum_pop
            dom = dominant(ag, forestry, manure, msw, biofrac)

            records.append({
                "id": p["id"],
                "name": p["name"],
                "level": "census_division",
                "parent": "CAN",
                "prov": p["prov"],
                "cduid": cd,
                "area_km2": p["area_km2"],
                "centroid": p["centroid"],
                "ag_residues_odt_mt": est(
                    ag, source="StatCan Census of Ag 2021 CD field-crop area (32-10-0309) x "
                    "per-ha residue weight, scaled to province total",
                    notes="residue-producing field crops (cereals, oilseeds, pulses); hay/forage excluded"),
                "forestry_residues_odt_mt": est(
                    forestry, source="province forestry-residue total allocated by CD land area",
                    notes="land-area proxy — weakest layer (no CD-level timberland inventory)"),
                "msw_total_mt": est(
                    msw, source="province MSW total allocated by CD population (2021 Census)"),
                "msw_biogenic_frac": {"value": biofrac, "source": "province value (global tool)"},
                "animal_manure_odt_mt": est(
                    manure, source="StatCan Census of Ag 2021 CD cattle/pigs/poultry "
                    "(32-10-0370/0372/0374) x relative manure-VS weights, scaled to province total",
                    notes="dairy-weighted cattle + pigs + poultry"),
                "human_wwtp_odt_mt": est(
                    wwtp, source="province biosolids total allocated by CD population"),
                "nutrient_status": nutrient,
                "nutrient_status_source": "inherited from province (global tool)",
                "dominant_feedstock": dom,
                "feedstock_density": "diffuse",   # engine recomputes from area + haul radius
                "notes": "CD-level disaggregation; see METHODOLOGY.md sec Canada",
            })

    records.sort(key=lambda r: r["cduid"])
    with open(OUT, "w") as f:
        json.dump(records, f, ensure_ascii=False)

    from collections import Counter

    def tot(key):
        return sum(r[key]["value"] for r in records)
    dc = Counter(r["dominant_feedstock"] for r in records)
    print(f"wrote {len(records)} CD feedstock records -> {OUT}")
    print(f"  ag {tot('ag_residues_odt_mt'):.1f}  forestry {tot('forestry_residues_odt_mt'):.1f}"
          f"  manure {tot('animal_manure_odt_mt'):.1f}  msw {tot('msw_total_mt'):.1f}"
          f"  wwtp {tot('human_wwtp_odt_mt'):.2f}  (Mt)")
    print("  dominant feedstock:", dict(dc))


if __name__ == "__main__":
    main()
