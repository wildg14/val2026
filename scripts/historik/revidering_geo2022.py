"""revidering: bygger de tva filer for 2022 som saknades i data/historik/ och som
docs/historik/valdistrikt-historik.md, tabellen "Definitionen jamforbart Majorna per ar",
hanvisar till med monstret geo_majorna_<ar>.csv for ovriga fyra ar.

Kallan ar exakt samma GeoJSON som geo2006.py, geo2010.py, geo2014.py och geo2018.py redan
anvander for 2022-sidan (Vastra Gotalands lan, egenskaper Lkfv/Vdnamn, SWEREF99 TM utan
crs-medlem i filen). Ingen ny kalla laggs till. Eftersom Majorna-unionen 2022 per definition
AR unionen av de 23 distrikten 14800526-14800548 ligger alla 23 till exakt 100 procent i den
och inget annat Goteborgsdistrikt overlappar den alls (indelningen ar en ren partition).

Skriver:
- data/historik/distrikt_2022_goteborg.geojson: alla Goteborgsdistrikt 2022 i WGS84,
  samma format som distrikt_2018_goteborg.geojson med flera.
- data/historik/geo_majorna_2022.csv: samma kolumner som geo_majorna_2018.csv med flera
  (kod;namn;area_m2;andel_i_majorna;andel_av_majorna;klass), en rad per Majornadistrikt.

Kors med scratchpad/venv/bin/python (behover pyshp for att lasa .prj-kontrollen i ett
grannskript men anvander bara json/shapely/pyproj har).
"""
import csv
import json

from pyproj import CRS, Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform, unary_union

SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"
GEOJSON_2022 = SCRATCH + "/unz/valgeografi_2022/VD_14_20220910_Val_20220911.json"

PROJEKT = "/Users/daniel/code/Temp"
UT_DATA = PROJEKT + "/data/historik"
UT_GEOJSON_GBG = UT_DATA + "/distrikt_2022_goteborg.geojson"
UT_MAJORNA_2022 = UT_DATA + "/geo_majorna_2022.csv"

KOMMUN = "1480"
MAJORNA_2022 = ["148005%02d" % i for i in range(26, 49)]  # 14800526-14800548, 23 distrikt

CRS_TM = CRS.from_epsg(3006)
CRS_WGS = CRS.from_epsg(4326)


def laga(geom):
    if geom.is_valid:
        return geom, False
    return geom.buffer(0), True


def las_geojson_2022(path):
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)
    ut = {}
    ogiltiga = []
    for ft in gj["features"]:
        kod = str(ft["properties"]["Lkfv"]).strip()
        if not kod.startswith(KOMMUN):
            continue
        g, var_ogiltig = laga(shape(ft["geometry"]))
        if var_ogiltig:
            ogiltiga.append(kod)
        if kod in ut:
            raise SystemExit("dubblettkod %s i %s" % (kod, path))
        ut[kod] = {"kod": kod, "namn": str(ft["properties"]["Vdnamn"]).strip(), "geom": g}
    return ut, ogiltiga, len(gj["features"])


def runda_koordinater(geom, dec=6):
    def f(x, y, z=None):
        return (round(x, dec), round(y, dec))
    return transform(f, geom)


def main():
    d2022, ogiltiga, n_lan = las_geojson_2022(GEOJSON_2022)
    print("poster i kallan (Vastra Gotalands lan):", n_lan, "Goteborgsdistrikt:", len(d2022))
    print("ogiltiga geometrier lagade med buffer(0):", ogiltiga)

    saknas = [k for k in MAJORNA_2022 if k not in d2022]
    if saknas:
        raise SystemExit("Majornakoder saknas i 2022: %s" % saknas)
    union = unary_union([d2022[k]["geom"] for k in MAJORNA_2022])
    print("Majorna-unionen 2022: %.4f km2 (%d distrikt)" % (union.area / 1e6, len(MAJORNA_2022)))

    # Kontroll: overlappar nagot annat Goteborgsdistrikt unionen? Ska vara noll, eftersom
    # unionen bestar av hela distrikt ur samma partition.
    utanfor_overlapp = 0.0
    for kod, d in d2022.items():
        if kod in MAJORNA_2022:
            continue
        snitt = d["geom"].intersection(union).area
        if snitt > 0:
            utanfor_overlapp += snitt
    print("overlapp mellan unionen och distrikt utanfor Majorna: %.4f m2 (ska vara ~0)" % utanfor_overlapp)

    rows = []
    for kod in MAJORNA_2022:
        d = d2022[kod]
        area = d["geom"].area
        rows.append({"kod": kod, "namn": d["namn"], "area_m2": area,
                     "andel_i_majorna": 1.0, "andel_av_majorna": area / union.area,
                     "klass": "inne"})
    rows.sort(key=lambda r: -r["andel_av_majorna"])
    with open(UT_MAJORNA_2022, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod", "namn", "area_m2", "andel_i_majorna", "andel_av_majorna", "klass"])
        for r in rows:
            w.writerow([r["kod"], r["namn"], "%.1f" % r["area_m2"], "%.4f" % r["andel_i_majorna"],
                        "%.4f" % r["andel_av_majorna"], r["klass"]])
    print("skrev", UT_MAJORNA_2022, "(%d rader)" % len(rows))

    till_wgs = Transformer.from_crs(CRS_TM, CRS_WGS, always_xy=True)
    features = []
    for kod in sorted(d2022):
        d = d2022[kod]
        g = runda_koordinater(transform(till_wgs.transform, d["geom"]))
        features.append({"type": "Feature", "properties": {"kod": d["kod"], "namn": d["namn"]},
                         "geometry": mapping(g)})
    with open(UT_GEOJSON_GBG, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False, separators=(",", ":"))
    print("skrev", UT_GEOJSON_GBG, "(%d features)" % len(features))


if __name__ == "__main__":
    main()
