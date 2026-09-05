#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xml2018_bygg.py - lasare av Valmyndighetens XML for valet 2018 (Goteborg,
1480) och oberoende kontroll av kedjan 2014 till 2018 per valdistrikt.

Bakgrund: XML-radata for 2018 saknades lange (se docs/historik/noter/val2018.md
och inventering.md, avsnitt "2018 ars XML"), men har nu hamtats fran Internet
Archive och packats upp permanent under Historiska dokument/dl_webb/2018/unz/.
Detta skript laser den XML:en, skriver tre nya filgrupper till data/historik/
och kor fyra kontroller (A-D) beskrivna i uppdraget.

Kallor (lases bara):
  Historiska dokument/dl_webb/2018/unz/slutresultat_1480R.xml, _1480L.xml, _1480K.xml
      (Goteborgs kommun, DTD parti_person_kommun 1.7/1.8, ISO-8859-1)
  Historiska dokument/dl_webb/2018/unz/slutresultat_00R.xml, _00L.xml, _00K.xml
      (riket, DTD parti_person_nation 1.7/1.8, anvands bara for en lattviktig
      integritetskontroll av Goteborgs kommunsumma)
  data/historik/roster_2018_<val>.csv, distrikt_2018_<val>.csv   (xlsx-bygget, facit i kontroll A)
  data/historik/kedja_2014_2018.csv                              (kopplingen i kontroll B och C)
  data/historik/roster_2014_<val>_xml.csv                        (faktiska 2014-roster i kontroll B och C)
  data/historik/geo_overlap_2014_2018.csv                        (areametoden i kontroll C)
  Historiska dokument/unz/mappning_2014_2018/vd-mappning-2014-2018.skv
      (Valmyndighetens officiella procentandelar i kontroll C, ISO-8859-1)
  data/historik/geo_majorna_2018.csv                             (de 22 "inne"-distrikten i kontroll D)
  data/historik/majorna_tidsserie.csv                            (2014-facit i kontroll D)

Skrivna filer (data/historik/), UTF-8, semikolon, punkt som decimaltecken,
koder som text med 8 siffror:
  roster_2018_<val>_xml.csv        ar;val;kod;namn;parti_kalla;parti;roster;andel
  distrikt_2018_<val>_xml.csv      ar;val;kod;namn;valkrets;giltiga;blanka;ogiltiga_ovriga;ogiltiga;
                                    rostande;rostberattigade;valdeltagande;kalla_fil
  fgval_2018_<val>.csv             ar_fg;val;kod_2018;namn_2018;parti;roster_2018;roster_fgval
  fgval_2018_<val>_deltagande.csv  ar_fg;val;kod_2018;namn_2018;giltiga_2018;giltiga_fgval;
                                    rostande_2018;rostande_fgval;rostberattigade_2018;rostberattigade_fgval;
                                    valdeltagande_2018;valdeltagande_fgval;indelning
  fgval_2018_metodjamforelse.csv   kod_2018;namn_2018;val;parti;fgval;skattning_area;skattning_officiell;
                                    diff_area;diff_officiell

Kors med:
  /Users/daniel/code/Temp/.venv/bin/python scripts/historik/xml2018_bygg.py
"""
import csv
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

# ------------------------------------------------------------------ kallvagar
BAS = "/Users/daniel/code/Temp"
XML_DIR = os.path.join(BAS, "Historiska dokument/dl_webb/2018/unz")
SKV_MAPPNING = os.path.join(
    BAS, "Historiska dokument/unz/mappning_2014_2018/vd-mappning-2014-2018.skv")
UT_DIR = os.path.join(BAS, "data/historik")

AR = 2018
AR_FG = 2014
KOMMUN_KOD = "1480"
VAL = {"rd": "R", "rf": "L", "kf": "K"}
VALKRETS = {"rd": "Göteborgs kommun", "rf": "Göteborgs kommun", "kf": ""}
NORM = {"FP": "L", "DEM": "D", "KP": "K"}
MAINPARTIER = ["V", "S", "MP", "M", "SD"]


def norm_parti(kalla):
    if kalla in NORM:
        return NORM[kalla]
    return kalla.upper()


def dec(s):
    return "" if s is None else s.replace(",", ".")


def i0(v):
    return int(v) if v not in (None, "") else 0


def load(name):
    return ET.parse(os.path.join(XML_DIR, name)).getroot()


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print("skrev %s (%d rader)" % (path, len(rows)))
    return path


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def read_skv(path):
    with open(path, encoding="iso-8859-1", newline="") as f:
        rows = []
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            rows.append(line.split(";"))
        return rows


# ------------------------------------------------------------- XML-tolkning
def parti_rader(el):
    """(partikod, element) for direkta GILTIGA, GILTIGA under OVRIGA_GILTIGA,
    HANDSKRIVNA och OVRIGA_FGVAL. Summan av RÖSTER for de forsta tre =
    elementets RÖSTER (kontrolleras i huvudloopen)."""
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
    return {o.get("TEXT"): o for o in el.findall("OGILTIGA")}


def distrikt_iter(root):
    """(kod, namn, element) for VALDISTRIKT (kod redan attsiffrig) och
    ONSDAGSDISTRIKT (uppsamling, kod byggd av sista delen av KOD-attributet,
    t ex "R-1480-00" -> 14800000)."""
    for d in root.iter("VALDISTRIKT"):
        yield d.get("KOD"), d.get("NAMN"), d
    for d in root.iter("ONSDAGSDISTRIKT"):
        kod = KOMMUN_KOD + d.get("KOD").split("-")[-1].zfill(4)
        yield kod, d.get("NAMN"), d


def bygg_val(val, bokstav, kallfil_basename):
    """Laser ett vals Goteborgs-XML, skriver roster/distrikt/fgval/deltagande
    och returnerar (roster_rows_dict, distrikt_dict) for vidare kontroller."""
    root = load(kallfil_basename)
    print("=== %s (%s): VALTYP=%s VALDAG=%s VALDAG_FGVAL=%s" % (
        val, kallfil_basename, root.get("VALTYP"), root.get("VALDAG"),
        root.get("VALDAG_FGVAL")))
    kommun = root.find("KOMMUN")
    assert kommun.get("KOD") == KOMMUN_KOD
    kretsar = kommun.findall("KRETS_KOMMUN")
    assert len(kretsar) == 1 and kretsar[0].get("KOD") == "148000", kretsar

    roster_rows, distrikt_rows, fg_rows, fgd_rows = [], [], [], []
    roster_lookup = {}   # (kod, parti) -> roster (int)
    distrikt_lookup = {}  # kod -> dict med giltiga/blanka/... (strangar)
    antal_ogej_med_fgval = 0
    n = 0
    for kod, namn, d in sorted(distrikt_iter(kommun), key=lambda t: t[0]):
        n += 1
        summa = 0
        for p, g in parti_rader(d):
            r = i0(g.get("RÖSTER"))
            if p != "ÖVRIGA_FGVAL":
                roster_rows.append([AR, val, kod, namn, p, norm_parti(p), r,
                                     dec(g.get("PROCENT"))])
                roster_lookup[(kod, norm_parti(p))] = r
                summa += r
            if g.get("RÖSTER_FGVAL") is not None:
                fg_rows.append([AR_FG, val, kod, namn, norm_parti(p), r,
                                 i0(g.get("RÖSTER_FGVAL"))])
        assert summa == i0(d.get("RÖSTER")), (val, kod, summa, d.get("RÖSTER"))

        og = ogiltiga(d)
        if "OGEJ" in og and og["OGEJ"].get("RÖSTER_FGVAL") is not None:
            antal_ogej_med_fgval += 1
        blanka = i0(og["BLANK"].get("RÖSTER")) if "BLANK" in og else 0
        ogej = i0(og["OGEJ"].get("RÖSTER")) if "OGEJ" in og else 0
        ogovr = i0(og["OG"].get("RÖSTER")) if "OG" in og else 0
        ogiltiga_ovriga = ogej + ogovr
        ogiltiga_tot = ogiltiga_ovriga + blanka
        vd = d.find("VALDELTAGANDE")
        rostberattigade = vd.get("RÖSTBERÄTTIGADE") if vd is not None else ""
        valdeltagande = dec(vd.get("PROCENT")) if vd is not None else ""
        giltiga = i0(d.get("RÖSTER"))
        # rostande = giltiga + ogiltiga alltid (identitet, sa aven for
        # ONSDAGSDISTRIKT/uppsamlingsdistriktet som saknar VALDELTAGANDE-
        # elementet helt). Kontrolleras mot kallans eget SUMMA_RÖSTER nar det
        # finns.
        rostande = giltiga + ogiltiga_tot
        if vd is not None and vd.get("SUMMA_RÖSTER") is not None:
            assert rostande == i0(vd.get("SUMMA_RÖSTER")), (
                val, kod, rostande, vd.get("SUMMA_RÖSTER"))
        distrikt_rows.append([
            AR, val, kod, namn, VALKRETS[val], giltiga, blanka,
            ogiltiga_ovriga, ogiltiga_tot, rostande, rostberattigade,
            valdeltagande, kallfil_basename])
        distrikt_lookup[kod] = {
            "namn": namn, "giltiga": giltiga, "blanka": blanka,
            "ogiltiga_ovriga": ogiltiga_ovriga, "ogiltiga": ogiltiga_tot,
            "rostande": rostande, "rostberattigade": rostberattigade,
            "valdeltagande": valdeltagande, "indelning": d.get("INDELNING") or "",
        }

        for text in ("BLANK", "OG"):
            if text in og and og[text].get("RÖSTER_FGVAL") is not None:
                fg_rows.append([AR_FG, val, kod, namn, text,
                                 i0(og[text].get("RÖSTER")),
                                 i0(og[text].get("RÖSTER_FGVAL"))])
        if d.get("RÖSTER_FGVAL") is not None:
            giltiga_fgval = i0(d.get("RÖSTER_FGVAL"))
        else:
            giltiga_fgval = ""
        if vd is not None and vd.get("SUMMA_RÖSTER_FGVAL") is not None:
            rostande_fgval = i0(vd.get("SUMMA_RÖSTER_FGVAL"))
            rostberattigade_fgval = i0(vd.get("RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL"))
            valdeltagande_fgval = dec(vd.get("PROCENT_FGVAL"))
        else:
            rostande_fgval = rostberattigade_fgval = valdeltagande_fgval = ""
        fgd_rows.append([
            AR_FG, val, kod, namn, giltiga, giltiga_fgval, rostande,
            rostande_fgval, rostberattigade, rostberattigade_fgval,
            valdeltagande, valdeltagande_fgval, d.get("INDELNING") or ""])

    print("  distrikt inlasta (inkl uppsamling): %d" % n)
    print("  OGEJ med RÖSTER_FGVAL (ska vara 0, ny kategori 2018): %d" %
          antal_ogej_med_fgval)

    # kontroll: distriktssumma = kretssumma = kommunsumma
    for niva_namn, el in (("krets 148000", kretsar[0]), ("kommun 1480", kommun)):
        niva_summa = sum(i0(g.get("RÖSTER")) for g in el.findall("GILTIGA"))
        ov = el.find("ÖVRIGA_GILTIGA")
        if ov is not None:
            niva_summa += sum(i0(g.get("RÖSTER")) for g in ov.findall("GILTIGA"))
            for tag in ("HANDSKRIVNA",):
                h = ov.find(tag)
                if h is not None:
                    niva_summa += i0(h.get("RÖSTER"))
        assert niva_summa == i0(el.get("RÖSTER")), (val, niva_namn, niva_summa, el.get("RÖSTER"))
    distrikt_summa = sum(v["giltiga"] for v in distrikt_lookup.values())
    assert distrikt_summa == i0(kommun.get("RÖSTER")), (val, distrikt_summa, kommun.get("RÖSTER"))
    print("  giltiga Göteborg (distriktssumma = kretssumma = kommunsumma): %d" %
          distrikt_summa)

    write_csv(os.path.join(UT_DIR, "roster_%d_%s_xml.csv" % (AR, val)),
              ["ar", "val", "kod", "namn", "parti_kalla", "parti", "roster", "andel"],
              roster_rows)
    write_csv(os.path.join(UT_DIR, "distrikt_%d_%s_xml.csv" % (AR, val)),
              ["ar", "val", "kod", "namn", "valkrets", "giltiga", "blanka",
               "ogiltiga_ovriga", "ogiltiga", "rostande", "rostberattigade",
               "valdeltagande", "kalla_fil"],
              distrikt_rows)
    write_csv(os.path.join(UT_DIR, "fgval_%d_%s.csv" % (AR, val)),
              ["ar_fg", "val", "kod_2018", "namn_2018", "parti", "roster_2018",
               "roster_fgval"], fg_rows)
    write_csv(os.path.join(UT_DIR, "fgval_%d_%s_deltagande.csv" % (AR, val)),
              ["ar_fg", "val", "kod_2018", "namn_2018", "giltiga_2018",
               "giltiga_fgval", "rostande_2018", "rostande_fgval",
               "rostberattigade_2018", "rostberattigade_fgval",
               "valdeltagande_2018", "valdeltagande_fgval", "indelning"],
              fgd_rows)
    return roster_lookup, distrikt_lookup, fg_rows


def riket_kontroll(val, bokstav, kommun_xml_el):
    """Lattviktig integritetskontroll: Goteborgs KOMMUN-element i riksfilen
    ska ha samma RÖSTER och RÖSTER_FGVAL som samma element i 1480-filen."""
    fn = "slutresultat_00%s.xml" % bokstav
    root = load(fn)
    print("--- %s: VALDAG=%s VALDAG_FGVAL=%s" % (fn, root.get("VALDAG"), root.get("VALDAG_FGVAL")))
    funnen = None
    for k in root.iter("KOMMUN"):
        if k.get("KOD") == KOMMUN_KOD:
            funnen = k
            break
    assert funnen is not None, "KOMMUN 1480 saknas i " + fn
    ok = (i0(funnen.get("RÖSTER")) == i0(kommun_xml_el.get("RÖSTER")) and
          i0(funnen.get("RÖSTER_FGVAL")) == i0(kommun_xml_el.get("RÖSTER_FGVAL")))
    print("  Göteborg i %s: RÖSTER=%s RÖSTER_FGVAL=%s, lika som 1480-filen: %s" % (
        fn, funnen.get("RÖSTER"), funnen.get("RÖSTER_FGVAL"), ok))
    assert ok


# ----------------------------------------------------------- kontroll A
def kontroll_a(val, roster_lookup, distrikt_lookup):
    print("\n### Kontroll A, %s ###" % val)
    xls_roster = read_csv(os.path.join(UT_DIR, "roster_%d_%s.csv" % (AR, val)))
    xls_distrikt = read_csv(os.path.join(UT_DIR, "distrikt_%d_%s.csv" % (AR, val)))

    # xlsx-kallan (Valmyndighetens per-distriktsfil) och XML-kallan namnger
    # tre partier och skrivrosterna olika. Belagt genom att jamforelsen blir
    # 0 avvikelser i alla tre valen efter denna kanonisering, se noten:
    #   xlsx-kod "470"/"1397" saknar den inledande nolla som XML har (numeriska
    #     partikoder ar alltid fyrsiffriga i XML)
    #   xlsx BASIP/INI/NYREF (bara i rd) = XML:s numeriska partikoder
    #     1372 Basinkomstpartiet, 1374 Initiativet, 1385 NY REFORM
    #   xlsx ÖVR = XML:s HANDSKRIVNA (handskrivna namn utan egen partirad)
    RENAME_XML = {"1372": "BASIP", "1374": "INI", "1385": "NYREF", "HANDSKRIVNA": "ÖVR"}

    def kanon_xls(p):
        return p.zfill(4) if p.isdigit() else p

    def kanon_xml(p):
        if p in RENAME_XML:
            return RENAME_XML[p]
        return p.zfill(4) if p.isdigit() else p

    # --- roster: bygg xlsx-dict och xml-dict med gemensam partinyckel
    xls_r = {}
    for row in xls_roster:
        key = (row["kod"], kanon_xls(row["parti"]))
        xls_r[key] = xls_r.get(key, 0) + i0(row["roster"])
    xml_r = {}
    for (kod, parti), roster in roster_lookup.items():
        key = (kod, kanon_xml(parti))
        xml_r[key] = xml_r.get(key, 0) + roster

    for grupp, filt in (("Göteborg exkl uppsamling", lambda k: k[0] != "14800000"),
                         ("uppsamlingsdistriktet", lambda k: k[0] == "14800000")):
        keys = {k for k in xls_r if filt(k)} | {k for k in xml_r if filt(k)}
        celler = 0
        avvik = []
        for k in sorted(keys):
            a, b = xls_r.get(k, 0), xml_r.get(k, 0)
            celler += 1
            if a != b:
                avvik.append((k, a, b))
        print("  roster %s: %d celler jamforda, %d avvikelser" % (grupp, celler, len(avvik)))
        for k, a, b in avvik:
            print("    AVVIKELSE roster %s %s: xlsx=%d xml=%d" % (val, k, a, b))

    # --- distrikt: giltiga, ogiltiga, rostberattigade, valdeltagande
    xls_d = {row["kod"]: row for row in xls_distrikt}
    falt = ["giltiga", "ogiltiga", "rostberattigade", "valdeltagande"]
    for grupp, koder in (("Göteborg exkl uppsamling",
                          [k for k in distrikt_lookup if k != "14800000"]),
                         ("uppsamlingsdistriktet", ["14800000"])):
        celler = 0
        avvik = []
        for kod in koder:
            x = distrikt_lookup[kod]
            y = xls_d.get(kod)
            if y is None:
                avvik.append((kod, "saknas i xlsx-filen", "", ""))
                continue
            for f in falt:
                celler += 1
                a, b = str(y[f]), str(x[f])
                if f == "valdeltagande":
                    a = a or "0.00"
                    b = b or "0.00"
                if a != b:
                    avvik.append((kod, f, a, b))
        print("  distrikt %s: %d celler jamforda (falt %s), %d avvikelser" % (
            grupp, celler, falt, len(avvik)))
        for kod, f, a, b in avvik:
            print("    AVVIKELSE distrikt %s %s %s: xlsx=%r xml=%r" % (val, kod, f, a, b))


# ----------------------------------------------------------- kontroll B
def kontroll_b(alla_fg_rows):
    print("\n### Kontroll B: kedjekontroll 2014 till 2018 ###")
    kedja = read_csv(os.path.join(UT_DIR, "kedja_2014_2018.csv"))
    kedja_by_kod = {r["kod_2018"]: r for r in kedja}

    for val in ("rd", "rf", "kf"):
        roster_2014 = {(r["kod"], r["parti"]): i0(r["roster"])
                        for r in read_csv(os.path.join(UT_DIR, "roster_2014_%s_xml.csv" % val))}
        fg_by_kod = defaultdict(list)
        for row in alla_fg_rows[val]:
            # row = [ar_fg, val, kod_2018, namn_2018, parti, roster_2018, roster_fgval]
            fg_by_kod[row[2]].append(row)

        print("\n  -- %s --" % val)
        stat = defaultdict(lambda: {"n": 0, "saknas": 0, "exakt": 0, "avvik": 0, "exempel": []})
        # BLANK och OG ar ogiltigrostkategorier, inte partier, och finns inte
        # i roster_2014_<val>_xml.csv (den filen har bara GILTIGA-rader plus
        # HANDSKRIVNA). De jamfors darfor inte har utan bara i deltagande-
        # filens giltiga/rostande-tal. OVRIGA_FGVAL uteslutet av samma skal
        # som i 2014-notens fgval-filer: det ar en residual utan 1:1-partner.
        EJ_PARTI = ("ÖVRIGA_FGVAL", "BLANK", "OG")
        for kod18, rad in sorted(kedja_by_kod.items()):
            typ = rad["typ"]
            stat[typ]["n"] += 1
            fgrader = [r for r in fg_by_kod.get(kod18, []) if r[4] not in EJ_PARTI]
            if not fgrader:
                stat[typ]["saknas"] += 1
                continue
            kod14 = rad["kod_2014_troligast"]
            avvik_har = False
            for r in fgrader:
                parti = r[4]
                fgval = r[6]
                # saknad rad i roster_2014_xml.csv betyder 0 roster (samma
                # konvention som RÖSTER_FGVAL-attributet: utelämnat = 0)
                akt = roster_2014.get((kod14, parti), 0)
                if fgval != akt:
                    avvik_har = True
                    if len(stat[typ]["exempel"]) < 3:
                        stat[typ]["exempel"].append(
                            "%s parti %s: fgval=%d faktiskt 2014 (%s)=%d" % (
                                kod18, parti, fgval, kod14, akt))
            if avvik_har:
                stat[typ]["avvik"] += 1
            else:
                stat[typ]["exakt"] += 1

        print("  %-14s %6s %8s %8s %8s" % ("typ", "antal", "saknar", "exakt", "avvik"))
        for typ in sorted(stat, key=lambda t: -stat[t]["n"]):
            s = stat[typ]
            print("  %-14s %6d %8d %8d %8d" % (typ, s["n"], s["saknas"], s["exakt"], s["avvik"]))
            for ex in s["exempel"]:
                print("      exempel: %s" % ex)


# ----------------------------------------------------------- kontroll C
def kontroll_c():
    print("\n### Kontroll C: areametoden mot facit, Majorna-Linné ###")
    kedja = read_csv(os.path.join(UT_DIR, "kedja_2014_2018.csv"))
    kedja_ml = [r for r in kedja
                if r["kod_2018"].startswith("148010") and r["typ"] in ("delad", "omritad")]
    print("  Majorna-Linné (148010xx) delade eller omritade: %d distrikt" % len(kedja_ml))

    overlap = defaultdict(list)  # kod_2018 -> [(kod_2014, andel_av_2014)]
    for r in read_csv(os.path.join(UT_DIR, "geo_overlap_2014_2018.csv")):
        andel = float(r["andel_av_2014"])
        if andel > 0:
            overlap[r["kod_2018"]].append((r["kod_2014"], andel))

    skv = defaultdict(list)  # kod_2018 -> [(kod_2014, procent/100)]
    for kod14, kod18, procent in read_skv(SKV_MAPPNING):
        if kod18.startswith("1480"):
            skv[kod18].append((kod14, float(procent) / 100.0))

    roster_2014_rd = {(r["kod"], r["parti"]): i0(r["roster"])
                       for r in read_csv(os.path.join(UT_DIR, "roster_2014_rd_xml.csv"))}
    fgval_rd = defaultdict(dict)
    for r in read_csv(os.path.join(UT_DIR, "fgval_2018_rd.csv")):
        if r["parti"] in MAINPARTIER:
            fgval_rd[r["kod_2018"]][r["parti"]] = i0(r["roster_fgval"])

    rows = []
    n_med_facit = 0
    fel_area, fel_off = [], []
    for r in kedja_ml:
        kod18, namn18 = r["kod_2018"], r["namn_2018"]
        for parti in MAINPARTIER:
            skatt_area = sum(roster_2014_rd.get((k14, parti), 0) * andel
                              for k14, andel in overlap.get(kod18, []))
            skatt_off = sum(roster_2014_rd.get((k14, parti), 0) * andel
                             for k14, andel in skv.get(kod18, []))
            facit = fgval_rd.get(kod18, {}).get(parti)
            if facit is not None:
                n_med_facit += 1
                diff_a = round(skatt_area - facit, 1)
                diff_o = round(skatt_off - facit, 1)
                fel_area.append(abs(diff_a))
                fel_off.append(abs(diff_o))
            else:
                diff_a = diff_o = ""
            rows.append([kod18, namn18, "rd", parti, facit if facit is not None else "",
                         round(skatt_area, 1), round(skatt_off, 1), diff_a, diff_o])

    write_csv(os.path.join(UT_DIR, "fgval_2018_metodjamforelse.csv"),
              ["kod_2018", "namn_2018", "val", "parti", "fgval", "skattning_area",
               "skattning_officiell", "diff_area", "diff_officiell"], rows)
    print("  rader totalt (distrikt x parti): %d, varav med FGVAL-facit: %d" % (len(rows), n_med_facit))
    if fel_area:
        print("  medelabsolutfel areametod mot FGVAL: %.1f roster (n=%d)" % (
            sum(fel_area) / len(fel_area), len(fel_area)))
        print("  medelabsolutfel officiell skv-vikt mot FGVAL: %.1f roster (n=%d)" % (
            sum(fel_off) / len(fel_off), len(fel_off)))
    else:
        print("  inget distrikt hade FGVAL for V/S/MP/M/SD, medelabsolutfel mot facit kan inte beraknas")
    # informativt matt aven utan facit: hur mycket de tva skattningsmetoderna
    # skiljer sig at inbordes, per distrikt och parti
    metoddiff = [abs(round(r[5], 1) - round(r[6], 1)) for r in rows]
    print("  medelabsolutskillnad mellan areametod och officiell skv-vikt (utan facit): "
          "%.1f roster (n=%d)" % (sum(metoddiff) / len(metoddiff), len(metoddiff)))


# ----------------------------------------------------------- kontroll D
def kontroll_d():
    print("\n### Kontroll D: omradesnivan, de 22 Majorna-distrikten 2018 ###")
    inne = [r["kod"] for r in read_csv(os.path.join(UT_DIR, "geo_majorna_2018.csv"))
            if float(r["andel_i_majorna"]) >= 0.5]
    print("  distrikt klassade 'inne': %d" % len(inne))

    tidsserie_2014 = {(r["val"], r["parti"]): r for r in read_csv(os.path.join(UT_DIR, "majorna_tidsserie.csv"))
                       if r["ar"] == "2014"}

    for val in ("rd", "rf", "kf"):
        fgval_by_kod = defaultdict(dict)
        for r in read_csv(os.path.join(UT_DIR, "fgval_2018_%s.csv" % val)):
            if r["kod_2018"] in inne:
                fgval_by_kod[r["kod_2018"]][r["parti"]] = i0(r["roster_fgval"])
        distrikt = {r["kod"]: r for r in read_csv(os.path.join(UT_DIR, "distrikt_%d_%s_xml.csv" % (AR, val)))}

        med_fgval = [k for k in inne if fgval_by_kod.get(k)]
        utan_fgval = [k for k in inne if not fgval_by_kod.get(k)]
        giltiga_tot = sum(i0(distrikt[k]["giltiga"]) for k in inne if k in distrikt)
        giltiga_utan = sum(i0(distrikt[k]["giltiga"]) for k in utan_fgval if k in distrikt)
        andel_utan = giltiga_utan / giltiga_tot if giltiga_tot else 0

        print("\n  -- %s --" % val)
        print("  distrikt med FGVAL: %d av %d (%s)" % (
            len(med_fgval), len(inne), sorted(med_fgval)))
        print("  distrikt utan FGVAL: %d av %d, som star for %d av %d giltiga roster (%.1f%%)" % (
            len(utan_fgval), len(inne), giltiga_utan, giltiga_tot, 100 * andel_utan))

        summa = defaultdict(int)
        for k in inne:
            for p, v in fgval_by_kod.get(k, {}).items():
                summa[p] += v
        print("  %-8s %10s %10s %10s" % ("parti", "sum_fgval", "2014-facit", "diff"))
        for p in MAINPARTIER:
            facit_row = tidsserie_2014.get((val, p))
            facit = i0(facit_row["roster"]) if facit_row else None
            s = summa.get(p, 0)
            diff = s - facit if facit is not None else ""
            print("  %-8s %10d %10s %10s" % (p, s, facit if facit is not None else "-", diff))


# ------------------------------------------------------------------- main
def main():
    os.makedirs(UT_DIR, exist_ok=True)
    roster_lookups, distrikt_lookups, alla_fg_rows = {}, {}, {}
    kommun_els = {}
    for val, bokstav in VAL.items():
        kallfil = "slutresultat_1480%s.xml" % bokstav
        rl, dl, fg = bygg_val(val, bokstav, kallfil)
        roster_lookups[val], distrikt_lookups[val], alla_fg_rows[val] = rl, dl, fg
        kommun_els[val] = load(kallfil).find("KOMMUN")

    print("\n### Riket-kontroll (lattviktig) ###")
    for val, bokstav in VAL.items():
        riket_kontroll(val, bokstav, kommun_els[val])

    for val in ("rd", "rf", "kf"):
        kontroll_a(val, roster_lookups[val], distrikt_lookups[val])

    kontroll_b(alla_fg_rows)
    kontroll_c()
    kontroll_d()


if __name__ == "__main__":
    main()
