#!/usr/bin/env bash
# Build the US county BiCRS map end-to-end (run from anywhere).
# Raw source files must already be staged under data/geo/us_raw/ (see download_raw.sh).
set -euo pipefail
cd "$(dirname "$0")"

echo "1/9 county geometry ..."        ; python3 build_county_geo.py
echo "2/9 storage-basin polygons ..." ; python3 build_basin_geo.py
echo "3/9 FIA county forestry weights ..." ; python3 build_fia_forestry.py
echo "4/9 county feedstocks ..."      ; python3 build_county_feedstocks.py
echo "5/9 infrastructure (incl. LMOP landfills) ..." ; python3 build_us_infrastructure.py
echo "6/9 transport nodes (NTAD rail + ports + rivers) ..." ; python3 build_transport_nodes.py
echo "7/9 transport cost + routes ..." ; python3 build_us_transport.py
echo "8/9 county recommendations ..." ; python3 build_us_recommendations.py
echo "9/9 bundle ..."                 ; python3 bundle_us.py
echo "done — open src/index.html (US scope) in a browser."
