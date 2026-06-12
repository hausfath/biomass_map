#!/usr/bin/env python3
"""Merge regional feedstock files, validate all data files, run sanity checks."""
import json, os, sys

P = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

def load(name):
    with open(os.path.join(P, name)) as f:
        return json.load(f)

# --- Merge feedstocks ---
regions = ["feedstocks_na.json", "feedstocks_eu.json", "feedstocks_asia.json", "feedstocks_row.json",
           "feedstocks_can_sub.json", "feedstocks_ind_sub.json", "feedstocks_chn_sub.json"]
feed = []
ids = set()
dupes = []
for r in regions:
    data = load(r)
    for rec in data:
        rid = rec.get("id")
        if rid in ids:
            dupes.append(rid)
        ids.add(rid)
        feed.append(rec)
    print(f"{r}: {len(data)} records")

print(f"\nTOTAL feedstock records: {len(feed)} | duplicate ids: {dupes or 'none'}")

# --- Validate required fields + collect totals ---
REQ = ["id","name","level","ag_residues_odt_mt","forestry_residues_odt_mt","msw_total_mt",
       "animal_manure_odt_mt","nutrient_status","dominant_feedstock","feedstock_density"]
missing = []
def v(rec, field):
    o = rec.get(field)
    if isinstance(o, dict):
        return o.get("value") or 0
    return 0

countries = [r for r in feed if r.get("level") == "country"]
ag_total = sum(v(r,"ag_residues_odt_mt") for r in countries)
for_total = sum(v(r,"forestry_residues_odt_mt") for r in countries)
msw_total = sum(v(r,"msw_total_mt") for r in countries)

for rec in feed:
    for field in REQ:
        if field not in rec:
            missing.append((rec.get("id"), field))

# --- Sanity vs thesis ---
print(f"\n=== SANITY (country-level sums) ===")
print(f"Ag residues:       {ag_total:,.0f} Mt odt/yr  (≈{ag_total/1000:.2f} Gt)")
print(f"Forestry residues: {for_total:,.0f} Mt odt/yr  (≈{for_total/1000:.2f} Gt)")
print(f"Ag+Forestry:       {(ag_total+for_total)/1000:.2f} Gt odt/yr  [thesis biomass mass ~2.8-4.0 Gt odt]")
print(f"  CDR @90% eff:    {(ag_total+for_total)*0.9*1.47/1000:.2f} Gt CO2/yr  [thesis ~2-5 Gtpa; 1 odt~1.47 tCO2]")
print(f"MSW total:         {msw_total:,.0f} Mt/yr  [World Bank ~2,000 Mt/yr global]")
print(f"\nMissing required fields: {len(missing)}")
for m in missing[:20]:
    print("  ", m)

# --- Validate storage + facilities parse ---
storage = load("storage.json")
facilities = load("facilities.json")
print(f"\nstorage.json: {len(storage)} records "
      f"({sum(1 for s in storage if s.get('kind')=='site')} sites, "
      f"{sum(1 for s in storage if s.get('kind')=='basin')} basins)")
print(f"facilities.json: {len(facilities)} records")

# Write merged feedstocks
with open(os.path.join(P, "feedstocks.json"), "w") as f:
    json.dump(feed, f, separators=(",",":"))
print(f"\nwrote merged feedstocks.json ({len(feed)} records)")
