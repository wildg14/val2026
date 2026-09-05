import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import hamta_2026 as hm

ROT = Path(__file__).resolve().parents[1]
GENREP = Path("/Users/daniel/code/Temp/Historiska dokument/dl_webb/genrep2026")
finns = pytest.mark.skipif(not (GENREP / "index_genrep2026.md5").exists(), reason="genrep-filerna saknas")
NYCKEL = ROT / "val-sign-pub.pem"

INDEX = """41a78ddad005c6b50313e3dcbfc95cae  ./p/kf/Val_2026_preliminar_1480_KF.zip
3e6407d8abce4a7856a396cd61e02724  ./p/rd/Val_2026_preliminar_00_RD.zip
392a8097010be810d0812c580b09590d  ./p/rf/Val_2026_preliminar_14_RF.zip
d573889b681dbe6e1a1f3a32607d4522  ./s/kf/Val_2026_slutlig_1480_KF.zip
f4d220f18d61c1aded3b7ac4aac50949  ./s/rd/Val_2026_slutlig_00_RD.zip
88c2379651d10bb07efe3f1bc459670e  ./s/rf/Val_2026_slutlig_14_RF.zip
0123456789abcdef0123456789abcdef  ./p/kf/Val_2026_preliminar_1481_KF.zip
"""


def test_las_index_och_valj_filer_preliminart_och_slutligt():
    index = hm.las_index(INDEX)
    assert len(index) == 7
    p = hm.valj_filer(index, "p")
    assert p["kf"] == ("./p/kf/Val_2026_preliminar_1480_KF.zip", "41a78ddad005c6b50313e3dcbfc95cae")
    assert p["rd"][0].endswith("_00_RD.zip") and p["rf"][0].endswith("_14_RF.zip")
    s = hm.valj_filer(index, "s")
    assert s["rd"][0] == "./s/rd/Val_2026_slutlig_00_RD.zip"


def test_valj_filer_kraver_exakt_en_traff():
    with pytest.raises(hm.HamtFel):
        hm.valj_filer(hm.las_index(INDEX.replace("./p/rd/", "./p/rx/")), "p")
    with pytest.raises(hm.HamtFel):
        hm.valj_filer(hm.las_index(INDEX + "ffffffffffffffffffffffffffffffff  ./p/rd/Val_2026_preliminar_2_00_RD.zip\n"), "p")


def test_las_index_avvisar_html():
    with pytest.raises(hm.HamtFel):
        hm.las_index("<html><head><title>404 Not Found</title></head></html>")


def test_kontrollera_md5():
    hm.kontrollera_md5(b"abc", hashlib.md5(b"abc").hexdigest())
    with pytest.raises(hm.HamtFel):
        hm.kontrollera_md5(b"abc", "00000000000000000000000000000000")


@finns
def test_genrep_index_valjer_ratt_filer():
    index = hm.las_index((GENREP / "index_genrep2026.md5").read_text("utf-8"))
    p = hm.valj_filer(index, "p")
    assert p["kf"][0] == "./p/kf/Genrep_2026_preliminar_1480_KF.zip"
    assert p["rd"][0] == "./p/rd/Genrep_2026_preliminar_00_RD.zip"
    assert p["rf"][0] == "./p/rf/Genrep_2026_preliminar_14_RF.zip"


@finns
def test_packa_upp_genrep_kf(tmp_path):
    data = (GENREP / "Genrep_2026_preliminar_1480_KF.zip").read_bytes()
    hm.kontrollera_md5(data, "41a78ddad005c6b50313e3dcbfc95cae")
    filer = hm.packa_upp(data, tmp_path / "kf")
    assert filer["rostfordelning"].name == "Genrep_2026_preliminar_rostfordelning_1480_KF.json"
    assert filer["mandatfordelning"].exists() and "summering" not in filer
    assert filer["signaturer"]["rostfordelning"].name.endswith("_sign.sha256")


@finns
def test_packa_upp_genrep_rd_har_summering(tmp_path):
    filer = hm.packa_upp((GENREP / "Genrep_2026_preliminar_00_RD.zip").read_bytes(), tmp_path / "rd")
    assert filer["summering"].name == "Genrep_2026_preliminar_summering_RD.json"


def test_packa_upp_avvisar_sokvagar_i_zip(tmp_path):
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("../ut.json", "{}")
    with pytest.raises(hm.HamtFel):
        hm.packa_upp(buf.getvalue(), tmp_path / "x")


@pytest.mark.skipif(not NYCKEL.exists() or not (GENREP / "unz").exists(), reason="val-sign-pub.pem saknas i projektroten, se README")
def test_signatur_verifieras_med_valmyndighetens_nyckel():
    mapp = GENREP / "unz" / "Genrep_2026_preliminar_1480_KF"
    ok = hm.verifiera_signatur(mapp / "Genrep_2026_preliminar_rostfordelning_1480_KF.json",
                               mapp / "Genrep_2026_preliminar_rostfordelning_1480_KF_sign.sha256", NYCKEL)
    assert ok is True


@finns
def test_lokal_korning_packar_upp_tre_val(tmp_path):
    r = subprocess.run([sys.executable, "scripts/hamta_2026.py", "--lokal", str(GENREP), "--ut", str(tmp_path), "--utan-signatur"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    mapp = Path(r.stdout.strip().splitlines()[-1].split("MAPP: ", 1)[1])
    assert (mapp / "rd").is_dir() and (mapp / "rf").is_dir() and (mapp / "kf").is_dir()
    assert any(p.name.endswith("_rostfordelning_1480_KF.json") for p in (mapp / "kf").iterdir())
    assert (tmp_path / "senaste").resolve() == mapp.resolve()
