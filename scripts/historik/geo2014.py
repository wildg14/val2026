"""geo2014: geografisk jamforbarhet for Goteborgs valdistrikt 2014 mot 2022 (och 2018).

Laser 2014 ars shapefile (SWEREF99 TM), 2018 ars shapefile (SWEREF99 TM) och 2022 ars
GeoJSON (SWEREF99 TM), raknar areaoverlapp mellan indelningarna, jamfor 2014-2018 med
Valmyndighetens officiella mappning och skriver CSV, GeoJSON och ett sammanfattnings-
underlag (JSON i scratchpad) till noteringen docs/historik/noter/geo2014.md.
Alla tal ar berakningar pa geometrierna i kallfilerna eller lasta ur skv-filerna;
inga valresultat ingar.

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

SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"
SHP_2014 = SCRATCH + "/unz/valgeografi_valdistrikt/valgeografi_valdistrikt.shp"        # falt VD, VD_NAMN; dbf latin-1; EPSG:3006
SHP_2018 = SCRATCH + "/unz/2018_valgeografi_valdistrikt/alla_valdistrikt.shp"          # falt VD, VD_NAMN; dbf utf-8; EPSG:3006
GEOJSON_2022 = SCRATCH + "/unz/valgeografi_2022/VD_14_20220910_Val_20220911.json"      # egenskaper Lkfv, Vdnamn; EPSG:3006
SKV_MAPPNING = SCRATCH + "/unz/mappning_2014_2018/vd-mappning-2014-2018.skv"           # kod 2014;kod 2018;procent (latin-1, CRLF)
SKV_INDELNING = SCRATCH + "/unz/mappning_2014_2018/vd-indelning-2018.skv"              # kod 2018;O/M/S/N

PROJEKT = "/Users/daniel/code/Temp"
UT_DATA = PROJEKT + "/data/historik"
UT_OVERLAP_2022 = UT_DATA + "/geo_overlap_2014_2022.csv"
UT_OVERLAP_2018 = UT_DATA + "/geo_overlap_2014_2018.csv"
UT_MAJORNA_2014 = UT_DATA + "/geo_majorna_2014.csv"
UT_CROSSWALK = UT_DATA + "/geo_crosswalk_2014_2022_majorna.csv"
UT_MAPPNING_JMF = UT_DATA + "/geo_mappning_2014_2018_jamforelse.csv"
UT_INDELNING_JMF = UT_DATA + "/geo_indelning_2018_jamforelse.csv"
UT_GEOJSON_GBG = UT_DATA + "/distrikt_2014_goteborg.geojson"
UT_GEOJSON_MAJ = UT_DATA + "/distrikt_2014_majornaomradet.geojson"
UT_SAMMANFATTNING = SCRATCH + "/geo2014_sammanfattning.json"   # underlag till noteringen, inte en projektfil

KOMMUN = "1480"
MAJORNA_2022 = ["148005%02d" % i for i in range(26, 49)]   # 14800526-14800548, 23 distrikt
VASTRA_CENTRUM_2022 = ["148005%02d" % i for i in range(1, 49)]

GRANS_INNE = 0.95      # andel_i_majorna >= 0.95 -> inne
GRANS_DELVIS = 0.05    # 0.05 <= andel < 0.95 -> delvis, annars ute
GRANS_MED = 0.001      # ta med distrikt med andel_i_majorna > 0.001
GRANS_IDENTISK = 0.98  # andel >= 0.98 at bada hallen -> identisk
GRANS_SLIVER = 0.02    # bidrag under 2 procent av mottagarens yta raknas som kantjustering vid klassning
GRANS_MAPPNING = 0.01  # geometriskt par under 1 procent av 2014-ytan raknas inte som ett par vid jamforelse med skv

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


def las_shapefile(path, kodfalt, namnfalt, encoding):
    r = shapefile.Reader(path, encoding=encoding)
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


def las_skv_mappning(path):
    """Returnerar dict kod_2014 -> lista av (kod_2018, procent) for Goteborg."""
    ut = defaultdict(list)
    with open(path, encoding="latin-1") as f:
        for rad in f:
            rad = rad.strip()
            if not rad or rad.startswith("#"):
                continue
            k14, k18, pct = rad.split(";")
            if not k14.startswith(KOMMUN) and not k18.startswith(KOMMUN):
                continue
            ut[k14].append((k18, float(pct)))
    return ut


def las_skv_indelning(path):
    ut = {}
    with open(path, encoding="latin-1") as f:
        for rad in f:
            rad = rad.strip()
            if not rad or rad.startswith("#"):
                continue
            kod, ind = rad.split(";")
            if kod.startswith(KOMMUN):
                ut[kod] = ind
    return ut


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
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod_2014", "namn_2014", "kod_%s" % ar_b, "namn_%s" % ar_b,
                    "overlapp_m2", "andel_av_2014", "andel_av_%s" % ar_b])
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
    """Klassar ett mottagardistrikt (t ex 2022) utifran sina givare (t ex 2014).
    bidrag: lista av (kod_givare, andel_av_mottagare, andel_av_givare) sorterad fallande pa andel_av_mottagare."""
    stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
    if bidrag and bidrag[0][1] >= GRANS_IDENTISK and bidrag[0][2] >= GRANS_IDENTISK:
        return "identisk"
    if len(stora) == 1 and stora[0][1] >= GRANS_IDENTISK and stora[0][2] < GRANS_IDENTISK:
        return "delning"
    if len(stora) >= 2 and all(b[2] >= GRANS_IDENTISK for b in stora) and sum(b[1] for b in stora) >= GRANS_IDENTISK:
        return "sammanslagning"
    return "omritning"


def klassa_givare(bidrag):
    """Beskriver vad som hande med ett givardistrikt (t ex 2014) till en senare indelning.
    bidrag: lista av (kod_mottagare, andel_av_givare, andel_av_mottagare) sorterad fallande pa andel_av_givare."""
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
    prj_2014 = las_prj(SHP_2014)
    prj_2018 = las_prj(SHP_2018)
    print("prj 2014:", prj_2014[:40])
    print("prj 2018:", prj_2018[:40])
    assert "SWEREF99_TM" in prj_2014 and "SWEREF99_TM" in prj_2018
    till_wgs = Transformer.from_crs(CRS_TM, CRS_WGS, always_xy=True)

    d2014, og2014 = las_shapefile(SHP_2014, "VD", "VD_NAMN", "latin-1")
    d2018, og2018 = las_shapefile(SHP_2018, "VD", "VD_NAMN", "utf-8")
    d2022, og2022 = las_geojson_2022(GEOJSON_2022)
    samman["ogiltiga_lagade"] = {"2014": og2014, "2018": og2018, "2022": og2022}
    print("ogiltiga geometrier lagade med buffer(0):", samman["ogiltiga_lagade"])
    samman["area"] = {"2014": area_kontroll("2014", d2014), "2018": area_kontroll("2018", d2018),
                      "2022": area_kontroll("2022", d2022)}
    sma = []
    for ar, dd in (("2014", d2014), ("2018", d2018), ("2022", d2022)):
        for d in dd.values():
            if d["geom"].is_empty or d["geom"].area < 1000:
                print("VARNING liten eller tom yta", ar, d["kod"], d["namn"], d["geom"].area)
                sma.append([ar, d["kod"], d["namn"], d["geom"].area])
    samman["sma_ytor"] = sma
    # kommunyta och lagesoverensstammelse
    u2014 = unary_union([d["geom"] for d in d2014.values()])
    u2018 = unary_union([d["geom"] for d in d2018.values()])
    u2022 = unary_union([d["geom"] for d in d2022.values()])
    samman["kommunyta"] = {"2014_km2": u2014.area / 1e6, "2018_km2": u2018.area / 1e6, "2022_km2": u2022.area / 1e6,
                           "snitt_2014_2022_km2": u2014.intersection(u2022).area / 1e6,
                           "snitt_2014_2018_km2": u2014.intersection(u2018).area / 1e6}
    print("kommunyta 2014 %.2f, 2018 %.2f, 2022 %.2f km2; snitt 14/22 %.2f, snitt 14/18 %.2f" % (
        u2014.area / 1e6, u2018.area / 1e6, u2022.area / 1e6,
        samman["kommunyta"]["snitt_2014_2022_km2"], samman["kommunyta"]["snitt_2014_2018_km2"]))
    # overlapp inom samma indelning (ska vara noll om distrikten inte overlappar varandra)
    for ar, dd in (("2014", d2014), ("2018", d2018), ("2022", d2022)):
        summa = sum(d["geom"].area for d in dd.values())
        samman["kommunyta"]["intern_overlapp_%s_km2" % ar] = (summa - unary_union([d["geom"] for d in dd.values()]).area) / 1e6

    # (2) overlapp 2014 mot 2022
    ov22 = overlapp(d2014, d2022)
    skriv_overlapp(UT_OVERLAP_2022, ov22, "2022")
    # (5) overlapp 2014 mot 2018
    ov18 = overlapp(d2014, d2018)
    skriv_overlapp(UT_OVERLAP_2018, ov18, "2018")
    samman["antal_par"] = {"2014_2022": len(ov22), "2014_2018": len(ov18)}

    # (3) Majorna-unionen 2022
    saknas = [k for k in MAJORNA_2022 if k not in d2022]
    if saknas:
        raise SystemExit("Majornakoder saknas i 2022: %s" % saknas)
    union = unary_union([d2022[k]["geom"] for k in MAJORNA_2022])
    samman["majorna_union_km2"] = union.area / 1e6
    maj_rader = []
    for d in d2014.values():
        snitt = d["geom"].intersection(union).area
        andel_i = snitt / d["geom"].area
        if andel_i > GRANS_MED:
            maj_rader.append({"kod": d["kod"], "namn": d["namn"], "area_m2": d["geom"].area,
                              "andel_i_majorna": andel_i, "andel_av_majorna": snitt / union.area,
                              "klass": klassa_majorna(andel_i)})
    maj_rader.sort(key=lambda r: -r["andel_av_majorna"])
    with open(UT_MAJORNA_2014, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod", "namn", "area_m2", "andel_i_majorna", "andel_av_majorna", "klass"])
        for r in maj_rader:
            w.writerow([r["kod"], r["namn"], "%.1f" % r["area_m2"], "%.4f" % r["andel_i_majorna"],
                        "%.4f" % r["andel_av_majorna"], r["klass"]])
    inne = [r for r in maj_rader if r["klass"] == "inne"]
    delvis = [r for r in maj_rader if r["klass"] == "delvis"]
    inne_union = unary_union([d2014[r["kod"]]["geom"] for r in inne]) if inne else None
    samman["majorna_2014"] = {
        "rader": maj_rader,
        "inne_koder": [r["kod"] for r in inne],
        "delvis_koder": [r["kod"] for r in delvis],
        "ute_koder": [r["kod"] for r in maj_rader if r["klass"] == "ute"],
        "inne_tacker_andel_av_union": (inne_union.intersection(union).area / union.area) if inne_union is not None else 0,
        "inne_yta_km2": (inne_union.area / 1e6) if inne_union is not None else 0,
        "inne_utanfor_union_km2": (inne_union.difference(union).area / 1e6) if inne_union is not None else 0,
        "union_utanfor_inne_km2": (union.difference(inne_union).area / 1e6) if inne_union is not None else union.area / 1e6,
    }
    # vilka 2022-distrikt ligger i den del av unionen som inne-distrikten inte tacker
    rest = union.difference(inne_union) if inne_union is not None else union
    rest_per_2022 = []
    for k in MAJORNA_2022:
        a = d2022[k]["geom"].intersection(rest).area
        if a > 100:
            rest_per_2022.append([k, d2022[k]["namn"], a, a / d2022[k]["geom"].area])
    rest_per_2022.sort(key=lambda x: -x[2])
    samman["majorna_2014"]["rest_per_2022"] = rest_per_2022
    # vilka 2022-distrikt (utanfor Majorna) far inne-distriktens yta utanfor unionen
    utanfor = inne_union.difference(union) if inne_union is not None else None
    utanfor_per_2022 = []
    if utanfor is not None and utanfor.area > 0:
        for d in d2022.values():
            a = d["geom"].intersection(utanfor).area
            if a > 100:
                utanfor_per_2022.append([d["kod"], d["namn"], a])
    utanfor_per_2022.sort(key=lambda x: -x[2])
    samman["majorna_2014"]["inne_utanfor_per_2022"] = utanfor_per_2022
    print("Majorna-unionen 2022: %.3f km2; inne-distrikt 2014: %d, tacker %.4f av unionen" % (
        union.area / 1e6, len(inne), samman["majorna_2014"]["inne_tacker_andel_av_union"]))

    # (4) crosswalk per 2022-distrikt i Majorna
    per_2022 = defaultdict(list)
    per_2014_22 = defaultdict(list)
    for r in ov22:
        per_2022[r["kod_b"]].append((r["kod_a"], r["andel_av_b"], r["andel_av_a"]))
        per_2014_22[r["kod_a"]].append((r["kod_b"], r["andel_av_a"], r["andel_av_b"]))
    cross = []
    klass_2022 = {}
    with open(UT_CROSSWALK, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod_2022", "namn_2022", "klass_2022", "antal_2014", "kod_2014", "namn_2014",
                    "andel_av_2022", "andel_av_2014", "overlapp_m2", "huvudkalla"])
        for kod in MAJORNA_2022:
            bidrag = sorted(per_2022[kod], key=lambda b: -b[1])
            bidrag = [b for b in bidrag if b[1] > GRANS_MED]
            klass = klassa_mottagare(bidrag)
            klass_2022[kod] = klass
            stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
            for b in bidrag:
                ovm2 = b[1] * d2022[kod]["geom"].area
                w.writerow([kod, d2022[kod]["namn"], klass, len(stora), b[0], d2014[b[0]]["namn"],
                            "%.4f" % b[1], "%.4f" % b[2], "%.1f" % ovm2, "ja" if b[1] >= GRANS_SLIVER else "nej"])
            cross.append({"kod_2022": kod, "namn_2022": d2022[kod]["namn"], "klass": klass,
                          "bidrag": [(b[0], d2014[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["crosswalk"] = cross
    samman["klass_2022_antal"] = {k: sum(1 for v in klass_2022.values() if v == k)
                                  for k in ("identisk", "delning", "sammanslagning", "omritning")}
    # klassning av 2014-distrikten i Majornaomradet (inne + delvis) mot 2022
    k2014 = []
    for r in maj_rader:
        if r["klass"] == "ute":
            continue
        bidrag = sorted(per_2014_22[r["kod"]], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        k2014.append({"kod": r["kod"], "namn": r["namn"], "klass_2014": r["klass"],
                      "utfall": klassa_givare(bidrag),
                      "bidrag": [(b[0], d2022[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["klass_2014"] = k2014
    samman["klass_2014_antal"] = {k: sum(1 for v in k2014 if v["utfall"] == k)
                                  for k in ("oforandrad", "delad", "sammanslagen", "omritad")}
    # samma 2014-distrikt mot 2018
    per_2014_18 = defaultdict(list)
    per_2018 = defaultdict(list)
    for r in ov18:
        per_2014_18[r["kod_a"]].append((r["kod_b"], r["andel_av_a"], r["andel_av_b"]))
        per_2018[r["kod_b"]].append((r["kod_a"], r["andel_av_b"], r["andel_av_a"]))
    k2018 = []
    for r in maj_rader:
        if r["klass"] == "ute":
            continue
        bidrag = sorted(per_2014_18[r["kod"]], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        k2018.append({"kod": r["kod"], "namn": r["namn"], "utfall": klassa_givare(bidrag),
                      "bidrag": [(b[0], d2018[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["klass_2014_2018"] = k2018
    samman["klass_2014_2018_antal"] = {k: sum(1 for v in k2018 if v["utfall"] == k)
                                       for k in ("oforandrad", "delad", "sammanslagen", "omritad")}

    # hela Goteborg: hur manga 2014-distrikt ar oforandrade 2018 respektive 2022
    def antal_oforandrade(per):
        n = 0
        for kod in d2014:
            b = sorted(per[kod], key=lambda x: -x[1])
            if b and b[0][1] >= GRANS_IDENTISK and b[0][2] >= GRANS_IDENTISK:
                n += 1
        return n
    samman["goteborg_oforandrade_2014"] = {"till_2018": antal_oforandrade(per_2014_18),
                                           "till_2022": antal_oforandrade(per_2014_22)}

    # (5b) jamforelse med Valmyndighetens officiella mappning 2014 -> 2018
    mapp = las_skv_mappning(SKV_MAPPNING)
    indelning = las_skv_indelning(SKV_INDELNING)
    jmf_rader = []
    stat = {"par_officiella": 0, "par_geo": 0, "bada": 0, "bara_officiell": 0, "bara_geo": 0,
            "abs_diff_summa": 0.0, "abs_diff_max": 0.0, "abs_diff_max_par": None,
            "diff_over_10": 0, "diff_over_20": 0, "kod_2014_bara_i_skv": [], "kod_2014_bara_i_shp": [],
            "kod_2018_bara_i_skv": [], "kod_2018_bara_i_shp": []}
    koder14_skv = set(mapp)
    koder18_skv = set(k for v in mapp.values() for k, _ in v)
    stat["kod_2014_bara_i_skv"] = sorted(koder14_skv - set(d2014))
    stat["kod_2014_bara_i_shp"] = sorted(set(d2014) - koder14_skv)
    stat["kod_2018_bara_i_skv"] = sorted(koder18_skv - set(d2018))
    stat["kod_2018_bara_i_shp"] = sorted(set(d2018) - koder18_skv)
    for kod in sorted(set(d2014) | koder14_skv):
        off = {k: p for k, p in mapp.get(kod, [])}
        geo = {b[0]: (b[1], b[2]) for b in per_2014_18.get(kod, [])}
        geo_stora = {k: v for k, v in geo.items() if v[0] >= GRANS_MAPPNING}
        alla = sorted(set(off) | set(geo_stora), key=lambda k: -(off.get(k, 0) / 100 + geo.get(k, (0, 0))[0]))
        for k18 in alla:
            p = off.get(k18)
            g = geo.get(k18)
            if p is not None and k18 in geo_stora:
                status = "bada"
            elif p is not None:
                status = "bara_officiell"
            else:
                status = "bara_geo"
            stat[status] += 1
            diff = None
            if p is not None and g is not None:
                diff = g[0] - p / 100
                stat["abs_diff_summa"] += abs(diff)
                if abs(diff) > stat["abs_diff_max"]:
                    stat["abs_diff_max"] = abs(diff)
                    stat["abs_diff_max_par"] = [kod, k18]
                if abs(diff) > 0.10:
                    stat["diff_over_10"] += 1
                if abs(diff) > 0.20:
                    stat["diff_over_20"] += 1
            jmf_rader.append([kod, d2014.get(kod, {}).get("namn", ""), k18, d2018.get(k18, {}).get("namn", ""),
                              "" if p is None else "%.1f" % p,
                              "" if g is None else "%.4f" % g[0],
                              "" if g is None else "%.4f" % g[1],
                              "" if diff is None else "%.4f" % diff,
                              status, indelning.get(k18, "")])
    stat["par_officiella"] = sum(len(v) for v in mapp.values())
    stat["par_geo"] = sum(1 for kod in d2014 for b in per_2014_18.get(kod, []) if b[1] >= GRANS_MAPPNING)
    n_bada = stat["bada"]
    stat["abs_diff_medel"] = stat["abs_diff_summa"] / n_bada if n_bada else None
    with open(UT_MAPPNING_JMF, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod_2014", "namn_2014", "kod_2018", "namn_2018", "procent_officiell",
                    "andel_av_2014_geo", "andel_av_2018_geo", "diff_geo_minus_officiell", "status", "indelning_2018"])
        w.writerows(jmf_rader)
    # indelningskoden O/M/S/N mot geometrisk klass for varje 2018-distrikt
    ind_rader = []
    ind_stat = defaultdict(lambda: defaultdict(int))
    for k18 in sorted(set(d2018) | set(indelning)):
        bidrag = sorted(per_2018.get(k18, []), key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        klass = klassa_mottagare(bidrag) if k18 in d2018 else ""
        ind = indelning.get(k18, "")
        stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
        huvud = bidrag[0] if bidrag else None
        # samma kod bade 2014 och 2018 med >= 0.98 at bada hallen betyder "oforandrad kod och yta"
        samma_kod = "ja" if (huvud and huvud[0] == k18 and huvud[1] >= GRANS_IDENTISK and huvud[2] >= GRANS_IDENTISK) else "nej"
        ind_stat[ind][klass] += 1
        ind_rader.append([k18, d2018.get(k18, {}).get("namn", ""), ind, klass, len(stora),
                          huvud[0] if huvud else "", "%.4f" % huvud[1] if huvud else "", "%.4f" % huvud[2] if huvud else "",
                          samma_kod])
    with open(UT_INDELNING_JMF, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod_2018", "namn_2018", "indelning_officiell", "klass_geo", "antal_2014_stora",
                    "storsta_kod_2014", "andel_av_2018", "andel_av_2014", "samma_kod_och_yta"])
        w.writerows(ind_rader)
    samman["mappning_2014_2018"] = stat
    samman["indelning_2018_mot_geo"] = {k: dict(v) for k, v in ind_stat.items()}
    # officiell mappning for Majornaomradets 2014-distrikt: pekar de bara pa 148010 11-45?
    maj_off = {}
    for r in maj_rader:
        if r["klass"] != "ute":
            maj_off[r["kod"]] = mapp.get(r["kod"], [])
    samman["mappning_majorna_2014"] = maj_off
    print("mappning 2014-2018:", {k: v for k, v in stat.items() if not isinstance(v, list)})
    print("indelning mot geo:", samman["indelning_2018_mot_geo"])

    # (6) GeoJSON i WGS84
    n1 = skriv_geojson(UT_GEOJSON_GBG, d2014, till_wgs)
    n2 = skriv_geojson(UT_GEOJSON_MAJ, d2014, till_wgs, koder={r["kod"] for r in maj_rader})
    samman["geojson"] = {"goteborg": n1, "majornaomradet": n2}

    with open(UT_SAMMANFATTNING, "w", encoding="utf-8") as f:
        json.dump(samman, f, ensure_ascii=False, indent=1)
    print("klass 2022:", samman["klass_2022_antal"])
    print("klass 2014 -> 2022:", samman["klass_2014_antal"])
    print("klass 2014 -> 2018:", samman["klass_2014_2018_antal"])
    print("oforandrade i Goteborg:", samman["goteborg_oforandrade_2014"])
    print("skrev", UT_OVERLAP_2022, UT_OVERLAP_2018, UT_MAJORNA_2014, UT_CROSSWALK, UT_MAPPNING_JMF,
          UT_INDELNING_JMF, UT_GEOJSON_GBG, UT_GEOJSON_MAJ)


if __name__ == "__main__":
    main()
