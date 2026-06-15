#!/usr/bin/env bash
# Download the raw public source files for the Canada CD map into data/geo/ca_raw/.
# StatCan tables are public CSV bulk downloads; CD geometry is fetched as GeoJSON from the
# StatCan ArcGIS cartographic-boundary service. Re-run to repopulate (files are .gitignored).
set -euo pipefail
cd "$(dirname "$0")/../../data/geo/ca_raw"

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"

echo "Census Division cartographic boundaries (StatCan 2021, GeoJSON WGS84) ..."
curl -sSL --max-time 300 -A "$UA" -o cd_boundary.geojson \
  "https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer/4/query?where=1%3D1&outFields=CDUID,CDNAME,CDTYPE,LANDAREA,PRUID&outSR=4326&returnGeometry=true&maxAllowableOffset=0.004&geometryPrecision=4&f=geojson"

# StatCan bulk CSV tables (Census of Agriculture 2021 + Census of Population 2021).
fetch_table () {  # $1 = 8-digit product id
  echo "StatCan table $1 ..."
  url=$(curl -sSL --max-time 60 "https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/$1/en" \
        | python3 -c "import sys,json;print(json.load(sys.stdin)['object'])")
  curl -sSL --max-time 400 -o "$1.zip" "$url"
  unzip -o "$1.zip" >/dev/null
}

fetch_table 32100309   # Field crops and hay (area), by CD
fetch_table 32100370   # Cattle inventory, by CD
fetch_table 32100372   # Pig inventory, by CD
fetch_table 32100374   # Poultry inventory, by CD
fetch_table 98100002   # Population and dwelling counts, by CD (2021 Census)

echo "done — raw files staged. Now run build_all.sh"
