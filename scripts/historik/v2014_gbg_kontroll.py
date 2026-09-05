#!/usr/bin/env python3
"""v2014: kontroller för 2014 års Göteborgsdata.

1. Excel (roster_2014_<val>_xls.csv, distrikt_2014_<val>.csv) mot XML
   (slutresultat_1480R/L/K.xml): koder, namn, röster per parti, andelar,
   giltiga, blanka, ogiltiga, röstande, röstberättigade, valdeltagande.
2. Koder och namn mot shapefilen valgeografi_valdistrikt.dbf (2014).
3. Summor per kommun och kommunvalkrets mot XML-summeringarna.
4. FGVAL (föregående val) per 2014-distrikt mot 2010 års XML per distrikt:
   hittar det 2010-distrikt vars riksdags-/kommunröster exakt motsvarar FGVAL.
   Skriver data/historik/fgval_matchning_2010_2014.csv.
5. Tabell över Majorna-Linnés 36 distrikt för noteringen.

Körs med scratchpad-venv (dbfread):
  venv/bin/python scripts/historik/v2014_gbg_kontroll.py
"""
import csv
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

from dbfread import DBF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v2014_gbg_xml as X  # noqa: E402

SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"
XML2014_DIR = os.path.join(SCRATCH, "unz/slutresultat")
XML2010_DIR = os.path.join(SCRATCH, "unz/slutresultat__1_")
DBF2014 = os.path.join(SCRATCH, "unz/valgeografi_valdistrikt/valgeografi_valdistrikt.dbf")
DBF2010 = os.path.join(SCRATCH, "unz/alla_valdistrikt/alla_valdistrikt.dbf")
UT_DIR = "/Users/daniel/code/Temp/data/historik"
KOMMUN = "1480"
VAL = {"rd": "R", "rf": "L", "kf": "K"}
MATCHPARTIER = ["M", "C", "FP", "KD", "S", "V", "MP", "SD"]
# 2010 års distrikt i SDN Majorna (148009xx) enligt alla_valdistrikt.dbf
MAJORNA_2010_PREFIX = "148009"


def read_csv(name):
    with open(os.path.join(UT_DIR, name), encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def load(d, name):
    return ET.parse(os.path.join(d, name)).getroot()


def xml_distrikt(root):
    out = {}
    for kod, namn, el in X.distrikt_iter(root):
        partier = {}
        fg = {}
        for p, g in X.parti_rader(el):
            partier[p] = (int(g.get("RÖSTER")), X.dec(g.get("PROCENT")))
            if g.get("RÖSTER_FGVAL") is not None:
                fg[p] = int(g.get("RÖSTER_FGVAL"))
        v = X.distrikt_varden(el)
        out[kod] = {"namn": namn, "partier": partier, "fg": fg, "v": v,
                    "indelning": el.get("INDELNING") or ""}
    return out


def kontroll_xls_mot_xml(val, xd):
    fel = 0
    roster = read_csv("roster_2014_%s_xls.csv" % val)
    distrikt = read_csv("distrikt_2014_%s.csv" % val)
    xls_koder = {r["kod"] for r in distrikt}
    if xls_koder != set(xd):
        print(val, "KODSKILLNAD xls-xml", sorted(xls_koder ^ set(xd))); fel += 1
    for r in distrikt:
        d = xd[r["kod"]]
        if r["namn"] != d["namn"]:
            print(val, "NAMN", r["kod"], r["namn"], "|", d["namn"]); fel += 1
        v = d["v"]
        for k_csv, k_xml in (("giltiga", "giltiga"), ("blanka", "blanka"),
                             ("ogiltiga_ovriga", "og"), ("rostande", "rostande"),
                             ("rostberattigade", "rostberattigade"),
                             ("valdeltagande", "valdeltagande")):
            a, b = r[k_csv], v[k_xml] or ""
            # uppsamlingsdistrikten saknar VALDELTAGANDE i XML, då är b tom
            if a != b and b != "":
                print(val, "VÄRDE", r["kod"], k_csv, a, "|", b); fel += 1
    per = defaultdict(dict)
    for r in roster:
        per[r["kod"]][r["parti_kalla"]] = (int(r["roster"]), r["andel"])
    for kod, pp in per.items():
        # jämför på normaliserad kod: Excel har tappat inledande nolla (450 = 0450)
        xp = {X.norm_parti(k): v for k, v in xd[kod]["partier"].items()}
        xls_namn = set()
        for p, (n, a) in pp.items():
            if p in ("OVR", "ÖVR"):
                continue
            p = X.norm_parti(p)
            xls_namn.add(p)
            if p not in xp:
                if n != 0:
                    print(val, "PARTI SAKNAS I XML", kod, p, n); fel += 1
                continue
            if xp[p][0] != n or (a and xp[p][1] != a):
                print(val, "RÖSTER", kod, p, n, a, "|", xp[p]); fel += 1
        ovr = pp.get("OVR", pp.get("ÖVR", (0, ""))) [0]
        rest = sum(n for p, (n, a) in xp.items() if p not in xls_namn)
        if ovr != rest:
            print(val, "ÖVR", kod, ovr, "|", rest); fel += 1
    print(val, "xls mot xml:", len(distrikt), "distrikt,", len(roster),
          "partirader, fel:", fel)


def kontroll_dbf(xd):
    d = DBF(DBF2014, encoding="latin-1")
    dbf = {r["VD"]: r["VD_NAMN"] for r in d if r["VD"].startswith(KOMMUN)}
    xml_vd = {k: v["namn"] for k, v in xd.items() if k[4:7] != "000"}
    print("dbf 2014:", len(dbf), "distrikt; koder lika:", set(dbf) == set(xml_vd),
          "; namn lika:", all(dbf[k] == xml_vd[k] for k in dbf))


def kontroll_summor(val, root):
    distrikt = read_csv("distrikt_2014_%s.csv" % val)
    roster = read_csv("roster_2014_%s_xls.csv" % val)
    krets = {r["kod"]: r["valkrets"] for r in distrikt}
    summa = defaultdict(lambda: defaultdict(int))
    for r in roster:
        summa["goteborg"][r["parti_kalla"]] += int(r["roster"])
        summa[krets[r["kod"]]][r["parti_kalla"]] += int(r["roster"])
    agg = read_csv("aggregat_2014_%s.csv" % val)
    fel = 0
    for a in agg:
        if a["niva"] in summa and a["parti_kalla"] in summa[a["niva"]]:
            if int(a["roster"]) != summa[a["niva"]][a["parti_kalla"]]:
                print(val, "SUMMA", a["niva"], a["parti_kalla"], a["roster"],
                      summa[a["niva"]][a["parti_kalla"]]); fel += 1
    g = {a["parti_kalla"]: int(a["roster"]) for a in agg if a["niva"] == "goteborg"}
    print(val, "summor per kommun och valkrets mot XML, fel:", fel,
          "; giltiga Göteborg xls:", sum(int(r["giltiga"]) for r in distrikt),
          "xml:", agg[[a["niva"] for a in agg].index("goteborg")]["giltiga"])


def fgval_matchning(val, xd, root2010, namn2010):
    """Matchar FGVAL-vektorn (M, C, FP, KD, S, V, MP, SD) mot 2010 års distrikt."""
    d2010 = {}
    for kod, namn, el in X.distrikt_iter(root2010):
        vec = {}
        for p, g in X.parti_rader(el):
            vec[p] = int(g.get("RÖSTER"))
        d2010[kod] = tuple(vec.get(p, 0) for p in MATCHPARTIER)
    index = defaultdict(list)
    for kod, vec in d2010.items():
        index[vec].append(kod)
    rader = []
    n_fg = n_exakt = n_flera = n_ingen = 0
    for kod in sorted(xd):
        d = xd[kod]
        if not d["fg"]:
            rader.append([val, kod, d["namn"], d["indelning"] or "Oförändrad", "", "", "ingen FGVAL"])
            continue
        n_fg += 1
        vec = tuple(d["fg"].get(p, 0) for p in MATCHPARTIER)
        tr = index.get(vec, [])
        if len(tr) == 1:
            n_exakt += 1
            rader.append([val, kod, d["namn"], d["indelning"] or "Oförändrad",
                          tr[0], namn2010.get(tr[0], ""), "exakt"])
        elif len(tr) > 1:
            n_flera += 1
            rader.append([val, kod, d["namn"], d["indelning"] or "Oförändrad",
                          "|".join(tr), "", "flera"])
        else:
            n_ingen += 1
            rader.append([val, kod, d["namn"], d["indelning"] or "Oförändrad", "", "", "ingen"])
    print(val, "FGVAL-matchning mot 2010 XML: distrikt med FGVAL", n_fg,
          "exakt", n_exakt, "flera", n_flera, "ingen", n_ingen,
          "; 2010-distrikt i XML:", len(d2010))
    return rader


def landsting_fgval(xd2014L, root2010L):
    k = root2010L.find("KOMMUN")
    v = X.distrikt_varden(k)
    fg = sum(d["fg"].get("GILTIGA", 0) for d in xd2014L.values())
    print("Landsting: 2010-09-19 Göteborg giltiga enligt 2010 XML:", v["giltiga"],
          "röstande:", v["rostande"], "valdeltagande:", v["valdeltagande"],
          "| 2014 XML KOMMUN RÖSTER_FGVAL:", root2010L is not None and
          load(XML2014_DIR, "slutresultat_1480L.xml").find("KOMMUN").get("RÖSTER_FGVAL"))


def majorna_tabell(xd, match_rd, match_kf, namn2010):
    m_rd = {r[1]: r for r in match_rd}
    m_kf = {r[1]: r for r in match_kf}
    print("\n| kod 2014 | namn 2014 | indelning | 2010-distrikt (FGVAL rd) | FGVAL kf lika | gamla SDN Majorna |")
    print("|---|---|---|---|---|---|")
    majorna = []
    for kod in sorted(k for k in xd if k.startswith("148010")):
        d = xd[kod]
        r = m_rd[kod]
        k = m_kf[kod]
        m2010 = ("%s %s" % (r[4], r[5])) if r[6] == "exakt" else r[6]
        kf_lika = "ja" if (k[6] == "exakt" and k[4] == r[4]) else ("-" if k[6] == r[6] else k[6])
        if r[6] == "exakt":
            i_majorna = "ja" if r[4].startswith(MAJORNA_2010_PREFIX) else "nej"
        else:
            i_majorna = "?"
        if i_majorna == "ja":
            majorna.append(kod)
        print("| %s | %s | %s | %s | %s | %s |" % (kod, d["namn"], d["indelning"] or "Oförändrad",
                                                  m2010, kf_lika, i_majorna))
    print("\nexakt matchade gamla SDN Majorna:", majorna, len(majorna))


def main():
    namn2010 = {r["LKFV"]: r["VDNAMN"] for r in DBF(DBF2010, encoding="latin-1")
                if r["LKFV"].startswith(KOMMUN)}
    print("2010 dbf Göteborg:", len(namn2010), "distrikt, varav SDN Majorna (148009xx):",
          sum(1 for k in namn2010 if k.startswith(MAJORNA_2010_PREFIX)))
    alla = {}
    matchrader = []
    xd_all = {}
    for val, b in VAL.items():
        root = load(XML2014_DIR, "slutresultat_1480%s.xml" % b)
        xd = xml_distrikt(root)
        xd_all[val] = xd
        kontroll_xls_mot_xml(val, xd)
        if val == "rd":
            kontroll_dbf(xd)
        kontroll_summor(val, root)
        root2010 = load(XML2010_DIR, "slutresultat_1480%s.xml" % b)
        alla[val] = fgval_matchning(val, xd, root2010, namn2010)
        if val == "rf":
            landsting_fgval(xd, root2010)
        if val in ("rd", "kf"):
            matchrader += alla[val]
    path = os.path.join(UT_DIR, "fgval_matchning_2010_2014.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["val", "kod_2014", "namn_2014", "indelning", "kod_2010",
                    "namn_2010", "matchning"])
        w.writerows(matchrader)
    print("skrev", path, len(matchrader), "rader")
    majorna_tabell(xd_all["rd"], alla["rd"], alla["kf"], namn2010)


if __name__ == "__main__":
    main()
