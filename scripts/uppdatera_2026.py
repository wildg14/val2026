#!/usr/bin/env python3
"""Tar in valresultat för ett nytt val (2026) och skriver data/valdata_<år>.json/.js samt swing mot 2022.

Vanlig körning på valnatten (en, två eller tre filer):
    .venv/bin/python scripts/uppdatera_2026.py --rd RD-FIL.xlsx [--rf RF-FIL.xlsx] [--kf KF-FIL.xlsx] \\
        --status preliminar [--tid 2026-09-13T21:30:00]

Reservväg om Valmyndighetens filformat ändrats: fyll i en CSV för hand (val;kod;parti;roster,
med raderna giltiga, rostande och rostberattigade per distrikt) och kör
    .venv/bin/python scripts/uppdatera_2026.py --csv valnatt.csv --status preliminar
Mall: --skriv-mall valnatt.csv

Generalrepetition: --repetera kör parsern på 2022 års råfiler och jämför med data/valdata_2022.json.

Skriptet filtrerar på de 23 distriktskoderna, larmar (VARNING:) om distrikt saknas, bytt namn,
om Göteborgs distriktsindelning ser ändrad ut eller om okända partier får röster, och avbryter (FEL:)
om filformatet inte känns igen eller om summorna inte går ihop.
"""
import argparse
import csv
import glob
import json
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))

from scripts import schema  # noqa: E402
from scripts.mandat import jamkade_uddatal  # noqa: E402
from scripts.valmyndigheten import (MAJORNA_KODER, NYCKELPARTIER, OVRIGA, VAL, FormatFel, SummaFel,  # noqa: E402
                                    aggregat_andelar, las_rafil, till_distrikt)

RAFIL_MONSTER = {"rd": "*oster-per-distrikt*riksdagsval*.xlsx", "rf": "*oster-per-distrikt*regionval*.xlsx",
                 "kf": "*oster-per-distrikt*kommunval*.xlsx"}
GOTEBORG_DISTRIKT_2022 = 411
METOD = "Räkneexempel: 4 %-spärr och jämkade uddatalsmetoden tillämpade på Majornas riksdagsröster {ar}."
VARNINGAR = []


def varning(text):
    VARNINGAR.append(text)
    print(f"VARNING: {text}", file=sys.stderr)


def fel(text):
    print(f"FEL: {text}", file=sys.stderr)
    sys.exit(1)


def tomma_distrikt(bas):
    namn = {d["kod"]: d["namn"] for d in bas["distrikt"]} if bas else {}
    return {kod: {"kod": kod, "namn": namn.get(kod, kod), "raknat": False, "rd": {}, "rf": {}, "kf": {},
                  "giltiga": {}, "rostande": {}, "rostberattigade": {}} for kod in MAJORNA_KODER}


def fyll(distrikt, kod, val, post):
    d = distrikt[kod]
    d[val] = post["roster"]
    d["giltiga"][val] = post["giltiga"]
    d["rostande"][val] = post["rostande"]
    d["rostberattigade"][val] = post["rostberattigade"]
    d["raknat"] = True


def las_rafiler(filer, distrikt, bas):
    """filer: {val: sökväg}. Fyller distrikt och returnerar jämförelseaggregat {omrade: {val: ...}}."""
    jamforelser = {"goteborg": {}, "riket": {}}
    for val, path in filer.items():
        print(f"Läser {val}: {path}")
        ra = las_rafil(path, MAJORNA_KODER)
        if ra["val"] != val:
            fel(f"{path}: bladet gäller {ra['val'].upper()}, men filen angavs som --{val}")
        gbg = ra["aggregat"]["goteborg"]["antal_distrikt"]
        if gbg != GOTEBORG_DISTRIKT_2022:
            varning(f"{val}: Göteborg har {gbg} valdistrikt i filen (2022: {GOTEBORG_DISTRIKT_2022}). "
                    "Distriktsindelningen kan ha ändrats, kontrollera att de 23 koderna fortfarande täcker Majorna.")
        for kod in MAJORNA_KODER:
            post = ra["distrikt"].get(kod)
            if post is None:
                varning(f"{val}: distrikt {kod} ({distrikt[kod]['namn']}) saknas i filen, markeras som oräknat")
                continue
            if bas and post["namn"] != bas_namn(bas, kod):
                varning(f"{val}: {kod} heter '{post['namn']}' i filen men '{bas_namn(bas, kod)}' 2022")
            try:
                d = till_distrikt(post, val)
            except SummaFel as ex:
                fel(f"{val}: {ex}")
            for etikett, n in d["okanda"].items():
                if n / d["giltiga"] >= 0.005:
                    varning(f"{val}: okänt parti '{etikett}' med {n} röster ({n / d['giltiga']:.1%}) i {post['namn']}, läggs i {OVRIGA}")
            fyll(distrikt, kod, val, d)
        try:
            agg = aggregat_andelar(ra)
        except SummaFel as ex:
            fel(f"{val}: {ex}")
        for omrade in ("goteborg", "riket"):
            if omrade in agg:
                jamforelser[omrade][val] = agg[omrade]
    return jamforelser


def bas_namn(bas, kod):
    return next((d["namn"] for d in bas["distrikt"] if d["kod"] == kod), kod)


def las_csv(path, distrikt):
    text = Path(path).read_text("utf-8-sig")
    avgransare = ";" if text.splitlines()[0].count(";") >= text.splitlines()[0].count(",") else ","
    rader = list(csv.DictReader(text.splitlines(), delimiter=avgransare))
    krav = {"val", "kod", "parti", "roster"}
    if not rader or not krav <= {k.strip().lower() for k in rader[0].keys()}:
        fel(f"{path}: CSV-filen måste ha kolumnerna val;kod;parti;roster")
    poster = {}
    for i, r in enumerate(rader, start=2):
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items()}
        if not r["kod"]:
            continue
        val, kod, parti = r["val"].lower(), r["kod"], r["parti"]
        if val not in VAL:
            fel(f"{path} rad {i}: okänt val '{val}' (rd, rf eller kf)")
        if kod not in MAJORNA_KODER:
            fel(f"{path} rad {i}: koden {kod} är inte ett av Majornas 23 distrikt")
        if r["roster"] == "":
            continue
        try:
            n = int(r["roster"].replace(" ", ""))
        except ValueError:
            fel(f"{path} rad {i}: '{r['roster']}' är inte ett heltal")
        p = poster.setdefault((val, kod), {"roster": {}, "giltiga": None, "rostande": None, "rostberattigade": 0})
        if parti.lower() in ("giltiga", "rostande", "rostberattigade"):
            p[parti.lower()] = n
        else:
            p["roster"][parti] = p["roster"].get(parti, 0) + n
    for (val, kod), p in sorted(poster.items()):
        if p["giltiga"] is None:
            fel(f"{path}: {val} {kod} saknar raden 'giltiga'")
        if sum(p["roster"].values()) != p["giltiga"]:
            fel(f"{path}: {val} {kod}: partiröster {sum(p['roster'].values())} != giltiga {p['giltiga']}")
        if p["rostande"] is None:
            varning(f"{val} {kod}: 'rostande' saknas, sätts lika med giltiga")
            p["rostande"] = p["giltiga"]
        if p["rostande"] < p["giltiga"]:
            fel(f"{path}: {val} {kod}: röstande {p['rostande']} < giltiga {p['giltiga']}")
        if not p["rostberattigade"]:
            varning(f"{val} {kod}: 'rostberattigade' saknas, valdeltagande kan inte visas")
        fyll(distrikt, kod, val, p)
    return {"goteborg": {}, "riket": {}}


def skriv_mall(path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["val", "kod", "parti", "roster"])
        bas = las_bas(ROT / "data" / "valdata_2022.json")
        for kod in MAJORNA_KODER:
            w.writerow([])
            w.writerow(["#", kod, bas_namn(bas, kod) if bas else "", ""])
            for p in NYCKELPARTIER["rd"] + [OVRIGA, "giltiga", "rostande", "rostberattigade"]:
                w.writerow(["rd", kod, p, ""])
    print(f"Mall skriven: {path} (rader som börjar med # ignoreras)")


def las_bas(path):
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text("utf-8"))


def bygg(ar, distrikt, status, jamforelser, tid, kalla):
    mandat = {"metod": METOD.format(ar=ar)}
    rd = [d for d in distrikt.values() if d.get("rd")]
    if rd:
        roster = {}
        for d in rd:
            for p, n in d["rd"].items():
                roster[p] = roster.get(p, 0) + n
        mandat["riksdag_majorna"] = jamkade_uddatal(roster, 349)
        mandat["riksdag_verklig"] = {}
    return schema.bygg_valdata(ar, list(distrikt.values()), status, jamforelser, mandat, uppdaterad=tid, kalla=kalla)


def repetera(ut_bas):
    filer = {}
    for val, monster in RAFIL_MONSTER.items():
        traffar = sorted(glob.glob(str(ROT / monster)))
        if not traffar:
            fel(f"hittar ingen råfil för {val} ({monster}) i {ROT}")
        filer[val] = traffar[0]
    bas = las_bas(ut_bas)
    if bas is None:
        fel(f"{ut_bas} saknas, kör scripts/bygg_data.py först")
    distrikt = tomma_distrikt(bas)
    jamforelser = las_rafiler(filer, distrikt, bas)
    v = bygg(2022, distrikt, "slutlig", jamforelser, bas["meta"]["uppdaterad"], bas["meta"]["kalla"])
    diffar = []
    for d, b in zip(v["distrikt"], bas["distrikt"]):
        for val in VAL:
            if d[val] != b[val]:
                diffar.append(f"{d['kod']} {val}: {d[val]} != {b[val]}")
            for f in ("giltiga", "rostande", "rostberattigade"):
                if d[f].get(val) != b[f].get(val):
                    diffar.append(f"{d['kod']} {val} {f}: {d[f].get(val)} != {b[f].get(val)}")
    if v["aggregat"]["majorna"] != bas["aggregat"]["majorna"]:
        diffar.append("aggregat.majorna skiljer sig")
    if v["mandat"]["riksdag_majorna"] != bas["mandat"]["riksdag_majorna"]:
        diffar.append(f"mandat: {v['mandat']['riksdag_majorna']} != {bas['mandat']['riksdag_majorna']}")
    for omrade in ("goteborg", "riket"):
        for val, post in bas["aggregat"][omrade].items():
            ny = v["aggregat"][omrade].get(val)
            if ny is None:
                diffar.append(f"aggregat.{omrade}.{val} saknas")
                continue
            for p, andel in post["andel"].items():
                if abs(ny["andel"].get(p, -1) - andel) > 1e-9:
                    diffar.append(f"aggregat.{omrade}.{val}.{p}: {ny['andel'].get(p)} != {andel}")
            tol = 5e-5 if omrade == "goteborg" else 1e-9
            if abs(ny["valdeltagande"] - post["valdeltagande"]) > tol:
                diffar.append(f"aggregat.{omrade}.{val}.valdeltagande: {ny['valdeltagande']} != {post['valdeltagande']}")
    for rad in diffar:
        print("DIFF " + rad)
    if diffar:
        print(f"REPETITION MISSLYCKADES: {len(diffar)} diffar mot {ut_bas}")
        return 1
    print(f"REPETITION OK: 2022 års råfiler ger exakt samma valdata som {Path(ut_bas).name} "
          f"(23 distrikt, 3 val, aggregat, mandat). Varningar: {len(VARNINGAR)}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for val in VAL:
        ap.add_argument(f"--{val}", help=f"Valmyndighetens råfil för {VAL[val].lower()}valet (blad roster_{val.upper()})")
    ap.add_argument("--csv", help="reservväg: manuellt ifylld CSV (val;kod;parti;roster)")
    ap.add_argument("--skriv-mall", metavar="FIL", help="skriv en tom CSV-mall och avsluta")
    ap.add_argument("--ar", type=int, default=2026)
    ap.add_argument("--status", choices=["preliminar", "slutlig"], default="preliminar")
    ap.add_argument("--tid", help="tidsstämpel ISO 8601, t.ex. 2026-09-13T21:30:00 (standard: nu)")
    ap.add_argument("--ut", default=ROT / "data")
    ap.add_argument("--bas", default=ROT / "data" / "valdata_2022.json", help="basår för swing")
    ap.add_argument("--repetera", action="store_true", help="kör 2022 års råfiler och jämför med --bas")
    ap.add_argument("--valnatt", action="store_true",
                    help="uppdatera data/konfig: lägg till året, gör det till standard och slå på valnattsläget")
    a = ap.parse_args()

    if a.skriv_mall:
        skriv_mall(a.skriv_mall)
        return 0
    if a.repetera:
        return repetera(a.bas)
    filer = {val: getattr(a, val) for val in VAL if getattr(a, val)}
    if not filer and not a.csv:
        ap.error("ange minst en av --rd, --rf, --kf eller --csv (eller --repetera / --skriv-mall)")
    bas = las_bas(a.bas)
    if bas is None:
        varning(f"{a.bas} saknas: ingen swing beräknas och distriktsnamnen tas ur filen")
    distrikt = tomma_distrikt(bas)
    jamforelser = {"goteborg": {}, "riket": {}}
    try:
        if filer:
            jamforelser = las_rafiler(filer, distrikt, bas)
        if a.csv:
            print(f"Läser CSV: {a.csv}")
            las_csv(a.csv, distrikt)
    except FormatFel as ex:
        fel(str(ex))
    kalla = f"Valmyndigheten, {'preliminär' if a.status == 'preliminar' else 'slutlig'} rösträkning per valdistrikt {a.ar}"
    v = bygg(a.ar, distrikt, a.status, jamforelser, a.tid, kalla)
    ut = Path(a.ut)
    filer_ut = list(schema.skriv(ut / f"valdata_{a.ar}", v))
    if a.valnatt:
        konfig = schema.las_konfig(ut)
        konfig["ar"] = sorted(set(konfig.get("ar", [])) | {str(a.ar)})
        konfig["standardAr"] = str(a.ar)
        konfig["valnatt"] = True
        filer_ut += list(schema.skriv_konfig(ut, konfig))
    if bas:
        filer_ut += list(schema.skriv(ut / f"swing_{a.ar}", schema.swing(v, bas)))
    raknade = {val: sum(1 for d in v["distrikt"] if d[val]) for val in VAL}
    print("Räknade distrikt: " + ", ".join(f"{VAL[val]} {n}/23" for val, n in raknade.items()))
    for f in filer_ut:
        print(f"    {f.stat().st_size / 1024:6.1f} kB  {f}")
    print(f"{len(VARNINGAR)} varningar. Status: {a.status}. Uppdaterad: {v['meta']['uppdaterad']}")
    if a.valnatt:
        print(f"Konfigen uppdaterad: ar {konfig['ar']}, standardAr {a.ar}, valnatt på. Ladda upp data/ (valdata, swing och konfig).")
    else:
        print(f"Nästa steg: kör med --valnatt för att slå på valnattsläget i data/konfig.js, eller redigera filen för hand. Ladda sedan upp data/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
