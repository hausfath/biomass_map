#!/usr/bin/env bash
# Download the raw public source files for the EU NUTS-2 map into data/geo/eu_raw/.
# These are large and .gitignored; re-run to repopulate.
set -euo pipefail
cd "$(dirname "$0")/../../data/geo/eu_raw"

echo "Eurostat GISCO NUTS-2 geometry (2021, 20M, WGS84) ..."
curl -sSL -o nuts2.geojson "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2021_4326_LEVL_2.geojson"

echo "JRC ENSPRESO biomass (NUTS-2) ..."
curl -sSL -o ENSPRESO_BIOMASS.xlsx "https://zenodo.org/records/10356004/files/ENSPRESO_BIOMASS.xlsx?download=1"

echo "CO2StoP open-format storage data (KML polygons) ..."
curl -sSL -o co2stop_open.zip "https://setis.ec.europa.eu/document/download/786a884f-0b33-4789-b744-28004b16bd1a_en?filename=co2jrc_openformats.zip"
mkdir -p co2stop && (cd co2stop && unzip -o ../co2stop_open.zip >/dev/null)

echo "Eurostat NUTS-2 population (2023 + 2019 fallback for UK) ..."
for yr in 2023 2019; do
  out="eurostat_pop.json"; [ "$yr" = 2019 ] && out="eurostat_pop_2019.json"
  curl -sSL -o "$out" "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_pjanaggr3?format=JSON&sex=T&age=TOTAL&unit=NR&time=$yr"
done

echo "EEA/EMODnet UWWTD large WWTPs (>=150k PE) ..."
BASE="https://ows.emodnet-humanactivities.eu/geoserver/emodnet/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=emodnet:treatmentplants&outputFormat=application/json&propertyName=uwwname,country,latitude,longitude,loadent_pe,capacit_pe,status"
: > uwwtd_large.ndjson
for off in 0 20000 40000; do
  curl -sSL "$BASE&count=20000&startIndex=$off" -o _uw_page.json
  python3 -c "
import json
d=json.load(open('_uw_page.json')); out=open('uwwtd_large.ndjson','a')
def num(x):
    try: return float(x)
    except: return 0.0
for f in d.get('features',[]):
    p=f['properties']; pe=max(num(p.get('capacit_pe')),num(p.get('loadent_pe')))
    if pe<150000: continue
    if (p.get('status') or '').lower() in ('closed','abandoned'): continue
    if p.get('latitude') is None or p.get('longitude') is None: continue
    out.write(json.dumps({'name':p.get('uwwname'),'country':p.get('country'),'lat':p['latitude'],'lon':p['longitude'],'pe':int(pe)})+chr(10))
"
done
rm -f _uw_page.json
echo "done — raw files staged. Now run build_all.sh"
