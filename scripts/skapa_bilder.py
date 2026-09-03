#!/usr/bin/env python3
"""Skapar stillbilder ur sidans bildläge med Chrome headless, för nyhetsbrevet och sociala medier.

    .venv/bin/python scripts/skapa_bilder.py [--ut bilder] [--ar 2022] [--etikett "Majposten · Valet 2026"] [--skala 2]

Renderar index.html?bild=jamforelse ("Majorna mot Sverige") och index.html?bild=karta (kartteaser) i två format per val:
  1200 x 630   Facebook, og:image, Beehiiv-thumbnail och länkförhandsvisning
  1080 x 1080  Instagram och själva brevet (värdena läsbara i 360 px bredd)
Filnamnet bär de logiska måtten; med --skala 2 (standard) blir pixelmåtten dubbla (2400 x 1260 och 2160 x 2160).
Bredvid varje PNG skrivs en .txt med alt-texten, räknad ur data/valdata_<år>.json med samma formel som sidan.
Kräver Google Chrome (macOS-sökväg som standard, annars --chrome). Ingen server behövs: sidan öppnas via file://.
Jämförelsen kräver att valdata_<år>.json har aggregat för riket, Västra Götaland och Göteborg (finns när
uppdatera_2026.py körts med Valmyndighetens filer, inte med CSV-reservvägen).
"""
import argparse
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
CHROME_STANDARD = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OMRADE = {"rd": "sverige", "rf": "vastra-gotaland", "kf": "goteborg"}
VALNAMN = {"rd": "riksdagsvalet", "rf": "regionvalet", "kf": "kommunvalet"}
FORMAT = {"liggande": (1200, 630), "kvadrat": (1080, 1080)}
ETIKETT_STANDARD = "Majposten · Inför valet"


def alttext(json_path, val):
    """Alt-text för bilden, samma tal och ordning som sidans divergens()."""
    v = json.loads(Path(json_path).read_text("utf-8"))
    m = v["aggregat"]["majorna"].get(val)
    if val == "kf":
        omr, namn = v["aggregat"]["goteborg"].get(val), "Göteborg"
    else:
        omr = v["aggregat"]["riket"].get(val)
        namn = (omr or {}).get("namn") or "Sverige"
        namn = "Sverige" if namn == "Riket" else namn
    if not m or not m.get("giltiga") or not omr or not omr.get("andel"):
        raise ValueError(f"{Path(json_path).name}: jämförelsedata för {val} saknas (aggregat för {namn}). "
                         "Bilden kan skapas när valdata byggts ur Valmyndighetens filer, inte ur CSV-reservvägen.")
    rader = sorted(((p, (m["roster"][p] / m["giltiga"] - omr["andel"][p]) * 100)
                    for p in m["roster"] if p != "Övriga" and p in omr["andel"]), key=lambda r: -r[1])
    tal = ", ".join(f"{p} {d:+.1f}".replace(".", ",") for p, d in rader)
    return f"Majorna mot {namn}, {VALNAMN[val]} {v['meta']['ar']}, skillnad i procentenheter: {tal}."


def alttext_karta(json_path, val):
    """Alt-text för kartteasern: största parti per distrikt, räknat ur datafilen."""
    v = json.loads(Path(json_path).read_text("utf-8"))
    namn, antal = v["meta"].get("partier", {}), {}
    for d in v["distrikt"]:
        if not d.get("raknat", True) or not d.get(val):
            continue
        p = max((q for q in d[val] if q != "Övriga"), key=lambda q: d[val][q])
        antal[p] = antal.get(p, 0) + 1
    if not antal:
        raise ValueError(f"{Path(json_path).name}: inga räknade distrikt för {val}")
    delar = ", ".join(f"{namn.get(q, q)} i {n}" for q, n in sorted(antal.items(), key=lambda x: (-x[1], x[0])))
    return f"Karta över Majornas {len(v['distrikt'])} valdistrikt, största parti i {VALNAMN[val]} {v['meta']['ar']}: {delar}."


def rendera(chrome, url, bredd, hojd, skala, ut):
    kommando = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                "--virtual-time-budget=5000", f"--force-device-scale-factor={skala}",
                f"--window-size={bredd},{hojd}", f"--screenshot={ut}", url]
    r = subprocess.run(kommando, capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not Path(ut).exists():
        raise RuntimeError(f"Chrome misslyckades ({r.returncode}): {r.stderr.strip()[-400:]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ut", default=ROT / "bilder")
    ap.add_argument("--ar", default="2022")
    ap.add_argument("--val", nargs="+", default=list(OMRADE), choices=list(OMRADE))
    ap.add_argument("--format", nargs="+", default=list(FORMAT), choices=list(FORMAT))
    ap.add_argument("--typ", nargs="+", default=["jamforelse", "karta"], choices=["jamforelse", "karta"])
    ap.add_argument("--etikett", default=ETIKETT_STANDARD, help="texten ovanför rubriken")
    ap.add_argument("--skala", type=int, default=2, help="pixlar per CSS-pixel (2 ger skarpa bilder på mobil)")
    ap.add_argument("--chrome", default=CHROME_STANDARD)
    ap.add_argument("--html", default=ROT / "index.html")
    ap.add_argument("--data", default=None, help="valdata-fil för alt-text (standard data/valdata_<år>.json)")
    a = ap.parse_args()
    if not Path(a.chrome).exists():
        print(f"FEL: hittar inte Chrome på {a.chrome} (ange --chrome)", file=sys.stderr)
        return 1
    data = Path(a.data) if a.data else ROT / "data" / f"valdata_{a.ar}.json"
    try:
        alt = {(typ, val): (alttext if typ == "jamforelse" else alttext_karta)(data, val) for typ in a.typ for val in a.val}
    except (ValueError, KeyError, FileNotFoundError) as ex:
        print(f"FEL: {ex}", file=sys.stderr)
        return 1
    ut = Path(a.ut)
    ut.mkdir(parents=True, exist_ok=True)
    for typ in a.typ:
        for val in a.val:
            for fmt in a.format:
                bredd, hojd = FORMAT[fmt]
                q = {"bild": typ, "val": val, "format": fmt, "ar": a.ar, "etikett": a.etikett}
                url = Path(a.html).resolve().as_uri() + "?" + urllib.parse.urlencode(q)
                namn = f"majorna-mot-{OMRADE[val]}" if typ == "jamforelse" else "majorna-karta"
                stam = ut / f"{namn}-{val}-{a.ar}-{bredd}x{hojd}"
                rendera(a.chrome, url, bredd, hojd, a.skala, stam.with_suffix(".png"))
                stam.with_suffix(".txt").write_text(alt[(typ, val)] + "\n", "utf-8")
                print(f"    {stam.with_suffix('.png').stat().st_size / 1024:6.1f} kB  {stam.with_suffix('.png')}")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
