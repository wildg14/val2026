#!/usr/bin/env python3
"""Jamfor 2002 ars valdistriktsnamn i Majornaomradet (forsamlingsbaserade namn:
Karl Johan, Masthugg, Oskar Fredrik, Haga, Annedal) med 2006 ars namn
(Kungsladugard-Sanna, Majorna, Stigberget, Masthugget, Olivedal, Annedal-Haga).
Skriver bara till skarmen; resultatet ar infort i docs/historik/noter/val2002.md.
"""
import csv
import re
from collections import defaultdict

import xlrd

ROSTER_2002 = "/Users/daniel/code/Temp/data/historik/roster_2002_rd.csv"
INDELNING_2002 = "/Users/daniel/code/Temp/data/historik/distrikt_2002_indelning.csv"
XLS_2006 = "/private/tmp/claude-501/-Users-daniel-code-Temp/f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad/dl2006/unz/riksdagen_i_valdistrikt.xls"
GRUPPER_2002 = ["Karl Johan", "Masthugg", "Oskar Fredrik", "Haga", "Annedal"]
GRUPPER_2006 = ["Kungsladugård-Sanna", "Majorna", "Stigberget", "Masthugget", "Olivedal", "Annedal-Haga"]


def grupp(namn, grupper):
    for g in grupper:
        if re.fullmatch(re.escape(g) + r" \d+", namn):
            return g
    return None


def main():
    # 2002: giltiga roster (summa av alla partikolumner inkl OVR) per distrikt, riksdagsvalet
    g2002 = defaultdict(lambda: {"n": 0, "giltiga": 0, "koder": [], "M": 0, "S": 0, "V": 0})
    per_kod = defaultdict(int)
    namn_av_kod = {}
    with open(ROSTER_2002, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            per_kod[r["kod"]] += int(r["roster"])
            namn_av_kod[r["kod"]] = r["namn"]
            g = grupp(r["namn"], GRUPPER_2002)
            if g and r["parti"] in ("M", "S", "V"):
                g2002[g][r["parti"]] += int(r["roster"])
    andrad = {}
    with open(INDELNING_2002, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["val"] == "rd":
                andrad[r["kod"]] = r["andrad_indelning"]
    for kod, giltiga in per_kod.items():
        g = grupp(namn_av_kod[kod], GRUPPER_2002)
        if g:
            g2002[g]["n"] += 1
            g2002[g]["giltiga"] += giltiga
            g2002[g]["koder"].append(kod)
    print("2002 (riksdagsvalet), forsamlingsbaserade namn, Goteborg 3 och 4:")
    for g in GRUPPER_2002:
        d = g2002[g]
        ko = sorted(d["koder"])
        n_andrad = sum(1 for k in ko if andrad.get(k) == "1")
        print(f"  {g:15s} {d['n']:2d} distrikt  koder {ko[0]}-{ko[-1]}  giltiga {d['giltiga']:6d}  "
              f"M {d['M']:5d} S {d['S']:5d} V {d['V']:5d}  andrad indelning mot 1998: {n_andrad} av {d['n']}")

    # 2006: riksdagen_i_valdistrikt.xls, kolumner LKFV, NAMN, <P>_ROST ... BLANK_ROST, TOT_ROST, ROSTB, VDT;
    # giltiga = summa av partikolumnerna *_ROST (inklusive OVR_ROST, exklusive BLANK_ROST och TOT_ROST)
    wb = xlrd.open_workbook(XLS_2006)
    sh = wb.sheet_by_index(0)
    hdr = sh.row_values(0)
    rost_cols = [i for i, h in enumerate(hdr) if str(h).endswith("_ROST") and h not in ("BLANK_ROST", "TOT_ROST")]
    im, is_, iv = hdr.index("M_ROST"), hdr.index("S_ROST"), hdr.index("V_ROST")
    g2006 = defaultdict(lambda: {"n": 0, "giltiga": 0, "koder": [], "M": 0, "S": 0, "V": 0})
    for r in range(1, sh.nrows):
        v = sh.row_values(r)
        kod = str(v[0]).strip()
        if not kod.startswith("1480"):
            continue
        g = grupp(str(v[1]).strip(), GRUPPER_2006)
        if not g:
            continue
        d = g2006[g]
        d["n"] += 1
        d["koder"].append(kod)
        d["giltiga"] += int(sum(float(v[i] or 0) for i in rost_cols))
        d["M"] += int(v[im] or 0)
        d["S"] += int(v[is_] or 0)
        d["V"] += int(v[iv] or 0)
    print("2006 (riksdagsvalet), kolumner *_ROST i riksdagen_i_valdistrikt.xls:")
    for g in GRUPPER_2006:
        d = g2006[g]
        ko = sorted(d["koder"])
        print(f"  {g:20s} {d['n']:2d} distrikt  koder {ko[0]}-{ko[-1]}  giltiga {d['giltiga']:6d}  "
              f"M {d['M']:5d} S {d['S']:5d} V {d['V']:5d}")
    print("Summor:")
    a = g2002["Karl Johan"]; b = g2006["Kungsladugård-Sanna"]; c = g2006["Majorna"]
    print(f"  Karl Johan 2002: {a['n']} distrikt, giltiga {a['giltiga']}  <->  Kungsladugård-Sanna + Majorna 2006: "
          f"{b['n'] + c['n']} distrikt, giltiga {b['giltiga'] + c['giltiga']}")
    a = g2002["Masthugg"]; b = g2006["Masthugget"]; c = g2006["Stigberget"]
    print(f"  Masthugg 2002: {a['n']} distrikt, giltiga {a['giltiga']}  <->  Masthugget + Stigberget 2006: "
          f"{b['n'] + c['n']} distrikt, giltiga {b['giltiga'] + c['giltiga']}")
    a = g2002["Oskar Fredrik"]; b = g2006["Olivedal"]
    print(f"  Oskar Fredrik 2002: {a['n']} distrikt, giltiga {a['giltiga']}  <->  Olivedal 2006: "
          f"{b['n']} distrikt, giltiga {b['giltiga']}")
    a = g2002["Haga"]; a2 = g2002["Annedal"]; b = g2006["Annedal-Haga"]
    print(f"  Haga + Annedal 2002: {a['n'] + a2['n']} distrikt, giltiga {a['giltiga'] + a2['giltiga']}  <->  "
          f"Annedal-Haga 2006: {b['n']} distrikt, giltiga {b['giltiga']} (Annedals forsamling omfattade aven "
          f"Guldheden och Landala, som 2006 troligen har egna namn)")


if __name__ == "__main__":
    main()
