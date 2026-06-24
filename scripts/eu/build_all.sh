#!/usr/bin/env bash
# Build the EU NUTS-2 BiCRS map end-to-end (run from anywhere).
# Raw source files must already be staged under data/geo/eu_raw/ (see download_raw.sh).
set -euo pipefail
cd "$(dirname "$0")"

echo "1/6 NUTS-2 geometry ..."       ; python3 build_nuts_geo.py
echo "2/6 storage formations ..."    ; python3 build_storage_geo.py
echo "3/6 NUTS-2 feedstocks ..."     ; python3 build_nuts_feedstocks.py
echo "4/6 infrastructure ..."        ; python3 build_eu_infrastructure.py
echo "5/6 transport cost + routes ."; python3 build_eu_transport.py
echo "6/6 recommendations + bundle ."; python3 build_eu_recommendations.py && python3 bundle_eu.py
echo "done — open src/index.html (Europe scope) in a browser."
