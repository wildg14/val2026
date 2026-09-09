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
import re
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


def datamapp(html):
    """data/ hör till den sida som fotograferas, inte till repot. Pekar --html på en kopia läser
    alt-texten annars helt andra siffror än bilden visar."""
    return Path(html).resolve().parent / "data"


def kontrollera_ar(konfig_path, ar):
    """Höjer ValueError om ar inte står i konfigens ar-lista.

    Sidan laddar bara år som står där och faller annars tillbaka på standardåret, tyst. Alt-texten och
    filnamnet räknas däremot ur den valda datafilen, så en export av ett år som inte är påslaget gav en
    bild av standardåret med fel årtal i namn och alt-text, och avslutade med OK (granskningsfynd 6)."""
    konfig_path = Path(konfig_path)
    try:
        konfig = json.loads(konfig_path.read_text("utf-8"))
    except (OSError, ValueError) as ex:
        raise ValueError(f"{konfig_path}: kunde inte läsas ({ex}), går inte att kontrollera att {ar} kan ritas") from None
    lista = [str(x) for x in (konfig.get("ar") or [])]
    if str(ar) not in lista:
        raise ValueError(f"året {ar} står inte i {konfig_path} (där står {', '.join(lista) or 'inga år'}). "
                         f"Sidan hade ritat {konfig.get('standardAr')} och bilden fått fel årtal i filnamn och "
                         "alt-text. Kör uppdatera_2026.py --valnatt först, eller lägg till året i konfigen.")


def las_renderat_ar(chrome, url):
    """Året sidan faktiskt ritade, läst ur bildramens data-ar med Chrome --dump-dom.

    Konfigkontrollen är ett antagande om vad sidan gör med adressen; det här är en avläsning av vad den
    gjorde. Körs en gång per export, inte en gång per bild."""
    r = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-first-run",
                        "--virtual-time-budget=5000", "--dump-dom", url],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"Chrome misslyckades vid årskontrollen ({r.returncode}): {r.stderr.strip()[-400:]}")
    m = re.search(r'class="bildram[^"]*"[^>]*\bdata-ar="(\d{4})"', r.stdout)   # klassen bär även bildtypen
    if not m:
        raise RuntimeError("sidan ritade ingen bildram: gick datafilerna att ladda?")
    return m.group(1)


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
    data = Path(a.data) if a.data else datamapp(a.html) / f"valdata_{a.ar}.json"
    try:
        kontrollera_ar(datamapp(a.html) / "konfig.json", a.ar)
        alt = {(typ, val): (alttext if typ == "jamforelse" else alttext_karta)(data, val) for typ in a.typ for val in a.val}
    except (ValueError, KeyError, FileNotFoundError) as ex:
        print(f"FEL: {ex}", file=sys.stderr)
        return 1
    ut = Path(a.ut)
    ut.mkdir(parents=True, exist_ok=True)
    forsta = {"bild": a.typ[0], "val": a.val[0], "format": a.format[0], "ar": a.ar, "etikett": a.etikett}
    try:
        ritat = las_renderat_ar(a.chrome, Path(a.html).resolve().as_uri() + "?" + urllib.parse.urlencode(forsta))
    except (RuntimeError, subprocess.TimeoutExpired) as ex:
        print(f"FEL: {ex}", file=sys.stderr)
        return 1
    if ritat != str(a.ar):
        print(f"FEL: sidan ritade {ritat}, inte {a.ar}. Bilden hade fått fel årtal i filnamn och alt-text.",
              file=sys.stderr)
        return 1
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
