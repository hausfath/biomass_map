#!/usr/bin/env python3
"""
Portugal wildfire-fuel-management residue (Europe scope). MODELLED, not observed.

Portugal is the only European country with a national annual fuel-management series (AGIF / SGIFR
annual activity reports). There is no regional breakdown and no measured biomass, so this is a
screening estimate (docs/wildfire_research/scoping_europe.md):

  treated area   AGIF reported fuel management, mainland Portugal, 2019-2024 (ha):
                 65,693 / 70,387 / 88,058 / 77,867 / 85,365 / 75,559  -> mean 77,155 ha/yr
                 (AGIF SGIFR Relatorio de Atividades 2024, Fig. 26; 2023 restated). Figures exclude
                 "a maioria das entidades privadas ... e autarquias", so they UNDERCOUNT the
                 mandatory private / municipal strips (sensitivity, not modelled).
  removable      x 0.92: drops grazing (5%) and controlled fire (3%) of the 2024 treatment mix
                 (AGIF 2024 Fig. 28), which leave no removable biomass.
  yield          central 2.3 t DM/ha collected (harvester-baler on Cistus shrubland, central Spain;
                 Bados et al. 2020, Croat. J. For. Eng. 41(2), doi 10.5552/crojfe.2020.688);
                 high 6.7 t/ha (standing shrub load 5 yr after fire, N Portugal; Enes et al. 2020,
                 Life 10(4):33) as an upper bound; low 0.6 x central. Do NOT port the US 13 odt/ac.
  allocation     mainland NUTS-2 (PT11 Norte, PT15 Algarve, PT16 Centro, PT17 AML, PT18 Alentejo)
                 by woodland + shrubland area, Eurostat LUCAS lan_lcv_ovw (C00 + D00, km2; 2022
                 where published, else 2018), queried 2026-10-19. A neutral vegetated-area proxy;
                 it likely over-weights Alentejo (montado, lower fire activity) and under-weights
                 Norte/Centro.

Writes data/processed/fuels_residues_eu.json -> {nuts_id: {"value","low","high"} Mt DM/yr}.
Consumed by build_nuts_feedstocks.py (folded into forestry, tagged separately).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "data", "processed", "fuels_residues_eu.json")

AGIF_HA = {2019: 65693, 2020: 70387, 2021: 88058, 2022: 77867, 2023: 85365, 2024: 75559}
REMOVABLE_SHARE = 0.92
YIELD_T_DM_HA = {"central": 2.3, "high": 6.7}
LOW_FACTOR = 0.6
# Eurostat lan_lcv_ovw, km2: (woodland C00, shrubland D00, year)
VEG_KM2 = {
    "PT11": (5676, 5379, 2022),
    "PT15": (1098, 1860, 2022),
    "PT16": (11843, 5547, 2018),
    "PT17": (846, 362, 2018),
    "PT18": (14182, 2616, 2018),
}


def main():
    ha = sum(AGIF_HA.values()) / len(AGIF_HA) * REMOVABLE_SHARE
    tot_c = ha * YIELD_T_DM_HA["central"] / 1e6
    tot_h = ha * YIELD_T_DM_HA["high"] / 1e6
    w = {k: c + d for k, (c, d, _) in VEG_KM2.items()}
    wsum = sum(w.values())
    out = {}
    for k, v in w.items():
        f = v / wsum
        out[k] = {"value": round(tot_c * f, 5), "low": round(tot_c * f * LOW_FACTOR, 5),
                  "high": round(tot_h * f, 5)}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"PT fuel management: {ha:,.0f} removable ha/yr -> {tot_c:.3f} Mt DM/yr "
          f"(low {tot_c * LOW_FACTOR:.3f}, high {tot_h:.3f})")
    for k, v in out.items():
        print(f"  {k}: {v['value']:.4f} Mt DM/yr")


if __name__ == "__main__":
    main()
