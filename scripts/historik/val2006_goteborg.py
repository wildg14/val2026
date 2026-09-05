#!/usr/bin/env python
"""val2006: valet 2006 for Goteborgs kommun (1480) per valdistrikt.

Laser Valmyndighetens xls (historik.val.se), shapefilens dbf och slutresultat-XML
(DTD parti_person_kommun 1.3) for riksdag (rd), landsting (rf) och kommun (kf),
kontrollerar kallorna mot varandra och skriver CSV i langt format till
data/historik/. Alla tal kommer ur kallfilerna, inget beraknas utom
ogiltiga = blanka + ogiltiga_ovriga (markerat i noteringen).

Kor: <venv>/bin/python scripts/historik/val2006_goteborg.py
"""
import csv
import os
import sys
from collections import OrderedDict, defaultdict

import xlrd
from dbfread import DBF
from lxml import etree

SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"
DL2006 = os.path.join(SCRATCH, "dl2006")
XLS_DIR = os.path.join(DL2006, "unz")
XLS_RD = os.path.join(XLS_DIR, "riksdagen_i_valdistrikt.xls")
XLS_RF = os.path.join(XLS_DIR, "landstingen_i_valdistrikt.xls")
XLS_KF = os.path.join(XLS_DIR, "kommunerna_i_valdistrikt_14.xls")
XLS_KOMMUNER_RD = os.path.join(XLS_DIR, "riksdagen_i_kommuner.xls")
DBF_RD = os.path.join(SCRATCH, "unz", "riksdagen_i_valdistrikt", "riksdagen_i_valdistrikt.dbf")
XML_1480 = {"rd": os.path.join(DL2006, "slutresultat_1480R.xml"),
            "rf": os.path.join(DL2006, "slutresultat_1480L.xml"),
            "kf": os.path.join(DL2006, "slutresultat_1480K.xml")}
XML_00 = {"rd": os.path.join(DL2006, "slutresultat_00R.xml"),
          "rf": os.path.join(DL2006, "slutresultat_00L.xml"),
          "kf": os.path.join(DL2006, "slutresultat_00K.xml")}
XLS_FILES = {"rd": XLS_RD, "rf": XLS_RF, "kf": XLS_KF}

PROJEKT = "/Users/daniel/code/Temp"
UT = os.path.join(PROJEKT, "data", "historik")
AR = 2006
KOMMUN = "1480"

# Normalisering av partikod enligt gemensam regel: FP->L, DEM->D, KP->K, annars versaler.
NORM = {"FP": "L", "DEM": "D", "KP": "K"}


def norm_parti(kod):
    k = kod.strip()
    return NORM.get(k.upper(), k.upper())


def pct(s):
    """'18,83' -> '18.83' (strang, oforandrad precision). Tom -> ''."""
    if s is None or s == "":
        return ""
    return s.replace(",", ".")


def fnum(v):
    """xls-flyttal med tva decimaler som text."""
    if v == "" or v is None:
        return ""
    return f"{float(v):.2f}"


def write_csv(name, header, rows):
    path = os.path.join(UT, name)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(["" if x is None else x for x in r])
    print(f"skrev {path} ({len(rows)} rader)")
    return path


# ----------------------------------------------------------------------------
# XLS per valdistrikt
# ----------------------------------------------------------------------------
def las_xls(path):
    """Returnerar (header, rader for 1480) dar rad = OrderedDict kolumn->varde."""
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    hdr = [str(c.value) for c in sh.row(0)]
    rows = []
    for r in range(1, sh.nrows):
        vals = [c.value for c in sh.row(r)]
        kod = str(vals[0]).strip()
        if not kod.startswith(KOMMUN):
            continue
        rows.append(OrderedDict(zip(hdr, vals)))
    return hdr, rows


def xls_partier(hdr):
    """Partikolumner (prefix) i ordning, exkl BLANK."""
    out = []
    for h in hdr:
        if h.endswith("_ROST") and h != "BLANK_ROST" and h != "TOT_ROST":
            out.append(h[:-5])
    return out


# ----------------------------------------------------------------------------
# XML
# ----------------------------------------------------------------------------
def las_xml(path):
    parser = etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False)
    return etree.parse(path, parser).getroot()


def xml_giltiga(el):
    """Lista (parti, roster, procent) for GILTIGA-elementen under el, med
    OVR uppdelad i VARAV_OVRIGA. Returnerar aven OVR-summan och avvikelser."""
    rader = []
    ovr_summa = None
    fel = []
    varav = set()
    for g in el.findall("GILTIGA"):
        p = g.get("PARTI")
        r = int(g.get("RÖSTER"))
        if p == "ÖVR":
            ovr_summa = r
            delsumma = 0
            for v in g.findall("VARAV_ÖVRIGA"):
                vr = int(v.get("RÖSTER"))
                delsumma += vr
                varav.add(v.get("PARTI"))
                rader.append((v.get("PARTI"), vr, pct(v.get("PROCENT"))))
            if delsumma != r:
                # Kallan anger en OVR-summa utan (fullstandig) uppdelning. Resten
                # skrivs som parti OVR sa att raderna summerar till RÖSTER.
                rest = r - delsumma
                varav.add("ÖVR")
                rader.append(("ÖVR", rest, pct(g.get("PROCENT")) if delsumma == 0 else ""))
                fel.append(f"ÖVR-summa {r} != summa VARAV_ÖVRIGA {delsumma}; resten {rest} skriven som parti ÖVR")
        else:
            rader.append((p, r, pct(g.get("PROCENT"))))
    return rader, ovr_summa, fel, varav


def xml_ogiltiga(el):
    d = {}
    for o in el.findall("OGILTIGA"):
        d[o.get("TEXT")] = int(o.get("RÖSTER"))
    return d


def xml_valdeltagande(el):
    v = el.find("VALDELTAGANDE")
    if v is None:
        return None
    return {"rostberattigade": int(v.get("RÖSTBERÄTTIGADE")),
            "rostande": int(v.get("SUMMA_RÖSTER")),
            "procent": pct(v.get("PROCENT"))}


def main():
    os.makedirs(UT, exist_ok=True)
    avvikelser = []
    kontroller = []

    # ------------------------------------------------------------------
    # 1. XML per valdistrikt, alla tre valen
    # ------------------------------------------------------------------
    xml_distrikt = {}     # val -> kod -> dict
    xml_roster = {}       # val -> kod -> {parti: roster}
    xml_ovr = {}          # val -> kod -> OVR-summa
    partier_rader = []    # partier_2006.csv
    aggregat = {v: [] for v in XML_1480}
    indelning = OrderedDict()

    for val, path in XML_1480.items():
        root = las_xml(path)
        fil = os.path.basename(path)
        for p in root.findall("PARTI"):
            partier_rader.append([AR, val, p.get("FÖRKORTNING"), norm_parti(p.get("FÖRKORTNING")),
                                  p.get("BETECKNING"), p.get("FÄRG") or "", fil])
        kommun = root.find("KOMMUN")
        assert kommun.get("KOD") == KOMMUN
        xml_distrikt[val] = OrderedDict()
        xml_roster[val] = {}
        xml_ovr[val] = {}

        def agg_rader(el, niva):
            rader, ovr, fel, varav = xml_giltiga(el)
            for f in fel:
                avvikelser.append(f"{fil} {niva}: {f}")
            og = xml_ogiltiga(el)
            vd = xml_valdeltagande(el)
            giltiga = int(el.get("RÖSTER"))
            if sum(r for _, r, _ in rader) != giltiga:
                avvikelser.append(f"{fil} {niva}: summa partier {sum(r for _, r, _ in rader)} != RÖSTER {giltiga}")
            out = []
            for p, r, a in rader:
                out.append([AR, val, niva, p, norm_parti(p), r, a, giltiga,
                            vd["rostande"] if vd else "", vd["rostberattigade"] if vd else ""])
            for text in ("BLANK", "OG"):
                if text in og:
                    o = [o for o in el.findall("OGILTIGA") if o.get("TEXT") == text][0]
                    out.append([AR, val, niva, text, text, og[text], pct(o.get("PROCENT")), giltiga,
                                vd["rostande"] if vd else "", vd["rostberattigade"] if vd else ""])
            if vd and giltiga + og.get("BLANK", 0) + og.get("OG", 0) != vd["rostande"]:
                avvikelser.append(f"{fil} {niva}: giltiga+blank+og != SUMMA_RÖSTER")
            return out

        aggregat[val] += agg_rader(kommun, "goteborg")
        for krets in kommun.findall("KRETS_KOMMUN"):
            kretsnamn = krets.get("NAMN")
            aggregat[val] += agg_rader(krets, kretsnamn)
            summa_krets = defaultdict(int)
            n_vd = 0
            for vd in list(krets.findall("VALDISTRIKT")) + list(krets.findall("ONSDAGSDISTRIKT")):
                kod = vd.get("KOD")
                onsdag = vd.tag == "ONSDAGSDISTRIKT"
                if onsdag:
                    # XML-kod R-1480-01 / L-1480-01 / K-1480-01 -> xls-kod 1480VK01
                    kod_x = KOMMUN + "VK" + kod[-2:]
                else:
                    kod_x = kod
                    n_vd += 1
                rader, ovr, fel, varav = xml_giltiga(vd)
                for f in fel:
                    avvikelser.append(f"{fil} {kod}: {f}")
                og = xml_ogiltiga(vd)
                vdl = xml_valdeltagande(vd)
                giltiga = int(vd.get("RÖSTER"))
                s = sum(r for _, r, _ in rader)
                if s != giltiga:
                    avvikelser.append(f"{fil} {kod}: summa partier {s} != RÖSTER {giltiga}")
                if vdl and giltiga + og.get("BLANK", 0) + og.get("OG", 0) != vdl["rostande"]:
                    avvikelser.append(f"{fil} {kod}: giltiga+blank+og != SUMMA_RÖSTER")
                for p, r, a in rader:
                    summa_krets[p] += r
                summa_krets["BLANK"] += og.get("BLANK", 0)
                summa_krets["OG"] += og.get("OG", 0)
                xml_distrikt[val][kod_x] = {
                    "kod_xml": kod, "namn": vd.get("NAMN"), "valkrets": kretsnamn,
                    "valkrets_kod": krets.get("KOD"), "onsdag": onsdag,
                    "indelning": vd.get("INDELNING") or "",
                    "roster_fgval": vd.get("RÖSTER_FGVAL") or "",
                    "giltiga": giltiga, "blanka": og.get("BLANK"), "og": og.get("OG"),
                    "rostande": vdl["rostande"] if vdl else None,
                    "rostberattigade": vdl["rostberattigade"] if vdl else None,
                    "valdeltagande": vdl["procent"] if vdl else "",
                    "rader": rader, "fil": fil}
                xml_roster[val][kod_x] = {p: r for p, r, _ in rader}
                xml_ovr[val][kod_x] = (ovr, varav)
                if not onsdag:
                    d = indelning.setdefault(kod, OrderedDict(
                        kod=kod, namn=vd.get("NAMN"), valkrets_kod=krets.get("KOD"), valkrets=kretsnamn))
                    d["indelning_" + val] = vd.get("INDELNING") or ""
                    d["giltiga_2002_" + val] = vd.get("RÖSTER_FGVAL") or ""
            # kontroll: distrikt + onsdagsdistrikt = krets
            krets_rader, _, _, _ = xml_giltiga(krets)
            krets_dict = {p: r for p, r, _ in krets_rader}
            krets_og = xml_ogiltiga(krets)
            diff = [p for p, r in krets_dict.items() if summa_krets.get(p, 0) != r]
            if krets_og.get("BLANK") != summa_krets["BLANK"] or krets_og.get("OG") != summa_krets["OG"]:
                diff.append("BLANK/OG")
            if diff:
                avvikelser.append(f"{fil} {kretsnamn}: summa distrikt != krets for {diff}")
            else:
                kontroller.append(f"{fil} {kretsnamn}: {n_vd} valdistrikt + onsdagsdistrikt summerar exakt till kretsen (alla partier, BLANK, OG)")
            if n_vd != int(krets.get("ALLA_VALDISTRIKT")) - 1:
                # ALLA_VALDISTRIKT raknar aven onsdagsdistriktet
                avvikelser.append(f"{fil} {kretsnamn}: {n_vd} VALDISTRIKT men ALLA_VALDISTRIKT={krets.get('ALLA_VALDISTRIKT')}")
        # kontroll: kretsar summerar till kommun
        kom_rader, _, _, _ = xml_giltiga(kommun)
        kom = {p: r for p, r, _ in kom_rader}
        summa = defaultdict(int)
        for kod_x, d in xml_distrikt[val].items():
            for p, r, _ in d["rader"]:
                summa[p] += r
        diff = [p for p, r in kom.items() if summa.get(p, 0) != r]
        if diff:
            avvikelser.append(f"{fil}: summa alla distrikt != KOMMUN for {diff}")
        else:
            kontroller.append(f"{fil}: alla {len(xml_distrikt[val])} distrikt (inkl onsdagsdistrikt) summerar exakt till KOMMUN 1480 per parti")

    # ------------------------------------------------------------------
    # 2. XML riket och lanet (00R/00L/00K)
    # ------------------------------------------------------------------
    mandat_rader = []
    for val, path in XML_00.items():
        root = las_xml(path)
        fil = os.path.basename(path)
        nation = root.find("NATION")

        def agg00(el, niva):
            rader, ovr, fel, varav = xml_giltiga(el)
            for f in fel:
                avvikelser.append(f"{fil} {niva}: {f}")
            og = xml_ogiltiga(el)
            vd = xml_valdeltagande(el)
            giltiga = int(el.get("RÖSTER"))
            if sum(r for _, r, _ in rader) != giltiga:
                avvikelser.append(f"{fil} {niva}: summa partier != RÖSTER")
            out = []
            for p, r, a in rader:
                out.append([AR, val, niva, p, norm_parti(p), r, a, giltiga, vd["rostande"], vd["rostberattigade"]])
            for text in ("BLANK", "OG"):
                o = [o for o in el.findall("OGILTIGA") if o.get("TEXT") == text][0]
                out.append([AR, val, niva, text, text, og[text], pct(o.get("PROCENT")), giltiga, vd["rostande"], vd["rostberattigade"]])
            return out

        aggregat[val] = agg00(nation, "riket") + aggregat[val]
        lan = [l for l in nation.findall("LÄN") if l.get("KOD") == "14"][0]
        aggregat[val] = aggregat[val][:len(agg00(nation, "riket"))] + agg00(lan, "vgregion") + aggregat[val][len(agg00(nation, "riket")):]
        # kontroll Goteborg i 00-filen mot 1480-filen
        for k in root.iter("KOMMUN"):
            if k.get("KOD") == KOMMUN:
                r00 = {p: r for p, r, _ in xml_giltiga(k)[0]}
                r1480 = {row[3]: row[5] for row in aggregat[val] if row[2] == "goteborg" and row[3] not in ("BLANK", "OG")}
                if r00 != r1480:
                    avvikelser.append(f"{fil} KOMMUN 1480 skiljer sig fran slutresultat_1480: {set(r00.items()) ^ set(r1480.items())}")
                else:
                    kontroller.append(f"{fil} KOMMUN 1480 = KOMMUN i slutresultat_1480 per parti")
                break
        if val == "rd":
            # mandatfordelning riksdagen: riket + varje riksdagsvalkrets
            def mandat(el, niva):
                for g in el.findall("GILTIGA"):
                    mandat_rader.append([AR, "rd", niva, el.get("KOD"), g.get("PARTI"), norm_parti(g.get("PARTI")),
                                         int(g.get("MANDAT")), int(g.get("VARAV_UTJÄMNING")),
                                         int(g.get("MANDAT_FGVAL")), int(g.get("RÖSTER")), pct(g.get("PROCENT")),
                                         el.get("MANDAT_VALKRETS") or el.get("MANDAT_VALOMRÅDE"), fil])
            mandat(nation, "riket")
            for kr in root.iter("KRETS_RIKSDAG"):
                mandat(kr, kr.get("NAMN"))
            s = sum(r[6] for r in mandat_rader if r[2] == "riket")
            if s != 349:
                avvikelser.append(f"{fil}: riksdagsmandat summerar till {s}, inte 349")
            else:
                kontroller.append(f"{fil}: riksdagsmandat pa riksniva summerar till 349; utjamningsmandat summerar till {sum(r[7] for r in mandat_rader if r[2] == 'riket')}")
            sk = sum(r[6] for r in mandat_rader if r[2] != "riket")
            if sk != 349:
                avvikelser.append(f"{fil}: valkretsmandat summerar till {sk}")

    # ------------------------------------------------------------------
    # 3. XLS per valdistrikt, alla tre valen, och jamforelse med XML
    # ------------------------------------------------------------------
    # xls-kolumn -> XML-partikod dar de skiljer sig
    XLS2XML = {"FI": "Fi", "PP": "0524", "SJVP": "Sjvåp"}
    xls_rows = {}
    for val, path in XLS_FILES.items():
        hdr, rows = las_xls(path)
        fil = os.path.basename(path)
        partier = xls_partier(hdr)
        xls_rows[val] = rows
        roster_rader = []
        n_mismatch = 0
        n_jamforda = 0
        for row in rows:
            kod = str(row["LKFV"]).strip()
            namn = str(row["NAMN"]).strip()
            xd = xml_distrikt[val].get(kod)
            if xd is None:
                avvikelser.append(f"{fil}: {kod} {namn} saknas i XML")
                continue
            if not xd["onsdag"] and xd["namn"] != namn:
                avvikelser.append(f"{fil}: namn '{namn}' != XML '{xd['namn']}' for {kod}")
            xr = xml_roster[val][kod]
            ovr_summa, varav = xml_ovr[val][kod]
            brutna_i_ovr = 0
            for p in partier:
                v = row[p + "_ROST"]
                if v == "":
                    continue
                r = int(v)
                roster_rader.append([AR, val, kod, namn, p, norm_parti(p), r, fnum(row[p + "_PROC"])])
                if p == "ÖVR":
                    continue
                xp = XLS2XML.get(p, p)
                n_jamforda += 1
                if xr.get(xp, 0) != r:
                    n_mismatch += 1
                    avvikelser.append(f"{fil} {kod} {p}: xls {r} != XML {xp} {xr.get(xp)}")
                if xp in varav:
                    brutna_i_ovr += r
            # xls OVR = XML OVR-summa minus de VARAV_OVRIGA-partier som xls bryter ut
            ovr_xls = int(row["ÖVR_ROST"])
            ovr_xml = ovr_summa - brutna_i_ovr
            if ovr_xls != ovr_xml:
                avvikelser.append(f"{fil} {kod} ÖVR: xls {ovr_xls} != XML-rest {ovr_xml}")
            # totaler
            tot = int(row["TOT_ROST"])
            xt = xd["giltiga"] + (xd["blanka"] or 0) + (xd["og"] or 0)
            if tot != xt:
                avvikelser.append(f"{fil} {kod} TOT_ROST {tot} != XML giltiga+blank+og {xt}")
            if int(row["BLANK_ROST"]) != xd["blanka"]:
                avvikelser.append(f"{fil} {kod} BLANK_ROST != XML BLANK")
            if not xd["onsdag"]:
                if int(row["ROSTB"]) != xd["rostberattigade"]:
                    avvikelser.append(f"{fil} {kod} ROSTB {row['ROSTB']} != XML {xd['rostberattigade']}")
                if fnum(row["VDT"]) != xd["valdeltagande"]:
                    avvikelser.append(f"{fil} {kod} VDT {row['VDT']} != XML {xd['valdeltagande']}")
            else:
                xd["rostande_xls"] = tot
        for kod in xml_distrikt[val]:
            if kod not in {str(r["LKFV"]).strip() for r in rows}:
                avvikelser.append(f"{fil}: XML-distrikt {kod} saknas i xls")
        kontroller.append(f"{fil}: {len(rows)} rader for 1480, {n_jamforda} partivarden jamforda med XML, {n_mismatch} avvikelser")
        write_csv(f"roster_{AR}_{val}_xls.csv",
                  ["ar", "val", "kod", "namn", "parti_kalla", "parti", "roster", "andel"], roster_rader)

    # ------------------------------------------------------------------
    # 4. roster_xml, distrikt, indelning
    # ------------------------------------------------------------------
    for val in XML_1480:
        rr = []
        dr = []
        for kod, d in xml_distrikt[val].items():
            for p, r, a in d["rader"]:
                rr.append([AR, val, kod, d["namn"], p, norm_parti(p), r, a])
            blank = d["blanka"] if d["blanka"] is not None else 0
            og = d["og"] if d["og"] is not None else 0
            rostande = d["rostande"] if d["rostande"] is not None else d.get("rostande_xls", "")
            dr.append([AR, val, kod, d["namn"], d["valkrets"], d["giltiga"], blank, og, blank + og,
                       rostande, d["rostberattigade"] if d["rostberattigade"] is not None else "",
                       d["valdeltagande"], d["fil"]])
        write_csv(f"roster_{AR}_{val}_xml.csv",
                  ["ar", "val", "kod", "namn", "parti_kalla", "parti", "roster", "andel"], rr)
        write_csv(f"distrikt_{AR}_{val}.csv",
                  ["ar", "val", "kod", "namn", "valkrets", "giltiga", "blanka", "ogiltiga_ovriga", "ogiltiga",
                   "rostande", "rostberattigade", "valdeltagande", "kalla_fil"], dr)
        write_csv(f"aggregat_{AR}_{val}.csv",
                  ["ar", "val", "niva", "parti_kalla", "parti", "roster", "andel", "giltiga", "rostande", "rostberattigade"],
                  aggregat[val])

    # ------------------------------------------------------------------
    # 5. dbf (riksdag): jamfor med xls och hamta valkretskoder
    # ------------------------------------------------------------------
    dbf = DBF(DBF_RD, encoding="latin-1", load=False)
    dbf_rows = {str(rec["Lkfv"]).strip(): rec for rec in dbf if str(rec["Lkfv"]).startswith(KOMMUN)}
    xls_rd = {str(r["LKFV"]).strip(): r for r in xls_rows["rd"]}
    n_ok = 0
    for kod, rec in dbf_rows.items():
        x = xls_rd.get(kod)
        if x is None:
            avvikelser.append(f"dbf: {kod} saknas i xls")
            continue
        for h in x:
            if h.endswith("_ROST") or h in ("ROSTB",):
                if int(x[h]) != int(rec[h]):
                    avvikelser.append(f"dbf {kod} {h}: {rec[h]} != xls {x[h]}")
        if rec["NAMN"].strip() != str(x["NAMN"]).strip():
            avvikelser.append(f"dbf {kod} namn '{rec['NAMN']}' != xls '{x['NAMN']}'")
        xd = xml_distrikt["rd"][kod]
        if rec["KVK_NAMN"].strip() != xd["valkrets"]:
            avvikelser.append(f"dbf {kod} KVK_NAMN '{rec['KVK_NAMN']}' != XML krets '{xd['valkrets']}'")
        d = indelning[kod]
        d["kvk_dbf"] = rec["KVK"].strip()
        d["lvk_dbf"] = rec["LVK"].strip() + " " + rec["LVK_NAMN"].strip()
        d["rvk_dbf"] = rec["RVK"].strip() + " " + rec["RVK_NAMN"].strip()
        n_ok += 1
    kontroller.append(f"dbf: {len(dbf_rows)} distrikt for 1480 (utan onsdagsdistrikt), {n_ok} jamforda med xls och XML-krets")

    ind_rader = []
    for kod, d in indelning.items():
        ind_rader.append([d["kod"], d["namn"], d["valkrets_kod"], d["valkrets"], d.get("kvk_dbf", ""),
                          d.get("lvk_dbf", ""), d.get("rvk_dbf", ""),
                          d.get("indelning_rd", ""), d.get("indelning_rf", ""), d.get("indelning_kf", ""),
                          d.get("giltiga_2002_rd", ""), d.get("giltiga_2002_rf", ""), d.get("giltiga_2002_kf", ""),
                          "slutresultat_1480R/L/K.xml; riksdagen_i_valdistrikt.dbf"])
    write_csv(f"distrikt_{AR}_indelning.csv",
              ["kod", "namn", "valkrets_kod", "valkrets", "kvk_dbf", "lvk_dbf", "rvk_dbf",
               "indelning_rd", "indelning_rf", "indelning_kf",
               "giltiga_2002_rd", "giltiga_2002_rf", "giltiga_2002_kf", "kalla_fil"], ind_rader)

    # ------------------------------------------------------------------
    # 6. riksdagen_i_kommuner.xls mot XML KOMMUN
    # ------------------------------------------------------------------
    wb = xlrd.open_workbook(XLS_KOMMUNER_RD)
    sh = wb.sheet_by_index(0)
    hdr = [str(c.value) for c in sh.row(0)]
    for r in range(1, sh.nrows):
        vals = [c.value for c in sh.row(r)]
        if str(vals[0]).strip() == KOMMUN:
            row = dict(zip(hdr, vals))
            gbg = {p: v for _, _, n, p, _, v, *_ in [tuple(x) for x in aggregat["rd"]] if n == "goteborg"}
            diff = []
            for p in xls_partier(hdr):
                if p == "ÖVR":
                    continue
                xp = XLS2XML.get(p, p)
                if gbg.get(xp) != int(row[p + "_ROST"]):
                    diff.append(p)
            tot = [x for x in aggregat["rd"] if x[2] == "goteborg"][0]
            if int(row["TOT_ROST"]) != tot[8] or int(row["ROSTB"]) != tot[9] or int(row["BLANK_ROST"]) != gbg["BLANK"]:
                diff.append("TOT/ROSTB/BLANK")
            if diff:
                avvikelser.append(f"riksdagen_i_kommuner.xls 1480 skiljer sig fran XML: {diff}")
            else:
                kontroller.append("riksdagen_i_kommuner.xls rad 1480 = XML KOMMUN 1480 for alla partikolumner, BLANK, TOT_ROST, ROSTB")
            break

    write_csv(f"mandat_{AR}_riksdag.csv",
              ["ar", "val", "niva", "kod", "parti_kalla", "parti", "mandat", "varav_utjamning", "mandat_2002",
               "roster", "andel", "mandat_totalt", "kalla_fil"], mandat_rader)
    write_csv(f"partier_{AR}.csv", ["ar", "val", "parti_kalla", "parti", "beteckning", "farg", "kalla_fil"], partier_rader)

    print("\nKONTROLLER")
    for k in kontroller:
        print(" ok ", k)
    print("\nAVVIKELSER", len(avvikelser))
    for a in avvikelser:
        print(" !! ", a)
    with open(os.path.join(SCRATCH, "val2006_kontroll.txt"), "w", encoding="utf-8") as f:
        f.write("KONTROLLER\n" + "\n".join(kontroller) + "\n\nAVVIKELSER\n" + "\n".join(avvikelser) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
