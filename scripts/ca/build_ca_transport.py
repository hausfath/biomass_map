#!/usr/bin/env python3
"""
Canada census-division multimodal transport cost + routes (to_do item 4, extended to CA).

Cross-border by construction: the graph combines the **US + Canada** transfer nodes (rail terminals,
coastal ports, river corridors) AND the **US + Canada** storage wells (operating + permitted, tiered),
so a Canadian CD routes to whichever well — Canadian (Quest/ACTL/Aquistore/…) or US (e.g. North Dakota
Class VI, Michigan) — is cheapest, crossing the border wherever that lowers cost.

Output: data/processed/transport_ca.json (keyed by CD id). Mirrors transport_us.json schema.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/
from transport_common import TransportGraph, build_records, save_caches  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROC = os.path.join(ROOT, "data", "processed")
GEO = os.path.join(ROOT, "data", "geo")

CD_GEO = os.path.join(GEO, "ca_cd.json")
WELLS_CA = os.path.join(PROC, "wells_ca.json")
WELLS_US = os.path.join(PROC, "wells_us.json")
NODES_CA = os.path.join(GEO, "transport_nodes_ca.json")
NODES_US = os.path.join(GEO, "transport_nodes_us.json")
OUT = os.path.join(PROC, "transport_ca.json")
CAP = 100.0


def _load(path):
    try:
        return json.load(open(path))
    except FileNotFoundError:
        return None


def main():
    cds = json.load(open(CD_GEO))["features"]
    # combined cross-border wells (CA CCS projects + all US wells), operating + permitted
    wells = [w for w in (json.load(open(WELLS_CA)) + (_load(WELLS_US) or []))
             if w.get("lat") is not None]
    n_op = sum(1 for w in wells if w.get("status") == "operational")

    ca, us = json.load(open(NODES_CA)), json.load(open(NODES_US))
    terminals = ca["rail_terminals"] + us["rail_terminals"]
    coastal_ports = ca["coastal_ports"] + us["coastal_ports"]
    river_corridors = dict(us.get("river_corridors", {}))
    river_corridors.update(ca.get("river_corridors", {}))

    print(f"wells: {len(wells)} ({n_op} operating + {len(wells)-n_op} permitted; CA+US) | "
          f"rail terminals: {len(terminals)} (CA+US) | coastal ports: {len(coastal_ports)} | "
          f"river waypoints: {sum(len(v) for v in river_corridors.values())}")
    graph = TransportGraph(wells, terminals, coastal_ports, river_corridors)

    regions = [(f["properties"]["id"], [f["properties"]["centroid"][1], f["properties"]["centroid"][0]])
               for f in cds]
    out, stats = build_records(graph, regions, cap=CAP)
    save_caches()
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    cs = sorted(r["by_payload"]["slurry"] for r in out.values())
    med = cs[len(cs) // 2] if cs else None
    # how many CDs route to a US (cross-border) well?
    us_names = {w["name"] for w in (_load(WELLS_US) or [])}
    xborder = sum(1 for r in out.values() if r.get("dest_well") in us_names)
    print(f"wrote {len(out)} CD transport records -> {OUT}")
    print(f"  paths: {stats['paths']} | no path: {stats['no_path']} | permitted-rescued: {stats['rescued']}")
    print(f"  leg-mode usage: {stats['modes']}")
    print(f"  cross-border (route to a US well): {xborder}")
    print(f"  slurry $/tCO₂: min {cs[0]:.0f} / median {med:.0f} / max {cs[-1]:.0f}")
    for cid, label in [("CA-4806", "Calgary region (AB)"), ("CA-3520", "Toronto (ON)"),
                       ("CA-2466", "Montreal (QC)"), ("CA-4711", "SE Sask (SK)")]:
        r = out.get(cid)
        if r:
            print(f"  {label}: {'+'.join(r['modes'])} -> {r['dest_well']} ({r['dest_status']}) "
                  f"co2 ${r['by_payload']['co2']}, slurry ${r['by_payload']['slurry']} /tCO₂")


if __name__ == "__main__":
    main()
