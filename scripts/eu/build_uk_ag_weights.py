#!/usr/bin/env python3
"""
UK-specific feedstock DISTRIBUTION WEIGHTS from the UK June Agricultural Census
(Eurostat Farm Structure Survey 2016, the last integrated UK wave), replacing the
population/per-capita proxy that put phantom manure in London (item 11).

Two weights per UK ITL-2 (NUTS-2 2021) region, later normalised to the country total in
build_nuts_feedstocks.py so the UK totals stay anchored:
  manure_w  = housed-livestock units = bovine + swine + poultry LSU  (ef_lsk_main, unit=LSU).
              Sheep/goats/horses are excluded — grazing manure is deposited on pasture and is
              not practically recoverable for AD/biogas (matches ENSPRESO's biogas basis).
  ag_w      = arable land, ha  (ef_lus_main, crops=ARA) — the driver for crop-residue (straw).

NUTS vintage: the FSS is NUTS 2013; the map geometry is NUTS 2021. We crosswalk by REGION NAME
(robust to the code renumbering), with three explicit exceptions:
  - UKI3 Inner London — West: absent in the FSS -> 0 (inner-London, negligible farming).
  - UKM8 West Central Scotland + UKM9 Southern Scotland: the 2021 split of FSS UKM3 "South
    Western Scotland". Split by documented fixed fractions (Glasgow conurbation vs the
    Ayrshire/Dumfries & Galloway dairy belt) — the only approximation, bounded to two regions.
  - UKN0 Northern Ireland: FSS label carries a "(UK)" suffix; matched explicitly.

Output: data/geo/uk_feedstock_weights.json  (committed; consumed by build_nuts_feedstocks.py).
Raw Eurostat responses are cached under data/geo/eu_raw/ (gitignored, re-fetched if missing).
"""
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(ROOT, "data", "geo", "eu_raw")
NUTS = os.path.join(ROOT, "data", "geo", "eu_nuts.json")
OUT = os.path.join(ROOT, "data", "geo", "uk_feedstock_weights.json")

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
LSK_Q = ("ef_lsk_main?format=JSON&lang=EN&freq=A&statinfo=TOTAL&farmtype=TOTAL&so_eur=TOTAL"
         "&uaarea=TOTAL&lsu=TOTAL&unit=LSU&time=2016"
         "&animals=A2000&animals=A3100&animals=A5000&animals=A4100")
ARA_Q = ("ef_lus_main?format=JSON&lang=EN&freq=A&statinfo=TOTAL&crops=ARA&farmtype=TOTAL"
         "&so_eur=TOTAL&uaarea=TOTAL&unit=HA&time=2016")

# UKM3 "South Western Scotland" (2013) -> 2021 West Central (UKM8) + Southern (UKM9).
# Southern (Ayrshire + Dumfries & Galloway) is Scotland's dairy/beef belt; West Central is the
# Glasgow conurbation (Lanarkshire retains some livestock/arable). Documented approximation.
UKM3_SPLIT = {"UKM8": {"manure": 0.18, "ag": 0.30},
              "UKM9": {"manure": 0.82, "ag": 0.70}}


def fetch(query, cache_name):
    path = os.path.join(RAW, cache_name)
    if os.path.exists(path):
        return json.load(open(path))
    os.makedirs(RAW, exist_ok=True)
    print(f"  fetching {cache_name} from Eurostat …")
    with urllib.request.urlopen(f"{API}/{query}", timeout=90) as r:
        data = json.loads(r.read().decode())
    if "error" in data:
        sys.exit("Eurostat error for %s: %s" % (cache_name, data["error"]))
    json.dump(data, open(path, "w"))
    return data


def jsonstat_values(d, want_geo):
    """Return {geo_code: {other_dim_code: value}} for a JSON-stat cube, isolating one dimension
    (`want_geo` = 'geo') and the single remaining varying dimension (animals, or none)."""
    sz, order = d["size"], d["id"]
    geo = d["dimension"]["geo"]["category"]["index"]
    val = d["value"]
    gpos = order.index("geo")
    # the other varying dim (size>1, not geo), if any (animals for lsk; none for ara)
    var = [(i, order[i]) for i in range(len(sz)) if sz[i] > 1 and order[i] != "geo"]
    vpos, vname = (var[0] if var else (None, None))
    vcat = d["dimension"][vname]["category"]["index"] if vname else {"_": 0}

    def flat(idx):
        f = 0
        for i, s in enumerate(sz):
            f = f * s + idx[i]
        return f

    out = {}
    for gcode, gp in geo.items():
        if not (gcode.startswith("UK") and len(gcode) == 4):
            continue
        row = {}
        for vcode, vp in vcat.items():
            idx = [0] * len(sz)
            idx[gpos] = gp
            if vpos is not None:
                idx[vpos] = vp
            row[vcode] = val.get(str(flat(idx)))
        out[gcode] = row
    return out


def norm(s):
    s = re.sub(r"\s*\(nuts.*?\)", "", s.lower())
    s = s.replace("(uk)", "")
    s = s.replace("—", "-").replace("–", "-")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def main():
    lsk = jsonstat_values(fetch(LSK_Q, "fss_lsk_2016.json"), "geo")
    ara = jsonstat_values(fetch(ARA_Q, "fss_ara_2016.json"), "geo")

    # 2013-code weights
    man13, ag13 = {}, {}
    for c, row in lsk.items():
        man13[c] = (row.get("A2000") or 0) + (row.get("A3100") or 0) + (row.get("A5000") or 0)
    for c, row in ara.items():
        ag13[c] = row.get("_") or 0

    # FSS label -> 2013 code (skip retired duplicate codes by preferring the one that also carries
    # data; name collisions e.g. Cheshire UKD2/UKD6 both exist — keep whichever the geometry name
    # resolves to below, both hold the same value so it doesn't matter).
    lab = json.load(open(os.path.join(RAW, "fss_lsk_2016.json")))["dimension"]["geo"]["category"]["label"]
    fss_by_name = {}
    for c, l in lab.items():
        if c.startswith("UK") and len(c) == 4:
            fss_by_name.setdefault(norm(l), c)

    regions = [f["properties"] for f in json.load(open(NUTS))["features"] if f["properties"]["cntr"] == "UK"]
    weights, missing = {}, []
    for p in regions:
        code, name = p["nuts_id"], p["name"]
        key = norm(name)
        if code == "UKI3":                       # Inner London — West: no farming
            weights[code] = {"manure_w": 0.0, "ag_w": 0.0, "src": "n/a (inner London)"}
            continue
        if code in UKM3_SPLIT:                    # West Central / Southern Scotland from FSS UKM3
            f = UKM3_SPLIT[code]
            weights[code] = {"manure_w": round(man13.get("UKM3", 0) * f["manure"], 1),
                             "ag_w": round(ag13.get("UKM3", 0) * f["ag"], 1),
                             "src": "FSS2016 UKM3 (South Western Scotland) split %.0f%%/%.0f%% man/ag"
                                    % (f["manure"] * 100, f["ag"] * 100)}
            continue
        src = fss_by_name.get(key)
        if not src:
            missing.append((code, name))
            continue
        weights[code] = {"manure_w": round(man13.get(src, 0), 1),
                         "ag_w": round(ag13.get(src, 0), 1),
                         "src": "FSS2016 %s" % src}

    if missing:
        sys.exit("Unmatched 2021 UK regions (fix crosswalk): %s" % missing)

    meta = {"_meta": "UK ITL-2 (NUTS-2 2021) feedstock distribution weights from Eurostat Farm "
                     "Structure Survey 2016 (UK June Census). manure_w = bovine+swine+poultry LSU "
                     "(ef_lsk_main); ag_w = arable land ha (ef_lus_main). Crosswalk 2013->2021 by "
                     "region name; UKM3 split to UKM8/UKM9 by documented fractions. Weights are "
                     "relative — build_nuts_feedstocks.py normalises them to the UK country totals."}
    json.dump({**meta, **weights}, open(OUT, "w"), indent=0)
    tot_m = sum(w["manure_w"] for w in weights.values())
    tot_a = sum(w["ag_w"] for w in weights.values())
    print(f"wrote {len(weights)} UK region weights -> {OUT}")
    print("  London manure share: %.2f%% | top manure: %s" % (
        100 * sum(weights[c]["manure_w"] for c in weights if c.startswith("UKI")) / tot_m,
        ", ".join(c for c, _ in sorted(weights.items(), key=lambda kv: -kv[1]["manure_w"])[:4])))
    print("  top arable: %s" % ", ".join(
        c for c, _ in sorted(weights.items(), key=lambda kv: -kv[1]["ag_w"])[:4]))


if __name__ == "__main__":
    main()
