#!/usr/bin/env python3
"""
Roads to Removal thinning SCENARIO for the US map (the "R2R scenario" toggle).

Default view = today's supply. The scenario sets each county's wildfire-fuels component to
max(today's completed-treatment stream, R2R potential in accessibility classes costing <=
R2R_MAX_COST_USD per short BDT) — the max, not the sum, because R2R's priority-area thinning would
subsume today's treatments — then reruns US transport (slurry density depends on the dominant
feedstock) and recommendations with the unchanged engine.

Full scenario outputs (~28 MB) go to data/processed/_scenarios/ (gitignored). Only the overlay is
committed: src/data_bundle_us_r2r.js -> window.US_R2R = {meta, recs (slim, records that differ from
today), feeds (changed feedstock fields), transport (changed transport records)}, lazy-loaded when
the toggle is switched on. Canada has no R2R data and is unchanged.

Run after the base US pipeline (build_all.sh step 10): python3 build_r2r_scenario.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from bundle_us import slim_recs  # noqa: E402
from build_fuels_r2r import CLASSES  # noqa: E402
from engine_core import ODT_TO_CO2  # noqa: E402

PROC = os.path.join(ROOT, "data", "processed")
SCEN = os.path.join(PROC, "_scenarios")
OUT_JS = os.path.join(ROOT, "src", "data_bundle_us_r2r.js")
R2R_MAX_COST_USD = 100.0          # scenario "B": classes <= $100/short BDT (4 of 6 classes)


def v(r, k):
    x = r.get(k)
    return (x or {}).get("value", 0.0) if isinstance(x, dict) else 0.0


def dominant(ag, forestry, manure, msw, biofrac):
    """Same rule as build_county_feedstocks.dominant."""
    co2 = {"dry": (ag + forestry) * ODT_TO_CO2, "manure_wet": manure * ODT_TO_CO2,
           "msw": msw * biofrac}
    top = max(co2, key=co2.get)
    if co2[top] <= 0:
        return "mixed"
    if top == "dry":
        return "forestry_woody" if forestry > ag else "ag_dry"
    return top


def main():
    os.makedirs(SCEN, exist_ok=True)
    feeds = json.load(open(os.path.join(PROC, "feedstocks_us_county.json")))
    r2r = json.load(open(os.path.join(PROC, "fuels_r2r_us.json")))
    keep = [i for i, c in enumerate(CLASSES) if c[3] <= R2R_MAX_COST_USD]
    added, n = 0.0, 0
    for r in feeds:
        fips = r["id"][3:]
        if fips not in r2r:
            continue
        pot = sum(r2r[fips]["classes"][i] for i in keep)
        fuels = v(r, "forestry_residues_fuels_odt_mt")
        delta = max(fuels, pot) - fuels
        if delta <= 0:
            continue
        added += delta
        n += 1
        r["forestry_residues_odt_mt"] = dict(r["forestry_residues_odt_mt"],
                                             value=round(v(r, "forestry_residues_odt_mt") + delta, 4))
        r["forestry_residues_fuels_odt_mt"] = dict(r.get("forestry_residues_fuels_odt_mt") or {},
                                                   value=round(fuels + delta, 4))
        r["dominant_feedstock"] = dominant(
            v(r, "ag_residues_odt_mt"), r["forestry_residues_odt_mt"]["value"],
            v(r, "animal_manure_odt_mt"), v(r, "msw_total_mt"),
            (r.get("msw_biogenic_frac") or {}).get("value", 0.61))
    feed_s = os.path.join(SCEN, "feedstocks_us_county_r2r.json")
    tr_s = os.path.join(SCEN, "transport_us_r2r.json")
    rec_s = os.path.join(SCEN, "recommendations_us_r2r.json")
    json.dump(feeds, open(feed_s, "w"))
    print(f"R2R scenario (classes <= ${R2R_MAX_COST_USD:.0f}/short BDT): +{added:.1f} Mt dry/yr "
          f"forestry in {n} counties")

    env = dict(os.environ, BICRS_US_FEED=feed_s, BICRS_US_TRANSPORT=tr_s, BICRS_US_RECS_OUT=rec_s)
    for script in ("build_us_transport.py", "build_us_recommendations.py"):
        subprocess.run([sys.executable, script], cwd=HERE, env=env, check=True,
                       stdout=subprocess.DEVNULL)

    # overlay: only what differs from today
    base_recs = {r["id"]: r for r in json.load(open(os.path.join(PROC, "recommendations_us.json")))}
    scen_recs = json.load(open(rec_s))
    diff_recs = [r for r in scen_recs if json.dumps(r, sort_keys=True)
                 != json.dumps(base_recs.get(r["id"]), sort_keys=True)]
    base_feed = {r["id"]: r for r in json.load(open(os.path.join(PROC, "feedstocks_us_county.json")))}
    feed_over = {}
    for r in feeds:
        b = base_feed[r["id"]]
        if (v(r, "forestry_residues_odt_mt") != v(b, "forestry_residues_odt_mt")
                or r["dominant_feedstock"] != b["dominant_feedstock"]):
            feed_over[r["id"]] = {"forestry": round(v(r, "forestry_residues_odt_mt"), 4),
                                  "forestry_fuels": round(v(r, "forestry_residues_fuels_odt_mt"), 4),
                                  "dominant_feedstock": r["dominant_feedstock"]}
    base_tr = json.load(open(os.path.join(PROC, "transport_us.json")))
    scen_tr = json.load(open(tr_s))
    tr_over = {k: t for k, t in scen_tr.items()
               if json.dumps(t, sort_keys=True) != json.dumps(base_tr.get(k), sort_keys=True)}
    changed = sum(1 for r in scen_recs if r["recommended"] != base_recs[r["id"]]["recommended"])
    base_cdr = sum(r.get("cdr_potential_mtpa") or 0 for r in base_recs.values())
    scen_cdr = sum(r.get("cdr_potential_mtpa") or 0 for r in scen_recs)
    meta = {"label": f"Roads to Removal thinning (≤${R2R_MAX_COST_USD:.0f}/short BDT)",
            "max_cost_usd_bdt": R2R_MAX_COST_USD, "added_mt_dry": round(added, 1),
            "counties_with_added_supply": n, "recommendation_changes": changed,
            "us_cdr_today": round(base_cdr, 1), "us_cdr_scenario": round(scen_cdr, 1)}
    with open(OUT_JS, "w") as f:
        f.write("// US Roads to Removal scenario overlay — generated by scripts/us/build_r2r_scenario.py\n")
        f.write("window.US_R2R = " + json.dumps({"meta": meta, "recs": slim_recs(diff_recs),
                                                 "feeds": feed_over, "transport": tr_over},
                                                separators=(",", ":")) + ";\n")
    print(f"  {len(diff_recs)} differing records, {len(feed_over)} feed overrides, "
          f"{len(tr_over)} transport overrides | {changed} recommendation changes | "
          f"US CDR {base_cdr:.1f} -> {scen_cdr:.1f} Mt CO2/yr")
    print(f"wrote {OUT_JS} ({os.path.getsize(OUT_JS):,} bytes)")


if __name__ == "__main__":
    main()
