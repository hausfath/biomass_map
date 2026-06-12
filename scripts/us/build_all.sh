#!/usr/bin/env bash
# Build the US county BiCRS map end-to-end (run from anywhere).
# Raw source files must already be staged under data/geo/us_raw/ (see download_raw.sh).
set -euo pipefail
cd "$(dirname "$0")"

echo "1/6 county geometry ..."        ; python3 build_county_geo.py
echo "2/6 storage-basin polygons ..." ; python3 build_basin_geo.py
echo "3/6 county feedstocks ..."      ; python3 build_county_feedstocks.py
echo "4/6 infrastructure ..."         ; python3 build_us_infrastructure.py
echo "5/6 county recommendations ..." ; python3 build_us_recommendations.py
echo "6/6 bundle ..."                 ; python3 bundle_us.py
echo "done — open src/us.html in a browser."
