"""geo2006: geografisk jamforbarhet for Goteborgs valdistrikt 2006 mot 2022 (och 2010).

Laser 2006 ars shapefile (RT90 2,5 gon V), 2010 ars shapefile (SWEREF99 TM) och
2022 ars GeoJSON (SWEREF99 TM), raknar areaoverlapp mellan indelningarna och
skriver CSV, GeoJSON och en sammanfattning som skriptet skriver ut i terminalen.
Alla tal ar berakningar pa geometrierna i kallfilerna; inga valresultat ingar.

Kors med scratchpad/venv/bin/python (behover pyshp, shapely, pyproj).
"""
import csv
import json
import math
import os
from collections import defaultdict

import shapefile
from pyproj import CRS, Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"
SHP_2006 = SCRATCH + "/unz/riksdagen_i_valdistrikt/riksdagen_i_valdistrikt.shp"   # falt Lkfv, NAMN; latin-1; RT90 2,5 gon V
SHP_2010 = SCRATCH + "/unz/alla_valdistrikt/alla_valdistrikt.shp"                 # falt LKFV, VDNAMN; latin-1; SWEREF99 TM
GEOJSON_2022 = SCRATCH + "/unz/valgeografi_2022/VD_14_20220910_Val_20220911.json"  # egenskaper Lkfv, Vdnamn; EPSG:3006

PROJEKT = "/Users/daniel/code/Temp"
UT_DATA = PROJEKT + "/data/historik"
UT_OVERLAP_2022 = UT_DATA + "/geo_overlap_2006_2022.csv"
UT_OVERLAP_2010 = UT_DATA + "/geo_overlap_2006_2010.csv"
UT_MAJORNA_2006 = UT_DATA + "/geo_majorna_2006.csv"
UT_CROSSWALK = UT_DATA + "/geo_crosswalk_2006_2022_majorna.csv"
UT_GEOJSON_GBG = UT_DATA + "/distrikt_2006_goteborg.geojson"
UT_GEOJSON_MAJ = UT_DATA + "/distrikt_2006_majornaomradet.geojson"
UT_SAMMANFATTNING = SCRATCH + "/geo2006_sammanfattning.json"   # underlag till noteringen, inte en projektfil

KOMMUN = "1480"
MAJORNA_2022 = ["148005%02d" % i for i in range(26, 49)]   # 14800526-14800548, 23 distrikt
VASTRA_CENTRUM_2022 = ["148005%02d" % i for i in range(1, 49)]

GRANS_INNE = 0.95      # andel_i_majorna >= 0.95 -> inne
GRANS_DELVIS = 0.05    # 0.05 <= andel < 0.95 -> delvis, annars ute
GRANS_MED = 0.001      # ta med distrikt med andel_i_majorna > 0.001
GRANS_IDENTISK = 0.98  # andel >= 0.98 at bada hallen -> identisk
GRANS_SLIVER = 0.02    # bidrag under 2 procent av 2022-ytan raknas som kantjustering vid klassning

CRS_2006 = CRS.from_epsg(3021)   # RT90 2,5 gon V
CRS_TM = CRS.from_epsg(3006)     # SWEREF99 TM
CRS_WGS = CRS.from_epsg(4326)


def las_prj(path):
    with open(os.path.splitext(path)[0] + ".prj", encoding="ascii", errors="replace") as f:
        return f.read().strip()


def laga(geom):
    """buffer(0) pa ogiltig geometri, returnerar (geometri, var_ogiltig)."""
    if geom.is_valid:
        return geom, False
    return geom.buffer(0), True


def las_shapefile(path, kodfalt, namnfalt, transformer=None):
    r = shapefile.Reader(path, encoding="latin-1")
    ut = {}
    ogiltiga = []
    for sr in r.iterShapeRecords():
        rec = sr.record.as_dict()
        kod = str(rec[kodfalt]).strip()
        if not kod.startswith(KOMMUN):
            continue
        g = shape(sr.shape.__geo_interface__)
        if transformer is not None:
            g = transform(transformer.transform, g)
        g, var_ogiltig = laga(g)
        if var_ogiltig:
            ogiltiga.append(kod)
        if kod in ut:
            raise SystemExit("dubblettkod %s i %s" % (kod, path))
        ut[kod] = {"kod": kod, "namn": str(rec[namnfalt]).strip(), "geom": g}
    return ut, ogiltiga


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
    return ut, ogiltiga


def area_kontroll(namn, distrikt):
    areor = sorted((d["geom"].area, d["kod"], d["namn"]) for d in distrikt.values())
    tot = sum(a for a, _, _ in areor)
    minst = areor[0]
    storst = areor[-1]
    print("%s: %d distrikt, total yta %.1f km2, minsta %s %s %.3f km2, storsta %s %s %.2f km2" % (
        namn, len(distrikt), tot / 1e6, minst[1], minst[2], minst[0] / 1e6, storst[1], storst[2], storst[0] / 1e6))
    return {"antal": len(distrikt), "total_km2": tot / 1e6,
            "minsta": [minst[1], minst[2], minst[0]], "storsta": [storst[1], storst[2], storst[0]]}


def overlapp(a_distrikt, b_distrikt):
    """Alla par (a, b) med positiv snittarea. Returnerar lista av dict."""
    b_lista = list(b_distrikt.values())
    tree = STRtree([d["geom"] for d in b_lista])
    rader = []
    for a in a_distrikt.values():
        for idx in tree.query(a["geom"]):
            b = b_lista[idx]
            if not a["geom"].intersects(b["geom"]):
                continue
            snitt = a["geom"].intersection(b["geom"]).area
            if snitt <= 0:
                continue
            rader.append({
                "kod_a": a["kod"], "namn_a": a["namn"], "kod_b": b["kod"], "namn_b": b["namn"],
                "overlapp_m2": snitt,
                "andel_av_a": snitt / a["geom"].area,
                "andel_av_b": snitt / b["geom"].area,
            })
    rader.sort(key=lambda r: (r["kod_a"], -r["overlapp_m2"]))
    return rader


def skriv_overlapp(path, rader, ar_b):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["kod_2006", "namn_2006", "kod_%s" % ar_b, "namn_%s" % ar_b,
                    "overlapp_m2", "andel_av_2006", "andel_av_%s" % ar_b])
        for r in rader:
            w.writerow([r["kod_a"], r["namn_a"], r["kod_b"], r["namn_b"],
                        "%.1f" % r["overlapp_m2"], "%.4f" % r["andel_av_a"], "%.4f" % r["andel_av_b"]])


def klassa_2006(andel):
    if andel >= GRANS_INNE:
        return "inne"
    if andel >= GRANS_DELVIS:
        return "delvis"
    return "ute"


def klassa_2022(bidrag):
    """bidrag: lista av (kod_2006, andel_av_2022, andel_av_2006) sorterad fallande pa andel_av_2022."""
    stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
    tackt = sum(b[1] for b in bidrag)
    if len(bidrag) >= 1 and bidrag[0][1] >= GRANS_IDENTISK and bidrag[0][2] >= GRANS_IDENTISK:
        return "identisk"
    if len(stora) == 1 and stora[0][1] >= GRANS_IDENTISK and stora[0][2] < GRANS_IDENTISK:
        return "delning"
    if len(stora) >= 2 and all(b[2] >= GRANS_IDENTISK for b in stora) and sum(b[1] for b in stora) >= GRANS_IDENTISK:
        return "sammanslagning"
    return "omritning"


def klassa_2006_mot_2022(bidrag):
    """bidrag: lista av (kod_2022, andel_av_2006, andel_av_2022) sorterad fallande pa andel_av_2006.
    Beskriver vad som hande med 2006-distriktet till 2022."""
    stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
    if bidrag and bidrag[0][1] >= GRANS_IDENTISK and bidrag[0][2] >= GRANS_IDENTISK:
        return "oforandrad"
    if len(stora) == 1 and stora[0][1] >= GRANS_IDENTISK and stora[0][2] < GRANS_IDENTISK:
        return "sammanslagen"
    if len(stora) >= 2 and all(b[2] >= GRANS_IDENTISK for b in stora) and sum(b[1] for b in stora) >= GRANS_IDENTISK:
        return "delad"
    return "omritad"


def runda_koordinater(geom, dec=6):
    def f(x, y, z=None):
        return (round(x, dec), round(y, dec))
    return transform(f, geom)


def skriv_geojson(path, distrikt, till_wgs, koder=None):
    features = []
    for kod in sorted(distrikt):
        if koder is not None and kod not in koder:
            continue
        d = distrikt[kod]
        g = runda_koordinater(transform(till_wgs.transform, d["geom"]))
        features.append({"type": "Feature", "properties": {"kod": d["kod"], "namn": d["namn"]},
                         "geometry": mapping(g)})
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False, separators=(",", ":"))
    return len(features)


def main():
    samman = {}
    prj_2006 = las_prj(SHP_2006)
    prj_2010 = las_prj(SHP_2010)
    print("prj 2006:", prj_2006[:60])
    print("prj 2010:", prj_2010[:40])
    assert "RT90_25_gon_W" in prj_2006 and "1500000" in prj_2006 and "15.808277" in prj_2006
    assert "SWEREF99_TM" in prj_2010
    tr_2006 = Transformer.from_crs(CRS_2006, CRS_TM, always_xy=True)
    samman["transformation_2006"] = tr_2006.description
    print("transformation 2006 -> 3006:", tr_2006.description)
    till_wgs = Transformer.from_crs(CRS_TM, CRS_WGS, always_xy=True)

    d2006, og2006 = las_shapefile(SHP_2006, "Lkfv", "NAMN", tr_2006)
    d2010, og2010 = las_shapefile(SHP_2010, "LKFV", "VDNAMN", None)
    d2022, og2022 = las_geojson_2022(GEOJSON_2022)
    samman["ogiltiga_lagade"] = {"2006": og2006, "2010": og2010, "2022": og2022}
    print("ogiltiga geometrier lagade med buffer(0):", samman["ogiltiga_lagade"])
    samman["area"] = {"2006": area_kontroll("2006", d2006), "2010": area_kontroll("2010", d2010),
                      "2022": area_kontroll("2022", d2022)}
    for ar, dd in (("2006", d2006), ("2010", d2010), ("2022", d2022)):
        for d in dd.values():
            if d["geom"].is_empty or d["geom"].area < 1000:
                print("VARNING liten eller tom yta", ar, d["kod"], d["namn"], d["geom"].area)
    # kontroll av lagesnoggrannhet: hur stor del av 2006-ytan hamnar inom unionen av 2022
    u2022 = unary_union([d["geom"] for d in d2022.values()])
    u2006 = unary_union([d["geom"] for d in d2006.values()])
    samman["kommunyta"] = {"2006_km2": u2006.area / 1e6, "2022_km2": u2022.area / 1e6,
                           "snitt_km2": u2006.intersection(u2022).area / 1e6}
    print("kommunyta 2006 %.2f km2, 2022 %.2f km2, snitt %.2f km2" % (
        u2006.area / 1e6, u2022.area / 1e6, u2006.intersection(u2022).area / 1e6))

    # (2) overlapp 2006 mot 2022
    ov22 = overlapp(d2006, d2022)
    skriv_overlapp(UT_OVERLAP_2022, ov22, "2022")
    # (5) overlapp 2006 mot 2010
    ov10 = overlapp(d2006, d2010)
    skriv_overlapp(UT_OVERLAP_2010, ov10, "2010")
    samman["antal_par"] = {"2006_2022": len(ov22), "2006_2010": len(ov10)}

    # (3) Majorna-unionen 2022
    saknas = [k for k in MAJORNA_2022 if k not in d2022]
    if saknas:
        raise SystemExit("Majornakoder saknas i 2022: %s" % saknas)
    union = unary_union([d2022[k]["geom"] for k in MAJORNA_2022])
    samman["majorna_union_km2"] = union.area / 1e6
    maj_rader = []
    for d in d2006.values():
        snitt = d["geom"].intersection(union).area
        andel_i = snitt / d["geom"].area
        if andel_i > GRANS_MED:
            maj_rader.append({"kod": d["kod"], "namn": d["namn"], "area_m2": d["geom"].area,
                              "andel_i_majorna": andel_i, "andel_av_majorna": snitt / union.area,
                              "klass": klassa_2006(andel_i)})
    maj_rader.sort(key=lambda r: -r["andel_av_majorna"])
    with open(UT_MAJORNA_2006, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["kod", "namn", "area_m2", "andel_i_majorna", "andel_av_majorna", "klass"])
        for r in maj_rader:
            w.writerow([r["kod"], r["namn"], "%.1f" % r["area_m2"], "%.4f" % r["andel_i_majorna"],
                        "%.4f" % r["andel_av_majorna"], r["klass"]])
    inne = [r for r in maj_rader if r["klass"] == "inne"]
    delvis = [r for r in maj_rader if r["klass"] == "delvis"]
    inne_union = unary_union([d2006[r["kod"]]["geom"] for r in inne]) if inne else None
    samman["majorna_2006"] = {
        "rader": maj_rader,
        "inne_koder": [r["kod"] for r in inne],
        "delvis_koder": [r["kod"] for r in delvis],
        "ute_koder": [r["kod"] for r in maj_rader if r["klass"] == "ute"],
        "inne_tacker_andel_av_union": (inne_union.intersection(union).area / union.area) if inne_union is not None else 0,
        "inne_yta_km2": (inne_union.area / 1e6) if inne_union is not None else 0,
        "inne_utanfor_union_km2": (inne_union.difference(union).area / 1e6) if inne_union is not None else 0,
    }
    print("Majorna-unionen 2022: %.3f km2; inne-distrikt 2006: %d, tacker %.4f av unionen" % (
        union.area / 1e6, len(inne), samman["majorna_2006"]["inne_tacker_andel_av_union"]))

    # (4) crosswalk per 2022-distrikt i Majorna
    per_2022 = defaultdict(list)
    per_2006 = defaultdict(list)
    for r in ov22:
        per_2022[r["kod_b"]].append((r["kod_a"], r["andel_av_b"], r["andel_av_a"]))
        per_2006[r["kod_a"]].append((r["kod_b"], r["andel_av_a"], r["andel_av_b"]))
    cross = []
    klass_2022 = {}
    with open(UT_CROSSWALK, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["kod_2022", "namn_2022", "klass_2022", "antal_2006", "kod_2006", "namn_2006",
                    "andel_av_2022", "andel_av_2006", "overlapp_m2", "huvudkalla"])
        for kod in MAJORNA_2022:
            bidrag = sorted(per_2022[kod], key=lambda b: -b[1])
            bidrag = [b for b in bidrag if b[1] > GRANS_MED]
            klass = klassa_2022(bidrag)
            klass_2022[kod] = klass
            stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
            for i, b in enumerate(bidrag):
                ovm2 = b[1] * d2022[kod]["geom"].area
                w.writerow([kod, d2022[kod]["namn"], klass, len(stora), b[0], d2006[b[0]]["namn"],
                            "%.4f" % b[1], "%.4f" % b[2], "%.1f" % ovm2, "ja" if b[1] >= GRANS_SLIVER else "nej"])
            cross.append({"kod_2022": kod, "namn_2022": d2022[kod]["namn"], "klass": klass,
                          "bidrag": [(b[0], d2006[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["crosswalk"] = cross
    samman["klass_2022_antal"] = {k: sum(1 for v in klass_2022.values() if v == k)
                                  for k in ("identisk", "delning", "sammanslagning", "omritning")}
    # klassning av 2006-distrikten i Majornaomradet (inne + delvis) mot 2022
    k2006 = []
    for r in maj_rader:
        if r["klass"] == "ute":
            continue
        bidrag = sorted(per_2006[r["kod"]], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        k2006.append({"kod": r["kod"], "namn": r["namn"], "klass_2006": r["klass"],
                      "utfall": klassa_2006_mot_2022(bidrag),
                      "bidrag": [(b[0], d2022[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["klass_2006"] = k2006
    samman["klass_2006_antal"] = {k: sum(1 for v in k2006 if v["utfall"] == k)
                                  for k in ("oforandrad", "delad", "sammanslagen", "omritad")}
    # motsvarande 2006 -> 2010 for samma 2006-distrikt
    per_2006_10 = defaultdict(list)
    for r in ov10:
        per_2006_10[r["kod_a"]].append((r["kod_b"], r["andel_av_a"], r["andel_av_b"]))
    k2010 = []
    for r in maj_rader:
        if r["klass"] == "ute":
            continue
        bidrag = sorted(per_2006_10[r["kod"]], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        k2010.append({"kod": r["kod"], "namn": r["namn"], "utfall": klassa_2006_mot_2022(bidrag),
                      "bidrag": [(b[0], d2010[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["klass_2006_2010"] = k2010
    samman["klass_2006_2010_antal"] = {k: sum(1 for v in k2010 if v["utfall"] == k)
                                       for k in ("oforandrad", "delad", "sammanslagen", "omritad")}
    # hela Goteborg: hur manga 2006-distrikt ar oforandrade 2010 respektive 2022
    def antal_oforandrade(per):
        n = 0
        for kod in d2006:
            b = sorted(per[kod], key=lambda x: -x[1])
            if b and b[0][1] >= GRANS_IDENTISK and b[0][2] >= GRANS_IDENTISK:
                n += 1
        return n
    samman["goteborg_oforandrade_2006"] = {"till_2010": antal_oforandrade(per_2006_10),
                                           "till_2022": antal_oforandrade(per_2006)}

    # (6) GeoJSON i WGS84
    n1 = skriv_geojson(UT_GEOJSON_GBG, d2006, till_wgs)
    n2 = skriv_geojson(UT_GEOJSON_MAJ, d2006, till_wgs, koder={r["kod"] for r in maj_rader})
    samman["geojson"] = {"goteborg": n1, "majornaomradet": n2}

    with open(UT_SAMMANFATTNING, "w", encoding="utf-8") as f:
        json.dump(samman, f, ensure_ascii=False, indent=1)
    print("klass 2022:", samman["klass_2022_antal"])
    print("klass 2006 -> 2022:", samman["klass_2006_antal"])
    print("klass 2006 -> 2010:", samman["klass_2006_2010_antal"])
    print("oforandrade i Goteborg:", samman["goteborg_oforandrade_2006"])
    print("skrev", UT_OVERLAP_2022, UT_OVERLAP_2010, UT_MAJORNA_2006, UT_CROSSWALK, UT_GEOJSON_GBG, UT_GEOJSON_MAJ)


if __name__ == "__main__":
    main()
