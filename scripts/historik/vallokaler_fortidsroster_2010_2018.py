#!/usr/bin/env python3
"""Vallokaler och mottagna förtidsröster i Göteborgs kommun 2010, 2014 och 2018.

Läser Valmyndighetens filer "vallokal" (en rad per valdistrikt med vallokal,
adress och koordinater) och "mottagna_fortidsroster" (en rad per
förtidsröstningslokal med antal mottagna röster per dag), filtrerar
Göteborg (län 14, kommun 80) och skriver till data/historik/:

  vallokaler_<år>.csv                   en rad per valdistrikt, normaliserade kolumner (alla källkolumner medtagna)
  vallokaler_<år>_lokaler.csv           en rad per vallokal (namn + gatuadress) med de distrikt som röstar där
  fortidsroster_<år>.csv                långt format ar;lokalid;lokal;datum;antal, plus en rad datum=totalt per lokal (källans Totalt)
  fortidsroster_<år>_lokaler.csv        en rad per lokal: totalt, antal dagar, första/sista dag, rang i Göteborg, andel
  fortidsroster_per_dag_2010_2018.csv   Göteborg och riket per dag (riket = källans egen summarad)
  fortidsroster_majornaomradet_2010_2018.csv  lokaler i eller nära Majorna med totalt, rang och andel

Körs med venv-python (behöver xlrd, openpyxl och pyproj):
  python scripts/historik/vallokaler_fortidsroster_2010_2018.py
"""
import csv
import datetime as dt
import os
import re
import sys

import openpyxl
import xlrd
from pyproj import Transformer

HIST = "/Users/daniel/code/Temp/Historiska dokument/"
REPARERAD = ("/Users/daniel/code/Temp/Historiska dokument/repaired/")
UT = "/Users/daniel/code/Temp/data/historik/"
LAN = 14
KOM = 80

# Vallokaler: (år, källfil). Kolumnuppsättningen skiljer sig mellan 2010 och 2014/2018, se MAPPNING nedan.
VALLOKAL_KALLOR = {
    2010: HIST + "vallokal (2).xls",
    2014: HIST + "vallokal (1).xls",
    2018: REPARERAD + "2018_vallokal.xlsx",   # reparerad kopia av Historiska dokument/vallokal.xls
}

# Mottagna förtidsröster: (år, källfil). Samma kolumnuppsättning alla tre åren
# (lan, län, kom, kommun, lokalid, lokal, en kolumn per datum, Totalt) och en sista rad "summa" för riket.
FORTID_KALLOR = {
    2010: HIST + "mottagna_fortidsroster (2).xls",
    2014: HIST + "mottagna_fortidsroster (1).xls",
    2018: REPARERAD + "2018_mottagna_fortidsroster.xlsx",   # reparerad kopia av Historiska dokument/mottagna_fortidsroster.xls
}

VALDAG = {2010: "2010-09-19", 2014: "2014-09-14", 2018: "2018-09-09"}

# Förtidsröstningslokaler i eller nära Majornaområdet, per lokalid (samma lokalid återkommer mellan åren
# när lokalen är densamma). Placeringen bygger på lokalens namn; där adressen går att belägga i
# vallokalsfilen (samma lokal används som vallokal på valdagen) anges det.
MAJORNA_LOKALER = {
    "8357":  ("Majornas bibliotek", "Majorna", "i Majorna (Chapmans torg), adress saknas i källan, allmän kännedom"),
    "12807": ("Dalheimers hus", "Majorna", "i Majorna, Slottskogsgatan 12 enligt vallokalsfilen 2010 och 2014"),
    "14133": ("Gråbergets vård- och äldreboende", "Majorna", "i Majorna (Gråberget), Stortoppsgatan 2 enligt vallokalsfilen 2010 och 2018, institutionsröstning"),
    "14228": ("Gråbergets vård och äldreboende", "Majorna", "i Majorna (Gråberget), Stortoppsgatan 2 enligt vallokalsfilen 2010 och 2018, institutionsröstning"),
    "6929":  ("Svaleboskogens äldreboende", "Majorna", "i Kungsladugård (Svaleboskogen), adress saknas i källan, allmän kännedom, institutionsröstning"),
    "8351":  ("Linnéstadens bibliotek", "Linné", "nära, Linnéstaden (Tredje Långgatan), adress saknas i källan, allmän kännedom"),
    "14137": ("Vegahusen 55", "Linné", "nära, Linnéplatsen, Vegagatan 55 enligt vallokalsfilen 2014 och 2018, institutionsröstning"),
    "14223": ("Stiftelsen Vegahusen 55", "Linné", "nära, Linnéplatsen, Vegagatan 55 enligt vallokalsfilen 2014 och 2018, institutionsröstning"),
    "6869":  ("Annedals äldreboende", "Annedal", "nära, Annedal, Carl Grimbergsgatan 11 enligt vallokalsfilen 2014, institutionsröstning"),
    "15638": ("Annedals äldreboende", "Annedal", "nära, Annedal, Carl Grimbergsgatan 11 enligt vallokalsfilen 2014, institutionsröstning"),
    "6940":  ("Änggårdsbackens äldreboende", "Änggården", "nära, Änggården, adress saknas i källan, allmän kännedom, institutionsröstning"),
    "6926":  ("Stiftelsen Neuberghska ålderdomshemmet", "osäker", "placering inte verifierad, adress saknas i källan, institutionsröstning"),
    "6913":  ("Majstångshemmet äldreboende", "osäker", "placering inte verifierad, adress saknas i källan, institutionsröstning"),
}

# RT90 2,5 gon V (EPSG:3021) till WGS84 (EPSG:4326). I källan är X nordlig koordinat och Y östlig.
RT90_TILL_WGS84 = Transformer.from_crs("EPSG:3021", "EPSG:4326", always_xy=True)


def las_blad(fil):
    """Returnerar (rubriker, rader) från första bladet i en xls- eller xlsx-fil."""
    if fil.endswith(".xls"):
        sh = xlrd.open_workbook(fil).sheet_by_index(0)
        hdr = [sh.cell_value(0, c) for c in range(sh.ncols)]
        rader = [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(1, sh.nrows)]
        return hdr, rader
    ws = openpyxl.load_workbook(fil, read_only=True, data_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True)
    hdr = list(next(it))
    return hdr, [list(r) for r in it]


def tom(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


def text(v):
    if tom(v):
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def heltal(v, fil, sammanhang):
    if tom(v):
        return 0
    if isinstance(v, bool) or not isinstance(v, (int, float)) or float(v) != int(v):
        sys.exit(f"Inte ett heltal i {fil} ({sammanhang}): {v!r}")
    return int(v)


MANADER = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
           "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}


def iso_datum(v, fil):
    """Datum i källorna: 20100919.0 (VALDAG 2010), 100919.0 (DAG 2010 och 2014),
    '14-SEP-14' (VALDAG_R/L/K 2014), '2018-09-09' (2018). Tomt ger tom sträng."""
    if tom(v):
        return ""
    if isinstance(v, (int, float)):
        s = str(int(v))
        if len(s) == 8:
            return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
        if len(s) == 6:
            return f"20{s[0:2]}-{s[2:4]}-{s[4:6]}"
        sys.exit(f"Okänt datumformat i {fil}: {v!r}")
    s = str(v).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    m = re.fullmatch(r"(\d{2})-([A-Z]{3})-(\d{2})", s.upper())
    if m:
        return f"20{m.group(3)}-{MANADER[m.group(2)]:02d}-{int(m.group(1)):02d}"
    sys.exit(f"Okänt datumformat i {fil}: {v!r}")


def skriv_csv(namn, rubriker, rader):
    vag = os.path.join(UT, namn)
    with open(vag, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(rubriker)
        w.writerows(rader)
    print(f"  skrev {vag} ({len(rader)} rader)")


# ----------------------------------------------------------------------------------------------
# Vallokaler
# ----------------------------------------------------------------------------------------------

VALLOKAL_RUBRIKER = [
    "ar", "kod", "namn", "kommunvalkrets_kod", "kommunvalkrets", "lokal", "adress1", "adress2", "adress3",
    "postort", "tillganglighet", "status", "x_rt90", "y_rt90", "latitud", "longitud", "koord_kalla",
    "valdag", "dag", "oppetpass", "aktiv_rd", "aktiv_rf", "aktiv_kf", "aktiv_eu", "valdag_eu",
    "kommun_klar", "lokal_klar", "valnamnd", "hemsida", "telnr", "kalla_fil",
]


def kolumnindex(hdr, fil):
    """Index per rubrik. Rubriken KLAR förekommer två gånger 2010 och 2014 (kommunens respektive
    lokalens klarmarkering); den första blir KLAR, den andra KLAR_2."""
    idx = {}
    for i, h in enumerate(hdr):
        h = str(h)
        if h in idx:
            if h == "KLAR" and "KLAR_2" not in idx:
                idx["KLAR_2"] = i
            else:
                sys.exit(f"Oväntad dubbel rubrik {h!r} i {fil}")
        else:
            idx[h] = i
    return idx


def las_vallokaler(ar, fil):
    hdr, rader = las_blad(fil)
    ix = kolumnindex(hdr, fil)
    g = lambda r, k: r[ix[k]] if k in ix else None
    ut = []
    kontroll_datum = set()
    for r in rader:
        if tom(g(r, "LAN")) or int(g(r, "LAN")) != LAN or int(g(r, "KOMMUN")) != KOM:
            continue
        kod = f"{int(g(r, 'LAN')):02d}{int(g(r, 'KOMMUN')):02d}{int(g(r, 'VALDISTRIKT')):04d}"
        if ar == 2010:
            krets_kod, krets = g(r, "VALKRETS"), g(r, "NAMN_VALKRETS")
            valdag = iso_datum(g(r, "VALDAG"), fil)
            aktiv = ("", "", "", "")
            valdag_eu = ""
            kommun_klar, lokal_klar = g(r, "KLAR"), g(r, "KLAR_2")
        else:
            krets_kod, krets = g(r, "KRETS_K"), g(r, "KRETS_NAMN_K")
            valdag = iso_datum(g(r, "VALDAG_R"), fil)
            kontroll_datum.add((valdag, iso_datum(g(r, "VALDAG_L"), fil), iso_datum(g(r, "VALDAG_K"), fil)))
            aktiv = (g(r, "AKTIV_R"), g(r, "AKTIV_L"), g(r, "AKTIV_K"), g(r, "AKTIV_E"))
            valdag_eu = iso_datum(g(r, "VALDAG_E"), fil)
            if ar == 2014:
                kommun_klar, lokal_klar = g(r, "KLAR"), g(r, "KLAR_2")
            else:
                kommun_klar, lokal_klar = g(r, "KOMMUN_KLAR"), g(r, "LOKAL_KLAR")
        krets_kod = f"{LAN:02d}{KOM:02d}{int(krets_kod):02d}"
        if ar == 2018:
            lat, lon = g(r, "LATITUD"), g(r, "LONGITUD")
            x = y = ""
            lat, lon = f"{float(lat):.6f}", f"{float(lon):.6f}"
            koord = "WGS84 (LATITUD, LONGITUD i källan)"
        else:
            x, y = int(g(r, "X")), int(g(r, "Y"))
            lon, lat = RT90_TILL_WGS84.transform(y, x)   # RT90: X nord, Y öst
            lat, lon = f"{lat:.6f}", f"{lon:.6f}"
            koord = "RT90 2,5 gon V (X, Y i källan), WGS84 omräknad med pyproj EPSG:3021 till 4326"
        ut.append([
            ar, kod, text(g(r, "NAMN_VALDISTRIKT")), krets_kod, text(krets), text(g(r, "LOKAL")),
            text(g(r, "ADRESS1")), text(g(r, "ADRESS2")), text(g(r, "ADRESS3")), text(g(r, "POSTORT")),
            text(g(r, "TILLGÄNGL")), text(g(r, "STATUS")), x, y, lat, lon, koord,
            valdag, iso_datum(g(r, "DAG"), fil), text(g(r, "ÖPPETPASS")),
            text(aktiv[0]), text(aktiv[1]), text(aktiv[2]), text(aktiv[3]), valdag_eu,
            text(kommun_klar), text(lokal_klar), text(g(r, "VALNAMND")), text(g(r, "HEMSIDA")), text(g(r, "TELNR")),
            os.path.basename(fil),
        ])
    for a, b, c in kontroll_datum:
        if not a == b == c:
            sys.exit(f"Olika valdagar för R, L och K i {fil}: {a} {b} {c}")
    koder = [r[1] for r in ut]
    if len(koder) != len(set(koder)):
        sys.exit(f"Dubbla distriktskoder i {fil}")
    ut.sort(key=lambda r: r[1])
    return hdr, ut


def lokaler_per_ar(ar, rader):
    """En rad per vallokal (LOKAL + ADRESS2) med antal distrikt och koder."""
    grupper = {}
    for r in rader:
        nyckel = (r[5], r[7])
        grupper.setdefault(nyckel, []).append(r)
    ut = []
    for (lokal, adress), rr in sorted(grupper.items()):
        lat = sorted(set(x[14] for x in rr))
        lon = sorted(set(x[15] for x in rr))
        ut.append([ar, lokal, adress, len(rr), " ".join(x[1] for x in rr), " | ".join(x[2] for x in rr),
                   lat[0], lon[0], len(lat) if len(lat) > 1 or len(lon) > 1 else 1])
    return ut


def kontroll_mot_distriktfiler(ar, koder):
    """Jämför distriktskoderna med distrikt_<år>_<val>.csv från andra delmoment, om de finns."""
    for val in ("rd", "rf", "kf"):
        fil = os.path.join(UT, f"distrikt_{ar}_{val}.csv")
        if not os.path.exists(fil):
            print(f"  kontroll {os.path.basename(fil)}: finns inte")
            continue
        with open(fil, encoding="utf-8") as f:
            andra = {r["kod"]: r.get("namn", "") for r in csv.DictReader(f, delimiter=";")}
        bara_dar = sorted(set(andra) - set(koder))
        bara_har = sorted(set(koder) - set(andra))
        print(f"  kontroll {os.path.basename(fil)}: gemensamma {len(set(andra) & set(koder))}, "
              f"bara i distriktfilen {bara_dar} , bara i vallokalsfilen {bara_har}")


# ----------------------------------------------------------------------------------------------
# Förtidsröster
# ----------------------------------------------------------------------------------------------

def las_fortidsroster(ar, fil):
    hdr, rader = las_blad(fil)
    hdr = [str(h) for h in hdr]
    if hdr[:6] != ["lan", "län", "kom", "kommun", "lokalid", "lokal"] or hdr[-1] != "Totalt":
        sys.exit(f"Oväntade rubriker i {fil}: {hdr}")
    datum = hdr[6:-1]
    for d in datum:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            sys.exit(f"Oväntad datumkolumn {d!r} i {fil}")
    if datum[-1] != VALDAG[ar]:
        sys.exit(f"Sista datumkolumnen {datum[-1]} är inte valdagen {VALDAG[ar]} i {fil}")
    goteborg = []
    riket_summa = None
    riket_beraknad = [0] * len(datum)
    riket_tot = 0
    for r in rader:
        if tom(r[0]):
            if str(r[5]).strip().lower() == "summa":
                riket_summa = [heltal(v, fil, "summa " + d) for v, d in zip(r[6:-1], datum)]
                riket_summa_tot = heltal(r[-1], fil, "summa Totalt")
                continue
            sys.exit(f"Oväntad rad utan län i {fil}: {r[:6]}")
        tal = [heltal(v, fil, f"{r[4]} {d}") for v, d in zip(r[6:-1], datum)]
        tot = heltal(r[-1], fil, f"{r[4]} Totalt")
        if sum(tal) != tot:
            sys.exit(f"Summan av dagarna ({sum(tal)}) stämmer inte med Totalt ({tot}) för lokal {r[4]} i {fil}")
        for i, v in enumerate(tal):
            riket_beraknad[i] += v
        riket_tot += tot
        if int(r[0]) == LAN and int(r[2]) == KOM:
            goteborg.append((text(r[4]), text(r[5]), tal, tot))
    if riket_summa is None:
        sys.exit(f"Ingen summarad i {fil}")
    if riket_summa != riket_beraknad or riket_summa_tot != riket_tot:
        print(f"  OBS: källans summarad skiljer sig från summan av raderna i {os.path.basename(fil)}: "
              f"{riket_summa_tot} mot {riket_tot}")
    else:
        print(f"  summarad för riket stämmer med summan av alla lokaler ({riket_tot})")
    lokalid = [g[0] for g in goteborg]
    if len(lokalid) != len(set(lokalid)):
        sys.exit(f"Dubbla lokalid för Göteborg i {fil}")
    goteborg.sort(key=lambda g: int(g[0]))
    return datum, goteborg, riket_summa, riket_summa_tot


def main():
    os.makedirs(UT, exist_ok=True)
    print("Vallokaler")
    vallokaler = {}
    for ar, fil in VALLOKAL_KALLOR.items():
        hdr, rader = las_vallokaler(ar, fil)
        vallokaler[ar] = rader
        print(f" {ar}: {os.path.basename(fil)}, {len(hdr)} kolumner: {hdr}")
        print(f"  göteborgsdistrikt: {len(rader)}, vallokaler (namn+adress): "
              f"{len(set((r[5], r[7]) for r in rader))}, unika lokalnamn: {len(set(r[5] for r in rader))}")
        skriv_csv(f"vallokaler_{ar}.csv", VALLOKAL_RUBRIKER, rader)
        skriv_csv(f"vallokaler_{ar}_lokaler.csv",
                  ["ar", "lokal", "adress", "antal_distrikt", "koder", "distriktnamn", "latitud", "longitud", "antal_koordinater"],
                  lokaler_per_ar(ar, rader))
        kontroll_mot_distriktfiler(ar, [r[1] for r in rader])

    # Kontroll av koordinatomräkningen: samma lokalnamn och adress 2014 (RT90 omräknad) och 2018 (WGS84 i källan).
    print(" koordinatkontroll 2014 (omräknad RT90) mot 2018 (källans WGS84), samma lokal och adress:")
    l14 = {(r[5], r[7]): (float(r[14]), float(r[15])) for r in vallokaler[2014]}
    l18 = {(r[5], r[7]): (float(r[14]), float(r[15])) for r in vallokaler[2018]}
    avst = []
    for k in sorted(set(l14) & set(l18)):
        dlat = (l14[k][0] - l18[k][0]) * 111_000
        dlon = (l14[k][1] - l18[k][1]) * 111_000 * 0.534   # cos(57,7 grader)
        avst.append(((dlat ** 2 + dlon ** 2) ** 0.5, k))
    avst.sort()
    if avst:
        print(f"  {len(avst)} gemensamma lokaler, median {avst[len(avst) // 2][0]:.0f} m, "
              f"max {avst[-1][0]:.0f} m ({avst[-1][1]})")
        for a, k in avst[-3:]:
            print(f"   {a:.0f} m {k}")
    for k in [("Karl Johansskolan", "Koopmansgatan 14-16"), ("Kungsladugårdsskolan", "Birger Jarlsgat. 1, entré B")]:
        if k in l14 and k in l18:
            print(f"  {k}: 2014 omräknad {l14[k]}, 2018 källa {l18[k]}")

    print("Förtidsröster")
    per_dag = []
    lokaler_alla = {}
    for ar, fil in FORTID_KALLOR.items():
        datum, goteborg, riket_summa, riket_tot = las_fortidsroster(ar, fil)
        gbg_tot = sum(g[3] for g in goteborg)
        gbg_per_dag = [sum(g[2][i] for g in goteborg) for i in range(len(datum))]
        print(f" {ar}: {os.path.basename(fil)}, {len(datum)} datumkolumner {datum[0]} till {datum[-1]}, "
              f"valdag {VALDAG[ar]}, göteborgslokaler {len(goteborg)}, Göteborg totalt {gbg_tot}, riket {riket_tot}")
        print(f"  lokaler med 0 röster: {[g[0] + ' ' + g[1] for g in goteborg if g[3] == 0]}")
        print(f"  dagar med mottagna röster i Göteborg: {sum(1 for v in gbg_per_dag if v > 0)} av {len(datum)}")
        # långt format
        langa = []
        for lokalid, lokal, tal, tot in goteborg:
            for d, v in zip(datum, tal):
                langa.append([ar, lokalid, lokal, d, v])
            langa.append([ar, lokalid, lokal, "totalt", tot])
        skriv_csv(f"fortidsroster_{ar}.csv", ["ar", "lokalid", "lokal", "datum", "antal"], langa)
        # per lokal med rang
        ordnade = sorted(goteborg, key=lambda g: -g[3])
        rang = {}
        for i, g in enumerate(ordnade):
            rang[g[0]] = rang.get(g[0]) or (i + 1 if i == 0 or g[3] != ordnade[i - 1][3] else rang[ordnade[i - 1][0]])
        summar = []
        for lokalid, lokal, tal, tot in goteborg:
            dagar = [d for d, v in zip(datum, tal) if v > 0]
            summar.append([ar, lokalid, lokal, tot, len(dagar), dagar[0] if dagar else "", dagar[-1] if dagar else "",
                           rang[lokalid], f"{100 * tot / gbg_tot:.2f}", max(tal), datum[tal.index(max(tal))] if tot else "",
                           tal[-1]])
            lokaler_alla[(ar, lokalid)] = (lokal, tot, len(dagar), rang[lokalid], 100 * tot / gbg_tot)
        skriv_csv(f"fortidsroster_{ar}_lokaler.csv",
                  ["ar", "lokalid", "lokal", "totalt", "antal_dagar", "forsta_dag", "sista_dag", "rang_goteborg",
                   "andel_goteborg_procent", "storsta_dag_antal", "storsta_dag", "antal_valdagen"], summar)
        summar_topp = sorted(summar, key=lambda s: s[7])[:5]
        print("  fem största: " + "; ".join(f"{s[2]} {s[3]}" for s in summar_topp))
        for i, d in enumerate(datum):
            dagar_kvar = (dt.date.fromisoformat(VALDAG[ar]) - dt.date.fromisoformat(d)).days
            per_dag.append([ar, d, i + 1, dagar_kvar, dt.date.fromisoformat(d).strftime("%a"), gbg_per_dag[i],
                            sum(1 for g in goteborg if g[2][i] > 0), riket_summa[i]])
        per_dag.append([ar, "totalt", "", "", "", gbg_tot, len(goteborg), riket_tot])
    skriv_csv("fortidsroster_per_dag_2010_2018.csv",
              ["ar", "datum", "dag_nr", "dagar_till_valdag", "veckodag", "goteborg", "goteborg_lokaler_med_roster",
               "riket_summarad_kalla"], per_dag)

    majorna = []
    for (ar, lokalid), (lokal, tot, dagar, rang, andel) in sorted(lokaler_alla.items(), key=lambda k: (k[0][0], int(k[0][1]))):
        if lokalid in MAJORNA_LOKALER:
            namn, omrade, placering = MAJORNA_LOKALER[lokalid]
            majorna.append([ar, lokalid, lokal, omrade, placering, tot, dagar, rang, f"{andel:.2f}"])
    skriv_csv("fortidsroster_majornaomradet_2010_2018.csv",
              ["ar", "lokalid", "lokal", "omrade", "placering", "totalt", "antal_dagar", "rang_goteborg",
               "andel_goteborg_procent"], majorna)
    # Namn i källan som inte används i MAJORNA_LOKALER men som innehåller ledtrådar till området
    print(" lokalnamn med Majorna-ledtrådar som inte är med i MAJORNA_LOKALER:")
    for (ar, lokalid), (lokal, *_rest) in sorted(lokaler_alla.items()):
        if lokalid not in MAJORNA_LOKALER and re.search(
                r"major|kungsladug|stigberg|masthugg|linn|järntorg|sanna|gråberg|klippan|dalheimer|slottsskog", lokal, re.I):
            print(f"  {ar} {lokalid} {lokal}")


if __name__ == "__main__":
    main()
