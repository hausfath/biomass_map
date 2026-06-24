#!/usr/bin/env python3
"""
EU NUTS-2 multimodal transport cost + routes (to_do item 4, extended to EU).

Destinations are the EU CO₂-storage **projects** (Northern Lights, Porthos, Greensand, Ravenna, …) —
nearly all **offshore**, so they are flagged marine and reached from coastal ports by ship (searoute),
not truck. Status tiers like the US: operational = full-confidence; construction/planned = "permitted"
(storage access later capped at moderate + flagged). Transfer nodes: curated EU rail hubs, ports, and
the Rhine / Main-Danube / Elbe / Rhône / Seine / Po barge corridors.

Output: data/processed/transport_eu.json (keyed by NUTS-2 id). Mirrors transport_us.json schema.
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

FEED = os.path.join(PROC, "feedstocks_eu_nuts.json")
PROJECTS = os.path.join(PROC, "storage_projects_eu.json")
NODES = os.path.join(GEO, "transport_nodes_eu.json")
OUT = os.path.join(PROC, "transport_eu.json")
CAP = 100.0


def main():
    feeds = json.load(open(FEED))
    projects = json.load(open(PROJECTS))
    # storage projects -> offshore "wells" (marine, reached by ship). Map project status to the
    # permit-confidence tiers: operational stays firm; under-CONSTRUCTION → 'issued' (firm, near-
    # certain); PLANNED/announced → 'pending' (speculative fallback).
    STAGE = {"operational": "operational", "construction": "issued", "planned": "pending"}
    wells = [{"name": p["name"], "lat": p["lat"], "lon": p["lon"],
              "status": STAGE.get(p.get("status"), "pending"), "marine": True}
             for p in projects if p.get("lat") is not None]
    n_op = sum(1 for w in wells if w["status"] in ("operational", "issued"))

    nodes = json.load(open(NODES))
    terminals = nodes["rail_terminals"]
    coastal_ports = nodes["coastal_ports"]
    river_corridors = nodes["river_corridors"]
    print(f"storage projects: {len(wells)} ({n_op} firm [operational+construction] + "
          f"{len(wells)-n_op} planned; all offshore) | rail hubs: {len(terminals)} | "
          f"ports: {len(coastal_ports)} | river waypoints: {sum(len(v) for v in river_corridors.values())}")
    graph = TransportGraph(wells, terminals, coastal_ports, river_corridors)

    regions = [(r["id"], [r["centroid"][1], r["centroid"][0]], r.get("dominant_feedstock"))
               for r in feeds if r.get("centroid")]
    out, stats = build_records(graph, regions, cap=CAP)
    save_caches()
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    cs = sorted(r["by_payload"]["slurry"] for r in out.values())
    med = cs[len(cs) // 2] if cs else None
    print(f"wrote {len(out)} NUTS-2 transport records -> {OUT}")
    print(f"  paths: {stats['paths']} | no path: {stats['no_path']} | permitted-rescued: {stats['rescued']}")
    print(f"  leg-mode usage: {stats['modes']}")
    print(f"  slurry $/tCO₂: min {cs[0]:.0f} / median {med:.0f} / max {cs[-1]:.0f}")
    for rid, label in [("EU-NL33", "Zuid-Holland / Rotterdam (NL)"),
                       ("EU-DE60", "Hamburg (DE)"), ("EU-ITC4", "Lombardia (IT)"),
                       ("EU-AT11", "Burgenland (AT, inland)")]:
        r = out.get(rid)
        if r:
            print(f"  {label}: {'+'.join(r['modes'])} -> {r['dest_well']} ({r['dest_status']}) "
                  f"co2 ${r['by_payload']['co2']}, slurry ${r['by_payload']['slurry']} /tCO₂")


if __name__ == "__main__":
    main()
