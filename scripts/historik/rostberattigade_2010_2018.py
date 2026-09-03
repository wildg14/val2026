#!/usr/bin/env python3
"""Röstberättigade per valdistrikt i Göteborgs kommun 2010, 2014 och 2018,
fördelade på kön, medborgarskap och åldersgrupp.

Läser Valmyndighetens filer "rostberattigade" (en per val och år), filtrerar
kommun_id 1480 och skriver till data/historik/:

  rostberattigade_<år>_<val>.csv          långt format: ar;val;kod;namn;kon;medborgarskap;aldersgrupp;antal
  rostberattigade_<år>_<val>_bred.csv     originalkolumnerna (id-kolumner + 20 kategorikolumner) plus ar, val, totalt
  rostberattigade_majornaomradet_<år>.csv distrikt vars namn börjar med Majorna-prefixet, summa av urvalet, Göteborg totalt
  rostberattigade_kontroll_2010_2018.csv  summan av kategorierna per distrikt jämförd med röstberättigade i resultatfilerna

Körs med venv-python (behöver xlrd och openpyxl):
  python scripts/historik/rostberattigade_2010_2018.py
"""
import csv
import glob
import os
import sys

import openpyxl
import xlrd

HIST = "/Users/daniel/code/Temp/Historiska dokument/"
REPARERAD = ("/private/tmp/claude-501/-Users-daniel-code-Temp/"
             "f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad/repaired/")
UT = "/Users/daniel/code/Temp/data/historik/"
KOMMUN = 1480

# (år, val, källfil). val: rd = riksdag, rf = landsting/region, kf = kommun.
KALLOR = [
    (2010, "rd", HIST + "rostberattigade (6).xls"),
    (2010, "rf", HIST + "rostberattigade (7).xls"),
    (2010, "kf", HIST + "rostberattigade (8).xls"),
    (2014, "rd", HIST + "rostberattigade (3).xls"),
    (2014, "rf", HIST + "rostberattigade (4).xls"),
    (2014, "kf", HIST + "rostberattigade (5).xls"),
    (2018, "rd", REPARERAD + "2018_rostberattigade_R.xlsx"),
    (2018, "rf", REPARERAD + "2018_rostberattigade_L.xlsx"),
    (2018, "kf", REPARERAD + "2018_rostberattigade_K.xlsx"),
]

# Resultatfiler för kontroll av totalsumman per distrikt:
# (fil, flik, rubrikrad (0-baserad; 2014-filerna har "Valmyndigheten 2014-10-02" på rad 0 och tom rad 1),
#  index för län, kommun och distrikt, kolumnnamn för röstberättigade)
KONTROLL = {
    (2010, "rd"): (HIST + "slutligt_valresultat_valdistrikt_R.xls", None, 0, 0, 1, 2, "Rostb"),
    (2010, "rf"): (HIST + "slutligt_valresultat_valdistrikt_L.xls", None, 0, 0, 1, 2, "Rostb"),
    (2010, "kf"): (HIST + "slutligt_valresultat_valdistrikt_K_antal.xls", None, 0, 0, 1, 2, "Rostb"),
    (2014, "rd"): (HIST + "2014_riksdagsval_per_valdistrikt.xls", None, 2, 0, 1, 3, "Rostb"),
    (2014, "rf"): (HIST + "2014_landstingsval_per_valdistrikt.xls", None, 2, 0, 1, 2, "Rostb"),
    (2014, "kf"): (HIST + "2014_kommunval_per_valdistrikt.xlsx", None, 2, 0, 1, 2, "Rostb"),
    (2018, "rd"): (HIST + "2018_R_per_valdistrikt.xlsx", "R antal", 0, 0, 1, 3, "RÖSTBERÄTTIGADE"),
    (2018, "rf"): (HIST + "2018_L_per_valdistrikt.xlsx", "L antal", 0, 0, 1, 3, "RÖSTBERÄTTIGADE"),
    (2018, "kf"): (HIST + "2018_K_per_valdistrikt.xlsx", "K antal", 0, 0, 1, 3, "RÖSTBERÄTTIGADE"),
}

# Namnprefix som avgränsar Majornaområdet i respektive års indelning.
MAJORNA_PREFIX = {2010: "Majorna,", 2014: "Majorna-Linné,", 2018: "Majorna-Linné,"}

LANG_KOLUMNER = ["ar", "val", "kod", "namn", "kon", "medborgarskap", "aldersgrupp", "antal"]


def las_blad(fil, flik=None):
    """Returnerar alla rader i bladet som listor. xls via xlrd, xlsx via openpyxl."""
    if fil.lower().endswith(".xls"):
        wb = xlrd.open_workbook(fil)
        sh = wb.sheet_by_name(flik) if flik else wb.sheet_by_index(0)
        return [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
    wb = openpyxl.load_workbook(fil, read_only=True, data_only=True)
    ws = wb[flik] if flik else wb.worksheets[0]
    return [list(r) for r in ws.iter_rows(values_only=True)]


def heltal(v):
    """Tal i källorna är flyttal (xls) eller int (xlsx). Tomt ger None."""
    if v is None or v == "":
        return None
    f = float(v)
    if f != int(f):
        raise ValueError(f"inte ett heltal: {v!r}")
    return int(f)


def kod8(v):
    k = f"{heltal(v):08d}"
    if len(k) != 8:
        raise ValueError(f"kod med fel längd: {k}")
    return k


def skriv_csv(fil, rubrik, rader):
    with open(fil, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(rubrik)
        w.writerows(rader)
    print(f"  skrev {fil} ({len(rader)} rader)")


def las_kalla(ar, val, fil):
    """Läser en rostberattigade-fil och returnerar (idkolumner, kategorier, göteborgsrader).

    göteborgsrader: lista av dict med kod, namn, id (dict originalkolumn -> värde),
    kat (dict originalkolumn -> int), totalt.
    """
    rader = las_blad(fil)
    rubrik = [str(c) for c in rader[0]]
    idkol = [c for c in rubrik if "/" not in c]
    katkol = [c for c in rubrik if "/" in c]
    if len(katkol) != 20:
        raise ValueError(f"{fil}: väntade 20 kategorikolumner, fann {len(katkol)}")
    ix = {c: i for i, c in enumerate(rubrik)}
    ut = []
    ej_svensk_riket = 0
    for r in rader[1:]:
        if r[ix["kommun_id"]] in (None, ""):
            continue
        for c in katkol:
            if "Ej svenska" in c:
                ej_svensk_riket += heltal(r[ix[c]])
        if heltal(r[ix["kommun_id"]]) != KOMMUN:
            continue
        kat = {c: heltal(r[ix[c]]) for c in katkol}
        idv = {}
        for c in idkol:
            v = r[ix[c]]
            if c == "valdistrikt_id":
                v = kod8(v)
            elif c.endswith("_id"):
                v = heltal(v)
            idv[c] = v
        ut.append({
            "kod": idv["valdistrikt_id"],
            "namn": str(r[ix["valdistrikt_namn"]]),
            "id": idv,
            "kat": kat,
            "totalt": sum(kat.values()),
        })
    koder = [d["kod"] for d in ut]
    if len(koder) != len(set(koder)):
        raise ValueError(f"{fil}: dubbla distriktskoder i Göteborg")
    ut.sort(key=lambda d: d["kod"])  # källan ligger i kommunvalkretsordning, utdata sorteras på kod
    return idkol, katkol, ut, ej_svensk_riket


def dela_kategori(c):
    """'Män/Svenska medborgare/30-49' -> ('Män', 'Svenska medborgare', '30-49')."""
    delar = c.split("/")
    if len(delar) != 3:
        raise ValueError(f"oväntad kategorikolumn: {c}")
    return tuple(delar)


def las_kontroll(ar, val):
    """Röstberättigade per göteborgsdistrikt ur resultatfilen, som dict kod -> tal."""
    fil, flik, rubrikrad, i_lan, i_kom, i_vd, rostb_namn = KONTROLL[(ar, val)]
    rader = las_blad(fil, flik)
    rubrik = [str(c) if c is not None else "" for c in rader[rubrikrad]]
    i_rostb = rubrik.index(rostb_namn)
    ut = {}
    namn = {}
    for r in rader[rubrikrad + 1:]:
        try:
            lan, kom, vd = heltal(r[i_lan]), heltal(r[i_kom]), heltal(r[i_vd])
        except (ValueError, TypeError):
            continue
        if lan is None or kom is None or vd is None:
            continue
        if lan * 100 + kom != KOMMUN:
            continue
        kod = f"{lan:02d}{kom:02d}{vd:04d}"
        ut[kod] = heltal(r[i_rostb])
        # Kodkolumnerna följs av lika många namnkolumner, distriktsnamnet står på index 2*i_vd+1.
        namn[kod] = r[2 * i_vd + 1] if 2 * i_vd + 1 < len(r) else ""
    return os.path.basename(fil) + (f" [{flik}]" if flik else ""), ut, namn


def las_historik(ar, val):
    """Röstberättigade ur redan skrivna distrikt_<år>_<val>*.csv i data/historik, om de finns."""
    ut = {}
    for fil in sorted(glob.glob(os.path.join(UT, f"distrikt_{ar}_{val}*.csv"))):
        with open(fil, encoding="utf-8", newline="") as f:
            for rad in csv.DictReader(f, delimiter=";"):
                v = rad.get("rostberattigade", "")
                if v not in ("", None):
                    ut.setdefault(os.path.basename(fil), {})[rad["kod"]] = int(float(v))
    return ut


def main():
    os.makedirs(UT, exist_ok=True)
    kontrollrader = []
    per_ar = {}
    sammanfattning = []
    for ar, val, fil in KALLOR:
        print(f"== {ar} {val}: {fil}")
        idkol, katkol, distrikt, ej_svensk_riket = las_kalla(ar, val, fil)
        per_ar.setdefault(ar, {})[val] = (idkol, katkol, distrikt)
        goteborg_tot = sum(d["totalt"] for d in distrikt)
        ej_svensk_gbg = sum(d["kat"][c] for d in distrikt for c in katkol if "Ej svenska" in c)
        print(f"  göteborgsdistrikt: {len(distrikt)}, röstberättigade totalt: {goteborg_tot}, "
              f"varav ej svenska medborgare: {ej_svensk_gbg} (hela filen: {ej_svensk_riket})")

        # Långt format
        lang = []
        for d in distrikt:
            for c in katkol:
                kon, medb, ald = dela_kategori(c)
                lang.append([ar, val, d["kod"], d["namn"], kon, medb, ald, d["kat"][c]])
        skriv_csv(os.path.join(UT, f"rostberattigade_{ar}_{val}.csv"), LANG_KOLUMNER, lang)

        # Bred variant med originalkolumnerna
        bred = []
        for d in distrikt:
            bred.append([ar, val] + [d["id"][c] for c in idkol] + [d["kat"][c] for c in katkol] + [d["totalt"]])
        skriv_csv(os.path.join(UT, f"rostberattigade_{ar}_{val}_bred.csv"),
                  ["ar", "val"] + idkol + katkol + ["totalt"], bred)

        # Kontroll mot resultatfil
        kalla_namn, facit, facit_namn = las_kontroll(ar, val)
        lika = olika = saknas_i_facit = 0
        for d in distrikt:
            fv = facit.get(d["kod"])
            if fv is None:
                saknas_i_facit += 1
                diff = ""
            else:
                diff = d["totalt"] - fv
                if diff == 0:
                    lika += 1
                else:
                    olika += 1
            kontrollrader.append([ar, val, d["kod"], d["namn"], d["totalt"],
                                  "" if fv is None else fv, diff, kalla_namn])
        saknas_har = sorted(set(facit) - {d["kod"] for d in distrikt})
        print(f"  kontroll mot {kalla_namn}: {len(facit)} göteborgsdistrikt i resultatfilen, "
              f"lika {lika}, olika {olika}, saknas i resultatfilen {saknas_i_facit}, "
              f"finns bara i resultatfilen {len(saknas_har)} "
              f"{[(k, facit_namn.get(k), facit.get(k)) for k in saknas_har[:6]]}")

        # Kontroll mot redan skrivna distriktfiler i data/historik
        hist = las_historik(ar, val)
        if not hist:
            print(f"  ingen distrikt_{ar}_{val}*.csv i data/historik ännu, kontrolleras senare")
        for hfil, hv in hist.items():
            h_lika = sum(1 for d in distrikt if hv.get(d["kod"]) == d["totalt"])
            h_olika = [(d["kod"], d["totalt"], hv[d["kod"]]) for d in distrikt
                       if d["kod"] in hv and hv[d["kod"]] != d["totalt"]]
            h_saknas = sum(1 for d in distrikt if d["kod"] not in hv)
            print(f"  kontroll mot {hfil}: lika {h_lika}, olika {len(h_olika)} {h_olika[:5]}, saknas {h_saknas}")

        sammanfattning.append((ar, val, len(distrikt), goteborg_tot, ej_svensk_gbg, ej_svensk_riket,
                               len(facit), lika, olika, saknas_i_facit, len(saknas_har)))

    skriv_csv(os.path.join(UT, "rostberattigade_kontroll_2010_2018.csv"),
              ["ar", "val", "kod", "namn", "summa_kategorier", "rostberattigade_resultatfil", "diff", "kalla_fil"],
              kontrollrader)

    # Majornaområdet per år: urval på namnprefix, summa av urvalet, Göteborg totalt
    for ar, valen in per_ar.items():
        prefix = MAJORNA_PREFIX[ar]
        katkol = None
        rader = []
        for val in ("rd", "rf", "kf"):
            idkol, katkol, distrikt = valen[val]
            urval = [d for d in distrikt if d["namn"].startswith(prefix)]
            for d in urval:
                rader.append([ar, val, "distrikt", d["kod"], d["namn"]] + [d["kat"][c] for c in katkol] + [d["totalt"]])
            rader.append([ar, val, "summa_urval", "", f"Summa distrikt med namn som börjar med '{prefix}' ({len(urval)} st)"]
                         + [sum(d["kat"][c] for d in urval) for c in katkol] + [sum(d["totalt"] for d in urval)])
            rader.append([ar, val, "goteborg", "", f"Göteborgs kommun totalt ({len(distrikt)} distrikt)"]
                         + [sum(d["kat"][c] for d in distrikt) for c in katkol] + [sum(d["totalt"] for d in distrikt)])
            print(f"== {ar} {val}: urval '{prefix}' {len(urval)} distrikt, "
                  f"{sum(d['totalt'] for d in urval)} röstberättigade av {sum(d['totalt'] for d in distrikt)} i Göteborg")
        skriv_csv(os.path.join(UT, f"rostberattigade_majornaomradet_{ar}.csv"),
                  ["ar", "val", "typ", "kod", "namn"] + katkol + ["totalt"], rader)

    print("\nSammanfattning (ar, val, distrikt, totalt, ej svenska Gbg, ej svenska hela filen, "
          "distrikt i resultatfil, lika, olika, saknas i resultatfil, bara i resultatfil):")
    for s in sammanfattning:
        print("  ", s)


if __name__ == "__main__":
    main()
