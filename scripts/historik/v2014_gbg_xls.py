#!/usr/bin/env python3
"""v2014: läser Valmyndighetens Excelfiler per valdistrikt för 2014 och skriver
Göteborgs kommun (1480) i långt format.

Utdata (data/historik/):
  roster_2014_rd_xls.csv, roster_2014_rf_xls.csv, roster_2014_kf_xls.csv
  distrikt_2014_rd.csv, distrikt_2014_rf.csv, distrikt_2014_kf.csv

Körs med scratchpad-venv (xlrd, openpyxl):
  venv/bin/python scripts/historik/v2014_gbg_xls.py
"""
import csv
import os
import sys

import openpyxl
import xlrd

KALLA_DIR = "/Users/daniel/code/Temp/Historiska dokument"
XLS_R = os.path.join(KALLA_DIR, "2014_riksdagsval_per_valdistrikt.xls")
XLS_L = os.path.join(KALLA_DIR, "2014_landstingsval_per_valdistrikt.xls")
XLSX_K = os.path.join(KALLA_DIR, "2014_kommunval_per_valdistrikt.xlsx")
UT_DIR = "/Users/daniel/code/Temp/data/historik"

AR = 2014
LAN = 14
KOM = 80
KOMMUN_KOD = "1480"
HEADER_ROW = 2  # rad 0 = "Valmyndigheten 2014-10-02", rad 1 = tom, rad 2 = rubriker

# Kommunvalkrets för uppsamlingsdistrikten (VALDIST 1-4) hämtas ur R-filens
# kolumner KVK och Kommunvalkrets; samma numrering används i L- och K-filen.
SPECIAL = {"OVR": "ÖVR", "ÖVR": "ÖVR", "BL": "BLANK", "BLANK": "BLANK", "OG": "OG"}
NORM = {"FP": "L", "DEM": "D", "KP": "K"}


def norm_parti(kalla):
    """Normaliserad partikod: FP->L, DEM->D, KP->K, annars versaler.
    Numeriska koder (oregistrerade partier) nollutfylls till fyra tecken,
    eftersom Excel tappat inledande nollor (450 -> 0450)."""
    if kalla in SPECIAL:
        return SPECIAL[kalla]
    if kalla in NORM:
        return NORM[kalla]
    if kalla.isdigit():
        return kalla.zfill(4)
    return kalla.upper()


def num(v):
    """Tal ur cell: '' eller None blir None, annars int om heltal."""
    if v is None or v == "":
        return None
    if isinstance(v, str):
        v = float(v.replace(",", "."))
    if float(v).is_integer():
        return int(v)
    return float(v)


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return ("%.2f" % v)
    return str(v)


def pct(v):
    """Procenttal skrivs alltid med två decimaler, som i källan (83 -> 83.00)."""
    return "" if v is None else "%.2f" % float(v)


def read_xls(path):
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    hdr = [str(sh.cell_value(HEADER_ROW, c)).strip() for c in range(sh.ncols)]
    rows = []
    for r in range(HEADER_ROW + 1, sh.nrows):
        rows.append([sh.cell_value(r, c) for c in range(sh.ncols)])
    return hdr, rows


def read_xlsx(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb[wb.sheetnames[0]]
    it = ws.iter_rows(values_only=True)
    raw = [list(r) for r in it]
    hdr = [str(h).strip() if h is not None else "" for h in raw[HEADER_ROW]]
    return hdr, raw[HEADER_ROW + 1:]


def gbg_rows(hdr, rows, layout):
    """Filtrerar Göteborg och returnerar (kod, namn, kvk, rad)."""
    out = []
    for row in rows:
        if num(row[0]) != LAN or num(row[1]) != KOM:
            continue
        if layout == "R":
            kvk = num(row[hdr.index("KVK")])
            vd = num(row[hdr.index("VALDIST")])
            namn = row[hdr.index("Valdistrikt")]
            kvk_namn = row[hdr.index("Kommunvalkrets")]
        else:
            kvk = None
            vd = num(row[2])
            namn = row[5]
            kvk_namn = None
        kod = KOMMUN_KOD + "%04d" % vd
        out.append((kod, str(namn).strip(), kvk, kvk_namn, row))
    out.sort(key=lambda t: t[0])
    return out


def party_columns(hdr):
    """Lista av (partikod, index_tal, index_proc) ur rubrikpar '<p> tal'/'<p> proc'."""
    cols = []
    for i, h in enumerate(hdr):
        if h.endswith(" tal"):
            p = h[:-4]
            proc = h[:-4] + " proc"
            j = hdr.index(proc) if proc in hdr else None
            cols.append((p, i, j))
    return cols


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print("skrev", path, len(rows), "rader")


def process(val, layout, path, hdr, rows, valkrets_map):
    g = gbg_rows(hdr, rows, layout)
    pcols = party_columns(hdr)
    ig = hdr.index("Rost Giltiga")
    ir = hdr.index("Rostande")
    ib = hdr.index("Rostb")
    iv = hdr.index("VDT")
    # partier med minst en röst i Göteborg (inkl uppsamlingsdistrikt)
    aktiva = []
    for p, i, j in pcols:
        if norm_parti(p) in ("BLANK", "OG"):
            continue
        if any((num(row[i]) or 0) > 0 for _, _, _, _, row in g):
            aktiva.append((p, i, j))
    roster = []
    distrikt = []
    for kod, namn, kvk, kvk_namn, row in g:
        if layout == "R":
            valkrets_map[kod] = kvk_namn
        valkrets = valkrets_map.get(kod, "")
        for p, i, j in aktiva:
            r = num(row[i]) or 0
            # andel lämnas tom när källcellen är tom (partiet fick 0 röster)
            a = num(row[j]) if j is not None else None
            roster.append([AR, val, kod, namn, p, norm_parti(p), r, pct(a)])
        blank = og = None
        for p, i, j in pcols:
            if norm_parti(p) == "BLANK":
                blank = num(row[i]) or 0
            elif norm_parti(p) == "OG":
                og = num(row[i]) or 0
        giltiga = num(row[ig])
        rostande = num(row[ir])
        rostb = num(row[ib])
        vdt = num(row[iv])
        uppsamling = namn == "Uppsamlingsdistrikt"
        if uppsamling:
            # källan har tomt (R) eller 0 (L, K) för röstberättigade och
            # valdeltagande i uppsamlingsdistrikten; skrivs som tomt
            rostb = None
            vdt = None
        assert sum(num(row[i]) or 0 for p, i, j in pcols
                   if norm_parti(p) not in ("BLANK", "OG")) == giltiga, kod
        assert giltiga + blank + og == rostande, kod
        distrikt.append([AR, val, kod, namn, valkrets, giltiga, blank, og,
                         blank + og, rostande, fmt(rostb), pct(vdt),
                         os.path.basename(path)])
    write_csv(os.path.join(UT_DIR, "roster_%d_%s_xls.csv" % (AR, val)),
              ["ar", "val", "kod", "namn", "parti_kalla", "parti", "roster", "andel"],
              roster)
    write_csv(os.path.join(UT_DIR, "distrikt_%d_%s.csv" % (AR, val)),
              ["ar", "val", "kod", "namn", "valkrets", "giltiga", "blanka",
               "ogiltiga_ovriga", "ogiltiga", "rostande", "rostberattigade",
               "valdeltagande", "kalla_fil"],
              distrikt)
    print(val, "distrikt:", len(distrikt), "partier:", [p for p, _, _ in aktiva])


def main():
    os.makedirs(UT_DIR, exist_ok=True)
    valkrets_map = {}
    hdr, rows = read_xls(XLS_R)
    process("rd", "R", XLS_R, hdr, rows, valkrets_map)
    hdr, rows = read_xls(XLS_L)
    process("rf", "LK", XLS_L, hdr, rows, valkrets_map)
    hdr, rows = read_xlsx(XLSX_K)
    process("kf", "LK", XLSX_K, hdr, rows, valkrets_map)


if __name__ == "__main__":
    main()
