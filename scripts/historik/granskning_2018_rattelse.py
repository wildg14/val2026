# -*- coding: utf-8 -*-
"""
granskning_2018_rattelse.py - fyller de tomma namnfalten i data/historik/partier_2018.csv.

val2018.md lamnade tre partibeteckningar i riksdagsvalet oppna eftersom kolumnrubrikerna BASIP,
INI och NYREF saknar PARTIFÖRKORTNING i deltagande_partier.skv. Granskningen har belagt dem mot
Valmyndighetens egna distriktssidor pa historik.val.se, dar tabellen "Röstfördelning övriga
partier" listar partiet med tom Förk.-cell men med partibeteckning och rostetal:

  BASIP  Basinkomstpartiet  14804154 Lundby, Rambergsstaden, Norra: sidan 3 roster,
         2018_R_per_valdistrikt.xlsx flik "R antal" kolumn BASIP = 3 (INI och NYREF = 0)
  INI    Initiativet        14805173 Askim-Frölunda-Högsbo, Gånglåten: sidan 3 roster,
         kolumn INI = 3 (BASIP och NYREF = 0)
  NYREF  NY REFORM          14807031 Västra Hisingen, Länsmansgården, Ö: sidan 1 rost,
         kolumn NYREF = 1 (BASIP och INI = 0)

I vart och ett av de tre distrikten ar det den enda raden utan forkortning pa sidan, sa
kopplingen ar entydig. Namnen stammer ocksa med deltagande_partier.skv, dar Basinkomstpartiet
(PARTIKOD 1372), Initiativet (1374) och NY REFORM (1385) star som riksdagspartier utan
forkortning.

ÖVR far partibeteckningen som Valmyndighetens distriktssidor anvander i samma tabell,
"Övriga anmälda partier". ÖVR ar ingen partibeteckning utan en restpost.

Skriptet ar idempotent: det andrar bara rader dar namn ar tomt och lamnar allt annat orort.
Kors med: <venv>/bin/python scripts/historik/granskning_2018_rattelse.py
"""
import csv
import os

FIL = "/Users/daniel/code/Temp/data/historik/partier_2018.csv"

NAMN = {
    ("rd", "BASIP"): ("Basinkomstpartiet",
                      "historik.val.se distriktssida R 14804154 (rad utan Förk.), "
                      "styrkt mot 2018_R_per_valdistrikt.xlsx kolumn BASIP"),
    ("rd", "INI"): ("Initiativet",
                    "historik.val.se distriktssida R 14805173 (rad utan Förk.), "
                    "styrkt mot 2018_R_per_valdistrikt.xlsx kolumn INI"),
    ("rd", "NYREF"): ("NY REFORM",
                      "historik.val.se distriktssida R 14807031 (rad utan Förk.), "
                      "styrkt mot 2018_R_per_valdistrikt.xlsx kolumn NYREF"),
    ("rd", "ÖVR"): ("Övriga anmälda partier", "historik.val.se distriktssidor, kolumnen Parti"),
    ("rf", "ÖVR"): ("Övriga anmälda partier", "historik.val.se distriktssidor, kolumnen Parti"),
    ("kf", "ÖVR"): ("Övriga anmälda partier", "historik.val.se distriktssidor, kolumnen Parti"),
}


def main():
    with open(FIL, encoding="utf-8", newline="") as f:
        las = csv.DictReader(f, delimiter=";")
        falt = las.fieldnames
        rader = list(las)
    andrade = []
    for r in rader:
        nyckel = (r["val"], r["parti_kalla"])
        if nyckel in NAMN and not r["namn"]:
            r["namn"], r["namn_kalla"] = NAMN[nyckel]
            andrade.append(f"{r['val']} {r['parti_kalla']} -> {r['namn']}")
    if not andrade:
        print("inget att andra, alla namn ar redan ifyllda")
        return
    tmp = FIL + ".ny"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        skriv = csv.DictWriter(f, fieldnames=falt, delimiter=";", lineterminator="\n")
        skriv.writeheader()
        skriv.writerows(rader)
    os.replace(tmp, FIL)
    print(f"{len(andrade)} rader andrade i {FIL}:")
    for a in andrade:
        print("  ", a)
    kvar = [(r["val"], r["parti_kalla"]) for r in rader if not r["namn"]]
    print("rader utan namn kvar:", kvar)


if __name__ == "__main__":
    main()
