#!/usr/bin/env python3
"""
Shared multimodal CO₂/biomass transport-cost model (to_do item 4, v2).

Least-cost combination of TRUCK + RAIL + SHIP + BARGE from a region centroid to the nearest
OPERATING geologic-storage well, and the carbon-density-weighted delivered cost ($/tCO₂) per payload.

v2 over v1:
  - RAIL: 233 real NTAD intermodal terminals (was 44 curated) → short, realistic first-mile trucking.
  - SHIP (coastal): port-to-port legs routed by `searoute` — real marine geometry that goes AROUND
    land (no more straight lines across Florida), with real sea distance. Cached at build time.
  - BARGE (inland): a curated navigable-river network (Mississippi/Ohio/Missouri/Illinois/Tennessee
    corridors as ordered waypoints). Barge legs route ALONG the channel and are drawn following the
    river — they never cross land. Corridors connect only at real confluences (junctions), so barge
    requires a connected waterway.
  - Each ship/barge leg carries a `path` polyline (the real water geometry) for the map; truck/rail
    legs are straight. Consecutive same-mode hops are merged into one leg.

The cost-minimising PATH is payload-independent (carbon density is a scalar multiplier), so one
Dijkstra per region is scaled per payload (+ a one-off CO₂ liquefaction cost for the gaseous payload).
"""
import heapq
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/
from engine_core import haversine_km  # noqa: E402

# --- Mode cost model ($/tonne-km, per-tonne handling on mode entry, GC->routed detour factor). ---
MODES = {
    "truck": {"usd_per_tkm": 0.12, "handling_usd_per_t": 2.0, "detour": 1.40},
    "rail":  {"usd_per_tkm": 0.035, "handling_usd_per_t": 4.0, "detour": 1.20},
    "ship":  {"usd_per_tkm": 0.015, "handling_usd_per_t": 5.0, "detour": 1.00},  # searoute = real km
    "barge": {"usd_per_tkm": 0.012, "handling_usd_per_t": 4.0, "detour": 1.05},  # inland river barge
}
CO2_LIQUEFACTION_USD_PER_T = 25.0   # once, to move captured CO₂ by truck/rail/ship (not pipeline)

# Payload carbon density: tonnes MOVED per tonne CO₂ stored (drives the whole cost).
PAYLOAD_MASS_PER_TCO2 = {"co2": 1.00, "bio_oil": 0.45, "slurry": 2.00}
PATHWAY_PAYLOAD = {
    "beccs": "co2", "beccs_pp": "co2", "wte_ccs": "co2", "ad_ccs": "co2",
    "bio_oil": "bio_oil", "bio_oil_htl": "bio_oil", "injection": "slurry",
}

# Graph fan-out (k-nearest keeps per-region Dijkstra small).
K_RAIL_NEIGHBORS = 7    # higher k -> better long-haul corridor connectivity in the rail graph
WELL_RAIL_LASTMILE = 3
WELL_PORT_LASTMILE = 2
WELL_RIVER_LASTMILE = 2
PORT_RAIL_LINK = 2
ORIG_WELL = 3
ORIG_RAIL = 3
ORIG_PORT = 2
ORIG_RIVER = 2

# River confluences that connect corridors but don't share a waypoint name.
RIVER_JUNCTIONS = [("Grafton IL", "St Louis")]   # Illinois R meets the Mississippi above St Louis

_SEAROUTE_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "data", "geo", "transport_raw", "searoute_cache.json")


def _leg_cost(mode, km):
    m = MODES[mode]
    return m["handling_usd_per_t"] + m["usd_per_tkm"] * km * m["detour"]


def _km(a, b):
    return haversine_km(a[1], a[0], b[1], b[0])   # nodes are [lat, lon]


# --- searoute coastal geometry/distance, cached on disk (key "lat,lon|lat,lon") ---
_searoute = None
_sr_cache = None
_sr_dirty = False


def _load_searoute():
    global _searoute, _sr_cache
    if _sr_cache is None:
        try:
            _sr_cache = json.load(open(_SEAROUTE_CACHE))
        except (FileNotFoundError, ValueError):
            _sr_cache = {}
        try:
            import searoute as sr
            _searoute = sr
        except ImportError:
            _searoute = False
            print("  (searoute not installed — coastal ship legs fall back to great-circle)")
    return _searoute


def _save_searoute_cache():
    if _sr_dirty:
        os.makedirs(os.path.dirname(_SEAROUTE_CACHE), exist_ok=True)
        with open(_SEAROUTE_CACHE, "w") as f:
            json.dump(_sr_cache, f, separators=(",", ":"))


def _sea_route(a, b):
    """(km, path[[lat,lon]...]) along real sea lanes between coastal points a,b ([lat,lon])."""
    global _sr_dirty
    sr = _load_searoute()
    key = f"{a[0]:.3f},{a[1]:.3f}|{b[0]:.3f},{b[1]:.3f}"
    if key in _sr_cache:
        c = _sr_cache[key]
        return c["km"], c["path"]
    if not sr:
        return _km(a, b), [list(a), list(b)]
    try:
        r = sr.searoute([a[1], a[0]], [b[1], b[0]])   # lon,lat
        km = round(float(r.properties["length"]))
        coords = [[round(y, 3), round(x, 3)] for x, y in r["geometry"]["coordinates"]]
        if len(coords) < 2:
            coords = [list(a), list(b)]
    except Exception:
        km, coords = round(_km(a, b)), [list(a), list(b)]
    _sr_cache[key] = {"km": km, "path": coords}
    _sr_dirty = True
    return km, coords


class TransportGraph:
    """Static multimodal graph (wells + rail terminals + coastal ports + river waypoints). Per region
    add a temporary origin, Dijkstra to the nearest well, then drop the origin."""

    def __init__(self, wells, terminals, coastal_ports, river_corridors):
        self.nodes = {}                # id -> {pos,kind,name,basin?,status?}
        self.adj = {}                  # id -> list[(nbr, cost, mode, km, path|None)]
        self._wells, self._terms, self._ports, self._rivers = [], [], [], []

        for i, w in enumerate(wells):
            nid = f"W{i}"
            self.nodes[nid] = {"pos": [w["lat"], w["lon"]], "kind": "well", "name": w["name"],
                               "status": w.get("status", "operational")}
            self._wells.append(nid)
        for i, t in enumerate(terminals):
            nid = f"R{i}"
            self.nodes[nid] = {"pos": [t["lat"], t["lon"]], "kind": "rail",
                               "name": t.get("name", "rail terminal")}
            self._terms.append(nid)
        for i, p in enumerate(coastal_ports):
            nid = f"P{i}"
            self.nodes[nid] = {"pos": [p["lat"], p["lon"]], "kind": "port",
                               "name": p.get("name", "port"), "basin": p.get("basin", "?")}
            self._ports.append(nid)
        # river waypoints: shared name == same node (junction)
        self._wp_by_name = {}
        for corridor in river_corridors.values():
            prev = None
            for (name, lat, lon) in corridor:
                if name not in self._wp_by_name:
                    nid = f"V{len(self._rivers)}"
                    self.nodes[nid] = {"pos": [lat, lon], "kind": "river", "name": name}
                    self._wp_by_name[name] = nid
                    self._rivers.append(nid)
                nid = self._wp_by_name[name]
                if prev is not None and prev != nid:
                    self._barge_edge(prev, nid)
                prev = nid
        for a, b in RIVER_JUNCTIONS:
            if a in self._wp_by_name and b in self._wp_by_name:
                self._barge_edge(self._wp_by_name[a], self._wp_by_name[b])

        for nid in self.nodes:
            self.adj.setdefault(nid, [])
        self._build_static_edges()

    # edge helpers ---------------------------------------------------------
    def _edge(self, a, b, mode, km=None, path=None, bidir=True):
        pa, pb = self.nodes[a]["pos"], self.nodes[b]["pos"]
        if km is None:
            km = _km(pa, pb)
        cost = _leg_cost(mode, km)
        self.adj.setdefault(a, []).append((b, cost, mode, km, path))
        if bidir:
            rpath = list(reversed(path)) if path else None
            self.adj.setdefault(b, []).append((a, cost, mode, km, rpath))

    def _barge_edge(self, a, b):
        pa, pb = self.nodes[a]["pos"], self.nodes[b]["pos"]
        self._edge(a, b, "barge", km=_km(pa, pb), path=[list(pa), list(pb)])

    def _nearest(self, src_pos, pool, k):
        cand = sorted(((_km(src_pos, self.nodes[n]["pos"]), n) for n in pool))
        return [n for _, n in cand[:k]]

    def _build_static_edges(self):
        # rail network
        for t in self._terms:
            for nbr in self._nearest(self.nodes[t]["pos"], self._terms, K_RAIL_NEIGHBORS + 1):
                if nbr != t:
                    self._edge(t, nbr, "rail")
        # coastal ship network: searoute between nearest same/adjacent-basin ports
        OPEN = {"Gulf": {"Gulf", "Atlantic"}, "Atlantic": {"Atlantic", "Gulf"},
                "Pacific": {"Pacific"}, "GreatLakes": {"GreatLakes"}}
        for p in self._ports:
            bp = self.nodes[p]["basin"]
            pool = [q for q in self._ports if q != p and self.nodes[q]["basin"] in OPEN.get(bp, {bp})]
            for nbr in self._nearest(self.nodes[p]["pos"], pool, 4):
                km, path = _sea_route(self.nodes[p]["pos"], self.nodes[nbr]["pos"])
                self._edge(p, nbr, "ship", km=km, path=path, bidir=False)
        # link ports & wells to the rail/river networks via truck last-mile
        for p in self._ports:
            for t in self._nearest(self.nodes[p]["pos"], self._terms, PORT_RAIL_LINK):
                self._edge(p, t, "truck")
        for w in self._wells:
            for t in self._nearest(self.nodes[w]["pos"], self._terms, WELL_RAIL_LASTMILE):
                self._edge(w, t, "truck")
            for p in self._nearest(self.nodes[w]["pos"], self._ports, WELL_PORT_LASTMILE):
                self._edge(w, p, "truck")
            for v in self._nearest(self.nodes[w]["pos"], self._rivers, WELL_RIVER_LASTMILE):
                self._edge(w, v, "truck")

    # per-region solve -----------------------------------------------------
    def least_cost_to_well(self, origin_pos):
        """Full Dijkstra (no early stop) → cheapest per-tonne path to the nearest OPERATING well and
        to the nearest PERMITTED (non-operating) well. Returns
        {"operational": (cost, legs, name) | None, "permitted": (cost, legs, name, status) | None}."""
        O = "_O"
        self.nodes[O] = {"pos": list(origin_pos), "kind": "origin", "name": "origin"}
        self.adj[O] = []
        for w in self._nearest(origin_pos, self._wells, ORIG_WELL):
            self._edge(O, w, "truck", bidir=False)
        for t in self._nearest(origin_pos, self._terms, ORIG_RAIL):
            self._edge(O, t, "truck", bidir=False)
        for p in self._nearest(origin_pos, self._ports, ORIG_PORT):
            self._edge(O, p, "truck", bidir=False)
        for v in self._nearest(origin_pos, self._rivers, ORIG_RIVER):
            self._edge(O, v, "truck", bidir=False)

        dist = {O: 0.0}
        prev = {}
        pq = [(0.0, O)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, float("inf")):
                continue
            for v, c, mode, km, path in self.adj.get(u, []):
                nd = d + c
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    prev[v] = (u, mode, km, path)
                    heapq.heappush(pq, (nd, v))

        best_op = best_perm = None      # (cost, well_id)
        for w in self._wells:
            if w not in dist:
                continue
            if self.nodes[w]["status"] == "operational":
                if best_op is None or dist[w] < best_op[0]:
                    best_op = (dist[w], w)
            else:
                if best_perm is None or dist[w] < best_perm[0]:
                    best_perm = (dist[w], w)

        def pack(entry, with_status=False):
            if entry is None:
                return None
            cost, wid = entry
            legs = self._reconstruct(prev, wid)
            out = (round(cost, 2), legs, self.nodes[wid]["name"])
            return out + (self.nodes[wid]["status"],) if with_status else out

        result = {"operational": pack(best_op), "permitted": pack(best_perm, with_status=True)}
        del self.nodes[O]
        del self.adj[O]
        return result

    def _reconstruct(self, prev, well):
        # walk back to origin collecting (a, b, mode, km, path)
        hops = []
        cur = well
        while cur in prev:
            p, mode, km, path = prev[cur]
            hops.append((p, cur, mode, km, path))
            cur = p
        hops.reverse()
        # merge consecutive same-mode hops into one leg (concatenating water geometry)
        legs = []
        for a, b, mode, km, path in hops:
            pa, pb = self.nodes[a]["pos"], self.nodes[b]["pos"]
            seg = path if path else [list(pa), list(pb)]
            if legs and legs[-1]["mode"] == mode:
                L = legs[-1]
                L["km"] = round(L["km"] + km * MODES[mode]["detour"])
                pts = L["path"]
                pts.extend(seg[1:] if seg and pts and pts[-1] == seg[0] else seg)
                L["to"] = [round(pb[0], 3), round(pb[1], 3)]
                L["to_name"] = self.nodes[b]["name"] if self.nodes[b]["kind"] != "origin" else None
            else:
                legs.append({
                    "mode": mode,
                    "from": [round(pa[0], 3), round(pa[1], 3)],
                    "to": [round(pb[0], 3), round(pb[1], 3)],
                    "km": round(km * MODES[mode]["detour"]),
                    "path": [[round(x, 3), round(y, 3)] for x, y in seg],
                    "to_name": self.nodes[b]["name"] if self.nodes[b]["kind"] != "origin" else None,
                })
        # drop trivial straight path on land legs (frontend draws from->to); keep water geometry
        for L in legs:
            if L["mode"] in ("truck", "rail"):
                L.pop("path", None)
        return legs


def payload_costs(per_tonne_usd, has_path):
    if per_tonne_usd is None:
        return {k: None for k in PAYLOAD_MASS_PER_TCO2}
    out = {}
    for payload, mass in PAYLOAD_MASS_PER_TCO2.items():
        c = per_tonne_usd * mass
        if payload == "co2" and has_path:
            c += CO2_LIQUEFACTION_USD_PER_T
        out[payload] = round(c, 1)
    return out


def save_caches():
    _save_searoute_cache()
