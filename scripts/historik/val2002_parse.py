#!/usr/bin/env python3
"""Tolkar 2002 ars slutresultat for Goteborg (1480) fran sparade sidor
(hamtade med val2002_fetch.py) och skriver CSV i langt format.

Utdata (UTF-8, semikolon, punkt som decimaltecken, koder som 8-siffrig text):
  roster_2002_<val>.csv          ar;val;kod;namn;parti_kalla;parti;roster;andel
  roster_2002_<val>_ovriga.csv   samma kolumner, uppdelning av "Varav ovriga" per distrikt
  distrikt_2002_<val>.csv        ar;val;kod;namn;valkrets;giltiga;blanka;ogiltiga_ovriga;ogiltiga;
                                 rostande;rostberattigade;valdeltagande;kalla_fil
  aggregat_2002_<val>.csv        ar;val;niva;parti_kalla;parti;roster;andel;giltiga;rostande;rostberattigade
  aggregat_2002_<val>_ovriga.csv samma kolumner, uppdelning av "Varav ovriga" per niva
  distrikt_2002_indelning.csv    ar;val;kod;namn;andrad_indelning  (1 = sidan visar "Andrad indelning",
                                 0 = sidan visar +-% mot 1998)
val = rd (riksdag, R), rf (landsting, L), kf (kommunfullmaktige, K).

Kallsidorna ar UTF-8 (META charset=UTF-8 i HTML-sidorna; textsidorna saknar META men ar
ocksa UTF-8). Alla tal kommer ordagrant ur sidorna; giltiga och rostande
ar summor av kolumnerna pa samma sida (giltiga = alla partikolumner inklusive OVR,
rostande = giltiga + OG). Rostberattigade finns inte pa 2002 ars sidor och lamnas tom.
"""
import csv
import html
import os
import re
import sys

DL_DIR = "/Users/daniel/code/Temp/Historiska dokument/dl2002"
OUT_DIR = "/Users/daniel/code/Temp/data/historik"
AR = "2002"
KOMMUN = "1480"
VALKRETSAR = ["148001", "148002", "148003", "148004"]
VAL_KOD = {"R": "rd", "L": "rf", "K": "kf"}
# Sidor med "I vallokal ej raknade roster" (fortidsroster med mera som raknats onsdagen efter valet
# och inte fordelats pa valdistrikt). R och L har en per kommun, K en per kommunvalkrets.
EJ_RAKNADE = {
    "R": [("14R_1480_R-1480-16.html", "ej_raknade_i_vallokal")],
    "L": [("14L_1480_L-1480-01.html", "ej_raknade_i_vallokal")],
    "K": [(f"14K_1480_K-1480-0{i}.html", f"ej_raknade_i_vallokal-Göteborg {i}") for i in (1, 2, 3, 4)],
}
# Sidor for aggregatnivaer: (fil med HTML-tabell, niva)
AGGREGAT_HTML = {
    "R": [("00R_00.html", "riket"), ("14R_14.html", "vgregion"), ("14R_1480_1480.html", "goteborg")],
    "L": [("00L_00.html", "riket"), ("14L_14.html", "vgregion"), ("14L_1480_1480.html", "goteborg")],
    "K": [("00K_00.html", "riket"), ("14K_14.html", "vgregion"), ("14K_1480_1480.html", "goteborg")],
}
PARTI_NORM = {"FP": "L", "DEM": "D", "KP": "K"}


def norm_parti(kalla):
    return PARTI_NORM.get(kalla, kalla.upper())


def num(s):
    """'1 234' eller '17,4' -> int eller float som text med punkt."""
    s = s.strip().replace("\xa0", "").replace(" ", "")
    if s in ("", "&nbsp;"):
        return ""
    if "," in s:
        return s.replace(",", ".")
    return s


ANOMALIER = []


def read(fname):
    with open(os.path.join(DL_DIR, fname), "rb") as f:
        b = f.read()
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        ANOMALIER.append(f"{fname}: inte giltig UTF-8, last som ISO-8859-1")
        return b.decode("iso-8859-1")


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def table_rows(seg):
    """Lista av rader, varje rad en lista av celltexter. Avstandsceller (WIDTH="0" och
    WIDTH="10") hoppas over, men tomma varden i riktiga celler behalls sa att kolumnerna
    ligger kvar i rätt position."""
    rows = []
    for tr in re.findall(r"<TR>(.*?)</TR>", seg, re.S):
        cells = []
        for attrs, content in re.findall(r"<T[DH]([^>]*)>(.*?)(?=<T[DH][^>]*>|$)", tr, re.S):
            if 'WIDTH="0"' in attrs or 'WIDTH="10"' in attrs:
                continue
            cells.append(strip_tags(content))
        rows.append(cells)
    return rows


def parse_votes_page(fname):
    """Tolkar en HTML-sida med rostetabell (valdistrikt, valkrets, kommun, lan, riket)."""
    t = read(fname)
    title = strip_tags(re.search(r"<TITLE>(.*?)</TITLE>", t, re.S).group(1))
    crumbs = re.findall(r'<A HREF="/val/val_02/slutresultat/[^"]*">([^<]*)</A>', t.split("<!-- Shortcuts 2 -->")[0])
    crumbs = [strip_tags(c) for c in crumbs]
    a = t.index("<!-- Votes Table -->")
    b = t.index("<!-- end table, level 1 -->", a)
    seg = t[a:b]
    # den inre tabellen med partirubrikerna (TH WIDTH="82" ALIGN=CENTER, bredden varierar mellan sidor)
    th_re = re.compile(r'<TH WIDTH="(?!0"|10")\d+" ALIGN=CENTER>(.*?)</TH>', re.S)
    h0 = th_re.search(seg).start()
    ta = seg.rindex("<TABLE", 0, h0)
    tb = seg.index("</TABLE>", h0)
    inner = seg[ta:tb]
    header = [strip_tags(h) for h in th_re.findall(inner)]
    if not header:
        raise ValueError(f"{fname}: ingen partirad")
    rows = [r for r in table_rows(inner) if any(c for c in r)]
    # rad 0 = rubriker, rad 1 = roster, rad 2 = procent, rad 3 = +-% eller "Andrad indelning"
    votes = rows[1]
    pct = rows[2]
    row3 = rows[3] if len(rows) > 3 else []
    if len(votes) != len(header):
        raise ValueError(f"{fname}: {len(votes)} rostceller mot {len(header)} rubriker: {votes}")
    if header[-1] != "OG":
        raise ValueError(f"{fname}: sista kolumnen ar inte OG: {header}")
    for i, c in enumerate(votes):
        if c == "":
            # tom cell for ett parti; procentraden visar 0,0 och textsidan 0
            ANOMALIER.append(f"{fname}: tom rostcell for {header[i]} tolkad som 0")
            votes[i] = "0"
        elif not re.fullmatch(r"\d+", c):
            raise ValueError(f"{fname}: oväntat värde i rostcell {header[i]}: {c!r}")
    andrad = 1 if any("ndrad indelning" in c for c in row3) else 0
    # Vdt% star i en egen liten tabell efter rostetabellen; sok bara inom den tabellen
    vdt = ""
    vi = seg.find("Vdt%")
    if vi >= 0:
        vseg = seg[vi:seg.index("</TABLE>", vi)]
        m = re.search(r"<TD[^>]*>\s*([\d,]+)\s*<", vseg, re.S)
        vdt = num(m.group(1)) if m else ""
    parties = []
    for i, h in enumerate(header[:-1]):
        parties.append((h, int(votes[i]), num(pct[i]) if i < len(pct) else ""))
    og = int(votes[-1])
    # Varav ovriga
    varav = []
    va = t.find('NAME="varav-ovriga"')
    if va >= 0:
        vb = t.find("<!-- w3c", va)
        for r in table_rows(t[va:vb]):
            r = [c for c in r if c != ""]
            if len(r) == 3 and re.fullmatch(r"\d+", r[2]):
                varav.append((r[0], r[1], int(r[2])))
    return {"fil": fname, "titel": title, "crumbs": crumbs, "parties": parties, "og": og,
            "vdt": vdt, "andrad": andrad, "varav": varav}


def distrikt_codes(val):
    codes = {}
    for vk in VALKRETSAR:
        t = read(f"14{val}_{KOMMUN}_{vk}.html")
        for m in re.finditer(r'HREF="/val/val_02/slutresultat/14%s/%s/(\d{8})\.html">([^<]*)</A>' % (val, KOMMUN), t):
            codes[m.group(1)] = re.sub(r"\s+", " ", m.group(2)).strip()
    return codes


def parse_text_page(fname):
    """Tolkar en -text.html-sida (fast bredd). Returnerar lista av block:
    (label, kolumner, summa-tal, procent-tal, distriktsrader[(namn, tal)])."""
    t = read(fname)
    t = t[t.index("<PRE>") + 5:t.index("</PRE>")]
    blocks = []
    cols = None
    cur = None
    for line in t.splitlines():
        if not line.strip():
            continue
        # kolumnerna ar fasta i byte (namnet fylls ut till byte 37), dela darfor pa UTF-8-bytes
        lb = line.encode("utf-8")
        label, nums = lb[:37].decode("utf-8", "replace"), lb[37:].decode("utf-8", "replace").split()
        lab = re.sub(r"\s+", " ", label).strip()
        if not nums:
            continue
        if not re.search(r"\d", nums[0]) or lab == "":
            # rubrikrad med partiforkortningar
            hdr = line.split()
            if hdr and hdr[0] == "M" and hdr[-1] == "Vdt%":
                cols = hdr
            continue
        if lab.endswith("Summa"):
            cur = {"label": lab[:-5].strip(), "cols": cols, "summa": nums, "procent": None, "rader": []}
            blocks.append(cur)
        elif re.fullmatch(r"\d+ av \d+ distrikt %", lab) and cur is not None and cur["procent"] is None:
            cur["procent"] = nums
        elif lab.startswith("+- ") or lab.startswith("M(U)") or lab.startswith("+-"):
            continue
        elif re.match(r"\s{2,}\S", line) and cur is not None:
            cur["rader"].append((lab, nums))
    return blocks


def w(fname, rows, header):
    path = os.path.join(OUT_DIR, fname)
    with open(path, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, delimiter=";", lineterminator="\n")
        wr.writerow(header)
        wr.writerows(rows)
    print(f"skrev {path} ({len(rows)} rader)")


H_ROSTER = ["ar", "val", "kod", "namn", "parti_kalla", "parti", "roster", "andel"]
H_DISTRIKT = ["ar", "val", "kod", "namn", "valkrets", "giltiga", "blanka", "ogiltiga_ovriga", "ogiltiga",
              "rostande", "rostberattigade", "valdeltagande", "kalla_fil"]
H_AGG = ["ar", "val", "niva", "parti_kalla", "parti", "roster", "andel", "giltiga", "rostande", "rostberattigade"]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    indelning = []
    problems = []
    for val in ("R", "L", "K"):
        v = VAL_KOD[val]
        codes = distrikt_codes(val)
        roster, roster_ovr, distrikt, agg, agg_ovr = [], [], [], [], []
        summa = {}
        for code in sorted(codes):
            fname = f"14{val}_{KOMMUN}_{code}.html"
            try:
                p = parse_votes_page(fname)
            except FileNotFoundError:
                problems.append(f"{val}: saknar {fname}")
                continue
            namn = p["titel"].split(" - ")[0].strip()
            if namn != codes[code]:
                problems.append(f"{val} {code}: titel '{namn}' mot lanktext '{codes[code]}'")
            valkrets = [c for c in p["crumbs"] if re.fullmatch(r"Göteborg \d", c)]
            valkrets = valkrets[0] if valkrets else ""
            giltiga = sum(r for _, r, _ in p["parties"])
            for kalla, r, pct in p["parties"]:
                roster.append([AR, v, code, namn, kalla, norm_parti(kalla), r, pct])
                summa[kalla] = summa.get(kalla, 0) + r
            summa["OG"] = summa.get("OG", 0) + p["og"]
            for kalla, _, r in p["varav"]:
                roster_ovr.append([AR, v, code, namn, kalla, norm_parti(kalla), r, ""])
            ovr_main = dict((k, r) for k, r, _ in p["parties"]).get("ÖVR")
            if p["varav"] and ovr_main is not None and sum(r for _, _, r in p["varav"]) != ovr_main:
                problems.append(f"{val} {code}: varav ovriga summerar inte till OVR")
            distrikt.append([AR, v, code, namn, valkrets, giltiga, "", "", p["og"], giltiga + p["og"], "",
                             p["vdt"], fname])
            indelning.append([AR, v, code, namn, p["andrad"]])
        # Ej raknade i vallokal
        for fname, niva in EJ_RAKNADE[val]:
            p = parse_votes_page(fname)
            giltiga = sum(r for _, r, _ in p["parties"])
            for kalla, r, pct in p["parties"]:
                agg.append([AR, v, niva, kalla, norm_parti(kalla), r, pct, giltiga, giltiga + p["og"], ""])
                summa[kalla] = summa.get(kalla, 0) + r
            summa["OG"] = summa.get("OG", 0) + p["og"]
            for kalla, _, r in p["varav"]:
                agg_ovr.append([AR, v, niva, kalla, norm_parti(kalla), r, "", giltiga, giltiga + p["og"], ""])
        # Aggregat: riket, vgregion, goteborg ur HTML-sidor
        gbg = None
        for fname, niva in AGGREGAT_HTML[val]:
            p = parse_votes_page(fname)
            giltiga = sum(r for _, r, _ in p["parties"])
            for kalla, r, pct in p["parties"]:
                agg.append([AR, v, niva, kalla, norm_parti(kalla), r, pct, giltiga, giltiga + p["og"], ""])
            for kalla, _, r in p["varav"]:
                agg_ovr.append([AR, v, niva, kalla, norm_parti(kalla), r, "", giltiga, giltiga + p["og"], ""])
            if niva == "goteborg":
                gbg = p
        # Aggregat: kommunvalkretsar ur textsidan, samt kontroll av distriktsrader
        blocks = parse_text_page(f"14{val}_{KOMMUN}_{KOMMUN}-text.html")
        text_rows = {}
        for blk in blocks:
            cols = blk["cols"]
            if blk["label"] != "Göteborg":
                niva = "valkrets-" + blk["label"]
                nums = blk["summa"]
                og = int(nums[len(cols) - 2])
                giltiga = sum(int(x) for x in nums[:len(cols) - 2])
                for i, kalla in enumerate(cols[:-2]):
                    pct = num(blk["procent"][i]) if blk["procent"] else ""
                    agg.append([AR, v, niva, kalla, norm_parti(kalla), int(nums[i]), pct, giltiga, giltiga + og, ""])
            for namn, nums in blk["rader"]:
                if namn in text_rows:
                    text_rows[namn + "#" + blk["label"]] = (cols, nums)
                else:
                    text_rows[namn] = (cols, nums)
        # kontroll distriktssida mot textsida
        by_name = {}
        for row in roster:
            by_name.setdefault(row[3], {})[row[4]] = row[6]
        n_ok = 0
        for namn, d in by_name.items():
            if namn not in text_rows:
                problems.append(f"{val}: '{namn}' saknas i textsidan")
                continue
            cols, nums = text_rows[namn]
            tv = {cols[i]: int(nums[i]) for i in range(len(cols) - 2)}
            if tv != d:
                problems.append(f"{val} {namn}: distriktssida {d} mot textsida {tv}")
            else:
                n_ok += 1
        # kontroll: distrikt + ej raknade = Goteborg
        for kalla, r, _ in gbg["parties"]:
            if summa.get(kalla) != r:
                problems.append(f"{val} {kalla}: distrikt+ej raknade {summa.get(kalla)} mot Goteborg {r}")
        if summa.get("OG") != gbg["og"]:
            problems.append(f"{val} OG: {summa.get('OG')} mot {gbg['og']}")
        print(f"{val}: {len(distrikt)} distrikt, {n_ok} stammer mot textsidan, "
              f"{len(text_rows)} rader i textsidan, kontrollsumma mot Goteborg {'ok' if not [x for x in problems if x.startswith(val + ' ') and 'mot Goteborg' in x] else 'FEL'}")
        w(f"roster_{AR}_{v}.csv", roster, H_ROSTER)
        w(f"roster_{AR}_{v}_ovriga.csv", roster_ovr, H_ROSTER)
        w(f"distrikt_{AR}_{v}.csv", distrikt, H_DISTRIKT)
        w(f"aggregat_{AR}_{v}.csv", agg, H_AGG)
        w(f"aggregat_{AR}_{v}_ovriga.csv", agg_ovr, H_AGG)
    w(f"distrikt_{AR}_indelning.csv", indelning, ["ar", "val", "kod", "namn", "andrad_indelning"])
    print(f"{len(problems)} avvikelser")
    for p in problems:
        print("  ", p)
    print(f"{len(ANOMALIER)} noteringar vid tolkningen")
    for a in ANOMALIER:
        print("  ", a)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
