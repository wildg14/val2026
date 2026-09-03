# -*- coding: utf-8 -*-
"""
val2010_bygg.py - valet 2010 for Goteborgs kommun (1480) per valdistrikt.

Laser Valmyndighetens xls-filer (slutligt valresultat per valdistrikt) och
XML-filer (slutresultat_1480R/L/K.xml, slutresultat_00R/L/K.xml) och skriver
CSV i langt format till data/historik/. Kor med:

  <venv>/bin/python scripts/historik/val2010_bygg.py

Alla tal kommer ur kallfilerna. Enda berakningen ar ogiltiga = blanka + ogiltiga_ovriga
i distriktfilen (tva kallkolumner summerade).
"""
import csv
import os
import re
import sys
from collections import OrderedDict, defaultdict

import xlrd
from dbfread import DBF
from lxml import etree

# ---------------------------------------------------------------- kallor
HIST = "/Users/daniel/code/Temp/Historiska dokument/"
SCRATCH = "/private/tmp/claude-501/-Users-daniel-code-Temp/f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad/"
XML_DIR = SCRATCH + "unz/slutresultat__1_/"

XLS_R = HIST + "slutligt_valresultat_valdistrikt_R.xls"
XLS_L = HIST + "slutligt_valresultat_valdistrikt_L.xls"
XLS_K_ANTAL = HIST + "slutligt_valresultat_valdistrikt_K_antal.xls"
XLS_K_PROCENT = HIST + "slutligt_valresultat_valdistrikt_K_procent.xls"
XLS_KOMMUNER_R = HIST + "slutligt_valresultat_kommuner_R.xls"
XLS_VALKRETSMANDAT_K = HIST + "valkretsmandat_K_2010.xls"
XLS_MANDAT_R = HIST + "mandatfordelning_per_valkrets_R (1).xls"
XML_1480 = {"rd": XML_DIR + "slutresultat_1480R.xml",
            "rf": XML_DIR + "slutresultat_1480L.xml",
            "kf": XML_DIR + "slutresultat_1480K.xml"}
XML_00 = {"rd": XML_DIR + "slutresultat_00R.xml",
          "rf": XML_DIR + "slutresultat_00L.xml",
          "kf": XML_DIR + "slutresultat_00K.xml"}
DBF_2010 = SCRATCH + "unz/alla_valdistrikt/alla_valdistrikt.dbf"

OUT = "/Users/daniel/code/Temp/data/historik/"
AR = "2010"
LAN, KOM = 14, 80

PARSER = etree.XMLParser(load_dtd=False, resolve_entities=False, no_network=True, huge_tree=True)

# ---------------------------------------------------------------- hjalp
def norm_parti(p):
    """Normaliserad partikod: FP->L, DEM->D, KP->K, annars kallans kod i versaler.
    Numeriska partikoder (t.ex. 450.0 i xls, "0450" i XML) skrivs med fyra siffror."""
    if isinstance(p, float):
        return "%04d" % int(p)
    p = str(p).strip()
    if re.fullmatch(r"\d+", p):
        return "%04d" % int(p)
    m = {"FP": "L", "DEM": "D", "KP": "K"}
    return m.get(p, p.upper())


def parti_kalla(p):
    if isinstance(p, float):
        return "%04d" % int(p)
    return str(p).strip()


def num(v):
    """xls-cell till text: heltal utan decimaler, annars som det ar, tom om tom."""
    if v is None or v == "":
        return ""
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return repr(v)
    return str(v)


def dec(s):
    """XML-procent '31,24' -> '31.24'; None -> ''."""
    if s is None:
        return ""
    return s.replace(",", ".")


def lika(a, b):
    """Numerisk jamforelse av tva textvarden ('63.8' == '63.80'); tomma varden ar lika bara med tomma."""
    if a in ("", None) or b in ("", None):
        return a in ("", None) and b in ("", None)
    return abs(float(a) - float(b)) < 1e-9


def kod8(lan, kom, vd):
    """LAN, KOM, VALDISTRIKT (float eller 'VK01') -> 8-siffrig kod."""
    if isinstance(vd, str):
        m = re.fullmatch(r"VK(\d+)", vd)
        if not m:
            raise ValueError("okand distriktkod %r" % vd)
        vd = int(m.group(1))
    return "%02d%02d%04d" % (int(lan), int(kom), int(vd))


def write_csv(name, header, rows):
    path = OUT + name
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)
    print("skrev %s (%d rader)" % (path, len(rows)))
    return path


# ---------------------------------------------------------------- xls
def las_xls_par(path):
    """R- och L-filen: kolumnpar '<parti> tal' / '<parti> proc'.
    Returnerar OrderedDict kod -> dict(namn, partier=[(kalla, tal, proc)], giltiga, blanka, og, rostande, rostb, vdt)."""
    sh = xlrd.open_workbook(path).sheet_by_index(0)
    hdr = [sh.cell_value(0, c) for c in range(sh.ncols)]
    tal_cols = [(c, hdr[c][:-4]) for c in range(6, sh.ncols) if isinstance(hdr[c], str) and hdr[c].endswith(" tal")]
    proc_col = {hdr[c][:-5]: c for c in range(6, sh.ncols) if isinstance(hdr[c], str) and hdr[c].endswith(" proc")}
    fasta = {n: hdr.index(n) for n in ("Rost Giltiga", "Rostande", "Rostb", "VDT")}
    out = OrderedDict()
    for r in range(1, sh.nrows):
        if sh.cell_value(r, 0) != LAN or sh.cell_value(r, 1) != KOM:
            continue
        kod = kod8(sh.cell_value(r, 0), sh.cell_value(r, 1), sh.cell_value(r, 2))
        d = {"namn": sh.cell_value(r, 5), "partier": [], "blanka": "", "og": ""}
        for c, p in tal_cols:
            tal = sh.cell_value(r, c)
            proc = sh.cell_value(r, proc_col[p])
            if p in ("BL", "BLANK"):
                d["blanka"] = num(tal)
            elif p == "OG":
                d["og"] = num(tal)
            elif tal != "":
                d["partier"].append((p, num(tal), num(proc)))
        d["giltiga"] = num(sh.cell_value(r, fasta["Rost Giltiga"]))
        d["rostande"] = num(sh.cell_value(r, fasta["Rostande"]))
        d["rostb"] = num(sh.cell_value(r, fasta["Rostb"]))
        d["vdt"] = num(sh.cell_value(r, fasta["VDT"]))
        out[kod] = d
    return out, hdr


def las_xls_k(path_antal, path_procent):
    """K-filerna: en kolumn per parti, antal och procent i var sin fil."""
    sa = xlrd.open_workbook(path_antal).sheet_by_index(0)
    sp = xlrd.open_workbook(path_procent).sheet_by_index(0)
    hdr = [sa.cell_value(0, c) for c in range(sa.ncols)]
    hdrp = [sp.cell_value(0, c) for c in range(sp.ncols)]
    assert hdr == hdrp, "K antal och K procent har olika kolumner"
    fasta = {n: hdr.index(n) for n in ("Rost Giltiga", "Rostande", "Rostb", "VDT")}
    parti_cols = [c for c in range(6, fasta["Rost Giltiga"]) if hdr[c] not in ("BLANK", "OG")]
    # procentfilen maste ha samma rader i samma ordning; kontrollera med koden
    out = OrderedDict()
    for r in range(1, sa.nrows):
        if sa.cell_value(r, 0) != LAN or sa.cell_value(r, 1) != KOM:
            continue
        kod = kod8(sa.cell_value(r, 0), sa.cell_value(r, 1), sa.cell_value(r, 2))
        kodp = kod8(sp.cell_value(r, 0), sp.cell_value(r, 1), sp.cell_value(r, 2))
        assert kod == kodp, "radordning skiljer mellan K antal och K procent vid %s" % kod
        d = {"namn": sa.cell_value(r, 5), "partier": []}
        for c in parti_cols:
            tal = sa.cell_value(r, c)
            if tal == "":
                continue
            d["partier"].append((hdr[c], num(tal), num(sp.cell_value(r, c))))
        d["blanka"] = num(sa.cell_value(r, hdr.index("BLANK")))
        d["og"] = num(sa.cell_value(r, hdr.index("OG")))
        d["giltiga"] = num(sa.cell_value(r, fasta["Rost Giltiga"]))
        d["rostande"] = num(sa.cell_value(r, fasta["Rostande"]))
        d["rostb"] = num(sa.cell_value(r, fasta["Rostb"]))
        d["vdt"] = num(sa.cell_value(r, fasta["VDT"]))
        out[kod] = d
    return out, hdr


def las_valkretsnamn_k():
    """valkretsmandat_K_2010.xls: rad med kommunkod 1480 -> {'148001': 'Göteborg, Hisingen', ...}."""
    sh = xlrd.open_workbook(XLS_VALKRETSMANDAT_K).sheet_by_index(0)
    namn = {}
    for r in range(sh.nrows):
        if sh.cell_value(r, 2) == 1480.0:
            namn["1480%02d" % int(sh.cell_value(r, 4))] = sh.cell_value(r, 5)
    return namn


def las_riksdagsvalkretsnamn():
    """mandatfordelning_per_valkrets_R (1).xls: LAN, VALKRETS -> NAMN, plus fasta mandat."""
    sh = xlrd.open_workbook(XLS_MANDAT_R).sheet_by_index(0)
    hdr = [sh.cell_value(0, c) for c in range(sh.ncols)]
    out = {}
    for r in range(1, sh.nrows):
        if sh.cell_value(r, 0) == "":
            continue
        kod = "%02d%02d" % (int(sh.cell_value(r, 0)), int(sh.cell_value(r, 1)))
        out[kod] = {"namn": sh.cell_value(r, 3), "fasta": num(sh.cell_value(r, 4)),
                    "rad": dict(zip(hdr, [sh.cell_value(r, c) for c in range(sh.ncols)]))}
    return out


# ---------------------------------------------------------------- xml
def partirader(node):
    """Alla partirader under en nod (KOMMUN, KRETS_KOMMUN, VALDISTRIKT, NATION ...):
    lista av dict(kalla, roster, fgval, procent, grupp, mandat, utj, mandat_fgval)."""
    rows = []

    def add(el, grupp):
        rows.append({"kalla": el.get("PARTI") if el.tag == "GILTIGA" else el.tag,
                     "roster": el.get("RÖSTER"), "fgval": el.get("RÖSTER_FGVAL"),
                     "procent": el.get("PROCENT"), "procent_fgval": el.get("PROCENT_FGVAL"),
                     "grupp": grupp, "mandat": el.get("MANDAT"),
                     "utj": el.get("VARAV_UTJÄMNING"), "mandat_fgval": el.get("MANDAT_FGVAL")})

    for ch in node:
        if ch.tag == "GILTIGA":
            add(ch, "giltiga")
        elif ch.tag == "ÖVRIGA_GILTIGA":
            for c2 in ch:
                if c2.tag in ("GILTIGA", "HANDSKRIVNA", "ÖVRIGA_FGVAL"):
                    add(c2, "ovriga")
    return rows


def ogiltiga(node):
    d = {}
    for ch in node.findall("OGILTIGA"):
        d[ch.get("TEXT")] = {"roster": ch.get("RÖSTER"), "fgval": ch.get("RÖSTER_FGVAL"),
                             "procent": ch.get("PROCENT"), "procent_fgval": ch.get("PROCENT_FGVAL")}
    return d


def deltagande(node):
    v = node.find("VALDELTAGANDE")
    if v is None:
        return {}
    return {"rostb": v.get("RÖSTBERÄTTIGADE"), "rostb_fgval": v.get("RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL"),
            "summa": v.get("SUMMA_RÖSTER"), "summa_fgval": v.get("SUMMA_RÖSTER_FGVAL"),
            "procent": v.get("PROCENT"), "procent_fgval": v.get("PROCENT_FGVAL")}


def las_xml_1480(path):
    root = etree.parse(path, PARSER).getroot()
    kommun = root.find("KOMMUN")
    assert kommun.get("KOD") == "1480"
    res = {"kommun": kommun, "kretsar": [], "distrikt": OrderedDict()}
    for kk in kommun.findall("KRETS_KOMMUN"):
        res["kretsar"].append(kk)
        for vd in kk.findall("VALDISTRIKT"):
            res["distrikt"][vd.get("KOD")] = (kk.get("KOD"), vd)
        for on in kk.findall("ONSDAGSDISTRIKT"):
            # XML-kod t.ex. R-1480-03 -> 14800003, samma form som xls
            m = re.fullmatch(r"[RLK]-1480-(\d\d)", on.get("KOD"))
            res["distrikt"]["1480%04d" % int(m.group(1))] = (kk.get("KOD"), on)
    return res


# ---------------------------------------------------------------- huvud
def main():
    valkretsnamn = las_valkretsnamn_k()
    print("kommunvalkretsar:", valkretsnamn)
    dbf_namn = {r["LKFV"]: r["VDNAMN"] for r in DBF(DBF_2010, encoding="latin-1") if r["LKFV"].startswith("1480")}
    print("dbf: %d Goteborgsdistrikt" % len(dbf_namn))

    xls = {}
    xls["rd"], hdr_r = las_xls_par(XLS_R)
    xls["rf"], hdr_l = las_xls_par(XLS_L)
    xls["kf"], hdr_k = las_xls_k(XLS_K_ANTAL, XLS_K_PROCENT)
    xmls = {v: las_xml_1480(p) for v, p in XML_1480.items()}
    kallfil = {"rd": os.path.basename(XLS_R), "rf": os.path.basename(XLS_L),
               "kf": os.path.basename(XLS_K_ANTAL) + " + " + os.path.basename(XLS_K_PROCENT)}

    skrivna = []
    avvikelser = []
    for val in ("rd", "rf", "kf"):
        X = xls[val]
        M = xmls[val]
        # ---- kodkontroll
        xk, mk = set(X), set(M["distrikt"])
        if xk != mk:
            avvikelser.append("%s: koder skiljer xls/xml: bara xls %s, bara xml %s" % (val, sorted(xk - mk), sorted(mk - xk)))
        riktiga = {k for k in xk if not k.startswith("148000")}
        if riktiga != set(dbf_namn):
            avvikelser.append("%s: koder skiljer xls/dbf: bara xls %s, bara dbf %s" % (val, sorted(riktiga - set(dbf_namn)), sorted(set(dbf_namn) - riktiga)))
        for k in riktiga:
            if dbf_namn.get(k) != X[k]["namn"]:
                avvikelser.append("%s: namn skiljer %s: xls %r dbf %r" % (val, k, X[k]["namn"], dbf_namn.get(k)))

        # ---- roster xls
        rows = []
        for kod, d in X.items():
            for p, tal, proc in d["partier"]:
                rows.append([AR, val, kod, d["namn"], parti_kalla(p), norm_parti(p), tal, proc])
        skrivna.append(write_csv("roster_%s_%s_xls.csv" % (AR, val), ["ar", "val", "kod", "namn", "parti_kalla", "parti", "roster", "andel"], rows))

        # ---- roster xml (namn fran xls via koden)
        rows = []
        fg = []
        fgd = []
        for kod, (krets, vd) in M["distrikt"].items():
            namn = X[kod]["namn"] if kod in X else ""
            for pr in partirader(vd):
                if pr["kalla"] == "ÖVRIGA_FGVAL":
                    pass  # bara i fgval-filen
                else:
                    rows.append([AR, val, kod, namn, pr["kalla"], norm_parti(pr["kalla"]), pr["roster"] or "", dec(pr["procent"])])
                fg.append([2006, val, kod, namn, norm_parti(pr["kalla"]), pr["roster"] or "", pr["fgval"] or ""])
            og = ogiltiga(vd)
            for t in ("BLANK", "OG"):
                if t in og:
                    fg.append([2006, val, kod, namn, t, og[t]["roster"] or "", og[t]["fgval"] or ""])
            dl = deltagande(vd)
            fgd.append([2006, val, kod, namn, vd.get("RÖSTER") or "", vd.get("RÖSTER_FGVAL") or "",
                        dl.get("summa") or "", dl.get("summa_fgval") or "", dl.get("rostb") or "", dl.get("rostb_fgval") or "",
                        dec(dl.get("procent")), dec(dl.get("procent_fgval")), vd.get("INDELNING") or ""])
        skrivna.append(write_csv("roster_%s_%s_xml.csv" % (AR, val), ["ar", "val", "kod", "namn", "parti_kalla", "parti", "roster", "andel"], rows))
        skrivna.append(write_csv("fgval_%s_%s.csv" % (AR, val), ["ar_fg", "val", "kod_2010", "namn_2010", "parti", "roster_2010", "roster_fgval"], fg))
        skrivna.append(write_csv("fgval_%s_%s_deltagande.csv" % (AR, val),
                                 ["ar_fg", "val", "kod_2010", "namn_2010", "giltiga_2010", "giltiga_fgval", "rostande_2010", "rostande_fgval",
                                  "rostberattigade_2010", "rostberattigade_fgval", "valdeltagande_2010", "valdeltagande_fgval", "indelning"], fgd))

        # ---- distrikt (xls, kontrollerad mot xml)
        rows = []
        n_ok = 0
        for kod, d in X.items():
            krets, vd = M["distrikt"][kod]
            og = ogiltiga(vd)
            dl = deltagande(vd)
            onsdag = kod.startswith("148000")
            # kontroller
            kontroll = [("giltiga", d["giltiga"], vd.get("RÖSTER")), ("blanka", d["blanka"], og["BLANK"]["roster"]),
                        ("og", d["og"], og["OG"]["roster"])]
            if not onsdag:
                kontroll += [("rostande", d["rostande"], dl["summa"]), ("rostb", d["rostb"], dl["rostb"]), ("vdt", d["vdt"], dec(dl["procent"]))]
            for namn, a, b in kontroll:
                if not lika(a, b):
                    avvikelser.append("%s %s %s: xls %r xml %r" % (val, kod, namn, a, b))
            # partier
            xmlp = {pr["kalla"]: pr for pr in partirader(vd)}
            ovr_xml = 0
            xls_partier = {parti_kalla(p) for p, _, _ in d["partier"]}
            for kalla, pr in xmlp.items():
                if kalla == "ÖVRIGA_FGVAL":
                    continue
                if kalla not in xls_partier:
                    ovr_xml += int(pr["roster"] or 0)
            for p, tal, proc in d["partier"]:
                pk = parti_kalla(p)
                if pk in ("OVR", "ÖVR"):
                    if int(tal) != ovr_xml:
                        avvikelser.append("%s %s OVR: xls %s, xml summa ovriga+handskrivna %s" % (val, kod, tal, ovr_xml))
                elif pk not in xmlp:
                    if int(tal) != 0:
                        avvikelser.append("%s %s parti %s finns i xls (%s) men inte i xml" % (val, kod, pk, tal))
                elif not lika(tal, xmlp[pk]["roster"]) or not lika(proc, dec(xmlp[pk]["procent"])):
                    avvikelser.append("%s %s %s: xls %s/%s xml %s/%s" % (val, kod, pk, tal, proc, xmlp[pk]["roster"], dec(xmlp[pk]["procent"])))
                else:
                    n_ok += 1
            ogilt = ""
            if d["blanka"] != "" and d["og"] != "":
                ogilt = str(int(d["blanka"]) + int(d["og"]))
            rows.append([AR, val, kod, d["namn"], valkretsnamn[krets], d["giltiga"], d["blanka"], d["og"], ogilt, d["rostande"],
                         "" if onsdag else d["rostb"], "" if onsdag else d["vdt"], kallfil[val]])
        print("%s: %d partivarden lika xls/xml" % (val, n_ok))
        skrivna.append(write_csv("distrikt_%s_%s.csv" % (AR, val),
                                 ["ar", "val", "kod", "namn", "valkrets", "giltiga", "blanka", "ogiltiga_ovriga", "ogiltiga", "rostande",
                                  "rostberattigade", "valdeltagande", "kalla_fil"], rows))

        # ---- aggregat
        agg = []

        def agg_rows(niva, node):
            dl = deltagande(node)
            for pr in partirader(node):
                if pr["kalla"] == "ÖVRIGA_FGVAL":
                    continue
                agg.append([AR, val, niva, pr["kalla"], norm_parti(pr["kalla"]), pr["roster"] or "", dec(pr["procent"]),
                            node.get("RÖSTER") or "", dl.get("summa") or "", dl.get("rostb") or ""])
            for t, o in ogiltiga(node).items():
                agg.append([AR, val, niva, t, t, o["roster"] or "", dec(o["procent"]), node.get("RÖSTER") or "", dl.get("summa") or "", dl.get("rostb") or ""])

        root00 = etree.parse(XML_00[val], PARSER).getroot()
        nation = root00.find("NATION")
        agg_rows("riket", nation)
        if val == "rf":
            lan14 = [l for l in nation.findall("LÄN") if l.get("KOD") == "14"][0]
            agg_rows("vgregion", lan14)
        agg_rows("goteborg", M["kommun"])
        for kk in M["kretsar"]:
            agg_rows(valkretsnamn[kk.get("KOD")], kk)
        skrivna.append(write_csv("aggregat_%s_%s.csv" % (AR, val),
                                 ["ar", "val", "niva", "parti_kalla", "parti", "roster", "andel", "giltiga", "rostande", "rostberattigade"], agg))

        # kontroll: kommunraden i kommuner_R.xls mot XML
        if val == "rd":
            sh = xlrd.open_workbook(XLS_KOMMUNER_R).sheet_by_index(0)
            hdr = [sh.cell_value(0, c) for c in range(sh.ncols)]
            for r in range(1, sh.nrows):
                if sh.cell_value(r, 0) == LAN and sh.cell_value(r, 1) == KOM:
                    rad = dict(zip(hdr, [sh.cell_value(r, c) for c in range(sh.ncols)]))
            xmlp = {pr["kalla"]: pr for pr in partirader(M["kommun"])}
            dl = deltagande(M["kommun"])
            for p in ("M", "C", "FP", "KD", "S", "V", "MP", "SD", "FI", "PP", "SPI"):
                if not lika(num(rad[p + " tal"]), xmlp[p]["roster"]):
                    avvikelser.append("kommuner_R: %s xls %s xml %s" % (p, num(rad[p + " tal"]), xmlp[p]["roster"]))
            for a, b in (("Rost Giltiga", M["kommun"].get("RÖSTER")), ("Rostande", dl["summa"]), ("Rostb", dl["rostb"]), ("VDT", dec(dl["procent"]))):
                if not lika(num(rad[a]), b):
                    avvikelser.append("kommuner_R: %s xls %s xml %s" % (a, num(rad[a]), b))
            print("kommuner_R.xls Goteborg kontrollerad mot 1480R.xml")

        # ---- mandat riksdag
        if val == "rd":
            rvk = las_riksdagsvalkretsnamn()
            rows = []

            def mandat_rows(niva, kod, namn, node, mandat_valkrets):
                for pr in partirader(node):
                    if pr["mandat"] is None and pr["mandat_fgval"] is None:
                        continue
                    rows.append([AR, val, niva, kod, namn, pr["kalla"], norm_parti(pr["kalla"]), pr["roster"] or "", dec(pr["procent"]),
                                 pr["mandat"] or "", pr["utj"] or "", pr["mandat_fgval"] or "", mandat_valkrets or ""])

            mandat_rows("riket", "00", "Riket", nation, nation.get("MANDAT_VALOMRÅDE"))
            for lan in nation.findall("LÄN"):
                for kr in lan.findall("KRETS_RIKSDAG"):
                    info = rvk.get(kr.get("KOD"), {})
                    mandat_rows("valkrets", kr.get("KOD"), info.get("namn", ""), kr, kr.get("MANDAT_VALKRETS"))
                    if kr.get("KOD") == "1416":
                        # kontroll mot mandatfordelning_per_valkrets_R (1).xls
                        for pr in partirader(kr):
                            if pr["mandat"] is None:
                                continue
                            x = info["rad"].get(pr["kalla"], "")
                            xu = info["rad"].get(pr["kalla"] + " utj", "")
                            tot = int(x or 0) + int(xu or 0)
                            if tot != int(pr["mandat"]):
                                avvikelser.append("mandat 1416 %s: xls %s+%s xml %s" % (pr["kalla"], x, xu, pr["mandat"]))
            skrivna.append(write_csv("mandat_%s_riksdag.csv" % AR,
                                     ["ar", "val", "niva", "kod", "namn", "parti_kalla", "parti", "roster", "andel", "mandat", "varav_utjamning",
                                      "mandat_fgval", "mandat_valkrets"], rows))

    # ---- partiforteckning ur XML:s PARTI-lista (1480X.xml och 00X.xml)
    rows = []
    for val in ("rd", "rf", "kf"):
        sett = set()
        for path in (XML_1480[val], XML_00[val]):
            root = etree.parse(path, PARSER).getroot()
            for pe in root.findall("PARTI"):
                k = pe.get("FÖRKORTNING")
                if k in sett:
                    continue
                sett.add(k)
                rows.append([AR, val, k, norm_parti(k), pe.get("BETECKNING"), pe.get("FÄRG") or "", os.path.basename(path)])
    skrivna.append(write_csv("partier_%s.csv" % AR, ["ar", "val", "parti_kalla", "parti", "beteckning", "farg", "kalla_fil"], rows))

    # ---- distriktlista for noteringen
    print("\nDistrikt per kommunvalkrets (rd):")
    for kod, (krets, vd) in xmls["rd"]["distrikt"].items():
        n = xls["rd"][kod]["namn"]
        if any(s in n for s in ("Majorna", "Linnéstaden", "Kungsten", "Älvsborg", "Högsbo")):
            print("  %s  %s  %s  indelning=%s fgval=%s" % (kod, valkretsnamn[krets], n, vd.get("INDELNING") or "-", vd.get("RÖSTER_FGVAL")))
    print("\nAvvikelser (%d):" % len(avvikelser))
    for a in avvikelser:
        print("  " + a)
    return skrivna


if __name__ == "__main__":
    main()
