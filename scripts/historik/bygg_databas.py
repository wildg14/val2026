#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bygg_databas.py - bygger den lilla historikdatabasen for valgrafiken "Sa rostade Majorna".

Laser CSV-filerna i data/historik/, 2022 ur valdata_2022.json och Valmyndighetens
xlsx-filer, och skriver:

  data/historik/majorna_historik.sqlite
  data/historik/roster_2022_<val>.csv, distrikt_2022_<val>.csv, aggregat_2022_<val>.csv
  data/historik/majorna_tidsserie.csv, majorna_tidsserie.json
  data/historik/jamforelse_tidsserie.csv   (Majorna, Goteborg, riket i samma fil)
  data/historik/majorna_tidsserie_fgval.csv (alternativ serie via FGVAL-kedjan)

Kors med scratchpadens venv:
  /Users/daniel/code/Temp/.venv/bin/python \
      /Users/daniel/code/Temp/scripts/historik/bygg_databas.py

Skriptet laser bara; det andrar ingen befintlig fil i projektet.
"""

import csv
import json
import os
import re
import sqlite3
import sys
import unicodedata

# ---------------------------------------------------------------- konstanter

ROT = "/Users/daniel/code/Temp"
DATA = os.path.join(ROT, "data", "historik")
DOCS = os.path.join(ROT, "docs", "historik")
SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"

DB = os.path.join(DATA, "majorna_historik.sqlite")

VALDATA_2022 = os.path.join(ROT, "data", "valdata_2022.json")
XLSX_2022 = {
    "rd": os.path.join(ROT, "Roster-per-distrikt-slutligt-antal-roster-"
                            "inklusive-totalt-valdeltagande-riksdagsvalet-2022.xlsx"),
    "rf": os.path.join(ROT, "roster-per-distrikt-slutligt-antal-roster-"
                            "inklusive-totalt-valdeltagande-regionval-2022.xlsx"),
    "kf": os.path.join(ROT, "roster-per-distrikt-slutligt-antal-roster-"
                            "inklusive-totalt-valdeltagande-kommunval-2022.xlsx"),
}
FLIK_2022 = {"rd": "roster_RD", "rf": "roster_RF", "kf": "roster_KF"}

# Valdagar. Varje datum kommer ur en fil, se kalla-kolumnen i tabellen val.
VALDAGAR = [
    (2002, "2002-09-15", "dl2006/slutresultat_1480R.xml, attributet VALDAG_FGVAL=20020915"),
    (2006, "2006-09-17", "dl2006/slutresultat_1480R.xml, attributet VALDAG=20060917"),
    (2010, "2010-09-19", "unz/slutresultat__1_/slutresultat_1480R.xml, attributet VALDAG=20100919"),
    (2014, "2014-09-14", "unz/slutresultat/slutresultat_1480R.xml, attributet VALDAG=20140914"),
    (2018, "2018-09-09", "data/historik/vallokaler_2018.csv, kolumnen valdag"),
    (2022, "2022-09-11", "unz/valgeografi_2022/VD_14_20220910_Val_20220911.json, filnamnets Val_20220911"),
]

AR_ALLA = [2002, 2006, 2010, 2014, 2018, 2022]
VALEN = ["rd", "rf", "kf"]

# Kallprioritet for rosterfilerna: XML fore xls dar bada finns (2006-2014).
ROSTER_KALLA = {
    2002: ("roster_2002_{val}.csv", "historik.val.se HTML, distriktssidor"),
    2006: ("roster_2006_{val}_xml.csv", "Valmyndighetens XML slutresultat_1480{X}.xml"),
    2010: ("roster_2010_{val}_xml.csv", "Valmyndighetens XML slutresultat_1480{X}.xml"),
    2014: ("roster_2014_{val}_xml.csv", "Valmyndighetens XML slutresultat_1480{X}.xml"),
    2018: ("roster_2018_{val}.csv", "2018_{X}_per_valdistrikt.xlsx flik '{X} antal'"),
}
XBOKSTAV = {"rd": "R", "rf": "L", "kf": "K"}

# De 23 valdistrikten i Majorna 2022 (kod 14800526-14800548).
MAJORNA_2022 = ["148005%02d" % n for n in range(26, 49)]

# Regel for jamforbart Majorna tidigare ar: ta med distrikt vars andel av ytan
# inom 2022 ars Majorna-union ar minst 0.5.
ANDEL_TROSKEL = 0.5

# Huvudpartier som foljs over tid i tidsserien (residualen skrivs som SUMMA_OVRIGA).
HUVUDPARTIER = ["V", "S", "MP", "SD", "M", "C", "L", "KD", "D", "FI", "K"]

# Harmonisering av partikoder mellan ar och kallor. Belagg i granskning_2002.md,
# granskning_2006.md och val2010.md.
PARTI_KANON = {
    "KPML": ("K", "2002 ars KPML ar samma parti som 2006 ars K, Kommunistiska Partiet "
                  "(belagt via FGVAL i granskning_2006.md)"),
    "SFV": ("SPVG", "2002 ars SFV ar samma parti som 2006 ars SPVG "
                    "(belagt via FGVAL i granskning_2006.md)"),
    "0524": ("PP", "Piratpartiet: XML 2006 skriver 0524, xls skriver PP"),
    "SJVÅP": ("SJVP", "Sjukvardspartiet: XML skriver SJVAP, xls skriver SJVP"),
    "OVR": ("ÖVR", "xls 2010 R-fil skriver OVR, L- och K-filerna ÖVR"),
}

# Partinamn i 2022 ars xlsx till partikod. Okanda namn far en slug och loggas.
PARTI_2022 = {
    "Moderaterna": "M",
    "Arbetarepartiet-Socialdemokraterna": "S",
    "Liberalerna (tidigare Folkpartiet)": "L",
    "Centerpartiet": "C",
    "Vänsterpartiet": "V",
    "Miljöpartiet de gröna": "MP",
    "Kristdemokraterna": "KD",
    "Sverigedemokraterna": "SD",
    "Feministiskt initiativ": "FI",
    "Piratpartiet": "PP",
    "Demokraterna": "D",
    "Kommunistiska Partiet": "K",
    "Enhet": "ENH",
    "Landsbygdspartiet Oberoende": "LPO",
    "Direktdemokraterna": "DD",
    "Nordiska motståndsrörelsen": "NMR",
    "Medborgerlig Samling": "MED",
    "Alternativ för Sverige": "AFS",
    "Partiet Nyans": "NYANS",
    "Knapptryckarna": "KNAPP",
    "Basinkomstpartiet": "BASIP",
    "Klimatalliansen": "KLIMA",
    "Kristna Värdepartiet": "KRVP",
    "MoD": "MOD",
    "Förenade Demokratiska Partiet": "FDP",
    "Kalle ankapartiet": "KALLE",
    "SKP": "SKP",
    "Stram Kurs Sverige": "SKS",
    "Volt Sverige": "VOLT",
    "Partiet Vändpunkt": "VÄND",
    "Swexitpartiet": "SWEXIT",
    "Klassiskt liberala partiet": "KLP",
    "Partiet Frihet": "FRIH",
    "Socialisterna-Välfärdspartiet": "SOCV",
    "Neoteknokraterna": "NEO",
    "övriga anmälda partier": "ÖVR",
    "Europeiska Arbetarpartiet-EAP": "EAP",
    "Sjukvårdspartiet - Västra Götaland": "SPVG",
    "Göteborgspartiet": "GBGP",
    "ANARKISTERNA": "ANARK",
    "BOHUSLÄNPARTIET": "BOHUS",
    "Det minst dåliga partiet": "DMDP",
    "Eropean radical reflektion a european dream party ERR": "ERR",
    "Humanistisk demokrati (HD)": "HD",
    "Naturens Parti": "NATUR",
    "Nix to the Six": "NIX",
    "Nu får det fan vara nog": "NUFAN",
    "Ond Kyckling Partiet": "OKP",
    "Politiskt Skifte": "POLSK",
    "Valsamverkanspartiet": "VSP",
}
RAD_2022_SUMMOR = {
    "Summa giltiga röster": "giltiga",
    "ej anmält deltagande": "ogiltiga_ej_anmalda",
    "blanka röster": "blanka",
    "övriga ogiltiga": "ogiltiga_ovriga",
    "Valdeltagande": "rostande",
}

# Rader i fgval-filerna som inte ar partier utan summor.
FGVAL_PSEUDO = {"GILTIGA", "BLANK", "OG", "SUMMA_RÖSTER", "RÖSTBERÄTTIGADE"}

okanda_partinamn = set()


# ---------------------------------------------------------------- hjalpare

def las(fil, **kw):
    """Las en semikolonseparerad UTF-8-fil som lista av dict."""
    sti = fil if os.path.isabs(fil) else os.path.join(DATA, fil)
    with open(sti, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";", **kw))


def finns(fil):
    return os.path.exists(fil if os.path.isabs(fil) else os.path.join(DATA, fil))


def heltal(s):
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    return int(round(float(s.replace(",", "."))))


def flyt(s):
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    return float(s.replace(",", "."))


def slugga(namn):
    t = unicodedata.normalize("NFKD", namn)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^A-Za-z0-9]+", "", t).upper()
    return t[:8] if t else "OKAND"


def kanon(parti):
    """Kanonisk partikod over ar och kallor."""
    p = (parti or "").strip()
    if p in PARTI_KANON:
        return PARTI_KANON[p][0]
    if re.fullmatch(r"\d{1,4}", p):          # numeriska partikoder, olika nollutfyllnad
        return p.zfill(4)
    return p


def omrade_av_namn(namn):
    """Stadsdel eller omradesprefix ur distriktsnamnet."""
    if not namn:
        return None
    if "," in namn:
        return namn.split(",", 1)[0].strip()
    return re.sub(r"\s+\d+$", "", namn).strip()


# Namn som Valmyndigheten anvander for distrikt utan geografi (sena fortidsroster).
UPPSAMLINGSNAMN = ("uppsamling", "onsdagsdistrikt", "ej räknade")


def ar_uppsamling(kod, namn):
    n = (namn or "").lower()
    return (any(t in n for t in UPPSAMLINGSNAMN)
            or not re.fullmatch(r"\d{8}", kod or ""))


# ---------------------------------------------------------------- 2022 ur xlsx

def las_2022_xlsx(val):
    """Las ett av 2022 ars xlsx-blad. Returnerar (rader_gbg, riket, vgregion, gbg_tot).

    rader_gbg: dict kod -> {"namn", "valkrets", "partier": {kod: (namn, roster)},
                            "giltiga", ..., "rostberattigade"}
    riket/vgregion/gbg_tot: dict med "partier" (kod -> (namn, roster)) och summor.
    """
    import openpyxl
    wb = openpyxl.load_workbook(XLSX_2022[val], read_only=True, data_only=True)
    ws = wb[FLIK_2022[val]]

    gbg = {}
    niva = {"riket": tom_niva(), "vgregion": tom_niva(), "goteborg": tom_niva()}
    sedda_rb = {"riket": {}, "vgregion": {}, "goteborg": {}}

    for r in ws.iter_rows(min_row=2, values_only=True):
        distrikt = r[1]
        if not distrikt:
            continue
        kod = str(distrikt).split("-", 1)[1].replace("-", "")   # RD-14-80-0526 -> 14800526
        lan = (str(r[2]) if r[2] else "").strip()
        kommun = (str(r[4]) if r[4] else "").strip()
        namn = (str(r[6]) if r[6] else "").strip()
        valkrets = (str(r[8]) if r[8] else "").strip()
        partinamn = (str(r[9]) if r[9] else "").strip()
        antal = heltal(r[10]) or 0
        rb = heltal(r[11]) or 0

        mal = ["riket"]
        if lan == "Västra Götaland":
            mal.append("vgregion")
        if kommun == "Göteborg":
            mal.append("goteborg")

        falt = RAD_2022_SUMMOR.get(partinamn)
        for m in mal:
            if falt:
                niva[m][falt] = niva[m].get(falt, 0) + antal
            else:
                pk = PARTI_2022.get(partinamn) or slugga(partinamn)
                nu = niva[m]["partier"].get(pk, [partinamn, 0])
                nu[1] += antal
                niva[m]["partier"][pk] = nu
            if kod not in sedda_rb[m]:
                sedda_rb[m][kod] = rb

        if kommun != "Göteborg":
            continue
        d = gbg.setdefault(kod, {"namn": namn, "valkrets": valkrets, "partier": {},
                                 "rostberattigade": rb})
        if falt:
            d[falt] = d.get(falt, 0) + antal
        else:
            pk = PARTI_2022.get(partinamn)
            if pk is None:
                okanda_partinamn.add(partinamn)
                pk = slugga(partinamn)
            d["partier"][pk] = (partinamn, antal)

    for m in niva:
        niva[m]["rostberattigade"] = sum(sedda_rb[m].values())
        niva[m]["ogiltiga"] = (niva[m].get("ogiltiga_ej_anmalda", 0)
                               + niva[m].get("blanka", 0)
                               + niva[m].get("ogiltiga_ovriga", 0))
    return gbg, niva


def tom_niva():
    return {"partier": {}, "giltiga": 0, "blanka": 0, "ogiltiga_ej_anmalda": 0,
            "ogiltiga_ovriga": 0, "rostande": 0, "rostberattigade": 0}


def skriv_2022_csv(gbg, niva, val):
    """Skriv 2022 i samma langa format som ovriga ar."""
    kallnamn = os.path.basename(XLSX_2022[val]) + " flik " + FLIK_2022[val]

    with open(os.path.join(DATA, "roster_2022_%s.csv" % val), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["ar", "val", "kod", "namn", "parti_kalla", "parti", "roster", "andel"])
        for kod in sorted(gbg):
            d = gbg[kod]
            giltiga = d.get("giltiga", 0)
            for pk in sorted(d["partier"]):
                pnamn, antal = d["partier"][pk]
                andel = "%.2f" % (100.0 * antal / giltiga) if giltiga else ""
                w.writerow([2022, val, kod, d["namn"], pnamn, pk, antal, andel])

    with open(os.path.join(DATA, "distrikt_2022_%s.csv" % val), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["ar", "val", "kod", "namn", "valkrets", "giltiga", "blanka",
                    "ogiltiga_ovriga", "ogiltiga", "rostande", "rostberattigade",
                    "valdeltagande", "kalla_fil"])
        for kod in sorted(gbg):
            d = gbg[kod]
            og = (d.get("ogiltiga_ej_anmalda", 0) + d.get("blanka", 0)
                  + d.get("ogiltiga_ovriga", 0))
            rb = d.get("rostberattigade") or 0
            vd = "%.2f" % (100.0 * d.get("rostande", 0) / rb) if rb else ""
            w.writerow([2022, val, kod, d["namn"], d["valkrets"], d.get("giltiga", 0),
                        d.get("blanka", 0), d.get("ogiltiga_ovriga", 0), og,
                        d.get("rostande", 0), rb if rb else "", vd, kallnamn])

    with open(os.path.join(DATA, "aggregat_2022_%s.csv" % val), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["ar", "val", "niva", "parti_kalla", "parti", "roster", "andel",
                    "giltiga", "rostande", "rostberattigade"])
        for n in ("riket", "vgregion", "goteborg"):
            v = niva[n]
            for pk in sorted(v["partier"]):
                pnamn, antal = v["partier"][pk]
                andel = "%.2f" % (100.0 * antal / v["giltiga"]) if v["giltiga"] else ""
                w.writerow([2022, val, n, pnamn, pk, antal, andel, v["giltiga"],
                            v["rostande"], v["rostberattigade"]])


# ---------------------------------------------------------------- databas

SCHEMA = """
DROP TABLE IF EXISTS val;
CREATE TABLE val (ar INTEGER, val TEXT, valdag TEXT, kalla TEXT,
                  PRIMARY KEY (ar, val));

DROP TABLE IF EXISTS distrikt;
CREATE TABLE distrikt (ar INTEGER, kod TEXT, namn TEXT, valkrets TEXT,
                       kommunvalkrets TEXT, sdn_eller_omrade TEXT,
                       uppsamlingsdistrikt INTEGER, kalla TEXT,
                       PRIMARY KEY (ar, kod));

DROP TABLE IF EXISTS roster;
CREATE TABLE roster (ar INTEGER, val TEXT, kod TEXT, parti TEXT, parti_kalla TEXT,
                     roster INTEGER, kalla TEXT, parti_kanon TEXT,
                     PRIMARY KEY (ar, val, kod, parti));

DROP TABLE IF EXISTS distrikt_summa;
CREATE TABLE distrikt_summa (ar INTEGER, val TEXT, kod TEXT, giltiga INTEGER,
                             ogiltiga INTEGER, rostande INTEGER,
                             rostberattigade INTEGER, valdeltagande REAL,
                             blanka INTEGER, kalla TEXT,
                             PRIMARY KEY (ar, val, kod));

DROP TABLE IF EXISTS aggregat;
CREATE TABLE aggregat (ar INTEGER, val TEXT, niva TEXT, parti TEXT, roster INTEGER,
                       andel REAL, parti_kalla TEXT, giltiga INTEGER, rostande INTEGER,
                       rostberattigade INTEGER, parti_kanon TEXT, kalla TEXT,
                       PRIMARY KEY (ar, val, niva, parti));

DROP TABLE IF EXISTS crosswalk;
CREATE TABLE crosswalk (ar_fran INTEGER, ar_till INTEGER, kod_fran TEXT, kod_till TEXT,
                        andel_av_fran REAL, andel_av_till REAL, typ TEXT, kalla TEXT);

DROP TABLE IF EXISTS majorna_medlem;
CREATE TABLE majorna_medlem (ar INTEGER, kod TEXT, namn TEXT, klass TEXT,
                             andel_i_majorna REAL, ingar_i_jamforbart_majorna INTEGER,
                             beslut TEXT, kalla TEXT, PRIMARY KEY (ar, kod));

DROP TABLE IF EXISTS parti_kanon;
CREATE TABLE parti_kanon (parti TEXT PRIMARY KEY, parti_kanon TEXT, kommentar TEXT);

DROP TABLE IF EXISTS partier;
CREATE TABLE partier (ar INTEGER, val TEXT, parti_kalla TEXT, parti TEXT, namn TEXT,
                      kalla TEXT);

DROP TABLE IF EXISTS rostberattigade_kategori;
CREATE TABLE rostberattigade_kategori (ar INTEGER, val TEXT, kod TEXT, namn TEXT,
                                       kon TEXT, medborgarskap TEXT, aldersgrupp TEXT,
                                       antal INTEGER, kalla TEXT);

DROP TABLE IF EXISTS fortidsroster;
CREATE TABLE fortidsroster (ar INTEGER, lokalid TEXT, lokal TEXT, datum TEXT,
                            antal INTEGER, kalla TEXT);

DROP TABLE IF EXISTS mandat;
CREATE TABLE mandat (ar INTEGER, val TEXT, niva TEXT, valkrets TEXT, parti TEXT,
                     fasta_mandat INTEGER, utjamningsmandat INTEGER, mandat INTEGER,
                     kalla TEXT);

DROP TABLE IF EXISTS tidsserie;
CREATE TABLE tidsserie (ar INTEGER, val TEXT, niva TEXT, parti TEXT, roster INTEGER,
                        andel REAL, giltiga INTEGER, rostande INTEGER,
                        rostberattigade INTEGER, valdeltagande REAL,
                        antal_distrikt INTEGER, metod TEXT,
                        PRIMARY KEY (ar, val, niva, parti));

CREATE INDEX ix_roster_ar_val_parti ON roster (ar, val, parti_kanon);
CREATE INDEX ix_roster_kod ON roster (ar, kod);
CREATE INDEX ix_cw_till ON crosswalk (ar_till, kod_till);
CREATE INDEX ix_cw_fran ON crosswalk (ar_fran, kod_fran);
CREATE INDEX ix_agg ON aggregat (ar, val, niva);
"""


def main():
    logg = []

    def log(s):
        print(s)
        logg.append(s)

    # ---------------- 2022 ur xlsx (och kontroll mot valdata_2022.json)
    gbg22, niva22 = {}, {}
    for val in VALEN:
        g, n = las_2022_xlsx(val)
        gbg22[val], niva22[val] = g, n
        skriv_2022_csv(g, n, val)
        log("2022 %s: %d distrikt i Goteborg, riket giltiga %d" %
            (val, len(g), n["riket"]["giltiga"]))
    if okanda_partinamn:
        log("Okanda partinamn 2022 (slug anvand): %s" % sorted(okanda_partinamn))

    vd22 = json.load(open(VALDATA_2022, encoding="utf-8"))

    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    cur = con.cursor()

    # ---------------- val
    for ar, dag, kalla in VALDAGAR:
        for val in VALEN:
            cur.execute("INSERT INTO val VALUES (?,?,?,?)", (ar, val, dag, kalla))

    # ---------------- parti_kanon
    for p, (k, komm) in PARTI_KANON.items():
        cur.execute("INSERT INTO parti_kanon VALUES (?,?,?)", (p, k, komm))

    # ---------------- roster + distrikt_summa + distrikt, 2002-2018
    distriktnamn = {}          # (ar, kod) -> namn
    valkrets_rd = {}           # (ar, kod) -> valkrets i riksdagsvalet
    valkrets_kf = {}           # (ar, kod) -> kommunvalkrets

    for ar in [2002, 2006, 2010, 2014, 2018]:
        mall, kallnamn = ROSTER_KALLA[ar]
        for val in VALEN:
            fil = mall.format(val=val)
            kalla = kallnamn.format(X=XBOKSTAV[val])
            rader = las(fil)
            poster = []
            for r in rader:
                if ar == 2002 and r["parti"] == "ÖVR":
                    continue           # ersatts av uppdelningen i _ovriga-filen
                poster.append((r["kod"], r["namn"], r["parti"], r["parti_kalla"],
                               heltal(r["roster"]), kalla))
            if ar == 2002:
                ofil = "roster_2002_%s_ovriga.csv" % val
                for r in las(ofil):
                    poster.append((r["kod"], r["namn"], r["parti"], r["parti_kalla"],
                                   heltal(r["roster"]),
                                   kalla + " (uppdelning av OVR ur " + ofil + ")"))
            for kod, namn, parti, pkalla, ro, ka in poster:
                distriktnamn.setdefault((ar, kod), namn)
                cur.execute("INSERT OR REPLACE INTO roster VALUES (?,?,?,?,?,?,?,?)",
                            (ar, val, kod, parti, pkalla, ro, ka, kanon(parti)))

            dfil = "distrikt_%d_%s.csv" % (ar, val)
            for r in las(dfil):
                kod = r["kod"]
                namn = r["namn"]
                distriktnamn.setdefault((ar, kod), namn)
                upps = ar_uppsamling(kod, namn)
                rb = heltal(r["rostberattigade"])
                vdl = flyt(r["valdeltagande"])
                if upps and (rb in (0, None)):
                    rb, vdl = None, None     # 2018 skriver 0, inte tomt
                cur.execute("INSERT OR REPLACE INTO distrikt_summa "
                            "VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (ar, val, kod, heltal(r["giltiga"]), heltal(r["ogiltiga"]),
                             heltal(r["rostande"]), rb, vdl, heltal(r["blanka"]),
                             r.get("kalla_fil") or dfil))
                if val == "rd":
                    valkrets_rd[(ar, kod)] = r["valkrets"] or None
                if val == "kf":
                    valkrets_kf[(ar, kod)] = r["valkrets"] or None

    # ---------------- roster/distrikt_summa 2022
    for val in VALEN:
        kalla = os.path.basename(XLSX_2022[val]) + " flik " + FLIK_2022[val]
        for kod, d in gbg22[val].items():
            distriktnamn.setdefault((2022, kod), d["namn"])
            for pk, (pnamn, antal) in d["partier"].items():
                cur.execute("INSERT OR REPLACE INTO roster VALUES (?,?,?,?,?,?,?,?)",
                            (2022, val, kod, pk, pnamn, antal, kalla, kanon(pk)))
            og = (d.get("ogiltiga_ej_anmalda", 0) + d.get("blanka", 0)
                  + d.get("ogiltiga_ovriga", 0))
            rb = d.get("rostberattigade") or None
            if ar_uppsamling(kod, d["namn"]):
                rb = None
            vdl = round(100.0 * d.get("rostande", 0) / rb, 2) if rb else None
            cur.execute("INSERT OR REPLACE INTO distrikt_summa VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (2022, val, kod, d.get("giltiga", 0), og, d.get("rostande", 0),
                         rb, vdl, d.get("blanka", 0), kalla))
            if val == "rd":
                valkrets_rd[(2022, kod)] = d["valkrets"] or None
            if val == "kf":
                valkrets_kf[(2022, kod)] = d["valkrets"] or None

    # ---------------- distrikt
    for (ar, kod), namn in sorted(distriktnamn.items()):
        cur.execute("INSERT OR REPLACE INTO distrikt VALUES (?,?,?,?,?,?,?,?)",
                    (ar, kod, namn, valkrets_rd.get((ar, kod)), valkrets_kf.get((ar, kod)),
                     omrade_av_namn(namn), 1 if ar_uppsamling(kod, namn) else 0,
                     "distrikt_%d_*.csv" % ar if ar != 2022 else "xlsx 2022"))

    # ---------------- aggregat 2002-2018 + 2022
    for ar in [2002, 2006, 2010, 2014, 2018]:
        for val in VALEN:
            fil = "aggregat_%d_%s.csv" % (ar, val)
            if not finns(fil):
                continue
            for r in las(fil):
                cur.execute("INSERT OR REPLACE INTO aggregat "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (ar, val, r["niva"], r["parti"], heltal(r["roster"]),
                             flyt(r["andel"]), r["parti_kalla"], heltal(r["giltiga"]),
                             heltal(r["rostande"]), heltal(r["rostberattigade"]),
                             kanon(r["parti"]), fil))
            ofil = "aggregat_%d_%s_ovriga.csv" % (ar, val)
            if finns(ofil):
                for r in las(ofil):
                    cur.execute("INSERT OR REPLACE INTO aggregat "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                (ar, val, r["niva"] + "|ovriga", r["parti"],
                                 heltal(r["roster"]), flyt(r["andel"]), r["parti_kalla"],
                                 heltal(r["giltiga"]), heltal(r["rostande"]),
                                 heltal(r["rostberattigade"]), kanon(r["parti"]), ofil))
    for val in VALEN:
        kalla = "aggregat_2022_%s.csv (byggd ur %s)" % (val, os.path.basename(XLSX_2022[val]))
        for n in ("riket", "vgregion", "goteborg"):
            v = niva22[val][n]
            for pk, (pnamn, antal) in v["partier"].items():
                andel = round(100.0 * antal / v["giltiga"], 2) if v["giltiga"] else None
                cur.execute("INSERT OR REPLACE INTO aggregat "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (2022, val, n, pk, antal, andel, pnamn, v["giltiga"],
                             v["rostande"], v["rostberattigade"], kanon(pk), kalla))

    # ---------------- crosswalk
    cw = 0
    par_geo = [(2006, 2010), (2010, 2014), (2014, 2018), (2018, 2022),
               (2006, 2022), (2010, 2022), (2014, 2022)]
    for a, b in par_geo:
        fil = "geo_overlap_%d_%d.csv" % (a, b)
        if not finns(fil):
            continue
        for r in las(fil):
            if flyt(r["overlapp_m2"]) in (None, 0.0):
                continue
            cur.execute("INSERT INTO crosswalk VALUES (?,?,?,?,?,?,?,?)",
                        (a, b, r["kod_%d" % a], r["kod_%d" % b],
                         flyt(r["andel_av_%d" % a]), flyt(r["andel_av_%d" % b]),
                         "geo_overlap", fil))
            cw += 1

    par_kedja = [(2006, 2010), (2010, 2014), (2014, 2018), (2018, 2022)]
    for a, b in par_kedja:
        fil = "kedja_%d_%d.csv" % (a, b)
        if not finns(fil):
            continue
        for r in las(fil):
            kf_ = r.get("kod_%d_troligast" % a) or None
            cur.execute("INSERT INTO crosswalk VALUES (?,?,?,?,?,?,?,?)",
                        (a, b, kf_, r["kod_%d" % b], None, None,
                         "kedja:" + (r.get("typ") or ""), fil))
            cw += 1

    if finns("mappning_2018_2022.csv"):
        for r in las("mappning_2018_2022.csv"):
            cur.execute("INSERT INTO crosswalk VALUES (?,?,?,?,?,?,?,?)",
                        (2018, 2022, r["kod_2018"] or None, r["kod_2022"], None,
                         flyt(r["procent"]) / 100.0 if r.get("procent") else None,
                         "mappning_officiell:jamforbart=" + (r.get("jamforbart") or ""),
                         "mappning_2018_2022.csv"))
            cw += 1

    if finns("granskning_2010_fgval_koppling_2006.csv"):
        sett = set()
        for r in las("granskning_2010_fgval_koppling_2006.csv"):
            if not r.get("kod_2006"):
                continue
            nyckel = (r["kod_2006"], r["kod_2010"])
            if nyckel in sett:
                continue
            sett.add(nyckel)
            cur.execute("INSERT INTO crosswalk VALUES (?,?,?,?,?,?,?,?)",
                        (2006, 2010, r["kod_2006"], r["kod_2010"], None, None,
                         "fgval", "granskning_2010_fgval_koppling_2006.csv"))
            cw += 1

    if finns("fgval_matchning_2010_2014.csv"):
        sett = set()
        for r in las("fgval_matchning_2010_2014.csv"):
            if not r.get("kod_2010"):
                continue
            nyckel = (r["kod_2010"], r["kod_2014"])
            if nyckel in sett:
                continue
            sett.add(nyckel)
            cur.execute("INSERT INTO crosswalk VALUES (?,?,?,?,?,?,?,?)",
                        (2010, 2014, r["kod_2010"], r["kod_2014"], None, None,
                         "fgval:" + (r.get("matchning") or ""),
                         "fgval_matchning_2010_2014.csv"))
            cw += 1
    log("crosswalk: %d rader" % cw)

    # ---------------- majorna_medlem
    medlem = {}
    for ar in (2006, 2010, 2014, 2018):
        fil = "geo_majorna_%d.csv" % ar
        for r in las(fil):
            andel = flyt(r["andel_i_majorna"])
            ingar = 1 if (andel is not None and andel >= ANDEL_TROSKEL) else 0
            beslut = ("andel_i_majorna %.4f >= %.2f, tas med" % (andel, ANDEL_TROSKEL)
                      if ingar else
                      "andel_i_majorna %.4f < %.2f, utesluts" % (andel, ANDEL_TROSKEL))
            cur.execute("INSERT OR REPLACE INTO majorna_medlem VALUES (?,?,?,?,?,?,?,?)",
                        (ar, r["kod"], r["namn"], r["klass"], andel, ingar, beslut, fil))
            if ingar:
                medlem.setdefault(ar, []).append(r["kod"])
    for kod in MAJORNA_2022:
        namn = distriktnamn.get((2022, kod), "")
        cur.execute("INSERT OR REPLACE INTO majorna_medlem VALUES (?,?,?,?,?,?,?,?)",
                    (2022, kod, namn, "inne", 1.0, 1,
                     "definitionsmangd: de 23 distrikten 14800526-14800548",
                     "data/valdata_2022.json meta.avgransning"))
    medlem[2022] = list(MAJORNA_2022)
    # 2002 saknar geografi
    for r in las("distrikt_2002_rd.csv"):
        if r["kod"].startswith("148013"):
            cur.execute("INSERT OR REPLACE INTO majorna_medlem VALUES (?,?,?,?,?,?,?,?)",
                        (2002, r["kod"], r["namn"], "ej_geo", None, 0,
                         "ingen shapefil finns for 2002; Karl Johan 1-12 tacker bara "
                         "grovt samma omrade och Stigberget ligger inne i Masthugg 1-8",
                         "docs/historik/noter/val2002.md"))
    for ar in sorted(medlem):
        log("jamforbart Majorna %d: %d distrikt" % (ar, len(medlem[ar])))

    # ---------------- partier
    for ar in (2006, 2010, 2018):
        fil = "partier_%d.csv" % ar
        if not finns(fil):
            continue
        for r in las(fil):
            cur.execute("INSERT INTO partier VALUES (?,?,?,?,?,?)",
                        (ar, r.get("val") or "", r.get("parti_kalla"), r.get("parti"),
                         r.get("namn") or r.get("beteckning"), fil))
    for val in VALEN:
        for pnamn, pk in sorted(PARTI_2022.items(), key=lambda t: t[1]):
            cur.execute("INSERT INTO partier VALUES (?,?,?,?,?,?)",
                        (2022, val, pnamn, pk, pnamn,
                         os.path.basename(XLSX_2022[val])))

    # ---------------- rostberattigade_kategori
    n = 0
    for ar in (2010, 2014, 2018):
        for val in VALEN:
            fil = "rostberattigade_%d_%s.csv" % (ar, val)
            if not finns(fil):
                continue
            for r in las(fil):
                cur.execute("INSERT INTO rostberattigade_kategori VALUES (?,?,?,?,?,?,?,?,?)",
                            (ar, val, r["kod"], r["namn"], r["kon"], r["medborgarskap"],
                             r["aldersgrupp"], heltal(r["antal"]), fil))
                n += 1
    log("rostberattigade_kategori: %d rader" % n)

    # ---------------- fortidsroster
    n = 0
    for ar in (2010, 2014, 2018):
        fil = "fortidsroster_%d.csv" % ar
        if not finns(fil):
            continue
        for r in las(fil):
            cur.execute("INSERT INTO fortidsroster VALUES (?,?,?,?,?,?)",
                        (ar, r["lokalid"], r["lokal"], r["datum"], heltal(r["antal"]), fil))
            n += 1
    log("fortidsroster: %d rader" % n)

    # ---------------- mandat
    n = 0
    for fil, ar, val, nivakol in [("mandat_2006_riksdag.csv", 2006, "rd", None),
                                  ("mandat_2010_riksdag.csv", 2010, "rd", None),
                                  ("mandat_2014_riksdag.csv", 2014, "rd", None),
                                  ("mandat_2014_kf.csv", 2014, "kf", None),
                                  ("mandat_2014_rf.csv", 2014, "rf", None),
                                  ("mandat_2018.csv", 2018, None, "val")]:
        if not finns(fil):
            continue
        for r in las(fil):
            cur.execute("INSERT INTO mandat VALUES (?,?,?,?,?,?,?,?,?)",
                        (heltal(r.get("ar")) or ar, r.get("val") or val,
                         r.get("niva") or "", r.get("valkrets") or "",
                         r.get("parti") or "", heltal(r.get("fasta_mandat")),
                         heltal(r.get("utjamningsmandat")),
                         heltal(r.get("mandat")) or heltal(r.get("mandat_totalt")), fil))
            n += 1
    if finns("mandat_riksdag_riket.csv"):
        for r in las("mandat_riksdag_riket.csv"):
            cur.execute("INSERT INTO mandat VALUES (?,?,?,?,?,?,?,?,?)",
                        (heltal(r["ar"]), "rd", "riket", "HELA LANDET", r["parti"],
                         None, None, heltal(r["mandat"]), "mandat_riksdag_riket.csv"))
            n += 1
    if finns("mandat_valkrets_goteborg.csv"):
        for r in las("mandat_valkrets_goteborg.csv"):
            cur.execute("INSERT INTO mandat VALUES (?,?,?,?,?,?,?,?,?)",
                        (heltal(r["ar"]), r["val"], "goteborg", r["valkrets"], r["parti"],
                         heltal(r["fasta"]), heltal(r["utjamning"]), heltal(r["totalt"]),
                         "mandat_valkrets_goteborg.csv"))
            n += 1
    log("mandat: %d rader" % n)

    con.commit()

    # ---------------- tidsserier
    tid = bygg_tidsserie(cur, medlem, log)
    for rad in tid:
        cur.execute("INSERT OR REPLACE INTO tidsserie VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    rad)
    con.commit()
    skriv_tidsserie(tid, medlem, cur, log)

    fgval_rader = bygg_fgval_serie(cur, medlem, log)
    skriv_fgval(fgval_rader)
    jamfor_metoder(cur, medlem, fgval_rader, log)

    kontroll(cur, vd22, log)
    con.commit()
    con.close()

    with open(os.path.join(SCRATCH, "bygg_databas_logg.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(logg) + "\n")


# ---------------------------------------------------------------- tidsserie

def bygg_tidsserie(cur, medlem, log):
    rader = []
    for ar in sorted(medlem):
        koder = medlem[ar]
        plats = ",".join("?" * len(koder))
        for val in VALEN:
            cur.execute("SELECT parti_kanon, SUM(roster) FROM roster "
                        "WHERE ar=? AND val=? AND kod IN (%s) GROUP BY parti_kanon" % plats,
                        [ar, val] + koder)
            partier = {p: r for p, r in cur.fetchall() if r}
            cur.execute("SELECT SUM(giltiga), SUM(rostande), SUM(rostberattigade) "
                        "FROM distrikt_summa WHERE ar=? AND val=? AND kod IN (%s)" % plats,
                        [ar, val] + koder)
            giltiga, rostande, rb = cur.fetchone()
            if not giltiga:
                continue
            vdl = round(100.0 * rostande / rb, 2) if rb else None
            metod = ("2022 ars 23 distrikt" if ar == 2022 else
                     "areametod: distrikt med andel_i_majorna >= %.2f i geo_majorna_%d.csv"
                     % (ANDEL_TROSKEL, ar))
            summa_huvud = sum(partier.get(p, 0) for p in HUVUDPARTIER)
            for p in sorted(partier):
                rader.append((ar, val, "majorna", p, partier[p],
                              round(100.0 * partier[p] / giltiga, 2), giltiga, rostande,
                              rb, vdl, len(koder), metod))
            rader.append((ar, val, "majorna", "SUMMA_ÖVRIGA", giltiga - summa_huvud,
                          round(100.0 * (giltiga - summa_huvud) / giltiga, 2), giltiga,
                          rostande, rb, vdl, len(koder),
                          metod + "; residual giltiga minus " + "+".join(HUVUDPARTIER)))
            if abs(sum(partier.values()) - giltiga) > 0:
                log("VARNING %d %s Majorna: partisumma %d != giltiga %d"
                    % (ar, val, sum(partier.values()), giltiga))

    # Rostberattigade for Goteborg 2002 saknas i aggregat_2002_*.csv (2002 ars
    # webbsidor redovisar dem inte). De finns daremot i valkretsar_goteborg.csv,
    # hamtade ur RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL i 2006 ars XML.
    rb_2002 = {}
    if finns("valkretsar_goteborg.csv"):
        for r in las("valkretsar_goteborg.csv"):
            if r["ar"] == "2002" and r["rostberattigade"].strip():
                rb_2002[r["val"]] = rb_2002.get(r["val"], 0) + int(r["rostberattigade"])

    # Goteborg och riket ur aggregat
    for ar in AR_ALLA:
        for val in VALEN:
            for niva in ("goteborg", "riket"):
                cur.execute("SELECT parti_kanon, SUM(roster), MAX(giltiga), MAX(rostande),"
                            " MAX(rostberattigade) FROM aggregat "
                            "WHERE ar=? AND val=? AND niva=? GROUP BY parti_kanon",
                            (ar, val, niva))
                rows = cur.fetchall()
                if not rows:
                    continue
                giltiga = max((r[2] or 0) for r in rows)
                rostande = max((r[3] or 0) for r in rows)
                rb = max((r[4] or 0) for r in rows)
                if not giltiga:
                    continue
                extra = ""
                if ar == 2002 and niva == "goteborg" and not rb and val in rb_2002:
                    rb = rb_2002[val]
                    extra = ("; rostberattigade ur valkretsar_goteborg.csv "
                             "(2006 ars XML, RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL)")
                vdl = round(100.0 * rostande / rb, 2) if rb else None
                partier = {r[0]: r[1] for r in rows if r[1]}
                # BLANK och OG ar inte partier
                for icke in ("BLANK", "OG"):
                    partier.pop(icke, None)
                summa_huvud = sum(partier.get(p, 0) for p in HUVUDPARTIER)
                metod = "ur aggregat_%d_%s.csv, niva %s%s" % (ar, val, niva, extra)
                for p in sorted(partier):
                    rader.append((ar, val, niva, p, partier[p],
                                  round(100.0 * partier[p] / giltiga, 2), giltiga,
                                  rostande, rb or None, vdl, None, metod))
                rader.append((ar, val, niva, "SUMMA_ÖVRIGA", giltiga - summa_huvud,
                              round(100.0 * (giltiga - summa_huvud) / giltiga, 2),
                              giltiga, rostande, rb or None, vdl, None,
                              metod + "; residual giltiga minus " + "+".join(HUVUDPARTIER)))
    return rader


def skriv_tidsserie(rader, medlem, cur, log):
    kolumner = ["ar", "val", "parti", "roster", "andel", "giltiga", "rostande",
                "rostberattigade", "valdeltagande", "antal_distrikt", "metod"]
    maj = [r for r in rader if r[2] == "majorna"]
    with open(os.path.join(DATA, "majorna_tidsserie.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(kolumner)
        for r in sorted(maj, key=lambda x: (x[0], x[1], x[3])):
            w.writerow([r[0], r[1], r[3], r[4], r[5], r[6], r[7],
                        r[8] if r[8] is not None else "",
                        r[9] if r[9] is not None else "", r[10], r[11]])

    with open(os.path.join(DATA, "jamforelse_tidsserie.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["ar", "val", "niva"] + kolumner[2:])
        for r in sorted(rader, key=lambda x: (x[0], x[1], x[2], x[3])):
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7],
                        r[8] if r[8] is not None else "",
                        r[9] if r[9] is not None else "",
                        r[10] if r[10] is not None else "", r[11]])

    # metadata: vilka distrikt som ingick, tackningsgrad i yta mot 2022-unionen
    tackning = {}
    for ar in (2006, 2010, 2014, 2018):
        try:
            rows = las("geo_majorna_%d.csv" % ar)
            tackning[ar] = round(sum(flyt(r["andel_av_majorna"]) for r in rows), 4)
        except Exception:
            pass
    tackning[2022] = 1.0

    ut = {
        "meta": {
            "beskrivning": "Tidsserie for Majorna, Goteborg och riket 2002-2022",
            "byggd_av": "scripts/historik/bygg_databas.py",
            "definition_majorna": {
                "2022": "de 23 valdistrikten 14800526-14800548 (valdata_2022.json)",
                "tidigare_ar": ("distrikt i geo_majorna_<ar>.csv med andel_i_majorna >= %.2f"
                                % ANDEL_TROSKEL),
                "2002": ("ingen geografi finns for 2002; aret ingar inte i "
                         "Majorna-serien, bara i Goteborg och riket"),
            },
            "huvudpartier": HUVUDPARTIER,
            "distrikt_per_ar": {str(a): sorted(medlem[a]) for a in sorted(medlem)},
            "antal_distrikt_per_ar": {str(a): len(medlem[a]) for a in sorted(medlem)},
            "tackningsgrad_yta_mot_2022_unionen": {str(a): tackning[a]
                                                   for a in sorted(tackning)},
        },
        "serier": [],
    }
    for r in sorted(rader, key=lambda x: (x[2], x[0], x[1], x[3])):
        ut["serier"].append({
            "ar": r[0], "val": r[1], "niva": r[2], "parti": r[3], "roster": r[4],
            "andel": r[5], "giltiga": r[6], "rostande": r[7], "rostberattigade": r[8],
            "valdeltagande": r[9], "antal_distrikt": r[10], "metod": r[11],
        })
    with open(os.path.join(DATA, "majorna_tidsserie.json"), "w", encoding="utf-8") as f:
        json.dump(ut, f, ensure_ascii=False, indent=1)
    log("majorna_tidsserie.csv: %d rader, jamforelse_tidsserie.csv: %d rader"
        % (len(maj), len(rader)))


# ---------------------------------------------------------------- FGVAL-serie

def bygg_fgval_serie(cur, medlem, log):
    """Alternativ serie: foregaende vals roster uttryckta i det senare arets distrikt.

    2006 lases ur fgval_2010_<val>.csv summerad over 2010 ars Majornadistrikt,
    2010 ur fgval_2014_<val>.csv summerad over 2014 ars Majornadistrikt.
    fgval_2014_rf.csv avser omvalet 2011 (se granskning_2010.md) och anvands inte.
    Raderna GILTIGA, BLANK, OG, SUMMA_ROSTER och ROSTBERATTIGADE ar summor, inte
    partier, och raknas inte som roster.
    """
    ut = []
    for ar_fg, ar_bar, valen in [(2006, 2010, VALEN), (2010, 2014, ["rd", "kf"])]:
        koder = set(medlem[ar_bar])
        for val in valen:
            fil = "fgval_%d_%s.csv" % (ar_bar, val)
            if not finns(fil):
                continue
            summa = {}
            trackade = set()
            giltiga_rad = 0
            for r in las(fil):
                kod = r["kod_%d" % ar_bar]
                if kod not in koder:
                    continue
                v = r["roster_fgval"]
                if v is None or str(v).strip() == "":
                    continue
                if r["parti"] in FGVAL_PSEUDO:
                    if r["parti"] == "GILTIGA":
                        giltiga_rad += int(v)
                        trackade.add(kod)
                    continue
                trackade.add(kod)
                summa[kanon(r["parti"])] = summa.get(kanon(r["parti"]), 0) + int(v)

            # giltiga: GILTIGA-raden om den finns, annars deltagandefilen
            giltiga = giltiga_rad
            dfil = "fgval_%d_%s_deltagande.csv" % (ar_bar, val)
            if not giltiga and finns(dfil):
                for r in las(dfil):
                    if r["kod_%d" % ar_bar] in koder and r["giltiga_fgval"].strip():
                        giltiga += int(r["giltiga_fgval"])
            if not giltiga:
                giltiga = sum(summa.values())
            saknar = len(koder - trackade)
            for p in sorted(summa):
                ut.append((ar_fg, val, p, summa[p],
                           round(100.0 * summa[p] / giltiga, 2) if giltiga else None,
                           giltiga, len(trackade), saknar,
                           "FGVAL i %s summerad over %d ars jamforbara Majornadistrikt"
                           % (fil, ar_bar)))
            log("fgval-serie %d %s: %d distrikt med FGVAL av %d, %d utan, giltiga %d, "
                "partisumma %d" % (ar_fg, val, len(trackade), len(koder), saknar,
                                   giltiga, sum(summa.values())))
    return ut


def skriv_fgval(rader):
    with open(os.path.join(DATA, "majorna_tidsserie_fgval.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["ar", "val", "parti", "roster", "andel", "giltiga",
                    "antal_distrikt_med_fgval", "antal_distrikt_utan_fgval", "metod"])
        for r in rader:
            w.writerow(list(r))


def jamfor_metoder(cur, medlem, fgval_rader, log):
    """Skillnaden mellan areametoden och FGVAL-kedjan, parti for parti."""
    fg = {}
    for ar, val, parti, roster, andel, giltiga, med, utan, metod in fgval_rader:
        fg.setdefault((ar, val), {})[parti] = roster

    ut = []
    for (ar, val), partier in sorted(fg.items()):
        cur.execute("SELECT parti, roster FROM tidsserie WHERE ar=? AND val=? "
                    "AND niva='majorna'", (ar, val))
        area = dict(cur.fetchall())
        for p in sorted(set(partier) | set(area)):
            a = area.get(p)
            f = partier.get(p)
            ut.append([ar, val, p, a if a is not None else "",
                       f if f is not None else "",
                       (f - a) if (a is not None and f is not None) else ""])

    # For 2010 ar FGVAL-kedjan ofullstandig. Jamfor darfor bara de 2010-distrikt
    # vars 2014-motsvarighet har FGVAL, mot samma distrikts faktiska 2010-tal.
    matchning = {}
    if finns("fgval_matchning_2010_2014.csv"):
        for r in las("fgval_matchning_2010_2014.csv"):
            if r.get("kod_2010"):
                matchning.setdefault(r["kod_2014"], r["kod_2010"])
    delrader = []
    for val in ("rd", "kf"):
        fil = "fgval_2014_%s.csv" % val
        if not finns(fil):
            continue
        med_fgval_2014 = set()
        summa_fg = {}
        for r in las(fil):
            if r["kod_2014"] not in set(medlem[2014]):
                continue
            v = r["roster_fgval"]
            if not str(v).strip():
                continue
            med_fgval_2014.add(r["kod_2014"])
            if r["parti"] in FGVAL_PSEUDO:
                continue
            summa_fg[kanon(r["parti"])] = summa_fg.get(kanon(r["parti"]), 0) + int(v)
        koder_2010 = sorted({matchning[k] for k in med_fgval_2014 if k in matchning})
        if not koder_2010:
            continue
        plats = ",".join("?" * len(koder_2010))
        cur.execute("SELECT parti_kanon, SUM(roster) FROM roster WHERE ar=2010 AND val=? "
                    "AND kod IN (%s) GROUP BY parti_kanon" % plats, [val] + koder_2010)
        fakta = dict(cur.fetchall())
        avvik = 0
        for p in sorted(set(summa_fg) | set(fakta)):
            d = (summa_fg.get(p, 0) - fakta.get(p, 0))
            if d:
                avvik += 1
            delrader.append([2010, val, p, fakta.get(p, 0), summa_fg.get(p, 0), d])
        log("delmangdsjamforelse 2010 %s: %d 2014-distrikt med FGVAL, %d 2010-distrikt, "
            "%d partier med avvikelse" % (val, len(med_fgval_2014), len(koder_2010), avvik))

    with open(os.path.join(DATA, "majorna_metodjamforelse.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["ar", "val", "parti", "roster_areametod", "roster_fgval",
                    "skillnad", "omfattning"])
        for r in ut:
            w.writerow(r + ["hela jamforbara Majorna"])
        for r in delrader:
            w.writerow(r + ["delmangd: bara distrikt dar FGVAL finns"])
    log("majorna_metodjamforelse.csv: %d rader" % (len(ut) + len(delrader)))


# ---------------------------------------------------------------- kontroller

def kontroll(cur, vd22, log):
    fel = 0
    # 1. V i Majorna 2022 kommunval ska bli 34.6 procent
    cur.execute("SELECT roster, andel, giltiga FROM tidsserie "
                "WHERE ar=2022 AND val='kf' AND niva='majorna' AND parti='V'")
    rad = cur.fetchone()
    log("kontroll V Majorna 2022 kf: %s roster, %s procent av %s giltiga"
        % (rad[0], rad[1], rad[2]))
    if rad[0] != 7479 or abs(rad[1] - 34.6) > 0.05:
        log("FEL: V 2022 kf stammer inte med valdata_2022.json (7479 av 21620 = 34.59)")
        fel += 1

    # 2. Majorna 2022 mot valdata_2022.json aggregat
    for val in VALEN:
        agg = vd22["aggregat"]["majorna"][val]
        cur.execute("SELECT MAX(giltiga), MAX(rostande), MAX(rostberattigade) "
                    "FROM tidsserie WHERE ar=2022 AND val=? AND niva='majorna'", (val,))
        g, ro, rb = cur.fetchone()
        if (g, ro, rb) != (agg["giltiga"], agg["rostande"], agg["rostberattigade"]):
            log("FEL 2022 %s: databasen %s mot valdata_2022.json %s"
                % (val, (g, ro, rb), (agg["giltiga"], agg["rostande"],
                                      agg["rostberattigade"])))
            fel += 1
    # 3. de 23 distriktens partitals mot json
    n = 0
    for d in vd22["distrikt"]:
        for val in VALEN:
            for p, v in d[val].items():
                if p == "Övriga":
                    continue
                cur.execute("SELECT roster FROM roster WHERE ar=2022 AND val=? AND kod=? "
                            "AND parti=?", (val, d["kod"], p))
                r = cur.fetchone()
                if not r or r[0] != v:
                    log("FEL 2022 %s %s %s: db %s mot json %s"
                        % (val, d["kod"], p, r, v))
                    fel += 1
                n += 1
    log("kontroll: %d partital i de 23 distrikten jamforda med valdata_2022.json" % n)

    # 4. partisumma = giltiga per distrikt och val
    cur.execute("""
        SELECT r.ar, r.val, COUNT(*) FROM (
          SELECT ar, val, kod, SUM(roster) s FROM roster GROUP BY ar, val, kod
        ) r JOIN distrikt_summa d
          ON d.ar=r.ar AND d.val=r.val AND d.kod=r.kod
        WHERE r.s <> d.giltiga GROUP BY r.ar, r.val""")
    for ar, val, c in cur.fetchall():
        log("VARNING partisumma != giltiga: %d %s, %d distrikt" % (ar, val, c))

    # 5. giltiga + ogiltiga = rostande
    cur.execute("SELECT ar, val, COUNT(*) FROM distrikt_summa "
                "WHERE giltiga + ogiltiga <> rostande GROUP BY ar, val")
    for ar, val, c in cur.fetchall():
        log("VARNING giltiga+ogiltiga != rostande: %d %s, %d distrikt" % (ar, val, c))

    # 6. antal distrikt per ar
    cur.execute("SELECT ar, COUNT(*), SUM(uppsamlingsdistrikt) FROM distrikt GROUP BY ar")
    for ar, c, u in cur.fetchall():
        log("distrikt %d: %d rader varav %d uppsamlingsdistrikt" % (ar, c, u or 0))

    log("kontroller klara, %d fel" % fel)
    return fel


if __name__ == "__main__":
    sys.exit(main())
