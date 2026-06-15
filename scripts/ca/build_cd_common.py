#!/usr/bin/env python3
"""Shared helpers for the Canada CD pipeline: province mapping + geometry simplification.

CD-level StatCan tables identify geography by DGUID. Census-division DGUIDs have the form
``2021A0003{CDUID}`` (the 4-digit CDUID is the trailing portion); province DGUIDs are
``2021A0002{PRUID}``. CDUID encodes the province in its first two digits (== PRUID).
"""

# PRUID (StatCan province/territory code) -> 2-letter code and full name (matches the
# global tool's feedstocks_can_sub.json province records, keyed by full name).
PRUID_TO_ABBR = {
    "10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON",
    "46": "MB", "47": "SK", "48": "AB", "59": "BC", "60": "YT", "61": "NT", "62": "NU",
}
PRUID_TO_NAME = {
    "10": "Newfoundland and Labrador", "11": "Prince Edward Island", "12": "Nova Scotia",
    "13": "New Brunswick", "24": "Quebec", "35": "Ontario", "46": "Manitoba",
    "47": "Saskatchewan", "48": "Alberta", "59": "British Columbia",
    "60": "Yukon", "61": "Northwest Territories", "62": "Nunavut",
}
ABBR_TO_NAME = {PRUID_TO_ABBR[k]: PRUID_TO_NAME[k] for k in PRUID_TO_ABBR}

CD_DGUID_PREFIX = "2021A0003"   # census-division DGUID prefix; CDUID follows


def cduid_from_dguid(dguid):
    """Return the 4-digit CDUID if `dguid` is a census-division DGUID, else None."""
    dguid = (dguid or "").strip()
    if dguid.startswith(CD_DGUID_PREFIX) and len(dguid) >= len(CD_DGUID_PREFIX) + 4:
        return dguid[len(CD_DGUID_PREFIX):len(CD_DGUID_PREFIX) + 4]
    return None


# --- Douglas-Peucker simplification (degree space), shared by geometry builders ---
def _perp_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def dp(points, tol):
    """Douglas-Peucker simplification of an open polyline."""
    if len(points) < 3:
        return points
    dmax, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        d = _perp_dist(points[i], points[0], points[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        left = dp(points[:idx + 1], tol)
        right = dp(points[idx:], tol)
        return left[:-1] + right
    return [points[0], points[-1]]


def simplify_ring(ring, tol, dp_round):
    """DP-simplify + round + dedupe a closed ring; keep it closed (>=4 pts) or []."""
    if len(ring) > 4:
        ring = dp(ring, tol)
    out, last = [], None
    for x, y in ring:
        pt = [round(x, dp_round), round(y, dp_round)]
        if pt != last:
            out.append(pt)
        last = pt
    if len(out) < 4:
        return []
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def ring_area_centroid(ring):
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
        n = len(ring) - 1 or 1
        return 0.0, [sum(p[0] for p in ring[:-1]) / n, sum(p[1] for p in ring[:-1]) / n]
    return a, [cx / (6 * a), cy / (6 * a)]
