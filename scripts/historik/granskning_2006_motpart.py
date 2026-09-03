#!/usr/bin/env python
"""granskning_2006_motpart: oberoende kontroll av val2006-agentens filer.

Laser kallfilerna (XML 1480R/L/K, 00R/L/K, xls per valdistrikt, dbf ur
shapefilen) med egen kod och jamfor med de skrivna CSV-filerna i
data/historik/. Skriver inget till data/, bara en rapport till stdout och
till scratchpad/granskning_2006_motpart.txt.

Kor: <venv>/bin/python scripts/historik/granskning_2006_motpart.py
"""
import csv
import os
import random
import re
import sys
from collections import defaultdict

import xlrd
from dbfread import DBF
from lxml import etree

SCRATCH = "/private/tmp/claude-501/-Users-daniel-code-Temp/f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad"
DL2006 = os.path.join(SCRATCH, "dl2006")
XLS = {"rd": os.path.join(DL2006, "unz", "riksdagen_i_valdistrikt.xls"),
       "rf": os.path.join(DL2006, "unz", "landstingen_i_valdistrikt.xls"),
       "kf": os.path.join(DL2006, "unz", "kommunerna_i_valdistrikt_14.xls")}
XLS_KOMMUNER_RD = os.path.join(DL2006, "unz", "riksdagen_i_kommuner.xls")
XML_1480 = {"rd": os.path.join(DL2006, "slutresultat_1480R.xml"),
            "rf": os.path.join(DL2006, "slutresultat_1480L.xml"),
            "kf": os.path.join(DL2006, "slutresultat_1480K.xml")}
XML_00 = {"rd": os.path.join(DL2006, "slutresultat_00R.xml"),
          "rf": os.path.join(DL2006, "slutresultat_00L.xml"),
          "kf": os.path.join(DL2006, "slutresultat_00K.xml")}
DBF_RD = os.path.join(SCRATCH, "unz", "riksdagen_i_valdistrikt", "riksdagen_i_valdistrikt.dbf")
SHP_RD = os.path.join(SCRATCH, "unz", "riksdagen_i_valdistrikt", "riksdagen_i_valdistrikt.shp")

PROJEKT = "/Users/daniel/code/Temp"
UT = os.path.join(PROJEKT, "data", "historik")
KOMMUN = "1480"
XLS2XML = {"FI": "Fi", "PP": "0524", "SJVP": "Sjvåp"}
NORM = {"FP": "L", "DEM": "D", "KP": "K"}
MAJORNA = ["14808401", "14808402", "14808403", "14808404", "14808405", "14808406", "14808407",
           "14808501", "14808502", "14808503", "14808504", "14808505", "14808506"]

fel = []      # avvikelser som bor rattas eller rapporteras
info = []     # observationer
ok = []       # godkanda kontroller


def norm(p):
    return NORM.get(p.upper(), p.upper())


def las_csv(name):
    with open(os.path.join(UT, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def xml_root(path):
    parser = etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False)
    return etree.parse(path, parser).getroot()


def partier_i(el):
    """{parti: roster} for el: egna GILTIGA plus VARAV_OVRIGA; ÖVR-rest som ÖVR.
    Returnerar aven {parti: procent}."""
    d = {}
    a = {}
    for g in el.findall("GILTIGA"):
        p = g.get("PARTI")
        r = int(g.get("RÖSTER"))
        if p == "ÖVR":
            s = 0
            for v in g.findall("VARAV_ÖVRIGA"):
                d[v.get("PARTI")] = d.get(v.get("PARTI"), 0) + int(v.get("RÖSTER"))
                a[v.get("PARTI")] = v.get("PROCENT", "").replace(",", ".")
                s += int(v.get("RÖSTER"))
            if s != r:
                d["ÖVR"] = r - s
                a["ÖVR"] = g.get("PROCENT", "").replace(",", ".") if s == 0 else ""
        else:
            d[p] = r
            a[p] = g.get("PROCENT", "").replace(",", ".")
    return d, a


def ogiltiga_i(el):
    return {o.get("TEXT"): int(o.get("RÖSTER")) for o in el.findall("OGILTIGA")}


# --------------------------------------------------------------------------
# 1. Egen lasning av XML per distrikt och kommun
# --------------------------------------------------------------------------
xml = {}       # val -> kod -> dict
xml_kommun = {}
xml_krets = {}
for val, path in XML_1480.items():
    root = xml_root(path)
    kommun = root.find("KOMMUN")
    xml_kommun[val] = {"partier": partier_i(kommun)[0], "og": ogiltiga_i(kommun),
                       "giltiga": int(kommun.get("RÖSTER")),
                       "vd": kommun.find("VALDELTAGANDE").attrib,
                       "fgval": {g.get("PARTI"): g.get("RÖSTER_FGVAL") for g in kommun.findall("GILTIGA")},
                       "fgval_sum": kommun.get("RÖSTER_FGVAL")}
    xml[val] = {}
    xml_krets[val] = {}
    for krets in kommun.findall("KRETS_KOMMUN"):
        xml_krets[val][krets.get("NAMN")] = {"partier": partier_i(krets)[0], "og": ogiltiga_i(krets),
                                             "giltiga": int(krets.get("RÖSTER")),
                                             "fgval": {g.get("PARTI"): g.get("RÖSTER_FGVAL") for g in krets.findall("GILTIGA")}}
        for vd in list(krets.findall("VALDISTRIKT")) + list(krets.findall("ONSDAGSDISTRIKT")):
            kod = vd.get("KOD")
            onsdag = vd.tag == "ONSDAGSDISTRIKT"
            kod_x = KOMMUN + "VK" + kod[-2:] if onsdag else kod
            p, a = partier_i(vd)
            v = vd.find("VALDELTAGANDE")
            xml[val][kod_x] = {"namn": vd.get("NAMN"), "krets": krets.get("NAMN"), "onsdag": onsdag,
                               "partier": p, "andel": a, "og": ogiltiga_i(vd),
                               "giltiga": int(vd.get("RÖSTER")),
                               "fgval": {g.get("PARTI"): g.get("RÖSTER_FGVAL") for g in vd.findall("GILTIGA") if g.get("RÖSTER_FGVAL")},
                               "indelning": vd.get("INDELNING"),
                               "rostb": int(v.get("RÖSTBERÄTTIGADE")) if v is not None else None,
                               "rostande": int(v.get("SUMMA_RÖSTER")) if v is not None else None,
                               "vdt": v.get("PROCENT").replace(",", ".") if v is not None else None}
    n_vd = sum(1 for d in xml[val].values() if not d["onsdag"])
    n_on = sum(1 for d in xml[val].values() if d["onsdag"])
    info.append(f"XML {val}: {n_vd} valdistrikt och {n_on} onsdagsdistrikt i 1480")

# --------------------------------------------------------------------------
# 2. Egen lasning av xls, jamforelse XML mot xls per distrikt och parti
# --------------------------------------------------------------------------
xls = {}
xls_pos = {}   # val -> kod -> (radindex, {kolumn: kolindex})
for val, path in XLS.items():
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    hdr = [str(c.value) for c in sh.row(0)]
    col = {h: i for i, h in enumerate(hdr)}
    xls[val] = {}
    for r in range(1, sh.nrows):
        row = sh.row(r)
        kod = str(row[0].value).strip()
        if not kod.startswith(KOMMUN):
            continue
        d = {"namn": str(row[1].value).strip(), "rad": r, "blad": sh.name}
        for h in hdr[2:]:
            v = row[col[h]].value
            d[h] = v
        xls[val][kod] = d
        xls_pos.setdefault(val, {})[kod] = (r, col)
    if set(xls[val]) != set(xml[val]):
        fel.append(f"{val}: koder skiljer sig xls/XML: {set(xls[val]) ^ set(xml[val])}")
    else:
        ok.append(f"{val}: samma {len(xls[val])} koder i xls och XML")
    n = 0
    for kod, x in xls[val].items():
        d = xml[val][kod]
        for h in hdr:
            if not h.endswith("_ROST") or h in ("ÖVR_ROST", "BLANK_ROST", "TOT_ROST"):
                continue
            p = h[:-5]
            if x[h] == "":
                continue
            xp = XLS2XML.get(p, p)
            n += 1
            if int(x[h]) != d["partier"].get(xp, 0):
                fel.append(f"{val} {kod} {p}: xls {int(x[h])} != XML {xp} {d['partier'].get(xp)}")
            # andel
            xa = f"{float(x[p + '_PROC']):.2f}"
            if xa != d["andel"].get(xp):
                fel.append(f"{val} {kod} {p}: xls andel {xa} != XML {d['andel'].get(xp)}")
        # summor
        tot = int(x["TOT_ROST"])
        if tot != d["giltiga"] + d["og"].get("BLANK", 0) + d["og"].get("OG", 0):
            fel.append(f"{val} {kod}: TOT_ROST {tot} != XML giltiga+blank+og")
        if int(x["BLANK_ROST"]) != d["og"].get("BLANK", 0):
            fel.append(f"{val} {kod}: BLANK_ROST != XML BLANK")
        if not d["onsdag"]:
            if int(x["ROSTB"]) != d["rostb"]:
                fel.append(f"{val} {kod}: ROSTB {x['ROSTB']} != XML {d['rostb']}")
            if d["namn"] != x["namn"]:
                fel.append(f"{val} {kod}: namn xls '{x['namn']}' != XML '{d['namn']}'")
        # partisumma i xls = giltiga
        s = sum(int(x[h]) for h in hdr if h.endswith("_ROST") and h not in ("BLANK_ROST", "TOT_ROST") and x[h] != "")
        if s != d["giltiga"]:
            fel.append(f"{val} {kod}: summa xls-partier inkl ÖVR {s} != XML giltiga {d['giltiga']}")
    ok.append(f"{val}: {n} partivarden xls mot XML jamforda (egen lasning)")

# --------------------------------------------------------------------------
# 3. Egen lasning av dbf, jamforelse med xls (rd)
# --------------------------------------------------------------------------
dbf = [rec for rec in DBF(DBF_RD, encoding="latin-1", load=False) if str(rec["Lkfv"]).startswith(KOMMUN)]
dbf_koder = {str(r["Lkfv"]).strip() for r in dbf}
xml_vd_koder = {k for k, d in xml["rd"].items() if not d["onsdag"]}
if dbf_koder != xml_vd_koder:
    fel.append(f"dbf-koder != XML-valdistrikt: {dbf_koder ^ xml_vd_koder}")
else:
    ok.append(f"dbf: {len(dbf)} poster for 1480, samma koder som XML:s valdistrikt (utan onsdagsdistrikt)")
n = 0
for rec in dbf:
    kod = str(rec["Lkfv"]).strip()
    x = xls["rd"][kod]
    for h in x:
        if h.endswith("_ROST") or h == "ROSTB":
            n += 1
            if int(x[h]) != int(rec[h]):
                fel.append(f"dbf {kod} {h}: {rec[h]} != xls {x[h]}")
ok.append(f"dbf: {n} varden jamforda med xls rd")
# shapefile geometrier
try:
    import shapefile
    sf = shapefile.Reader(SHP_RD, encoding="latin-1")
    n_shp = sum(1 for r in sf.iterRecords() if str(r[0]).startswith(KOMMUN))
    info.append(f"shapefile 2006: {n_shp} geometrier med Lkfv 1480xxxx, {len(sf)} totalt i riket")
    if n_shp != 279:
        fel.append(f"shapefile: {n_shp} Goteborgsdistrikt, forvantat 279")
except Exception as e:  # noqa
    info.append(f"pyshp kunde inte lasa shp: {e}")

# --------------------------------------------------------------------------
# 4. Kontroll av de skrivna CSV-filerna
# --------------------------------------------------------------------------
for val in ("rd", "rf", "kf"):
    r_xml = las_csv(f"roster_2006_{val}_xml.csv")
    r_xls = las_csv(f"roster_2006_{val}_xls.csv")
    dist = las_csv(f"distrikt_2006_{val}.csv")
    agg = las_csv(f"aggregat_2006_{val}.csv")

    # koder
    for name, rows in (("roster_xml", r_xml), ("roster_xls", r_xls), ("distrikt", dist)):
        koder = {r["kod"] for r in rows}
        bad = [k for k in koder if not re.fullmatch(r"\d{8}", k)]
        if bad:
            info.append(f"{val} {name}: {len(bad)} koder som inte ar 8 siffror: {sorted(bad)}")
        if len({k for k in koder if re.fullmatch(r'\d{8}', k)}) != 279:
            fel.append(f"{val} {name}: {len(koder)} distinkta koder, ej 279 8-siffriga")
        for r in rows:
            if r["ar"] != "2006" or r["val"] != val:
                fel.append(f"{val} {name}: fel ar/val i rad {r}")
                break

    # distrikt: giltiga = summa roster_xml; giltiga+ogiltiga = rostande; vdt
    by_kod = defaultdict(int)
    by_kod_xls = defaultdict(int)
    for r in r_xml:
        by_kod[r["kod"]] += int(r["roster"])
    for r in r_xls:
        by_kod_xls[r["kod"]] += int(r["roster"])
    n_vdt = 0
    for r in dist:
        kod = r["kod"]
        g = int(r["giltiga"])
        if by_kod[kod] != g:
            fel.append(f"{val} distrikt {kod}: summa roster_xml {by_kod[kod]} != giltiga {g}")
        if by_kod_xls[kod] != g:
            fel.append(f"{val} distrikt {kod}: summa roster_xls {by_kod_xls[kod]} != giltiga {g}")
        if int(r["blanka"]) + int(r["ogiltiga_ovriga"]) != int(r["ogiltiga"]):
            fel.append(f"{val} distrikt {kod}: blanka+og != ogiltiga")
        if g + int(r["ogiltiga"]) != int(r["rostande"]):
            fel.append(f"{val} distrikt {kod}: giltiga+ogiltiga {g + int(r['ogiltiga'])} != rostande {r['rostande']}")
        if r["rostberattigade"]:
            v = round(int(r["rostande"]) / int(r["rostberattigade"]) * 100, 2)
            if abs(v - float(r["valdeltagande"])) > 0.011:
                fel.append(f"{val} distrikt {kod}: valdeltagande {r['valdeltagande']} != beraknat {v:.2f}")
            n_vdt += 1
        # mot egen XML-lasning
        d = xml[val][kod]
        if d["giltiga"] != g or d["og"].get("BLANK", 0) != int(r["blanka"]) or d["og"].get("OG", 0) != int(r["ogiltiga_ovriga"]):
            fel.append(f"{val} distrikt {kod}: giltiga/blank/og skiljer sig fran egen XML-lasning")
        if d["rostb"] is not None and (d["rostb"] != int(r["rostberattigade"]) or d["rostande"] != int(r["rostande"]) or d["vdt"] != r["valdeltagande"]):
            fel.append(f"{val} distrikt {kod}: rostb/rostande/vdt skiljer sig fran egen XML-lasning")
        if d["namn"] != r["namn"] or d["krets"] != r["valkrets"]:
            fel.append(f"{val} distrikt {kod}: namn/valkrets skiljer sig fran XML")
    ok.append(f"{val} distrikt: {len(dist)} rader, partisumma = giltiga, giltiga+ogiltiga = rostande, valdeltagande omraknat for {n_vdt} rader")

    # roster_xml mot egen XML-lasning, rad for rad
    egen = {(k, p): r for k, d in xml[val].items() for p, r in d["partier"].items()}
    skrivet = {(r["kod"], r["parti_kalla"]): int(r["roster"]) for r in r_xml}
    if egen != skrivet:
        diff = set(egen.items()) ^ set(skrivet.items())
        fel.append(f"{val} roster_xml skiljer sig fran egen XML-lasning: {sorted(diff)[:20]}")
    else:
        ok.append(f"{val} roster_xml: alla {len(skrivet)} (kod, parti, roster) lika med egen XML-lasning")
    for r in r_xml:
        if norm(r["parti_kalla"]) != r["parti"]:
            fel.append(f"{val} roster_xml {r['kod']} {r['parti_kalla']}: parti {r['parti']} foljer inte regeln")
            break
        a = xml[val][r["kod"]]["andel"].get(r["parti_kalla"])
        if a != r["andel"]:
            fel.append(f"{val} roster_xml {r['kod']} {r['parti_kalla']}: andel {r['andel']} != XML {a}")
            break

    # roster_xls mot egen xls-lasning (rad, cell)
    n = 0
    for r in r_xls:
        x = xls[val][r["kod"]]
        v = x[r["parti_kalla"] + "_ROST"]
        n += 1
        if v == "" or int(v) != int(r["roster"]):
            fel.append(f"{val} roster_xls {r['kod']} {r['parti_kalla']}: {r['roster']} != cell {v}")
        if f"{float(x[r['parti_kalla'] + '_PROC']):.2f}" != r["andel"]:
            fel.append(f"{val} roster_xls {r['kod']} {r['parti_kalla']}: andel {r['andel']} != cell")
        if norm(r["parti_kalla"]) != r["parti"]:
            fel.append(f"{val} roster_xls {r['kod']} {r['parti_kalla']}: parti {r['parti']}")
    # tomma celler som hoppats over: kontrollera att inga ifyllda celler saknas
    for kod, x in xls[val].items():
        ifyllda = {h[:-5] for h in x if h.endswith("_ROST") and h not in ("BLANK_ROST", "TOT_ROST") and x[h] != ""}
        skrivna = {r["parti_kalla"] for r in r_xls if r["kod"] == kod}
        if ifyllda != skrivna:
            fel.append(f"{val} roster_xls {kod}: partier i xls {ifyllda ^ skrivna} saknas/overskott")
    ok.append(f"{val} roster_xls: {n} rader lika med xls-cellerna (roster och andel)")

    # roster_xls mot roster_xml per distrikt och parti
    xm = defaultdict(dict)
    for r in r_xml:
        xm[r["kod"]][r["parti_kalla"]] = int(r["roster"])
    n = 0
    n_ovr = 0
    for r in r_xls:
        p = r["parti_kalla"]
        if p == "ÖVR":
            # xls OVR = summa av XML-partier som xls inte bryter ut
            xls_partier = {XLS2XML.get(q["parti_kalla"], q["parti_kalla"]) for q in r_xls if q["kod"] == r["kod"] and q["parti_kalla"] != "ÖVR"}
            rest = sum(v for q, v in xm[r["kod"]].items() if q not in xls_partier)
            n_ovr += 1
            if rest != int(r["roster"]):
                fel.append(f"{val} {r['kod']} ÖVR: xls {r['roster']} != XML-rest {rest}")
            continue
        n += 1
        xv = xm[r["kod"]].get(XLS2XML.get(p, p), 0)
        if xv != int(r["roster"]):
            fel.append(f"{val} {r['kod']} {p}: roster_xls {r['roster']} != roster_xml {xv}")
    ok.append(f"{val}: roster_xls mot roster_xml: {n} partivarden och {n_ovr} ÖVR-rester jamforda")

    # aggregat: goteborg = summa distrikt (inkl onsdag) per parti, och = KOMMUN-elementet
    summa = defaultdict(int)
    for r in r_xml:
        summa[r["parti_kalla"]] += int(r["roster"])
    gbg = {r["parti_kalla"]: int(r["roster"]) for r in agg if r["niva"] == "goteborg"}
    for p, v in xml_kommun[val]["partier"].items():
        if gbg.get(p) != v:
            fel.append(f"{val} aggregat goteborg {p}: {gbg.get(p)} != KOMMUN {v}")
        if summa.get(p, 0) != v:
            fel.append(f"{val} summa distrikt {p} {summa.get(p, 0)} != KOMMUN {v}")
    for p in gbg:
        if p not in xml_kommun[val]["partier"] and p not in ("BLANK", "OG"):
            fel.append(f"{val} aggregat goteborg har parti {p} som inte finns i KOMMUN")
    og = xml_kommun[val]["og"]
    if gbg.get("BLANK") != og.get("BLANK") or gbg.get("OG") != og.get("OG"):
        fel.append(f"{val} aggregat goteborg BLANK/OG != KOMMUN")
    sb = sum(int(r["blanka"]) for r in dist)
    so = sum(int(r["ogiltiga_ovriga"]) for r in dist)
    if sb != og.get("BLANK") or so != og.get("OG"):
        fel.append(f"{val} summa distrikt BLANK {sb}/OG {so} != KOMMUN {og}")
    g_rows = [r for r in agg if r["niva"] == "goteborg"]
    vd = xml_kommun[val]["vd"]
    if any(int(r["giltiga"]) != xml_kommun[val]["giltiga"] or int(r["rostande"]) != int(vd["SUMMA_RÖSTER"]) or int(r["rostberattigade"]) != int(vd["RÖSTBERÄTTIGADE"]) for r in g_rows):
        fel.append(f"{val} aggregat goteborg: giltiga/rostande/rostberattigade != KOMMUN")
    sg = sum(int(r["giltiga"]) for r in dist)
    sr = sum(int(r["rostande"]) for r in dist)
    srb = sum(int(r["rostberattigade"]) for r in dist if r["rostberattigade"])
    if sg != xml_kommun[val]["giltiga"] or sr != int(vd["SUMMA_RÖSTER"]):
        fel.append(f"{val}: summa distrikt giltiga {sg} / rostande {sr} != KOMMUN {xml_kommun[val]['giltiga']} / {vd['SUMMA_RÖSTER']}")
    if srb != int(vd["RÖSTBERÄTTIGADE"]):
        info.append(f"{val}: summa rostberattigade over distrikt {srb} mot KOMMUN RÖSTBERÄTTIGADE {vd['RÖSTBERÄTTIGADE']} (KLARA_VALDISTRIKT {vd.get('RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT')})")
    ok.append(f"{val} aggregat goteborg: alla partier, BLANK, OG, giltiga, rostande, rostberattigade lika med KOMMUN och med summan av distrikten")
    # kretsar
    for kn, kd in xml_krets[val].items():
        kr = {r["parti_kalla"]: int(r["roster"]) for r in agg if r["niva"] == kn}
        ds = defaultdict(int)
        for r in r_xml:
            if xml[val][r["kod"]]["krets"] == kn:
                ds[r["parti_kalla"]] += int(r["roster"])
        for p, v in kd["partier"].items():
            if kr.get(p) != v or ds.get(p, 0) != v:
                fel.append(f"{val} aggregat {kn} {p}: agg {kr.get(p)} / distrikt {ds.get(p, 0)} != KRETS {v}")
        if kr.get("BLANK") != kd["og"].get("BLANK") or kr.get("OG") != kd["og"].get("OG"):
            fel.append(f"{val} aggregat {kn}: BLANK/OG != KRETS")
    ok.append(f"{val} aggregat: fyra kretsar lika med KRETS_KOMMUN och med summan av kretsens distrikt")
    # andel i aggregat: roster/giltiga
    for r in agg:
        if r["parti_kalla"] in ("BLANK", "OG"):
            base = int(r["rostande"])
        else:
            base = int(r["giltiga"])
        if r["andel"] and abs(int(r["roster"]) / base * 100 - float(r["andel"])) > 0.011:
            fel.append(f"{val} aggregat {r['niva']} {r['parti_kalla']}: andel {r['andel']} stammer inte med roster/giltiga ({int(r['roster']) / base * 100:.2f})")
    nivaer = sorted({r["niva"] for r in agg})
    info.append(f"{val} aggregat nivaer: {nivaer}")
    # riket och vgregion mot 00-filen
    root00 = xml_root(XML_00[val])
    nation = root00.find("NATION")
    rik = partier_i(nation)[0]
    riket = {r["parti_kalla"]: int(r["roster"]) for r in agg if r["niva"] == "riket" and r["parti_kalla"] not in ("BLANK", "OG")}
    if rik != riket:
        fel.append(f"{val} aggregat riket != NATION: {set(rik.items()) ^ set(riket.items())}")
    lan = [l for l in nation.findall("LÄN") if l.get("KOD") == "14"][0]
    vg = partier_i(lan)[0]
    vgr = {r["parti_kalla"]: int(r["roster"]) for r in agg if r["niva"] == "vgregion" and r["parti_kalla"] not in ("BLANK", "OG")}
    if vg != vgr:
        fel.append(f"{val} aggregat vgregion != LÄN 14: {set(vg.items()) ^ set(vgr.items())}")
    ok.append(f"{val} aggregat riket ({len(riket)} partier) och vgregion ({len(vgr)}) lika med 00-filen")
    # goteborg i 00-filen
    for k in root00.iter("KOMMUN"):
        if k.get("KOD") == KOMMUN:
            if partier_i(k)[0] != xml_kommun[val]["partier"]:
                fel.append(f"{val}: KOMMUN 1480 i 00-filen != 1480-filen")
            break

# riksdagen_i_kommuner.xls
wb = xlrd.open_workbook(XLS_KOMMUNER_RD)
sh = wb.sheet_by_index(0)
hdr = [str(c.value) for c in sh.row(0)]
for r in range(1, sh.nrows):
    row = [c.value for c in sh.row(r)]
    if str(row[0]).strip() == KOMMUN:
        x = dict(zip(hdr, row))
        g = xml_kommun["rd"]
        d = []
        for h in hdr:
            if h.endswith("_ROST") and h not in ("ÖVR_ROST", "BLANK_ROST", "TOT_ROST"):
                p = h[:-5]
                if int(x[h]) != g["partier"].get(XLS2XML.get(p, p), 0):
                    d.append(p)
        if int(x["BLANK_ROST"]) != g["og"]["BLANK"] or int(x["TOT_ROST"]) != int(g["vd"]["SUMMA_RÖSTER"]) or int(x["ROSTB"]) != int(g["vd"]["RÖSTBERÄTTIGADE"]):
            d.append("BLANK/TOT/ROSTB")
        if d:
            fel.append(f"riksdagen_i_kommuner.xls 1480 != XML: {d}")
        else:
            ok.append(f"riksdagen_i_kommuner.xls rad {r}: 1480 lika med XML KOMMUN (partier, BLANK, TOT_ROST {int(x['TOT_ROST'])}, ROSTB {int(x['ROSTB'])})")
        break

# --------------------------------------------------------------------------
# 5. Mandat, partier, indelning
# --------------------------------------------------------------------------
mandat = las_csv("mandat_2006_riksdag.csv")
riket = [r for r in mandat if r["niva"] == "riket"]
s = sum(int(r["mandat"]) for r in riket)
su = sum(int(r["varav_utjamning"]) for r in riket)
s02 = sum(int(r["mandat_2002"]) for r in riket)
kretsar = {r["niva"] for r in mandat if r["niva"] != "riket"}
sk = sum(int(r["mandat"]) for r in mandat if r["niva"] != "riket")
sk_fast = sum(int(r["mandat_totalt"]) for r in mandat if r["niva"] != "riket" and r["parti_kalla"] == "M")
if s != 349 or s02 != 349 or sk != 349:
    fel.append(f"mandat: riket {s}, 2002 {s02}, kretsar {sk}")
else:
    ok.append(f"mandat: riket 349 (utjamning {su}), 2002 349, summa over {len(kretsar)} kretsar 349, fasta mandat over kretsar {sk_fast}")
gbg_m = {r["parti_kalla"]: (r["mandat"], r["varav_utjamning"]) for r in mandat if r["niva"] == "Göteborgs kommun"}
info.append(f"mandat Goteborgs kommun: {gbg_m}")
for r in mandat:
    if norm(r["parti_kalla"]) != r["parti"]:
        fel.append(f"mandat: parti {r['parti']} for {r['parti_kalla']}")
        break

partier = las_csv("partier_2006.csv")
dubb = defaultdict(int)
for r in partier:
    dubb[(r["val"], r["parti_kalla"])] += 1
if any(v > 1 for v in dubb.values()):
    fel.append("partier_2006: dubbletter " + str([k for k, v in dubb.items() if v > 1]))
# alla parti_kalla i roster_xml finns i partier
for val in ("rd", "rf", "kf"):
    pk = {r["parti_kalla"] for r in partier if r["val"] == val}
    rk = {r["parti_kalla"] for r in las_csv(f"roster_2006_{val}_xml.csv")}
    if rk - pk:
        fel.append(f"partier_2006 {val}: saknar {rk - pk}")
ok.append(f"partier_2006: {len(partier)} rader, inga dubbletter, tacker alla partier i roster_xml")

ind = las_csv("distrikt_2006_indelning.csv")
if len(ind) != 279 or {r["kod"] for r in ind} != xml_vd_koder:
    fel.append("distrikt_2006_indelning: koder != 279 XML-valdistrikt")
cnt = defaultdict(int)
for r in ind:
    cnt[(r["indelning_rd"], r["indelning_rf"], r["indelning_kf"])] += 1
    if r["kvk_dbf"] != r["valkrets_kod"][-2:]:
        fel.append(f"indelning {r['kod']}: kvk_dbf {r['kvk_dbf']} != valkrets_kod {r['valkrets_kod']}")
    d = xml["rd"][r["kod"]]
    if (d["indelning"] or "") != r["indelning_rd"] or (xml["rd"][r["kod"]]["fgval"] and False):
        fel.append(f"indelning {r['kod']}: indelning_rd != XML")
info.append(f"indelning kombinationer (rd, rf, kf): {dict(cnt)}")
maj = [r for r in ind if r["kod"] in MAJORNA]
info.append(f"Majorna: {len(maj)} distrikt, valkretsar {sorted({r['valkrets'] for r in maj})}, indelning {sorted({r['indelning_rd'] for r in maj})}")

# --------------------------------------------------------------------------
# 6. Stickprov: tre slumpade Majornadistrikt, tre partital mot racell
# --------------------------------------------------------------------------
random.seed(2006)
stick = []
for kod in random.sample(MAJORNA, 3):
    val = random.choice(["rd", "rf", "kf"])
    r_xls = [r for r in las_csv(f"roster_2006_{val}_xls.csv") if r["kod"] == kod]
    r_xml = {r["parti_kalla"]: int(r["roster"]) for r in las_csv(f"roster_2006_{val}_xml.csv") if r["kod"] == kod}
    rad, col = xls_pos[val][kod]
    wb = xlrd.open_workbook(XLS[val])
    sh = wb.sheet_by_index(0)
    for r in random.sample([q for q in r_xls if q["parti_kalla"] != "ÖVR"], 3):
        h = r["parti_kalla"] + "_ROST"
        c = col[h]
        cell = sh.cell_value(rad, c)
        kol = xlrd.colname(c)
        xp = XLS2XML.get(r["parti_kalla"], r["parti_kalla"])
        st = (f"{kod} {r['namn']} {val} {r['parti_kalla']}: csv {r['roster']}, xls {os.path.basename(XLS[val])} "
              f"blad {sh.name} rad {rad + 1} kolumn {kol} ({h}) = {int(cell)}, XML {xp} = {r_xml.get(xp)}")
        if int(cell) != int(r["roster"]) or r_xml.get(xp) != int(r["roster"]):
            fel.append("stickprov: " + st)
        stick.append(st)

# --------------------------------------------------------------------------
# 7. FGVAL 2002 i 2006-XML mot 2002-agentens filer
# --------------------------------------------------------------------------
fg = []
try:
    a02 = las_csv("aggregat_2002_rd.csv")
    r02 = {v: las_csv(f"roster_2002_{v}.csv") for v in ("rd", "rf", "kf")}
    d02 = {v: las_csv(f"distrikt_2002_{v}.csv") for v in ("rd", "rf", "kf")}
    g02 = {r["parti_kalla"]: int(r["roster"]) for r in a02 if r["niva"] == "goteborg"}
    for p, v in xml_kommun["rd"]["fgval"].items():
        if v is None:
            continue
        m = g02.get(p)
        fg.append(f"goteborg rd {p}: 2006-XML RÖSTER_FGVAL {v}, 2002-fil {m}, {'lika' if m == int(v) else 'OLIKA'}")
    # Goteborg 4 krets 2002 i 2002-filerna?
    k4 = {r["parti_kalla"]: int(r["roster"]) for r in a02 if r["niva"] == "Göteborg 4"}
    for p, v in xml_krets["rd"]["Göteborg 4"]["fgval"].items():
        if v is None:
            continue
        m = k4.get(p)
        fg.append(f"Göteborg 4 rd {p}: FGVAL {v}, 2002-fil {m if k4 else 'saknar niva'}, {'lika' if m == int(v) else 'OLIKA'}")
    for val in ("rd", "rf", "kf"):
        for kod, d in xml[val].items():
            if d["fgval"] and not d["onsdag"]:
                r = {q["parti_kalla"]: int(q["roster"]) for q in r02[val] if q["kod"] == kod}
                dd = [q for q in d02[val] if q["kod"] == kod]
                namn02 = dd[0]["namn"] if dd else "saknas"
                for p, v in d["fgval"].items():
                    m = r.get(p)
                    fg.append(f"{kod} {d['namn']} {val} {p}: FGVAL {v}, 2002-fil ({namn02}) {m}, {'lika' if m == int(v) else 'OLIKA'}")
    # Majorna: finns FGVAL?
    n_maj = sum(1 for k in MAJORNA if xml["rd"][k]["fgval"])
    fg.append(f"Majornadistrikt med RÖSTER_FGVAL i 2006-XML: {n_maj} av 13 (alla Modifierad)")
    # 2002 koder som aterkommer 2006 med annat namn
    n02 = {r["kod"]: r["namn"] for r in d02["rd"]}
    aterbruk = [(k, n02[k], xml["rd"][k]["namn"]) for k in xml_vd_koder if k in n02 and n02[k] != xml["rd"][k]["namn"]]
    lika = [k for k in xml_vd_koder if k in n02 and n02[k] == xml["rd"][k]["namn"]]
    fg.append(f"koder som finns bade 2002 och 2006: {sum(1 for k in xml_vd_koder if k in n02)}, med samma namn {len(lika)}, med annat namn {len(aterbruk)}; exempel {sorted(aterbruk)[:5]}")
except FileNotFoundError as e:
    fg.append(f"2002-filer saknas: {e}")

# --------------------------------------------------------------------------
# Rapport
# --------------------------------------------------------------------------
lines = ["GODKANDA KONTROLLER"] + [" ok  " + x for x in ok]
lines += ["", "OBSERVATIONER"] + [" -   " + x for x in info]
lines += ["", "STICKPROV"] + [" -   " + x for x in stick]
lines += ["", "FGVAL 2002"] + [" -   " + x for x in fg]
lines += ["", f"AVVIKELSER ({len(fel)})"] + [" !!  " + x for x in fel]
txt = "\n".join(lines)
print(txt)
with open(os.path.join(SCRATCH, "granskning_2006_motpart.txt"), "w", encoding="utf-8") as f:
    f.write(txt + "\n")
sys.exit(0)
