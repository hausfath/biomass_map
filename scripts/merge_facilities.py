#!/usr/bin/env python3
"""Merge regional facility expansion files into facilities.json with dedup + validation."""
import json, os, re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")

EXISTING = os.path.join(PROC, "facilities.json")
REGION_FILES = ["facilities_na.json", "facilities_uknordic.json", "facilities_eu.json",
                "facilities_apac.json", "facilities_row.json"]
VALID_TYPES = {"pulp_paper", "ethanol", "wte", "bioenergy", "biogas_ad"}


def load(name):
    with open(os.path.join(PROC, name)) as f:
        return json.load(f)


def norm_name(n):
    n = (n or "").lower()
    n = re.sub(r"[^a-z0-9]+", " ", n).strip()
    return n


def valid(f):
    if f.get("type") not in VALID_TYPES:
        return False, f"bad type {f.get('type')}"
    lat, lon = f.get("lat"), f.get("lon")
    if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return False, "bad coords"
    if not f.get("name") or not f.get("country"):
        return False, "missing name/country"
    co2 = f.get("est_biogenic_co2_mtpa")
    if not isinstance(co2, dict) or co2.get("value") is None:
        return False, "missing co2 estimate"
    if f.get("retrofit_score") not in ("high", "medium", "low"):
        return False, "bad retrofit_score"
    return True, ""


merged = []
seen_names = set()
seen_geo = {}          # (round(lat,2), round(lon,2), type) -> name
dupes, invalid, geodupes = [], [], []

# existing first (authoritative; keep their existing/flags)
existing = load(EXISTING)
for f in existing:
    merged.append(f)
    seen_names.add((norm_name(f["name"]), f.get("country")))
    seen_geo[(round(f["lat"], 2), round(f["lon"], 2), f["type"])] = f["name"]

added_by_file = {}
for rf in REGION_FILES:
    recs = load(rf)
    added = 0
    for f in recs:
        ok, why = valid(f)
        if not ok:
            invalid.append((f.get("name"), why)); continue
        key = (norm_name(f["name"]), f.get("country"))
        if key in seen_names:
            dupes.append(f["name"]); continue
        gkey = (round(f["lat"], 2), round(f["lon"], 2), f["type"])
        if gkey in seen_geo:
            geodupes.append(f"{f['name']} ~ {seen_geo[gkey]}"); continue
        # strip any transient engine field
        f.pop("_state", None)
        merged.append(f)
        seen_names.add(key)
        seen_geo[gkey] = f["name"]
        added += 1
    added_by_file[rf] = added

with open(EXISTING, "w") as out:
    json.dump(merged, out, indent=2, ensure_ascii=False)

print(f"Existing: {len(existing)}  ->  Merged total: {len(merged)}")
print("Added per file:", added_by_file)
print("Name dupes skipped:", len(dupes), dupes[:8])
print("Geo dupes skipped:", len(geodupes), geodupes[:8])
print("Invalid skipped:", len(invalid), invalid[:8])
print("\nBy type:", dict(Counter(f["type"] for f in merged)))
print("By country (top 15):", Counter(f["country"] for f in merged).most_common(15))
