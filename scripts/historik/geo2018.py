"""geo2018: geografisk jamforbarhet for Goteborgs valdistrikt 2018 mot 2022.

Laser 2018 ars shapefile (Valmyndighetens valgeografi, SWEREF99 TM, dbf i UTF-8)
och 2022 ars GeoJSON for Vastra Gotaland (SWEREF99 TM), raknar areaoverlapp
mellan indelningarna for hela Goteborgs kommun (1480), bygger unionen av de 23
Majornadistrikten 2022 och beskriver varje 2022-distrikt i Vastra Centrum som
en kombination av 2018-distrikt. Skriver CSV, GeoJSON (WGS84) och en JSON-
sammanfattning i scratchpad som underlag till noteringen docs/historik/noter/geo2018.md.

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

SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"
SHP_2018 = SCRATCH + "/unz/2018_valgeografi_valdistrikt/alla_valdistrikt.shp"    # falt VD, VD_NAMN; dbf UTF-8; SWEREF99 TM
GEOJSON_2022 = SCRATCH + "/unz/valgeografi_2022/VD_14_20220910_Val_20220911.json"  # egenskaper Lkfv, Vdnamn; EPSG:3006

PROJEKT = "/Users/daniel/code/Temp"
UT_DATA = PROJEKT + "/data/historik"
UT_OVERLAP = UT_DATA + "/geo_overlap_2018_2022.csv"
UT_MAJORNA_2018 = UT_DATA + "/geo_majorna_2018.csv"
UT_CROSSWALK_MAJ = UT_DATA + "/geo_crosswalk_2018_2022_majorna.csv"
UT_CROSSWALK_VC = UT_DATA + "/geo_crosswalk_2018_2022_vastra_centrum.csv"
UT_GEOJSON_GBG = UT_DATA + "/distrikt_2018_goteborg.geojson"
UT_GEOJSON_MAJ = UT_DATA + "/distrikt_2018_majornaomradet.geojson"
UT_SAMMANFATTNING = SCRATCH + "/geo2018_sammanfattning.json"   # underlag till noteringen, inte en projektfil

KOMMUN = "1480"
MAJORNA_2022 = ["148005%02d" % i for i in range(26, 49)]        # 14800526-14800548, 23 distrikt
VASTRA_CENTRUM_2022 = ["148005%02d" % i for i in range(1, 49)]  # 14800501-14800548, 48 distrikt

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


def las_shapefile_2018(path):
    r = shapefile.Reader(path, encoding="utf-8")
    ut = {}
    ogiltiga = []
    antal_totalt = 0
    for sr in r.iterShapeRecords():
        antal_totalt += 1
        rec = sr.record.as_dict()
        kod = str(rec["VD"]).strip()
        if not kod.startswith(KOMMUN):
            continue
        g, var_ogiltig = laga(shape(sr.shape.__geo_interface__))
        if var_ogiltig:
            ogiltiga.append(kod)
        if kod in ut:
            raise SystemExit("dubblettkod %s i %s" % (kod, path))
        ut[kod] = {"kod": kod, "namn": str(rec["VD_NAMN"]).strip(), "geom": g,
                   "kvk": str(rec["KVK"]).strip(), "kvk_namn": str(rec["KVK_NAMN"]).strip()}
    return ut, ogiltiga, antal_totalt


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


def area_kontroll(namn, distrikt):
    areor = sorted((d["geom"].area, d["kod"], d["namn"]) for d in distrikt.values())
    tot = sum(a for a, _, _ in areor)
    minst = areor[0]
    storst = areor[-1]
    print("%s: %d distrikt, total yta %.1f km2, minsta %s %s %.3f km2, storsta %s %s %.2f km2" % (
        namn, len(distrikt), tot / 1e6, minst[1], minst[2], minst[0] / 1e6, storst[1], storst[2], storst[0] / 1e6))
    return {"antal": len(distrikt), "total_km2": tot / 1e6,
            "minsta": [minst[1], minst[2], minst[0]], "storsta": [storst[1], storst[2], storst[0]],
            "under_1_ha": [[k, n, a] for a, k, n in areor if a < 10000]}


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


def skriv_overlapp(path, rader):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod_2018", "namn_2018", "kod_2022", "namn_2022",
                    "overlapp_m2", "andel_av_2018", "andel_av_2022"])
        for r in rader:
            w.writerow([r["kod_a"], r["namn_a"], r["kod_b"], r["namn_b"],
                        "%.1f" % r["overlapp_m2"], "%.4f" % r["andel_av_a"], "%.4f" % r["andel_av_b"]])


def klassa_i_majorna(andel):
    if andel >= GRANS_INNE:
        return "inne"
    if andel >= GRANS_DELVIS:
        return "delvis"
    return "ute"


def klassa_2022(bidrag):
    """bidrag: lista av (kod_2018, andel_av_2022, andel_av_2018) sorterad fallande pa andel_av_2022.
    identisk: ett 2018-distrikt tacker >= 98 procent av 2022-distriktet och 2022-distriktet tacker >= 98 procent av det.
    delning: ett enda betydande 2018-distrikt tacker >= 98 procent, men 2022-distriktet ar bara en del av det.
    sammanslagning: flera betydande 2018-distrikt som vart och ett ligger helt (>= 98 procent) i 2022-distriktet
    och tillsammans tacker >= 98 procent. Allt annat: omritning."""
    stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
    if bidrag and bidrag[0][1] >= GRANS_IDENTISK and bidrag[0][2] >= GRANS_IDENTISK:
        return "identisk"
    if len(stora) == 1 and stora[0][1] >= GRANS_IDENTISK and stora[0][2] < GRANS_IDENTISK:
        return "delning"
    if len(stora) >= 2 and all(b[2] >= GRANS_IDENTISK for b in stora) and sum(b[1] for b in stora) >= GRANS_IDENTISK:
        return "sammanslagning"
    return "omritning"


def klassa_2018_mot_2022(bidrag):
    """bidrag: lista av (kod_2022, andel_av_2018, andel_av_2022) sorterad fallande pa andel_av_2018.
    Beskriver vad som hande med 2018-distriktet till 2022 (speglar klassa_2022)."""
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


def skriv_crosswalk(path, koder, per_2022, d2018, d2022):
    """En rad per (2022-distrikt, bidragande 2018-distrikt). Returnerar lista av dict per 2022-distrikt."""
    ut = []
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod_2022", "namn_2022", "klass_2022", "antal_2018", "kod_2018", "namn_2018",
                    "andel_av_2022", "andel_av_2018", "overlapp_m2", "huvudkalla"])
        for kod in koder:
            bidrag = sorted(per_2022[kod], key=lambda b: -b[1])
            bidrag = [b for b in bidrag if b[1] > GRANS_MED]
            klass = klassa_2022(bidrag)
            stora = [b for b in bidrag if b[1] >= GRANS_SLIVER]
            for b in bidrag:
                ovm2 = b[1] * d2022[kod]["geom"].area
                w.writerow([kod, d2022[kod]["namn"], klass, len(stora), b[0], d2018[b[0]]["namn"],
                            "%.4f" % b[1], "%.4f" % b[2], "%.1f" % ovm2, "ja" if b[1] >= GRANS_SLIVER else "nej"])
            ut.append({"kod_2022": kod, "namn_2022": d2022[kod]["namn"], "klass": klass,
                       "area_m2": d2022[kod]["geom"].area,
                       "bidrag": [(b[0], d2018[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    return ut


def main():
    samman = {}
    prj_2018 = las_prj(SHP_2018)
    print("prj 2018:", prj_2018[:40])
    assert "SWEREF99_TM" in prj_2018 and "Central_Meridian\",15.0" in prj_2018
    till_wgs = Transformer.from_crs(CRS_TM, CRS_WGS, always_xy=True)

    d2018, og2018, n_riket_2018 = las_shapefile_2018(SHP_2018)
    d2022, og2022, n_lan_2022 = las_geojson_2022(GEOJSON_2022)
    samman["antal_i_kallan"] = {"2018_riket": n_riket_2018, "2022_lan_14": n_lan_2022}
    samman["ogiltiga_lagade"] = {"2018": og2018, "2022": og2022}
    print("poster i kallan: 2018 riket %d, 2022 lan 14 %d" % (n_riket_2018, n_lan_2022))
    print("ogiltiga geometrier lagade med buffer(0):", samman["ogiltiga_lagade"])
    samman["area"] = {"2018": area_kontroll("2018", d2018), "2022": area_kontroll("2022", d2022)}
    for ar, dd in (("2018", d2018), ("2022", d2022)):
        for d in dd.values():
            if d["geom"].is_empty or d["geom"].area < 1000:
                print("VARNING liten eller tom yta", ar, d["kod"], d["namn"], d["geom"].area)
    kvk = sorted({(d["kvk"], d["kvk_namn"]) for d in d2018.values()})
    samman["kommunvalkretsar_2018"] = kvk
    print("kommunvalkretsar i shapefilen 2018:", kvk)
    # kontroll av lagesnoggrannhet: kommunytorna
    u2022 = unary_union([d["geom"] for d in d2022.values()])
    u2018 = unary_union([d["geom"] for d in d2018.values()])
    samman["kommunyta"] = {"2018_km2": u2018.area / 1e6, "2022_km2": u2022.area / 1e6,
                           "snitt_km2": u2018.intersection(u2022).area / 1e6,
                           "2018_utanfor_2022_km2": u2018.difference(u2022).area / 1e6,
                           "2022_utanfor_2018_km2": u2022.difference(u2018).area / 1e6}
    print("kommunyta 2018 %.2f km2, 2022 %.2f km2, snitt %.2f km2" % (
        u2018.area / 1e6, u2022.area / 1e6, u2018.intersection(u2022).area / 1e6))
    # overlappande 2018-distrikt sinsemellan (ska vara noll eller obetydligt)
    lista = list(d2018.values())
    tree = STRtree([d["geom"] for d in lista])
    intern = 0.0
    for i, a in enumerate(lista):
        for j in tree.query(a["geom"]):
            if j <= i:
                continue
            if a["geom"].intersects(lista[j]["geom"]):
                intern += a["geom"].intersection(lista[j]["geom"]).area
    samman["intern_overlapp_2018_m2"] = intern
    print("intern overlapp mellan 2018-distrikt: %.1f m2" % intern)

    # (2) overlapp 2018 mot 2022, hela Goteborg
    ov = overlapp(d2018, d2022)
    skriv_overlapp(UT_OVERLAP, ov)
    samman["antal_par"] = len(ov)
    per_2022 = defaultdict(list)
    per_2018 = defaultdict(list)
    for r in ov:
        per_2022[r["kod_b"]].append((r["kod_a"], r["andel_av_b"], r["andel_av_a"]))
        per_2018[r["kod_a"]].append((r["kod_b"], r["andel_av_a"], r["andel_av_b"]))

    # (3) Majorna-unionen 2022
    saknas = [k for k in MAJORNA_2022 if k not in d2022]
    if saknas:
        raise SystemExit("Majornakoder saknas i 2022: %s" % saknas)
    union = unary_union([d2022[k]["geom"] for k in MAJORNA_2022])
    samman["majorna_union_km2"] = union.area / 1e6
    maj_rader = []
    for d in d2018.values():
        snitt = d["geom"].intersection(union).area
        andel_i = snitt / d["geom"].area
        if andel_i > GRANS_MED:
            maj_rader.append({"kod": d["kod"], "namn": d["namn"], "area_m2": d["geom"].area,
                              "andel_i_majorna": andel_i, "andel_av_majorna": snitt / union.area,
                              "klass": klassa_i_majorna(andel_i)})
    maj_rader.sort(key=lambda r: -r["andel_av_majorna"])
    with open(UT_MAJORNA_2018, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod", "namn", "area_m2", "andel_i_majorna", "andel_av_majorna", "klass"])
        for r in maj_rader:
            w.writerow([r["kod"], r["namn"], "%.1f" % r["area_m2"], "%.4f" % r["andel_i_majorna"],
                        "%.4f" % r["andel_av_majorna"], r["klass"]])
    inne = [r for r in maj_rader if r["klass"] == "inne"]
    delvis = [r for r in maj_rader if r["klass"] == "delvis"]
    inne_union = unary_union([d2018[r["kod"]]["geom"] for r in inne]) if inne else None
    samman["majorna_2018"] = {
        "rader": maj_rader,
        "inne_koder": [r["kod"] for r in inne],
        "delvis_koder": [r["kod"] for r in delvis],
        "ute_koder": [r["kod"] for r in maj_rader if r["klass"] == "ute"],
        "inne_tacker_andel_av_union": (inne_union.intersection(union).area / union.area) if inne_union is not None else 0,
        "inne_yta_km2": (inne_union.area / 1e6) if inne_union is not None else 0,
        "inne_utanfor_union_km2": (inne_union.difference(union).area / 1e6) if inne_union is not None else 0,
        "union_utanfor_inne_km2": (union.difference(inne_union).area / 1e6) if inne_union is not None else union.area / 1e6,
    }
    # alternativ: inne plus delvis-distrikt med mer an halva ytan i unionen
    alt = [r["kod"] for r in maj_rader if r["andel_i_majorna"] >= 0.5]
    alt_union = unary_union([d2018[k]["geom"] for k in alt])
    samman["majorna_2018"]["alt_halva_koder"] = alt
    samman["majorna_2018"]["alt_halva_yta_km2"] = alt_union.area / 1e6
    samman["majorna_2018"]["alt_halva_tacker_andel_av_union"] = alt_union.intersection(union).area / union.area
    samman["majorna_2018"]["alt_halva_utanfor_union_km2"] = alt_union.difference(union).area / 1e6
    print("Majorna-unionen 2022: %.4f km2; inne-distrikt 2018: %d, tacker %.4f av unionen, %d delvis" % (
        union.area / 1e6, len(inne), samman["majorna_2018"]["inne_tacker_andel_av_union"], len(delvis)))
    # vart hamnar den del av unionen som inne-distrikten inte tacker
    rest = union.difference(inne_union) if inne_union is not None else union
    rest_bidrag = []
    for d in d2018.values():
        if d["kod"] in samman["majorna_2018"]["inne_koder"]:
            continue
        a = d["geom"].intersection(rest).area
        if a > 100:
            rest_bidrag.append([d["kod"], d["namn"], a])
    rest_bidrag.sort(key=lambda x: -x[2])
    samman["majorna_2018"]["rest_m2"] = rest.area
    samman["majorna_2018"]["rest_bidrag"] = rest_bidrag

    # (4) crosswalk per 2022-distrikt i Majorna, (5) samma for hela Vastra Centrum
    cross_maj = skriv_crosswalk(UT_CROSSWALK_MAJ, MAJORNA_2022, per_2022, d2018, d2022)
    cross_vc = skriv_crosswalk(UT_CROSSWALK_VC, VASTRA_CENTRUM_2022, per_2022, d2018, d2022)
    samman["crosswalk_majorna"] = cross_maj
    samman["crosswalk_vastra_centrum"] = cross_vc
    klasser = ("identisk", "delning", "sammanslagning", "omritning")
    samman["klass_2022_majorna_antal"] = {k: sum(1 for c in cross_maj if c["klass"] == k) for k in klasser}
    samman["klass_2022_vc_antal"] = {k: sum(1 for c in cross_vc if c["klass"] == k) for k in klasser}
    # hela Goteborg per 2022-distrikt
    alla_2022 = []
    for kod in sorted(d2022):
        bidrag = sorted(per_2022[kod], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        alla_2022.append(klassa_2022(bidrag))
    samman["klass_2022_goteborg_antal"] = {k: alla_2022.count(k) for k in klasser}

    # klassning av 2018-distrikten i Majornaomradet (inne + delvis) mot 2022
    utfall = ("oforandrad", "delad", "sammanslagen", "omritad")
    k2018 = []
    for r in maj_rader:
        if r["klass"] == "ute":
            continue
        bidrag = sorted(per_2018[r["kod"]], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        k2018.append({"kod": r["kod"], "namn": r["namn"], "klass_2018": r["klass"],
                      "utfall": klassa_2018_mot_2022(bidrag),
                      "bidrag": [(b[0], d2022[b[0]]["namn"], b[1], b[2]) for b in bidrag]})
    samman["klass_2018"] = k2018
    samman["klass_2018_antal"] = {k: sum(1 for v in k2018 if v["utfall"] == k) for k in utfall}
    alla_2018 = []
    for kod in sorted(d2018):
        bidrag = sorted(per_2018[kod], key=lambda b: -b[1])
        bidrag = [b for b in bidrag if b[1] > GRANS_MED]
        alla_2018.append(klassa_2018_mot_2022(bidrag))
    samman["klass_2018_goteborg_antal"] = {k: alla_2018.count(k) for k in utfall}
    # namn som finns bada aren men med olika granser (Majorna-Linne 2018 mot Vastra Centrum 2022)
    namn_2018 = {}
    for d in d2018.values():
        if d["namn"].startswith("Majorna-Linné, "):
            namn_2018[d["namn"].split(", ", 1)[1]] = d["kod"]
    namn_lika = []
    for kod in VASTRA_CENTRUM_2022:
        kort = d2022[kod]["namn"].split(", ", 1)[1]
        if kort in namn_2018:
            k18 = namn_2018[kort]
            snitt = d2018[k18]["geom"].intersection(d2022[kod]["geom"]).area
            namn_lika.append([kort, k18, kod, snitt / d2018[k18]["geom"].area, snitt / d2022[kod]["geom"].area])
    samman["samma_namn_bada_aren"] = namn_lika

    # (6) GeoJSON i WGS84
    n1 = skriv_geojson(UT_GEOJSON_GBG, d2018, till_wgs)
    n2 = skriv_geojson(UT_GEOJSON_MAJ, d2018, till_wgs, koder={r["kod"] for r in maj_rader})
    samman["geojson"] = {"goteborg": n1, "majornaomradet": n2}

    with open(UT_SAMMANFATTNING, "w", encoding="utf-8") as f:
        json.dump(samman, f, ensure_ascii=False, indent=1)
    print("klass 2022 Majorna:", samman["klass_2022_majorna_antal"])
    print("klass 2022 Vastra Centrum:", samman["klass_2022_vc_antal"])
    print("klass 2022 Goteborg:", samman["klass_2022_goteborg_antal"])
    print("klass 2018 -> 2022 Majornaomradet:", samman["klass_2018_antal"])
    print("klass 2018 -> 2022 Goteborg:", samman["klass_2018_goteborg_antal"])
    print("skrev", UT_OVERLAP, UT_MAJORNA_2018, UT_CROSSWALK_MAJ, UT_CROSSWALK_VC, UT_GEOJSON_GBG, UT_GEOJSON_MAJ)


if __name__ == "__main__":
    main()
