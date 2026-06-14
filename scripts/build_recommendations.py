#!/usr/bin/env python3
"""
Best-Use-of-Biomass Recommendation Engine (global / country + admin-1).

Deterministic encoding of Frontier's BiCRS decision framework
(see data/ENGINE_SPEC.md and PLAN.md sec 4).

Reads:  data/processed/{feedstocks,storage,facilities}.json
Writes: data/processed/recommendations.json   (one record per feedstock region)

The decision logic, pathway constants, scoring, ranking, and rationale text live in
scripts/engine_core.py and are shared with the US county engine so the two never diverge.
This module supplies the *global* inputs — centroid/in-country storage access and
country/state facility matching — then runs the shared engine over every region.

Every output carries a transparent rationale, caveats, and Frontier-exclusion flags.
"""

import json
import os
from collections import Counter

from engine_core import (
    PATHWAYS,
    HAS_SUBNATIONAL,
    NO_OPTION_RATIONALE,
    haversine_km,
    region_country,
    _point_in_geometry,
    decide,
    kpi_score,
    cdr_potential_mtpa,
    build_ranked,
    build_ranked_none,
    build_rationale,
    build_caveats_flags,
)

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")

FEEDSTOCKS_PATH = os.path.join(PROC, "feedstocks.json")
STORAGE_PATH = os.path.join(PROC, "storage.json")
FACILITIES_PATH = os.path.join(PROC, "facilities.json")
SUBNATIONAL_PATH = os.path.join(ROOT, "data", "geo", "subnational.json")
OUT_PATH = os.path.join(PROC, "recommendations.json")


# --------------------------------------------------------------------------
# Step 1 -- storage proximity
# --------------------------------------------------------------------------
_ACCESS_RANK = {"poor": 0, "moderate": 1, "good": 2}


def _in_country_storage_grade(country, storage):
    """
    Storage access implied by qualifying storage located *within the same country*.
    Robust for large countries whose geographic centroid sits far from any basin
    centroid (e.g. the US, whose centroid in Kansas is >500 km from Gulf Coast /
    Illinois basins despite world-class in-country storage).
      good     : in-country high-confidence basin OR operational/construction site
      moderate : in-country medium-confidence basin (capacity_gt >= 1)
      poor     : only low-confidence in-country storage, or none
    Returns (grade, only_low_in_country).
    """
    has_good = False
    has_moderate = False
    has_low = False
    for s in storage:
        if s.get("country") != country:
            continue
        kind = s.get("kind")
        if kind == "site" and s.get("status") in ("operational", "construction"):
            has_good = True
        elif kind == "basin":
            conf = s.get("confidence")
            cap = s.get("capacity_gt") or 0
            if cap < 1:
                continue
            if conf == "high":
                has_good = True
            elif conf == "medium":
                has_moderate = True
            elif conf == "low":
                has_low = True
    if has_good:
        return "good", False
    if has_moderate:
        return "moderate", False
    if has_low:
        return "poor", True
    return "poor", False


def compute_storage_access(centroid, country, storage):
    """
    Returns (storage_access, nearest_storage_km, only_low_conf_nearby).

    Combines two signals and takes the more favourable:
      (1) nearest_storage_km = min haversine distance from region centroid to any
          qualifying site (operational/construction) or high/medium basin (cap>=1):
            good < 500 km, moderate < 1000 km, else poor.
          Forced 'poor' if the only basin within reach is low-confidence.
      (2) in-country qualifying storage grade (handles large-country centroid bias).
    nearest_storage_km is still reported from the centroid signal for the rationale.
    """
    # --- centroid signal ---
    centroid_access = "poor"
    nearest_good = None
    nearest_low = None
    only_low_nearby = False
    if centroid and len(centroid) >= 2 and centroid[0] is not None and centroid[1] is not None:
        lon, lat = centroid[0], centroid[1]
        for s in storage:
            slat, slon = s.get("lat"), s.get("lon")
            if slat is None or slon is None:
                continue
            d = haversine_km(lon, lat, slon, slat)
            kind = s.get("kind")
            if kind == "site":
                if s.get("status") in ("operational", "construction"):
                    if nearest_good is None or d < nearest_good:
                        nearest_good = d
            elif kind == "basin":
                conf = s.get("confidence")
                cap = s.get("capacity_gt") or 0
                if conf in ("high", "medium") and cap >= 1:
                    if nearest_good is None or d < nearest_good:
                        nearest_good = d
                elif conf == "low":
                    if nearest_low is None or d < nearest_low:
                        nearest_low = d
        if nearest_good is not None:
            only_low_nearby = (
                nearest_low is not None and nearest_low < 500 and nearest_good >= 500
            )
            if only_low_nearby:
                centroid_access = "poor"
            elif nearest_good < 500:
                centroid_access = "good"
            elif nearest_good < 1000:
                centroid_access = "moderate"
            else:
                centroid_access = "poor"

    # --- in-country signal ---
    country_access, only_low_in_country = _in_country_storage_grade(country, storage)

    # --- combine: take the better grade ---
    if _ACCESS_RANK[country_access] >= _ACCESS_RANK[centroid_access]:
        access = country_access
    else:
        access = centroid_access

    # only_low flag: only meaningful when the final access is poor
    only_low = (access == "poor") and (only_low_nearby or only_low_in_country)

    nearest_km = round(nearest_good) if nearest_good is not None else (
        round(nearest_low) if nearest_low is not None else None
    )
    return access, nearest_km, only_low


# --------------------------------------------------------------------------
# Step 2 -- retrofit availability (country / US-state facility matching)
# --------------------------------------------------------------------------
def load_subnational():
    """Returns [(id, geometry, country_iso3), ...] for all subnational regions we analyse
    (US states + Canada/India/China provinces); ids match the feedstock ids."""
    with open(SUBNATIONAL_PATH) as f:
        gj = json.load(f)
    return [(feat["properties"]["id"], feat["geometry"], feat["properties"]["country"])
            for feat in gj["features"]]


def annotate_facility_states(facilities, subnational):
    """Tag each facility with the subnational region it sits in (point-in-polygon), restricted
    to regions in the facility's own country so a facility only matches its own country's
    provinces/states."""
    by_country = {}
    for sid, geom, iso in subnational:
        by_country.setdefault(iso, []).append((sid, geom))
    for f in facilities:
        f["_state"] = None
        regions = by_country.get(f.get("country"))
        if not regions:
            continue
        lon, lat = f.get("lon"), f.get("lat")
        if lon is None or lat is None:
            continue
        for sid, geom in regions:
            if _point_in_geometry(lon, lat, geom):
                f["_state"] = sid
                break


def compute_retrofit(region, facilities):
    """
    Match retrofittable EXISTING facilities to the region.
      - US states: facilities physically located in that state (point-in-polygon), so an
        anchor only appears where a facility actually exists -- not a country-wide match.
      - countries: facilities whose `country` == region id.
    Excludes greenfield / developer / aggregation-hub entries (`existing == False`),
    e.g. Arbor (greenfield new-build) and Super6 (CO2 aggregation platform): these are not
    existing facilities one can retrofit.

    Returns (has_retrofit, anchor_name, anchor_type, has_pp_or_bioenergy).
      anchor   = best EXISTING facility in the region (any score), preferring pulp_paper /
                 bioenergy then higher score; None if none -> UI shows "none mapped".
      has_retrofit / has_pp_or_bioenergy are keyed on score in {high, medium} and drive the
      BECCS-pulp&paper branch.
    """
    if region.get("level") == "subnational":
        sid = region.get("id")
        in_region = [f for f in facilities if f.get("_state") == sid]
    else:
        rid = region.get("id")
        in_region = [f for f in facilities if f.get("country") == rid]

    # Only existing physical facilities can be retrofit anchors.
    existing = [f for f in in_region if f.get("existing", True)]

    qualifying = [f for f in existing if f.get("retrofit_score") in ("high", "medium")]
    has_retrofit = len(qualifying) > 0

    # Per-type retrofit availability gates beccs_pp / wte_ccs / ad_ccs. At country/state
    # resolution "within procurement radius" reduces to "a facility of that type exists in the
    # region"; beccs_pp anchors on a pulp&paper mill specifically (bioenergy -> plain BECCS).
    avail = {
        "pp": any(f.get("type") == "pulp_paper" for f in existing),
        "wte": any(f.get("type") == "wte" for f in existing),
        "ad": any(f.get("type") == "biogas_ad" for f in existing),
    }

    anchor_name = None
    anchor_type = None
    if existing:
        score_rank = {"high": 0, "medium": 1, "low": 2}
        # Prefer pulp_paper/bioenergy, then higher retrofit score.
        def keyfn(f):
            pref = 0 if f.get("type") in ("pulp_paper", "bioenergy") else 1
            return (pref, score_rank.get(f.get("retrofit_score"), 3))

        best = sorted(existing, key=keyfn)[0]
        anchor_name = best.get("name")
        anchor_type = best.get("type")

    return has_retrofit, anchor_name, anchor_type, avail


# --------------------------------------------------------------------------
# Main build
# --------------------------------------------------------------------------
def build():
    with open(FEEDSTOCKS_PATH) as f:
        feedstocks = json.load(f)
    with open(STORAGE_PATH) as f:
        storage = json.load(f)
    with open(FACILITIES_PATH) as f:
        facilities = json.load(f)

    # Tag US facilities with the state they sit in, so state anchors match by location.
    annotate_facility_states(facilities, load_subnational())

    records = []
    for region in feedstocks:
        centroid = region.get("centroid")
        country = region_country(region)

        # Step 1
        storage_access, nearest_km, only_low_conf = compute_storage_access(
            centroid, country, storage
        )
        # Step 2
        has_retrofit, anchor_name, anchor_type, avail = compute_retrofit(region, facilities)
        # Step 3
        rec_key, runner_key, eff_dom = decide(region, storage_access, has_retrofit, avail)
        no_option = (rec_key == "none")
        anchor_str = f"{anchor_name} ({anchor_type})" if anchor_name else None
        # The decision may be made on a secondary feedstock (e.g. urban biosolids -> injection);
        # use that effective feedstock for CDR / rationale / ranked options.
        rregion = region if eff_dom == region.get("dominant_feedstock") else dict(region, dominant_feedstock=eff_dom)

        nutrient_alt = False
        if no_option:
            # No good BiCRS pathway (MSW-only region with no WtE and no other significant biomass).
            rec_label, runner_label = "No viable BiCRS pathway", None
            score = eff = cost = None
            cdr = 0.0
            rationale = NO_OPTION_RATIONALE
            ranked = build_ranked_none(region, storage_access, nearest_km, avail, anchor_str)
        else:
            # Excess-nutrient nuance (thesis sec 2.2): where the ecosystem carries surplus
            # nutrients, surface biomass burial as the alternative for dry-biomass removal recs.
            if (region.get("nutrient_status") == "excess"
                    and rec_key in ("beccs", "beccs_pp", "bio_oil", "injection")
                    and runner_key != "burial"):
                runner_key = "burial"
                nutrient_alt = True
            score = kpi_score(rec_key, storage_access)
            eff = PATHWAYS[rec_key]["cdr_efficiency"]
            cost = PATHWAYS[rec_key]["cost_band"]
            cdr = cdr_potential_mtpa(rregion, rec_key)
            rec_label = PATHWAYS[rec_key]["label"]
            runner_label = PATHWAYS[runner_key]["label"]
            rationale = build_rationale(rregion, rec_key, storage_access, nearest_km,
                                        has_retrofit, anchor_name, anchor_type)
            ranked = build_ranked(rregion, rec_key, runner_key, storage_access, nearest_km,
                                  avail, anchor_str)

        caveats, flags = build_caveats_flags(
            region, rec_key, runner_key, only_low_conf, anchor_type, nutrient_alt
        )

        # Country rollups for countries we also map sub-nationally are redundant with their
        # subnational cells; flag them so global sums don't double-count.
        superseded = (region.get("level") == "country"
                      and region.get("id") in HAS_SUBNATIONAL)

        rec = {
            "id": region.get("id"),
            "name": region.get("name"),
            "level": region.get("level"),
            "superseded_by_subnational": superseded,
            "recommended": rec_key,
            "recommended_label": rec_label,
            "runner_up": runner_key,
            "runner_up_label": runner_label,
            "kpi_score": score,
            "cdr_efficiency": eff,
            "cost_band": cost,
            "cdr_potential_mtpa": cdr,
            "storage_access": storage_access,
            "nearest_storage_km": nearest_km,
            "has_retrofit": has_retrofit,
            "no_option": no_option,
            "anchor_facility": anchor_str,
            "rationale": rationale,
            "caveats": caveats,
            "flags": flags,
            "ranked": ranked,
        }
        records.append(rec)

    with open(OUT_PATH, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    return records


def print_summary(records):
    by_path = Counter(r["recommended"] for r in records)
    # Exclude country rollups that are superseded by their own subnational cells.
    total_cdr = sum(r["cdr_potential_mtpa"] or 0
                    for r in records if not r.get("superseded_by_subnational"))

    print(f"\nWrote {len(records)} recommendation records to {OUT_PATH}\n")
    print("Regions per recommended pathway:")
    for key in PATHWAYS:
        if by_path.get(key):
            print(f"  {key:12s} {PATHWAYS[key]['label']:28s} {by_path[key]:4d}")
    if by_path.get("none"):
        print(f"  {'none':12s} {'No viable BiCRS pathway':28s} {by_path['none']:4d}")
    for key, n in by_path.items():
        if key not in PATHWAYS and key != "none":
            print(f"  {key:12s} (UNKNOWN) {n}")

    print(f"\nTotal regions: {sum(by_path.values())}")
    print(f"Global summed CDR potential across recommended pathways: "
          f"{total_cdr:,.1f} Mtpa  (~{total_cdr/1000:.2f} Gtpa)")


if __name__ == "__main__":
    recs = build()
    print_summary(recs)
