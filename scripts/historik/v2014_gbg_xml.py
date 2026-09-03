#!/usr/bin/env python3
"""v2014: läser Valmyndighetens XML (slutresultat 2014, DTD 1.6) för Göteborg
(1480) och riket (00) och skriver långt format.

Utdata (data/historik/):
  roster_2014_<val>_xml.csv   per valdistrikt (297) + 4 uppsamlingsdistrikt
  aggregat_2014_<val>.csv     riket, vgregion, goteborg, fyra kommunvalkretsar
  fgval_2014_<val>.csv        Valmyndighetens FGVAL (föregående val) per distrikt
  mandat_2014_riksdag.csv     riket + 29 riksdagsvalkretsar
  mandat_2014_kf.csv          Göteborgs kommunfullmäktige + fyra valkretsar
  mandat_2014_rf.csv          Västra Götalands regionfullmäktige + fem valkretsar

Körs med scratchpad-venv (bara standardbiblioteket behövs):
  venv/bin/python scripts/historik/v2014_gbg_xml.py
"""
import csv
import os
import xml.etree.ElementTree as ET

XML_DIR = ("/private/tmp/claude-501/-Users-daniel-code-Temp/"
           "f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad/unz/slutresultat")
UT_DIR = "/Users/daniel/code/Temp/data/historik"

AR = 2014
KOMMUN_KOD = "1480"
VAL = {"rd": "R", "rf": "L", "kf": "K"}
# Filhuvudet säger VALDAG_FGVAL=20100919 för alla tre, men landstingets
# FGVAL-siffror är omvalet 2011-05-15 (visas av v2014_gbg_kontroll.py).
AR_FG = {"rd": 2010, "rf": 2011, "kf": 2010}
NORM = {"FP": "L", "DEM": "D", "KP": "K"}
PSEUDO = ("HANDSKRIVNA", "ÖVRIGA_FGVAL", "GILTIGA", "BLANK", "OG",
          "SUMMA_RÖSTER", "RÖSTBERÄTTIGADE")


def norm_parti(kalla):
    if kalla in PSEUDO:
        return kalla
    if kalla in NORM:
        return NORM[kalla]
    if kalla.isdigit():
        return kalla.zfill(4)
    return kalla.upper()


def dec(s):
    """'23,86' -> '23.86', None -> ''."""
    return "" if s is None else s.replace(",", ".")


def load(name):
    return ET.parse(os.path.join(XML_DIR, name)).getroot()


def parti_rader(el):
    """(partikod, element) för direkta GILTIGA, GILTIGA under ÖVRIGA_GILTIGA,
    HANDSKRIVNA och ÖVRIGA_FGVAL. Summan av RÖSTER blir elementets RÖSTER."""
    rows = [(g.get("PARTI"), g) for g in el.findall("GILTIGA")]
    ov = el.find("ÖVRIGA_GILTIGA")
    if ov is not None:
        rows += [(g.get("PARTI"), g) for g in ov.findall("GILTIGA")]
        for tag in ("HANDSKRIVNA", "ÖVRIGA_FGVAL"):
            h = ov.find(tag)
            if h is not None:
                rows.append((tag, h))
    return rows


def ogiltiga(el):
    out = {}
    for o in el.findall("OGILTIGA"):
        out[o.get("TEXT")] = o
    return out


def distrikt_iter(root):
    """(kod, namn, element) för VALDISTRIKT och ONSDAGSDISTRIKT (uppsamling).
    Uppsamlingsdistrikt R-1480-03 får koden 14800003, samma som Excelfilerna."""
    for d in root.iter("VALDISTRIKT"):
        yield d.get("KOD"), d.get("NAMN"), d
    for d in root.iter("ONSDAGSDISTRIKT"):
        kod = KOMMUN_KOD + d.get("KOD").split("-")[-1].zfill(4)
        yield kod, d.get("NAMN"), d


def distrikt_varden(el):
    """Sammanfattning av ett distrikt-/summeringselement."""
    og = ogiltiga(el)
    vd = el.find("VALDELTAGANDE")
    return {
        "giltiga": el.get("RÖSTER"),
        "blanka": og["BLANK"].get("RÖSTER") if "BLANK" in og else None,
        "og": og["OG"].get("RÖSTER") if "OG" in og else None,
        "rostande": vd.get("SUMMA_RÖSTER") if vd is not None else None,
        "rostberattigade": vd.get("RÖSTBERÄTTIGADE") if vd is not None else None,
        "valdeltagande": dec(vd.get("PROCENT")) if vd is not None else None,
    }


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print("skrev", path, len(rows), "rader")


def roster_och_fgval(val, root):
    roster, fgval = [], []
    for kod, namn, d in sorted(distrikt_iter(root), key=lambda t: t[0]):
        summa = 0
        for p, g in parti_rader(d):
            r = int(g.get("RÖSTER"))
            if p == "ÖVRIGA_FGVAL" and r == 0:
                pass  # alltid 0 i aktuellt val, skrivs bara till fgval-filen
            else:
                roster.append([AR, val, kod, namn, p, norm_parti(p), r,
                               dec(g.get("PROCENT"))])
            summa += r
            if g.get("RÖSTER_FGVAL") is not None:
                fgval.append([AR_FG[val], val, kod, namn, norm_parti(p), r,
                              int(g.get("RÖSTER_FGVAL"))])
        assert summa == int(d.get("RÖSTER")), (kod, summa, d.get("RÖSTER"))
        if d.get("RÖSTER_FGVAL") is not None:
            fgval.append([AR_FG[val], val, kod, namn, "GILTIGA",
                          int(d.get("RÖSTER")), int(d.get("RÖSTER_FGVAL"))])
        for text, o in ogiltiga(d).items():
            if o.get("RÖSTER_FGVAL") is not None:
                fgval.append([AR_FG[val], val, kod, namn, text,
                              int(o.get("RÖSTER")), int(o.get("RÖSTER_FGVAL"))])
        vd = d.find("VALDELTAGANDE")
        if vd is not None and vd.get("SUMMA_RÖSTER_FGVAL") is not None:
            fgval.append([AR_FG[val], val, kod, namn, "SUMMA_RÖSTER",
                          int(vd.get("SUMMA_RÖSTER")),
                          int(vd.get("SUMMA_RÖSTER_FGVAL"))])
            fgval.append([AR_FG[val], val, kod, namn, "RÖSTBERÄTTIGADE",
                          int(vd.get("RÖSTBERÄTTIGADE")),
                          int(vd.get("RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL"))])
    write_csv(os.path.join(UT_DIR, "roster_%d_%s_xml.csv" % (AR, val)),
              ["ar", "val", "kod", "namn", "parti_kalla", "parti", "roster", "andel"],
              roster)
    write_csv(os.path.join(UT_DIR, "fgval_%d_%s.csv" % (AR, val)),
              ["ar_fg", "val", "kod_2014", "namn_2014", "parti", "roster_2014",
               "roster_fgval"], fgval)


def aggregat(val, root_gbg, root_riket):
    nivaer = []
    nat = root_riket.find("NATION")
    nivaer.append(("riket", nat))
    for lan in root_riket.iter("LÄN"):
        if lan.get("KOD") == "14":
            nivaer.append(("vgregion", lan))
    kommun = root_gbg.find("KOMMUN")
    assert kommun.get("KOD") == KOMMUN_KOD
    nivaer.append(("goteborg", kommun))
    for k in sorted(kommun.findall("KRETS_KOMMUN"), key=lambda e: e.get("KOD")):
        nivaer.append((k.get("NAMN"), k))
    rows = []
    for niva, el in nivaer:
        v = distrikt_varden(el)
        summa = 0
        for p, g in parti_rader(el):
            r = int(g.get("RÖSTER"))
            summa += r
            if p == "ÖVRIGA_FGVAL" and r == 0:
                continue
            rows.append([AR, val, niva, p, norm_parti(p), r, dec(g.get("PROCENT")),
                         v["giltiga"], v["rostande"] or "", v["rostberattigade"] or ""])
        assert summa == int(el.get("RÖSTER")), (niva, summa, el.get("RÖSTER"))
    write_csv(os.path.join(UT_DIR, "aggregat_%d_%s.csv" % (AR, val)),
              ["ar", "val", "niva", "parti_kalla", "parti", "roster", "andel",
               "giltiga", "rostande", "rostberattigade"], rows)


def mandat_rader(val, niva, el):
    tot = el.get("MANDAT_VALOMRÅDE") or el.get("MANDAT_VALKRETS") or ""
    rows = []
    for p, g in parti_rader(el):
        if g.get("MANDAT") is None:
            continue
        rows.append([AR, val, niva, el.get("KOD"), tot, p, norm_parti(p),
                     g.get("RÖSTER"), dec(g.get("PROCENT")), g.get("MANDAT"),
                     g.get("VARAV_UTJÄMNING") or "", g.get("MANDAT_FGVAL") or ""])
    return rows


MANDAT_HDR = ["ar", "val", "niva", "niva_kod", "mandat_totalt", "parti_kalla",
              "parti", "roster", "andel", "mandat", "varav_utjamning", "mandat_fgval"]


def mandat_riksdag(root):
    rows = mandat_rader("rd", "riket", root.find("NATION"))
    for k in sorted(root.iter("KRETS_RIKSDAG"), key=lambda e: e.get("KOD")):
        rows += mandat_rader("rd", k.get("NAMN"), k)
    write_csv(os.path.join(UT_DIR, "mandat_%d_riksdag.csv" % AR), MANDAT_HDR, rows)


def mandat_kf(root):
    kommun = root.find("KOMMUN")
    rows = mandat_rader("kf", "goteborg", kommun)
    for k in sorted(kommun.findall("KRETS_KOMMUN"), key=lambda e: e.get("KOD")):
        rows += mandat_rader("kf", k.get("NAMN"), k)
    write_csv(os.path.join(UT_DIR, "mandat_%d_kf.csv" % AR), MANDAT_HDR, rows)


def mandat_rf(root):
    rows = []
    for lan in root.iter("LÄN"):
        if lan.get("KOD") != "14":
            continue
        rows += mandat_rader("rf", "vgregion", lan)
        for k in sorted(lan.findall("KRETS_LANDSTING"), key=lambda e: e.get("KOD")):
            rows += mandat_rader("rf", k.get("NAMN"), k)
    write_csv(os.path.join(UT_DIR, "mandat_%d_rf.csv" % AR), MANDAT_HDR, rows)


def main():
    os.makedirs(UT_DIR, exist_ok=True)
    for val, bokstav in VAL.items():
        gbg = load("slutresultat_1480%s.xml" % bokstav)
        riket = load("slutresultat_00%s.xml" % bokstav)
        print(val, gbg.get("VALTYP"), "VALDAG", gbg.get("VALDAG"),
              "VALDAG_FGVAL", gbg.get("VALDAG_FGVAL"))
        roster_och_fgval(val, gbg)
        aggregat(val, gbg, riket)
        if val == "rd":
            mandat_riksdag(riket)
        elif val == "kf":
            mandat_kf(gbg)
        else:
            mandat_rf(riket)


if __name__ == "__main__":
    main()
