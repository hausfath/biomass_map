#!/usr/bin/env python3
"""
One-off: lower the agricultural-residue sustainable-removal cap from 40% -> 30% (to_do item 3).

The cap is not a live constant — it is embedded in the stored ag-residue values, applied
heterogeneously when each region was compiled. Audit (2026-06) showed:
  - The dominant methodology (NA, Asia, India states, China provinces, most of ROW, and the
    EU García-Condado records) computed recoverable = gross x RPR x ~40% — these carry a literal
    "40%" in their source string and ARE rescaled here by 30/40 = 0.75.
  - Records that used a PUBLISHED net/technical recoverable potential (EU S2BIOM, Australia
    Crawford, Ethiopia/Egypt/Ghana/Nigeria/Turkey studies, Ukraine "accessible") never applied a
    40% gross cap — no literal "40%" — and are LEFT UNCHANGED.
  - Canadian provinces were already compiled at 30% — no literal "40%" — and are LEFT UNCHANGED.

A literal "40%" (percent sign) is a reliable marker: residue-to-product ratios and bagasse
fractions are written as decimals (0.25, 1.3), never as percentages, so there is no false match.
Ranges like "40-75%" do not contain the substring "40%" and so are not matched.

Rescales ag_residues_odt_mt value/low/high by 0.75 and rewrites the source text 40%->30% for
matched records, in the source feedstock files. Re-run merge_validate.py and the scope builders
afterwards. Use --apply to write; default is a dry run.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")

SOURCE_FILES = [
    "feedstocks_na.json", "feedstocks_eu.json", "feedstocks_asia.json", "feedstocks_row.json",
    "feedstocks_can_sub.json", "feedstocks_ind_sub.json", "feedstocks_chn_sub.json",
]
FACTOR = 0.30 / 0.40   # 0.75

PCT40 = re.compile(r"40\s?%")          # literal "40%" / "40 %"
# Records that used the same ~40% Billion-Ton recoverable methodology but whose source text states
# the result ("16 Mt gross -> 6.4 Mt recoverable" = 40%) rather than a literal "40%". Curated from
# the audit so a major ag state isn't left inconsistent with its neighbours. (file, name).
INCLUDE = {("feedstocks_na.json", "Illinois")}
# rewrite "40%" -> "30%" and the few spelled-out variants, preserving surrounding text
SUB_PATTERNS = [
    (re.compile(r"40(\s?)%"), r"30\1%"),
    (re.compile(r"~40\b"), "~30"),
    (re.compile(r"40 percent", re.I), "30 percent"),
]


def is_capped(src):
    return bool(PCT40.search(src or ""))


def rewrite_src(src):
    out = src
    for pat, repl in SUB_PATTERNS:
        out = pat.sub(repl, out)
    return out


def agval(rec):
    a = rec.get("ag_residues_odt_mt")
    return a.get("value", 0.0) if isinstance(a, dict) else 0.0


def main(apply):
    total_before = total_after = 0.0
    n_rescaled = n_left = 0
    moved = []
    left_big = []
    files = {}

    for fn in SOURCE_FILES:
        path = os.path.join(PROC, fn)
        data = json.load(open(path))
        for rec in data:
            a = rec.get("ag_residues_odt_mt")
            if not isinstance(a, dict):
                continue
            v = a.get("value", 0.0) or 0.0
            total_before += v
            src = str(a.get("source", ""))
            if is_capped(src) or (fn, rec.get("name")) in INCLUDE:
                n_rescaled += 1
                new_v = round(v * FACTOR, 4)
                moved.append((fn, rec.get("name"), v, new_v))
                if apply:
                    for k in ("value", "low", "high"):
                        if isinstance(a.get(k), (int, float)):
                            a[k] = round(a[k] * FACTOR, 4)
                    new_src = rewrite_src(src)
                    if new_src == src:   # no literal "40%" to swap (INCLUDE case) -> annotate
                        new_src = src.rstrip(". ") + "; recoverable cap lowered to ~30% (2026)"
                    a["source"] = new_src
                total_after += new_v
            else:
                n_left += 1
                total_after += v
                if v >= 15:
                    left_big.append((fn, rec.get("name"), v, src[:70]))
        files[fn] = data

    print(f"{'APPLY' if apply else 'DRY RUN'} — ag-residue cap 40% -> 30% (x{FACTOR:.3f})\n")
    print(f"records rescaled: {n_rescaled} | left unchanged: {n_left}")
    print(f"global ag total (all records): {total_before:,.1f} -> {total_after:,.1f} Mt odt "
          f"({100*(total_after/total_before-1):+.1f}%)\n")

    print("Largest rescaled (top 12):")
    for fn, name, v, nv in sorted(moved, key=lambda x: -x[2])[:12]:
        print(f"  {name:18s} {v:7.1f} -> {nv:7.1f}   ({fn})")

    print("\nLEFT UNCHANGED but >=15 Mt (verify these are genuinely published-net / already-30%):")
    for fn, name, v, src in sorted(left_big, key=lambda x: -x[2]):
        print(f"  {name:16s} {v:6.1f}  [{fn.replace('feedstocks_','').replace('.json','')}] {src}")

    if apply:
        for fn, data in files.items():
            with open(os.path.join(PROC, fn), "w") as f:
                json.dump(data, f, ensure_ascii=False)
        print(f"\nWROTE {len(files)} files. Now run: merge_validate.py, then the scope builders + bundles.")
    else:
        print("\n(dry run — no files written; pass --apply to write)")


if __name__ == "__main__":
    main("--apply" in sys.argv)
