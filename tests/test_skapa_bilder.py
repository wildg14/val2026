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
