#!/usr/bin/env python3
"""
US county multimodal CO₂/biomass transport cost + least-cost route (to_do item 4, Phase A).

For each county centroid, find the least-cost truck+rail+ship path to the nearest OPERATING geologic
storage well (wells_us.json status=operational), and the carbon-density-weighted delivered cost in
$/tCO₂ for each payload class (co2 / bio_oil / slurry). Schematic v1: sparse graph over curated rail
terminals + ports (data/geo/transport_nodes_us.json); see scripts/transport_common.py.

Output: data/processed/transport_us.json  (keyed by county id)
  { "US-06037": {"per_tonne_usd": .., "dest_well": "..", "legs": [{mode,from,to,km,to_name}..],
                 "by_payload": {"co2": $/tCO2, "bio_oil": .., "slurry": ..},
                 "modes": ["truck","rail"], "total_km": ..} , ... }
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

COUNTIES = os.path.join(GEO, "us_counties.json")
WELLS = os.path.join(PROC, "wells_us.json")
WELLS_CA = os.path.join(PROC, "wells_ca.json")           # cross-border: Canadian CCS also stores US CO₂
NODES = os.path.join(GEO, "transport_nodes_us.json")
NODES_CA = os.path.join(GEO, "transport_nodes_ca.json")  # cross-border transfer nodes
FEED = os.path.join(PROC, "feedstocks_us_county.json")   # for dominant feedstock (slurry density)
OUT = os.path.join(PROC, "transport_us.json")


CAP = 100.0   # $/tCO₂ CO₂-delivered cap (matches engine TRANSPORT_MAX_USD)


def _load(path):
    try:
        return json.load(open(path))
    except FileNotFoundError:
        return None


def main():
    counties = json.load(open(COUNTIES))["features"]
    # Tier by status: operating wells are full-confidence storage; permitted (issued / under-
    # construction / draft / pending) wells "rescue" counties that have no affordable operating
    # well, but are flagged lower-confidence. Route to BOTH and choose per county below.
    # CROSS-BORDER (symmetric with the Canada build): CO₂ storage doesn't stop at the border, so a US
    # county is scored against the Canadian CCS wells too (Quest/ACTL/Aquistore/…) and can route to
    # one where it is cheaper — e.g. northern-tier states toward the Western Canada Sedimentary Basin.
    us_wells = [w for w in json.load(open(WELLS)) if w.get("lat") is not None]
    ca_wells = [w for w in (_load(WELLS_CA) or []) if w.get("lat") is not None]
    wells = us_wells + ca_wells
    n_op = sum(1 for w in wells if w.get("status") == "operational")
    nodes = json.load(open(NODES))
    ca_nodes = _load(NODES_CA) or {"rail_terminals": [], "coastal_ports": [], "river_corridors": {}}
    terminals = nodes["rail_terminals"] + ca_nodes.get("rail_terminals", [])
    coastal_ports = nodes["coastal_ports"] + ca_nodes.get("coastal_ports", [])
    river_corridors = dict(nodes["river_corridors"])
    river_corridors.update(ca_nodes.get("river_corridors", {}))
    nwp = sum(len(v) for v in river_corridors.values())
    print(f"wells: {len(wells)} ({n_op} operating + {len(wells)-n_op} permitted; US+CA) | "
          f"rail terminals: {len(terminals)} (US+CA) | coastal ports: {len(coastal_ports)} | "
          f"river waypoints: {nwp}")
    graph = TransportGraph(wells, terminals, coastal_ports, river_corridors)

    dom = {r["id"]: r.get("dominant_feedstock") for r in json.load(open(FEED))}
    regions = [(f["properties"]["id"], [f["properties"]["centroid"][1], f["properties"]["centroid"][0]],
                dom.get(f["properties"]["id"])) for f in counties]
    out, stats = build_records(graph, regions, cap=CAP)
    save_caches()
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    cs = sorted(r["by_payload"]["slurry"] for r in out.values())
    med = cs[len(cs) // 2] if cs else None
    ca_names = {w["name"] for w in ca_wells}
    xb_gen = sum(1 for r in out.values() if r.get("dest_well") in ca_names)
    xb_co2 = sum(1 for r in out.values() if r.get("co2_dest_well") in ca_names)
    print(f"wrote {len(out)} county transport records -> {OUT}")
    print(f"  paths found: {stats['paths']} | no path: {stats['no_path']} | "
          f"rescued by a permitted well: {stats['rescued']}")
    print(f"  leg-mode usage: {stats['modes']}")
    print(f"  cross-border to a Canadian well: general {xb_gen} | CO₂ {xb_co2}")
    print(f"  slurry $/tCO₂: min {cs[0]:.0f} / median {med:.0f} / max {cs[-1]:.0f}")
    # spot checks
    for cid, label in [("US-19153", "Polk Co, IA (corn belt)"),
                       ("US-06037", "Los Angeles, CA"),
                       ("US-48201", "Harris Co, TX (Houston/Gulf)"),
                       ("US-38101", "Ward Co, ND (border)"),
                       ("US-36061", "New York Co, NY")]:
        r = out.get(cid)
        if r:
            print(f"  {label}: {'+'.join(r['modes'])} -> {r['dest_well']} "
                  f"({r['total_km']} km) | co2 ${r['by_payload']['co2']}, "
                  f"bio_oil ${r['by_payload']['bio_oil']}, slurry ${r['by_payload']['slurry']} /tCO₂")


if __name__ == "__main__":
    main()
