#!/usr/bin/env python3
"""
Roads to Removal (R2R) wildfire-fuel-treatment biomass POTENTIAL by US county.

Source: county-level forestry data from the LLNL-led "Roads to Removal: Options for Carbon Dioxide
Removal in the United States" (Pett-Ridge et al., Dec 2023), shared by the R2R team (personal
communication, Oct 2026; see docs/wildfire_research/roads_to_removal.md). Raw workbook (not in git):
data/geo/us_raw/r2r/Roads to Removal Forestry Data.xlsx.

R2R scenario (workbook notes): 70 M acres of priority wildfire-hazard areas (40 M USFS + 30 M other
ownership) thinned once over 10 years (~7 M ac/yr), removing trees < 12 in diameter and tops, to 80%
of full stocking; reserved land excluded. Biomass is split into six accessibility classes (distance
to road x slope), each with an acquisition cost ($/short BDT; R2R, built on Pan et al. 2007 and
Petitmermet et al. 2019). The workbook's "BDT/10 years" columns (short bone-dry tons per year) are
used; short -> metric x 0.9072 (as the workbook does). This is a TECHNICAL POTENTIAL for a
needed-treatment scale-up, NOT current supply: it is shown as its own map layer and is NOT added to
the forestry total or used by the recommendation engine. Workbook notes: it ignores re-treatment at
3-10 yr intervals (conservative) and assumes a first thinning to 80% stocking.

Writes data/processed/fuels_r2r_us.json -> {fips: {"value": Mt dry/yr, "acres_yr", "usfs_share",
"cost_usd_bdt" (BDT-weighted acquisition cost), "classes": [Mt dry/yr per accessibility class]}}.
"""
import json
import os
import re

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
XLSX = os.path.join(ROOT, "data", "geo", "us_raw", "r2r", "Roads to Removal Forestry Data.xlsx")
OUT = os.path.join(ROOT, "data", "processed", "fuels_r2r_us.json")
SHORT_TO_METRIC = 0.9072

# Accessibility classes: (first column = USFS Acre, annual "BDT/10 years" column, $/short BDT).
# Costs from the R2R team (personal communication), matching the workbook's per-class totals.
CLASSES = [
    ("<500 ft from road, 0-20% slope", 2, 7, 77.80),
    ("500-1,000 ft, 0-20%", 8, 13, 81.98),
    ("1,000 ft-0.5 mi, 0-20%", 14, 19, 99.85),
    ("<500 ft, 20-40%", 21, 26, 98.52),
    ("500-1,000 ft, 20-40%", 27, 32, 102.70),
    ("1,000 ft-0.5 mi, 20-40%", 33, 38, 120.57),
]
# Workbook per-class annual totals (short BDT/yr), for a reproduction check.
CLASS_TOTALS = [24334182.6, 13652321.9, 23909273.1, 22460307.1, 13077805.7, 23928559.4]


def main():
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    rows = list(wb.worksheets[0].iter_rows(values_only=True))
    out = {}
    cls_sum = [0.0] * len(CLASSES)
    for r in rows:
        lab = r[1] if len(r) > 1 else None
        if not isinstance(lab, str) or not re.match(r"^\d{5} ", lab):
            continue
        fips = lab[:5]
        ann = [float(r[c_ann] or 0) for _, _, c_ann, _ in CLASSES]
        usfs_ac = sum(float(r[c] or 0) for _, c, _, _ in CLASSES)
        oth_ac = sum(float(r[c + 1] or 0) for _, c, _, _ in CLASSES)
        tot = sum(ann)
        for i, a in enumerate(ann):
            cls_sum[i] += a
        if tot <= 0:
            continue
        out[fips] = {
            "value": round(tot * SHORT_TO_METRIC / 1e6, 5),
            "acres_yr": round((usfs_ac + oth_ac) / 10),
            "usfs_share": round(usfs_ac / (usfs_ac + oth_ac), 3) if usfs_ac + oth_ac else None,
            "cost_usd_bdt": round(sum(a * c[3] for a, c in zip(ann, CLASSES)) / tot, 2),
            "classes": [round(a * SHORT_TO_METRIC / 1e6, 5) for a in ann],
        }
    # reproduce the workbook's per-class totals (and hence the R2R cost table)
    for (name, *_), got, ref in zip(CLASSES, cls_sum, CLASS_TOTALS):
        assert abs(got - ref) < 1.0, (name, got, ref)
    with open(OUT, "w") as f:
        json.dump(out, f)
    tot = sum(v["value"] for v in out.values())
    print(f"R2R: {len(out)} counties, {tot:.1f} Mt dry/yr potential "
          f"({sum(cls_sum) / 1e6:.1f} M short BDT/yr; per-class totals reproduce the workbook)")


if __name__ == "__main__":
    main()
