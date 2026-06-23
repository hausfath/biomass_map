#!/usr/bin/env python3
"""
Assemble the US multimodal transport node/network file (to_do item 4, v2).

Writes data/geo/transport_nodes_us.json with three layers:
  rail_terminals : 241 real NTAD Intermodal Freight Facilities Rail TOFC/COFC terminals
                   (data/geo/transport_raw/ntad_rail_tofc.json) — replaces the v1 curated 44,
                   so first-mile truck legs to a railhead are short and realistic.
  coastal_ports  : curated coastal/Great-Lakes ports (basin tag) — ship legs between these are
                   routed by searoute at build time (real marine geometry, never crossing land).
  river_corridors: ordered waypoint polylines along the actually-navigable inland waterways
                   (Mississippi system + connectors). Consecutive waypoints are barge-connected;
                   corridors meet at shared-name junctions. Barge legs route ALONG these (no land
                   crossing); a region trucks to the nearest river waypoint, barges, trucks to a well.

Run after download_raw.sh (which fetches the NTAD layer). Re-run is cheap.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEO = os.path.join(ROOT, "data", "geo")
RAW = os.path.join(GEO, "transport_raw", "ntad_rail_tofc.json")
OUT = os.path.join(GEO, "transport_nodes_us.json")


def load_rail():
    d = json.load(open(RAW))
    out = []
    seen = set()
    for f in d.get("features", []):
        a = f["attributes"]
        lat, lon = a.get("LAT"), a.get("LON")
        if lat is None or lon is None:
            continue
        # dedupe near-coincident terminals (same ~0.05° cell) to keep the graph tidy
        cell = (round(lat, 2), round(lon, 2))
        if cell in seen:
            continue
        seen.add(cell)
        name = (a.get("TERMINAL") or "").strip() or "rail terminal"
        city = (a.get("CITY") or "").strip()
        st = (a.get("STATE") or "").strip()
        label = f"{name}" + (f" ({city}, {st})" if city else (f" ({st})" if st else ""))
        out.append({"name": label, "lat": round(lat, 4), "lon": round(lon, 4)})
    return out


# --- Coastal / Great-Lakes ports (ship legs routed by searoute). basin is informational. ---
COASTAL_PORTS = [
    {"name": "Houston, TX", "lat": 29.73, "lon": -95.27, "basin": "Gulf"},
    {"name": "Corpus Christi, TX", "lat": 27.80, "lon": -97.40, "basin": "Gulf"},
    {"name": "New Orleans, LA", "lat": 29.94, "lon": -90.06, "basin": "Gulf"},
    {"name": "Beaumont, TX", "lat": 30.08, "lon": -94.10, "basin": "Gulf"},
    {"name": "Lake Charles, LA", "lat": 30.22, "lon": -93.22, "basin": "Gulf"},
    {"name": "Mobile, AL", "lat": 30.69, "lon": -88.04, "basin": "Gulf"},
    {"name": "Tampa, FL", "lat": 27.92, "lon": -82.45, "basin": "Gulf"},
    {"name": "New York/NJ", "lat": 40.49, "lon": -74.26, "basin": "Atlantic"},
    {"name": "Norfolk, VA", "lat": 36.92, "lon": -76.33, "basin": "Atlantic"},
    {"name": "Savannah, GA", "lat": 32.08, "lon": -80.90, "basin": "Atlantic"},
    {"name": "Charleston, SC", "lat": 32.78, "lon": -79.92, "basin": "Atlantic"},
    {"name": "Jacksonville, FL", "lat": 30.39, "lon": -81.41, "basin": "Atlantic"},
    {"name": "Baltimore, MD", "lat": 39.22, "lon": -76.53, "basin": "Atlantic"},
    {"name": "Philadelphia, PA", "lat": 39.90, "lon": -75.13, "basin": "Atlantic"},
    {"name": "Wilmington, NC", "lat": 34.20, "lon": -77.95, "basin": "Atlantic"},
    {"name": "Los Angeles/Long Beach, CA", "lat": 33.74, "lon": -118.21, "basin": "Pacific"},
    {"name": "Oakland, CA", "lat": 37.80, "lon": -122.33, "basin": "Pacific"},
    {"name": "Seattle/Tacoma, WA", "lat": 47.34, "lon": -122.34, "basin": "Pacific"},
    {"name": "Portland, OR", "lat": 46.18, "lon": -123.83, "basin": "Pacific"},
    {"name": "Duluth, MN", "lat": 46.77, "lon": -92.09, "basin": "GreatLakes"},
    {"name": "Chicago, IL", "lat": 41.85, "lon": -87.61, "basin": "GreatLakes"},
    {"name": "Detroit, MI", "lat": 42.31, "lon": -83.08, "basin": "GreatLakes"},
    {"name": "Cleveland, OH", "lat": 41.51, "lon": -81.71, "basin": "GreatLakes"},
    {"name": "Toledo, OH", "lat": 41.69, "lon": -83.47, "basin": "GreatLakes"},
]

# --- Navigable inland waterways: ordered waypoints following the real river channels. Consecutive
#     waypoints are barge-connected; a waypoint name shared across corridors is a JUNCTION (the two
#     corridors connect there). Coordinates trace the channel so drawn legs never cross land. ---
RIVER_CORRIDORS = {
    # Lower + Upper Mississippi (Cairo & St Louis are junctions)
    "mississippi": [
        ("New Orleans", 29.95, -90.07), ("Baton Rouge", 30.45, -91.19),
        ("Natchez", 31.56, -91.40), ("Vicksburg", 32.34, -90.88),
        ("Greenville MS", 33.41, -91.06), ("Helena AR", 34.53, -90.59),
        ("Memphis", 35.13, -90.06), ("Cairo", 37.00, -89.18),
        ("Cape Girardeau", 37.31, -89.52), ("Chester IL", 37.91, -89.82),
        ("St Louis", 38.63, -90.19), ("Hannibal MO", 39.71, -91.36),
        ("Quincy IL", 39.93, -91.41), ("Burlington IA", 40.81, -91.10),
        ("Quad Cities", 41.51, -90.58), ("Dubuque", 42.50, -90.66),
        ("La Crosse WI", 43.81, -91.25), ("Winona MN", 44.05, -91.64),
        ("St Paul MN", 44.94, -93.09), ("Minneapolis", 44.98, -93.26),
    ],
    # Ohio River: joins the Mississippi at Cairo
    "ohio": [
        ("Cairo", 37.00, -89.18), ("Paducah KY", 37.08, -88.60),
        ("Evansville IN", 37.97, -87.57), ("Owensboro KY", 37.77, -87.11),
        ("Louisville", 38.26, -85.76), ("Cincinnati", 39.09, -84.50),
        ("Huntington WV", 38.42, -82.45), ("Wheeling WV", 40.06, -80.72),
        ("Pittsburgh", 40.44, -80.01),
    ],
    # Missouri River: joins the Mississippi at St Louis
    "missouri": [
        ("St Louis", 38.63, -90.19), ("Jefferson City", 38.58, -92.18),
        ("Kansas City", 39.11, -94.63), ("St Joseph MO", 39.77, -94.85),
        ("Omaha", 41.26, -95.93), ("Sioux City IA", 42.50, -96.41),
    ],
    # Illinois Waterway: Mississippi (near St Louis/Grafton) to Chicago
    "illinois": [
        ("Grafton IL", 38.97, -90.43), ("Peoria IL", 40.69, -89.59),
        ("Joliet IL", 41.52, -88.08), ("Chicago", 41.85, -87.61),
    ],
    # Tennessee R + Tennessee-Tombigbee to Mobile (joins Ohio at Paducah)
    "tennessee": [
        ("Paducah KY", 37.08, -88.60), ("Pickwick TN", 35.07, -88.25),
        ("Demopolis AL", 32.51, -87.84), ("Mobile", 30.69, -88.04),
    ],
}


def main():
    rail = load_rail()
    doc = {
        "_meta": "v2 multimodal transport nodes. rail_terminals = real NTAD TOFC/COFC (deduped). "
                 "coastal_ports routed by searoute (real marine geometry). river_corridors = curated "
                 "navigable inland waterways; barge follows these (no land crossing); shared waypoint "
                 "names are junctions.",
        "rail_terminals": rail,
        "coastal_ports": COASTAL_PORTS,
        "river_corridors": RIVER_CORRIDORS,
    }
    with open(OUT, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    nwp = sum(len(v) for v in RIVER_CORRIDORS.values())
    print(f"wrote {OUT}")
    print(f"  rail terminals: {len(rail)} (from NTAD)  | coastal ports: {len(COASTAL_PORTS)}  "
          f"| river corridors: {len(RIVER_CORRIDORS)} ({nwp} waypoints)")


if __name__ == "__main__":
    main()
