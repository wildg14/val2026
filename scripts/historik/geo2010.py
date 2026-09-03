"""geo2010: geografisk jamforbarhet for Goteborgs valdistrikt 2010 mot 2022 (och 2014).

Laser 2010 ars shapefile (SWEREF99 TM), 2014 ars shapefile (SWEREF99 TM) och
2022 ars GeoJSON (SWEREF99 TM), raknar areaoverlapp mellan indelningarna och
skriver CSV, GeoJSON och en sammanfattning (JSON i scratchpad) som underlag
till noteringen docs/historik/noter/geo2010.md.
Alla tal ar berakningar pa geometrierna i kallfilerna; inga valresultat ingar.

Kors med scratchpad/venv/bin/python (behover pyshp, shapely, pyproj).
"""
import csv
import json
import os
from collections import defaultdict

import shapefile
from pyproj import CRS, Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

SCRATCH = "/private/tmp/claude-501/-Users-daniel-code-Temp/f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad"
SHP_2010 = SCRATCH + "/unz/alla_valdistrikt/alla_valdistrikt.shp"                     # falt LKFV, VDNAMN; latin-1; SWEREF99 TM
SHP_2014 = SCRATCH + "/unz/valgeografi_valdistrikt/valgeografi_valdistrikt.shp"       # falt VD, VD_NAMN; latin-1; SWEREF99 TM
GEOJSON_2022 = SCRATCH + "/unz/valgeografi_2022/VD_14_20220910_Val_20220911.json"    # egenskaper Lkfv, Vdnamn; EPSG:3006

PROJEKT = "/Users/daniel/code/Temp"
UT_DATA = PROJEKT + "/data/historik"
UT_OVERLAP_2022 = UT_DATA + "/geo_overlap_2010_2022.csv"
UT_OVERLAP_2014 = UT_DATA + "/geo_overlap_2010_2014.csv"
UT_MAJORNA_2010 = UT_DATA + "/geo_majorna_2010.csv"
UT_CROSSWALK = UT_DATA + "/geo_crosswalk_2010_2022_majorna.csv"
UT_GEOJSON_GBG = UT_DATA + "/distrikt_2010_goteborg.geojson"
UT_GEOJSON_MAJ = UT_DATA + "/distrikt_2010_majornaomradet.geojson"
UT_SAMMANFATTNING = SCRATCH + "/geo2010_sammanfattning.json"   # underlag till noteringen, inte en projektfil

KOMMUN = "1480"
MAJORNA_2022 = ["148005%02d" % i for i in range(26, 49)]   # 14800526-14800548, 23 distrikt
VASTRA_CENTRUM_2022 = ["148005%02d" % i for i in range(1, 49)]

GRANS_INNE = 0.95      # andel_i_majorna >= 0.95 -> inne
GRANS_DELVIS = 0.05    # 0.05 <= andel < 0.95 -> delvis, annars ute
GRANS_MED = 0.001      # ta med distrikt med andel_i_majorna > 0.001
GRANS_IDENTISK = 0.98  # andel >= 0.98 at bada hallen -> identisk
GRANS_SLIVER = 0.02    # bidrag under 2 procent av mottagarens yta raknas som kantjustering vid klassning

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


def las_shapefile(path, kodfalt, namnfalt):
    r = shapefile.Reader(path, encoding="latin-1")
    ut = {}
    ogiltiga = []
    for sr in r.iterShapeRecords():
        rec = sr.record.as_dict()
        kod = str(rec[kodfalt]).strip()
        if not kod.startswith(KOMMUN):
            continue
        g, var_ogiltig = laga(shape(sr.shape.__geo_interface__))
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
        w.writerow(["kod_2010", "namn_2010", "kod_%s" % ar_b, "namn_%s" % ar_b,
                    "overlapp_m2", "andel_av_2010", "andel_av_%s" % ar_b])
        for r in rader:
            w.writerow([r["kod_a"], r["namn_a"], r["kod_b"], r["namn_b"],
                        "%.1f" % r["overlapp_m2"], "%.4f" % r["andel_av_a"], "%.4f" % r["andel_av_b"]])


def klassa_majorna(andel):
    if andel >= GRANS_INNE:
        return "inne"
    if andel >= GRANS_DELVIS:
        return "delvis"
    return "ute"


def klassa_mottagare(bidrag):
    """bidrag: lista av (kod_kalla, andel_av_mottagare, andel_av_kalla) sorterad fallande pa andel_av_mottagare.
    Beskriver hur mottagardistriktet (t ex 2022) ar uppbyggt av kalldistrikt (t ex 2010)."""
    stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
    if len(bidrag) >= 1 and bidrag[0][1] >= GRANS_IDENTISK and bidrag[0][2] >= GRANS_IDENTISK:
        return "identisk"
    if len(stora) == 1 and stora[0][1] >= GRANS_IDENTISK and stora[0][2] < GRANS_IDENTISK:
        return "delning"
    if len(stora) >= 2 and all(b[2] >= GRANS_IDENTISK for b in stora) and sum(b[1] for b in stora) >= GRANS_IDENTISK:
        return "sammanslagning"
    return "omritning"


def klassa_kalla(bidrag):
    """bidrag: lista av (kod_mottagare, andel_av_kalla, andel_av_mottagare) sorterad fallande pa andel_av_kalla.
    Beskriver vad som hande med kalldistriktet (2010) fram till mottagarindelningen."""
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
    prj_2010 = las_prj(SHP_2010)
    prj_2014 = las_prj(SHP_2014)
    print("prj 2010:", prj_2010[:40])
    print("prj 2014:", prj_2014[:40])
    assert "SWEREF99_TM" in prj_2010 and "SWEREF99_TM" in prj_2014
    till_wgs = Transformer.from_crs(CRS_TM, CRS_WGS, always_xy=True)

    # (1) las in och kontrollera
    d2010, og2010 = las_shapefile(SHP_2010, "LKFV", "VDNAMN")
    d2014, og2014 = las_shapefile(SHP_2014, "VD", "VD_NAMN")
    d2022, og2022 = las_geojson_2022(GEOJSON_2022)
    samman["ogiltiga_lagade"] = {"2010": og2010, "2014": og2014, "2022": og2022}
    print("ogiltiga geometrier lagade med buffer(0):", samman["ogiltiga_lagade"])
    samman["area"] = {"2010": area_kontroll("2010", d2010), "2014": area_kontroll("2014", d2014),
                      "2022": area_kontroll("2022", d2022)}
    varningar = []
    for ar, dd in (("2010", d2010), ("2014", d2014), ("2022", d2022)):
        for d in dd.values():
            if d["geom"].is_empty or d["geom"].area < 1000:
                varningar.append([ar, d["kod"], d["namn"], d["geom"].area])
                print("VARNING liten eller tom yta", ar, d["kod"], d["namn"], d["geom"].area)
    samman["varningar_yta"] = varningar
    # inbordes overlapp inom samma ar (ska vara nara noll)
    def intern_overlapp(dd):
        lista = list(dd.values())
        tree = STRtree([d["geom"] for d in lista])
        tot = 0.0
        for i, a in enumerate(lista):
            for j in tree.query(a["geom"]):
                if j <= i:
                    continue
                if a["geom"].intersects(lista[j]["geom"]):
                    tot += a["geom"].intersection(lista[j]["geom"]).area
        return tot
    samman["intern_overlapp_m2"] = {"2010": intern_overlapp(d2010), "2014": intern_overlapp(d2014),
                                    "2022": intern_overlapp(d2022)}
    print("intern overlapp inom samma ar (m2):", samman["intern_overlapp_m2"])
    u2010 = unary_union([d["geom"] for d in d2010.values()])
    u2014 = unary_union([d["geom"] for d in d2014.values()])
    u2022 = unary_union([d["geom"] for d in d2022.values()])
    samman["kommunyta"] = {"2010_km2": u2010.area / 1e6, "2014_km2": u2014.area / 1e6, "2022_km2": u2022.area / 1e6,
                           "snitt_2010_2022_km2": u2010.intersection(u2022).area / 1e6,
                           "snitt_2010_2014_km2": u2010.intersection(u2014).area / 1e6}
    print("kommunyta 2010 %.2f km2, 2014 %.2f km2, 2022 %.2f km2, snitt 2010/2022 %.2f km2" % (
        u2010.area / 1e6, u2014.area / 1e6, u2022.area / 1e6, u2010.intersection(u2022).area / 1e6))

    # (2) overlapp 2010 mot 2022
    ov22 = overlapp(d2010, d2022)
    skriv_overlapp(UT_OVERLAP_2022, ov22, "2022")
    # (5) overlapp 2010 mot 2014
    ov14 = overlapp(d2010, d2014)
    skriv_overlapp(UT_OVERLAP_2014, ov14, "2014")
    samman["antal_par"] = {"2010_2022": len(ov22), "2010_2014": len(ov14)}

    # (3) Majorna-unionen 2022
    saknas = [k for k in MAJORNA_2022 if k not in d2022]
    if saknas:
        raise SystemExit("Majornakoder saknas i 2022: %s" % saknas)
    union = unary_union([d2022[k]["geom"] for k in MAJORNA_2022])
    samman["majorna_union_km2"] = union.area / 1e6
    maj_rader = []
    for d in d2010.values():
        snitt = d["geom"].intersection(union).area
        andel_i = snitt / d["geom"].area
        if andel_i > GRANS_MED:
            maj_rader.append({"kod": d["kod"], "namn": d["namn"], "area_m2": d["geom"].area,
                              "andel_i_majorna": andel_i, "andel_av_majorna": snitt / union.area,
                              "klass": klassa_majorna(andel_i)})
    maj_rader.sort(key=lambda r: -r["andel_av_majorna"])
    with open(UT_MAJORNA_2010, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["kod", "namn", "area_m2", "andel_i_majorna", "andel_av_majorna", "klass"])
        for r in maj_rader:
            w.writerow([r["kod"], r["namn"], "%.1f" % r["area_m2"], "%.4f" % r["andel_i_majorna"],
                        "%.4f" % r["andel_av_majorna"], r["klass"]])
    inne = [r for r in maj_rader if r["klass"] == "inne"]
    delvis = [r for r in maj_rader if r["klass"] == "delvis"]
    inne_union = unary_union([d2010[r["kod"]]["geom"] for r in inne]) if inne else None
    inne_delvis_union = unary_union([d2010[r["kod"]]["geom"] for r in inne + delvis]) if (inne + delvis) else None
    samman["majorna_2010"] = {
        "rader": maj_rader,
        "inne_koder": [r["kod"] for r in inne],
        "delvis_koder": [r["kod"] for r in delvis],
        "ute_koder": [r["kod"] for r in maj_rader if r["klass"] == "ute"],
        "inne_tacker_andel_av_union": (inne_union.intersection(union).area / union.area) if inne_union is not None else 0,
        "inne_yta_km2": (inne_union.area / 1e6) if inne_union is not None else 0,
        "inne_utanfor_union_km2": (inne_union.difference(union).area / 1e6) if inne_union is not None else 0,
        "inne_delvis_tacker_andel_av_union": (inne_delvis_union.intersection(union).area / union.area) if inne_delvis_union is not None else 0,
        "inne_delvis_yta_km2": (inne_delvis_union.area / 1e6) if inne_delvis_union is not None else 0,
        "inne_delvis_utanfor_union_km2": (inne_delvis_union.difference(union).area / 1e6) if inne_delvis_union is not None else 0,
    }
    print("Majorna-unionen 2022: %.3f km2; inne-distrikt 2010: %d, tacker %.4f av unionen; inne+delvis tacker %.4f" % (
        union.area / 1e6, len(inne), samman["majorna_2010"]["inne_tacker_andel_av_union"],
        samman["majorna_2010"]["inne_delvis_tacker_andel_av_union"]))

    # (4) crosswalk per 2022-distrikt i Majorna
    per_2022 = defaultdict(list)
    per_2010 = defaultdict(list)
    for r in ov22:
        per_2022[r["kod_b"]].append((r["kod_a"], r["andel_av_b"], r["andel_av_a"]))
        per_2010[r["kod_a"]].append((r["kod_b"], r["andel_av_a"], r["andel_av_b"]))
    cross = []
    klass_2022 = {}
    with open(UT_CROSSWALK, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["kod_2022", "namn_2022", "klass_2022", "antal_2010", "kod_2010", "namn_2010",
                    "andel_av_2022", "andel_av_2010", "overlapp_m2", "huvudkalla"])
        for kod in MAJORNA_2022:
            bidrag = sorted(per_2022[kod], key=lambda b: -b[1])
            bidrag = [b for b in bidrag if b[1] > GRANS_MED]
            klass = klassa_mottagare(bidrag)
            klass_2022[kod] = klass
            stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
            for b in bidrag:
                ovm2 = b[1] * d2022[kod]["geom"].area
                w.writerow([kod, d2022[kod]["namn"], klass, len(stora), b[0], d2010[b[0]]["namn"],
                            "%.4f" % b[1], "%.4f" % b[2], "%.1f" % ovm2, "ja" if b[1] >= GRANS_SLIVER else "nej"])
            cross.append({"kod_2022": kod, "namn_2022": d2022[kod]["namn"], "klass": klass,
                          "bidrag": [(b[0], d2010[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["crosswalk"] = cross
    samman["klass_2022_antal"] = {k: sum(1 for v in klass_2022.values() if v == k)
                                  for k in ("identisk", "delning", "sammanslagning", "omritning")}
    # klassning av 2010-distrikten i Majornaomradet (inne + delvis) mot 2022
    k2010_22 = []
    for r in maj_rader:
        if r["klass"] == "ute":
            continue
        bidrag = sorted(per_2010[r["kod"]], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        k2010_22.append({"kod": r["kod"], "namn": r["namn"], "klass_majorna": r["klass"],
                         "utfall": klassa_kalla(bidrag),
                         "bidrag": [(b[0], d2022[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["klass_2010_2022"] = k2010_22
    samman["klass_2010_2022_antal"] = {k: sum(1 for v in k2010_22 if v["utfall"] == k)
                                       for k in ("oforandrad", "delad", "sammanslagen", "omritad")}
    # motsvarande 2010 -> 2014 for samma 2010-distrikt
    per_2010_14 = defaultdict(list)
    per_2014 = defaultdict(list)
    for r in ov14:
        per_2010_14[r["kod_a"]].append((r["kod_b"], r["andel_av_a"], r["andel_av_b"]))
        per_2014[r["kod_b"]].append((r["kod_a"], r["andel_av_b"], r["andel_av_a"]))
    k2010_14 = []
    for r in maj_rader:
        if r["klass"] == "ute":
            continue
        bidrag = sorted(per_2010_14[r["kod"]], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        k2010_14.append({"kod": r["kod"], "namn": r["namn"], "klass_majorna": r["klass"], "utfall": klassa_kalla(bidrag),
                         "bidrag": [(b[0], d2014[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["klass_2010_2014"] = k2010_14
    samman["klass_2010_2014_antal"] = {k: sum(1 for v in k2010_14 if v["utfall"] == k)
                                       for k in ("oforandrad", "delad", "sammanslagen", "omritad")}
    # 2014-distrikt som ligger i Majorna-unionen, klassade mot 2010
    maj_2014 = []
    for d in d2014.values():
        snitt = d["geom"].intersection(union).area
        andel_i = snitt / d["geom"].area
        if andel_i > GRANS_MED:
            bidrag = sorted(per_2014[d["kod"]], key=lambda b: -b[1])
            bidrag = [b for b in bidrag if b[1] > GRANS_MED]
            maj_2014.append({"kod": d["kod"], "namn": d["namn"], "andel_i_majorna": andel_i,
                             "klass_majorna": klassa_majorna(andel_i), "klass_mot_2010": klassa_mottagare(bidrag),
                             "bidrag": [(b[0], d2010[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    maj_2014.sort(key=lambda r: r["kod"])
    samman["majorna_2014"] = maj_2014
    # hela Goteborg: hur manga 2010-distrikt ar oforandrade 2014 respektive 2022
    def antal_oforandrade(per):
        n = 0
        koder = []
        for kod in d2010:
            b = sorted(per[kod], key=lambda x: -x[1])
            if b and b[0][1] >= GRANS_IDENTISK and b[0][2] >= GRANS_IDENTISK:
                n += 1
                koder.append(kod)
        return n, koder
    n14, _ = antal_oforandrade(per_2010_14)
    n22, _ = antal_oforandrade(per_2010)
    samman["goteborg_oforandrade_2010"] = {"till_2014": n14, "till_2022": n22}
    # hela Goteborg: klassning av alla 2022-distrikt mot 2010
    gbg_klass_2022 = defaultdict(int)
    for kod in d2022:
        bidrag = sorted(per_2022[kod], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        gbg_klass_2022[klassa_mottagare(bidrag)] += 1
    samman["goteborg_klass_2022_antal"] = dict(gbg_klass_2022)
    # Vastra Centrum 2022 som helhet mot 2010: vilka 2010-distrikt bygger upp kretsen
    vc_union = unary_union([d2022[k]["geom"] for k in VASTRA_CENTRUM_2022 if k in d2022])
    vc_rader = []
    for d in d2010.values():
        snitt = d["geom"].intersection(vc_union).area
        andel_i = snitt / d["geom"].area
        if andel_i > GRANS_MED:
            vc_rader.append([d["kod"], d["namn"], andel_i, snitt / vc_union.area, klassa_majorna(andel_i)])
    vc_rader.sort(key=lambda r: -r[3])
    samman["vastra_centrum_2010"] = {"union_km2": vc_union.area / 1e6, "rader": vc_rader}

    # (6) GeoJSON i WGS84
    n1 = skriv_geojson(UT_GEOJSON_GBG, d2010, till_wgs)
    n2 = skriv_geojson(UT_GEOJSON_MAJ, d2010, till_wgs, koder={r["kod"] for r in maj_rader})
    samman["geojson"] = {"goteborg": n1, "majornaomradet": n2}

    with open(UT_SAMMANFATTNING, "w", encoding="utf-8") as f:
        json.dump(samman, f, ensure_ascii=False, indent=1)
    print("klass 2022 (Majorna):", samman["klass_2022_antal"])
    print("klass 2022 (hela Goteborg):", samman["goteborg_klass_2022_antal"])
    print("klass 2010 -> 2022:", samman["klass_2010_2022_antal"])
    print("klass 2010 -> 2014:", samman["klass_2010_2014_antal"])
    print("oforandrade i Goteborg:", samman["goteborg_oforandrade_2010"])
    print("skrev", UT_OVERLAP_2022, UT_OVERLAP_2014, UT_MAJORNA_2010, UT_CROSSWALK, UT_GEOJSON_GBG, UT_GEOJSON_MAJ)


if __name__ == "__main__":
    main()
