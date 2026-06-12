#!/usr/bin/env python3
"""
US geologic CO2 storage-basin polygons for the county-level BiCRS map.

Source: NETL NATCARB Atlas saline storage formation outlines (v1502),
  data/geo/us_raw/natcarb_saline/.../NATCARB_Saline_Poly_v1502.shp
  Projection: Lambert Azimuthal Equal-Area (lon_0=-100, lat_0=45, WGS84, meters).

We keep ASSESSED, non-duplicate saline formations (real, assessed storage resource),
reproject to WGS84 lon/lat, simplify, and round to 3 dp. These are the "actual shapes"
of storage basins — used both as a map overlay and by the county engine (a county whose
centroid falls inside a formation has storage on-site; otherwise distance is measured to
the nearest formation boundary).

Output:
  data/geo/geometry_us_basins.js      window.GEO_US_BASINS (FeatureCollection; file:// safe)
  data/processed/storage_us_basins.json   polygons + bbox for the engine (point-in / distance)
"""
import json
import os

import shapefile  # pyshp
import pyproj

from build_county_geo import _dp, _ring_area_centroid  # reuse simplification helpers

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEO = os.path.join(ROOT, "data", "geo")
PROC = os.path.join(ROOT, "data", "processed")
SHP = os.path.join(GEO, "us_raw", "natcarb_saline",
                   "Natcarb_Saline_poly_shapefile", "NATCARB_Saline_Poly_v1502")

COORD_DP = 3
BASIN_TOL = 0.01   # Douglas-Peucker tolerance in degrees (~1 km) — basins are broad
MIN_AREA_M2 = 3e8  # drop tiny slivers (<300 km^2) to reduce clutter

# Source CRS (from the .prj): Lambert Azimuthal Equal-Area on WGS84.
SRC = pyproj.CRS.from_proj4(
    "+proj=laea +lat_0=45 +lon_0=-100 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)
TF = pyproj.Transformer.from_crs(SRC, "EPSG:4326", always_xy=True)


def simplify_ring_ll(ring):
    """ring is a list of (lon,lat); DP-simplify + round + dedupe; keep closed (>=4 pts)."""
    if len(ring) > 4:
        ring = _dp(ring, BASIN_TOL)
    out, last = [], None
    for x, y in ring:
        pt = [round(x, COORD_DP), round(y, COORD_DP)]
        if pt != last:
            out.append(pt)
        last = pt
    if len(out) < 4:
        return None
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def reproject_ring(ring):
    """LAEA meters -> [lon,lat] list."""
    out = []
    for x, y in ring:
        lon, lat = TF.transform(x, y)
        out.append((lon, lat))
    return out


def process_shape(geo):
    """Reproject + simplify a pyshp geometry. Return (geometry, centroid) or (None, None)."""
    t = geo["type"]
    polys = [geo["coordinates"]] if t == "Polygon" else (
        geo["coordinates"] if t == "MultiPolygon" else None)
    if polys is None:
        return None, None

    new_polys = []
    best_area, best_centroid = -1.0, None
    for poly in polys:
        new_rings = []
        for ri, ring in enumerate(poly):
            sr = simplify_ring_ll(reproject_ring(ring))
            if sr:
                new_rings.append(sr)
                if ri == 0:
                    area, c = _ring_area_centroid(sr)
                    if abs(area) > best_area:
                        best_area, best_centroid = abs(area), c
        if new_rings:
            new_polys.append(new_rings)

    if not new_polys:
        return None, None
    geom = ({"type": "Polygon", "coordinates": new_polys[0]} if len(new_polys) == 1
            else {"type": "MultiPolygon", "coordinates": new_polys})
    return geom, best_centroid


def bbox_of(geom):
    """[minlon, minlat, maxlon, maxlat] over all coordinates."""
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for x in c:
                walk(x)
    walk(geom["coordinates"])
    return [min(xs), min(ys), max(xs), max(ys)]


def main():
    r = shapefile.Reader(SHP)
    fn = [f[0] for f in r.fields[1:]]
    feats = []
    engine = []
    for sr in r.iterShapeRecords():
        rec = dict(zip(fn, sr.record))
        if rec.get("ASSESSED") != 1 or rec.get("DUPLICATE") == 1:
            continue
        if (rec.get("Shape_Area") or 0) < MIN_AREA_M2:
            continue
        geom, centroid = process_shape(sr.shape.__geo_interface__)
        if not geom:
            continue
        name = (rec.get("RESOURCE_N") or "").strip() or "Saline formation"
        partnership = (rec.get("PARTNERSHI") or "").strip()
        bb = bbox_of(geom)
        props = {
            "name": name,
            "partnership": partnership,
            "storage_type": "saline",
            "confidence": "assessed",   # NATCARB-assessed saline storage resource
            "centroid": [round(centroid[0], COORD_DP), round(centroid[1], COORD_DP)],
        }
        feats.append({"type": "Feature", "properties": props, "geometry": geom})
        engine.append({"name": name, "confidence": "assessed", "bbox": bb,
                       "centroid": props["centroid"], "geometry": geom})

    fc = {"type": "FeatureCollection", "features": feats}
    out_js = os.path.join(GEO, "geometry_us_basins.js")
    with open(out_js, "w") as f:
        f.write("// Auto-generated by scripts/us/build_basin_geo.py — NATCARB saline storage basins.\n")
        f.write("window.GEO_US_BASINS = " + json.dumps(fc, separators=(",", ":")) + ";\n")

    out_json = os.path.join(PROC, "storage_us_basins.json")
    with open(out_json, "w") as f:
        json.dump(engine, f, separators=(",", ":"))

    print(f"basins: {len(feats)} assessed saline formations")
    print(f"wrote {out_js} ({os.path.getsize(out_js):,} bytes)")
    print(f"wrote {out_json} ({os.path.getsize(out_json):,} bytes)")


if __name__ == "__main__":
    main()
