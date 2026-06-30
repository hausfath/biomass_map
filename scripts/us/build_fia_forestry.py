#!/usr/bin/env python3
"""
FIA-based county forestry-residue allocation weights (to_do item 2, phase 1).

Replaces the within-state woodland-acreage proxy (USDA Census-of-Ag WOODLAND acres) — the
weakest layer in the county feedstock build — with REAL forest data from the USDA Forest
Service Forest Inventory & Analysis (FIA) program, so within-state forestry tracks actual
harvest/standing forest rather than farm-woodland acreage. The DOE Billion-Ton state totals
remain the scaling anchor (this only changes the *within-state county distribution*).

Per county we fetch two FIA EVALIDator estimates (latest evaluation per state):
  - snum 369  Average annual REMOVALS of aboveground biomass of trees (>=1 in), dry short
              tons/yr, on forest land  -> the residue-generation proxy (logging residues are
              the tops/limbs/unmerchantable left behind, proportional to what is harvested).
  - snum 10   Aboveground BIOMASS of live trees (>=1 in), dry short tons, on forest land
              -> standing-forest presence; smooths the noisy, single-plot removals signal and
              keeps forested-but-lightly-harvested counties from dropping to zero.

The county weight is a within-state blend of the two shares: 0.7 * removals-share +
0.3 * standing-share. (Removals are the right residue basis; standing is a robustness floor.)

Reads:  data/geo/us_raw/fia/wc.html (state evaluation-group codes; downloaded if missing)
        + the FIA EVALIDator NJSON API (cached per state under data/geo/us_raw/fia/).
Writes: data/processed/fia_county_forestry.json  ->  {fips: {removals_dst, standing_dst,
        plots, weight}}  (weight = blended within-state share, comparable within a state).

Run before build_county_feedstocks.py. If a state's API calls fail, that state is simply
omitted and build_county_feedstocks falls back to the woodland-acreage proxy for it.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(ROOT, "data", "geo", "us_raw", "fia")
OUT = os.path.join(ROOT, "data", "processed", "fia_county_forestry.json")

API = "https://apps.fs.usda.gov/fiadb-api/fullreport"
WC_URL = API + "/parameters/wc"
SNUM_REMOVALS = 369   # avg annual removals of aboveground biomass, dry short tons/yr, forest land
SNUM_STANDING = 10    # aboveground biomass of live trees, dry short tons, forest land
REMOVALS_W, STANDING_W = 0.7, 0.3
UA = {"User-Agent": "BiCRS-Atlas/1.0 (research; county forestry allocation)"}


def _get(url, dest, binary=False):
    """Fetch url -> dest (cached). Returns the text."""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return open(dest, encoding="utf-8", errors="replace").read()
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read().decode("utf-8", "replace")
            with open(dest, "w", encoding="utf-8") as f:
                f.write(data)
            return data
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                print(f"    ! failed {url}: {e}")
                return ""
            time.sleep(3)
    return ""


def latest_wc_per_state(wc_html):
    """Parse the wc-parameter page -> {statecd: latest wc code (statecd*10000 + year)}."""
    latest = {}
    for b in re.split(r"<th scope=row", wc_html)[1:]:
        tds = re.findall(r"<td[^>]*>([^<]*)</td>", b)
        if len(tds) < 2:
            continue
        try:
            statecd = int(tds[0].strip())
        except ValueError:
            continue
        if not (1 <= statecd <= 56):
            continue
        for x in tds:
            x = x.strip()
            if x.isdigit() and x.isascii() and len(x) >= 5 and int(x) // 10000 == statecd:
                yr = int(x) % 10000
                if 1990 <= yr <= 2026 and (statecd not in latest or int(x) > latest[statecd]):
                    latest[statecd] = int(x)
    return latest


def fetch_estimate(wc, snum, dest):
    """County-level FIA estimate -> {fips: (value, plots)}."""
    q = urllib.parse.urlencode({
        "snum": snum, "rselected": "County code and name",
        "wc": wc, "outputFormat": "NJSON", "estOnly": "Y",
    })
    txt = _get(API + "?" + q, dest)
    out = {}
    if not txt:
        return out
    try:
        ests = json.loads(txt).get("estimates", [])
    except ValueError:
        return out
    for e in ests:
        grp = str(e.get("GRP1", ""))
        m = re.search(r"(\d{5})", grp)          # `06001 6001 CA Alameda -> 06001
        if not m:
            continue
        fips = m.group(1)
        val = e.get("ESTIMATE")
        if val is None:
            continue
        out[fips] = (max(0.0, float(val)), float(e.get("PLOT_COUNT") or 0))
    return out


def main():
    os.makedirs(RAW, exist_ok=True)
    wc_html = _get(WC_URL, os.path.join(RAW, "wc.html"))
    wcs = latest_wc_per_state(wc_html)
    print(f"FIA: {len(wcs)} state evaluation groups")

    per_county = {}   # fips -> {removals_dst, standing_dst, plots}
    for statecd in sorted(wcs):
        wc = wcs[statecd]
        remv = fetch_estimate(wc, SNUM_REMOVALS, os.path.join(RAW, f"remv_{statecd}.json"))
        stand = fetch_estimate(wc, SNUM_STANDING, os.path.join(RAW, f"stand_{statecd}.json"))
        if not remv and not stand:
            print(f"  state {statecd:02d} (wc {wc}): no data — will fall back to woodland proxy")
            continue
        # within-state shares, blended
        srem = sum(v for v, _ in remv.values()) or 0.0
        sstd = sum(v for v, _ in stand.values()) or 0.0
        fips_all = set(remv) | set(stand)
        for fips in fips_all:
            rv, rp = remv.get(fips, (0.0, 0.0))
            sv, _ = stand.get(fips, (0.0, 0.0))
            rshare = (rv / srem) if srem > 0 else 0.0
            sshare = (sv / sstd) if sstd > 0 else 0.0
            weight = REMOVALS_W * rshare + STANDING_W * sshare
            per_county[fips] = {
                "removals_dst": round(rv, 1),
                "standing_dst": round(sv, 1),
                "plots": rp,
                "weight": round(weight, 8),
            }
        print(f"  state {statecd:02d} (wc {wc}): {len(fips_all)} counties, "
              f"removals {srem:,.0f} dst/yr, standing {sstd:,.0f} dst")

    with open(OUT, "w") as f:
        json.dump(per_county, f)
    nzero = sum(1 for v in per_county.values() if v["weight"] <= 0)
    print(f"wrote {len(per_county)} county FIA weights -> {OUT}  ({nzero} zero-weight)")


if __name__ == "__main__":
    main()
