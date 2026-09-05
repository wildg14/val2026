#!/usr/bin/env python
"""granskning_2006: oberoende granskning av val2006-agentens filer.

Laser kallfilerna (xls, XML, dbf) med egen kod, raknar om totaler och jamfor
med data/historik/*_2006_*.csv. Skriver en rapport till stdout och till
scratchpad/granskning_2006_rapport.txt. Andrar inga filer.

Kor: <venv>/bin/python scripts/historik/granskning_2006_kontroll.py
"""
import csv
import os
import random
import struct
import sys
from collections import defaultdict, OrderedDict

import xlrd
from dbfread import DBF
from lxml import etree

SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"
DL = os.path.join(SCRATCH, "dl2006")
XLS = {"rd": os.path.join(DL, "unz", "riksdagen_i_valdistrikt.xls"),
       "rf": os.path.join(DL, "unz", "landstingen_i_valdistrikt.xls"),
       "kf": os.path.join(DL, "unz", "kommunerna_i_valdistrikt_14.xls")}
XLS_KOMMUNER = os.path.join(DL, "unz", "riksdagen_i_kommuner.xls")
XML = {"rd": os.path.join(DL, "slutresultat_1480R.xml"),
       "rf": os.path.join(DL, "slutresultat_1480L.xml"),
       "kf": os.path.join(DL, "slutresultat_1480K.xml")}
XML00 = {"rd": os.path.join(DL, "slutresultat_00R.xml"),
         "rf": os.path.join(DL, "slutresultat_00L.xml"),
         "kf": os.path.join(DL, "slutresultat_00K.xml")}
SHP_DIR = os.path.join(SCRATCH, "unz", "riksdagen_i_valdistrikt")
DBF_RD = os.path.join(SHP_DIR, "riksdagen_i_valdistrikt.dbf")
SHP_RD = os.path.join(SHP_DIR, "riksdagen_i_valdistrikt.shp")
UT = "/Users/daniel/code/Temp/data/historik"
RAPPORT = os.path.join(SCRATCH, "granskning_2006_rapport.txt")

XLS2XML = {"FI": "Fi", "PP": "0524", "SJVP": "Sjvåp"}
# 2002-agentens partikoder som avviker fran 2006-XML:s (samma parti)
P2002 = {"SPVG": "SFV", "K": "KPML"}
MAJORNA = ["14808401", "14808402", "14808403", "14808404", "14808405", "14808406", "14808407",
           "14808501", "14808502", "14808503", "14808504", "14808505", "14808506"]

fel = []
ok = []
info = []


def F(m):
    fel.append(m)


def OK(m):
    ok.append(m)


def I(m):
    info.append(m)


def las_csv(name):
    with open(os.path.join(UT, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def col_letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


# --------------------------------------------------------------------------
# Egen lasning av XLS
# --------------------------------------------------------------------------
def las_xls(path):
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    hdr = [str(c.value) for c in sh.row(0)]
    rows = OrderedDict()
    for r in range(1, sh.nrows):
        c0 = sh.cell(r, 0)
        kod = str(c0.value).strip()
        if c0.ctype != xlrd.XL_CELL_TEXT:
            kod = str(int(c0.value)) if c0.ctype == xlrd.XL_CELL_NUMBER else kod
        if not kod.startswith("1480"):
            continue
        rows[kod] = (r, {h: sh.cell(r, i) for i, h in enumerate(hdr)})
    partier = [h[:-5] for h in hdr if h.endswith("_ROST") and h not in ("BLANK_ROST", "TOT_ROST")]
    return sh.name, hdr, rows, partier


# --------------------------------------------------------------------------
# Egen lasning av XML
# --------------------------------------------------------------------------
def las_xml(path):
    parser = etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False)
    return etree.parse(path, parser).getroot()


def giltiga_rader(el):
    """Parti -> roster, med OVR uppdelad i VARAV_OVRIGA och rest som OVR."""
    d = OrderedDict()
    pct = {}
    for g in el.findall("GILTIGA"):
        p = g.get("PARTI")
        r = int(g.get("RÖSTER"))
        if p == "ÖVR":
            s = 0
            for v in g.findall("VARAV_ÖVRIGA"):
                d[v.get("PARTI")] = d.get(v.get("PARTI"), 0) + int(v.get("RÖSTER"))
                pct[v.get("PARTI")] = v.get("PROCENT")
                s += int(v.get("RÖSTER"))
            if s != r:
                d["ÖVR"] = r - s
                pct["ÖVR"] = g.get("PROCENT") if s == 0 else None
        else:
            d[p] = r
            pct[p] = g.get("PROCENT")
    return d, pct


def ogiltiga(el):
    return {o.get("TEXT"): (int(o.get("RÖSTER")), o.get("PROCENT")) for o in el.findall("OGILTIGA")}


def deltagande(el):
    v = el.find("VALDELTAGANDE")
    if v is None:
        return None
    return int(v.get("RÖSTBERÄTTIGADE")), int(v.get("SUMMA_RÖSTER")), v.get("PROCENT")


def p2f(s):
    return None if s in (None, "") else float(s.replace(",", "."))


def main():
    random.seed(20060917)
    # ----------------------------------------------------------------------
    # (1) och (3): egna totaler ur xls och XML, jamfor med agentens filer
    # ----------------------------------------------------------------------
    xls_data = {}
    xml_data = {}
    for val in ("rd", "rf", "kf"):
        sheet, hdr, rows, partier = las_xls(XLS[val])
        xls_data[val] = (sheet, hdr, rows, partier)
        root = las_xml(XML[val])
        kommun = root.find("KOMMUN")
        xd = OrderedDict()
        krets_av = {}
        for krets in kommun.findall("KRETS_KOMMUN"):
            kn = krets.get("NAMN")
            krets_av[kn] = (giltiga_rader(krets)[0], ogiltiga(krets), deltagande(krets), int(krets.get("RÖSTER")), krets)
            for vd in list(krets.findall("VALDISTRIKT")) + list(krets.findall("ONSDAGSDISTRIKT")):
                kod = vd.get("KOD")
                kod_x = "1480VK" + kod[-2:] if vd.tag == "ONSDAGSDISTRIKT" else kod
                g, pct = giltiga_rader(vd)
                xd[kod_x] = dict(kod_xml=kod, namn=vd.get("NAMN"), krets=kn, giltiga=int(vd.get("RÖSTER")),
                                 partier=g, pct=pct, og=ogiltiga(vd), delt=deltagande(vd),
                                 fgval=vd.get("RÖSTER_FGVAL"), fgval_partier={x.get("PARTI"): x.get("RÖSTER_FGVAL") for x in vd.findall("GILTIGA") if x.get("RÖSTER_FGVAL")},
                                 indelning=vd.get("INDELNING"), onsdag=vd.tag == "ONSDAGSDISTRIKT", line=vd.sourceline)
        xml_data[val] = (root, kommun, xd, krets_av)

        # -- xls: totaler per parti for Goteborg
        tot_xls = defaultdict(int)
        for kod, (r, cells) in rows.items():
            for p in partier:
                c = cells[p + "_ROST"]
                if c.ctype == xlrd.XL_CELL_EMPTY or c.value == "":
                    continue
                tot_xls[p] += int(c.value)
        # -- XML: totaler per parti ur distrikten
        tot_xml = defaultdict(int)
        for kod, d in xd.items():
            for p, r in d["partier"].items():
                tot_xml[p] += r
        kom_g, _ = giltiga_rader(kommun)
        if dict(tot_xml) != dict(kom_g):
            F(f"{val}: summa distrikt (egen XML-lasning) != KOMMUN: {set(tot_xml.items()) ^ set(kom_g.items())}")
        else:
            OK(f"{val}: egen summering av {len(xd)} XML-distrikt = KOMMUN 1480 for alla {len(kom_g)} partikoder")
        # -- jamfor med aggregat goteborg
        agg = [r for r in las_csv(f"aggregat_2006_{val}.csv") if r["niva"] == "goteborg"]
        agg_p = {r["parti_kalla"]: int(r["roster"]) for r in agg if r["parti_kalla"] not in ("BLANK", "OG")}
        if agg_p != dict(kom_g):
            F(f"{val}: aggregat goteborg != egen XML KOMMUN: {set(agg_p.items()) ^ set(kom_g.items())}")
        else:
            OK(f"{val}: aggregat_2006_{val}.csv goteborg = egen XML-lasning ({len(agg_p)} partier)")
        # xls-totaler mot aggregat (via mappning)
        diff = []
        for p, r in tot_xls.items():
            if p == "ÖVR":
                continue
            if agg_p.get(XLS2XML.get(p, p)) != r:
                diff.append((p, r, agg_p.get(XLS2XML.get(p, p))))
        if diff:
            F(f"{val}: xls-totaler != aggregat goteborg: {diff}")
        else:
            OK(f"{val}: egen xls-summering av {len(rows)} rader = aggregat goteborg for {len(tot_xls)-1} partier (ÖVR ej jamford)")
        # kontroll av kommun BLANK/OG/deltagande i aggregat
        kom_og = ogiltiga(kommun)
        kom_d = deltagande(kommun)
        for r in agg:
            if r["parti_kalla"] in ("BLANK", "OG"):
                if int(r["roster"]) != kom_og[r["parti_kalla"]][0]:
                    F(f"{val}: aggregat goteborg {r['parti_kalla']} {r['roster']} != XML {kom_og[r['parti_kalla']][0]}")
            if int(r["giltiga"]) != int(kommun.get("RÖSTER")) or int(r["rostande"]) != kom_d[1] or int(r["rostberattigade"]) != kom_d[0]:
                F(f"{val}: aggregat goteborg giltiga/rostande/rostberattigade != XML pa rad {r['parti_kalla']}")
        # kretsar
        for kn, (kg, kog, kd, kgil, _) in krets_av.items():
            a = [r for r in las_csv(f"aggregat_2006_{val}.csv") if r["niva"] == kn]
            ap = {r["parti_kalla"]: int(r["roster"]) for r in a if r["parti_kalla"] not in ("BLANK", "OG")}
            if ap != dict(kg):
                F(f"{val} {kn}: aggregat != egen XML: {set(ap.items()) ^ set(kg.items())}")
            s = defaultdict(int)
            for kod, d in xd.items():
                if d["krets"] == kn:
                    for p, r in d["partier"].items():
                        s[p] += r
            if dict(s) != dict(kg):
                F(f"{val} {kn}: summa distrikt != krets")
        OK(f"{val}: alla 4 kretsar i aggregat = egen XML-lasning, och distrikt summerar till krets")

        # -- roster_xml.csv mot egen XML-lasning, rad for rad
        rx = las_csv(f"roster_2006_{val}_xml.csv")
        rx_d = defaultdict(dict)
        for r in rx:
            rx_d[r["kod"]][r["parti_kalla"]] = (int(r["roster"]), r["andel"])
        n = 0
        for kod, d in xd.items():
            mine = {p: r for p, r in d["partier"].items()}
            theirs = {p: v[0] for p, v in rx_d.get(kod, {}).items()}
            if mine != theirs:
                F(f"{val} roster_xml {kod}: {set(mine.items()) ^ set(theirs.items())}")
            for p, (r, a) in rx_d.get(kod, {}).items():
                exp = d["pct"].get(p)
                exp = "" if exp is None else exp.replace(",", ".")
                if a != exp:
                    F(f"{val} roster_xml {kod} {p}: andel {a} != XML PROCENT {exp}")
                # andel mot roster/giltiga
                if a != "" and d["giltiga"]:
                    calc = 100.0 * r / d["giltiga"]
                    if abs(calc - float(a)) > 0.006:
                        F(f"{val} roster_xml {kod} {p}: andel {a} avviker fran roster/giltiga {calc:.3f}")
                n += 1
        if set(rx_d) != set(xd):
            F(f"{val} roster_xml: distriktsmangd skiljer sig: {set(rx_d) ^ set(xd)}")
        OK(f"{val}: roster_2006_{val}_xml.csv {n} rader = egen XML-lasning (roster och andel, andel = roster/giltiga inom 0.006)")

        # -- roster_xls.csv mot egen xls-lasning
        rxl = las_csv(f"roster_2006_{val}_xls.csv")
        rxl_d = defaultdict(dict)
        for r in rxl:
            rxl_d[r["kod"]][r["parti_kalla"]] = (int(r["roster"]), r["andel"])
        n = 0
        for kod, (ri, cells) in rows.items():
            mine = {}
            for p in partier:
                c = cells[p + "_ROST"]
                if c.ctype == xlrd.XL_CELL_EMPTY or c.value == "":
                    continue
                mine[p] = int(c.value)
                pc = cells[p + "_PROC"].value
                a = rxl_d[kod].get(p, (None, None))[1]
                if a is None or abs(float(a) - float(pc)) > 1e-9:
                    F(f"{val} roster_xls {kod} {p}: andel {a} != xls PROC {pc}")
                n += 1
            theirs = {p: v[0] for p, v in rxl_d.get(kod, {}).items()}
            if mine != theirs:
                F(f"{val} roster_xls {kod}: {set(mine.items()) ^ set(theirs.items())}")
        if set(rxl_d) != set(rows):
            F(f"{val} roster_xls: distriktsmangd skiljer sig: {set(rxl_d) ^ set(rows)}")
        OK(f"{val}: roster_2006_{val}_xls.csv {n} rader = egen xls-lasning (roster och andel)")

        # (3) xls mot XML per distrikt och parti
        n = 0
        for kod, (ri, cells) in rows.items():
            d = xd.get(kod)
            if d is None:
                F(f"{val}: xls-kod {kod} saknas i XML")
                continue
            for p in partier:
                c = cells[p + "_ROST"]
                if c.ctype == xlrd.XL_CELL_EMPTY or c.value == "" or p == "ÖVR":
                    continue
                xp = XLS2XML.get(p, p)
                if d["partier"].get(xp, 0) != int(c.value):
                    F(f"{val} {kod} {p}: xls {int(c.value)} != XML {xp} {d['partier'].get(xp)}")
                n += 1
            # totaler
            tot = int(cells["TOT_ROST"].value)
            xt = d["giltiga"] + d["og"].get("BLANK", (0,))[0] + d["og"].get("OG", (0,))[0]
            if tot != xt:
                F(f"{val} {kod}: TOT_ROST {tot} != XML giltiga+blank+og {xt}")
            if int(cells["BLANK_ROST"].value) != d["og"].get("BLANK", (0,))[0]:
                F(f"{val} {kod}: BLANK_ROST != XML")
            if d["delt"]:
                if int(cells["ROSTB"].value) != d["delt"][0]:
                    F(f"{val} {kod}: ROSTB != XML")
                if abs(float(cells["VDT"].value) - p2f(d["delt"][2])) > 1e-9:
                    F(f"{val} {kod}: VDT {cells['VDT'].value} != XML {d['delt'][2]}")
            # summa xls partier inkl OVR = XML giltiga
            s = sum(int(cells[p + "_ROST"].value) for p in partier if cells[p + "_ROST"].ctype != xlrd.XL_CELL_EMPTY and cells[p + "_ROST"].value != "")
            if s != d["giltiga"]:
                F(f"{val} {kod}: summa xls partikolumner inkl ÖVR {s} != XML giltiga {d['giltiga']}")
        OK(f"{val}: xls mot XML: {n} partivarden lika i alla {len(rows)} distrikt; TOT_ROST, BLANK_ROST, ROSTB, VDT lika; summa xls-kolumner = XML giltiga")

        # (2) distriktsfilens interna samband
        df = las_csv(f"distrikt_2006_{val}.csv")
        n_vdt = 0
        for r in df:
            kod = r["kod"]
            d = xd[kod]
            g, b, o, og, ro = int(r["giltiga"]), int(r["blanka"]), int(r["ogiltiga_ovriga"]), int(r["ogiltiga"]), int(r["rostande"])
            s = sum(rx_d[kod][p][0] for p in rx_d[kod])
            if s != g:
                F(f"{val} distrikt {kod}: summa partiroster {s} != giltiga {g}")
            if b + o != og:
                F(f"{val} distrikt {kod}: blanka+ogiltiga_ovriga != ogiltiga")
            if g + og != ro:
                F(f"{val} distrikt {kod}: giltiga+ogiltiga {g+og} != rostande {ro}")
            if r["rostberattigade"]:
                rb = int(r["rostberattigade"])
                calc = 100.0 * ro / rb
                if abs(calc - float(r["valdeltagande"])) > 0.0051:
                    F(f"{val} distrikt {kod}: valdeltagande {r['valdeltagande']} != rostande/rostberattigade {calc:.3f}")
                n_vdt += 1
            elif not d["onsdag"]:
                F(f"{val} distrikt {kod}: saknar rostberattigade men ar inte onsdagsdistrikt")
            # mot egen XML
            if g != d["giltiga"] or b != d["og"].get("BLANK", (0,))[0] or o != d["og"].get("OG", (0,))[0]:
                F(f"{val} distrikt {kod}: giltiga/blanka/og != egen XML")
            if d["delt"] and (ro != d["delt"][1] or int(r["rostberattigade"]) != d["delt"][0] or r["valdeltagande"] != d["delt"][2].replace(",", ".")):
                F(f"{val} distrikt {kod}: rostande/rostberattigade/valdeltagande != egen XML")
            if r["namn"] != d["namn"] or r["valkrets"] != d["krets"]:
                F(f"{val} distrikt {kod}: namn/valkrets != XML")
        if len(df) != len(xd):
            F(f"{val} distrikt: {len(df)} rader, XML har {len(xd)}")
        OK(f"{val}: distrikt_2006_{val}.csv {len(df)} rader: partisumma = giltiga, giltiga+ogiltiga = rostande, valdeltagande = rostande/rostberattigade (2 dec) for {n_vdt} distrikt; alla falt = egen XML-lasning")

        # aggregat riket/vgregion mot egen lasning av 00-filen
        root00 = las_xml(XML00[val])
        nation = root00.find("NATION")
        lan = [l for l in nation.findall("LÄN") if l.get("KOD") == "14"][0]
        for niva, el in (("riket", nation), ("vgregion", lan)):
            a = [r for r in las_csv(f"aggregat_2006_{val}.csv") if r["niva"] == niva]
            ap = {r["parti_kalla"]: int(r["roster"]) for r in a if r["parti_kalla"] not in ("BLANK", "OG")}
            eg, _ = giltiga_rader(el)
            if ap != dict(eg):
                F(f"{val} {niva}: aggregat != egen 00-lasning: {set(ap.items()) ^ set(eg.items())}")
            eo = ogiltiga(el)
            ed = deltagande(el)
            for r in a:
                if r["parti_kalla"] in ("BLANK", "OG") and int(r["roster"]) != eo[r["parti_kalla"]][0]:
                    F(f"{val} {niva} {r['parti_kalla']}: != XML")
                if int(r["giltiga"]) != int(el.get("RÖSTER")) or int(r["rostande"]) != ed[1] or int(r["rostberattigade"]) != ed[0]:
                    F(f"{val} {niva}: giltiga/rostande/rostberattigade != XML")
            # partisumma = giltiga
            if sum(ap.values()) != int(el.get("RÖSTER")):
                F(f"{val} {niva}: partisumma {sum(ap.values())} != giltiga {el.get('RÖSTER')}")
            if int(el.get("RÖSTER")) + eo["BLANK"][0] + eo["OG"][0] != ed[1]:
                F(f"{val} {niva}: giltiga+blank+og != summa roster i kallan")
            I(f"{val} {niva}: giltiga {el.get('RÖSTER')}, rostande {ed[1]}, rostberattigade {ed[0]}, valdeltagande {ed[2]}, {len(ap)} partier")
        OK(f"{val}: aggregat riket och vgregion = egen lasning av slutresultat_00{val[0].upper() if val != 'rf' else 'L'}.xml")
        # 00-filens kommun 1480 mot 1480-filen
        for k in root00.iter("KOMMUN"):
            if k.get("KOD") == "1480":
                g00, _ = giltiga_rader(k)
                if dict(g00) != dict(kom_g):
                    F(f"{val}: 00-filens KOMMUN 1480 != 1480-filens KOMMUN: {set(g00.items()) ^ set(kom_g.items())}")
                else:
                    OK(f"{val}: 00-filens KOMMUN 1480 = 1480-filens KOMMUN per parti")
                break

    # ----------------------------------------------------------------------
    # riksdagen_i_kommuner.xls
    # ----------------------------------------------------------------------
    wb = xlrd.open_workbook(XLS_KOMMUNER)
    sh = wb.sheet_by_index(0)
    hdr = [str(c.value) for c in sh.row(0)]
    kom_g, _ = giltiga_rader(xml_data["rd"][1])
    for r in range(1, sh.nrows):
        if str(sh.cell(r, 0).value).strip() == "1480":
            row = {h: sh.cell(r, i).value for i, h in enumerate(hdr)}
            diff = [(p, int(row[p + "_ROST"]), kom_g.get(XLS2XML.get(p, p))) for p in [h[:-5] for h in hdr if h.endswith("_ROST")]
                    if p not in ("ÖVR", "BLANK", "TOT") and kom_g.get(XLS2XML.get(p, p)) != int(row[p + "_ROST"])]
            if diff:
                F(f"riksdagen_i_kommuner.xls 1480: {diff}")
            else:
                OK(f"riksdagen_i_kommuner.xls blad {sh.name} rad {r+1} (1480) = XML KOMMUN per parti; TOT_ROST {int(row['TOT_ROST'])}, ROSTB {int(row['ROSTB'])}")
            break

    # ----------------------------------------------------------------------
    # dbf mot xls och XML, shp-antal
    # ----------------------------------------------------------------------
    dbf = DBF(DBF_RD, encoding="latin-1", load=False)
    fields = [f.name for f in dbf.fields]
    recs = {str(rec["Lkfv"]).strip(): rec for rec in dbf if str(rec["Lkfv"]).startswith("1480")}
    sheet, hdr, rows, partier = xls_data["rd"]
    xd = xml_data["rd"][2]
    n = 0
    for kod, rec in recs.items():
        ri, cells = rows[kod]
        for p in partier:
            c = cells[p + "_ROST"]
            if c.ctype == xlrd.XL_CELL_EMPTY or c.value == "":
                if rec[p + "_ROST"] not in (None, 0):
                    F(f"dbf {kod} {p}: dbf {rec[p+'_ROST']} men xls tom")
                continue
            if int(rec[p + "_ROST"]) != int(c.value):
                F(f"dbf {kod} {p}: dbf {rec[p+'_ROST']} != xls {int(c.value)}")
            n += 1
        if int(rec["ROSTB"]) != int(cells["ROSTB"].value) or int(rec["TOT_ROST"]) != int(cells["TOT_ROST"].value) or int(rec["BLANK_ROST"]) != int(cells["BLANK_ROST"].value):
            F(f"dbf {kod}: ROSTB/TOT_ROST/BLANK_ROST != xls")
        if rec["NAMN"].strip() != xd[kod]["namn"]:
            F(f"dbf {kod}: namn '{rec['NAMN']}' != XML '{xd[kod]['namn']}'")
        if rec["KVK_NAMN"].strip() != xd[kod]["krets"]:
            F(f"dbf {kod}: KVK_NAMN != XML krets")
    OK(f"dbf: {len(recs)} poster for 1480, {n} partivarden = xls; ROSTB, TOT_ROST, BLANK_ROST, namn, KVK_NAMN lika")
    with open(SHP_RD, "rb") as f:
        f.seek(24)
        flen = struct.unpack(">i", f.read(4))[0] * 2
        f.seek(100)
        nshp = 0
        pos = 100
        while pos < flen:
            f.seek(pos + 4)
            clen = struct.unpack(">i", f.read(4))[0] * 2
            pos += 8 + clen
            nshp += 1
    I(f"shp: {nshp} geometrier i hela filen, dbf har {len(list(DBF(DBF_RD, encoding='latin-1', load=False)))} poster; Goteborg 1480 i dbf: {len(recs)}")
    # indelningsfilen mot dbf
    ind = las_csv("distrikt_2006_indelning.csv")
    if len(ind) != len(recs):
        F(f"distrikt_2006_indelning.csv har {len(ind)} rader, dbf {len(recs)}")
    for r in ind:
        rec = recs[r["kod"]]
        if r["kvk_dbf"] != rec["KVK"].strip() or r["valkrets"] != rec["KVK_NAMN"].strip():
            F(f"indelning {r['kod']}: kvk != dbf")
        for val in ("rd", "rf", "kf"):
            d = xml_data[val][2][r["kod"]]
            if r["indelning_" + val] != (d["indelning"] or "") or r["giltiga_2002_" + val] != (d["fgval"] or ""):
                F(f"indelning {r['kod']} {val}: indelning/fgval != XML")
    OK(f"distrikt_2006_indelning.csv: {len(ind)} rader = dbf (KVK, KVK_NAMN) och XML (INDELNING, RÖSTER_FGVAL) i alla tre valen")
    from collections import Counter
    I("INDELNING rd: " + str(Counter(r["indelning_rd"] for r in ind)))

    # ----------------------------------------------------------------------
    # (4) koder
    # ----------------------------------------------------------------------
    for name in ["roster_2006_rd_xls.csv", "roster_2006_rd_xml.csv", "roster_2006_rf_xls.csv", "roster_2006_rf_xml.csv",
                 "roster_2006_kf_xls.csv", "roster_2006_kf_xml.csv", "distrikt_2006_rd.csv", "distrikt_2006_rf.csv",
                 "distrikt_2006_kf.csv", "distrikt_2006_indelning.csv"]:
        rows_ = las_csv(name)
        bad = sorted({r["kod"] for r in rows_ if not (len(r["kod"]) == 8 and r["kod"].isdigit())})
        koder = {r["kod"] for r in rows_}
        n8 = len([k for k in koder if k.isdigit()])
        msg = f"{name}: {len(koder)} koder, {n8} attasiffriga, ej attasiffriga: {bad}"
        if bad:
            I(msg)
        else:
            OK(msg)
    # rad ar/val konstanta
    for name in ["roster_2006_rd_xls.csv", "distrikt_2006_kf.csv", "aggregat_2006_rf.csv"]:
        rows_ = las_csv(name)
        if {r["ar"] for r in rows_} != {"2006"} or len({r["val"] for r in rows_}) != 1:
            F(f"{name}: ar/val inte konstanta")

    # ----------------------------------------------------------------------
    # (5) stickprov Majorna mot racell
    # ----------------------------------------------------------------------
    prov = random.sample(MAJORNA, 3)
    for kod in prov:
        val = random.choice(["rd", "rf", "kf"])
        sheet, hdr, rows, partier = xls_data[val]
        ri, cells = rows[kod]
        d = xml_data[val][2][kod]
        ps = random.sample([p for p in partier if p != "ÖVR" and cells[p + "_ROST"].ctype != xlrd.XL_CELL_EMPTY], 3)
        for p in ps:
            ci = hdr.index(p + "_ROST")
            raw = int(cells[p + "_ROST"].value)
            xp = XLS2XML.get(p, p)
            csv_xls = [r for r in las_csv(f"roster_2006_{val}_xls.csv") if r["kod"] == kod and r["parti_kalla"] == p][0]
            csv_xml = [r for r in las_csv(f"roster_2006_{val}_xml.csv") if r["kod"] == kod and r["parti_kalla"] == xp][0]
            status = "OK" if int(csv_xls["roster"]) == raw == int(csv_xml["roster"]) == d["partier"][xp] else "FEL"
            I(f"stickprov {status}: {kod} {d['namn']} {val} {p}: {os.path.basename(XLS[val])} blad '{sheet}' rad {ri+1} kolumn {col_letter(ci)} ({p}_ROST) = {raw}; "
              f"XML {os.path.basename(XML[val])} rad {d['line']} GILTIGA/VARAV_ÖVRIGA PARTI={xp} RÖSTER={d['partier'][xp]}; "
              f"roster_xls.csv {csv_xls['roster']}, roster_xml.csv {csv_xml['roster']}")
            if status == "FEL":
                F(f"stickprov {kod} {p} avviker")

    # ----------------------------------------------------------------------
    # (6) FGVAL 2002 i 2006-XML mot 2002-agentens filer
    # ----------------------------------------------------------------------
    for val in ("rd", "rf", "kf"):
        try:
            r02 = las_csv(f"roster_2002_{val}.csv")
            a02 = las_csv(f"aggregat_2002_{val}.csv")
            d02 = las_csv(f"distrikt_2002_{val}.csv")
        except FileNotFoundError:
            I(f"{val}: 2002-filer saknas, FGVAL-kontroll far goras senare")
            continue
        root, kommun, xd, krets_av = xml_data[val]
        # kommunniva
        a_g = {r["parti_kalla"]: int(r["roster"]) for r in a02 if r["niva"] == "goteborg"}
        a_g.update({p: a_g[q] for p, q in P2002.items() if q in a_g})
        g_tot = {r["giltiga"] for r in a02 if r["niva"] == "goteborg"}
        fg = {g.get("PARTI"): int(g.get("RÖSTER_FGVAL")) for g in kommun.findall("GILTIGA") if g.get("RÖSTER_FGVAL")}
        diff = {p: (fg[p], a_g.get(p)) for p in fg if a_g.get(p) != fg[p]}
        if diff or kommun.get("RÖSTER_FGVAL") not in g_tot:
            F(f"{val} FGVAL kommun: {diff}; RÖSTER_FGVAL {kommun.get('RÖSTER_FGVAL')} vs 2002 giltiga {g_tot}")
        else:
            OK(f"{val}: KOMMUN RÖSTER_FGVAL per parti ({len(fg)} koder inkl ÖVR) och total {kommun.get('RÖSTER_FGVAL')} = aggregat_2002_{val}.csv goteborg")
        # kretsniva
        for kn, (_, _, _, _, krets) in krets_av.items():
            a_k = {r["parti_kalla"]: int(r["roster"]) for r in a02 if r["niva"] in (kn, "valkrets-" + kn)}
            a_k.update({p: a_k[q] for p, q in P2002.items() if q in a_k})
            fgk = {g.get("PARTI"): int(g.get("RÖSTER_FGVAL")) for g in krets.findall("GILTIGA") if g.get("RÖSTER_FGVAL")}
            if not a_k:
                I(f"{val} {kn}: ingen kretsrad i aggregat_2002_{val}.csv, FGVAL {fgk}")
                continue
            diff = {p: (fgk[p], a_k.get(p)) for p in fgk if a_k.get(p) != fgk[p]}
            if diff:
                F(f"{val} FGVAL {kn}: {diff}")
            else:
                OK(f"{val} {kn}: KRETS_KOMMUN RÖSTER_FGVAL per parti = aggregat_2002_{val}.csv")
        # distrikt med FGVAL
        r02d = defaultdict(dict)
        for r in r02:
            r02d[r["kod"]][r["parti_kalla"]] = int(r["roster"])
        for kod in r02d:
            r02d[kod].update({p: r02d[kod][q] for p, q in P2002.items() if q in r02d[kod]})
        d02d = {r["kod"]: r for r in d02}
        n = 0
        for kod, d in xd.items():
            if not d["fgval"]:
                continue
            if d["onsdag"]:
                I(f"{val} {kod} ({d['kod_xml']}): onsdagsdistrikt RÖSTER_FGVAL {d['fgval']}, partier {d['fgval_partier']}; 2002 ej_raknade finns bara per kommun/krets i aggregat_2002")
                continue
            t = r02d.get(kod)
            if not t:
                I(f"{val} {kod} {d['namn']}: FGVAL {d['fgval']} men koden finns inte i roster_2002_{val}.csv")
                continue
            diff = {p: (int(v), t.get(p)) for p, v in d["fgval_partier"].items() if t.get(p) != int(v)}
            if diff or int(d["fgval"]) != int(d02d[kod]["giltiga"]):
                F(f"{val} {kod} {d['namn']} FGVAL: {diff}; total {d['fgval']} vs 2002 giltiga {d02d[kod]['giltiga']} ({d02d[kod]['namn']})")
            else:
                OK(f"{val} {kod} {d['namn']}: RÖSTER_FGVAL {d['fgval']} och {len(d['fgval_partier'])} partital = 2002 {d02d[kod]['namn']} i roster/distrikt_2002_{val}.csv")
            n += 1
        # Majorna: finns FGVAL?
        maj_fg = [k for k in MAJORNA if xd[k]["fgval"]]
        I(f"{val}: Majornadistrikt med RÖSTER_FGVAL: {maj_fg if maj_fg else 'inga (alla Modifierad)'}; kontroll per Majornadistrikt mot 2002 ar darfor inte mojlig i 2006-XML")

    # ----------------------------------------------------------------------
    # mandat, partier
    # ----------------------------------------------------------------------
    m = las_csv("mandat_2006_riksdag.csv")
    riket = [r for r in m if r["niva"] == "riket"]
    s = sum(int(r["mandat"]) for r in riket)
    su = sum(int(r["varav_utjamning"]) for r in riket)
    s02 = sum(int(r["mandat_2002"]) for r in riket)
    kr = [r for r in m if r["niva"] != "riket"]
    sk = sum(int(r["mandat"]) for r in kr)
    fasta = {r["niva"]: int(r["mandat_totalt"]) for r in kr}
    if s != 349 or sk != 349 or s02 != 349 or sum(fasta.values()) + su != 349:
        F(f"mandat: riket {s}, kretsar {sk}, 2002 {s02}, fasta {sum(fasta.values())} + utjamning {su}")
    else:
        OK(f"mandat_2006_riksdag.csv: riket 349, kretsar 349, 2002 349, fasta {sum(fasta.values())} + utjamning {su} = 349, {len(fasta)} valkretsar")
    gbg = [r for r in kr if r["kod"] == "1416"]
    I("mandat Goteborgs kommun 2006: " + ", ".join(f"{r['parti_kalla']} {r['mandat']}({r['varav_utjamning']})" for r in gbg) + f"; fasta {fasta.get('Göteborgs kommun')}")
    pr = las_csv("partier_2006.csv")
    bad = [r for r in pr if r["parti"] != {"FP": "L"}.get(r["parti_kalla"], r["parti_kalla"].upper())]
    if bad:
        F(f"partier_2006.csv: normalisering avviker: {[(r['parti_kalla'], r['parti']) for r in bad]}")
    # samma parti olika kod xls/xml
    I("parti-koder for samma parti: xls FI->FI, XML Fi->FI; xls PP->PP, XML 0524->0524; xls SJVP->SJVP, XML Sjvåp->SJVÅP")
    # aggregat andel BLANK/OG definition
    for val in ("rd",):
        a = [r for r in las_csv(f"aggregat_2006_{val}.csv") if r["niva"] == "goteborg" and r["parti_kalla"] in ("BLANK", "OG")]
        for r in a:
            I(f"aggregat {val} goteborg {r['parti_kalla']}: andel {r['andel']} = roster/rostande {100*int(r['roster'])/int(r['rostande']):.2f}, roster/giltiga {100*int(r['roster'])/int(r['giltiga']):.2f}")

    lines = ["OK"] + [" ok  " + x for x in ok] + ["", "INFO"] + [" i   " + x for x in info] + ["", f"FEL ({len(fel)})"] + [" !!  " + x for x in fel]
    print("\n".join(lines))
    with open(RAPPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
