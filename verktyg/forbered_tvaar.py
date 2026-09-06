#!/usr/bin/env python3
"""Bygger tmp/tvaar/ med två år (2022 ur data/, 2026 ur en valnattskörning) för verktyg/tvaar-check.js.

    .venv/bin/python verktyg/forbered_tvaar.py --valnatt-data /tmp/valnatt-test/data

Mappen /tmp/valnatt-test/data skrivs av uppdatera_2026.py (se plan, Task 6 steg 5). Testsidan nås som
http://localhost:8765/tmp/tvaar/index.html när servern kör i projektroten.
"""
import argparse
import shutil
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))
from scripts import schema  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--valnatt-data", required=True, help="mapp med valdata_2026.js och swing_2026.js")
    ap.add_argument("--ut", default=ROT / "tmp" / "tvaar")
    ap.add_argument("--valnatt", action="store_true", help="slå på valnattsläget i testsidans konfig")
    a = ap.parse_args()
    ut = Path(a.ut).resolve()   # relativ --ut ska fungera, sökvägen skrivs ut mot projektroten
    if ut.exists():
        shutil.rmtree(ut)
    (ut / "data").mkdir(parents=True)
    for namn in ("index.html", "valgrafik.js", "valgrafik.css"):
        shutil.copy(ROT / namn, ut / namn)
    for namn in ("bakgrund.js", "distrikt_2022.js", "valdata_2022.js", "distrikt_2026.js"):
        shutil.copy(ROT / "data" / namn, ut / "data" / namn)
    for namn in ("valdata_2026.js", "swing_2026.js"):
        shutil.copy(Path(a.valnatt_data) / namn, ut / "data" / namn)
    konfig = schema.las_konfig(ROT / "data")
    konfig.update({"ar": ["2022", "2026"], "standardAr": "2026", "valnatt": bool(a.valnatt)})
    schema.skriv_konfig(ut / "data", konfig)
    if ut.is_relative_to(ROT):
        print(f"Testsida: http://localhost:8765/{ut.relative_to(ROT)}/index.html")
    else:
        print(f"Testsida: {ut / 'index.html'} (utanför projektroten, servern i roten når den inte)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
