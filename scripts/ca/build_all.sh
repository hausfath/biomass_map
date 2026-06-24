#!/usr/bin/env bash
# Build the Canada census-division BiCRS map end-to-end (run from anywhere).
# Raw source files must already be staged under data/geo/ca_raw/ (see download_raw.sh).
set -euo pipefail
cd "$(dirname "$0")"

echo "1/7 CD geometry ..."             ; python3 build_cd_geo.py
echo "2/7 storage-basin polygons ..."  ; python3 build_basin_geo.py
echo "3/7 CD feedstocks ..."           ; python3 build_cd_feedstocks.py
echo "4/7 infrastructure ..."          ; python3 build_ca_infrastructure.py
echo "5/7 transport cost + routes (cross-border US+CA) ..." ; python3 build_ca_transport.py
echo "6/7 CD recommendations ..."      ; python3 build_ca_recommendations.py
echo "7/7 bundle ..."                  ; python3 bundle_ca.py
echo "done — open src/index.html (Canada scope) in a browser."
