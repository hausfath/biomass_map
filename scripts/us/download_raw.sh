#!/usr/bin/env bash
# Download the raw public source files for the US county map into data/geo/us_raw/.
# These are large (~340 MB total) and are .gitignored; re-run to repopulate.
set -euo pipefail
cd "$(dirname "$0")/../../data/geo/us_raw"

echo "Census cartographic boundary counties (20m) ..."
curl -sSL -o cb_county_20m.zip "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_county_20m.zip"
unzip -o cb_county_20m.zip >/dev/null

echo "NATCARB saline storage basin polygons ..."
curl -sSL -o natcarb_saline_poly.zip "https://edx.netl.doe.gov/storage/f/edx/2022/05/2022-05-14T00:30:07.630Z/366fae1f-2ec4-47c9-8130-a391e1383c39/natcarb_saline_poly_shapefile.zip"
mkdir -p natcarb_saline && (cd natcarb_saline && unzip -o ../natcarb_saline_poly.zip >/dev/null)

echo "EPA AgSTAR livestock anaerobic digester database (for AD+CCS gating) ..."
mkdir -p ../ad_raw
curl -sSL -o ../ad_raw/agstar.xlsx "https://www.epa.gov/sites/default/files/2020-10/agstar-livestock-ad-database.xlsx"

echo "USDA Census of Agriculture 2022 (QuickStats bulk) ..."
curl -sSL -o qs.census2022.txt.gz "https://www.nass.usda.gov/datasets/qs.census2022.txt.gz"

echo "Census county population (Vintage 2023) ..."
curl -sSL -o co-est2023.csv "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/counties/totals/co-est2023-alldata.csv"

echo "EPA GHGRP 2023 data summary spreadsheets ..."
curl -sSL -o ghgrp_2023.zip "https://www.epa.gov/system/files/other-files/2024-10/2023_data_summary_spreadsheets.zip"
mkdir -p ghgrp && (cd ghgrp && unzip -o ../ghgrp_2023.zip >/dev/null)

echo "EPA LMOP Landfill & Project Database (for LFG+CCS / LFG-RNG+CCS gating) ..."
mkdir -p lmop
curl -sSL -o lmop/lmopcompositedata.xlsx "https://www.epa.gov/system/files/documents/2024-09/lmopcompositedata.xlsx"

echo "EPA FRS Major POTWs (wastewater) via ArcGIS ..."
BASE="https://geodata.epa.gov/arcgis/rest/services/OEI/FRS_Wastewater/MapServer/0/query"
WHERE="CWP_MAJOR_MINOR_STATUS%3D%27Major%27%20AND%20CWP_FACILITY_TYPE_INDICATOR%3D%27POTW%27"
: > wwtp_major.ndjson
for off in 0 2000 4000; do
  curl -sSL "$BASE?where=$WHERE&outFields=CWP_NAME,CWP_STATE,FAC_LAT,FAC_LONG&returnGeometry=false&resultOffset=$off&resultRecordCount=2000&f=json" \
    | python3 -c "import sys,json;[print(json.dumps(ft['attributes'])) for ft in json.load(sys.stdin).get('features',[])]" >> wwtp_major.ndjson
done

echo "NTAD intermodal rail TOFC/COFC terminals (transport model) ..."
mkdir -p transport_raw
RAILSVC="https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_Intermodal_Freight_Facilities_Rail_TOFC_COFC/FeatureServer/0/query"
curl -sSL --max-time 90 "$RAILSVC?where=1%3D1&outFields=TERMINAL,CITY,STATE,RAIL_CO,LAT,LON&returnGeometry=false&f=json" \
  -o transport_raw/ntad_rail_tofc.json

echo "done — raw files staged. Now run build_all.sh"
echo "NOTE: build_fia_forestry.py (USFS FIA county forest data) and build_fuels_residues.py"
echo "      (USFS FACTS hazardous-fuel treatments) self-download + cache their inputs under"
echo "      data/geo/us_raw/{fia,facts}/ on first run — no staging needed here."
echo "NOTE: the transport model also needs the 'searoute' Python package:"
echo "      python3 -m pip install --break-system-packages searoute"
