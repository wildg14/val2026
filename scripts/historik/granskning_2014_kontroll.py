#!/usr/bin/env python3
"""granskning_2014: oberoende granskning av v2014-agentens filer för valet 2014.

Läser källfilerna själv (Excel R/L/K, XML 1480R/L/K och 00R/L/K, dbf 2014)
med egen kod och jämför mot data/historik/*2014*.csv. Skriver ingenting till
data/historik, bara till stdout. Alla avvikelser skrivs med kod och tal.

Körs med scratchpad-venv (xlrd, openpyxl, dbfread):
  venv/bin/python scripts/historik/granskning_2014_kontroll.py
"""
import csv
import os
import random
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

import openpyxl
import xlrd
from dbfread import DBF

KALLA_DIR = "/Users/daniel/code/Temp/Historiska dokument"
XLS_R = os.path.join(KALLA_DIR, "2014_riksdagsval_per_valdistrikt.xls")
XLS_L = os.path.join(KALLA_DIR, "2014_landstingsval_per_valdistrikt.xls")
XLSX_K = os.path.join(KALLA_DIR, "2014_kommunval_per_valdistrikt.xlsx")
SCRATCH = ("/private/tmp/claude-501/-Users-daniel-code-Temp/"
           "f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad")
XML2014 = os.path.join(SCRATCH, "unz/slutresultat")
XML2010 = os.path.join(SCRATCH, "unz/slutresultat__1_")
DBF2014 = os.path.join(SCRATCH, "unz/valgeografi_valdistrikt/valgeografi_valdistrikt.dbf")
UT_DIR = "/Users/daniel/code/Temp/data/historik"

VAL = {"rd": ("R", XLS_R), "rf": ("L", XLS_L), "kf": ("K", XLSX_K)}
NORM = {"FP": "L", "DEM": "D", "KP": "K"}
MAJORNA_2014 = ["14801011", "14801012", "14801013", "14801014", "14801015",
                "14801016", "14801021", "14801031", "14801032", "14801033",
                "14801034", "14801035", "14801036", "14801041", "14801042",
                "14801043", "14801044"]
FEL = []


def fel(msg):
    FEL.append(msg)
    print("FEL:", msg)


def norm(p):
    if p in NORM:
        return NORM[p]
    if p.isdigit():
        return p.zfill(4)
    return p.upper()


def col_letter(idx):
    s = ""
    idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def read_csv(name):
    with open(os.path.join(UT_DIR, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def to_int(v):
    if v is None or v == "":
        return 0
    return int(round(float(v)))


# ---------------------------------------------------------------- Excel
def read_excel(val):
    """Returnerar (hdr, rows) där rows = lista av (excelrad_1baserad, celler)."""
    bokstav, path = VAL[val]
    if path.endswith(".xls"):
        wb = xlrd.open_workbook(path)
        sh = wb.sheet_by_index(0)
        sheet = sh.name
        hdr = [str(sh.cell_value(2, c)).strip() for c in range(sh.ncols)]
        rows = [(r + 1, [sh.cell_value(r, c) for c in range(sh.ncols)])
                for r in range(3, sh.nrows)]
    else:
        wb = openpyxl.load_workbook(path, read_only=True)
        ws = wb[wb.sheetnames[0]]
        sheet = ws.title
        raw = [list(r) for r in ws.iter_rows(values_only=True)]
        hdr = [str(h).strip() if h is not None else "" for h in raw[2]]
        rows = [(i + 1, r) for i, r in enumerate(raw) if i >= 3]
    gbg = []
    for rn, r in rows:
        if to_int(r[0]) == 14 and to_int(r[1]) == 80:
            gbg.append((rn, r))
    return sheet, hdr, gbg


def excel_distrikt(val):
    """Dict kod -> {namn, rad, partier{kalla: (tal, proc)}, giltiga, blank, og, rostande, rostb, vdt}."""
    sheet, hdr, gbg = read_excel(val)
    if val == "rd":
        i_vd, i_namn = hdr.index("VALDIST"), hdr.index("Valdistrikt")
    else:
        i_vd, i_namn = 2, 5
    pcols = [(h[:-4], i, hdr.index(h[:-4] + " proc") if (h[:-4] + " proc") in hdr else None)
             for i, h in enumerate(hdr) if h.endswith(" tal")]
    out = {}
    for rn, r in gbg:
        kod = "1480%04d" % to_int(r[i_vd])
        partier = {}
        for p, i, j in pcols:
            partier[p] = (to_int(r[i]), r[j] if j is not None else None, i, j)
        out[kod] = {
            "namn": str(r[i_namn]).strip(), "rad": rn, "partier": partier,
            "giltiga": to_int(r[hdr.index("Rost Giltiga")]),
            "rostande": to_int(r[hdr.index("Rostande")]),
            "rostb": r[hdr.index("Rostb")], "vdt": r[hdr.index("VDT")],
        }
    return sheet, hdr, out


# ---------------------------------------------------------------- XML
def xml_partier(el):
    rows = {}
    for g in el.findall("GILTIGA"):
        rows[g.get("PARTI")] = g
    ov = el.find("ÖVRIGA_GILTIGA")
    if ov is not None:
        for g in ov.findall("GILTIGA"):
            rows[g.get("PARTI")] = g
        for tag in ("HANDSKRIVNA", "ÖVRIGA_FGVAL"):
            h = ov.find(tag)
            if h is not None:
                rows[tag] = h
    return rows


def xml_distrikt(val):
    root = ET.parse(os.path.join(XML2014, "slutresultat_1480%s.xml" % VAL[val][0])).getroot()
    out = {}
    for d in root.iter("VALDISTRIKT"):
        out[d.get("KOD")] = d
    for d in root.iter("ONSDAGSDISTRIKT"):
        out["1480" + d.get("KOD").split("-")[-1].zfill(4)] = d
    return root, out


def xml_summering(el):
    og = {o.get("TEXT"): int(o.get("RÖSTER")) for o in el.findall("OGILTIGA")}
    vd = el.find("VALDELTAGANDE")
    return {
        "giltiga": int(el.get("RÖSTER")),
        "blanka": og.get("BLANK"), "og": og.get("OG"),
        # ONSDAGSDISTRIKT saknar VALDELTAGANDE; röstande = giltiga + blank + og
        "rostande": int(vd.get("SUMMA_RÖSTER")) if vd is not None
        else int(el.get("RÖSTER")) + og.get("BLANK", 0) + og.get("OG", 0),
        "rostb": int(vd.get("RÖSTBERÄTTIGADE")) if vd is not None else None,
        "vdt": vd.get("PROCENT").replace(",", ".") if vd is not None else None,
    }


# ---------------------------------------------------------------- kontroller
def kontroll_1_totaler(val, xd_excel, root, xd_xml):
    """(1) Göteborgs totaler per parti ur Excel och XML mot aggregat och distrikt."""
    agg = {norm(r["parti_kalla"]): r for r in read_csv("aggregat_2014_%s.csv" % val)
           if r["niva"] == "goteborg"}
    tot_x = defaultdict(int)
    for kod, d in xd_excel.items():
        for p, (n, a, i, j) in d["partier"].items():
            tot_x[p] += n
    kommun = root.find("KOMMUN")
    xp = {p: int(g.get("RÖSTER")) for p, g in xml_partier(kommun).items()}
    # Excel-summa av partier mot aggregat (goteborg = KOMMUN-elementet)
    n = 0
    for p, s in tot_x.items():
        if p in ("OVR", "ÖVR", "BL", "BLANK", "OG"):
            continue
        if norm(p) not in agg:
            if s:
                fel("%s aggregat saknar parti %s (Excel-summa %d)" % (val, p, s))
            continue
        if int(agg[norm(p)]["roster"]) != s:
            fel("%s aggregat goteborg %s: %s, Excel-summa %d" % (val, p, agg[norm(p)]["roster"], s))
        n += 1
    # ÖVR i Excel = XML-partier utanför Excel + HANDSKRIVNA
    excel_p = {norm(p) for p in tot_x}
    rest = sum(v for p, v in xp.items() if norm(p) not in excel_p and p != "ÖVRIGA_FGVAL")
    ovr = tot_x.get("OVR", tot_x.get("ÖVR", 0))
    if ovr != rest:
        fel("%s Excel ÖVR-summa %d, XML övriga+handskrivna %d" % (val, ovr, rest))
    # XML-summa per parti över distrikt = KOMMUN-elementet = aggregat
    summa_xml = defaultdict(int)
    for kod, el in xd_xml.items():
        for p, g in xml_partier(el).items():
            summa_xml[p] += int(g.get("RÖSTER"))
    for p, s in summa_xml.items():
        if xp.get(p) != s:
            fel("%s XML KOMMUN %s=%s men distriktssumma %d" % (val, p, xp.get(p), s))
        if p != "ÖVRIGA_FGVAL" and (norm(p) not in agg or int(agg[norm(p)]["roster"]) != s):
            fel("%s aggregat goteborg %s=%s, XML distriktssumma %d" % (val, p, agg.get(norm(p), {}).get("roster"), s))
    # giltiga, röstande, röstberättigade
    ks = xml_summering(kommun)
    dist = read_csv("distrikt_2014_%s.csv" % val)
    g_sum = sum(int(r["giltiga"]) for r in dist)
    r_sum = sum(int(r["rostande"]) for r in dist)
    b_sum = sum(int(r["rostberattigade"] or 0) for r in dist)
    g_x = sum(d["giltiga"] for d in xd_excel.values())
    r_x = sum(d["rostande"] for d in xd_excel.values())
    b_x = sum(to_int(d["rostb"]) for d in xd_excel.values())
    a0 = next(iter(agg.values()))
    print("%s giltiga: Excel %d, distrikt.csv %d, XML KOMMUN %d, aggregat %s" % (val, g_x, g_sum, ks["giltiga"], a0["giltiga"]))
    print("%s rostande: Excel %d, distrikt.csv %d, XML KOMMUN %d, aggregat %s" % (val, r_x, r_sum, ks["rostande"], a0["rostande"]))
    print("%s rostberattigade: Excel %d, distrikt.csv %d (utan uppsamling), XML KOMMUN %d, aggregat %s" % (val, b_x, b_sum, ks["rostb"], a0["rostberattigade"]))
    if not (g_x == g_sum == ks["giltiga"] == int(a0["giltiga"])):
        fel("%s giltiga-summor skiljer sig" % val)
    if not (r_x == r_sum == ks["rostande"] == int(a0["rostande"])):
        fel("%s rostande-summor skiljer sig" % val)
    if not (b_x == b_sum == ks["rostb"] == int(a0["rostberattigade"])):
        fel("%s rostberattigade-summor skiljer sig (Excel %d, csv %d, XML %d)" % (val, b_x, b_sum, ks["rostb"]))
    # valkretsnivåer i aggregat mot distriktsfilens summor
    agg_all = read_csv("aggregat_2014_%s.csv" % val)
    per_krets = defaultdict(lambda: [0, 0, 0])
    for r in dist:
        k = per_krets[r["valkrets"]]
        k[0] += int(r["giltiga"]); k[1] += int(r["rostande"]); k[2] += int(r["rostberattigade"] or 0)
    for r in agg_all:
        if r["niva"] in per_krets and r["parti_kalla"] == "M":
            k = per_krets[r["niva"]]
            if (int(r["giltiga"]), int(r["rostande"]), int(r["rostberattigade"])) != tuple(k):
                fel("%s aggregat %s giltiga/rostande/rostb %s/%s/%s, distriktssumma %s" % (val, r["niva"], r["giltiga"], r["rostande"], r["rostberattigade"], k))
    # riksnivå mot 00-filen
    root00 = ET.parse(os.path.join(XML2014, "slutresultat_00%s.xml" % VAL[val][0])).getroot()
    nat = root00.find("NATION")
    np_ = {p: int(g.get("RÖSTER")) for p, g in xml_partier(nat).items()}
    for r in agg_all:
        if r["niva"] == "riket" and np_.get(r["parti_kalla"]) != int(r["roster"]):
            fel("%s aggregat riket %s=%s, 00-XML NATION %s" % (val, r["parti_kalla"], r["roster"], np_.get(r["parti_kalla"])))
    lan = [l for l in root00.iter("LÄN") if l.get("KOD") == "14"]
    print("%s 00-XML: NATION RÖSTER %s; LÄN 14: %s" % (val, nat.get("RÖSTER"),
          [(l.get("NAMN"), l.get("RÖSTER"), l.tag) for l in lan]))
    lp = {p: int(g.get("RÖSTER")) for p, g in xml_partier(lan[0]).items()}
    for r in agg_all:
        if r["niva"] == "vgregion" and lp.get(r["parti_kalla"]) != int(r["roster"]):
            fel("%s aggregat vgregion %s=%s, 00-XML LÄN 14 %s" % (val, r["parti_kalla"], r["roster"], lp.get(r["parti_kalla"])))
    print("%s kontroll 1 klar: %d partier jämförda mot aggregat goteborg" % (val, n))


def kontroll_2_aritmetik(val):
    """(2) Per distrikt i CSV-filerna."""
    dist = read_csv("distrikt_2014_%s.csv" % val)
    for src in ("xls", "xml"):
        roster = read_csv("roster_2014_%s_%s.csv" % (val, src))
        s = defaultdict(int)
        for r in roster:
            s[r["kod"]] += int(r["roster"])
        n_fel = 0
        for d in dist:
            if s[d["kod"]] != int(d["giltiga"]):
                n_fel += 1
                fel("%s %s partisumma %d != giltiga %s för %s" % (val, src, s[d["kod"]], d["giltiga"], d["kod"]))
        print("%s roster_%s: partisumma = giltiga i %d av %d distrikt" % (val, src, len(dist) - n_fel, len(dist)))
    n_vdt = n_fel = 0
    for d in dist:
        g, b, o, og, r = (int(d[k]) for k in ("giltiga", "blanka", "ogiltiga_ovriga", "ogiltiga", "rostande"))
        if b + o != og:
            fel("%s %s blanka+ogiltiga_ovriga %d != ogiltiga %d" % (val, d["kod"], b + o, og))
        if g + og != r:
            fel("%s %s giltiga+ogiltiga %d != rostande %d" % (val, d["kod"], g + og, r))
        if d["rostberattigade"]:
            rb = int(d["rostberattigade"])
            calc = round(100.0 * r / rb, 2)
            if abs(calc - float(d["valdeltagande"])) > 0.011:
                n_fel += 1
                fel("%s %s valdeltagande %s, beräknat %.2f (%d/%d)" % (val, d["kod"], d["valdeltagande"], calc, r, rb))
            n_vdt += 1
        elif d["valdeltagande"]:
            fel("%s %s valdeltagande utan röstberättigade" % (val, d["kod"]))
    print("%s distrikt: valdeltagande kontrollerat i %d distrikt, %d avvikelser > 0.01" % (val, n_vdt, n_fel))
    # andel i roster-filerna mot roster/giltiga
    gilt = {d["kod"]: int(d["giltiga"]) for d in dist}
    for src in ("xls", "xml"):
        roster = read_csv("roster_2014_%s_%s.csv" % (val, src))
        n_a = n_f = n_tom = 0
        for r in roster:
            if r["andel"] == "":
                n_tom += 1
                continue
            n_a += 1
            calc = round(100.0 * int(r["roster"]) / gilt[r["kod"]], 2)
            if abs(calc - float(r["andel"])) > 0.011:
                n_f += 1
                if n_f <= 5:
                    fel("%s %s %s %s andel %s, beräknat %.2f" % (val, src, r["kod"], r["parti_kalla"], r["andel"], calc))
        print("%s roster_%s: andel kontrollerad i %d rader, %d tomma, %d avvikelser" % (val, src, n_a, n_tom, n_f))


def kontroll_3_xls_xml(val, xd_excel, xd_xml):
    """(3) Excel mot XML per distrikt och parti, ur källfilerna direkt, och CSV mot CSV."""
    if set(xd_excel) != set(xd_xml):
        fel("%s kodmängd Excel != XML: %s" % (val, sorted(set(xd_excel) ^ set(xd_xml))))
    n = n_fel = 0
    for kod in sorted(xd_excel):
        e, x = xd_excel[kod], xd_xml[kod]
        namn_x = x.get("NAMN")
        if e["namn"] != namn_x:
            fel("%s %s namn Excel '%s' XML '%s'" % (val, kod, e["namn"], namn_x))
        xp = {norm(p): int(g.get("RÖSTER")) for p, g in xml_partier(x).items()}
        ep = {}
        for p, (t, a, i, j) in e["partier"].items():
            if p in ("OVR", "ÖVR", "BL", "BLANK", "OG"):
                continue
            ep[norm(p)] = t
            n += 1
            if xp.get(norm(p), 0) != t:
                n_fel += 1
                fel("%s %s %s Excel %d XML %s" % (val, kod, p, t, xp.get(norm(p))))
        rest = sum(v for p, v in xp.items() if p not in ep and p != "ÖVRIGA_FGVAL")
        ovr = e["partier"].get("OVR", e["partier"].get("ÖVR"))[0]
        if ovr != rest:
            n_fel += 1
            fel("%s %s ÖVR Excel %d XML-rest %d" % (val, kod, ovr, rest))
        xs = xml_summering(x)
        bl = e["partier"].get("BL", e["partier"].get("BLANK"))[0]
        og = e["partier"]["OG"][0]
        if (e["giltiga"], bl, og, e["rostande"]) != (xs["giltiga"], xs["blanka"], xs["og"], xs["rostande"]):
            n_fel += 1
            fel("%s %s giltiga/blank/og/rostande Excel %s XML %s" % (val, kod, (e["giltiga"], bl, og, e["rostande"]), (xs["giltiga"], xs["blanka"], xs["og"], xs["rostande"])))
        if xs["rostb"] is not None:
            if to_int(e["rostb"]) != xs["rostb"]:
                n_fel += 1
                fel("%s %s rostb Excel %s XML %s" % (val, kod, e["rostb"], xs["rostb"]))
            if abs(float(e["vdt"]) - float(xs["vdt"])) > 0.005:
                n_fel += 1
                fel("%s %s vdt Excel %s XML %s" % (val, kod, e["vdt"], xs["vdt"]))
    print("%s källa Excel mot XML: %d partital jämförda i %d distrikt, %d avvikelser" % (val, n, len(xd_excel), n_fel))
    # CSV mot CSV
    a = {(r["kod"], r["parti"]): int(r["roster"]) for r in read_csv("roster_2014_%s_xls.csv" % val)}
    b = {(r["kod"], r["parti"]): int(r["roster"]) for r in read_csv("roster_2014_%s_xml.csv" % val)}
    n_fel = 0
    for k, v in a.items():
        if k[1] == "ÖVR":
            continue
        if b.get(k, 0) != v:
            n_fel += 1
            fel("%s CSV %s %s xls %d xml %s" % (val, k[0], k[1], v, b.get(k)))
    print("%s CSV xls mot xml: %d nycklar, %d avvikelser" % (val, len(a), n_fel))


def kontroll_4_koder(val, xd_excel):
    dbf = {r["VD"]: r["VD_NAMN"] for r in DBF(DBF2014, encoding="latin-1") if r["VD"].startswith("1480")}
    for name in ("roster_2014_%s_xls.csv", "roster_2014_%s_xml.csv", "distrikt_2014_%s.csv"):
        rows = read_csv(name % val)
        bad = [r["kod"] for r in rows if not (len(r["kod"]) == 8 and r["kod"].isdigit())]
        if bad:
            fel("%s koder ej 8 siffror: %s" % (name % val, bad[:5]))
    for name in ("fgval_2014_%s.csv",):
        rows = read_csv(name % val)
        bad = [r["kod_2014"] for r in rows if not (len(r["kod_2014"]) == 8 and r["kod_2014"].isdigit())]
        if bad:
            fel("%s koder ej 8 siffror: %s" % (name % val, bad[:5]))
    dist = {r["kod"]: r["namn"] for r in read_csv("distrikt_2014_%s.csv" % val)}
    vanliga = {k: v for k, v in dist.items() if not k.startswith("148000")}
    if set(vanliga) != set(dbf):
        fel("%s distriktskoder != dbf 2014: %s" % (val, sorted(set(vanliga) ^ set(dbf))))
    namnfel = [k for k in dbf if dbf[k] != vanliga.get(k)]
    if namnfel:
        fel("%s namn skiljer mot dbf: %s" % (val, namnfel[:5]))
    print("%s koder: %d i distrikt.csv (%d vanliga + %d uppsamling), dbf 2014 Göteborg %d, namn lika: %s" % (
        val, len(dist), len(vanliga), len(dist) - len(vanliga), len(dbf), not namnfel))
    # råtexten: koderna ska vara citerade eller rena strängar utan .0
    with open(os.path.join(UT_DIR, "distrikt_2014_%s.csv" % val), encoding="utf-8") as f:
        f.readline()
        l = f.readline()
    print("%s rå rad 2: %s" % (val, l.strip()[:60]))


def kontroll_5_stickprov(val, sheet, hdr, xd_excel, rng):
    koder = rng.sample(MAJORNA_2014, 3)
    roster = {(r["kod"], r["parti_kalla"]): r for r in read_csv("roster_2014_%s_xls.csv" % val)}
    for kod in koder:
        e = xd_excel[kod]
        partier = [p for p in e["partier"] if p not in ("OVR", "ÖVR", "BL", "BLANK", "OG") and e["partier"][p][0] > 0]
        for p in rng.sample(partier, 3):
            t, a, i, j = e["partier"][p]
            csv_r = roster.get((kod, p))
            ok = csv_r is not None and int(csv_r["roster"]) == t
            print("  stickprov %s %s %s: fil %s flik '%s' rad %d kolumn %s (%s) = %s; CSV roster %s andel %s; källcell proc %s -> %s" % (
                val, kod, p, os.path.basename(VAL[val][1]), sheet, e["rad"], col_letter(i), hdr[i], t,
                csv_r["roster"] if csv_r else None, csv_r["andel"] if csv_r else None, a, "OK" if ok else "FEL"))
            if not ok:
                fel("%s stickprov %s %s: cell %s, CSV %s" % (val, kod, p, t, csv_r))


def kontroll_6_fgval(val, rng):
    """FGVAL för Majornadistrikt mot 2010-agentens filer via fgval_matchning."""
    ar = "2010"
    fg = defaultdict(dict)
    for r in read_csv("fgval_2014_%s.csv" % val):
        fg[r["kod_2014"]][r["parti"]] = (int(r["roster_2014"]), int(r["roster_fgval"]), r["ar_fg"])
    match = {r["kod_2014"]: r for r in read_csv("fgval_matchning_2010_2014.csv") if r["val"] == ("rd" if val == "rd" else "kf")}
    r2010 = defaultdict(dict)
    for r in read_csv("roster_2010_%s_xml.csv" % val):
        r2010[r["kod"]][r["parti"]] = int(r["roster"])
    d2010 = {r["kod"]: r for r in read_csv("distrikt_2010_%s.csv" % val)}
    kand = [k for k in MAJORNA_2014 if k in fg]
    koder = rng.sample(kand, 5)
    for kod in koder:
        m = match[kod]
        k10 = m["kod_2010"]
        n = n_fel = 0
        for p, (r14, rfg, arfg) in fg[kod].items():
            if p in ("GILTIGA", "BLANK", "OG", "SUMMA_RÖSTER", "RÖSTBERÄTTIGADE", "ÖVRIGA_FGVAL", "HANDSKRIVNA"):
                continue
            n += 1
            v10 = r2010[k10].get(p)
            if v10 != rfg:
                n_fel += 1
                fel("%s fgval %s %s: roster_fgval %d, 2010-fil %s %s" % (val, kod, p, rfg, k10, v10))
        g = fg[kod].get("GILTIGA")
        s = fg[kod].get("SUMMA_RÖSTER")
        b = fg[kod].get("RÖSTBERÄTTIGADE")
        d = d2010.get(k10, {})
        ok_g = g and int(d.get("giltiga", -1)) == g[1]
        ok_s = s and int(d.get("rostande", -1)) == s[1]
        ok_b = b and int(d.get("rostberattigade", -1) or -1) == b[1]
        print("  fgval %s %s (%s) -> 2010 %s %s: %d partier, %d avvikelser; GILTIGA fg %s / 2010 %s %s; SUMMA_RÖSTER fg %s / 2010 %s %s; RÖSTB fg %s / 2010 %s %s" % (
            val, kod, m["namn_2014"], k10, m["namn_2010"], n, n_fel,
            g and g[1], d.get("giltiga"), "OK" if ok_g else "AVVIKER",
            s and s[1], d.get("rostande"), "OK" if ok_s else "AVVIKER",
            b and b[1], d.get("rostberattigade"), "OK" if ok_b else "AVVIKER"))
        if not (ok_g and ok_s):
            fel("%s fgval %s summor avviker mot distrikt_2010" % (val, kod))
    return koder


def kontroll_6_fgval_alla(val):
    """Hela FGVAL-filen: alla matchade distrikt mot 2010-filerna, inte bara stickprov."""
    match = {r["kod_2014"]: r for r in read_csv("fgval_matchning_2010_2014.csv") if r["val"] == ("rd" if val == "rd" else "kf") and r["matchning"] == "exakt"}
    r2010 = defaultdict(dict)
    for r in read_csv("roster_2010_%s_xml.csv" % val):
        r2010[r["kod"]][r["parti"]] = int(r["roster"])
    d2010 = {r["kod"]: r for r in read_csv("distrikt_2010_%s.csv" % val)}
    n = n_fel = n_dist = 0
    avv = []
    for r in read_csv("fgval_2014_%s.csv" % val):
        kod = r["kod_2014"]
        if kod not in match:
            continue
        k10 = match[kod]["kod_2010"]
        p = r["parti"]
        if p == "GILTIGA":
            n_dist += 1
            if int(d2010[k10]["giltiga"]) != int(r["roster_fgval"]):
                n_fel += 1; avv.append((kod, p, r["roster_fgval"], d2010[k10]["giltiga"]))
        elif p == "SUMMA_RÖSTER":
            if int(d2010[k10]["rostande"]) != int(r["roster_fgval"]):
                n_fel += 1; avv.append((kod, p, r["roster_fgval"], d2010[k10]["rostande"]))
        elif p == "RÖSTBERÄTTIGADE":
            if (d2010[k10]["rostberattigade"] or "-1") != r["roster_fgval"]:
                n_fel += 1; avv.append((kod, p, r["roster_fgval"], d2010[k10]["rostberattigade"]))
        elif p == "BLANK":
            if int(d2010[k10]["blanka"]) != int(r["roster_fgval"]):
                n_fel += 1; avv.append((kod, p, r["roster_fgval"], d2010[k10]["blanka"]))
        elif p == "OG":
            if int(d2010[k10]["ogiltiga_ovriga"]) != int(r["roster_fgval"]):
                n_fel += 1; avv.append((kod, p, r["roster_fgval"], d2010[k10]["ogiltiga_ovriga"]))
        elif p in ("ÖVRIGA_FGVAL", "HANDSKRIVNA"):
            continue
        else:
            n += 1
            if r2010[k10].get(p) != int(r["roster_fgval"]):
                n_fel += 1; avv.append((kod, p, r["roster_fgval"], r2010[k10].get(p)))
    print("%s fgval alla matchade: %d distrikt, %d partirader, %d avvikelser %s" % (val, n_dist, n, n_fel, avv[:8]))
    return avv


def kontroll_rf_fgval_2011():
    """Belägg för att rf FGVAL är omvalet 2011."""
    root10 = ET.parse(os.path.join(XML2010, "slutresultat_1480L.xml")).getroot()
    root14 = ET.parse(os.path.join(XML2014, "slutresultat_1480L.xml")).getroot()
    k10 = root10.find("KOMMUN"); k14 = root14.find("KOMMUN")
    vd14 = k14.find("VALDELTAGANDE")
    print("rf: 2010 L-XML KOMMUN RÖSTER %s, 2014 L-XML KOMMUN RÖSTER_FGVAL %s, SUMMA_RÖSTER_FGVAL %s, PROCENT_FGVAL %s, RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL %s" % (
        k10.get("RÖSTER"), k14.get("RÖSTER_FGVAL"), vd14.get("SUMMA_RÖSTER_FGVAL"), vd14.get("PROCENT_FGVAL"),
        vd14.get("RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL")))
    p10 = {p: int(g.get("RÖSTER")) for p, g in xml_partier(k10).items()}
    p14 = {p: g.get("RÖSTER_FGVAL") for p, g in xml_partier(k14).items()}
    print("rf: per parti 2010 vs FGVAL i 2014-filen:", {p: (p10.get(p), p14.get(p)) for p in ("M", "S", "V", "MP", "FP", "SD", "VägV", "SPVG")})
    # samma sak i R och K som referens
    for b in ("R", "K"):
        r10 = ET.parse(os.path.join(XML2010, "slutresultat_1480%s.xml" % b)).getroot().find("KOMMUN")
        r14 = ET.parse(os.path.join(XML2014, "slutresultat_1480%s.xml" % b)).getroot().find("KOMMUN")
        print("%s: 2010 KOMMUN RÖSTER %s, 2014 RÖSTER_FGVAL %s" % (b, r10.get("RÖSTER"), r14.get("RÖSTER_FGVAL")))


def kontroll_mandat():
    for name, niva, tot in (("mandat_2014_riksdag.csv", "riket", 349), ("mandat_2014_kf.csv", "goteborg", 81), ("mandat_2014_rf.csv", "vgregion", 149)):
        rows = read_csv(name)
        s = sum(int(r["mandat"]) for r in rows if r["niva"] == niva)
        print("%s: %s mandatsumma %d (förväntat %d)" % (name, niva, s, tot))
        if s != tot:
            fel("%s mandatsumma %d != %d" % (name, s, tot))
        if niva == "riket":
            g = [(r["parti_kalla"], r["mandat"]) for r in rows if r["niva_kod"] == "1416"]
            print("  Göteborgs kommun (1416):", g, "summa", sum(int(m) for _, m in g))
    # valkretssummor kf
    rows = read_csv("mandat_2014_kf.csv")
    per = defaultdict(int)
    for r in rows:
        per[r["niva"]] += int(r["mandat"])
    print("  kf mandat per nivå:", dict(per))


def kontroll_partilista():
    for val in VAL:
        agg = read_csv("aggregat_2014_%s.csv" % val)
        nivaer = defaultdict(set)
        for r in agg:
            nivaer[r["niva"]].add(r["parti_kalla"])
        print("%s aggregat nivåer: %s" % (val, {k: len(v) for k, v in nivaer.items()}))
        # partier i roster_xml med andel tom
        roster = read_csv("roster_2014_%s_xml.csv" % val)
        tom = [r for r in roster if r["andel"] == ""]
        print("%s roster_xml rader med tom andel: %d (%s)" % (val, len(tom), sorted({r["parti_kalla"] for r in tom})))


def main():
    rng = random.Random(2014)
    for val in VAL:
        print("\n==== %s ====" % val)
        sheet, hdr, xd_excel = excel_distrikt(val)
        root, xd_xml = xml_distrikt(val)
        print("%s Excel Göteborg: %d rader; XML: %d distrikt" % (val, len(xd_excel), len(xd_xml)))
        kontroll_1_totaler(val, xd_excel, root, xd_xml)
        kontroll_2_aritmetik(val)
        kontroll_3_xls_xml(val, xd_excel, xd_xml)
        kontroll_4_koder(val, xd_excel)
        kontroll_5_stickprov(val, sheet, hdr, xd_excel, rng)
        if val in ("rd", "kf"):
            kontroll_6_fgval(val, rng)
            kontroll_6_fgval_alla(val)
    print("\n==== övrigt ====")
    kontroll_rf_fgval_2011()
    kontroll_mandat()
    kontroll_partilista()
    print("\nAntal fel:", len(FEL))
    for f in FEL:
        print(" -", f)


if __name__ == "__main__":
    main()
