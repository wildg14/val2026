#!/usr/bin/env python3
"""Skriver data/distrikt_<år>.geojson och .js ur Valmyndighetens valgeografi för ett år.

    .venv/bin/python scripts/bygg_geo.py --ar 2026
    .venv/bin/python scripts/bygg_geo.py --ar 2022

Standardsökvägar: 2022 valdistrikt-vastra-gotalands-lan.zip i projektroten, 2026 länets zip under
Historiska dokument/dl_webb/2026/. Skriver ut antal distrikt och unionsytan (av den faktiska
geometrin, inte summan av avrundade area_km2), och jämför unionen geometriskt med
data/distrikt_2022.geojson när ett annat år byggs: symmetrisk differens är arean som skiljer mellan
unionerna, dvs luckor och överlapp - villkoret för att områdesnivån ska kunna jämföras rakt av mellan
åren är att den är liten.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))

from scripts import geo, schema  # noqa: E402
from scripts.valmyndigheten import MAJORNA_KODER  # noqa: E402

ZIP = {"2022": ROT / "valdistrikt-vastra-gotalands-lan.zip",
       "2026": ROT / "Historiska dokument" / "dl_webb" / "2026" / "valdistrikt-vastra-gotaland-lan-2026.zip"}

SYMDIFF_TROSKEL = 10  # kvadratmeter


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ar", required=True)
    ap.add_argument("--zip", default=None)
    ap.add_argument("--ut", default=ROT / "data")
    ap.add_argument("--jamfor", default=None, help="geojson att jämföra ytan med (standard data/distrikt_2022.geojson)")
    a = ap.parse_args()

    if not re.fullmatch(r"\d{4}", a.ar):
        print(f"FEL: --ar ska vara fyra siffror, fick {a.ar!r}", file=sys.stderr)
        return 1
    # Sökvägarna kontrolleras med is_file() (en katalog och en tom sträng finns men går inte att läsa)
    # och båda före inläsningen, som tar en stund: felet ska komma direkt.
    zip_path = Path(a.zip) if a.zip is not None else ZIP.get(a.ar)
    if zip_path is None or not zip_path.is_file():
        print(f"FEL: hittar ingen zip för {a.ar} (ange --zip)", file=sys.stderr)
        return 1

    if a.jamfor is not None:
        jamfor = Path(a.jamfor)
        if not jamfor.is_file():
            print(f"FEL: hittar inte jämförelsefilen {a.jamfor}", file=sys.stderr)
            return 1
    elif a.ar == "2022":
        jamfor = None
    else:
        jamfor = Path(a.ut) / "distrikt_2022.geojson"
        if not jamfor.is_file():
            print(f"Ingen ytjämförelse: {jamfor} saknas")
            jamfor = None

    fc = geo.las_distrikt(zip_path, MAJORNA_KODER)
    yta = geo.union_yta(fc)
    print(f"{a.ar}: {len(fc['features'])} distrikt, unionsyta {yta:.0f} kvadratmeter, bbox {fc['bbox']}")

    if jamfor is not None:
        andra = json.loads(jamfor.read_text("utf-8"))
        resultat = geo.jamfor_union(andra, fc)
        print(f"Mot {jamfor.name}: skillnad {resultat['skillnad']:+.0f} kvadratmeter, "
              f"symmetrisk differens {resultat['symmetrisk_differens']:.0f} kvadratmeter")
        if resultat["symmetrisk_differens"] > SYMDIFF_TROSKEL:
            print(f"VARNING: symmetrisk differens över {SYMDIFF_TROSKEL} kvadratmeter; "
                  "områdesnivån är då inte rakt jämförbar", file=sys.stderr)

    for f in schema.skriv(Path(a.ut) / f"distrikt_{a.ar}", fc, json_suffix=".geojson"):
        print(f"    {f.stat().st_size / 1024:6.1f} kB  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
