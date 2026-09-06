#!/usr/bin/env python3
"""Bygger tmp/tvaar/ med två år (2022 ur data/, 2026 ur en valnattskörning) för verktyg/tvaar-check.js.

    .venv/bin/python verktyg/forbered_tvaar.py --valnatt-data /tmp/valnatt-test/data

Mappen /tmp/valnatt-test/data skrivs av uppdatera_2026.py (se plan, Task 6 steg 5). Testsidan nås som
http://localhost:8765/tmp/tvaar/index.html när servern kör i projektroten.

Med --kf-raknade N doktoreras den kopierade valdata_2026.js så att bara de N första distrikten har
kommunvalet räknat. Då går det att kontrollera att panelens markörtext räknar per val och inte per fil.

Med --status slutlig|preliminar skrivs meta.status om i den kopierade valdata_2026.js. Tillsammans med
--valnatt av ger det statusradens två stillsamma grenar: "Slutligt resultat, riksdagsvalet 2026." och
"Preliminärt resultat 2026.", båda utan "Ladda om".
"""
import argparse
import shutil
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))
from scripts import schema  # noqa: E402

# Utan de här filerna finns ingen testsida att kontrollera.
OBLIGATORISKA = (("", "index.html"), ("", "valgrafik.js"), ("", "valgrafik.css"),
                 ("data", "distrikt_2022.js"), ("data", "valdata_2022.js"), ("data", "distrikt_2026.js"))
# Valfria: bakgrunden ritas bara om den finns, och swing_2022.js skrivs först av historikplanen.
VALFRIA = (("data", "bakgrund.js"), ("data", "swing_2022.js"))


def kopiera(kalla, mal, obligatorisk):
    if not kalla.exists():
        if obligatorisk:
            raise SystemExit(f"FEL: {kalla} saknas")
        return False
    shutil.copy(kalla, mal)
    return True


def icke_negativ(text):
    """argparse-typ: fångar ett negativt tal redan i argumentläsningen, innan --ut hinner tömmas."""
    antal = int(text)
    if antal < 0:
        raise argparse.ArgumentTypeError(f"{antal} är negativt")
    return antal


def doktorera_kf(fil, antal):
    """Tömmer kommunvalet i alla distrikt utom de `antal` första och räknar om aggregatet."""
    valdata = schema.las_js(fil)
    distrikt = valdata["distrikt"]
    if antal > len(distrikt):
        raise SystemExit(f"FEL: --kf-raknade {antal} men filen har {len(distrikt)} distrikt")
    for d in distrikt[antal:]:
        d["kf"] = {}
        for nyckel in ("giltiga", "rostande", "rostberattigade"):
            d[nyckel].pop("kf", None)
    valdata["aggregat"]["majorna"]["kf"] = schema._summa(distrikt, "kf")
    schema.skriv_js(fil.with_suffix(""), valdata)
    return antal


def satt_status(fil, status):
    """Skriver om meta.status i den kopierade valdata_2026.js."""
    valdata = schema.las_js(fil)
    valdata["meta"]["status"] = status
    schema.skriv_js(fil.with_suffix(""), valdata)
    return status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--valnatt-data", required=True, help="mapp med valdata_2026.js och swing_2026.js")
    ap.add_argument("--ut", default=ROT / "tmp" / "tvaar")
    ap.add_argument("--valnatt", action="store_true", help="slå på valnattsläget i testsidans konfig")
    ap.add_argument("--kf-raknade", type=icke_negativ, help="låt bara de N första distrikten ha kommunvalet räknat")
    ap.add_argument("--status", choices=("slutlig", "preliminar"), help="skriv om meta.status i testsidans valdata_2026.js")
    a = ap.parse_args()
    ut = Path(a.ut).resolve()   # relativ --ut ska fungera, sökvägen skrivs ut mot projektroten
    if ut.exists():
        shutil.rmtree(ut)
    (ut / "data").mkdir(parents=True)
    for mapp, namn in OBLIGATORISKA:
        kopiera(ROT / mapp / namn, ut / mapp / namn, True)
    hoppade = [namn for mapp, namn in VALFRIA if not kopiera(ROT / mapp / namn, ut / mapp / namn, False)]
    kopiera(Path(a.valnatt_data) / "valdata_2026.js", ut / "data" / "valdata_2026.js", True)
    if not kopiera(Path(a.valnatt_data) / "swing_2026.js", ut / "data" / "swing_2026.js", False):
        hoppade.append("swing_2026.js")
    if a.kf_raknade is not None:
        doktorera_kf(ut / "data" / "valdata_2026.js", a.kf_raknade)
        print(f"valdata_2026.js doktorerad: {a.kf_raknade} distrikt har kommunvalet räknat")
    if a.status:
        satt_status(ut / "data" / "valdata_2026.js", a.status)
        print(f"valdata_2026.js doktorerad: meta.status = {a.status}")
    konfig = schema.las_konfig(ROT / "data")
    konfig.update({"ar": ["2022", "2026"], "standardAr": "2026", "valnatt": bool(a.valnatt)})
    schema.skriv_konfig(ut / "data", konfig)
    if hoppade:
        print("valfria filer som saknas: " + ", ".join(hoppade))
    if ut.is_relative_to(ROT):
        print(f"Testsida: http://localhost:8765/{ut.relative_to(ROT)}/index.html")
    else:
        print(f"Testsida: {ut / 'index.html'} (utanför projektroten, servern i roten når den inte)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
