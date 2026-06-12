#!/usr/bin/env python3
"""
US county geometry for the county-level BiCRS map.

Source: US Census Cartographic Boundary file (1:20m) — data/geo/us_raw/cb_2022_us_county_20m.*
Output:
  data/geo/geometry_us_counties.js   window.GEO_US_COUNTIES (FeatureCollection; file:// safe)
  data/geo/us_counties.json          same features, for the engine (point-in-polygon, basin overlap)

Counties are simplified (Douglas-Peucker) and coordinates rounded to 3 dp (~110 m). Properties:
  id    = "US-{FIPS}"  (5-digit GEOID, e.g. US-06037)
  name  = county name
  state = USPS abbreviation (e.g. CA)
  fips  = 5-digit GEOID
  area_km2 = land area (ALAND), used by the engine for feedstock density (t/km^2)
  centroid = [lon, lat] area-weighted centroid of the largest ring (interior point)
"""
import json
import os

import shapefile  # pyshp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEO = os.path.join(ROOT, "data", "geo")
SHP = os.path.join(GEO, "us_raw", "cb_2022_us_county_20m")

COORD_DP = 3            # decimal places (~110 m)
SIMPLIFY_TOL = 0.006    # Douglas-Peucker tolerance in degrees (~600 m)

# Exclude outlying territories with no biomass assessment (AS, GU, MP, PR, VI).
EXCLUDE_STATEFP = {"60", "66", "69", "72", "78"}


def _perp_dist(p, a, b):
    """Perpendicular distance from point p to segment a-b (in degree space)."""
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def _dp(points, tol):
    """Douglas-Peucker simplification of an open polyline."""
    if len(points) < 3:
        return points
    dmax, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        d = _perp_dist(points[i], points[0], points[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        left = _dp(points[:idx + 1], tol)
        right = _dp(points[idx:], tol)
        return left[:-1] + right
    return [points[0], points[-1]]


def simplify_ring(ring):
    """Simplify + round a closed ring; keep it closed and valid (>=4 points)."""
    if len(ring) > 4:
        ring = _dp(ring, SIMPLIFY_TOL)
    out = []
    last = None
    for x, y in ring:
        pt = [round(x, COORD_DP), round(y, COORD_DP)]
        if pt != last:
            out.append(pt)
        last = pt
    if len(out) < 4:
        # Too small after simplification — fall back to a rounded (unsimplified) ring.
        out = []
        last = None
        for x, y in ring:
            pt = [round(x, COORD_DP), round(y, COORD_DP)]
            if pt != last:
                out.append(pt)
            last = pt
    if out and out[0] != out[-1]:
        out.append(out[0])
    return out


def _ring_area_centroid(ring):
    """Signed area (deg^2) and area-weighted centroid of a closed ring."""
    a = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i]
        x1, y1 = ring[i + 1]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a *= 0.5
    if a == 0:
        # Degenerate: average vertices.
        n = len(ring) - 1 or 1
        return 0.0, [sum(p[0] for p in ring[:-1]) / n, sum(p[1] for p in ring[:-1]) / n]
    return a, [cx / (6 * a), cy / (6 * a)]


def process_geometry(geo):
    """Simplify a pyshp __geo_interface__ geometry; return (geometry, centroid, ok)."""
    t = geo["type"]
    if t == "Polygon":
        polys = [geo["coordinates"]]
    elif t == "MultiPolygon":
        polys = geo["coordinates"]
    else:
        return None, None, False

    new_polys = []
    best_area, best_centroid = -1.0, None
    for poly in polys:
        new_rings = []
        for ri, ring in enumerate(poly):
            sr = simplify_ring([list(pt) for pt in ring])
            if len(sr) >= 4:
                new_rings.append(sr)
                if ri == 0:  # exterior ring — track largest for centroid
                    area, c = _ring_area_centroid(sr)
                    if abs(area) > best_area:
                        best_area, best_centroid = abs(area), c
        if new_rings:
            new_polys.append(new_rings)

    if not new_polys:
        return None, None, False
    if len(new_polys) == 1:
        geom = {"type": "Polygon", "coordinates": new_polys[0]}
    else:
        geom = {"type": "MultiPolygon", "coordinates": new_polys}
    return geom, best_centroid, True


def main():
    r = shapefile.Reader(SHP)
    field_names = [f[0] for f in r.fields[1:]]
    features = []
    skipped = 0
    for sr in r.iterShapeRecords():
        rec = dict(zip(field_names, sr.record))
        if rec["STATEFP"] in EXCLUDE_STATEFP:
            continue
        geom, centroid, ok = process_geometry(sr.shape.__geo_interface__)
        if not ok:
            skipped += 1
            continue
        fips = rec["GEOID"]
        features.append({
            "type": "Feature",
            "properties": {
                "id": "US-" + fips,
                "name": rec["NAME"],
                "state": rec["STUSPS"],
                "fips": fips,
                "area_km2": round((rec.get("ALAND") or 0) / 1e6, 1),
                "centroid": [round(centroid[0], COORD_DP), round(centroid[1], COORD_DP)],
            },
            "geometry": geom,
        })

    fc = {"type": "FeatureCollection", "features": features}

    out_js = os.path.join(GEO, "geometry_us_counties.js")
    with open(out_js, "w") as f:
        f.write("// Auto-generated by scripts/us/build_county_geo.py — US county geometry (Census 20m).\n")
        f.write("window.GEO_US_COUNTIES = " + json.dumps(fc, separators=(",", ":")) + ";\n")

    out_json = os.path.join(GEO, "us_counties.json")
    with open(out_json, "w") as f:
        json.dump(fc, f, separators=(",", ":"))

    print(f"counties: {len(features)} (skipped {skipped})")
    print(f"wrote {out_js} ({os.path.getsize(out_js):,} bytes)")
    print(f"wrote {out_json} ({os.path.getsize(out_json):,} bytes)")


if __name__ == "__main__":
    main()
