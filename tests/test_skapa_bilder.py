import json
import struct
import subprocess
import sys
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parents[1]
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
ALT_RD = ("Majorna mot Sverige, riksdagsvalet 2022, skillnad i procentenheter: "
          "V +20,4, MP +10,6, L -0,5, C -2,4, KD -3,0, S -4,4, M -10,2, SD -10,4.")
ALT_KARTA_RD = "Karta över Majornas 23 valdistrikt, största parti i riksdagsvalet 2022: Vänsterpartiet i 14, Socialdemokraterna i 9."


def png_storlek(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


@pytest.mark.skipif(not CHROME.exists(), reason="Chrome saknas")
def test_skapa_bilder_skriver_png_2x_och_alttext(tmp_path):
    r = subprocess.run([sys.executable, "scripts/skapa_bilder.py", "--ut", str(tmp_path), "--val", "rd", "kf"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    liggande = tmp_path / "majorna-mot-sverige-rd-2022-1200x630.png"
    kvadrat = tmp_path / "majorna-mot-sverige-rd-2022-1080x1080.png"
    assert liggande.exists() and kvadrat.exists(), sorted(p.name for p in tmp_path.iterdir())
    assert png_storlek(liggande) == (2400, 1260)
    assert png_storlek(kvadrat) == (2160, 2160)
    assert (tmp_path / "majorna-mot-goteborg-kf-2022-1200x630.png").exists()
    assert (tmp_path / "majorna-mot-sverige-rd-2022-1200x630.txt").read_text("utf-8").strip() == ALT_RD
    assert "Göteborg, kommunvalet 2022" in (tmp_path / "majorna-mot-goteborg-kf-2022-1080x1080.txt").read_text("utf-8")
    assert png_storlek(tmp_path / "majorna-karta-rd-2022-1200x630.png") == (2400, 1260)
    assert png_storlek(tmp_path / "majorna-karta-rd-2022-1080x1080.png") == (2160, 2160)
    assert (tmp_path / "majorna-karta-rd-2022-1200x630.txt").read_text("utf-8").strip() == ALT_KARTA_RD
    assert "kommunvalet 2022: Vänsterpartiet i 23." in (tmp_path / "majorna-karta-kf-2022-1080x1080.txt").read_text("utf-8")


@pytest.mark.skipif(not CHROME.exists(), reason="Chrome saknas")
def test_skala_1_ger_logiska_matt(tmp_path):
    r = subprocess.run([sys.executable, "scripts/skapa_bilder.py", "--ut", str(tmp_path), "--val", "rd", "--format", "liggande", "--skala", "1"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert png_storlek(tmp_path / "majorna-mot-sverige-rd-2022-1200x630.png") == (1200, 630)


def test_alttext_beraknas_ur_datan():
    from scripts import skapa_bilder as sb
    assert sb.alttext(ROT / "data" / "valdata_2022.json", "rd") == ALT_RD
    assert sb.alttext_karta(ROT / "data" / "valdata_2022.json", "rd") == ALT_KARTA_RD


# --- Granskningsfynd 6: bilden och alt-texten kunde beskriva olika val ---
# Sidan laddar bara år som står i konfigens ar-lista och faller annars tillbaka på standardåret, utan
# att säga ifrån. Alt-texten och filnamnet räknades däremot ur den valda datafilen. En export med
# --ar 2026 mot en konfig utan 2026 gav därför en bild av 2022 med 2026 i namn och alt-text, och OK.

def _kopia(tmp_path, ar_lista):
    """En isolerad kopia av sidan med en egen konfig, som granskarens felprov."""
    from scripts import schema
    kopia = tmp_path / "sida"
    (kopia / "data").mkdir(parents=True)
    for namn in ("index.html", "valgrafik.js", "valgrafik.css"):
        (kopia / namn).write_bytes((ROT / namn).read_bytes())
    for namn in ("valdata_2022.js", "distrikt_2022.js"):
        (kopia / "data" / namn).write_bytes((ROT / "data" / namn).read_bytes())
    (kopia / "data" / "valdata_2022.json").write_bytes((ROT / "data" / "valdata_2022.json").read_bytes())
    konfig = json.loads((ROT / "data" / "konfig.json").read_text("utf-8"))
    konfig["ar"] = ar_lista
    konfig["standardAr"] = ar_lista[-1]
    schema.skriv_konfig(kopia / "data", konfig)
    return kopia


def test_ar_utanfor_konfigen_avvisas(tmp_path):
    from scripts import skapa_bilder as sb
    kopia = _kopia(tmp_path, ["2010", "2014", "2018", "2022"])
    with pytest.raises(ValueError) as ex:
        sb.kontrollera_ar(kopia / "data" / "konfig.json", "2026")
    assert "2026" in str(ex.value)
    assert "2022" in str(ex.value), "meddelandet ska säga vilket år sidan hade ritat i stället"


def test_ar_i_konfigen_gar_igenom(tmp_path):
    from scripts import skapa_bilder as sb
    sb.kontrollera_ar(ROT / "data" / "konfig.json", "2022")
    kopia = _kopia(tmp_path, ["2022", "2026"])
    sb.kontrollera_ar(kopia / "data" / "konfig.json", "2026")


def test_hela_korningen_stoppas_av_fel_ar(tmp_path):
    """Granskarens prov, hela vägen: OK och en felmärkt PNG blev det förut."""
    kopia = _kopia(tmp_path, ["2018", "2022"])
    r = subprocess.run([sys.executable, "scripts/skapa_bilder.py", "--ut", str(tmp_path / "bilder"),
                        "--ar", "2026", "--val", "kf", "--typ", "karta", "--format", "liggande",
                        "--html", str(kopia / "index.html")], cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "2026" in r.stderr
    assert not (tmp_path / "bilder").exists() or not list((tmp_path / "bilder").glob("*.png")), \
        "ingen bild får skrivas när året inte går att rita"


def test_datafilen_foljer_html_filen(tmp_path):
    """Alt-texten läste repots data/ även när --html pekade på en kopia, alltså en annan sida än den
    som fotograferades. Bild, alt-text och filnamn ska komma ur samma mapp."""
    from scripts import skapa_bilder as sb
    kopia = _kopia(tmp_path, ["2022"])
    assert sb.datamapp(kopia / "index.html") == kopia / "data"
    assert sb.datamapp(ROT / "index.html") == ROT / "data"


@pytest.mark.skipif(not CHROME.exists(), reason="Chrome saknas")
def test_alttexten_kommer_ur_samma_mapp_som_bilden(tmp_path):
    """Hela vägen, inte bara hjälpfunktionen: kopians egna siffror ska stå i .txt-filen. Läses datan ur
    repots mapp medan bilden renderas ur kopians beskriver de två olika resultat."""
    kopia = _kopia(tmp_path, ["2022"])
    v = json.loads((kopia / "data" / "valdata_2022.json").read_text("utf-8"))
    for d in v["distrikt"]:          # gör V störst i vartenda distrikt, vilket det inte är i repots data
        if d.get("raknat", True) and d.get("rd"):
            d["rd"]["V"] = max(d["rd"].values()) + 1000
    (kopia / "data" / "valdata_2022.json").write_text(json.dumps(v), "utf-8")
    r = subprocess.run([sys.executable, "scripts/skapa_bilder.py", "--ut", str(tmp_path / "bilder"),
                        "--val", "rd", "--typ", "karta", "--format", "liggande",
                        "--html", str(kopia / "index.html")], cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    alt = (tmp_path / "bilder" / "majorna-karta-rd-2022-1200x630.txt").read_text("utf-8").strip()
    assert "Vänsterpartiet i 23" in alt, alt
    assert alt != ALT_KARTA_RD, "repots egen alt-text säger V i 14, alltså lästes fel mapp"


@pytest.mark.skipif(not CHROME.exists(), reason="Chrome saknas")
def test_sidan_talar_om_vilket_ar_den_ritade(tmp_path):
    """Bildramen bär data-ar, och exporten läser det ur den renderade sidan innan den fotograferar.
    Konfigkontrollen är ett antagande om vad sidan gör; det här är en avläsning av vad den gjorde."""
    from scripts import skapa_bilder as sb
    import urllib.parse
    url = (ROT / "index.html").resolve().as_uri() + "?" + urllib.parse.urlencode(
        {"bild": "karta", "val": "rd", "format": "liggande", "ar": "2022"})
    assert sb.las_renderat_ar(str(CHROME), url) == "2022"
