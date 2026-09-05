#!/usr/bin/env python3
"""Granskning av 2002-agentens filer (etikett granskning_2002).

Laser kallsidorna fran historik.val.se (sparade av val2002_fetch.py) med egen kod,
oberoende av val2002_parse.py, och jamfor med de skrivna CSV-filerna i data/historik/.
Dessutom jamfors 2002 ars tal med RÖSTER_FGVAL i 2006 ars XML (Valmyndigheten), som ar
en helt annan kalla for samma val.

Skriver bara till skarmen. Andrar inga filer.
"""
import csv
import os
import random
import re
import sys
from collections import defaultdict

from lxml import etree, html as lhtml

DL_DIR = "/Users/daniel/code/Temp/Historiska dokument/dl2002"
XML2006_DIR = "/Users/daniel/code/Temp/Historiska dokument/dl2006"
DATA_DIR = "/Users/daniel/code/Temp/data/historik"
KOMMUN = "1480"
VAL = {"R": "rd", "L": "rf", "K": "kf"}
EJ_RAKNADE = {
    "R": ["14R_1480_R-1480-16.html"],
    "L": ["14L_1480_L-1480-01.html"],
    "K": [f"14K_1480_K-1480-0{i}.html" for i in (1, 2, 3, 4)],
}
MAJORNA = [f"148013{i:02d}" for i in range(1, 13)]
PARTI_NORM = {"FP": "L", "DEM": "D", "KP": "K"}
# 2006 ars XML anvander andra forkortningar for samma partier som 2002 ars sidor
ALIAS_2006 = {"SPVG": "SFV", "K": "KPML"}

FEL = []
INFO = []


def fel(s):
    FEL.append(s)
    print("FEL", s)


def info(s):
    INFO.append(s)
    print("INFO", s)


def read_bytes(fname):
    with open(os.path.join(DL_DIR, fname), "rb") as f:
        return f.read()


def txt(el):
    return re.sub(r"\s+", " ", (el.text_content() or "").replace("\xa0", " ")).strip()


def to_num(s):
    s = s.replace("\xa0", "").replace(" ", "").strip()
    if s == "":
        return None
    if "," in s:
        return float(s.replace(",", "."))
    return int(s)


# ---------------------------------------------------------------- HTML-sidor (lxml)
def parse_html_page(fname):
    """Oberoende tolkning av en sida med rostetabell. Returnerar dict med header (partier + OG),
    votes (lista av int eller None for tom cell), pct, row4-text, vdt, varav (lista), titel,
    valkrets (brodsmula 'Göteborg N'), radindex och cellindex for sparbarhet."""
    b = read_bytes(fname)
    b.decode("utf-8")  # kastar UnicodeDecodeError om inte UTF-8
    doc = lhtml.fromstring(b.decode("utf-8"))
    title = txt(doc.find(".//title"))
    votes_tbl = None
    for tbl in doc.iter("table"):
        rows = tbl.findall("tr")
        if not rows:
            continue
        ths = [txt(c) for c in rows[0].findall("th") if c.get("width") not in ("0", "10")]
        if ths and ths[0] == "M" and ths[-1] == "OG" and tbl.find(".//table") is None:
            votes_tbl = tbl
            break
    if votes_tbl is None:
        raise ValueError(f"{fname}: ingen rostetabell")
    rows = votes_tbl.findall("tr")
    header = [txt(c) for c in rows[0].findall("th") if c.get("width") not in ("0", "10")]
    # rad 2: roster. Behall tomma celler.
    vcells = [c for c in rows[1] if c.get("width") not in ("0", "10")]
    votes = [to_num(txt(c)) for c in vcells]
    raw_index = [list(rows[1]).index(c) for c in vcells]  # cellindex i raden i HTML (0-baserat, inkl avstandsceller)
    pcells = [c for c in rows[2] if c.get("width") not in ("0", "10")]
    pct = [to_num(txt(c)) for c in pcells]
    row4 = txt(rows[3]) if len(rows) > 3 else ""
    if len(votes) != len(header):
        raise ValueError(f"{fname}: {len(votes)} celler mot {len(header)} rubriker")
    vdt = None
    for tbl in doc.iter("table"):
        rows2 = tbl.findall("tr")
        if rows2 and txt(rows2[0]) == "Vdt%" and len(rows2) >= 3:
            vdt = to_num(txt(rows2[2]))
            break
    varav = []
    anchors = doc.xpath('//a[@name="varav-ovriga"]')
    if anchors:
        a = anchors[0]
        # narmast foljande table med rubriken "Varav övriga"
        for tbl in a.xpath("following::table"):
            if "Varav" in txt(tbl):
                for tr in tbl.findall("tr")[2:]:
                    cells = [txt(c) for c in tr.findall("td")]
                    if len(cells) == 4:
                        varav.append((cells[0], cells[2], int(cells[3])))
                break
    crumbs = [txt(a) for a in doc.xpath('//a[starts-with(@href, "/val/val_02/slutresultat/")]')]
    valkrets = [c for c in crumbs if re.fullmatch(r"Göteborg \d", c)]
    return {
        "fil": fname, "titel": title, "header": header, "votes": votes, "pct": pct, "row4": row4,
        "vdt": vdt, "varav": varav, "valkrets": valkrets[0] if valkrets else "", "raw_index": raw_index,
    }


# ---------------------------------------------------------------- textsidor (fast bredd)
def parse_text_page(fname):
    """Oberoende tolkning av -text.html. Returnerar lista av (block, namn, cols, tal)
    dar tal ar lista av int/float i kolumnordning (Vdt kan saknas)."""
    t = read_bytes(fname).decode("utf-8")
    t = t[t.index("<PRE>") + 5:t.index("</PRE>")]
    out = []
    cols = None
    block = None
    for line in t.splitlines():
        if not line.strip() or line.startswith("<"):
            continue
        toks = line.split()
        if toks[0] == "M" and toks[-1] == "Vdt%":
            cols = toks
            continue
        if cols is None:
            continue
        # Summa-rader: allt efter ordet Summa ar tal. Ovriga rader: sista len(cols) tokens
        # ar tal om Vdt finns, annars len(cols)-1 (distriktsnamn kan sluta pa en siffra).
        if "Summa" in toks:
            n = len(toks) - toks.index("Summa") - 1
        else:
            n = len(cols)
            if not re.fullmatch(r"\d+,\d", toks[-1]):
                n -= 1
        nums = toks[-n:]
        if not all(re.fullmatch(r"\d+(,\d)?", x) for x in nums):
            continue  # +-%-rad, M(U)-rad m m
        rad_cols = cols
        har_vdt = 1 if re.fullmatch(r"\d+,\d", toks[-1]) else 0
        if "Summa" in toks and n != len(cols) - 1 + har_vdt:
            # i rikets textsida (K) har grupperingsrader for riksdagsvalkretsar bara riksdagspartierna
            # utan egen rubrikrad; anta grundkolumnerna
            bas = ["M", "C", "FP", "KD", "S", "V", "MP", "ÖVR", "OG", "Vdt%"]
            if n == len(bas) - 1 + har_vdt:
                rad_cols = bas
            else:
                # rad med tom cell (till exempel kommuner i andra lan i rikets textsida); anvands inte har
                continue
        label = " ".join(toks[:-n])
        if label.startswith("+-") or label.startswith("M(U)"):
            continue
        if label.endswith("Summa"):
            block = label[:-5].strip()
            out.append((block, "Summa", rad_cols, [to_num(x) for x in nums]))
        elif re.fullmatch(r"\d+ av \d+ distrikt %", label):
            continue
        else:
            out.append((block, label, cols, [to_num(x) for x in nums]))
    return out


# ---------------------------------------------------------------- CSV
def read_csv(fname):
    with open(os.path.join(DATA_DIR, fname), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def csv_quoted_codes(fname):
    """Kontroll att koden ar skriven som 8-siffrig text (ingen exponent, ingen avrundning)."""
    with open(os.path.join(DATA_DIR, fname), encoding="utf-8") as f:
        next(f)
        bad = [l.split(";")[2] for l in f if not re.fullmatch(r"\d{8}", l.split(";")[2])]
    return bad


# ---------------------------------------------------------------- 2006 XML
def fgval_2006(val):
    """RÖSTER_FGVAL (2002) ur 2006 ars XML: kommun, kretsar och de distrikt som har FGVAL."""
    path = os.path.join(XML2006_DIR, f"slutresultat_1480{val}.xml")
    root = etree.parse(path).getroot()
    kommun = root.find(".//KOMMUN")
    res = {}

    def giltiga(el):
        d = {}
        for g in el.findall("GILTIGA"):
            if g.get("RÖSTER_FGVAL") is not None:
                d[g.get("PARTI")] = int(g.get("RÖSTER_FGVAL"))
        og = None
        for o in el.findall("OGILTIGA"):
            if o.get("TEXT") == "OG" and o.get("RÖSTER_FGVAL") is not None:
                og = int(o.get("RÖSTER_FGVAL"))
        vd = el.find("VALDELTAGANDE")
        rb = vd.get("RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL") if vd is not None else None
        sr = vd.get("SUMMA_RÖSTER_FGVAL") if vd is not None else None
        return {"parti": d, "og": og, "roster_fgval": el.get("RÖSTER_FGVAL"),
                "rostberattigade": rb, "summa_roster": sr, "namn": el.get("NAMN"), "kod": el.get("KOD")}

    res["kommun"] = giltiga(kommun)
    res["krets"] = [giltiga(k) for k in kommun.findall("KRETS_KOMMUN")]
    res["distrikt"] = [giltiga(d) for d in kommun.iter("VALDISTRIKT") if d.get("RÖSTER_FGVAL") is not None]
    res["onsdag"] = [giltiga(d) for d in kommun.iter("ONSDAGSDISTRIKT") if d.get("RÖSTER_FGVAL") is not None]
    return res


# ---------------------------------------------------------------- huvudkontroll
def main():
    print("Granskning av 2002-filerna")
    print("=" * 70)
    alla_koder = {}
    for val, v in VAL.items():
        print(f"\n### {val} ({v})")
        roster = read_csv(f"roster_{2002}_{v}.csv")
        roster_ovr = read_csv(f"roster_{2002}_{v}_ovriga.csv")
        distrikt = read_csv(f"distrikt_{2002}_{v}.csv")
        agg = read_csv(f"aggregat_{2002}_{v}.csv")
        agg_ovr = read_csv(f"aggregat_{2002}_{v}_ovriga.csv")

        # (4) koder
        for fn in (f"roster_2002_{v}.csv", f"distrikt_2002_{v}.csv", f"roster_2002_{v}_ovriga.csv"):
            bad = csv_quoted_codes(fn)
            if bad:
                fel(f"{fn}: koder som inte ar 8 siffror: {sorted(set(bad))[:5]}")
        koder = [d["kod"] for d in distrikt]
        if len(koder) != len(set(koder)):
            fel(f"{v}: dubbla koder i distriktfilen")
        alla_koder[v] = set(koder)
        info(f"{v}: {len(koder)} distrikt i distriktfilen, {len(set(d['kod'] for d in roster))} i rosterfilen")
        if not all(k.startswith(KOMMUN) for k in koder):
            fel(f"{v}: koder som inte borjar med {KOMMUN}")
        # lankliste-koder ur valkretssidorna (oberoende)
        lank = {}
        for vk in ("148001", "148002", "148003", "148004"):
            doc = lhtml.fromstring(read_bytes(f"14{val}_1480_{vk}.html").decode("utf-8"))
            for a in doc.xpath('//a[@href]'):
                m = re.fullmatch(r"/val/val_02/slutresultat/14%s/1480/(\d{8})\.html" % val, a.get("href"))
                if m:
                    lank[m.group(1)] = (txt(a), f"Göteborg {vk[-1]}")
        if set(lank) != set(koder):
            fel(f"{v}: lanklistans koder skiljer sig fran distriktfilen: {set(lank) ^ set(koder)}")

        # (1)+(2)+(3) egen tolkning av alla distriktssidor
        rows_by_kod = defaultdict(dict)
        pct_by_kod = defaultdict(dict)
        for r in roster:
            rows_by_kod[r["kod"]][r["parti_kalla"]] = int(r["roster"])
            pct_by_kod[r["kod"]][r["parti_kalla"]] = r["andel"]
        ovr_by_kod = defaultdict(dict)
        for r in roster_ovr:
            ovr_by_kod[r["kod"]][r["parti_kalla"]] = int(r["roster"])
        dist_by_kod = {d["kod"]: d for d in distrikt}
        indelning = {r["kod"]: r["andrad_indelning"] for r in read_csv("distrikt_2002_indelning.csv") if r["val"] == v}

        summa_html = defaultdict(int)
        og_html = 0
        n_ok = 0
        tomma = 0
        headers = set()
        parsed = {}
        n_trunk = [0, 0, 0]  # [stammer med trunkering, darav stammer inte med avrundning, stammer bara med avrundning]
        for kod in sorted(koder):
            p = parse_html_page(f"14{val}_1480_{kod}.html")
            parsed[kod] = p
            headers.add(tuple(p["header"]))
            hv = dict(zip(p["header"], p["votes"]))
            og = hv.pop("OG")
            tomma += sum(1 for x in hv.values() if x is None)
            hv0 = {k: (x if x is not None else 0) for k, x in hv.items()}
            for k, x in hv0.items():
                summa_html[k] += x
            og_html += og
            d = dist_by_kod[kod]
            ok = True
            if hv0 != rows_by_kod[kod]:
                fel(f"{v} {kod}: roster i CSV {rows_by_kod[kod]} mot HTML {hv0}")
                ok = False
            if int(d["ogiltiga"]) != og:
                fel(f"{v} {kod}: ogiltiga CSV {d['ogiltiga']} mot HTML {og}")
                ok = False
            if d["valdeltagande"] != ("" if p["vdt"] is None else f"{p['vdt']:.1f}"):
                fel(f"{v} {kod}: valdeltagande CSV {d['valdeltagande']} mot HTML {p['vdt']}")
                ok = False
            # namn
            namn_html = p["titel"].split(" - ")[0].strip()
            if namn_html != d["namn"] or lank[kod][0].replace("  ", " ") != d["namn"]:
                fel(f"{v} {kod}: namn CSV '{d['namn']}' mot TITLE '{namn_html}' och lank '{lank[kod][0]}'")
            if d["valkrets"] != p["valkrets"] or d["valkrets"] != lank[kod][1]:
                fel(f"{v} {kod}: valkrets CSV {d['valkrets']} mot brodsmula {p['valkrets']} och lanklista {lank[kod][1]}")
            # procent
            hp = dict(zip(p["header"][:-1], p["pct"]))
            giltiga = sum(hv0.values())
            for k, x in hv0.items():
                src = hp.get(k)
                csvp = pct_by_kod[kod][k]
                if (src is None and csvp != "") or (src is not None and csvp != f"{src:.1f}"):
                    fel(f"{v} {kod} {k}: andel CSV {csvp} mot HTML {src}")
                if src is not None and giltiga:
                    exakt = 100.0 * x / giltiga
                    trunk = int(exakt * 10 + 1e-9) / 10.0
                    avr = round(exakt + 1e-9, 1)
                    if abs(trunk - src) < 1e-6:
                        n_trunk[0] += 1
                        if abs(avr - src) > 1e-6:
                            n_trunk[1] += 1
                    elif abs(avr - src) < 1e-6:
                        n_trunk[2] += 1
                    else:
                        fel(f"{v} {kod} {k}: andel {src} ar varken trunkerad ({trunk}) eller avrundad ({avr}) {x}/{giltiga}")
            # (2) summor
            if int(d["giltiga"]) != giltiga:
                fel(f"{v} {kod}: giltiga {d['giltiga']} mot partisumma {giltiga}")
            if int(d["rostande"]) != int(d["giltiga"]) + int(d["ogiltiga"]):
                fel(f"{v} {kod}: rostande {d['rostande']} != giltiga + ogiltiga")
            if d["rostberattigade"] != "" or d["blanka"] != "" or d["ogiltiga_ovriga"] != "":
                fel(f"{v} {kod}: rostberattigade/blanka/ogiltiga_ovriga inte tomma")
            if d["kalla_fil"] != p["fil"]:
                fel(f"{v} {kod}: kalla_fil {d['kalla_fil']}")
            # varav ovriga
            varav = {a: n for a, _, n in p["varav"]}
            if varav != ovr_by_kod[kod]:
                fel(f"{v} {kod}: varav ovriga CSV {ovr_by_kod[kod]} mot HTML {varav}")
            if varav and sum(varav.values()) != hv0.get("ÖVR"):
                fel(f"{v} {kod}: varav ovriga summerar till {sum(varav.values())}, ÖVR = {hv0.get('ÖVR')}")
            if not varav and hv0.get("ÖVR", 0) != 0:
                fel(f"{v} {kod}: ÖVR {hv0.get('ÖVR')} men ingen varav-tabell")
            # indelning
            andrad = "1" if "ndrad indelning" in p["row4"] else "0"
            if indelning.get(kod) != andrad:
                fel(f"{v} {kod}: andrad_indelning CSV {indelning.get(kod)} mot HTML '{p['row4']}'")
            if ok:
                n_ok += 1
        info(f"{v}: {n_ok} av {len(koder)} distrikt identiska med HTML-sidan (roster, OG, Vdt); "
             f"{tomma} tomma rostceller; kolumnuppsattningar {sorted(headers)}")
        info(f"{v}: andel (procent) i kallan: {n_trunk[0]} celler stammer med trunkering till en decimal, "
             f"varav {n_trunk[1]} skulle blivit annat vid avrundning; {n_trunk[2]} stammer bara med avrundning")
        # normalisering av partikod
        for r in roster + roster_ovr + agg + agg_ovr:
            exp = PARTI_NORM.get(r["parti_kalla"], r["parti_kalla"].upper())
            if r["parti"] != exp:
                fel(f"{v}: parti {r['parti']} for kalla {r['parti_kalla']}, vantat {exp}")

        # ej raknade i vallokal
        ej = {}
        for fn in EJ_RAKNADE[val]:
            p = parse_html_page(fn)
            hv = dict(zip(p["header"], p["votes"]))
            og = hv.pop("OG")
            hv = {k: (x or 0) for k, x in hv.items()}
            ej[fn] = (hv, og, {a: n for a, _, n in p["varav"]})
            for k, x in hv.items():
                summa_html[k] += x
            og_html += og
        # goteborg ur kommunsidan
        gbg = parse_html_page(f"14{val}_1480_1480.html")
        ghv = dict(zip(gbg["header"], gbg["votes"]))
        gog = ghv.pop("OG")
        if ghv != dict(summa_html):
            fel(f"{v}: summa distrikt + ej raknade {dict(summa_html)} mot kommunsidan {ghv}")
        else:
            info(f"{v}: summa over 286 distriktssidor + ej raknade = kommunsidan for alla partier")
        if gog != og_html:
            fel(f"{v}: OG summa {og_html} mot kommunsidan {gog}")

        # aggregat-filen
        agg_by = defaultdict(dict)
        agg_meta = {}
        for r in agg:
            agg_by[r["niva"]][r["parti_kalla"]] = int(r["roster"])
            agg_meta[r["niva"]] = (int(r["giltiga"]), int(r["rostande"]), r["rostberattigade"])
        for niva, d in agg_by.items():
            g, rs, rb = agg_meta[niva]
            if sum(d.values()) != g:
                fel(f"{v} aggregat {niva}: giltiga {g} != summa partier {sum(d.values())}")
            if rb != "":
                fel(f"{v} aggregat {niva}: rostberattigade inte tomt")
        if agg_by["goteborg"] != ghv:
            fel(f"{v} aggregat goteborg {agg_by['goteborg']} mot kommunsidan {ghv}")
        if agg_meta["goteborg"][1] - agg_meta["goteborg"][0] != gog:
            fel(f"{v} aggregat goteborg: rostande - giltiga != OG {gog}")
        # ej raknade i aggregat
        ej_nivaer = [n for n in agg_by if n.startswith("ej_raknade")]
        ej_sum = defaultdict(int)
        for n in ej_nivaer:
            for k, x in agg_by[n].items():
                ej_sum[k] += x
        ej_src = defaultdict(int)
        ej_og = 0
        for hv, og, _ in ej.values():
            for k, x in hv.items():
                ej_src[k] += x
            ej_og += og
        if dict(ej_sum) != dict(ej_src):
            fel(f"{v} aggregat ej_raknade {dict(ej_sum)} mot sidorna {dict(ej_src)}")
        else:
            info(f"{v}: ej raknade i vallokal: {len(ej_nivaer)} nivaer, giltiga {sum(ej_src.values())}, OG {ej_og}")

        # textsidan (kommun) - tredje lasning av distriktsraderna, plus valkretsblock
        text = parse_text_page(f"14{val}_1480_1480-text.html")
        by_block_name = {}
        for block, namn, cols, nums in text:
            by_block_name[(block, namn)] = (cols, nums)
        n_text_ok = 0
        for kod in koder:
            d = dist_by_kod[kod]
            key = (d["valkrets"], d["namn"])
            if key not in by_block_name:
                fel(f"{v} {kod}: '{d['namn']}' finns inte i block {d['valkrets']} i textsidan")
                continue
            cols, nums = by_block_name[key]
            tv = {cols[i]: nums[i] for i in range(len(cols) - 2)}
            tog = nums[len(cols) - 2]
            tvdt = nums[len(cols) - 1] if len(nums) == len(cols) else None
            if tv != rows_by_kod[kod] or tog != int(d["ogiltiga"]) or f"{tvdt:.1f}" != d["valdeltagande"]:
                fel(f"{v} {kod}: textsidan {tv} OG {tog} Vdt {tvdt} mot CSV")
            else:
                n_text_ok += 1
        info(f"{v}: {n_text_ok} av {len(koder)} distrikt stammer med textsidan (roster, OG, Vdt)")
        # valkretsar
        dist_per_vk = defaultdict(lambda: defaultdict(int))
        og_per_vk = defaultdict(int)
        for kod in koder:
            for k, x in rows_by_kod[kod].items():
                dist_per_vk[dist_by_kod[kod]["valkrets"]][k] += x
            og_per_vk[dist_by_kod[kod]["valkrets"]] += int(dist_by_kod[kod]["ogiltiga"])
        for vk in ("Göteborg 1", "Göteborg 2", "Göteborg 3", "Göteborg 4"):
            cols, nums = by_block_name[(vk, "Summa")]
            tv = {cols[i]: nums[i] for i in range(len(cols) - 2)}
            tog = nums[len(cols) - 2]
            niva = "valkrets-" + vk
            if agg_by.get(niva) != tv:
                fel(f"{v} aggregat {niva} {agg_by.get(niva)} mot textsidan {tv}")
            if agg_meta[niva][1] - agg_meta[niva][0] != tog:
                fel(f"{v} aggregat {niva}: OG {agg_meta[niva][1] - agg_meta[niva][0]} mot textsidan {tog}")
            # summa av distrikten i kretsen, med och utan ej raknade
            ejk = {}
            for fn, (hv, og, _) in ej.items():
                if val != "K" or fn.endswith(f"0{vk[-1]}.html"):
                    ejk = hv
                    ejog = og
            d_only = dict(dist_per_vk[vk])
            d_plus = {k: d_only.get(k, 0) + ejk.get(k, 0) for k in set(d_only) | set(ejk)}
            if tv == d_only:
                info(f"{v} {niva}: textsidans Summa = summa av distrikten utan ej raknade")
            elif tv == d_plus:
                info(f"{v} {niva}: textsidans Summa = summa av distrikten PLUS ej raknade")
            else:
                fel(f"{v} {niva}: textsidans Summa {tv} varken distrikt {d_only} eller distrikt + ej raknade {d_plus}")
        # riket och vgregion: HTML-sidorna i aggregat mot rikets textsida.
        # Vastra Gotalands lan finns i rikets textsida som riksdagsvalkretsar (norra, sodra, vastra, ostra)
        # plus Goteborg (R, K) eller som en rad (L); vgregion kontrolleras som summan av dessa.
        riket_text = parse_text_page(f"00{val}_00-text.html")
        vg_sum = defaultdict(int)
        vg_og = 0
        vg_block = []
        for block, namn, cols, nums in riket_text:
            if namn != "Summa":
                continue
            tv = {cols[i]: nums[i] for i in range(len(cols) - 2)}
            tog = nums[len(cols) - 2]
            if block.startswith("Västra Götaland") or block == ("Göteborgs kommun" if val == "L" else "Göteborg"):
                vg_block.append(block)
                # partier som inte har egen kolumn pa lansnivan (14X_14.html) laggs till ÖVR
                for k, x in tv.items():
                    vg_sum[k if k in agg_by["vgregion"] else "ÖVR"] += x
                vg_og += tog
            niva = {"Sverige": "riket", "Göteborg": "goteborg"}.get(block)
            if niva is None:
                continue
            if agg_by.get(niva) != tv:
                fel(f"{v} aggregat {niva} {agg_by.get(niva)} mot rikets textsida {tv}")
            elif agg_meta[niva][1] - agg_meta[niva][0] != tog:
                fel(f"{v} aggregat {niva}: OG mot rikets textsida {tog}")
            else:
                info(f"{v} aggregat {niva}: identisk med rikets textsida ({block}), giltiga {agg_meta[niva][0]}, OG {tog}")
        # riksdagsvalkretsarna i rikets textsida har NBP inuti ÖVR utom pa Sverige-raden (R)
        vg_cmp = dict(agg_by.get("vgregion", {}))
        if vg_cmp == dict(vg_sum) and agg_meta["vgregion"][1] - agg_meta["vgregion"][0] == vg_og:
            info(f"{v} aggregat vgregion: identisk med summan av {vg_block} i rikets textsida, giltiga {agg_meta['vgregion'][0]}, OG {vg_og}")
        else:
            fel(f"{v} aggregat vgregion {vg_cmp} (OG {agg_meta['vgregion'][1] - agg_meta['vgregion'][0]}) mot summan av {vg_block} {dict(vg_sum)} (OG {vg_og})")
        # andel i aggregat: trunkerad eller avrundad
        n_agg = [0, 0, 0]
        for r in agg:
            if r["andel"] == "":
                n_agg[2] += 1
                continue
            ex = 100.0 * int(r["roster"]) / int(r["giltiga"])
            tr = int(ex * 10 + 1e-9) / 10.0
            av = round(ex + 1e-9, 1)
            src = float(r["andel"])
            if abs(tr - src) < 1e-6:
                n_agg[0] += 1
            elif abs(av - src) < 1e-6:
                n_agg[1] += 1
            else:
                fel(f"{v} aggregat {r['niva']} {r['parti_kalla']}: andel {src} varken trunkerad {tr} eller avrundad {av}")
        info(f"{v} aggregat andel: {n_agg[0]} trunkerade, {n_agg[1]} bara avrundade, {n_agg[2]} tomma")
        # aggregat ovriga: summerar till ÖVR per niva
        ao = defaultdict(int)
        for r in agg_ovr:
            ao[r["niva"]] += int(r["roster"])
        for niva, s in ao.items():
            if s != agg_by[niva].get("ÖVR"):
                fel(f"{v} aggregat_ovriga {niva}: summa {s} mot ÖVR {agg_by[niva].get('ÖVR')}")
        info(f"{v}: aggregat_ovriga summerar till ÖVR for {len(ao)} nivaer")

        # (6) 2006 ars XML: RÖSTER_FGVAL = 2002
        fg = fgval_2006(val)
        km = fg["kommun"]
        for nyckel in ("kommun",):
            fg[nyckel]["parti"] = {ALIAS_2006.get(k, k): x for k, x in fg[nyckel]["parti"].items()}
        for kr in fg["krets"] + fg["distrikt"] + fg["onsdag"]:
            kr["parti"] = {ALIAS_2006.get(k, k): x for k, x in kr["parti"].items()}
        diff = {k: (km["parti"].get(k), ghv.get(k)) for k in set(km["parti"]) | set(ghv) if km["parti"].get(k) != ghv.get(k)}
        if diff:
            fel(f"{v} 2006-XML kommun FGVAL mot 2002 kommunsidan, avvikelser: {diff}")
        else:
            info(f"{v}: 2006-XML KOMMUN RÖSTER_FGVAL identisk med 2002 kommunsidan for {len(km['parti'])} partier")
        if km["og"] != gog:
            fel(f"{v} 2006-XML OG FGVAL {km['og']} mot 2002 {gog}")
        info(f"{v}: 2006-XML ger for 2002: RÖSTER_FGVAL {km['roster_fgval']}, SUMMA_RÖSTER_FGVAL {km['summa_roster']}, "
             f"RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL {km['rostberattigade']}; 2002-sidan: giltiga {agg_meta['goteborg'][0]}, "
             f"rostande {agg_meta['goteborg'][1]}, Vdt {[r['andel'] for r in []]}")
        vdt_gbg = gbg["vdt"]
        if km["rostberattigade"] and km["summa_roster"]:
            rb = int(km["rostberattigade"])
            sr = int(km["summa_roster"])
            info(f"{v}: baklanges: 2002 rostande {agg_meta['goteborg'][1]} / rostberattigade {rb} = "
                 f"{100.0 * agg_meta['goteborg'][1] / rb:.2f} procent, 2002-sidan visar Vdt {vdt_gbg}; "
                 f"SUMMA_RÖSTER_FGVAL {sr} {'=' if sr == agg_meta['goteborg'][1] else '!='} rostande")
        for kr in fg["krets"]:
            niva = "valkrets-" + kr["namn"]
            a = agg_by.get(niva, {})
            d2 = {k: (kr["parti"].get(k), a.get(k)) for k in set(kr["parti"]) | set(a) if kr["parti"].get(k) != a.get(k)}
            if d2:
                info(f"{v} 2006-XML krets {kr['kod']} {kr['namn']} FGVAL skiljer sig fran 2002 textsidans valkretssumma: {d2}")
            else:
                info(f"{v} 2006-XML krets {kr['kod']} {kr['namn']} FGVAL = 2002 textsidans valkretssumma")
        # distrikt med FGVAL i 2006: hitta 2002-distrikt med identisk partivektor
        for dd in fg["distrikt"]:
            match = [kod for kod in koder if all(rows_by_kod[kod].get(k) == x for k, x in dd["parti"].items())]
            samma_kod = rows_by_kod.get(dd["kod"])
            info(f"{v} 2006-XML distrikt {dd['kod']} {dd['namn']} FGVAL {dd['parti']} OG {dd['og']} "
                 f"matchar 2002-distrikt {[(m, dist_by_kod[m]['namn'], dist_by_kod[m]['ogiltiga']) for m in match]}; "
                 f"2002 med samma kod: {samma_kod} OG {dist_by_kod.get(dd['kod'], {}).get('ogiltiga')}")
            if not match:
                # par av 2002-distrikt som summerar till FGVAL (Summerad)
                import itertools
                par = [(a, b) for a, b in itertools.combinations(koder, 2)
                       if all(rows_by_kod[a].get(k, 0) + rows_by_kod[b].get(k, 0) == x for k, x in dd["parti"].items())]
                if par:
                    info(f"{v} 2006-XML distrikt {dd['kod']}: FGVAL = summa av 2002-distrikten "
                         f"{[(a, dist_by_kod[a]['namn'], b, dist_by_kod[b]['namn']) for a, b in par]}")
        for dd in fg["onsdag"]:
            info(f"{v} 2006-XML onsdagsdistrikt {dd['kod']} FGVAL {dd['parti']} OG {dd['og']}")

    # koder lika i alla tre valen
    if not (alla_koder["rd"] == alla_koder["rf"] == alla_koder["kf"]):
        fel("koderna skiljer sig mellan valen")
    else:
        info(f"samma {len(alla_koder['rd'])} koder i rd, rf och kf; Majorna (Karl Johan 1-12) = {MAJORNA}")
    # indelning-filen
    ind = read_csv("distrikt_2002_indelning.csv")
    info(f"distrikt_2002_indelning.csv: {len(ind)} rader, per val {dict((v, sum(1 for r in ind if r['val'] == v)) for v in ('rd', 'rf', 'kf'))}, "
         f"andrade per val {dict((v, sum(1 for r in ind if r['val'] == v and r['andrad_indelning'] == '1')) for v in ('rd', 'rf', 'kf'))}")
    per_kod = defaultdict(set)
    for r in ind:
        per_kod[r["kod"]].add(r["andrad_indelning"])
    olika = [k for k, s in per_kod.items() if len(s) > 1]
    if olika:
        info(f"andrad_indelning skiljer sig mellan valen for {olika}")

    # (5) stickprov: tre Majornadistrikt, tre partital var, mot racellen
    print("\n### Stickprov Majorna (slumpfro 2002)")
    rng = random.Random(2002)
    for val, v in VAL.items():
        kod = rng.choice(MAJORNA)
        p = parse_html_page(f"14{val}_1480_{kod}.html")
        roster = {(r["kod"], r["parti_kalla"]): (r["roster"], r["andel"]) for r in read_csv(f"roster_2002_{v}.csv")}
        partier = rng.sample(p["header"][:-1], 3)
        for pa in partier:
            i = p["header"].index(pa)
            cell = p["votes"][i]
            csvv = roster[(kod, pa)]
            status = "ok" if str(cell if cell is not None else 0) == csvv[0] else "FEL"
            print(f"  {status} {v} {kod} {p['titel'].split(' - ')[0].strip()} {pa}: racell {cell!r} "
                 f"(fil {p['fil']}, rostetabellen rad 2 'Röster', partikolumn {i + 1} av {len(p['header'])}, "
                 f"TD-index {p['raw_index'][i]} i raden), CSV roster {csvv[0]} andel {csvv[1]}")
            if status == "FEL":
                fel(f"stickprov {v} {kod} {pa}: {cell} mot {csvv[0]}")

    print("\n" + "=" * 70)
    print(f"{len(FEL)} fel, {len(INFO)} noteringar")
    for f in FEL:
        print("  FEL", f)
    return 1 if FEL else 0


if __name__ == "__main__":
    sys.exit(main())
