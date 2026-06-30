#!/usr/bin/env python3
"""
County-level feedstock supply for the US BiCRS map (~3,140 counties).

Method — "Billion-Ton state totals, spatially disaggregated to counties":
  Each feedstock's *spatial distribution* within a state comes from authoritative county
  data; each county is then scaled so the counties of a state sum to that state's total
  already in the global tool (data/processed/feedstocks.json, US-<State> records, which are
  anchored to the DOE 2023 Billion-Ton Report + USDA NASS). This gives real county geography
  AND exact consistency with the national/state numbers. Because we scale to state totals,
  the per-county factors only need to be RELATIVELY correct within a state.

County distribution signals (USDA Census of Agriculture 2022, county FIPS):
  ag residues  <- crop production x residue-to-product ratio x ~30% recoverable fraction
  manure       <- livestock inventory x relative manure (volatile-solids) weights
  forestry     <- county woodland acreage (AG LAND, WOODLAND) — proxy within state
  MSW & WWTP   <- county population (Census Vintage-2023 estimates)

Inputs (all under data/geo/us_raw/ unless noted):
  qs.census2022.txt.gz                 USDA Census of Agriculture 2022 (QuickStats bulk)
  co-est2023.csv                       Census county population estimates
  data/geo/us_counties.json            county centroids / area / names (build_county_geo.py)
  data/processed/feedstocks.json       global tool — US state totals + nutrient_status (anchors)

Output: data/processed/feedstocks_us_county.json
"""
import csv
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/
from engine_core import ODT_TO_CO2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(ROOT, "data", "geo", "us_raw")
PROC = os.path.join(ROOT, "data", "processed")

CENSUS = os.path.join(RAW, "qs.census2022.txt.gz")
POP = os.path.join(RAW, "co-est2023.csv")
COUNTIES = os.path.join(ROOT, "data", "geo", "us_counties.json")
STATE_FEED = os.path.join(PROC, "feedstocks.json")
FIA = os.path.join(PROC, "fia_county_forestry.json")   # FIA county forestry weights (item 2 ph.1)
FUELS = os.path.join(PROC, "fuels_residues_us.json")   # FACTS wildfire-fuels residue (item 2 ph.3)
OUT = os.path.join(PROC, "feedstocks_us_county.json")

# --- residue-to-product factors: odt recoverable residue per production unit ---
# (Only relative weighting within a state matters; values scaled to state totals.)
CROPS = {
    "CORN, GRAIN - PRODUCTION, MEASURED IN BU": 0.00859,
    "WHEAT - PRODUCTION, MEASURED IN BU": 0.01224,
    "SOYBEANS - PRODUCTION, MEASURED IN BU": 0.00710,
    "SORGHUM, GRAIN - PRODUCTION, MEASURED IN BU": 0.00859,
    "BARLEY - PRODUCTION, MEASURED IN BU": 0.00883,
    "OATS - PRODUCTION, MEASURED IN BU": 0.00637,
    "RICE - PRODUCTION, MEASURED IN CWT": 0.02210,
    "COTTON - PRODUCTION, MEASURED IN BALES": 0.16,
    "SUGARCANE, SUGAR & SEED - PRODUCTION, MEASURED IN TONS": 0.12,
}

# --- livestock relative manure (collectable volatile-solids) weights, odt/head/yr ---
MILK = "CATTLE, COWS, MILK - INVENTORY"
ALLCATTLE = "CATTLE, INCL CALVES - INVENTORY"
LIVESTOCK = {
    "HOGS - INVENTORY": 0.18,
    "CHICKENS, LAYERS - INVENTORY": 0.011,
    "CHICKENS, BROILERS - INVENTORY": 0.03,
    "TURKEYS - INVENTORY": 0.05,
}
MILK_W, OTHER_CATTLE_W = 2.7, 0.35
WOODLAND = "AG LAND, WOODLAND - ACRES"

ALL_DESCS = set(CROPS) | set(LIVESTOCK) | {MILK, ALLCATTLE, WOODLAND}


def parse_value(s):
    s = (s or "").strip().replace(",", "")
    if not s or s.startswith("(") or s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_census():
    """One streaming pass -> per-FIPS dict of {short_desc: value} for our target series."""
    data = {}
    with gzip.open(CENSUS, "rt", encoding="latin-1") as f:
        header = f.readline().rstrip("\n").split("\t")
        ix = {name: i for i, name in enumerate(header)}
        i_agg, i_dom = ix["AGG_LEVEL_DESC"], ix["DOMAIN_DESC"]
        i_sd, i_val = ix["SHORT_DESC"], ix["VALUE"]
        i_sf, i_cc = ix["STATE_FIPS_CODE"], ix["COUNTY_CODE"]
        for line in f:
            row = line.rstrip("\n").split("\t")
            if len(row) <= i_val:
                continue
            if row[i_agg] != "COUNTY" or row[i_dom] != "TOTAL":
                continue
            sd = row[i_sd]
            if sd not in ALL_DESCS:
                continue
            v = parse_value(row[i_val])
            if v is None:
                continue
            cc = row[i_cc]
            if not cc or cc in ("998", "999", "888"):  # NASS non-county aggregates
                continue
            fips = row[i_sf] + cc
            data.setdefault(fips, {})[sd] = v
    return data


def load_population():
    pop = {}
    with open(POP, encoding="latin-1") as f:
        for r in csv.DictReader(f):
            if r["COUNTY"] == "000":      # state row
                continue
            fips = r["STATE"].zfill(2) + r["COUNTY"].zfill(3)
            try:
                pop[fips] = float(r["POPESTIMATE2023"])
            except (ValueError, KeyError):
                pop[fips] = 0.0
    return pop


def raw_ag(rec):
    return sum(rec.get(sd, 0.0) * f for sd, f in CROPS.items())


def raw_manure(rec):
    milk = rec.get(MILK, 0.0)
    allc = rec.get(ALLCATTLE, 0.0)
    other = max(allc - milk, 0.0)
    m = milk * MILK_W + other * OTHER_CATTLE_W
    m += sum(rec.get(sd, 0.0) * w for sd, w in LIVESTOCK.items())
    return m


def est(value, lo=0.6, hi=1.5, source="", notes=""):
    value = round(value, 4)
    return {"value": value, "low": round(value * lo, 4), "high": round(value * hi, 4),
            "source": source, "notes": notes}


def dominant(ag, forestry, manure, msw, biofrac):
    """Argmax of CO2-weighted feedstock streams -> dominant_feedstock key."""
    co2 = {
        "dry": (ag + forestry) * ODT_TO_CO2,
        "manure_wet": manure * ODT_TO_CO2,
        "msw": msw * biofrac,
    }
    top = max(co2, key=co2.get)
    if co2[top] <= 0:
        return "mixed"
    if top == "dry":
        return "forestry_woody" if forestry > ag else "ag_dry"
    return top


def main():
    census = load_census()
    pop = load_population()

    # FIA county forestry weights (item 2, phase 1): a within-state blend of harvest removals
    # (residue-generation proxy) + standing biomass, replacing the woodland-acreage proxy where
    # available. Falls back to woodland acreage for any county/state the FIA build didn't cover.
    fia = {}
    if os.path.exists(FIA):
        fia = json.load(open(FIA))
    n_fia = sum(1 for v in fia.values() if (v.get("weight") or 0) > 0)
    print(f"  FIA forestry weights: {n_fia} counties with positive weight"
          if fia else "  (no FIA weights — using woodland-acreage proxy for forestry)")

    # Wildfire-fuels-treatment residue (item 2, phase 3): a separate, largely-additional forestry
    # sub-stream (Mt odt/yr per county) from USFS FACTS. Added ON TOP of the BT23-anchored commercial
    # forestry (it is mostly federal-land treatment not in the commercial logging total), and folded
    # into the forestry stream so it drives dominant_feedstock + CDR — but kept tagged for provenance.
    fuels = json.load(open(FUELS)) if os.path.exists(FUELS) else {}
    print(f"  fuels-treatment residue: {len(fuels)} counties, {sum(fuels.values()):.1f} Mt odt/yr"
          if fuels else "  (no fuels-treatment residue layer)")

    counties = {f["properties"]["fips"]: f["properties"]
                for f in json.load(open(COUNTIES))["features"]}

    state_recs = {r["name"].upper(): r for r in json.load(open(STATE_FEED))
                  if r.get("parent") == "USA" and r.get("level") == "subnational"}

    # Census STATE_NAME is uppercase; map state FIPS -> uppercase name via population file.
    sf_to_name = {}
    with open(POP, encoding="latin-1") as f:
        for r in csv.DictReader(f):
            sf_to_name[r["STATE"].zfill(2)] = r["STNAME"].upper()

    def sv(rec, key):
        v = rec.get(key)
        return (v or {}).get("value", 0.0) if isinstance(v, dict) else 0.0

    # States with FIA coverage (>=1 county with a positive FIA weight). Forestry is allocated by
    # FIA weight for ALL counties in such a state (a county absent from FIA -> 0, i.e. no forest);
    # states without FIA coverage fall back to the woodland-acreage proxy for all their counties.
    # (Never mix the two within one state — the scales differ.)
    fia_states = set()
    for fp, v in fia.items():
        if (v.get("weight") or 0) > 0:
            fia_states.add(fp[:2])

    # --- 1. raw per-county signals ---
    raw = {}
    for fips, props in counties.items():
        c = census.get(fips, {})
        if fips[:2] in fia_states:
            forestry_sig = (fia.get(fips, {}).get("weight") or 0.0)
            forestry_src = "fia"
        else:
            forestry_sig = c.get(WOODLAND, 0.0)
            forestry_src = "woodland"
        raw[fips] = {
            "ag": raw_ag(c),
            "forestry": forestry_sig,
            "forestry_src": forestry_src,
            "manure": raw_manure(c),
            "pop": pop.get(fips, 0.0),
            "state_fips": fips[:2],
        }

    # --- 2. scale within each state to the state total in the global tool ---
    states = {}
    for fips, r in raw.items():
        states.setdefault(r["state_fips"], []).append(fips)

    records = []
    NAT_MSW_PER_CAP = 0.66      # t biogenic-relevant MSW per person-yr fallback (DC etc.)
    NAT_WWTP_PER_CAP = 6.5e-3 * 365 / 1e3  # ~2.4 kg DS/person-yr -> t (matches state calc)

    for sfips, fips_list in states.items():
        sname = sf_to_name.get(sfips, "")
        srec = state_recs.get(sname)
        # raw sums for share computation
        sum_ag = sum(raw[f]["ag"] for f in fips_list) or 1.0
        sum_for = sum(raw[f]["forestry"] for f in fips_list) or 1.0
        sum_man = sum(raw[f]["manure"] for f in fips_list) or 1.0
        sum_pop = sum(raw[f]["pop"] for f in fips_list) or 1.0

        if srec:
            tot_ag = sv(srec, "ag_residues_odt_mt")
            tot_for = sv(srec, "forestry_residues_odt_mt")
            tot_man = sv(srec, "animal_manure_odt_mt")
            tot_msw = sv(srec, "msw_total_mt")
            tot_wwtp = sv(srec, "human_wwtp_odt_mt")
            biofrac = sv(srec, "msw_biogenic_frac") or 0.61
            nutrient = srec.get("nutrient_status", "moderate")
        else:  # e.g. DC — no state record; population-driven wastes only
            tot_ag = tot_for = tot_man = 0.0
            tot_msw = sum_pop * NAT_MSW_PER_CAP / 1e6
            tot_wwtp = sum_pop * NAT_WWTP_PER_CAP / 1e6
            biofrac, nutrient = 0.61, "moderate"

        for fips in fips_list:
            props = counties[fips]
            r = raw[fips]
            ag = tot_ag * r["ag"] / sum_ag
            forestry_comm = tot_for * r["forestry"] / sum_for   # BT23-anchored commercial residue
            fuels_res = fuels.get(fips, 0.0)                    # FACTS fuels-treatment residue (add'l)
            forestry = forestry_comm + fuels_res               # total forestry the engine sees
            manure = tot_man * r["manure"] / sum_man
            msw = tot_msw * r["pop"] / sum_pop
            wwtp = tot_wwtp * r["pop"] / sum_pop
            dom = dominant(ag, forestry, manure, msw, biofrac)

            records.append({
                "id": props["id"],
                "name": props["name"],
                "level": "county",
                "parent": "USA",
                "state": props["state"],
                "fips": fips,
                "area_km2": props["area_km2"],
                "centroid": props["centroid"],
                "ag_residues_odt_mt": est(
                    ag, source="USDA Census of Ag 2022 county crop production x RPR x "
                    "~30% recoverable fraction, scaled to BT23 state total",
                    notes="cereal straw + corn stover + sorghum/cotton/rice/sugarcane residues"),
                "forestry_residues_odt_mt": est(
                    forestry,
                    source=(("BT23 state forestry residue allocated by county FIA forest data "
                             "(USFS FIA: 0.7 harvest-removals + 0.3 standing-biomass share)"
                             if r["forestry_src"] == "fia" else
                             "BT23 state forestry residue allocated by county woodland acreage "
                             "(USDA Census of Ag 2022)")
                            + (" + USFS FACTS wildfire-fuels-treatment residue"
                               if fuels_res > 0 else "")),
                    notes=("commercial residue " + (
                        "(FIA-allocated)" if r["forestry_src"] == "fia" else "(woodland-area proxy)")
                        + (f" plus {fuels_res:.3f} Mt/yr fuels-treatment residue "
                           f"(thinning/pile/chipping, largely additional)" if fuels_res > 0 else ""))),
                "forestry_residues_fuels_odt_mt": est(
                    fuels_res, source="USFS FACTS hazardous-fuel-treatment removable biomass "
                    "(acres x per-type odt/acre, annualized FY2018-2024)",
                    notes="wildfire-management residue today pile-burned/left; included in the "
                          "forestry total above") if fuels_res > 0 else {"value": 0.0},
                "msw_total_mt": est(
                    msw, source="state MSW total allocated by county population "
                    "(Census Vintage-2023)"),
                "msw_biogenic_frac": {"value": biofrac, "source": "US national avg ~0.61"},
                "animal_manure_odt_mt": est(
                    manure, source="USDA Census of Ag 2022 county livestock inventory x "
                    "relative manure VS weights, scaled to state total",
                    notes="dairy + other cattle + hogs + poultry + turkeys"),
                "human_wwtp_odt_mt": est(
                    wwtp, source="state biosolids total allocated by county population"),
                "nutrient_status": nutrient,
                "nutrient_status_source": "inherited from state (global tool)",
                "dominant_feedstock": dom,
                "feedstock_density": "diffuse",  # engine recomputes from area + haul radius
                "notes": "county-level disaggregation; see METHODOLOGY.md sec US",
            })

    records.sort(key=lambda r: r["fips"])
    with open(OUT, "w") as f:
        json.dump(records, f, ensure_ascii=False)

    # --- summary / sanity ---
    def tot(key):
        return sum(r[key]["value"] for r in records)
    from collections import Counter
    dc = Counter(r["dominant_feedstock"] for r in records)
    print(f"wrote {len(records)} county feedstock records -> {OUT}")
    print(f"  ag {tot('ag_residues_odt_mt'):.1f}  forestry {tot('forestry_residues_odt_mt'):.1f}"
          f"  manure {tot('animal_manure_odt_mt'):.1f}  msw {tot('msw_total_mt'):.1f}"
          f"  wwtp {tot('human_wwtp_odt_mt'):.2f}  (Mt)")
    print("  dominant feedstock:", dict(dc))


if __name__ == "__main__":
    main()
