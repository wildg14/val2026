# -*- coding: utf-8 -*-
"""
val2018_majorna_geo.py - vilka valdistrikt 2018 ligger i Majornaomradet?

Jamfor 2018 ars distriktspolygoner (Valmyndighetens shapefil, SWEREF99 TM)
med unionen av 2022 ars 23 Majornadistrikt (14800526-14800548, Valmyndighetens
GeoJSON for Vastra Gotaland, EPSG:3006) och skriver ut andelen av varje
Goteborgsdistrikts yta som ligger i 2022 ars Majornaomrade.

Kors med:
  <venv>/bin/python scripts/historik/val2018_majorna_geo.py
"""
import json
import sys

import shapefile
from shapely.geometry import shape
from shapely.ops import unary_union

SCRATCH = ("/private/tmp/claude-501/-Users-daniel-code-Temp/"
           "f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad/unz")
SHP_2018 = SCRATCH + "/2018_valgeografi_valdistrikt/alla_valdistrikt"
GEOJSON_2022 = SCRATCH + "/valgeografi_2022/VD_14_20220910_Val_20220911.json"
MAJORNA_2022 = {f"148005{n:02d}" for n in range(26, 49)}
GRANS = 0.01  # rapportera distrikt med mer an 1 procent av ytan i omradet


def main():
    r = shapefile.Reader(SHP_2018, encoding="utf-8")
    d18 = {}
    for sr in r.iterShapeRecords():
        if str(sr.record["VD"]).startswith("1480"):
            d18[sr.record["VD"]] = (sr.record["VD_NAMN"], shape(sr.shape.__geo_interface__))
    g = json.load(open(GEOJSON_2022, encoding="utf-8"))
    maj = [shape(f["geometry"]) for f in g["features"] if str(f["properties"]["Lkfv"]) in MAJORNA_2022]
    if len(maj) != 23:
        print("fel: hittade", len(maj), "Majornadistrikt 2022")
        return 1
    u22 = unary_union(maj)
    print(f"Goteborgsdistrikt 2018: {len(d18)}, Majornaomradet 2022: {u22.area / 1e6:.4f} km2")
    inne = []
    print("kod;namn;andel_av_ytan_i_majorna_2022;yta_ha")
    for vd, (namn, geom) in sorted(d18.items()):
        andel = geom.intersection(u22).area / geom.area if geom.area else 0
        if andel > GRANS:
            print(f"{vd};{namn};{andel:.3f};{geom.area / 1e4:.1f}")
            if andel > 0.5:
                inne.append(vd)
    yta = sum(d18[vd][1].area for vd in inne) / 1e6
    print(f"{len(inne)} distrikt med mer an halva ytan i omradet, sammanlagd yta {yta:.4f} km2")
    print("koder:", " ".join(inne))
    return 0


if __name__ == "__main__":
    sys.exit(main())
