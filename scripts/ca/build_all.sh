#!/usr/bin/env bash
# Build the Canada census-division BiCRS map end-to-end (run from anywhere).
# Raw source files must already be staged under data/geo/ca_raw/ (see download_raw.sh).
set -euo pipefail
cd "$(dirname "$0")"

echo "1/6 CD geometry ..."             ; python3 build_cd_geo.py
echo "2/6 storage-basin polygons ..."  ; python3 build_basin_geo.py
echo "3/6 CD feedstocks ..."           ; python3 build_cd_feedstocks.py
echo "4/6 infrastructure ..."          ; python3 build_ca_infrastructure.py
echo "5/6 CD recommendations ..."      ; python3 build_ca_recommendations.py
echo "6/6 bundle ..."                  ; python3 bundle_ca.py
echo "done — open src/index.html (Canada scope) in a browser."
