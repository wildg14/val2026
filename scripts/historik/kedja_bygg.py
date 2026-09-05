#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kedja_bygg.py - kedjekontroll av jamforbarhet mellan valen 2006, 2010, 2014, 2018 och 2022
for Goteborgs kommun (1480).

Bygger:
  data/historik/kedja_2006_2010.csv
  data/historik/kedja_2010_2014.csv
  data/historik/kedja_2014_2018.csv
  data/historik/kedja_2018_2022.csv
  data/historik/kedja_majorna_2006_2022.csv

Metod i korthet:
  1. Valmyndighetens FGVAL (foregaende vals roster uttryckta i aktuella distrikt) matchas
     mot foregaende vals faktiska tal per distrikt och parti. Exakt traff pa vektorn
     (M, C, L, KD, S, V, MP, SD) i bade riksdags- och kommunvalet ger identitet.
  2. Namnjamforelse pa kardelen av namnet (delen efter forsta ", ", dvs utan
     stadsdelsnamnds- eller valkretsprefix).
  3. Geometriskt overlapp ur geo_overlap_<ar1>_<ar2>.csv.
  4. For 2014->2018 finns ingen FGVAL, da anvands Valmyndighetens skv-mappning.
     For 2018->2022 anvands Goteborgs stads jamforelsefil (mappning_2018_2022.csv)
     plus geometri.

Kors med:
  /Users/daniel/code/Temp/.venv/bin/python \
      /Users/daniel/code/Temp/scripts/historik/kedja_bygg.py
"""

import csv
import json
import os
import re
import sys
import collections

# ---------------------------------------------------------------- konstanter

DATA = "/Users/daniel/code/Temp/data/historik/"
UT = DATA
JSON_2022 = "/Users/daniel/code/Temp/data/valdata_2022.json"
SKV_DIR = ("/Users/daniel/code/Temp/Historiska dokument/unz/mappning_2014_2018/")
SKV_VD_MAPP = SKV_DIR + "vd-mappning-2014-2018.skv"      # kod 2014;kod 2018;procent
SKV_VD_IND = SKV_DIR + "vd-indelning-2018.skv"           # kod 2018;O/M/S/N
SKV_UPP_MAPP = SKV_DIR + "upp-mappning-2014-2018.skv"    # R148001;R148000;100.0
SKV_UPP_IND = SKV_DIR + "upp-indelning-2018.skv"

MAPP_2018_2022 = DATA + "mappning_2018_2022.csv"

# Kandistrikten 2022 i Majornaomradet (Vastra Centrum, primaromradena Majorna,
# Stigberget, Kungsladugard, Sanna).
MAJORNA_2022 = ["148005%02d" % n for n in range(26, 49)]

# Karnpartier som finns i alla ar och i alla kallor, normaliserade (FP -> L).
KARNPARTIER = ["M", "C", "L", "KD", "S", "V", "MP", "SD"]

# Trosklar for geometrisk klassning (andelar 0-1 ur geo_overlap-filerna).
T_SAMMA = 0.98    # "i praktiken samma yta"
T_HEL = 0.90      # foregangaren ligger i allt vasentligt inne i det nya distriktet
T_BIDRAG = 0.05   # minsta bidrag for att raknas som kalla

TYPER = ("identisk", "namnbyte", "sammanslagen", "delad", "omritad", "ny", "okänd")
JAMFORBARA_TYPER = ("identisk", "namnbyte")

# ---------------------------------------------------------------- hjalpare


def las(fil, delimiter=";", encoding="utf-8"):
    with open(fil, encoding=encoding, newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def skriv(fil, kolumner, rader):
    with open(fil, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=kolumner, delimiter=";",
                           lineterminator="\n", extrasaction="raise")
        w.writeheader()
        for r in rader:
            w.writerow(r)
    print("skrev %s (%d rader)" % (fil, len(rader)))


def kod8(v):
    v = (v or "").strip()
    return v


def karna(namn):
    """Namnets kardel: det som star efter forsta ', ' (stadsdelsnamnd eller
    valkrets tas bort). Saknas komma returneras hela namnet."""
    n = (namn or "").strip()
    if ", " in n:
        n = n.split(", ", 1)[1]
    return n


def normnamn(namn):
    n = karna(namn).casefold()
    n = n.replace("m.fl.", "m fl").replace("m fl.", "m fl")
    n = re.sub(r"[^0-9a-zåäöéü ]+", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def namnlika(a, b):
    na, nb = normnamn(a), normnamn(b)
    if not na or not nb:
        return False
    return na == nb


def f(v, standard=0.0):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return standard


def i(v, standard=0):
    try:
        return int(float(str(v).replace(",", ".")))
    except (TypeError, ValueError):
        return standard


# ---------------------------------------------------------------- geometri


class Geo(object):
    """Overlapp mellan tva ars distriktsindelningar."""

    def __init__(self, fil, kol_tidig, kol_tidig_namn, kol_sen, kol_sen_namn,
                 kol_andel_tidig, kol_andel_sen):
        self.fil = os.path.basename(fil)
        self.per_sen = collections.defaultdict(list)
        self.per_tidig = collections.defaultdict(list)
        self.namn_tidig = {}
        self.namn_sen = {}
        for r in las(fil):
            kt, ks = kod8(r[kol_tidig]), kod8(r[kol_sen])
            at = f(r[kol_andel_tidig])   # andel av det tidiga distriktet
            asen = f(r[kol_andel_sen])   # andel av det sena distriktet
            m2 = f(r["overlapp_m2"])
            if m2 <= 0.0:
                continue
            self.namn_tidig[kt] = r[kol_tidig_namn]
            self.namn_sen[ks] = r[kol_sen_namn]
            self.per_sen[ks].append((asen, at, kt, r[kol_tidig_namn], m2))
            self.per_tidig[kt].append((at, asen, ks, r[kol_sen_namn], m2))
        for d in (self.per_sen, self.per_tidig):
            for k in d:
                d[k].sort(key=lambda t: -t[0])

    def par(self, kod_tidig, kod_sen):
        for asen, at, kt, namn, m2 in self.per_sen.get(kod_sen, []):
            if kt == kod_tidig:
                return asen, at
        return None, None

    def klassa(self, kod_sen):
        """Returnerar (typ_utan_namnhansyn, basta_kod_tidig, basta_namn, belagg)."""
        ov = self.per_sen.get(kod_sen, [])
        if not ov:
            return "ny", "", "", "ingen geometrisk överlappning i %s" % self.fil
        asen, at, kt, namn, m2 = ov[0]
        bidrag = [t for t in ov if t[0] >= T_BIDRAG]
        hela = [t for t in bidrag if t[1] >= T_HEL]
        if asen >= T_SAMMA and at >= T_SAMMA:
            typ = "samma_yta"
        elif asen >= T_SAMMA:
            typ = "delad"
        elif len(hela) >= 2:
            typ = "sammanslagen"
        else:
            typ = "omritad"
        txt = ("geometri %s: %s (%s) täcker %.1f procent av det nya distriktet, "
               "%.1f procent av det gamla ligger där, %d källor över %.0f procent"
               % (self.fil, kt, namn, asen * 100.0, at * 100.0,
                  len(bidrag), T_BIDRAG * 100.0))
        return typ, kt, namn, txt


# ---------------------------------------------------------------- FGVAL


def fgval_vektor(fil, kol_kod, kol_namn):
    """Vektor per distrikt ur en fgval-fil: {kod: (namn, tuple(karnpartier))}.
    Tomt roster_fgval raknas som 0 (attributet utelamnas nar vardet ar 0)."""
    ut = {}
    namn = {}
    tal = collections.defaultdict(dict)
    for r in las(fil):
        kod = kod8(r[kol_kod])
        namn[kod] = r.get(kol_namn, "")
        p = r["parti"]
        if p in KARNPARTIER:
            v = r["roster_fgval"].strip()
            tal[kod][p] = i(v) if v != "" else 0
    for kod, d in tal.items():
        vek = tuple(d.get(p, 0) for p in KARNPARTIER)
        if sum(vek) > 0:
            ut[kod] = (namn[kod], vek)
    return ut


def faktisk_vektor(fil):
    """Vektor per distrikt ur en roster-fil: {kod: (namn, tuple(karnpartier))}."""
    namn = {}
    tal = collections.defaultdict(dict)
    for r in las(fil):
        kod = kod8(r["kod"])
        namn[kod] = r["namn"]
        p = r["parti"]
        if p in KARNPARTIER:
            tal[kod][p] = i(r["roster"])
    return {k: (namn[k], tuple(d.get(p, 0) for p in KARNPARTIER))
            for k, d in tal.items()}


def matcha_fgval(fg, faktisk):
    """{kod_sen: (lista av kod_tidig med identisk vektor, vektor)}"""
    index = collections.defaultdict(list)
    for kod, (namn, vek) in faktisk.items():
        index[vek].append(kod)
    ut = {}
    for kod, (namn, vek) in fg.items():
        ut[kod] = (sorted(index.get(vek, [])), vek)
    return ut


# ---------------------------------------------------------------- steg 1 och 2


def bygg_fgval_kedja(ar_tidig, ar_sen, fgval_filer, roster_filer, geo,
                     distrikt_sen_fil, utfil):
    """Gemensam rutin for 2006->2010 och 2010->2014, dar FGVAL finns."""
    # FGVAL-matchning per val
    matchningar = {}
    for val, (fgfil, rostfil) in sorted(fgval_filer.items()):
        fg = fgval_vektor(DATA + fgfil, "kod_%d" % ar_sen, "namn_%d" % ar_sen)
        fak = faktisk_vektor(DATA + roster_filer[val])
        matchningar[val] = matcha_fgval(fg, fak)
    val_lista = sorted(matchningar)

    # namn och koder for det sena aret
    sen = las(DATA + distrikt_sen_fil)
    namn_sen = {}
    for r in sen:
        namn_sen[kod8(r["kod"])] = r["namn"]
    namn_tidig = {}
    for val in val_lista:
        for kod, (namn, vek) in faktisk_vektor(DATA + roster_filer[val]).items():
            namn_tidig.setdefault(kod, namn)

    rader = []
    stat = collections.Counter()
    for kod in sorted(namn_sen):
        namn = namn_sen[kod]
        # 1. FGVAL
        traffar = {}
        for val in val_lista:
            m = matchningar[val].get(kod)
            if m and len(m[0]) == 1:
                traffar[val] = m[0][0]
        eniga = set(traffar.values())
        kod_t, namn_t, typ, belagg = "", "", "", ""
        if len(eniga) == 1 and len(traffar) == len(val_lista):
            kod_t = sorted(eniga)[0]
            namn_t = namn_tidig.get(kod_t, geo.namn_tidig.get(kod_t, ""))
            vek = matchningar[val_lista[0]][kod][1]
            asen, at = geo.par(kod_t, kod)
            typ = "identisk" if namnlika(namn, namn_t) else "namnbyte"
            geotxt = ""
            if asen is not None:
                geotxt = (", geometri %.1f/%.1f procent" % (asen * 100.0, at * 100.0))
            belagg = ("FGVAL %s ger var för sig identisk vektor, %s: M,C,L,KD,S,V,MP,SD = %s "
                      "(summa %d) mot %s %s%s, namn %s"
                      % ("+".join(val_lista), val_lista[0],
                         ",".join(str(x) for x in vek),
                         sum(vek), ar_tidig, kod_t, geotxt,
                         "lika" if typ == "identisk" else "olika"))
        elif len(eniga) > 1:
            gtyp, gkod, gnamn, gtxt = geo.klassa(kod)
            kod_t, namn_t = gkod, gnamn
            typ = "okänd"
            belagg = ("FGVAL pekar på olika %s-distrikt i olika val (%s), %s"
                      % (ar_tidig,
                         " ".join("%s=%s" % (v, traffar[v]) for v in sorted(traffar)),
                         gtxt))
        else:
            gtyp, gkod, gnamn, gtxt = geo.klassa(kod)
            kod_t, namn_t = gkod, gnamn
            saknas = ("ingen FGVAL i källan, det vill säga Valmyndigheten anger distriktet "
                      "som ändrat (INDELNING=Modifierad)")
            if gtyp == "samma_yta":
                # officiell kalla gar fore geometrin: distriktet ar inte jamforbart
                typ = "omritad"
                gtxt += (" OBS geometrin är i praktiken 1:1 (%s) trots att FGVAL saknas"
                         % gnamn)
            elif gtyp == "ny":
                typ = "ny"
            else:
                typ = gtyp
            belagg = "%s, %s" % (saknas, gtxt)
        stat[typ] += 1
        rader.append(collections.OrderedDict([
            ("kod_%d" % ar_sen, kod),
            ("namn_%d" % ar_sen, namn),
            ("kod_%d_troligast" % ar_tidig, kod_t),
            ("namn_%d" % ar_tidig, namn_t),
            ("typ", typ),
            ("belagg", belagg),
        ]))
    kol = list(rader[0].keys())
    skriv(UT + utfil, kol, rader)
    print("  %s: %s" % (utfil, dict(stat)))
    return {r["kod_%d" % ar_sen]: r for r in rader}


# ---------------------------------------------------------------- steg 3


def las_skv(fil):
    rader = []
    with open(fil, encoding="latin-1") as fh:
        for rad in fh:
            rad = rad.strip()
            if not rad or rad.startswith("#"):
                continue
            rader.append(rad.split(";"))
    return rader


def bygg_2014_2018(geo, utfil):
    """2014 -> 2018. Ingen FGVAL finns for 2018 (Valmyndighetens XML for 2018 saknas
    bland kallorna), darfor anvands Valmyndighetens officiella skv-mappning
    vd-mappning-2014-2018.skv och vd-indelning-2018.skv, rangordnad med geometrin."""
    mapp = collections.defaultdict(list)     # kod_2018 -> [(kod_2014, procent av 2014-distriktet)]
    ut_2014 = collections.defaultdict(list)  # kod_2014 -> [(kod_2018, procent)]
    for rad in las_skv(SKV_VD_MAPP):
        k14, k18, pr = rad[0], rad[1], f(rad[2])
        if not (k14.startswith("1480") and k18.startswith("1480")):
            continue
        mapp[k18].append((k14, pr))
        ut_2014[k14].append((k18, pr))
    indelning = {}
    for rad in las_skv(SKV_VD_IND):
        if rad[0].startswith("1480"):
            indelning[rad[0]] = rad[1]
    upp_ind = ""
    upp_kallor = set()
    for rad in las_skv(SKV_UPP_IND):
        if rad[0].startswith("R1480"):
            upp_ind = rad[1]
    for rad in las_skv(SKV_UPP_MAPP):
        if rad[0].startswith("R1480") and rad[1].startswith("R1480"):
            upp_kallor.add("1480" + rad[0][5:].zfill(4))

    namn18 = dict(geo.namn_sen)
    namn14 = dict(geo.namn_tidig)
    for r in las(DATA + "distrikt_2018_rd.csv"):
        namn18.setdefault(kod8(r["kod"]), r["namn"])
    for r in las(DATA + "distrikt_2014_rd.csv"):
        namn14.setdefault(kod8(r["kod"]), r["namn"])

    IND_TEXT = {"O": "oforandrat", "M": "modifierat", "S": "summerat", "N": "nytt"}
    rader = []
    stat = collections.Counter()
    for kod in sorted(namn18):
        namn = namn18[kod]
        if kod == "14800000":
            kallor_txt = ", ".join(sorted(upp_kallor)) or "14800001-14800004"
            rader.append(collections.OrderedDict([
                ("kod_2018", kod), ("namn_2018", namn),
                ("kod_2014_troligast", sorted(upp_kallor)[0] if upp_kallor else "14800001"),
                ("namn_2014", "Uppsamlingsdistrikt"),
                ("typ", "sammanslagen"),
                ("belagg", ("upp-mappning-2014-2018.skv: %s till R148000 med 100 procent vardera, "
                            "upp-indelning-2018.skv = %s (summerat). De fyra uppsamlingsdistrikten, "
                            "ett per kommunvalkrets, blev ett för hela kommunen"
                            % (kallor_txt, upp_ind or "S"))),
                ("kalla", "skv upp-mappning")]))
            stat["sammanslagen"] += 1
            continue

        ind = indelning.get(kod, "")
        skv_kallor = mapp.get(kod, [])
        # rangordna kandidaterna efter hur stor del av 2018-distriktet de tacker (geometri)
        geo_ov = geo.per_sen.get(kod, [])
        geo_andel = {t[2]: (t[0], t[1]) for t in geo_ov}
        kandidater = []
        for k14, pr in skv_kallor:
            asen, at = geo_andel.get(k14, (None, None))
            kandidater.append((asen if asen is not None else pr / 100.0, pr, k14))
        kandidater.sort(key=lambda t: (-t[0], -t[1]))

        gtyp, gkod, gnamn, gtxt = geo.klassa(kod)
        kalla = "vd-mappning-2014-2018.skv + vd-indelning-2018.skv"
        if not kandidater:
            kod_t, namn_t = ("", "") if ind == "N" else (gkod, gnamn)
            typ = "ny" if ind == "N" else "okänd"
            belagg = ("saknas i vd-mappning-2014-2018.skv, vd-indelning-2018.skv = %s (%s). %s"
                      % (ind or "saknas", IND_TEXT.get(ind, "okand"), gtxt))
            kalla += " + geometri"
        else:
            andel_sen, pr, kod_t = kandidater[0]
            namn_t = namn14.get(kod_t, geo.namn_tidig.get(kod_t, ""))
            # hur mycket av kalldistriktet gick till detta 2018-distrikt
            helt_hit = [k for k, p in skv_kallor if p >= T_HEL * 100.0]
            delat_ut = [x for x in ut_2014.get(kod_t, []) if x[1] >= 2.0]
            if ind == "O":
                typ = "identisk" if namnlika(namn, namn_t) else "namnbyte"
            elif ind == "N":
                typ = "ny"
            elif ind == "S":
                typ = "sammanslagen"
            elif len(helt_hit) >= 2:
                typ = "sammanslagen"
            elif len(skv_kallor) == 1 and len(delat_ut) >= 2:
                typ = "delad"
            else:
                typ = "omritad"
            belagg = ("vd-indelning-2018.skv = %s (%s). vd-mappning-2014-2018.skv ger %d källa eller källor: %s. %s"
                      % (ind or "saknas", IND_TEXT.get(ind, "okand"), len(skv_kallor),
                         ", ".join("%s %.1f procent av 2014-distriktet" % (k, p)
                                   for k, p in sorted(skv_kallor, key=lambda t: -t[1])[:4]),
                         gtxt))
            asen, at = geo.par(kod_t, kod)
            if typ in ("identisk", "namnbyte"):
                if asen is not None and (asen < T_SAMMA or at < T_SAMMA):
                    belagg += (" OBS geometrin ger bara %.1f/%.1f procent" % (asen * 100.0, at * 100.0))
            elif asen is not None and asen >= T_SAMMA and at >= T_SAMMA:
                belagg += (" OBS geometrin är i praktiken 1:1 (%.1f/%.1f procent) trots att "
                           "indelningen anges som modifierad" % (asen * 100.0, at * 100.0))
        stat[typ] += 1
        rader.append(collections.OrderedDict([
            ("kod_2018", kod), ("namn_2018", namn),
            ("kod_2014_troligast", kod_t), ("namn_2014", namn_t),
            ("typ", typ), ("belagg", belagg), ("kalla", kalla)]))
    skriv(UT + utfil, list(rader[0].keys()), rader)
    print("  %s: %s" % (utfil, dict(stat)))
    return {r["kod_2018"]: r for r in rader}


# ---------------------------------------------------------------- steg 4


def bygg_2018_2022(geo, utfil):
    officiell = {}
    namn22_off = {}
    for r in las(MAPP_2018_2022):
        k22 = kod8(r["kod_2022"])
        namn22_off[k22] = r["namn_2022"]
        if r["jamforbart"] == "ja" and kod8(r["kod_2018"]):
            officiell[k22] = (kod8(r["kod_2018"]), r["namn_2018"], r["kalla_fil"])
    namn22 = dict(geo.namn_sen)
    for k, v in namn22_off.items():
        namn22.setdefault(k, v)
    namn18 = dict(geo.namn_tidig)
    for r in las(DATA + "distrikt_2018_rd.csv"):
        namn18.setdefault(kod8(r["kod"]), r["namn"])

    rader = []
    stat = collections.Counter()
    for kod in sorted(namn22):
        namn = namn22[kod]
        gtyp, gkod, gnamn, gtxt = geo.klassa(kod)
        kod_t, namn_t, typ, belagg, kalla = "", "", "okänd", "", "geometri"
        if kod in officiell:
            kod_t, n18, kfil = officiell[kod]
            namn_t = namn18.get(kod_t, n18)
            typ = "identisk" if namnlika(namn, namn_t) else "namnbyte"
            asen, at = geo.par(kod_t, kod)
            gt = ("geometri %.1f/%.1f procent" % (asen * 100.0, at * 100.0)) if asen is not None else "ingen geometri"
            belagg = ("Göteborgs stad %s: kolumnen Jämförbart pekar på 2018-distrikt %s, %s. %s"
                      % (kfil, kod_t, gt, gtxt))
            kalla = "mappning_2018_2022.csv (Goteborgs stad) + geometri"
            if asen is not None and (asen < T_SAMMA or at < T_SAMMA):
                belagg += (" OBS geometrin är inte 1:1, %s täcker %.1f procent av 2022-distriktet "
                           "och %.1f procent av 2018-distriktet ligger där"
                           % (kod_t, asen * 100.0, at * 100.0))
        else:
            kod_t, namn_t = gkod, gnamn
            if gtyp == "samma_yta":
                typ = "omritad"
            elif gtyp == "ny":
                typ = "ny"
            else:
                typ = gtyp
            belagg = ("ej markerad som jämförbar i kolumnen Jämförbart i Göteborgs stads fil "
                      "(mappning_2018_2022.csv). %s" % gtxt)
            if gtyp == "samma_yta":
                asen, at = geo.par(gkod, kod)
                belagg += (" OBS geometrin är i praktiken 1:1 (%s täcker %.1f procent av "
                           "2022-distriktet, %.1f procent av 2018-distriktet ligger där) trots att "
                           "källan inte markerar distriktet som jämförbart"
                           % (gkod, (asen or 0.0) * 100.0, (at or 0.0) * 100.0))
            kalla = "geometri + mappning_2018_2022.csv"
        stat[typ] += 1
        rader.append(collections.OrderedDict([
            ("kod_2022", kod), ("namn_2022", namn),
            ("kod_2018_troligast", kod_t), ("namn_2018", namn_t),
            ("typ", typ), ("belagg", belagg), ("kalla", kalla)]))
    skriv(UT + utfil, list(rader[0].keys()), rader)
    print("  %s: %s" % (utfil, dict(stat)))
    return {r["kod_2022"]: r for r in rader}


# ---------------------------------------------------------------- steg 5


def bygg_majorna(k1822, k1418, k1014, k0610, utfil):
    j22 = {d["kod"]: d["namn"] for d in json.load(open(JSON_2022, encoding="utf-8"))["distrikt"]}
    rader = []
    rakning = collections.Counter()
    for kod22 in MAJORNA_2022:
        r22 = k1822.get(kod22, {})
        namn22 = r22.get("namn_2022", "")
        kort = j22.get(kod22, "")
        kod18 = r22.get("kod_2018_troligast", "")
        typ_1822 = r22.get("typ", "okänd")
        r18 = k1418.get(kod18, {}) if kod18 else {}
        kod14 = r18.get("kod_2014_troligast", "")
        typ_1418 = r18.get("typ", "okänd") if kod18 else "okänd"
        r14 = k1014.get(kod14, {}) if kod14 else {}
        kod10 = r14.get("kod_2010_troligast", "")
        typ_1014 = r14.get("typ", "okänd") if kod14 else "okänd"
        r10 = k0610.get(kod10, {}) if kod10 else {}
        kod06 = r10.get("kod_2006_troligast", "")
        typ_0610 = r10.get("typ", "okänd") if kod10 else "okänd"

        steg = [("2018", typ_1822), ("2014", typ_1418),
                ("2010", typ_1014), ("2006", typ_0610)]
        tillbaka = "2022"
        for ar, typ in steg:
            if typ in JAMFORBARA_TYPER:
                tillbaka = ar
            else:
                break
        direkt = "ja" if tillbaka == "2006" else "nej"
        anm = []
        if "OBS" in r22.get("belagg", ""):
            anm.append("2018-2022: %s" % r22["belagg"].split("OBS", 1)[1].strip())
        if kod18 and "OBS" in r18.get("belagg", ""):
            anm.append("2014-2018: %s" % r18["belagg"].split("OBS", 1)[1].strip())
        if not kod18:
            anm.append("ingen 2018-föregångare kunde fastställas")
        for ar in ("2018", "2014", "2010", "2006"):
            if int(tillbaka) <= int(ar):
                rakning[ar] += 1
        rader.append(collections.OrderedDict([
            ("kod_2022", kod22),
            ("namn_2022", namn22),
            ("kortnamn_2022", kort),
            ("kod_2018", kod18),
            ("namn_2018", r18.get("namn_2018", "")),
            ("typ_2018_2022", typ_1822),
            ("kod_2014", kod14),
            ("namn_2014", r14.get("namn_2014", "")),
            ("typ_2014_2018", typ_1418),
            ("kod_2010", kod10),
            ("namn_2010", r10.get("namn_2010", "")),
            ("typ_2010_2014", typ_1014),
            ("kod_2006", kod06),
            ("namn_2006", r10.get("namn_2006", "")),
            ("typ_2006_2010", typ_0610),
            ("jamforbar_tillbaka_till", tillbaka),
            ("jamforbar_direkt", direkt),
            ("anmarkning", "; ".join(anm)),
        ]))
    skriv(UT + utfil, list(rader[0].keys()), rader)
    print("  direkt jamforbara tillbaka till: %s av 23" % dict(rakning))
    return rader


# ---------------------------------------------------------------- main


def main():
    geo0610 = Geo(DATA + "geo_overlap_2006_2010.csv", "kod_2006", "namn_2006",
                  "kod_2010", "namn_2010", "andel_av_2006", "andel_av_2010")
    geo1014 = Geo(DATA + "geo_overlap_2010_2014.csv", "kod_2010", "namn_2010",
                  "kod_2014", "namn_2014", "andel_av_2010", "andel_av_2014")
    geo1418 = Geo(DATA + "geo_overlap_2014_2018.csv", "kod_2014", "namn_2014",
                  "kod_2018", "namn_2018", "andel_av_2014", "andel_av_2018")
    geo1822 = Geo(DATA + "geo_overlap_2018_2022.csv", "kod_2018", "namn_2018",
                  "kod_2022", "namn_2022", "andel_av_2018", "andel_av_2022")

    print("== 2006 -> 2010")
    k0610 = bygg_fgval_kedja(
        2006, 2010,
        {"rd": ("fgval_2010_rd.csv", None), "kf": ("fgval_2010_kf.csv", None),
         "rf": ("fgval_2010_rf.csv", None)},
        {"rd": "roster_2006_rd_xls.csv", "kf": "roster_2006_kf_xls.csv",
         "rf": "roster_2006_rf_xls.csv"},
        geo0610, "distrikt_2010_rd.csv", "kedja_2006_2010.csv")

    print("== 2010 -> 2014")
    k1014 = bygg_fgval_kedja(
        2010, 2014,
        {"rd": ("fgval_2014_rd.csv", None), "kf": ("fgval_2014_kf.csv", None)},
        {"rd": "roster_2010_rd_xls.csv", "kf": "roster_2010_kf_xls.csv"},
        geo1014, "distrikt_2014_rd.csv", "kedja_2010_2014.csv")

    print("== 2014 -> 2018")
    k1418 = bygg_2014_2018(geo1418, "kedja_2014_2018.csv")

    print("== 2018 -> 2022")
    k1822 = bygg_2018_2022(geo1822, "kedja_2018_2022.csv")

    print("== Majorna 2006-2022")
    bygg_majorna(k1822, k1418, k1014, k0610, "kedja_majorna_2006_2022.csv")


if __name__ == "__main__":
    main()
