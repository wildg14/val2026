# -*- coding: utf-8 -*-
"""
granskning_2010_fgval_koppling.py - hittar vilket 2006-distrikt som ligger bakom
RÖSTER_FGVAL i 2010 års XML, genom att jamfora FGVAL-vektorn (M, C, FP/L, KD, S, V, MP, SD,
giltiga, rostande, rostberattigade) per 2010-distrikt med 2006 ars faktiska tal i
data/historik/roster_2006_<val>_xml.csv och distrikt_2006_<val>.csv.

Skriver data/historik/granskning_2010_fgval_koppling_2006.csv med kolumnerna
ar;val;kod_2010;namn_2010;indelning;kod_2006;namn_2006;traffar
(traffar = antal 2006-distrikt med identisk vektor; kod_2006 tom om 0 eller >1 traffar).
Saknat RÖSTER_FGVAL for ett parti tolkas som 0, eftersom XML utelamnar attributet nar 2006-vardet var 0.
Onsdagsdistrikten 14800001-14800004 far 0 traffar eftersom 2006-filerna har koderna 1480VK01-1480VK04 utan rostberattigade.
Kor med: <venv>/bin/python scripts/historik/granskning_2010_fgval_koppling.py
"""
import csv
from collections import defaultdict

DATA = "/Users/daniel/code/Temp/data/historik/"
UT = DATA + "granskning_2010_fgval_koppling_2006.csv"
STORA = ["M", "C", "L", "KD", "S", "V", "MP", "SD"]


def read_csv(name):
    with open(DATA + name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    rows = []
    stat = {}
    for val in ("rd", "rf", "kf"):
        r06 = read_csv("roster_2006_%s_xml.csv" % val)
        d06 = {r["kod"]: r for r in read_csv("distrikt_2006_%s.csv" % val)}
        by06 = defaultdict(dict)
        namn06 = {}
        for r in r06:
            by06[r["kod"]][r["parti"]] = int(r["roster"])
            namn06[r["kod"]] = r["namn"]
        vek06 = {}
        for k, d in by06.items():
            dd = d06.get(k, {})
            vek06[k] = tuple(d.get(p, 0) for p in STORA) + (dd.get("giltiga"), dd.get("rostande"), dd.get("rostberattigade"))
        fg = read_csv("fgval_2010_%s.csv" % val)
        fgd = {r["kod_2010"]: r for r in read_csv("fgval_2010_%s_deltagande.csv" % val)}
        by10 = defaultdict(dict)
        namn10 = {}
        for r in fg:
            namn10[r["kod_2010"]] = r["namn_2010"]
            if r["roster_fgval"] != "":
                by10[r["kod_2010"]][r["parti"]] = int(r["roster_fgval"])
        n = defaultdict(int)
        for k in fgd:
            d = fgd[k]
            v10 = by10.get(k, {})
            # RÖSTER_FGVAL saknas i XML nar 2006-vardet var 0 (t.ex. C i 14800262), darfor 0 for saknat parti
            vek = tuple(v10.get(p, 0) for p in STORA) + (d["giltiga_fgval"] or None, d["rostande_fgval"] or None, d["rostberattigade_fgval"] or None)
            if d["giltiga_fgval"] == "":
                tr = []
                typ = "ingen fgval"
            else:
                tr = [k6 for k6, v6 in vek06.items() if v6 == vek]
                typ = {0: "0 traffar", 1: "1 traff"}.get(len(tr), "flera traffar")
            n[typ] += 1
            rows.append([2010, val, k, namn10[k], d["indelning"], tr[0] if len(tr) == 1 else "", namn06[tr[0]] if len(tr) == 1 else "", len(tr)])
        stat[val] = dict(n)
        print(val, dict(n))
        for r in rows:
            if r[1] == val and r[7] != 1 and not r[2].startswith("148000"):
                print("   ", r[2], r[3], "indelning=%r" % r[4], "traffar", r[7])
    with open(UT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["ar", "val", "kod_2010", "namn_2010", "indelning", "kod_2006", "namn_2006", "traffar"])
        w.writerows(rows)
    print("skrev", UT, len(rows), "rader")
    # Majorna och Linnestaden
    for r in rows:
        if r[1] == "rd" and ("Majorna" in r[3] or "Linnéstaden" in r[3]):
            print("  %s %s -> %s %s (%d)" % (r[2], r[3], r[5], r[6], r[7]))


if __name__ == "__main__":
    main()
