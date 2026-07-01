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

# Storage-well confidence tiers by permit status (how likely to be operational in time for a
# project starting today; see the Class VI permit-conversion analysis):
#   firm    — operational, or ISSUED (final permit granted; ~80-90% reach injection) → real storage.
#   draft   — draft permit at public-comment stage (~55-70%) → usable but lower confidence.
#   pending — application under review, no draft (~30-50%, slow/uncertain) → fallback only.
# (EU "construction" maps to issued; "planned" to pending — done in the EU transport build.)
STATUS_TIER = {"operational": "firm", "issued": "firm", "draft": "draft", "pending": "pending"}
FIRM_STATUSES = {"operational", "issued"}

# Payload carbon density: tonnes MOVED per tonne CO₂ stored (drives the whole cost). Derived from
# the material's carbon mass-fraction as transported:  mass = (12/44) / f_C = 0.273 / f_C  (storing
# 1 t CO₂ needs 0.273 t C). So a denser-carbon payload is cheaper to haul per tCO₂.
#   co2     1.00  — captured CO₂ is 27.3% C and the whole molecule is stored (+ liquefaction $).
#   bio_oil 0.55  — pyrolysis bio-oil ~50% C as transported (raw ~55-65% C dry but carries water).
#   bio_oil_htl 0.45 — HTL bio-crude is more deoxygenated (~60-65% C), so denser than pyrolysis oil.
#   slurry  — biomass injected as a pumpable slurry; carbon density depends HEAVILY on feedstock
#             (dry C fraction × as-injected solids fraction), so it is feedstock-specific below.
PAYLOAD_MASS_PER_TCO2 = {"co2": 1.00, "bio_oil": 0.55, "bio_oil_htl": 0.45, "slurry": 2.6}

# Biomass-injection (slurry) mass per tCO₂ by dominant feedstock. f_C_hauled = dry-C × solids:
#   woody  ~50% C dry × ~30% solids = 0.15 -> 1.8 ;  crop ~45% × ~28% = 0.126 -> 2.2 ;
#   manure/biosolids ~38% C dry × ~18% solids = 0.068 -> 4.0 (mostly water) ;  msw/mixed -> 2.6.
SLURRY_MASS_BY_FEEDSTOCK = {
    "forestry_woody": 1.8, "ag_dry": 2.2, "manure_wet": 4.0, "msw": 2.6, "mixed": 2.6,
}

PATHWAY_PAYLOAD = {
    "beccs": "co2", "beccs_pp": "co2", "wte_ccs": "co2", "ad_ccs": "co2",
    "bio_oil": "bio_oil", "bio_oil_htl": "bio_oil_htl", "injection": "slurry",
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
                               "status": w.get("status", "operational"),
                               "marine": bool(w.get("marine")),   # offshore storage → reached by ship
                               # Gaseous-CO₂ eligibility (item 7): captured CO₂ needs a dedicated CO₂
                               # store — a Class VI/RR well (or an offshore CCS project) — NOT a
                               # Class V biomass/bio-oil injection site (Vaulted/Charm). Class V is
                               # the ONLY ineligible class; everything else (VI, VI/RR, CA/EU CCS
                               # projects with no class) accepts CO₂.
                               "well_class": w.get("well_class"),
                               "co2_ok": w.get("well_class") != "V"}
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
        # navigably-connected sea basins (US + EU; scopes build separately so no transatlantic mix)
        OPEN = {"Gulf": {"Gulf", "Atlantic"}, "Atlantic": {"Atlantic", "Gulf", "NorthSea"},
                "Pacific": {"Pacific"}, "GreatLakes": {"GreatLakes"},
                "NorthSea": {"NorthSea", "Atlantic", "Baltic"}, "Baltic": {"Baltic", "NorthSea"},
                "Mediterranean": {"Mediterranean", "BlackSea", "Atlantic"},
                "BlackSea": {"BlackSea", "Mediterranean"}}
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
            if self.nodes[w]["marine"]:
                # offshore storage (e.g. North-Sea CCS): reached from coastal ports by SHIP, not truck
                for p in self._nearest(self.nodes[w]["pos"], self._ports, 3):
                    km, path = _sea_route(self.nodes[p]["pos"], self.nodes[w]["pos"])
                    self._edge(w, p, "ship", km=km, path=list(reversed(path)))
                continue
            for t in self._nearest(self.nodes[w]["pos"], self._terms, WELL_RAIL_LASTMILE):
                self._edge(w, t, "truck")
            for p in self._nearest(self.nodes[w]["pos"], self._ports, WELL_PORT_LASTMILE):
                self._edge(w, p, "truck")
            for v in self._nearest(self.nodes[w]["pos"], self._rivers, WELL_RIVER_LASTMILE):
                self._edge(w, v, "truck")

    # per-region solve -----------------------------------------------------
    def least_cost_to_well(self, origin_pos):
        """Full Dijkstra (no early stop) → cheapest per-tonne path to the nearest well in each
        CONFIDENCE TIER (by permit status; see STATUS_TIER): 'firm' = operational + issued (high odds
        of being operational in time, treated as real storage), 'draft' = draft permit (moderate),
        'pending' = pending application (speculative, fallback only). The path/cost are payload-
        independent, but the eligible DESTINATION SET differs by payload (item 7): gaseous CO₂ may
        only go to a CO₂-eligible well (Class VI/RR or a CCS project — `co2_ok`), while biomass
        bio-oil/slurry may use ANY well. So we return best-per-tier for both groups:
        {"gen": {tier: packed|None}, "co2": {tier: packed|None}}  (packed = (cost, legs, name, status))."""
        O = "_O"
        self.nodes[O] = {"pos": list(origin_pos), "kind": "origin", "name": "origin"}
        self.adj[O] = []
        onshore_wells = [w for w in self._wells if not self.nodes[w]["marine"]]
        for w in self._nearest(origin_pos, onshore_wells, ORIG_WELL):
            self._edge(O, w, "truck", bidir=False)   # direct truck only to onshore wells
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

        empty = {"firm": None, "draft": None, "pending": None}
        best = {"gen": dict(empty), "co2": dict(empty)}   # group -> tier -> (cost, well_id)
        for w in self._wells:
            if w not in dist:
                continue
            tier = STATUS_TIER.get(self.nodes[w]["status"], "pending")
            d = dist[w]
            if best["gen"][tier] is None or d < best["gen"][tier][0]:
                best["gen"][tier] = (d, w)
            if self.nodes[w]["co2_ok"] and (best["co2"][tier] is None or d < best["co2"][tier][0]):
                best["co2"][tier] = (d, w)

        def pack(entry):
            if entry is None:
                return None
            cost, wid = entry
            legs = self._reconstruct(prev, wid)
            return (round(cost, 2), legs, self.nodes[wid]["name"], self.nodes[wid]["status"])

        result = {grp: {tier: pack(e) for tier, e in tiers.items()} for grp, tiers in best.items()}
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


def build_records(graph, regions, cap=100.0):
    """Per-region transport records with status tiering, shared by all scopes.
    `regions` = iterable of (region_id, [lat, lon]) or (region_id, [lat, lon], dominant_feedstock).
    The dominant feedstock (if given) sets the feedstock-specific slurry carbon density. Returns
    (records_dict, stats_dict). Operating well preferred where its CO₂-delivered cost ≤ cap; else a
    permitted well 'rescues' the region. Stores legs (water geometry), per-payload cost, dest, etc."""
    from collections import Counter
    out, mode_use = {}, Counter()
    n_path = n_nopath = n_rescued = n_co2_far = 0
    for region in regions:
        rid, pos = region[0], region[1]
        dom = region[2] if len(region) > 2 else None
        res = graph.least_cost_to_well(pos)

        def co2_of(entry):
            return payload_costs(entry[0], True, dom)["co2"] if entry else None

        def choose(tiers):
            """Prefer a FIRM well (operational/issued) when its CO₂-delivered cost is within the cap;
            then a draft permit; then a pending application; else the cheapest well with any path."""
            firm, draft, pend = tiers["firm"], tiers["draft"], tiers["pending"]
            rescued = False
            pick = None
            if firm and co2_of(firm) is not None and co2_of(firm) <= cap:
                pick = firm
            elif draft and co2_of(draft) is not None and co2_of(draft) <= cap:
                pick = draft; rescued = True
            elif pend and co2_of(pend) is not None and co2_of(pend) <= cap:
                pick = pend; rescued = True
            if pick is None:
                cands = [e for e in (firm, draft, pend) if e]
                pick = min(cands, key=lambda e: e[0]) if cands else None
            return pick, rescued

        # General destination (ANY well) — drives storage access + the biomass payloads (bio-oil /
        # slurry can use any well, incl. Class V). CO₂-eligible destination (Class VI/RR or a CCS
        # project) — drives the gaseous-CO₂ payload only (item 7).
        gen, rescued = choose(res["gen"])
        co2, _ = choose(res["co2"])
        if gen is None:
            n_nopath += 1
            continue
        if rescued:
            n_rescued += 1
        per_tonne, legs, dest, dest_status = gen
        n_path += 1
        modes = sorted({leg["mode"] for leg in legs})
        for m in modes:
            mode_use[m] += 1

        by = payload_costs(per_tonne, bool(legs), dom)          # biomass payloads via the ANY well
        # gaseous CO₂ is re-costed to the nearest CO₂-ELIGIBLE well (None if none reachable → the
        # capture pathways get disqualified downstream). access_co2_usd keeps the general (any-well)
        # CO₂ cost for the storage-access grade so injection/bio-oil availability is NOT tightened.
        access_co2 = by["co2"]
        co2_dest = co2_status = co2_km = None
        co2_route_legs = None
        if co2:
            co2_pt, co2_route_legs, co2_dest, co2_status = co2
            by["co2"] = payload_costs(co2_pt, True, dom)["co2"]
            co2_km = sum(L["km"] for L in co2_route_legs)
            if co2_dest != dest:
                n_co2_far += 1
        else:
            by["co2"] = None

        rec = {
            "per_tonne_usd": per_tonne, "dest_well": dest, "dest_status": dest_status,
            "legs": legs, "by_payload": by,
            "modes": modes, "total_km": sum(leg["km"] for leg in legs),
            "access_co2_usd": access_co2,        # general (any-well) CO₂ cost → storage-access grade
            "co2_dest_well": co2_dest, "co2_dest_status": co2_status, "co2_total_km": co2_km,
        }
        # For a capture (gaseous-CO₂) pathway the CO₂ ships to a CO₂-ELIGIBLE well, which may differ
        # from the general destination — store its route legs so the map draws the right path (item 7).
        # Only stored when it actually differs, to keep the bundle small.
        if co2_route_legs is not None and co2_dest != dest:
            rec["co2_legs"] = co2_route_legs
        if res["co2"]["firm"]:
            rec["firm_co2_usd"] = co2_of(res["co2"]["firm"])   # nearest firm CO₂ store, for reference
        out[rid] = rec
    return out, {"paths": n_path, "no_path": n_nopath, "rescued": n_rescued,
                 "co2_to_distinct_well": n_co2_far, "modes": dict(mode_use)}


def payload_costs(per_tonne_usd, has_path, dom=None):
    """Delivered $/tCO₂ per payload class. The slurry (biomass-injection) factor is feedstock-
    specific (`dom` = dominant feedstock) since a manure slurry hauls ~2× the mass of woody residue
    per tCO₂; other payloads are feedstock-independent."""
    if per_tonne_usd is None:
        return {k: None for k in PAYLOAD_MASS_PER_TCO2}
    out = {}
    for payload, mass in PAYLOAD_MASS_PER_TCO2.items():
        if payload == "slurry":
            mass = SLURRY_MASS_BY_FEEDSTOCK.get(dom, mass)
        c = per_tonne_usd * mass
        if payload == "co2" and has_path:
            c += CO2_LIQUEFACTION_USD_PER_T
        out[payload] = round(c, 1)
    return out


def save_caches():
    _save_searoute_cache()
