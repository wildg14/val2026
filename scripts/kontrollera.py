#!/usr/bin/env python3
"""Stämmer av data/valdata_<år>.json mot den kurerade xlsx:en.

    python scripts/kontrollera.py data/valdata_2022.json majorna-valresultat-2022.xlsx
    python scripts/kontrollera.py data/valdata_2022.json majorna-valresultat-2022.xlsx --historik data/historik.json

Skriver en rad per diff och avslutar med kod 1 vid minsta avvikelse. Kontrollerar även att
.js-filen bredvid JSON-filen innehåller identisk data. Med --historik kontrolleras även att
historik.json:s majorna-rad för valdatas år stämmer med valdatas aggregat, för alla tre valen.
"""
import argparse
import json
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))

from scripts import schema  # noqa: E402
from scripts.valmyndigheten import VAL, las_kurerad  # noqa: E402


def kontrollera(valdata_path, xlsx_path):
    diffar, antal = [], 0
    v = json.loads(Path(valdata_path).read_text("utf-8"))
    k = las_kurerad(xlsx_path)

    def jamfor(etikett, a, b, tol=0):
        nonlocal antal
        antal += 1
        if tol and isinstance(a, (int, float)) and isinstance(b, (int, float)):
            lika = abs(a - b) <= tol
        else:
            lika = a == b
        if not lika:
            diffar.append(f"DIFF {etikett} json={a} xlsx={b}")

    jamfor("antal distrikt", len(v["distrikt"]), len(k["distrikt"]))
    jamfor("distriktskoder", sorted(d["kod"] for d in v["distrikt"]), sorted(k["distrikt"]))
    for d in v["distrikt"]:
        kd = k["distrikt"].get(d["kod"])
        if kd is None:
            continue
        jamfor(f"{d['kod']} namn", d["namn"], kd["namn"])
        for val in VAL:
            for p in sorted(set(d[val]) | set(kd[val])):
                jamfor(f"{d['kod']} {val} {p}", d[val].get(p), kd[val].get(p))
            for f in ("giltiga", "rostande", "rostberattigade"):
                jamfor(f"{d['kod']} {val} {f}", d[f].get(val), kd[f].get(val))
            jamfor(f"{d['kod']} {val} partisumma=giltiga", sum(d[val].values()), d["giltiga"].get(val))
    for val in VAL:
        m = v["aggregat"]["majorna"][val]
        t = k["total"][val]
        for p in sorted(set(m["roster"]) | set(t["roster"])):
            jamfor(f"majorna {val} {p}", m["roster"].get(p), t["roster"].get(p))
        for f in ("giltiga", "rostande", "rostberattigade"):
            jamfor(f"majorna {val} {f}", m[f], t[f])
        for p in t["roster"]:
            jamfor(f"kolumnsumma {val} {p}", sum(d[val].get(p, 0) for d in v["distrikt"]), t["roster"][p])
        s = k["sammanfattning"]["majorna"][val]
        for p, n in s["roster"].items():
            jamfor(f"sammanfattning {val} {p}", m["roster"].get(p), n)
        jamfor(f"sammanfattning {val} giltiga", m["giltiga"], s["giltiga"])
        jamfor(f"sammanfattning {val} valdeltagande", m["rostande"] / m["rostberattigade"], s["valdeltagande"], tol=1e-9)
    js = Path(valdata_path).with_suffix(".js")
    if js.exists():
        jamfor("js-filen identisk med json-filen", schema.las_js(js) == v, True)
    return diffar, antal


def kontrollera_historik(valdata_path, historik_path):
    """historik.json, nivå majorna, valdatas år -> samma röster och summor som valdata_<år>.json. Returnerar (diffar, antal).

    En historikfil som saknas, har trasig JSON eller saknar serie- eller meta-nyckeln ger en enda
    diff-rad i stället för en traceback - kontrollskriptet ska rapportera fel, inte krascha."""
    v = json.loads(Path(valdata_path).read_text("utf-8"))
    ar = v["meta"]["ar"]
    try:
        hst = json.loads(Path(historik_path).read_text("utf-8"))
        serie = hst["serie"]
        hst["meta"]
    except (OSError, ValueError, KeyError) as e:
        return [f"DIFF historik: {historik_path} saknas eller går inte att läsa: {e}"], 1
    diffar, antal = [], 0
    for val in VAL:
        agg = v["aggregat"]["majorna"][val]
        rad = next((p for p in serie[val]["majorna"] if p["ar"] == ar), None)
        if rad is None:
            antal += len(agg["roster"]) + 3
            diffar.append(f"DIFF historik {val}: år {ar} saknas i serien")
            continue
        for p in sorted(set(agg["roster"]) | set(rad["roster"])):
            antal += 1
            if rad["roster"].get(p) != agg["roster"].get(p):
                diffar.append(f"DIFF historik {val} {p} serie={rad['roster'].get(p)} valdata={agg['roster'].get(p)}")
        for f in ("giltiga", "rostande", "rostberattigade"):
            antal += 1
            if rad.get(f) != agg[f]:
                diffar.append(f"DIFF historik {val} {f} serie={rad.get(f)} valdata={agg[f]}")
    return diffar, antal


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("valdata", nargs="?", default=ROT / "data" / "valdata_2022.json")
    ap.add_argument("xlsx", nargs="?", default=ROT / "majorna-valresultat-2022.xlsx")
    ap.add_argument("--historik", help="historik.json: kontrollera att områdesserien stämmer med valdata")
    a = ap.parse_args(argv[1:])

    diffar, antal = kontrollera(a.valdata, a.xlsx)
    for rad in diffar:
        print(rad)

    historik_diffar, historik_antal = [], 0
    if a.historik:
        historik_diffar, historik_antal = kontrollera_historik(a.valdata, a.historik)
        for rad in historik_diffar:
            print(rad)

    alla_diffar = diffar + historik_diffar
    if alla_diffar:
        print(f"FEL: {len(alla_diffar)} diffar av {antal + historik_antal} kontroller. Bygget stoppas.")
        return 1
    svans = f" plus {historik_antal} historikkontroller" if a.historik else ""
    print(f"OK: {antal} kontroller, 0 diffar ({Path(a.valdata).name} mot {Path(a.xlsx).name}){svans}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
