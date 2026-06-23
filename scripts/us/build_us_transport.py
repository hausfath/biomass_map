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
from transport_common import TransportGraph, payload_costs  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROC = os.path.join(ROOT, "data", "processed")
GEO = os.path.join(ROOT, "data", "geo")

COUNTIES = os.path.join(GEO, "us_counties.json")
WELLS = os.path.join(PROC, "wells_us.json")
NODES = os.path.join(GEO, "transport_nodes_us.json")
OUT = os.path.join(PROC, "transport_us.json")


def main():
    counties = json.load(open(COUNTIES))["features"]
    wells = [w for w in json.load(open(WELLS))
             if w.get("status") == "operational" and w.get("lat") is not None]
    nodes = json.load(open(NODES))
    terminals, ports = nodes["rail_terminals"], nodes["ports"]

    print(f"operating wells: {len(wells)} | rail terminals: {len(terminals)} | ports: {len(ports)}")
    graph = TransportGraph(wells, terminals, ports)

    out = {}
    n_path = n_nopath = 0
    from collections import Counter
    mode_use = Counter()
    cost_samples = []
    for f in counties:
        p = f["properties"]
        lon, lat = p["centroid"]
        per_tonne, legs, dest = graph.least_cost_to_well([lat, lon])
        if per_tonne is None:
            n_nopath += 1
            continue
        n_path += 1
        modes = sorted({leg["mode"] for leg in legs})
        for m in modes:
            mode_use[m] += 1
        total_km = sum(leg["km"] for leg in legs)
        bp = payload_costs(per_tonne, has_path=bool(legs))
        cost_samples.append(bp["slurry"])
        out[p["id"]] = {
            "per_tonne_usd": per_tonne,
            "dest_well": dest,
            "legs": legs,
            "by_payload": bp,
            "modes": modes,
            "total_km": total_km,
        }

    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    cost_samples.sort()
    med = cost_samples[len(cost_samples) // 2] if cost_samples else None
    print(f"wrote {len(out)} county transport records -> {OUT}")
    print(f"  paths found: {n_path} | no path: {n_nopath}")
    print(f"  leg-mode usage (counties whose route includes the mode): {dict(mode_use)}")
    print(f"  slurry $/tCO₂: min {cost_samples[0]:.0f} / median {med:.0f} / max {cost_samples[-1]:.0f}")
    # spot checks
    for cid, label in [("US-19153", "Polk Co, IA (corn belt)"),
                       ("US-06037", "Los Angeles, CA"),
                       ("US-48201", "Harris Co, TX (Houston/Gulf)"),
                       ("US-36061", "New York Co, NY")]:
        r = out.get(cid)
        if r:
            print(f"  {label}: {'+'.join(r['modes'])} -> {r['dest_well']} "
                  f"({r['total_km']} km) | co2 ${r['by_payload']['co2']}, "
                  f"bio_oil ${r['by_payload']['bio_oil']}, slurry ${r['by_payload']['slurry']} /tCO₂")


if __name__ == "__main__":
    main()
