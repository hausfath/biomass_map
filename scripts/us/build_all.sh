#!/usr/bin/env bash
# Build the US county BiCRS map end-to-end (run from anywhere).
# Raw source files must already be staged under data/geo/us_raw/ (see download_raw.sh).
set -euo pipefail
cd "$(dirname "$0")"

echo "1/10 county geometry ..."        ; python3 build_county_geo.py
echo "2/10 storage-basin polygons ..." ; python3 build_basin_geo.py
echo "3/10 FIA county forestry weights ..." ; python3 build_fia_forestry.py
echo "4/10 wildfire-fuels-treatment residue (USFS FACTS) ..." ; python3 build_fuels_residues.py
echo "5/10 county feedstocks ..."      ; python3 build_county_feedstocks.py
echo "6/10 infrastructure (incl. LMOP landfills) ..." ; python3 build_us_infrastructure.py
echo "7/10 transport nodes (NTAD rail + ports + rivers) ..." ; python3 build_transport_nodes.py
echo "8/10 transport cost + routes ..." ; python3 build_us_transport.py
echo "9/10 county recommendations ..." ; python3 build_us_recommendations.py
echo "10/10 bundle ..."                ; python3 bundle_us.py
echo "done — open src/index.html (US scope) in a browser."
