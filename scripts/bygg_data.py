#!/usr/bin/env python3
"""Bygger data/ för 2022 ur källfilerna i projektmappen.

    .venv/bin/python scripts/bygg_data.py [--ut data] [--utan-rafiler]

Steg: (1) läser majorna-valresultat-2022.xlsx och kontrollerar rad- och kolumnsummor mot
totalraden och fliken Sammanfattning, (2) läser riksdagens verkliga mandat och räknar
"Om Majorna bestämde", (3) läser valgeografin och kontrollerar att alla 23 distrikt finns,
(4) stämmer av mot Valmyndighetens rådatafiler om de finns (generalrepetition för 2026),
(5) skriver data/valdata_2022.json/.js och data/distrikt_2022.geojson/.js,
(6) kör kontrollera.py, (7) skriver ut filstorlekar.
Avbryter vid minsta diff.
"""
import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

import openpyxl

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))

from scripts import geo, schema  # noqa: E402
from scripts.mandat import jamkade_uddatal  # noqa: E402
from scripts.valmyndigheten import (MAJORNA_KODER, VAL, aggregat_andelar, las_kurerad,  # noqa: E402
                                    las_rafil, partikod, till_distrikt)

RAFIL_MONSTER = {"rd": "*oster-per-distrikt*riksdagsval*.xlsx", "rf": "*oster-per-distrikt*regionval*.xlsx",
                 "kf": "*oster-per-distrikt*kommunval*.xlsx"}
METOD = ("Räkneexempel: 4 %-spärr och jämkade uddatalsmetoden tillämpade på Majornas "
         "riksdagsröster {ar}.")


def fel(text):
    print(f"FEL: {text}")
    sys.exit(1)


def steg(n, text):
    print(f"[{n}] {text}")


def las_mandat(path):
    """Fliken Riksdag i Mandatfordelning-filen: parti -> mandat 2022."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rader = list(wb["Riksdag"].iter_rows(values_only=True))
    finally:
        wb.close()
    huvud = list(rader[0])
    if 2022 not in huvud:
        fel(f"{path}: hittar ingen kolumn 2022 i fliken Riksdag")
    kol = huvud.index(2022)
    total, mandat = None, {}
    for r in rader[1:]:
        if r[0] == "Sverige":
            total = int(r[kol])
        elif partikod(r[0]) and r[kol]:
            mandat[partikod(r[0])] = int(r[kol])
    if total is None or sum(mandat.values()) != total:
        fel(f"{path}: mandaten summerar till {sum(mandat.values())}, inte {total}")
    return mandat


def kontrollera_kurerad(k):
    for kod, d in k["distrikt"].items():
        for val in VAL:
            if sum(d[val].values()) != d["giltiga"][val]:
                fel(f"{kod} {val}: partiröster {sum(d[val].values())} != giltiga {d['giltiga'][val]}")
    for val in VAL:
        t = k["total"][val]
        for p, n in t["roster"].items():
            s = sum(d[val][p] for d in k["distrikt"].values())
            if s != n:
                fel(f"kolumnsumma {val} {p}: {s} != totalraden {n}")
        for f in ("giltiga", "rostande", "rostberattigade"):
            s = sum(d[f][val] for d in k["distrikt"].values())
            if s != t[f]:
                fel(f"kolumnsumma {val} {f}: {s} != totalraden {t[f]}")
        s = k["sammanfattning"]["majorna"][val]
        for p, n in s["roster"].items():
            if t["roster"].get(p) != n:
                fel(f"Sammanfattning {val} {p}: {n} != totalraden {t['roster'].get(p)}")
        if s["giltiga"] != t["giltiga"]:
            fel(f"Sammanfattning {val} giltiga: {s['giltiga']} != totalraden {t['giltiga']}")


def kontrollera_mot_rafiler(k, mapp):
    hittade = 0
    for val, monster in RAFIL_MONSTER.items():
        traffar = sorted(glob.glob(str(Path(mapp) / monster)))
        if not traffar:
            print(f"    {val}: ingen råfil hittad ({monster}), hoppar över")
            continue
        hittade += 1
        ra = las_rafil(traffar[0], MAJORNA_KODER)
        if ra["val"] != val:
            fel(f"{traffar[0]}: bladet gäller {ra['val']}, inte {val}")
        for kod, post in ra["distrikt"].items():
            d = till_distrikt(post, val)
            kd = k["distrikt"][kod]
            if d["roster"] != kd[val]:
                fel(f"råfil {val} {kod}: {d['roster']} != xlsx {kd[val]}")
            for f in ("giltiga", "rostande", "rostberattigade"):
                if d[f] != kd[f][val]:
                    fel(f"råfil {val} {kod} {f}: {d[f]} != xlsx {kd[f][val]}")
        agg = aggregat_andelar(ra)
        s = k["sammanfattning"]
        for omrade in ("goteborg", "riket"):
            if val not in s[omrade]:
                continue
            for p, andel in s[omrade][val]["andel"].items():
                if abs(agg[omrade]["andel"].get(p, -1) - andel) > 1e-9:
                    fel(f"råfil {val} {omrade} {p}: {agg[omrade]['andel'].get(p)} != Sammanfattning {andel}")
            tol = 5e-5 if omrade == "goteborg" else 1e-9
            if abs(agg[omrade]["valdeltagande"] - s[omrade][val]["valdeltagande"]) > tol:
                fel(f"råfil {val} {omrade} valdeltagande: {agg[omrade]['valdeltagande']} != {s[omrade][val]['valdeltagande']}")
        print(f"    {val}: {Path(traffar[0]).name}: 23 distrikt och jämförelseaggregat stämmer exakt")
    return hittade


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", default=ROT / "majorna-valresultat-2022.xlsx")
    ap.add_argument("--zip", default=ROT / "valdistrikt-vastra-gotalands-lan.zip")
    ap.add_argument("--mandat", default=ROT / "Mandatfordelning-jamforelser-mellan-2018-och-2022.xlsx")
    ap.add_argument("--ut", default=ROT / "data")
    ap.add_argument("--rafiler", default=ROT, help="mapp med Valmyndighetens råfiler (steg 4)")
    ap.add_argument("--utan-rafiler", action="store_true", help="hoppa över steg 4")
    ap.add_argument("--ar", type=int, default=2022)
    a = ap.parse_args()

    steg(1, f"Läser {Path(a.xlsx).name}")
    k = las_kurerad(a.xlsx)
    if sorted(k["distrikt"]) != MAJORNA_KODER:
        fel(f"xlsx innehåller inte exakt de 23 distrikten: {sorted(k['distrikt'])}")
    kontrollera_kurerad(k)
    print("    23 distrikt, radsummor, kolumnsummor och Sammanfattning stämmer")

    steg(2, "Mandat")
    verklig = las_mandat(a.mandat)
    majorna = jamkade_uddatal(k["total"]["rd"]["roster"], 349)
    print(f"    Riksdagen {a.ar}: {verklig}")
    print(f"    Om Majorna bestämde: {majorna}")

    steg(3, f"Geodata ur {Path(a.zip).name}")
    fc = geo.las_distrikt(a.zip, MAJORNA_KODER)
    namn_geo = {f["properties"]["kod"]: f["properties"]["namn"] for f in fc["features"]}
    namn_xlsx = {kod: d["namn"] for kod, d in k["distrikt"].items()}
    if namn_geo != namn_xlsx:
        skillnad = {kod: (namn_geo.get(kod), namn_xlsx.get(kod)) for kod in MAJORNA_KODER if namn_geo.get(kod) != namn_xlsx.get(kod)}
        fel(f"distriktsnamn skiljer sig mellan geodata och xlsx: {skillnad}")
    print(f"    {len(fc['features'])} polygoner, namnen matchar xlsx, bbox {fc['bbox']}")

    steg(4, "Kontroll mot Valmyndighetens råfiler")
    if a.utan_rafiler:
        print("    hoppas över (--utan-rafiler)")
    elif not kontrollera_mot_rafiler(k, a.rafiler):
        print("    inga råfiler hittades, hoppar över")

    steg(5, "Skriver filer")
    distrikt = []
    for kod in MAJORNA_KODER:
        d = k["distrikt"][kod]
        distrikt.append({"kod": kod, "namn": d["namn"], "raknat": True, **{val: d[val] for val in VAL},
                         "giltiga": d["giltiga"], "rostande": d["rostande"], "rostberattigade": d["rostberattigade"]})
    jamforelser = {"goteborg": k["sammanfattning"]["goteborg"], "riket": k["sammanfattning"]["riket"]}
    mandat = {"riksdag_verklig": verklig, "riksdag_majorna": majorna, "metod": METOD.format(ar=a.ar)}
    v = schema.bygg_valdata(a.ar, distrikt, "slutlig", jamforelser, mandat,
                            kalla=f"Valmyndigheten, slutlig rösträkning per valdistrikt {a.ar}")
    ut = Path(a.ut)
    filer = list(schema.skriv(ut / f"valdata_{a.ar}", v))
    filer += list(schema.skriv(ut / "distrikt_2022", fc, json_suffix=".geojson"))
    if not (ut / "konfig.json").exists():   # redaktörens ändringar skrivs aldrig över
        filer += list(schema.skriv_konfig(ut, schema.KONFIG_STANDARD))
        print("    data/konfig.json saknades: standardkonfig skriven (ar 2022, valnatt av)")
    for f in filer:
        print(f"    {f.relative_to(ROT) if f.is_relative_to(ROT) else f}")

    steg(6, "Kontrollskript")
    r = subprocess.run([sys.executable, str(ROT / "scripts" / "kontrollera.py"), str(ut / f"valdata_{a.ar}.json"),
                        str(a.xlsx)], capture_output=True, text=True)
    print("    " + (r.stdout.strip() + "\n" + r.stderr.strip()).strip().replace("\n", "\n    "))
    if r.returncode != 0:
        fel("kontrollera.py rapporterar diffar")

    steg(7, "Sidvikt (html + js-data)")
    konfig = schema.las_konfig(ut)
    filer_sidvikt = [ROT / "index.html", ut / "konfig.js", ut / "bakgrund.js"]
    for ar_konfig in konfig["ar"]:
        filer_sidvikt += [ut / f"distrikt_{ar_konfig}.js", ut / f"valdata_{ar_konfig}.js", ut / f"swing_{ar_konfig}.js"]
    total = 0
    for f in filer_sidvikt:
        if f.exists():
            total += f.stat().st_size
            print(f"    {f.stat().st_size / 1024:7.1f} kB  {f.name}")
    print(f"    {total / 1024:7.1f} kB  totalt")
    print("OK")


if __name__ == "__main__":
    main()
