#!/usr/bin/env python3
"""
Build data/processed/ad_maturity.json — a data-driven, continuous anaerobic-digestion
"maturity" index that replaces the engine's old hardcoded HIGH_AD_PENETRATION country set.

WHAT IT MEASURES
  ad_maturity(region) in [0,1] = the fraction of a region's organic/manure AD POTENTIAL that
  is already being realized as biogas/biomethane ("utilization"). High where a large existing
  AD industry already exists relative to the resource (→ AD+CCS retrofits it, leads over
  injection for wet manure); low where AD is sparse (→ Vaulted-style injection leads).
  This is the IEA "Outlook for Biogas and Biomethane" utilization framing (EU avg ~40% of
  potential used, US/China/India <5%, ~5% global).

  index = actual biogas production / sustainable biomethane potential        (energy ÷ energy)

COUNTRY SCORES (countries{}) are transcribed once from harmonized public sources — there is no
single open machine-readable production÷potential table, so this static table is the reproducible
artifact (sources cited per entry below). Numerator: FAOSTAT gaseous-biofuels production +
IEA Outlook current production (for biomethane-led EU markets). Denominator: IEA Outlook 2025
sustainable biomethane potential. Cross-checks: IRENA capacity, EBA Statistical Report.

SUB-NATIONAL SCORES (regions{}) are computed here from real facility data where it exists:
  - US states (US-<abbr>): EPA AgSTAR operating-digester biogas capacity ÷ state manure
    potential, scaled so the manure-weighted US mean equals the USA country score.
  - Canada provinces (CA-<abbr>): Canadian Biogas Association provincial facility shares ÷
    provincial manure share, × the national score.
  - EU NUTS-2 (EU-<nuts>): the country score refined by within-country AD-facility density
    (our curated AD clusters), clamped so weak/coarse facility data can never flip a region
    across the decision threshold (no open NUTS-2 production numerator exists).

The engine (scripts/engine_core.py) loads this file: ad_maturity_score(region) checks regions{}
(by id, then US-<state>/CA-<prov>), else countries{}, else AD_MATURITY_DEFAULT; manure_ad_preferred
is the threshold test score >= _meta.threshold.
"""
import json
import os
import sys

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/
from engine_core import haversine_km  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
AD_XLSX = os.path.join(ROOT, "data", "geo", "ad_raw", "agstar.xlsx")
OUT = os.path.join(PROC, "ad_maturity.json")

THRESHOLD = 0.15          # score at/above which AD+CCS leads over injection for wet manure
DEFAULT = 0.05            # nascent-AD economies with no compiled score

# --- Country AD-maturity scores: actual biogas production / sustainable biomethane potential.
#     Transcribed from IEA Outlook 2025 (potential + utilization framing), FAOSTAT Bioenergy
#     (production), IRENA (capacity cross-check), EBA Statistical Report (EU manure shares).
#     See docs/METHODOLOGY.md for the per-country basis. Data-driven — note this places ESP,
#     POL, IRL BELOW threshold (large potential, little realized AD) despite their being in the
#     old hardcoded "high-AD" set; that correction is intentional. ---
COUNTRIES = {
    "DEU": 0.85, "DNK": 0.70, "ITA": 0.45, "CZE": 0.40, "NLD": 0.35, "GBR": 0.35,
    "FRA": 0.30, "SWE": 0.30, "AUT": 0.30, "BEL": 0.30, "SVK": 0.30, "CHE": 0.25,
    "FIN": 0.20, "LUX": 0.20, "HUN": 0.15,
    "ESP": 0.10, "POL": 0.08, "IRL": 0.06,            # below threshold (data-corrected)
    "CAN": 0.14, "CHN": 0.07, "BRA": 0.05, "AUS": 0.05, "USA": 0.03, "IND": 0.04,
}

# Canadian Biogas Association — provincial shares of the existing biogas/RNG fleet (Market
# Summary 2023). The "rest" is distributed across remaining provinces by manure potential.
CA_FACILITY_SHARE = {"ON": 0.50, "QC": 0.16, "BC": 0.13, "AB": 0.07}
CA_REST_SHARE = 1.0 - sum(CA_FACILITY_SHARE.values())   # ~0.14 spread over the other provinces


def _v(rec, key):
    x = rec.get(key)
    return (x or {}).get("value", 0.0) if isinstance(x, dict) else 0.0


def _fnum(x):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


# -------------------------------------------------------------------- US states (AgSTAR)
def us_state_scores():
    counties = json.load(open(os.path.join(PROC, "feedstocks_us_county.json")))
    manure = {}
    for r in counties:
        manure[r["state"]] = manure.get(r["state"], 0.0) + _v(r, "animal_manure_odt_mt")

    cap = {}
    if os.path.exists(AD_XLSX):
        wb = openpyxl.load_workbook(AD_XLSX, read_only=True)
        ws = wb["Operational and Construction"]
        it = ws.iter_rows(values_only=True)
        hdr = list(next(it))
        i_state, i_bg = hdr.index("State"), hdr.index("Biogas Generation Estimate (cu-ft/day)")
        for row in it:
            if not row or row[i_state] is None:
                continue
            st = str(row[i_state]).strip()
            # AgSTAR rows with no biogas estimate still count as one operating digester (min cap)
            cap[st] = cap.get(st, 0.0) + (_fnum(row[i_bg]) or 1.0e5)
    else:
        print("  (AgSTAR file missing; US states inherit national score)")
        return {}

    nat = COUNTRIES["USA"]
    tot_cap = sum(cap.values())
    tot_man = sum(manure.get(s, 0.0) for s in cap)
    nat_density = (tot_cap / tot_man) if tot_man else 0.0
    out = {}
    for st, c in cap.items():
        m = manure.get(st, 0.0)
        if m <= 0 or nat_density <= 0:
            continue
        density = c / m
        score = nat * density / nat_density
        out["US-" + st] = round(min(max(score, 0.0), 1.0), 3)
    return out


# -------------------------------------------------------------- Canada provinces (CBA shares)
def ca_province_scores():
    cd = json.load(open(os.path.join(PROC, "feedstocks_ca_cd.json")))
    manure = {}
    for r in cd:
        manure[r["prov"]] = manure.get(r["prov"], 0.0) + _v(r, "animal_manure_odt_mt")
    tot_man = sum(manure.values()) or 1.0

    # distribute the "rest" facility share across non-listed provinces by manure potential
    rest_provs = {p: m for p, m in manure.items() if p not in CA_FACILITY_SHARE}
    rest_man = sum(rest_provs.values()) or 1.0
    fac_share = dict(CA_FACILITY_SHARE)
    for p, m in rest_provs.items():
        fac_share[p] = CA_REST_SHARE * m / rest_man

    nat = COUNTRIES["CAN"]
    out = {}
    for p, m in manure.items():
        man_share = m / tot_man
        if man_share <= 0:
            continue
        density = fac_share.get(p, 0.0) / man_share          # national density == 1 by construction
        out["CA-" + p] = round(min(max(nat * density, 0.0), 1.0), 3)
    return out


# ------------------------------------------------------------ EU NUTS-2 (facility-density refine)
def eu_nuts_scores():
    feeds = json.load(open(os.path.join(PROC, "feedstocks_eu_nuts.json")))
    # AD facility points (curated clusters + EU biogas_ad facilities)
    facs = []
    for fn in ("facilities_ad.json", "facilities_eu.json"):
        path = os.path.join(PROC, fn)
        if not os.path.exists(path):
            continue
        for f in json.load(open(path)):
            if f.get("type") == "biogas_ad" and f.get("lat") is not None:
                facs.append((f["lon"], f["lat"], _v(f, "est_biogenic_co2_mtpa") or 0.04))

    # assign each facility to the nearest NUTS-2 centroid
    cap = {}
    cents = [(r["id"], r["centroid"][0], r["centroid"][1]) for r in feeds if r.get("centroid")]
    for flon, flat, c in facs:
        best, bid = None, None
        for rid, clon, clat in cents:
            d = haversine_km(flon, flat, clon, clat)
            if best is None or d < best:
                best, bid = d, rid
        if bid:
            cap[bid] = cap.get(bid, 0.0) + c

    # per-country density stats
    by_country = {}
    for r in feeds:
        by_country.setdefault(r["parent"], []).append(r)

    out = {}
    for cc, regs in by_country.items():
        nat = COUNTRIES.get(cc, DEFAULT)
        # Only refine where the clamp [0.6,1.4] cannot cross the threshold — i.e. clearly-above
        # (>=0.30) or clearly-below (<0.10) countries. Borderline countries stay flat (the EU has
        # no open sub-national production numerator, so coarse facility data must not flip a call).
        refine = nat >= 0.30 or nat < 0.10
        dens = {}
        for r in regs:
            m = _v(r, "animal_manure_odt_mt")
            dens[r["id"]] = (cap.get(r["id"], 0.0) / m) if m > 0 else 0.0
        mean_d = (sum(dens.values()) / len(dens)) if dens else 0.0
        for r in regs:
            if refine and mean_d > 0:
                factor = max(0.6, min(1.4, dens[r["id"]] / mean_d))
            else:
                factor = 1.0
            out[r["id"]] = round(min(max(nat * factor, 0.0), 1.0), 3)
    return out


def main():
    regions = {}
    regions.update(us_state_scores())
    regions.update(ca_province_scores())
    regions.update(eu_nuts_scores())

    doc = {
        "_meta": {
            "threshold": THRESHOLD,
            "default": DEFAULT,
            "method": "ad_maturity = actual biogas production / sustainable biomethane potential "
                      "(IEA utilization framing). Country scores transcribed from IEA Outlook 2025 "
                      "+ FAOSTAT + IRENA + EBA; sub-national from AgSTAR (US), Canadian Biogas "
                      "Association (CA), and AD-facility density vs ENSPRESO manure potential (EU).",
            "version": "2026-06",
            "note": "Replaces the former HIGH_AD_PENETRATION binary. Score >= threshold => AD+CCS "
                    "leads over injection for wet manure (with storage + a digester within reach).",
        },
        "countries": COUNTRIES,
        "regions": regions,
    }
    with open(OUT, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)

    above = sorted([k for k, v in {**COUNTRIES}.items() if v >= THRESHOLD])
    n_reg_above = sum(1 for v in regions.values() if v >= THRESHOLD)
    print(f"wrote {OUT}")
    print(f"  countries: {len(COUNTRIES)} ({len(above)} >= {THRESHOLD}: {', '.join(above)})")
    print(f"  region overrides: {len(regions)} ({n_reg_above} >= threshold)")
    ca = {k: v for k, v in regions.items() if k.startswith("CA-")}
    print(f"  Canada provinces: {ca}")


if __name__ == "__main__":
    main()
