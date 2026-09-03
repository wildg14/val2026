# -*- coding: utf-8 -*-
"""
granskning_2010_extra.py - kompletterande, oberoende granskning av val2010-filerna
i data/historik/ (andra granskningsvarvet). Tacker det som granskning_2010_kontroll.py
inte gor:

 A. filformat: BOM, radslut, rubriker, 8-siffriga koder, flyttalsartefakter i andel
 B. summan av roster_xml per parti (alla partier, aven smapartier och HANDSKRIVNA)
    mot KOMMUN- och KRETS_KOMMUN-noderna i XML, och summan av fgval roster_fgval
    mot nodernas RÖSTER_FGVAL
 C. aggregat: riket mot summan av LÄN-noderna i 00X.xml, vgregion mot summan av
    kommunerna under LÄN 14 i 00L.xml, goteborg mot KOMMUN-noden i 00X.xml
 D. mandat_2010_riksdag.csv mot mandatfordelning_per_valkrets_R (1).xls for alla 29 valkretsar
 E. 2010 ars distriktstal mot Valmyndighetens FGVAL i 2014 ars XML (fgval_2014_<val>.csv
    fran 2014-delen) - en oberoende omskrivning av 2010 ars resultat
 F. distriktfilens rostberattigade och valdeltagande mot XML VALDELTAGANDE (egen lasning)
 G. stickprov med eget slumpfro: tre Majornadistrikt, tre partier, mot racell i xls
 H. fgval for fem Majornadistrikt mot 2006-delens xls-baserade filer (roster_2006_<val>_xls.csv)

Skriver bara till stdout, andrar inga filer.
Kor med: <venv>/bin/python scripts/historik/granskning_2010_extra.py
"""
import csv
import random
import re
from collections import OrderedDict, defaultdict

import xlrd
from lxml import etree

HIST = "/Users/daniel/code/Temp/Historiska dokument/"
SCRATCH = "/private/tmp/claude-501/-Users-daniel-code-Temp/f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad/"
XML_DIR = SCRATCH + "unz/slutresultat__1_/"
XML_1480 = {"rd": XML_DIR + "slutresultat_1480R.xml", "rf": XML_DIR + "slutresultat_1480L.xml", "kf": XML_DIR + "slutresultat_1480K.xml"}
XML_00 = {"rd": XML_DIR + "slutresultat_00R.xml", "rf": XML_DIR + "slutresultat_00L.xml", "kf": XML_DIR + "slutresultat_00K.xml"}
XLS = {"rd": HIST + "slutligt_valresultat_valdistrikt_R.xls",
       "rf": HIST + "slutligt_valresultat_valdistrikt_L.xls",
       "kf": HIST + "slutligt_valresultat_valdistrikt_K_antal.xls"}
XLS_MANDAT_R = HIST + "mandatfordelning_per_valkrets_R (1).xls"
DATA = "/Users/daniel/code/Temp/data/historik/"
PARSER = etree.XMLParser(load_dtd=False, resolve_entities=False, no_network=True, huge_tree=True)

MAJORNA = ["14800911", "14800912", "14800913", "14800914", "14800915", "14800916", "14800921", "14800931", "14800932",
           "14800933", "14800934", "14800935", "14800936", "14800941", "14800942", "14800943", "14800944"]
STORA = ["M", "C", "L", "KD", "S", "V", "MP", "SD"]
HEADERS = {
    "roster": "ar;val;kod;namn;parti_kalla;parti;roster;andel",
    "distrikt": "ar;val;kod;namn;valkrets;giltiga;blanka;ogiltiga_ovriga;ogiltiga;rostande;rostberattigade;valdeltagande;kalla_fil",
    "aggregat": "ar;val;niva;parti_kalla;parti;roster;andel;giltiga;rostande;rostberattigade",
}

fel = []


def F(msg):
    fel.append(msg)
    print("FEL: " + msg)


def I(msg):
    print("info: " + msg)


def read_csv(name):
    with open(DATA + name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def norm(p):
    if re.fullmatch(r"\d+", p):
        return "%04d" % int(p)
    return {"FP": "L", "DEM": "D", "KP": "K"}.get(p, p.upper())


def col_letter(c):
    s = ""
    c += 1
    while c:
        c, r = divmod(c - 1, 26)
        s = chr(65 + r) + s
    return s


def xml_partier(node):
    """parti_kalla -> element for GILTIGA (direkt och under ÖVRIGA_GILTIGA) och HANDSKRIVNA."""
    out = OrderedDict()
    for ch in node:
        if ch.tag == "GILTIGA":
            out[ch.get("PARTI")] = ch
        elif ch.tag == "ÖVRIGA_GILTIGA":
            for c2 in ch:
                if c2.tag == "GILTIGA":
                    out[c2.get("PARTI")] = c2
                elif c2.tag in ("HANDSKRIVNA", "ÖVRIGA_FGVAL"):
                    out[c2.tag] = c2
    return out


def kontroll_format():
    print("\n== A. filformat")
    filer = sorted(f for f in __import__("os").listdir(DATA) if re.match(r"(roster|distrikt|aggregat|fgval)_2010_.*\.csv$", f) or f in ("mandat_2010_riksdag.csv", "partier_2010.csv"))
    for fn in filer:
        raw = open(DATA + fn, "rb").read()
        if raw.startswith(b"\xef\xbb\xbf"):
            F("%s: BOM" % fn)
        if b"\r" in raw:
            F("%s: CR i filen" % fn)
        try:
            txt = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            F("%s: inte UTF-8: %s" % (fn, e))
            continue
        lines = txt.split("\n")
        typ = fn.split("_")[0]
        if typ in HEADERS and lines[0] != HEADERS[typ]:
            F("%s: rubrik %r, vantat %r" % (fn, lines[0], HEADERS[typ]))
        ncol = lines[0].count(";") + 1
        bad = [i + 1 for i, l in enumerate(lines) if l and l.count(";") + 1 != ncol]
        if bad:
            F("%s: rader med fel antal kolumner: %s" % (fn, bad[:5]))
        # koder
        hdr = lines[0].split(";")
        # mandatfilens kod ar valkretskod (00 eller 4 siffror), inte distriktkod
        kodcols = [i for i, h in enumerate(hdr) if h in ("kod", "kod_2010")] if not fn.startswith("mandat_") else []
        for l in lines[1:]:
            if not l:
                continue
            c = l.split(";")
            for i in kodcols:
                if not re.fullmatch(r"\d{8}", c[i]):
                    F("%s: kod %r ar inte 8 siffror" % (fn, c[i]))
                    break
            # flyttalsartefakter: fler an 2 decimaler eller exponent
            for v in c:
                if re.fullmatch(r"-?\d+\.\d{3,}", v) or re.search(r"[eE][+-]?\d", v) and re.match(r"-?\d", v):
                    F("%s: misstankt flyttal %r i rad %r" % (fn, v, l[:60]))
    I("%d filer kontrollerade for BOM, radslut, rubriker, kolumnantal, koder och decimaler" % len(filer))


def kontroll_xml_summor(val, kommun, krets_nodes, kretsnamn):
    print("\n== B. %s: summor ur roster_xml och fgval mot XML KOMMUN och KRETS_KOMMUN" % val)
    r_xml = read_csv("roster_2010_%s_xml.csv" % val)
    fg = read_csv("fgval_2010_%s.csv" % val)
    dist = {r["kod"]: r for r in read_csv("distrikt_2010_%s.csv" % val)}
    # per parti totalt
    s_xml = defaultdict(int)
    for r in r_xml:
        s_xml[r["parti_kalla"]] += int(r["roster"])
    s_fg = defaultdict(int)
    s_fg10 = defaultdict(int)
    for r in fg:
        if r["roster_fgval"] != "":
            s_fg[r["parti"]] += int(r["roster_fgval"])
        if r["roster_2010"] != "":
            s_fg10[r["parti"]] += int(r["roster_2010"])
    xp = xml_partier(kommun)
    n = 0
    for p, el in xp.items():
        if p == "ÖVRIGA_FGVAL":
            continue
        if s_xml.get(p, 0) != int(el.get("RÖSTER")):
            F("%s KOMMUN %s: summa roster_xml %d, XML RÖSTER %s" % (val, p, s_xml.get(p, 0), el.get("RÖSTER")))
        n += 1
    extra = set(s_xml) - set(xp)
    if extra:
        F("%s: partier i roster_xml som saknas i KOMMUN-noden: %s" % (val, sorted(extra)))
    I("%s: %d partier (inkl. smapartier och HANDSKRIVNA): summa av distrikten i roster_xml = KOMMUN-nodens RÖSTER" % (val, n))
    # fgval-summor mot KOMMUN RÖSTER_FGVAL per parti. Distriktens FGVAL tacker bara
    # distrikt som ar oforandrade sedan 2006 (11 Modifierad-distrikt saknar FGVAL), medan
    # KOMMUN-nodens RÖSTER_FGVAL tacker hela kommunen 2006. Skillnaden ska darfor vara
    # exakt 2006 ars roster i de 2006-distrikt som inte har nagon 2010-motsvarighet
    # (granskning_2010_fgval_koppling_2006.csv, distrikt_2006 och roster_2006 ur 2006-delen).
    try:
        kop = read_csv("granskning_2010_fgval_koppling_2006.csv")
        d06 = read_csv("distrikt_2006_%s.csv" % val)
        r06 = read_csv("roster_2006_%s_xml.csv" % val)
    except FileNotFoundError:
        kop = d06 = r06 = None
    tot_fg = kommun.get("RÖSTER_FGVAL")
    s_all = sum(v for p, v in s_fg.items() if p not in ("BLANK", "OG"))
    gap = {}
    for p, el in xp.items():
        pn = norm(p) if p not in ("HANDSKRIVNA", "ÖVRIGA_FGVAL") else p
        fgv = el.get("RÖSTER_FGVAL")
        if fgv is not None:
            gap[pn] = int(fgv) - s_fg.get(pn, 0)
    if kop is None:
        I("%s: summa roster_fgval %d, KOMMUN RÖSTER_FGVAL %s; 2006-filer saknas, avstamningen far goras senare" % (val, s_all, tot_fg))
    else:
        lankade = {r["kod_2006"] for r in kop if r["val"] == val and r["kod_2006"]}
        olankade = [r for r in d06 if r["kod"] not in lankade and not r["kod"].startswith("1480VK")]
        s_ol = sum(int(r["giltiga"]) for r in olankade)
        if int(tot_fg) - s_all != s_ol:
            F("%s: KOMMUN RÖSTER_FGVAL %s - summa roster_fgval %d = %d, men de %d olankade 2006-distrikten har %d giltiga" % (
                val, tot_fg, s_all, int(tot_fg) - s_all, len(olankade), s_ol))
        else:
            I("%s: KOMMUN RÖSTER_FGVAL %s - summa roster_fgval i distrikten %d = %d = giltiga 2006 i de %d 2006-distrikt utan 2010-motsvarighet (%s)" % (
                val, tot_fg, s_all, s_ol, len(olankade), ", ".join(r["kod"] + " " + r["namn"] for r in olankade)))
        ol_koder = {r["kod"] for r in olankade}
        s06 = defaultdict(int)
        for r in r06:
            if r["kod"] in ol_koder:
                s06[r["parti"]] += int(r["roster"])
        for p in STORA:
            if gap.get(p) != s06.get(p, 0):
                F("%s: FGVAL-gap for %s ar %s men de olankade 2006-distrikten har %d" % (val, p, gap.get(p), s06.get(p, 0)))
        I("%s: gapet per parti (M, C, L, KD, S, V, MP, SD) = de olankade 2006-distriktens roster: %s" % (val, {p: gap.get(p) for p in STORA}))
    # per krets
    for kk in krets_nodes:
        namn = kretsnamn[kk.get("KOD")]
        koder = {k for k, r in dist.items() if r["valkrets"] == namn}
        s = defaultdict(int)
        for r in r_xml:
            if r["kod"] in koder:
                s[r["parti_kalla"]] += int(r["roster"])
        for p, el in xml_partier(kk).items():
            if p == "ÖVRIGA_FGVAL":
                continue
            if s.get(p, 0) != int(el.get("RÖSTER")):
                F("%s krets %s %s: distriktsumma %d, XML %s" % (val, namn, p, s.get(p, 0), el.get("RÖSTER")))
        v = kk.find("VALDELTAGANDE")
        rb = sum(int(dist[k]["rostberattigade"]) for k in koder if dist[k]["rostberattigade"])
        if rb != int(v.get("RÖSTBERÄTTIGADE")):
            F("%s krets %s: summa rostberattigade %d, XML %s" % (val, namn, rb, v.get("RÖSTBERÄTTIGADE")))
    I("%s: alla partier per kommunvalkrets = distriktsummor; rostberattigade per krets = summa av distrikten" % val)


def kontroll_aggregat_00(val, kommun1480):
    print("\n== C. %s: aggregat riket/vgregion/goteborg mot 00-filen" % val)
    agg = read_csv("aggregat_2010_%s.csv" % val)
    root = etree.parse(XML_00[val], PARSER).getroot()
    nation = root.find("NATION")
    lan = nation.findall("LÄN")
    # riket = summa av LÄN
    s = defaultdict(int)
    for l in lan:
        for p, el in xml_partier(l).items():
            if p != "ÖVRIGA_FGVAL":
                s[p] += int(el.get("RÖSTER"))
    riket = {r["parti_kalla"]: r for r in agg if r["niva"] == "riket"}
    for p, v in s.items():
        if p not in riket or int(riket[p]["roster"]) != v:
            F("%s riket %s: summa LÄN %d, aggregat %s" % (val, p, v, riket.get(p, {}).get("roster")))
    rb = sum(int(l.find("VALDELTAGANDE").get("RÖSTBERÄTTIGADE")) for l in lan)
    sr = sum(int(l.find("VALDELTAGANDE").get("SUMMA_RÖSTER")) for l in lan)
    g = list(riket.values())[0]
    if rb != int(g["rostberattigade"]) or sr != int(g["rostande"]):
        F("%s riket: summa LÄN rostb/rostande %d/%d, aggregat %s/%s" % (val, rb, sr, g["rostberattigade"], g["rostande"]))
    I("%s: riket i aggregat = summa av %d LÄN-noder for %d partier samt rostande och rostberattigade" % (val, len(lan), len(s)))
    # goteborg i 00-filen
    kommuner = {k.get("KOD"): k for k in nation.iter("KOMMUN")}
    gbg = kommuner.get("1480")
    if gbg is None:
        F("%s: KOMMUN 1480 saknas i 00-filen" % val)
    else:
        goteborg = {r["parti_kalla"]: r for r in agg if r["niva"] == "goteborg"}
        for p, el in xml_partier(gbg).items():
            if p == "ÖVRIGA_FGVAL":
                continue
            if p not in goteborg or goteborg[p]["roster"] != el.get("RÖSTER"):
                F("%s goteborg %s: 00-filen %s, aggregat %s" % (val, p, el.get("RÖSTER"), goteborg.get(p, {}).get("roster")))
        if gbg.get("RÖSTER") != kommun1480.get("RÖSTER"):
            F("%s: KOMMUN 1480 RÖSTER skiljer mellan 00-filen och 1480-filen" % val)
        I("%s: goteborg i aggregat = KOMMUN 1480 i 00-filen (oberoende av 1480-filen), giltiga %s" % (val, gbg.get("RÖSTER")))
    if val == "rf":
        l14 = [l for l in lan if l.get("KOD") == "14"][0]
        vg = {r["parti_kalla"]: r for r in agg if r["niva"] == "vgregion"}
        # varje kommun ligger bade under KRETS_RIKSDAG och KRETS_LANDSTING; ta en per KOD
        kl = list({k.get("KOD"): k for k in l14.iter("KOMMUN")}.values())
        s = defaultdict(int)
        for k in kl:
            for p, el in xml_partier(k).items():
                if p != "ÖVRIGA_FGVAL":
                    s[p] += int(el.get("RÖSTER"))
        for p, v in s.items():
            if p not in vg or int(vg[p]["roster"]) != v:
                F("rf vgregion %s: summa kommuner %d, aggregat %s" % (p, v, vg.get(p, {}).get("roster")))
        rb = sum(int(k.find("VALDELTAGANDE").get("RÖSTBERÄTTIGADE")) for k in kl)
        g = list(vg.values())[0]
        if rb != int(g["rostberattigade"]):
            F("rf vgregion rostberattigade: summa kommuner %d, aggregat %s" % (rb, g["rostberattigade"]))
        I("rf: vgregion i aggregat = summa av %d kommuner under LÄN 14 (%s, %s mandat) for %d partier; rostberattigade %d" % (
            len(kl), l14.get("TYP"), l14.get("MANDAT_VALOMRÅDE"), len(s), rb))


def kontroll_mandat():
    print("\n== D. mandat_2010_riksdag.csv mot mandatfordelning_per_valkrets_R (1).xls, alla valkretsar")
    sh = xlrd.open_workbook(XLS_MANDAT_R).sheet_by_index(0)
    hdr = [sh.cell_value(0, c) for c in range(sh.ncols)]
    xls = {}
    for r in range(1, sh.nrows):
        if sh.cell_value(r, 0) == "":
            continue
        kod = "%02d%02d" % (int(sh.cell_value(r, 0)), int(sh.cell_value(r, 1)))
        xls[kod] = dict(zip(hdr, [sh.cell_value(r, c) for c in range(sh.ncols)]))
    m = read_csv("mandat_2010_riksdag.csv")
    vk = defaultdict(dict)
    for r in m:
        if r["niva"] == "valkrets":
            vk[r["kod"]][r["parti_kalla"]] = r
    if set(vk) != set(xls):
        F("mandat: valkretskoder skiljer csv %s xls %s" % (sorted(set(vk) - set(xls)), sorted(set(xls) - set(vk))))
    n = 0
    for kod, rad in xls.items():
        for p in ("M", "C", "FP", "KD", "S", "V", "MP", "SD"):
            fast = int(rad[p] or 0)
            utj = int(rad[p + " utj"] or 0)
            r = vk[kod].get(p)
            got = int(r["mandat"] or 0) if r else 0
            gotu = int(r["varav_utjamning"] or 0) if r else 0
            if got != fast + utj or gotu != utj:
                F("mandat %s %s %s: xls %d+%d, csv %d (utj %d)" % (kod, rad["NAMN"], p, fast, utj, got, gotu))
            n += 1
        if int(rad["ANT_MAND_FAST"]) != int(list(vk[kod].values())[0]["mandat_valkrets"]):
            F("mandat %s: fasta mandat xls %s csv %s" % (kod, rad["ANT_MAND_FAST"], list(vk[kod].values())[0]["mandat_valkrets"]))
        if rad["NAMN"] != list(vk[kod].values())[0]["namn"]:
            F("mandat %s: namn xls %r csv %r" % (kod, rad["NAMN"], list(vk[kod].values())[0]["namn"]))
    I("mandat: %d parti-valkrets-varden (fasta + utjamning), fasta mandat och namn lika xls for %d valkretsar" % (n, len(xls)))


def kontroll_fgval_2014(val):
    print("\n== E. %s: 2010 ars distrikt mot FGVAL i 2014 ars XML (fgval_2014_%s.csv)" % (val, val))
    try:
        fg14 = read_csv("fgval_2014_%s.csv" % val)
    except FileNotFoundError:
        I("%s: fgval_2014_%s.csv saknas, kontrollen far goras senare" % (val, val))
        return
    ar_fg = sorted({r["ar_fg"] for r in fg14})
    if ar_fg != ["2010"]:
        I("%s: fgval_2014_%s.csv har ar_fg %s, inte 2010 (for regionvalet ar foregaende val omvalet 2011-05-15); kontrollen kan inte goras for %s" % (val, val, ar_fg, val))
        return
    by14 = defaultdict(dict)
    namn14 = {}
    for r in fg14:
        namn14[r["kod_2014"]] = r["namn_2014"]
        if r["roster_fgval"] != "":
            by14[r["kod_2014"]][r["parti"]] = int(r["roster_fgval"])
    vek14 = defaultdict(list)
    for k, d in by14.items():
        vek14[tuple(d.get(p, 0) for p in STORA)].append(k)
    r10 = read_csv("roster_2010_%s_xml.csv" % val)
    by10 = defaultdict(dict)
    namn10 = {}
    for r in r10:
        by10[r["kod"]][r["parti"]] = int(r["roster"])
        namn10[r["kod"]] = r["namn"]
    n1 = n0 = nm = 0
    saknas = []
    majorna = []
    for k, d in by10.items():
        vek = tuple(d.get(p, 0) for p in STORA)
        tr = vek14.get(vek, [])
        if len(tr) == 1:
            n1 += 1
            if k in MAJORNA:
                majorna.append("%s %s = 2014 %s %s" % (k, namn10[k], tr[0], namn14[tr[0]]))
        elif len(tr) == 0:
            n0 += 1
            saknas.append("%s %s" % (k, namn10[k]))
        else:
            nm += 1
    I("%s: %d av %d 2010-distrikt har exakt ett 2014-distrikt vars FGVAL (M,C,FP,KD,S,V,MP,SD) ar identiskt med 2010 ars tal; %d utan traff, %d med flera" % (
        val, n1, len(by10), n0, nm))
    I("%s: utan traff (andrade distrikt 2014 eller onsdagsdistrikt): %s" % (val, "; ".join(saknas)))
    m_ok = [k for k in MAJORNA if any(l.startswith(k) for l in majorna)]
    if len(m_ok) != len(MAJORNA):
        I("%s: Majornadistrikt utan exakt 2014-traff: %s" % (val, sorted(set(MAJORNA) - set(m_ok))))
    for l in majorna:
        print("   " + l)


def kontroll_deltagande(val, XM):
    print("\n== F. %s: distriktfilens rostberattigade/valdeltagande mot XML VALDELTAGANDE" % val)
    dist = read_csv("distrikt_2010_%s.csv" % val)
    n = 0
    for r in dist:
        vd = XM[r["kod"]]
        v = vd.find("VALDELTAGANDE")
        if r["kod"].startswith("148000"):
            if v is not None and v.get("RÖSTBERÄTTIGADE"):
                F("%s %s: onsdagsdistrikt har RÖSTBERÄTTIGADE i XML men tomt i csv" % (val, r["kod"]))
            continue
        if r["rostberattigade"] != v.get("RÖSTBERÄTTIGADE") or abs(float(r["valdeltagande"]) - float(v.get("PROCENT").replace(",", "."))) > 1e-9 \
                or r["rostande"] != v.get("SUMMA_RÖSTER") or r["giltiga"] != vd.get("RÖSTER"):
            F("%s %s: csv rostb/vdt/rostande/giltiga %s/%s/%s/%s, XML %s/%s/%s/%s" % (
                val, r["kod"], r["rostberattigade"], r["valdeltagande"], r["rostande"], r["giltiga"],
                v.get("RÖSTBERÄTTIGADE"), v.get("PROCENT"), v.get("SUMMA_RÖSTER"), vd.get("RÖSTER")))
        n += 1
    I("%s: %d geografiska distrikt: rostberattigade, valdeltagande, rostande och giltiga = XML" % (val, n))


def stickprov(val, rng):
    print("\n== G. %s: stickprov mot racell (eget slumpfro)" % val)
    wb = xlrd.open_workbook(XLS[val])
    sh = wb.sheet_by_index(0)
    hdr = [sh.cell_value(0, c) for c in range(sh.ncols)]
    if val in ("rd", "rf"):
        cols = [(c, h[:-4]) for c, h in enumerate(hdr) if isinstance(h, str) and h.endswith(" tal") and h[:-4] not in ("BL", "BLANK", "OG")]
    else:
        cols = [(c, ("%04d" % int(h)) if isinstance(h, float) else str(h)) for c, h in enumerate(hdr) if 6 <= c < hdr.index("BLANK")]
    rows = {}
    for r in range(1, sh.nrows):
        if sh.cell_value(r, 0) == 14.0 and sh.cell_value(r, 1) == 80.0:
            vd = sh.cell_value(r, 2)
            if isinstance(vd, float):
                rows["1480%04d" % int(vd)] = r
    csvm = {(r["kod"], r["parti_kalla"]): r["roster"] for r in read_csv("roster_2010_%s_xls.csv" % val)}
    for kod in rng.sample(MAJORNA, 3):
        r = rows[kod]
        fyllda = [(c, p) for c, p in cols if sh.cell_value(r, c) != ""]
        for c, p in rng.sample(fyllda[:9], 3):
            v = sh.cell_value(r, c)
            csvv = csvm.get((kod, p))
            ok = v != "" and csvv is not None and int(v) == int(csvv)
            line = "%s %s %s: %s, flik %r, rad %d, kolumn %s (%r) = %r; csv %s -> %s" % (
                val, kod, p, XLS[val].split("/")[-1], sh.name, r + 1, col_letter(c), hdr[c], v, csvv, "lika" if ok else "OLIKA")
            print("   " + line)
            if not ok:
                F("stickprov " + line)


def kontroll_fgval_2006(val):
    print("\n== H. %s: fgval for fem Majornadistrikt mot 2006-delens xls-filer" % val)
    try:
        r06 = read_csv("roster_2006_%s_xls.csv" % val)
        d06 = {r["kod"]: r for r in read_csv("distrikt_2006_%s.csv" % val)}
    except FileNotFoundError:
        I("%s: 2006-filer saknas, kontrollen far goras senare" % val)
        return
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
    for kod in ["14800912", "14800916", "14800921", "14800936", "14800944"]:
        vek = tuple(by10[kod].get(p, 0) for p in STORA)
        tr = [k for k, d in by06.items() if tuple(d.get(p, 0) for p in STORA) == vek]
        if len(tr) != 1:
            F("%s %s: %d traffar i roster_2006_%s_xls.csv for FGVAL %s" % (val, kod, len(tr), val, vek))
            continue
        dd = d06[tr[0]]
        fd = fgd[kod]
        delt = (fd["giltiga_fgval"], fd["rostande_fgval"], fd["rostberattigade_fgval"]) == (dd["giltiga"], dd["rostande"], dd["rostberattigade"])
        if not delt:
            F("%s %s: deltagande fgval %s/%s/%s, 2006-fil %s/%s/%s" % (val, kod, fd["giltiga_fgval"], fd["rostande_fgval"], fd["rostberattigade_fgval"],
                                                                    dd["giltiga"], dd["rostande"], dd["rostberattigade"]))
        print("   %s %s: FGVAL %s = 2006 %s %s (giltiga/rostande/rostb %s/%s/%s %s)" % (
            val, kod, dict(zip(STORA, vek)), tr[0], namn06[tr[0]], dd["giltiga"], dd["rostande"], dd["rostberattigade"], "lika" if delt else "OLIKA"))


def main():
    rng = random.Random(20100919)
    kontroll_format()
    kretsnamn = {"148001": "Göteborg, Hisingen", "148002": "Göteborg, Öster", "148003": "Göteborg, Centrum", "148004": "Göteborg, Väster"}
    for val in ("rd", "rf", "kf"):
        root = etree.parse(XML_1480[val], PARSER).getroot()
        kommun = root.find("KOMMUN")
        kretsar = kommun.findall("KRETS_KOMMUN")
        XM = {}
        for kk in kretsar:
            for vd in kk.findall("VALDISTRIKT"):
                XM[vd.get("KOD")] = vd
            for on in kk.findall("ONSDAGSDISTRIKT"):
                XM["1480%04d" % int(on.get("KOD")[-2:])] = on
        kontroll_xml_summor(val, kommun, kretsar, kretsnamn)
        kontroll_aggregat_00(val, kommun)
        kontroll_fgval_2014(val)
        kontroll_deltagande(val, XM)
        stickprov(val, rng)
        kontroll_fgval_2006(val)
    kontroll_mandat()
    print("\nFEL: %d" % len(fel))
    for f in fel:
        print("  " + f)


if __name__ == "__main__":
    main()
