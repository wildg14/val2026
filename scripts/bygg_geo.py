#!/usr/bin/env python3
"""Skriver data/distrikt_<år>.geojson och .js ur Valmyndighetens valgeografi för ett år.

    .venv/bin/python scripts/bygg_geo.py --ar 2026
    .venv/bin/python scripts/bygg_geo.py --ar 2022

Standardsökvägar: 2022 valdistrikt-vastra-gotalands-lan.zip i projektroten, 2026 länets zip under
Historiska dokument/dl_webb/2026/. Skriver ut antal distrikt och unionsytan, och jämför ytan med
data/distrikt_2022.geojson när ett annat år byggs (samma yta är villkoret för att områdesnivån ska
kunna jämföras rakt av mellan åren).
"""
import argparse
import json
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))

from scripts import geo, schema  # noqa: E402
from scripts.valmyndigheten import MAJORNA_KODER  # noqa: E402

ZIP = {"2022": ROT / "valdistrikt-vastra-gotalands-lan.zip",
       "2026": ROT / "Historiska dokument" / "dl_webb" / "2026" / "valdistrikt-vastra-gotaland-lan-2026.zip"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ar", required=True)
    ap.add_argument("--zip", default=None)
    ap.add_argument("--ut", default=ROT / "data")
    ap.add_argument("--jamfor", default=None, help="geojson att jämföra ytan med (standard data/distrikt_2022.geojson)")
    a = ap.parse_args()
    zip_path = Path(a.zip or ZIP.get(a.ar, ""))
    if not zip_path.exists():
        print(f"FEL: hittar inte {zip_path} (ange --zip)", file=sys.stderr)
        return 1
    fc = geo.las_distrikt(zip_path, MAJORNA_KODER)
    yta = sum(f["properties"]["area_km2"] for f in fc["features"])
    print(f"{a.ar}: {len(fc['features'])} distrikt, unionsyta {yta:.4f} km², bbox {fc['bbox']}")
    jamfor = Path(a.jamfor) if a.jamfor else (Path(a.ut) / "distrikt_2022.geojson" if a.ar != "2022" else None)
    if jamfor and jamfor.exists():
        andra = json.loads(jamfor.read_text("utf-8"))
        yta2 = sum(f["properties"]["area_km2"] for f in andra["features"])
        skillnad = (yta - yta2) * 1e6
        print(f"Skillnad i yta mot {jamfor.name}: {skillnad:+.0f} kvadratmeter")
        if abs(skillnad) > 1000:
            print("VARNING: ytan skiljer sig mer än 1 000 kvadratmeter; områdesnivån är då inte rakt jämförbar", file=sys.stderr)
    for f in schema.skriv(Path(a.ut) / f"distrikt_{a.ar}", fc, json_suffix=".geojson"):
        print(f"    {f.stat().st_size / 1024:6.1f} kB  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
