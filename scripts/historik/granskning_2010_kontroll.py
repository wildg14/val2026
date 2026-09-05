# -*- coding: utf-8 -*-
"""
granskning_2010_kontroll.py - oberoende granskning av val2010-filerna i data/historik/.

Laser kallfilerna (xls, XML, dbf) med egen kod, raknar om totaler och jamfor med
de CSV-filer som val2010_bygg.py skrivit. Skriver bara till stdout (och en
rapportfil i scratchpad), andrar inga filer.

Kor med: <venv>/bin/python scripts/historik/granskning_2010_kontroll.py
"""
import csv
import glob
import os
import random
import re
from collections import OrderedDict, defaultdict

import xlrd
from dbfread import DBF
from lxml import etree

HIST = "/Users/daniel/code/Temp/Historiska dokument/"
SCRATCH = "/Users/daniel/code/Temp/Historiska dokument/"
XML_DIR = SCRATCH + "unz/slutresultat__1_/"
DBF_2010 = SCRATCH + "unz/alla_valdistrikt/alla_valdistrikt.dbf"
XLS = {"rd": HIST + "slutligt_valresultat_valdistrikt_R.xls",
       "rf": HIST + "slutligt_valresultat_valdistrikt_L.xls",
       "kf": HIST + "slutligt_valresultat_valdistrikt_K_antal.xls"}
XLS_K_PROCENT = HIST + "slutligt_valresultat_valdistrikt_K_procent.xls"
XLS_KOMMUNER_R = HIST + "slutligt_valresultat_kommuner_R.xls"
XLS_VALKRETSMANDAT_K = HIST + "valkretsmandat_K_2010.xls"
XML_1480 = {"rd": XML_DIR + "slutresultat_1480R.xml", "rf": XML_DIR + "slutresultat_1480L.xml", "kf": XML_DIR + "slutresultat_1480K.xml"}
XML_00 = {"rd": XML_DIR + "slutresultat_00R.xml", "rf": XML_DIR + "slutresultat_00L.xml", "kf": XML_DIR + "slutresultat_00K.xml"}
DATA = "/Users/daniel/code/Temp/data/historik/"
PARSER = etree.XMLParser(load_dtd=False, resolve_entities=False, no_network=True, huge_tree=True)

MAJORNA = ["14800911", "14800912", "14800913", "14800914", "14800915", "14800916", "14800921", "14800931", "14800932",
           "14800933", "14800934", "14800935", "14800936", "14800941", "14800942", "14800943", "14800944"]

fel = []
info = []


def F(msg):
    fel.append(msg)
    print("FEL: " + msg)


def I(msg):
    info.append(msg)
    print("info: " + msg)


def read_csv(name):
    with open(DATA + name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def fnum(s):
    return float(s) if s not in ("", None) else None


def col_letter(c):
    s = ""
    c += 1
    while c:
        c, r = divmod(c - 1, 26)
        s = chr(65 + r) + s
    return s


# ---------------------------------------------------------------- egen xls-lasning
def xls_rows(path):
    """Alla Goteborgsrader som dict rubrik -> varde, plus radnummer (1-baserat) och kolumnindex."""
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    hdr = [sh.cell_value(0, c) for c in range(sh.ncols)]
    rows = OrderedDict()
    for r in range(1, sh.nrows):
        if sh.cell_value(r, 0) == 14.0 and sh.cell_value(r, 1) == 80.0:
            vd = sh.cell_value(r, 2)
            if isinstance(vd, str):
                vd = int(re.sub(r"\D", "", vd))
            kod = "1480%04d" % int(vd)
            rows[kod] = {"rad": r + 1, "flik": sh.name, "celler": [sh.cell_value(r, c) for c in range(sh.ncols)]}
    return hdr, rows


def xls_partier(val, hdr):
    """Lista (kolumnindex, partikod_kalla) for partikolumner (antal)."""
    if val in ("rd", "rf"):
        return [(c, h[:-4]) for c, h in enumerate(hdr) if isinstance(h, str) and h.endswith(" tal") and h[:-4] not in ("BL", "BLANK", "OG")]
    end = hdr.index("BLANK")
    out = []
    for c in range(6, end):
        h = hdr[c]
        out.append((c, ("%04d" % int(h)) if isinstance(h, float) else str(h).strip()))
    return out


# ---------------------------------------------------------------- xml
def xml_partier(node):
    out = OrderedDict()
    for ch in node:
        if ch.tag == "GILTIGA":
            out[ch.get("PARTI")] = ch
        elif ch.tag == "ÖVRIGA_GILTIGA":
            for c2 in ch:
                if c2.tag == "GILTIGA":
                    out[c2.get("PARTI")] = c2
                elif c2.tag == "HANDSKRIVNA":
                    out["HANDSKRIVNA"] = c2
    return out


def xml_lasa(val):
    root = etree.parse(XML_1480[val], PARSER).getroot()
    kommun = root.find("KOMMUN")
    dist = OrderedDict()
    for kk in kommun.findall("KRETS_KOMMUN"):
        for vd in kk.findall("VALDISTRIKT"):
            dist[vd.get("KOD")] = (kk.get("KOD"), vd)
        for on in kk.findall("ONSDAGSDISTRIKT"):
            dist["1480%04d" % int(on.get("KOD")[-2:])] = (kk.get("KOD"), on)
    return kommun, dist


def main():
    random.seed(2010)
    dbf = {r["LKFV"]: r["VDNAMN"] for r in DBF(DBF_2010, encoding="latin-1") if r["LKFV"].startswith("1480")}
    I("dbf alla_valdistrikt: %d distrikt med LKFV 1480" % len(dbf))

    # kommunvalkretsnamn, egen lasning
    sh = xlrd.open_workbook(XLS_VALKRETSMANDAT_K).sheet_by_index(0)
    kretsnamn = {}
    for r in range(sh.nrows):
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        if 1480.0 in row:
            kretsnamn["1480%02d" % int(row[4])] = row[5]
    I("kommunvalkretsar ur valkretsmandat_K_2010.xls: %s" % kretsnamn)

    rapport_stick = []
    for val in ("rd", "rf", "kf"):
        print("\n==================== %s ====================" % val)
        hdr, X = xls_rows(XLS[val])
        partikol = xls_partier(val, hdr)
        c_gilt, c_rostande, c_rostb, c_vdt = (hdr.index(n) for n in ("Rost Giltiga", "Rostande", "Rostb", "VDT"))
        c_bl = hdr.index("BL tal") if "BL tal" in hdr else (hdr.index("BLANK tal") if "BLANK tal" in hdr else hdr.index("BLANK"))
        c_og = hdr.index("OG tal") if "OG tal" in hdr else hdr.index("OG")
        kommun, XM = xml_lasa(val)
        r_xls = read_csv("roster_2010_%s_xls.csv" % val)
        r_xml = read_csv("roster_2010_%s_xml.csv" % val)
        dist = read_csv("distrikt_2010_%s.csv" % val)
        agg = read_csv("aggregat_2010_%s.csv" % val)
        fg = read_csv("fgval_2010_%s.csv" % val)
        fgd = read_csv("fgval_2010_%s_deltagande.csv" % val)

        # (4) koder
        for fn, rows in (("roster_xls", r_xls), ("roster_xml", r_xml), ("distrikt", dist)):
            bad = [r["kod"] for r in rows if not re.fullmatch(r"\d{8}", r["kod"])]
            if bad:
                F("%s %s: koder som inte ar 8 siffror: %s" % (val, fn, sorted(set(bad))[:10]))
        for fn, rows in (("fgval", fg), ("fgval_deltagande", fgd)):
            bad = [r["kod_2010"] for r in rows if not re.fullmatch(r"\d{8}", r["kod_2010"])]
            if bad:
                F("%s %s: koder som inte ar 8 siffror: %s" % (val, fn, sorted(set(bad))[:10]))
        koder_dist = [r["kod"] for r in dist]
        geo = [k for k in koder_dist if not k.startswith("148000")]
        if len(koder_dist) != len(set(koder_dist)):
            F("%s distrikt: dubbletter i kod" % val)
        if set(geo) != set(dbf):
            F("%s distrikt: geografiska koder skiljer fran dbf: bara csv %s bara dbf %s" % (val, sorted(set(geo) - set(dbf)), sorted(set(dbf) - set(geo))))
        else:
            I("%s: %d geografiska distrikt + %d onsdagsdistrikt, koder = dbf (%d)" % (val, len(geo), len(koder_dist) - len(geo), len(dbf)))
        namnfel = [(r["kod"], r["namn"], dbf[r["kod"]]) for r in dist if r["kod"] in dbf and r["namn"] != dbf[r["kod"]]]
        if namnfel:
            F("%s distrikt: namn skiljer fran dbf: %s" % (val, namnfel[:5]))
        if set(X) != set(koder_dist):
            F("%s: xls-koder (egen lasning) skiljer fran distriktfilen: %s / %s" % (val, sorted(set(X) - set(koder_dist)), sorted(set(koder_dist) - set(X))))
        if set(XM) != set(koder_dist):
            F("%s: xml-koder skiljer fran distriktfilen" % val)
        if len(set(r["kod"] for r in r_xls)) != len(koder_dist) or len(set(r["kod"] for r in r_xml)) != len(koder_dist):
            F("%s: roster-filerna har annat antal distrikt an distriktfilen" % val)

        # (1) totaler per parti ur xls, egen lasning
        tot_xls = defaultdict(int)
        for kod, d in X.items():
            for c, p in partikol:
                v = d["celler"][c]
                if v != "":
                    tot_xls[p] += int(v)
        tot_csv_xls = defaultdict(int)
        for r in r_xls:
            tot_csv_xls[r["parti_kalla"]] += int(r["roster"])
        tot_csv_xml = defaultdict(int)
        for r in r_xml:
            tot_csv_xml[r["parti_kalla"]] += int(r["roster"])
        agg_gbg = {r["parti_kalla"]: r for r in agg if r["niva"] == "goteborg"}
        for p, v in sorted(tot_xls.items()):
            if tot_csv_xls.get(p) != v:
                F("%s total %s: egen xls-summa %d, roster_xls.csv %s" % (val, p, v, tot_csv_xls.get(p)))
            if p in ("OVR", "ÖVR"):
                ovr_xml = sum(v2 for p2, v2 in tot_csv_xml.items() if p2 not in tot_xls)
                if ovr_xml != v:
                    F("%s total %s: xls %d, xml ovriga+handskrivna %d" % (val, p, v, ovr_xml))
                if p in agg_gbg:
                    F("%s aggregat goteborg har rad %s" % (val, p))
                continue
            if tot_csv_xml.get(p) != v:
                F("%s total %s: egen xls-summa %d, roster_xml.csv %s" % (val, p, v, tot_csv_xml.get(p)))
            if p not in agg_gbg:
                F("%s aggregat goteborg saknar %s" % (val, p))
            elif int(agg_gbg[p]["roster"]) != v:
                F("%s total %s: egen xls-summa %d, aggregat goteborg %s" % (val, p, v, agg_gbg[p]["roster"]))
        I("%s: %d partier i xls, Goteborgstotaler kontrollerade mot roster_xls, roster_xml och aggregat: %s" % (val, len(tot_xls), dict(sorted(tot_xls.items()))))
        # aggregat goteborg mot XML kommun-noden, egen lasning
        xp = xml_partier(kommun)
        for p, el in xp.items():
            if p not in agg_gbg or agg_gbg[p]["roster"] != el.get("RÖSTER"):
                F("%s aggregat goteborg %s: csv %s xml %s" % (val, p, agg_gbg.get(p, {}).get("roster"), el.get("RÖSTER")))
        for p in agg_gbg:
            if p not in xp and p not in ("BLANK", "OG"):
                F("%s aggregat goteborg har parti %s som inte finns i XML KOMMUN" % (val, p))
        # totaler ur distriktfilen
        s_gilt = sum(int(r["giltiga"]) for r in dist)
        s_rost = sum(int(r["rostande"]) for r in dist)
        s_rostb = sum(int(r["rostberattigade"]) for r in dist if r["rostberattigade"] != "")
        s_bl = sum(int(r["blanka"]) for r in dist)
        s_og = sum(int(r["ogiltiga_ovriga"]) for r in dist)
        g = list(agg_gbg.values())[0]
        if s_gilt != int(g["giltiga"]) or s_rost != int(g["rostande"]) or s_rostb != int(g["rostberattigade"]):
            F("%s distriktsumma giltiga/rostande/rostb %d/%d/%d, aggregat goteborg %s/%s/%s" % (val, s_gilt, s_rost, s_rostb, g["giltiga"], g["rostande"], g["rostberattigade"]))
        else:
            I("%s: summa distrikt giltiga %d rostande %d rostberattigade %d = aggregat goteborg" % (val, s_gilt, s_rost, s_rostb))
        if agg_gbg.get("BLANK") and int(agg_gbg["BLANK"]["roster"]) != s_bl:
            F("%s blanka summa %d, aggregat %s" % (val, s_bl, agg_gbg["BLANK"]["roster"]))
        if agg_gbg.get("OG") and int(agg_gbg["OG"]["roster"]) != s_og:
            F("%s og summa %d, aggregat %s" % (val, s_og, agg_gbg["OG"]["roster"]))
        # giltiga i xls egen lasning
        s_gilt_xls = sum(int(d["celler"][c_gilt]) for d in X.values())
        if s_gilt_xls != s_gilt:
            F("%s: summa Rost Giltiga i xls %d, distriktfil %d" % (val, s_gilt_xls, s_gilt))

        # (2) per distrikt
        sum_xls = defaultdict(int)
        for r in r_xls:
            sum_xls[r["kod"]] += int(r["roster"])
        sum_xml = defaultdict(int)
        for r in r_xml:
            sum_xml[r["kod"]] += int(r["roster"])
        n_vdt = 0
        for r in dist:
            k = r["kod"]
            gi, bl, og, ogt, ro = (int(r[x]) for x in ("giltiga", "blanka", "ogiltiga_ovriga", "ogiltiga", "rostande"))
            if sum_xls[k] != gi:
                F("%s %s: summa partier roster_xls %d, giltiga %d" % (val, k, sum_xls[k], gi))
            if sum_xml[k] != gi:
                F("%s %s: summa partier roster_xml %d, giltiga %d" % (val, k, sum_xml[k], gi))
            if bl + og != ogt:
                F("%s %s: blanka+ogiltiga_ovriga %d != ogiltiga %d" % (val, k, bl + og, ogt))
            if gi + ogt != ro:
                F("%s %s: giltiga+ogiltiga %d != rostande %d" % (val, k, gi + ogt, ro))
            if r["rostberattigade"] != "":
                rb = int(r["rostberattigade"])
                vdt = float(r["valdeltagande"])
                if abs(round(100.0 * ro / rb, 2) - vdt) > 0.011:
                    F("%s %s: valdeltagande %s, rostande/rostb = %.3f" % (val, k, vdt, 100.0 * ro / rb))
                n_vdt += 1
            elif not k.startswith("148000"):
                F("%s %s: rostberattigade tomt for geografiskt distrikt" % (val, k))
            if r["valkrets"] != kretsnamn[XM[k][0]]:
                F("%s %s: valkrets %r, XML krets %s = %r" % (val, k, r["valkrets"], XM[k][0], kretsnamn[XM[k][0]]))
            # egen xls-lasning mot distriktfilen
            d = X[k]["celler"]
            for namn, c, v in (("giltiga", c_gilt, gi), ("blanka", c_bl, bl), ("ogiltiga_ovriga", c_og, og), ("rostande", c_rostande, ro)):
                if int(d[c]) != v:
                    F("%s %s: %s csv %d, xls-cell %s" % (val, k, namn, v, d[c]))
            if r["rostberattigade"] != "" and int(d[c_rostb]) != int(r["rostberattigade"]):
                F("%s %s: rostb csv %s xls %s" % (val, k, r["rostberattigade"], d[c_rostb]))
            if r["rostberattigade"] != "" and abs(float(d[c_vdt]) - float(r["valdeltagande"])) > 1e-9:
                F("%s %s: vdt csv %s xls %s" % (val, k, r["valdeltagande"], d[c_vdt]))
        I("%s: %d distrikt kontrollerade (partisumma, ogiltiga, rostande, valdeltagande, valkrets, xls-celler)" % (val, len(dist)))
        # andel = roster/giltiga
        gilt = {r["kod"]: int(r["giltiga"]) for r in dist}
        n_andel = 0
        ovr_andel = []
        for fn, rows in (("roster_xls", r_xls), ("roster_xml", r_xml)):
            for r in rows:
                if r["andel"] == "":
                    F("%s %s %s %s: andel tom" % (val, fn, r["kod"], r["parti_kalla"]))
                    continue
                a = float(r["andel"])
                b = 100.0 * int(r["roster"]) / gilt[r["kod"]]
                if abs(round(b, 2) - a) > 0.011:
                    if r["parti_kalla"] in ("OVR", "ÖVR"):
                        ovr_andel.append("%s %s %s: OVR-andel i xls %s, roster/giltiga %.3f (roster %s, giltiga %d)" % (val, fn, r["kod"], a, b, r["roster"], gilt[r["kod"]]))
                    else:
                        F("%s %s %s %s: andel %s, roster/giltiga %.3f" % (val, fn, r["kod"], r["parti_kalla"], a, b))
                n_andel += 1
        I("%s: %d andel-varden kontrollerade mot roster/giltiga (avrundat till 2 decimaler); OVR/ÖVR-andel i xls avviker for %d rader: %s" % (val, n_andel, len(ovr_andel), ovr_andel))

        # (3) xls mot xml per distrikt och parti (ur csv-filerna) och egen xls-lasning mot csv
        mx = {(r["kod"], r["parti_kalla"]): r for r in r_xml}
        ms = {(r["kod"], r["parti_kalla"]): r for r in r_xls}
        n = 0
        nollrader = []
        for (k, p), r in ms.items():
            if p in ("OVR", "ÖVR"):
                ovr = sum(int(r2["roster"]) for (k2, p2), r2 in mx.items() if k2 == k and (k, p2) not in ms)
                if ovr != int(r["roster"]):
                    F("%s %s %s: xls %s, xml summa ovriga %d" % (val, k, p, r["roster"], ovr))
                continue
            if (k, p) not in mx:
                if int(r["roster"]) != 0:
                    F("%s %s %s: finns i roster_xls (%s) men inte i roster_xml" % (val, k, p, r["roster"]))
                else:
                    nollrader.append((k, p))
                continue
            if r["roster"] != mx[(k, p)]["roster"] or abs(float(r["andel"]) - float(mx[(k, p)]["andel"])) > 1e-9:
                F("%s %s %s: xls %s/%s xml %s/%s" % (val, k, p, r["roster"], r["andel"], mx[(k, p)]["roster"], mx[(k, p)]["andel"]))
            n += 1
        I("%s: %d (distrikt, parti) lika i roster_xls och roster_xml; OVR/ÖVR = summa ovriga i xml; %d nollrader i xls utan motsvarighet i xml (partier: %s)" % (val, n, len(nollrader), sorted(set(p for _, p in nollrader))))
        # egen xls-lasning mot roster_xls.csv, alla celler
        n = 0
        for k, d in X.items():
            for c, p in partikol:
                v = d["celler"][c]
                if v == "":
                    if (k, p) in ms:
                        F("%s %s %s: tom cell i xls men rad i csv" % (val, k, p))
                    continue
                if (k, p) not in ms:
                    F("%s %s %s: cell %s i xls saknas i csv" % (val, k, p, v))
                elif int(v) != int(ms[(k, p)]["roster"]):
                    F("%s %s %s: xls-cell %s csv %s" % (val, k, p, v, ms[(k, p)]["roster"]))
                else:
                    n += 1
        I("%s: %d partiroster i xls (egen lasning) = roster_xls.csv" % (val, n))
        # xml egen lasning mot roster_xml.csv och fgval
        fgm = {(r["kod_2010"], r["parti"]): r for r in fg}
        n = 0
        for k, (krets, vd) in XM.items():
            xp = xml_partier(vd)
            for p, el in xp.items():
                if (k, p) not in mx or mx[(k, p)]["roster"] != el.get("RÖSTER"):
                    F("%s %s %s: xml %s csv %s" % (val, k, p, el.get("RÖSTER"), mx.get((k, p), {}).get("roster")))
                else:
                    n += 1
                pn = {"FP": "L"}.get(p, p.upper())
                if (k, pn) not in fgm:
                    F("%s fgval saknar %s %s" % (val, k, pn))
                elif fgm[(k, pn)]["roster_2010"] != el.get("RÖSTER") or fgm[(k, pn)]["roster_fgval"] != (el.get("RÖSTER_FGVAL") or ""):
                    F("%s fgval %s %s: csv %s/%s xml %s/%s" % (val, k, pn, fgm[(k, pn)]["roster_2010"], fgm[(k, pn)]["roster_fgval"], el.get("RÖSTER"), el.get("RÖSTER_FGVAL")))
            for p in [p for (k2, p) in mx if k2 == k]:
                if p not in xp:
                    F("%s %s %s: i roster_xml men inte i XML" % (val, k, p))
        I("%s: %d partiroster i XML (egen lasning) = roster_xml.csv, fgval roster_2010/roster_fgval = XML" % (val, n))

        # aggregat: intern konsistens
        for niva in sorted(set(r["niva"] for r in agg)):
            rows = [r for r in agg if r["niva"] == niva]
            parti = [r for r in rows if r["parti_kalla"] not in ("BLANK", "OG")]
            og = {r["parti_kalla"]: int(r["roster"]) for r in rows if r["parti_kalla"] in ("BLANK", "OG")}
            gi = int(rows[0]["giltiga"])
            ro = int(rows[0]["rostande"])
            s = sum(int(r["roster"]) for r in parti)
            if s != gi:
                F("%s aggregat %s: summa partier %d != giltiga %d" % (val, niva, s, gi))
            if gi + og.get("BLANK", 0) + og.get("OG", 0) != ro:
                F("%s aggregat %s: giltiga+blank+og %d != rostande %d" % (val, niva, gi + og.get("BLANK", 0) + og.get("OG", 0), ro))
            for r in parti:
                if abs(round(100.0 * int(r["roster"]) / gi, 2) - float(r["andel"])) > 0.011:
                    F("%s aggregat %s %s: andel %s, roster/giltiga %.3f" % (val, niva, r["parti_kalla"], r["andel"], 100.0 * int(r["roster"]) / gi))
            for r in rows:
                if r["parti_kalla"] in ("BLANK", "OG") and abs(round(100.0 * int(r["roster"]) / ro, 2) - float(r["andel"])) > 0.011:
                    F("%s aggregat %s %s: andel %s, roster/rostande %.3f" % (val, niva, r["parti_kalla"], r["andel"], 100.0 * int(r["roster"]) / ro))
            if niva.startswith("Göteborg, "):
                dd = [r for r in dist if r["valkrets"] == niva]
                if sum(int(r["giltiga"]) for r in dd) != gi or sum(int(r["rostande"]) for r in dd) != ro:
                    F("%s aggregat %s: distriktsumma giltiga %d/rostande %d != %d/%d" % (val, niva, sum(int(r["giltiga"]) for r in dd), sum(int(r["rostande"]) for r in dd), gi, ro))
                tp = defaultdict(int)
                for r in r_xml:
                    if r["kod"] in {x["kod"] for x in dd}:
                        tp[r["parti_kalla"]] += int(r["roster"])
                for r in parti:
                    if tp.get(r["parti_kalla"], 0) != int(r["roster"]):
                        F("%s aggregat %s %s: %s, distriktsumma %d" % (val, niva, r["parti_kalla"], r["roster"], tp.get(r["parti_kalla"], 0)))
        I("%s: aggregat internt konsistent (partisumma = giltiga, giltiga+blank+og = rostande, andel, valkretsar = distriktsummor): nivaer %s" % (val, sorted(set(r["niva"] for r in agg))))

        # fgval_deltagande mot XML egen lasning
        fgdm = {r["kod_2010"]: r for r in fgd}
        for k, (krets, vd) in XM.items():
            v = vd.find("VALDELTAGANDE")
            if v is None:
                v = etree.Element("VALDELTAGANDE")
            r = fgdm[k]
            exp = [vd.get("RÖSTER") or "", vd.get("RÖSTER_FGVAL") or "", v.get("SUMMA_RÖSTER") or "", v.get("SUMMA_RÖSTER_FGVAL") or "",
                   v.get("RÖSTBERÄTTIGADE") or "", v.get("RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL") or "", vd.get("INDELNING") or ""]
            got = [r["giltiga_2010"], r["giltiga_fgval"], r["rostande_2010"], r["rostande_fgval"], r["rostberattigade_2010"], r["rostberattigade_fgval"], r["indelning"]]
            if exp != got:
                F("%s fgval_deltagande %s: csv %s xml %s" % (val, k, got, exp))
        mod = [k for k, r in fgdm.items() if r["indelning"]]
        I("%s: fgval_deltagande = XML for alla %d distrikt; %d med INDELNING: %s" % (val, len(fgdm), len(mod), sorted(mod)))
        # kommun-nodens FGVAL
        kv = kommun.find("VALDELTAGANDE")
        I("%s: KOMMUN RÖSTER_FGVAL=%s SUMMA_RÖSTER_FGVAL=%s RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL=%s KLARA_VALDISTRIKT=%s" % (
            val, kommun.get("RÖSTER_FGVAL"), kv.get("SUMMA_RÖSTER_FGVAL"), kv.get("RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL"), kommun.get("KLARA_VALDISTRIKT")))

        # (5) stickprov: tre Majornadistrikt, tre partier, mot racell
        for kod in random.sample(MAJORNA, 3):
            d = X[kod]
            for c, p in random.sample(partikol[:8], 3):
                v = d["celler"][c]
                csvv = ms.get((kod, p), {}).get("roster")
                ok = v != "" and int(v) == int(csvv)
                line = "%s %s %s: %s flik %r rad %d kolumn %s (%r) = %s, csv %s -> %s" % (
                    val, kod, p, os.path.basename(XLS[val]), d["flik"], d["rad"], col_letter(c), hdr[c], v, csvv, "lika" if ok else "OLIKA")
                rapport_stick.append(line)
                if not ok:
                    F("stickprov " + line)
        # kf: procentfilen
        if val == "kf":
            hp, XP = xls_rows(XLS_K_PROCENT)
            if hp != hdr:
                F("kf: K_procent har andra rubriker an K_antal")
            for k, d in XP.items():
                for c, p in partikol:
                    v = d["celler"][c]
                    if v == "":
                        continue
                    if abs(float(v) - float(ms[(k, p)]["andel"])) > 1e-9:
                        F("kf %s %s: K_procent-cell %s csv andel %s" % (k, p, v, ms[(k, p)]["andel"]))
            I("kf: alla procentceller i K_procent.xls = andel i roster_kf_xls.csv")

    print("\n==================== riket ur kommuner_R.xls ====================")
    sh = xlrd.open_workbook(XLS_KOMMUNER_R).sheet_by_index(0)
    hdr = [sh.cell_value(0, c) for c in range(sh.ncols)]
    tot = defaultdict(float)
    n = 0
    for r in range(1, sh.nrows):
        if sh.cell_value(r, 0) == "" or not isinstance(sh.cell_value(r, 0), float):
            continue
        n += 1
        for c, h in enumerate(hdr):
            if isinstance(h, str) and (h.endswith(" tal") or h in ("Rost Giltiga", "Rostande", "Rostb")):
                v = sh.cell_value(r, c)
                if v != "":
                    tot[h] += float(v)
    agg = read_csv("aggregat_2010_rd.csv")
    riket = {r["parti_kalla"]: r for r in agg if r["niva"] == "riket"}
    I("kommuner_R.xls: %d kommunrader summerade" % n)
    for h, v in sorted(tot.items()):
        p = h[:-4] if h.endswith(" tal") else h
        if p in ("OVR", "BL", "OG"):
            continue
        if p in riket and int(riket[p]["roster"]) != int(v):
            F("riket rd %s: summa kommuner_R.xls %d, aggregat riket %s" % (p, v, riket[p]["roster"]))
    g = list(riket.values())[0]
    for h, key in (("Rost Giltiga", "giltiga"), ("Rostande", "rostande"), ("Rostb", "rostberattigade")):
        if int(tot[h]) != int(g[key]):
            F("riket rd %s: summa kommuner_R.xls %d, aggregat riket %s" % (h, tot[h], g[key]))
    I("riket rd: partier och giltiga/rostande/rostb i aggregat = summa av alla kommuner i kommuner_R.xls")

    print("\n==================== mandat ====================")
    m = read_csv("mandat_2010_riksdag.csv")
    rik = [r for r in m if r["niva"] == "riket"]
    s = sum(int(r["mandat"]) for r in rik if r["mandat"])
    if s != 349:
        F("mandat riket summa %d" % s)
    gbg = [r for r in m if r["kod"] == "1416"]
    s = sum(int(r["mandat"]) for r in gbg if r["mandat"])
    u = sum(int(r["varav_utjamning"]) for r in gbg if r["varav_utjamning"])
    I("mandat: riket 349, Goteborg 1416 %d mandat varav %d utjamning, mandat_valkrets %s; %s" % (
        s, u, gbg[0]["mandat_valkrets"], [(r["parti"], r["mandat"], r["varav_utjamning"]) for r in gbg if r["mandat"] and r["mandat"] != "0"]))
    vk = defaultdict(int)
    for r in m:
        if r["niva"] == "valkrets" and r["mandat"]:
            vk[r["kod"]] += int(r["mandat"])
    if sum(vk.values()) != 349 or len(vk) != 29:
        F("mandat valkretsar: %d kretsar, summa %d" % (len(vk), sum(vk.values())))
    tomma = sorted(set(r["kod"] for r in m if r["niva"] == "valkrets" and not r["namn"]))
    if tomma:
        F("mandat: valkretsar utan namn %s" % tomma)

    print("\n==================== partier_2010 ====================")
    pt = read_csv("partier_2010.csv")
    for val in ("rd", "rf", "kf"):
        kanda = {r["parti_kalla"] for r in pt if r["val"] == val}
        anv = {r["parti_kalla"] for r in read_csv("roster_2010_%s_xml.csv" % val)} | {r["parti_kalla"] for r in read_csv("roster_2010_%s_xls.csv" % val)}
        saknas = sorted(anv - kanda - {"HANDSKRIVNA", "OVR", "ÖVR"})
        if saknas:
            F("%s: partikoder i roster utan rad i partier_2010: %s" % (val, saknas))
        I("%s: partikoder i bruk %s" % (val, sorted(anv)))

    print("\n==================== (6) fgval mot 2006 ====================")
    fg_rapport = []
    for val, valfil in (("rd", "rd"), ("rf", "rf"), ("kf", "kf")):
        cand = sorted(glob.glob(DATA + "roster_2006_%s*.csv" % valfil))
        if not cand:
            I("%s: inga 2006-filer i data/historik, fgval-kontroll far goras senare" % val)
            continue
        src = cand[0]
        r06 = read_csv(os.path.basename(src))
        d06f = glob.glob(DATA + "distrikt_2006_%s*.csv" % valfil)
        d06 = {r["kod"]: r for r in read_csv(os.path.basename(d06f[0]))} if d06f else {}
        by06 = defaultdict(dict)
        namn06 = {}
        for r in r06:
            by06[r["kod"]][r["parti"]] = int(r["roster"])
            namn06[r["kod"]] = r["namn"]
        fg = read_csv("fgval_2010_%s.csv" % val)
        fgd = {r["kod_2010"]: r for r in read_csv("fgval_2010_%s_deltagande.csv" % val)}
        by10 = defaultdict(dict)
        for r in fg:
            if r["roster_fgval"] != "":
                by10[r["kod_2010"]][r["parti"]] = int(r["roster_fgval"])
        stora = ["M", "C", "L", "KD", "S", "V", "MP", "SD"]
        for kod in ["14800911", "14800913", "14800932", "14800934", "14800942"]:
            v10 = by10.get(kod, {})
            vec = tuple(v10.get(p) for p in stora)
            tr = [k for k, d in by06.items() if tuple(d.get(p) for p in stora) == vec]
            extra = ""
            if len(tr) == 1 and d06:
                dd = d06[tr[0]]
                fd = fgd[kod]
                extra = "; deltagande fgval giltiga/rostande/rostb %s/%s/%s, 2006-fil %s/%s/%s" % (
                    fd["giltiga_fgval"], fd["rostande_fgval"], fd["rostberattigade_fgval"], dd["giltiga"], dd["rostande"], dd["rostberattigade"])
                alla06 = by06[tr[0]]
                diff = {p: (v10.get(p), alla06.get(p)) for p in set(v10) | set(alla06) if v10.get(p) != alla06.get(p)}
                extra += "; ovriga partier lika" if not diff else "; skiljer for %s" % diff
            line = "%s %s: FGVAL %s -> 2006-distrikt med samma tal: %s%s" % (val, kod, dict(zip(stora, vec)), [(t, namn06[t]) for t in tr], extra)
            fg_rapport.append(line)
            print(line)
            if len(tr) != 1:
                F("fgval %s %s: %d traffar i 2006-filen (%s)" % (val, kod, len(tr), os.path.basename(src)))

    with open(SCRATCH + "granskning_2010_rapport.txt", "w", encoding="utf-8") as f:
        f.write("INFO\n" + "\n".join(info) + "\n\nSTICKPROV\n" + "\n".join(rapport_stick) + "\n\nFGVAL\n" + "\n".join(fg_rapport) + "\n\nFEL (%d)\n" % len(fel) + "\n".join(fel) + "\n")
    print("\nSTICKPROV")
    for l in rapport_stick:
        print("  " + l)
    print("\nFEL: %d" % len(fel))
    for f_ in fel:
        print("  " + f_)


if __name__ == "__main__":
    main()
