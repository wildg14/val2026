#!/usr/bin/env python3
"""Stämmer av data/valdata_<år>.json mot den kurerade xlsx:en.

    python scripts/kontrollera.py data/valdata_2022.json majorna-valresultat-2022.xlsx

Skriver en rad per diff och avslutar med kod 1 vid minsta avvikelse. Kontrollerar även att
.js-filen bredvid JSON-filen innehåller identisk data.
"""
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


def main(argv):
    valdata = argv[1] if len(argv) > 1 else ROT / "data" / "valdata_2022.json"
    xlsx = argv[2] if len(argv) > 2 else ROT / "majorna-valresultat-2022.xlsx"
    diffar, antal = kontrollera(valdata, xlsx)
    for rad in diffar:
        print(rad)
    if diffar:
        print(f"FEL: {len(diffar)} diffar av {antal} kontroller. Bygget stoppas.")
        return 1
    print(f"OK: {antal} kontroller, 0 diffar ({Path(valdata).name} mot {Path(xlsx).name})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
