#!/usr/bin/env python3
"""Bygger tmp/tvaar/ med två år (2022 ur data/, 2026 ur en valnattskörning) för verktyg/tvaar-check.js.

    .venv/bin/python verktyg/forbered_tvaar.py --valnatt-data /tmp/valnatt-test/data

Mappen /tmp/valnatt-test/data skrivs av uppdatera_2026.py (se plan, Task 6 steg 5). Testsidan nås som
http://localhost:8765/tmp/tvaar/index.html när servern kör i projektroten.

Med --kf-raknade N doktoreras den kopierade valdata_2026.js så att bara de N första distrikten har
kommunvalet räknat. Då går det att kontrollera att panelens markörtext räknar per val och inte per fil.
Swingfilen räknas då om av det här verktyget: schema.swing körs på den doktorerade valdatan mot
data/valdata_2022.json och skriver över den kopierade swing_2026.js. Annars skulle kohorten fortfarande
säga att alla distrikt är räknade och kortets kohorttext utebli. Testsidans swingfil är alltså verktygets
egen, inte den som uppdatera_2026.py skrev: en grön kf-kontroll säger något om sidan, inte om pipelinen.

Med --status slutlig|preliminar skrivs meta.status om i den kopierade valdata_2026.js, och ordet i
meta.kalla följer med när källan är pipelinens ("... preliminär|slutlig rösträkning per valdistrikt
{år}"): annars skulle Om siffrorna säga slutligt resultat med den preliminära räkningen som källa.
Tillsammans med --valnatt av ger det statusradens två stillsamma grenar: "Slutligt resultat, riksdagsvalet 2026." och
"Preliminärt resultat 2026.", båda utan "Ladda om".

Med --utan-parti S tas partiet bort ur den kopierade swing_2026.js, i alla val och både per distrikt och
på områdesnivån, som om partiet inte redovisats båda åren. Sidan ska då hoppa över partiet i raden "Hur
har det ändrats" och låta nästa parti ta platsen, aldrig skriva ut ett "0,0".

Med --partiell N doktoreras den kopierade valdata_2026.js så att bara de N första distrikten är räknade,
i alla tre valen på en gång - till skillnad från --kf-raknade som bara doktorerar kommunvalet. De
återstående distrikten får raknat=False och tomma tal, aggregaten räknas om och meta.valnatt.raknade
sätts till N. Swingfilen räknas om som vid --kf-raknade. Går inte att kombinera med --kf-raknade.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))
from scripts import schema  # noqa: E402

# Utan de här filerna finns ingen testsida att kontrollera.
OBLIGATORISKA = (("", "index.html"), ("", "valgrafik.js"), ("", "valgrafik.css"),
                 ("data", "distrikt_2022.js"), ("data", "valdata_2022.js"), ("data", "distrikt_2026.js"))
# Valfria: bakgrunden ritas bara om den finns, och historikfilerna skrivs av bygg_historik.py.
# Utan historik.js och distrikt_2006.js döljer sidan sektionen "Majorna sedan 2006"; testsidan fungerar ändå.
VALFRIA = (("data", "bakgrund.js"), ("data", "swing_2022.js"), ("data", "historik.js"), ("data", "distrikt_2006.js"))


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


def doktorera_partiell(fil, antal):
    """Sätter raknat=False och tömmer alla tre valens tal i alla distrikt utom de `antal` första.

    Till skillnad från --kf-raknade, som bara doktorerar kommunvalet, speglar det här valnatten innan
    något distrikt alls är klart: ett oräknat distrikt saknar tal i riksdags-, region- och kommunvalet
    på en gång."""
    valdata = schema.las_js(fil)
    distrikt = valdata["distrikt"]
    if antal > len(distrikt):
        raise SystemExit(f"FEL: --partiell {antal} men filen har {len(distrikt)} distrikt")
    for d in distrikt[antal:]:
        d["raknat"] = False
        for val in ("rd", "rf", "kf"):
            d[val] = {}
        for nyckel in ("giltiga", "rostande", "rostberattigade"):
            d[nyckel] = {}
    for val in ("rd", "rf", "kf"):
        valdata["aggregat"]["majorna"][val] = schema._summa(distrikt, val)
    # En valdatafil utan valnatt-block (äldre vägar skriver inget) ska få ett, inte fälla bygget.
    valnatt = valdata["meta"].setdefault("valnatt", {})
    valnatt["raknade"] = antal
    valnatt.setdefault("totalt", len(distrikt))
    schema.skriv_js(fil.with_suffix(""), valdata)
    return antal


def rakna_om_swing(mapp):
    """Räknar om swing_2026.js ur den doktorerade valdatan, mot samma basår som uppdatera_2026.py använder.

    Kohorten i swingfilen ska spegla testsidans räknade distrikt, annars säger kortet "räknat på 23
    jämförbara distrikt av 23" på en sida där bara några distrikt är räknade i kommunvalet."""
    bas_fil = ROT / "data" / "valdata_2022.json"
    if not bas_fil.exists():
        raise SystemExit(f"FEL: {bas_fil} saknas, swingen kan inte räknas om")
    ny = schema.las_js(mapp / "valdata_2026.js")
    bas = json.loads(bas_fil.read_text("utf-8"))
    jamforbara = [d["kod"] for d in ny["distrikt"] if d.get("jamforbar_mot_bas", True)]
    schema.skriv_js(mapp / "swing_2026", schema.swing(ny, bas, jamforbara=jamforbara))


def rakna_om_swing_om_finns(ut):
    """Samma efterarbete för --kf-raknade och --partiell: räkna om swingfilen när den kopierats med."""
    if not (ut / "swing_2026.js").exists():
        return False
    rakna_om_swing(ut)
    print("swing_2026.js omräknad mot data/valdata_2022.json, kohorten följer den doktorerade valdatan")
    return True


def ta_bort_parti(fil, parti):
    """Tar bort ett parti ur swingfilen: alla val, alla distrikt och områdesnivån.

    Speglar ett parti som inte redovisas båda åren. Kortets rad ska hoppa över det och låta nästa parti
    ta platsen. Hittas partiet inte alls är flaggan felskriven och bygget avbryts."""
    sw = schema.las_js(fil)
    poster = list((sw.get("distrikt") or {}).values()) + [sw.get("majorna") or {}]
    borttagna = sum(1 for post in poster for tal in post.values()
                    if isinstance(tal, dict) and tal.pop(parti, None) is not None)
    if not borttagna:
        raise SystemExit(f"FEL: --utan-parti {parti} men partiet finns inte i {fil.name}")
    schema.skriv_js(fil.with_suffix(""), sw)
    return borttagna


def doktorera_riket(fil, antal):
    """Skruvar ned aggregat.riket.rd.antal_distrikt i den kopierade valdata_2026.js.

    Rikets aggregat är färdigräknat i genrepsfilerna, så ett delvis räknat riket går inte att pröva ur
    datan som den är. Det läget är däremot normalt under valkvällens första timmar, och det är då sidan
    ska skriva förbehållet under halvcirkeln - i både mandatläget och procentläget."""
    valdata = schema.las_js(fil)
    post = ((valdata.get("aggregat") or {}).get("riket") or {}).get("rd")
    if not post:
        raise SystemExit(f"FEL: --riket-delvis men {fil.name} saknar aggregat.riket.rd")
    totalt = post.get("totalt_distrikt")
    if totalt is None:
        raise SystemExit(f"FEL: --riket-delvis men aggregat.riket.rd saknar totalt_distrikt")
    if antal > totalt:
        raise SystemExit(f"FEL: --riket-delvis {antal} men riket har {totalt} distrikt")
    post["antal_distrikt"] = antal
    schema.skriv_js(fil.with_suffix(""), valdata)
    return antal, totalt


def satt_status(fil, status):
    """Skriver om meta.status i den kopierade valdata_2026.js, och ordet i meta.kalla när det står där.

    Pipelinen sätter kalla till "... {preliminär|slutlig} rösträkning per valdistrikt {år}" efter status,
    så en testsida med bytt status ska inte säga slutligt resultat med den preliminära räkningen som källa.
    En källa av något annat slag lämnas orörd."""
    valdata = schema.las_js(fil)
    valdata["meta"]["status"] = status
    ratt_ord = "slutlig" if status == "slutlig" else "preliminär"
    kalla = valdata["meta"].get("kalla") or ""
    for gammalt in ("preliminär rösträkning", "slutlig rösträkning"):
        if gammalt in kalla:
            valdata["meta"]["kalla"] = kalla.replace(gammalt, f"{ratt_ord} rösträkning")
            break
    schema.skriv_js(fil.with_suffix(""), valdata)
    return status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--valnatt-data", required=True, help="mapp med valdata_2026.js och swing_2026.js")
    ap.add_argument("--ut", default=ROT / "tmp" / "tvaar")
    ap.add_argument("--valnatt", action="store_true", help="slå på valnattsläget i testsidans konfig")
    ap.add_argument("--kf-raknade", type=icke_negativ, help="låt bara de N första distrikten ha kommunvalet räknat")
    ap.add_argument("--status", choices=("slutlig", "preliminar"), help="skriv om meta.status i testsidans valdata_2026.js")
    ap.add_argument("--utan-parti", metavar="PARTI", help="ta bort partiet ur testsidans swing_2026.js (alla val, distrikt och områdesnivå)")
    ap.add_argument("--partiell", type=icke_negativ, metavar="N",
                     help="markera bara de N första distrikten som räknade i alla tre valen och räkna om swingfilen; kan inte kombineras med --kf-raknade")
    ap.add_argument("--riket-delvis", type=icke_negativ, metavar="N",
                     help="skruva ned aggregat.riket.rd.antal_distrikt till N, för förbehållet under halvcirkeln")
    a = ap.parse_args()
    if a.partiell is not None and a.kf_raknade is not None:
        print("FEL: --partiell och --kf-raknade kan inte kombineras", file=sys.stderr)
        sys.exit(1)
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
        rakna_om_swing_om_finns(ut / "data")
    if a.partiell is not None:
        doktorera_partiell(ut / "data" / "valdata_2026.js", a.partiell)
        print(f"valdata_2026.js doktorerad: {a.partiell} distrikt räknade i alla tre valen")
        rakna_om_swing_om_finns(ut / "data")
    if a.riket_delvis is not None:
        antal, totalt = doktorera_riket(ut / "data" / "valdata_2026.js", a.riket_delvis)
        print(f"valdata_2026.js doktorerad: riket {antal} av {totalt} distrikt räknade")
    if a.status:
        satt_status(ut / "data" / "valdata_2026.js", a.status)
        print(f"valdata_2026.js doktorerad: meta.status = {a.status}")
    if a.utan_parti:   # sist, så att en omräknad swing inte skriver tillbaka partiet
        swing_fil = ut / "data" / "swing_2026.js"
        if not swing_fil.exists():
            raise SystemExit("FEL: --utan-parti kräver swing_2026.js, den saknas i valnattsdatan")
        antal = ta_bort_parti(swing_fil, a.utan_parti)
        print(f"swing_2026.js doktorerad: {a.utan_parti} borttaget ur {antal} valposter")
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
