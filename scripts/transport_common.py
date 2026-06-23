#!/usr/bin/env python3
"""
Shared multimodal CO₂/biomass transport-cost model (to_do item 4).

Computes the least-cost combination of TRUCK + RAIL + SHIP/BARGE to move material from a region
centroid to the nearest OPERATING geologic-storage well, and the carbon-density-weighted delivered
cost in $/tCO₂ for each payload class. v1 is "schematic": a sparse graph over curated transfer nodes
(rail terminals, ports) with straight legs and mode-specific detour factors — distances are
great-circle screening estimates, not network-routed (a v2 upgrade). Cost accuracy is decent; the
drawn path is stylized.

Key property used throughout: the cost-minimising PATH is independent of payload, because the payload
carbon-density (mass moved per tonne CO₂ stored) is a single scalar that multiplies every leg equally.
So we solve ONE least-cost path per region, then scale by each payload's mass factor (plus a one-off
CO₂ liquefaction cost for the gaseous-CO₂ payload). Per-leg handling costs approximate intermodal
transfers (each mode-entry carries a loading/handling charge).
"""
import heapq
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/
from engine_core import haversine_km  # noqa: E402

# --- Mode cost model (country-level $ is fine; literature-anchored midpoints, tunable) ---
# $/tonne-km, a per-tonne handling/transfer charge applied on entering the mode, and a detour
# factor converting great-circle km to an approximate routed distance.
MODES = {
    "truck": {"usd_per_tkm": 0.12, "handling_usd_per_t": 2.0, "detour": 1.40},
    "rail":  {"usd_per_tkm": 0.035, "handling_usd_per_t": 4.0, "detour": 1.20},
    "ship":  {"usd_per_tkm": 0.015, "handling_usd_per_t": 5.0, "detour": 1.20},  # coastal/barge
}
CO2_LIQUEFACTION_USD_PER_T = 25.0   # once, to move captured CO₂ by truck/rail/ship (not pipeline)

# Payload carbon density: tonnes MOVED per tonne CO₂ ultimately stored. Drives the whole cost.
#   co2     — move the captured gaseous/liquefied CO₂ itself (~1:1) + liquefaction.
#   bio_oil — pyrolysis-densified liquid (~2.2 tCO₂/t) → cheap to haul far (Charm).
#   slurry  — wet biomass/organic-waste slurry (water-heavy) → expensive beyond short haul (Vaulted).
# burial / biochar are storage-INDEPENDENT (buried/applied locally) → no transport-to-well cost; the
# engine treats them as 0 and must not read this table for them.
PAYLOAD_MASS_PER_TCO2 = {"co2": 1.00, "bio_oil": 0.45, "slurry": 2.00}

# Which pathway moves which payload to the well (for the engine, Phase C).
PATHWAY_PAYLOAD = {
    "beccs": "co2", "beccs_pp": "co2", "wte_ccs": "co2", "ad_ccs": "co2",
    "bio_oil": "bio_oil", "injection": "slurry",
    # burial, biochar: no transport-to-well (None)
}

# Graph fan-out (sparse k-nearest keeps per-region Dijkstra trivial).
K_RAIL_NEIGHBORS = 4     # terminal -> nearest rail terminals
K_SHIP_NEIGHBORS = 4     # port -> nearest same-basin (or River↔Gulf) ports
WELL_RAIL_LASTMILE = 3   # well <- nearest terminals (truck last mile)
WELL_PORT_LASTMILE = 2   # well <- nearest ports (truck last mile)
PORT_RAIL_LINK = 2       # port <-> nearest terminals (truck, links ship net to rail net)
ORIG_WELL = 3            # origin -> nearest wells (truck, incl. pure-truck option)
ORIG_RAIL = 3            # origin -> nearest terminals (truck first mile)
ORIG_PORT = 2            # origin -> nearest ports (truck first mile)

# Ship basins that are navigably connected (besides intra-basin). The Mississippi/Ohio river
# system ("River") empties into the Gulf, so barge traffic reaches Gulf storage.
BASIN_LINKS = {("River", "Gulf"), ("Gulf", "River")}


def _leg_cost(mode, km):
    m = MODES[mode]
    return m["handling_usd_per_t"] + m["usd_per_tkm"] * km * m["detour"]


def _km(a, b):
    return haversine_km(a[1], a[0], b[1], b[0])   # nodes are [lat, lon]


class TransportGraph:
    """Static multimodal graph over wells + rail terminals + ports. Per region, add the origin
    node, run a small Dijkstra to the nearest well, then drop the origin."""

    def __init__(self, wells, terminals, ports):
        # node id -> {"pos":[lat,lon], "kind":..., "name":..., "basin":...}
        self.nodes = {}
        self.adj = {}   # node id -> list[(nbr_id, cost, mode)]
        self._wells = []
        for i, w in enumerate(wells):
            nid = f"W{i}"
            self.nodes[nid] = {"pos": [w["lat"], w["lon"]], "kind": "well", "name": w["name"]}
            self._wells.append(nid)
        self._terms = []
        for i, t in enumerate(terminals):
            nid = f"R{i}"
            self.nodes[nid] = {"pos": [t["lat"], t["lon"]], "kind": "rail", "name": t.get("name", "rail terminal")}
            self._terms.append(nid)
        self._ports = []
        for i, p in enumerate(ports):
            nid = f"P{i}"
            self.nodes[nid] = {"pos": [p["lat"], p["lon"]], "kind": "port",
                               "name": p.get("name", "port"), "basin": p.get("basin", "?")}
            self._ports.append(nid)
        for nid in self.nodes:
            self.adj[nid] = []
        self._build_static_edges()

    def _add(self, a, b, mode, bidir=True):
        km = _km(self.nodes[a]["pos"], self.nodes[b]["pos"])
        c = _leg_cost(mode, km)
        self.adj[a].append((b, c, mode))
        if bidir:
            self.adj[b].append((a, c, mode))

    def _nearest(self, src, pool, k, pred=None):
        cand = [(self._d(src, n), n) for n in pool if n != src and (pred is None or pred(n))]
        cand.sort()
        return [n for _, n in cand[:k]]

    def _d(self, a, b):
        return _km(self.nodes[a]["pos"], self.nodes[b]["pos"])

    def _build_static_edges(self):
        # rail network: each terminal -> nearest terminals (rail)
        for t in self._terms:
            for nbr in self._nearest(t, self._terms, K_RAIL_NEIGHBORS):
                self._add(t, nbr, "rail")
        # ship network: each port -> nearest ports in a navigable-connected basin (ship)
        def connected(a):
            ba = self.nodes[a]["basin"]
            return lambda n: self.nodes[n]["basin"] == ba or (ba, self.nodes[n]["basin"]) in BASIN_LINKS
        for p in self._ports:
            for nbr in self._nearest(p, self._ports, K_SHIP_NEIGHBORS, pred=connected(p)):
                self._add(p, nbr, "ship")
        # link ship network to rail network (truck) and to wells (truck last mile)
        for p in self._ports:
            for t in self._nearest(p, self._terms, PORT_RAIL_LINK):
                self._add(p, t, "truck")
        for w in self._wells:
            for t in self._nearest(w, self._terms, WELL_RAIL_LASTMILE):
                self._add(w, t, "truck")
            for p in self._nearest(w, self._ports, WELL_PORT_LASTMILE):
                self._add(w, p, "truck")

    def least_cost_to_well(self, origin_pos):
        """Dijkstra from a temporary origin (truck first-mile to nearby wells/terminals/ports).
        Returns (per_tonne_usd, legs, dest_well_name) or (None, [], None)."""
        O = "_O"
        self.nodes[O] = {"pos": origin_pos, "kind": "origin", "name": "origin"}
        self.adj[O] = []
        for w in self._nearest(O, self._wells, ORIG_WELL):
            self._add(O, w, "truck", bidir=False)
        for t in self._nearest(O, self._terms, ORIG_RAIL):
            self._add(O, t, "truck", bidir=False)
        for p in self._nearest(O, self._ports, ORIG_PORT):
            self._add(O, p, "truck", bidir=False)

        dist = {O: 0.0}
        prev = {}                 # node -> (prev_node, mode)
        pq = [(0.0, O)]
        best_well, best_cost = None, None
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, float("inf")):
                continue
            if self.nodes[u]["kind"] == "well":
                best_well, best_cost = u, d
                break
            for v, c, mode in self.adj[u]:
                nd = d + c
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    prev[v] = (u, mode)
                    heapq.heappush(pq, (nd, v))

        legs = []
        if best_well is not None:
            # reconstruct path
            chain = []
            cur = best_well
            while cur in prev:
                p, mode = prev[cur]
                chain.append((p, cur, mode))
                cur = p
            chain.reverse()
            for a, b, mode in chain:
                pa, pb = self.nodes[a]["pos"], self.nodes[b]["pos"]
                legs.append({
                    "mode": mode,
                    "from": [round(pa[0], 3), round(pa[1], 3)],
                    "to": [round(pb[0], 3), round(pb[1], 3)],
                    "km": round(_km(pa, pb) * MODES[mode]["detour"]),
                    "to_name": self.nodes[b]["name"] if self.nodes[b]["kind"] != "origin" else None,
                })
        # drop the temporary origin and its edges
        for nid in (self._nearest(O, self._wells, ORIG_WELL)
                    + self._nearest(O, self._terms, ORIG_RAIL)
                    + self._nearest(O, self._ports, ORIG_PORT)):
            pass
        del self.nodes[O]
        del self.adj[O]
        dest_name = self.nodes[best_well]["name"] if best_well is not None else None
        return (round(best_cost, 2) if best_cost is not None else None, legs, dest_name)


def payload_costs(per_tonne_usd, has_path):
    """Per-payload delivered $/tCO₂ from the (payload-independent) per-tonne path cost."""
    if per_tonne_usd is None:
        return {k: None for k in PAYLOAD_MASS_PER_TCO2}
    out = {}
    for payload, mass in PAYLOAD_MASS_PER_TCO2.items():
        c = per_tonne_usd * mass
        if payload == "co2" and has_path:
            c += CO2_LIQUEFACTION_USD_PER_T
        out[payload] = round(c, 1)
    return out
