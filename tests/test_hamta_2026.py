import hashlib
import http.client
import io
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError

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


def _bygg_zip(dela=("rostfordelning", "mandatfordelning"), med_signatur=(), suffix="1480_KF"):
    """En minimal resultatzip: X_<del>_<suffix>.json för varje del i dela, plus signaturfil för de i med_signatur."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for d in dela:
            z.writestr(f"X_{d}_{suffix}.json", "{}")
            if d in med_signatur:
                z.writestr(f"X_{d}_{suffix}_sign.sha256", "dummy-signatur")
    return buf.getvalue()


def _kor(argv, cwd=ROT):
    return subprocess.run([sys.executable, "scripts/hamta_2026.py", *argv], cwd=cwd, capture_output=True, text=True)


def _huvud(argv):
    """Kör hm.main() in-process med argv (utan skriptnamnet behöver inte anges separat)."""
    gammal = sys.argv
    sys.argv = ["hamta_2026.py", *argv]
    try:
        return hm.main()
    finally:
        sys.argv = gammal


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


def test_las_index_med_bom():
    # utf-8-sig-avkodning ger en text som redan kan börja med ett BOM-tecken; las_index ska tåla det.
    index = hm.las_index("﻿" + INDEX)
    assert len(index) == 7


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
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("../ut.json", "{}")
    with pytest.raises(hm.HamtFel):
        hm.packa_upp(buf.getvalue(), tmp_path / "x")


def test_packa_upp_validerar_innan_den_skriver(tmp_path):
    # En giltig post före en otillåten sökväg ska inte hinna skrivas: hela namnlistan valideras först.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("bra_rostfordelning_1480_KF.json", "{}")
        z.writestr("../ut.json", "{}")
    mal = tmp_path / "x"
    with pytest.raises(hm.HamtFel):
        hm.packa_upp(buf.getvalue(), mal)
    assert not mal.exists() or not any(mal.iterdir())


@pytest.mark.skipif(not NYCKEL.exists() or not (GENREP / "unz").exists(), reason="val-sign-pub.pem saknas i projektroten, se README")
def test_signatur_verifieras_med_valmyndighetens_nyckel():
    mapp = GENREP / "unz" / "Genrep_2026_preliminar_1480_KF"
    ok = hm.verifiera_signatur(mapp / "Genrep_2026_preliminar_rostfordelning_1480_KF.json",
                               mapp / "Genrep_2026_preliminar_rostfordelning_1480_KF_sign.sha256", NYCKEL)
    assert ok is True


@pytest.mark.skipif(not NYCKEL.exists() or not (GENREP / "unz").exists(), reason="val-sign-pub.pem saknas i projektroten, se README")
def test_signatur_ger_false_vid_andrad_byte(tmp_path):
    mapp = GENREP / "unz" / "Genrep_2026_preliminar_1480_KF"
    json_src = mapp / "Genrep_2026_preliminar_rostfordelning_1480_KF.json"
    sign_src = mapp / "Genrep_2026_preliminar_rostfordelning_1480_KF_sign.sha256"
    data = bytearray(json_src.read_bytes())
    data[0] ^= 0xFF
    json_kopia = tmp_path / json_src.name
    json_kopia.write_bytes(bytes(data))
    ok = hm.verifiera_signatur(json_kopia, sign_src, NYCKEL)
    assert ok is False


@finns
def test_lokal_korning_packar_upp_tre_val(tmp_path):
    def kor():
        r = _kor(["--lokal", str(GENREP), "--ut", str(tmp_path), "--utan-signatur"])
        assert r.returncode == 0, r.stdout + r.stderr
        return Path(r.stdout.strip().splitlines()[-1].split("MAPP: ", 1)[1])

    mapp1 = kor()
    assert (mapp1 / "rd").is_dir() and (mapp1 / "rf").is_dir() and (mapp1 / "kf").is_dir()
    assert any(p.name.endswith("_rostfordelning_1480_KF.json") for p in (mapp1 / "kf").iterdir())
    assert (tmp_path / "senaste").resolve() == mapp1.resolve()

    # Andra körningen: senaste ska bytas till den nya mappen (tidsstämpeln görs unik med suffix vid krock).
    mapp2 = kor()
    assert mapp2 != mapp1
    assert (tmp_path / "senaste").resolve() == mapp2.resolve()


@finns
def test_lokal_bara_om_nytt_ger_kod_3(tmp_path):
    r1 = _kor(["--lokal", str(GENREP), "--ut", str(tmp_path), "--utan-signatur"])
    assert r1.returncode == 0, r1.stdout + r1.stderr
    r2 = _kor(["--lokal", str(GENREP), "--ut", str(tmp_path), "--utan-signatur", "--bara-om-nytt"])
    assert r2.returncode == 3, r2.stdout + r2.stderr
    assert "Inget nytt" in r2.stdout


# --- Punkt 1: saknad signaturfil ska ge ett tydligt HamtFel, inte KeyError ---

def test_signatur_saknas_ger_tydligt_fel(tmp_path):
    lokal = tmp_path / "kalla"
    lokal.mkdir()
    for suffix in ("00_RD", "14_RF", "1480_KF"):
        (lokal / f"X_{suffix}.zip").write_bytes(_bygg_zip(suffix=suffix))  # inga signaturfiler alls
    dummy_nyckel = tmp_path / "dummy-nyckel.pem"
    dummy_nyckel.write_text("används aldrig, felet ska komma innan verifieringen", "utf-8")

    r = _kor(["--lokal", str(lokal), "--ut", str(tmp_path / "ut"), "--nyckel", str(dummy_nyckel)])
    assert r.returncode == 1, r.stdout + r.stderr
    assert "signatur saknas" in r.stdout + r.stderr


# --- Punkt 2: ett återförsök när filerna ändras under hämtningen ---

def test_atermforsok_vid_andrade_filer(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(hm, "PAUS_SEKUNDER", 0)  # ingen anledning att vänta 3 sekunder i ett test
    zip_ratt = _bygg_zip(suffix="TEST")
    md5_ratt = hashlib.md5(zip_ratt).hexdigest()
    index_text = (
        f"{md5_ratt}  ./p/rd/Test_00_RD.zip\n"
        f"{md5_ratt}  ./p/rf/Test_14_RF.zip\n"
        f"{md5_ratt}  ./p/kf/Test_1480_KF.zip\n"
    )
    tillstand = {"index": 0, "zip": 0}

    def fake_hamta(url, timeout=30):
        if url.endswith("index.md5"):
            tillstand["index"] += 1
            return index_text.encode("utf-8")
        tillstand["zip"] += 1
        if tillstand["zip"] == 1:
            return b"fel innehall, matchar inte md5"
        return zip_ratt

    monkeypatch.setattr(hm, "hamta", fake_hamta)

    kod = _huvud(["--bas-url", "https://example.invalid/", "--utan-signatur", "--ut", str(tmp_path)])

    assert kod == 0
    assert tillstand["index"] == 2
    assert "Filerna ändrades under hämtningen, försöker igen" in capsys.readouterr().out


def test_atermforsok_gors_bara_vid_andrade_filer_inte_vid_404(monkeypatch, tmp_path, capsys):
    """404 på index är ett vanligt HamtFel, inte AndradUnderHamtning: inget andra försök, ingen paus."""
    monkeypatch.setattr(hm, "PAUS_SEKUNDER", 0)
    antal = {"index": 0}

    def fake_hamta(url, timeout=30):
        if url.endswith("index.md5"):
            antal["index"] += 1
            raise hm.HamtFel(f"{url} svarar 404: resultatfilerna publiceras först på valkvällen")
        raise AssertionError("zip-filer ska inte hämtas: 404 på index ska avbryta direkt")

    monkeypatch.setattr(hm, "hamta", fake_hamta)

    kod = _huvud(["--bas-url", "https://example.invalid/", "--utan-signatur", "--ut", str(tmp_path)])

    assert kod == 1
    assert antal["index"] == 1, "bara en indexhämtning, inget andra försök"
    ut = capsys.readouterr()
    assert "försöker igen" not in ut.out


# --- Punkt 3: peka_senaste byter länken atomärt och relativt ---

def test_peka_senaste_skapar_lank(tmp_path):
    ut = tmp_path / "ut"
    ut.mkdir()
    mapp = ut / "20260905-120000"
    mapp.mkdir()
    hm.peka_senaste(ut, mapp)
    lank = ut / "senaste"
    assert lank.is_symlink()
    assert lank.resolve() == mapp.resolve()
    assert os.readlink(lank) == mapp.name  # relativ länk, inte absolut sökväg


def test_peka_senaste_byter_till_ny_mapp(tmp_path):
    ut = tmp_path / "ut"
    ut.mkdir()
    mapp1 = ut / "20260905-120000"
    mapp1.mkdir()
    hm.peka_senaste(ut, mapp1)
    mapp2 = ut / "20260905-130000"
    mapp2.mkdir()
    hm.peka_senaste(ut, mapp2)
    assert (ut / "senaste").resolve() == mapp2.resolve()


def test_peka_senaste_vagrar_riktig_katalog(tmp_path):
    ut = tmp_path / "ut"
    ut.mkdir()
    (ut / "senaste").mkdir()  # riktig katalog, inte en länk
    mapp = ut / "20260905-120000"
    mapp.mkdir()
    with pytest.raises(hm.HamtFel, match=re.escape(str(ut / "senaste"))):
        hm.peka_senaste(ut, mapp)


def test_main_vagrar_riktig_katalog_som_senaste_innan_hamtning(monkeypatch, tmp_path):
    """Vakten mot en riktig katalog i stället för länken ska köras tidigt i main, före hämtning."""
    ut = tmp_path / "ut"
    ut.mkdir()
    (ut / "senaste").mkdir()  # riktig katalog i stället för en länk

    def fake_hamta(url, timeout=30):
        raise AssertionError("katalogvakten ska stoppa körningen innan någon hämtning görs")

    monkeypatch.setattr(hm, "hamta", fake_hamta)

    kod = _huvud(["--ut", str(ut)])
    assert kod == 1


# --- Punkt 4: --bara-om-nytt jämför bara md5 för de tre valda filerna ---

def test_ar_oforandrat_identiskt_och_andrat_urval(tmp_path):
    senaste = tmp_path / "senaste"
    senaste.mkdir()
    (senaste / "index.md5").write_text(INDEX, "utf-8")
    urval = hm.valj_filer(hm.las_index(INDEX), "p")
    assert hm.ar_oforandrat(tmp_path, "p", urval) is True

    andrat = dict(urval)
    andrat["kf"] = (andrat["kf"][0], "0" * 32)
    assert hm.ar_oforandrat(tmp_path, "p", andrat) is False


def test_ar_oforandrat_saknad_eller_trasig_senaste(tmp_path):
    urval = hm.valj_filer(hm.las_index(INDEX), "p")
    assert hm.ar_oforandrat(tmp_path, "p", urval) is False  # senaste finns inte alls

    senaste = tmp_path / "senaste"
    senaste.mkdir()
    (senaste / "index.md5").write_text("trasigt, inte alls i md5-format", "utf-8")
    assert hm.ar_oforandrat(tmp_path, "p", urval) is False


# --- Punkt 6/7: BOM-tålig indexläsning testas ovan (test_las_index_med_bom); nätfel här ---

def test_hamta_404_pa_index_ger_tydligt_fel(monkeypatch):
    def fake_urlopen(req, timeout=30):
        raise HTTPError(req.full_url, 404, "Not Found", {}, None)
    monkeypatch.setattr(hm, "urlopen", fake_urlopen)
    with pytest.raises(hm.HamtFel, match="valkvällen"):
        hm.hamta("https://resultat.val.se/resultatfiler/val2026/index.md5")


def test_hamta_annat_http_fel_namner_adressen(monkeypatch):
    def fake_urlopen(req, timeout=30):
        raise HTTPError(req.full_url, 500, "Server Error", {}, None)
    monkeypatch.setattr(hm, "urlopen", fake_urlopen)
    with pytest.raises(hm.HamtFel, match="example.invalid"):
        hm.hamta("https://example.invalid/x.zip")


def test_hamta_natverksfel_namner_adressen(monkeypatch):
    def fake_urlopen(req, timeout=30):
        raise URLError("nätverket är nere")
    monkeypatch.setattr(hm, "urlopen", fake_urlopen)
    with pytest.raises(hm.HamtFel, match="example.invalid"):
        hm.hamta("https://example.invalid/x.zip")


def test_hamta_timeout_ar_30_sekunder():
    import inspect
    assert inspect.signature(hm.hamta).parameters["timeout"].default == 30


def test_hamta_incomplete_read_ger_hamtfel_med_adress(monkeypatch):
    class FelanadeSvar:
        def read(self):
            raise http.client.IncompleteRead(b"", 10)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=30):
        return FelanadeSvar()

    monkeypatch.setattr(hm, "urlopen", fake_urlopen)
    with pytest.raises(hm.HamtFel, match="example.invalid"):
        hm.hamta("https://example.invalid/x.zip")


# --- Punkt 2 (fortsättning): las_index, valj_lokala_filer och packa_upp gör fler undantag till HamtFel ---

def test_las_index_med_bytes_ogiltig_kodning_ger_hamtfel():
    with pytest.raises(hm.HamtFel):
        hm.las_index(b"\xe5\xe4\xf6  ./p/rd/x.zip\n")


def test_valj_lokala_filer_hoppar_over_indexfil_med_fel_teckenkodning(tmp_path):
    for suffix in ("00_RD", "14_RF", "1480_KF"):
        (tmp_path / f"Test_{suffix}.zip").write_bytes(b"")
    (tmp_path / "index_1_latin1.md5").write_bytes(b"\xe5\xe4\xf6, inte giltig utf-8\n")
    riktigt = "\n".join(
        f"{'0' * 32}  ./p/{kat}/Test_{suffix}.zip"
        for kat, suffix in (("rd", "00_RD"), ("rf", "14_RF"), ("kf", "1480_KF"))
    ) + "\n"
    (tmp_path / "index_2_giltig.md5").write_text(riktigt, "utf-8")

    index_text, index, urval = hm.valj_lokala_filer(tmp_path, "p")
    assert index is not None
    assert urval["kf"][1] == "0" * 32


def test_packa_upp_ogiltig_zip_ger_hamtfel(tmp_path):
    with pytest.raises(hm.HamtFel):
        hm.packa_upp(b"inte en zip", tmp_path / "x")


def test_main_ovantat_fel_ger_fel_rad_och_kod_2(monkeypatch, tmp_path, capsys):
    """Ett undantag som inte är HamtFel eller OSError ska ändå ge en tydlig FEL-rad och returkod 2,
    så att in-process-anrop (till exempel från uppdatera_2026.py) alltid får en returkod."""
    lokal = tmp_path / "kalla"
    lokal.mkdir()
    for suffix in ("00_RD", "14_RF", "1480_KF"):
        (lokal / f"X_{suffix}.zip").write_bytes(_bygg_zip(suffix=suffix))

    def fake_peka_senaste(ut, mapp):
        raise ValueError("kaboom")

    monkeypatch.setattr(hm, "peka_senaste", fake_peka_senaste)

    kod = _huvud(["--lokal", str(lokal), "--ut", str(tmp_path / "ut"), "--utan-signatur"])

    assert kod == 2
    assert "FEL: oväntat fel: ValueError: kaboom" in capsys.readouterr().err


# --- Punkt 8: --lokal hoppar över index som inte går att tolka, skiftlägesokänslig slutlig-markör ---

def test_valj_lokala_filer_hoppar_over_ogiltigt_index(tmp_path):
    for suffix in ("00_RD", "14_RF", "1480_KF"):
        (tmp_path / f"Test_{suffix}.zip").write_bytes(b"")
    (tmp_path / "index_1_ogiltig.md5").write_text("<html>404</html>", "utf-8")
    riktigt = "\n".join(
        f"{'0' * 32}  ./p/{kat}/Test_{suffix}.zip"
        for kat, suffix in (("rd", "00_RD"), ("rf", "14_RF"), ("kf", "1480_KF"))
    ) + "\n"
    (tmp_path / "index_2_giltig.md5").write_text(riktigt, "utf-8")

    index_text, index, urval = hm.valj_lokala_filer(tmp_path, "p")
    assert index is not None
    assert urval["kf"][1] == "0" * 32
    assert urval["rd"][0].endswith("Test_00_RD.zip")


@finns
def test_valj_lokala_filer_slutlig_saknar_rd_och_rf(tmp_path):
    with pytest.raises(hm.HamtFel):
        hm.valj_lokala_filer(GENREP, "s")


def test_valj_lokala_filer_slutlig_skiftlageokansligt(tmp_path):
    for suffix in ("00_RD", "14_RF", "1480_KF"):
        (tmp_path / f"X_Slutlig_{suffix}.zip").write_bytes(b"")
        (tmp_path / f"X_prelim_{suffix}.zip").write_bytes(b"")
    _, _, urval = hm.valj_lokala_filer(tmp_path, "s")
    assert urval["kf"][0].endswith("X_Slutlig_1480_KF.zip")


def test_valj_lokala_filer_varnar_om_index_saknar_fil(tmp_path, capsys):
    for suffix in ("00_RD", "14_RF", "1480_KF"):
        (tmp_path / f"X_{suffix}.zip").write_bytes(b"")
    (tmp_path / "index.md5").write_text(
        f"{'a' * 32}  ./p/rd/X_00_RD.zip\n{'b' * 32}  ./p/rf/X_14_RF.zip\n", "utf-8")
    # X_1480_KF.zip saknas avsiktligt i index.md5
    _, index, urval = hm.valj_lokala_filer(tmp_path, "p")
    err = capsys.readouterr().err
    assert "VARNING" in err and "X_1480_KF.zip" in err
    assert urval["kf"][1] is None


# --- Punkt 10: nyckelhämtning skriver till exakt --nyckel-sökvägen och sker före tidsstämpelmappen ---

def test_hamta_nyckel_skriver_till_exakt_sokvag(tmp_path, monkeypatch):
    def fake_hamta(url, timeout=30):
        return b"CERT-INNEHALL"

    class FakeResultat:
        returncode = 0
        stdout = "PUBLIK-NYCKEL\n"
        stderr = ""

    monkeypatch.setattr(hm, "hamta", fake_hamta)
    monkeypatch.setattr(hm.subprocess, "run", lambda *a, **k: FakeResultat())

    nyckel_path = tmp_path / "min-nyckel.pem"
    ut = hm.hamta_nyckel(nyckel_path)
    assert ut == nyckel_path
    assert nyckel_path.read_text("utf-8") == "PUBLIK-NYCKEL\n"
    assert (tmp_path / "val-sign-crt.pem").read_bytes() == b"CERT-INNEHALL"


def test_nyckelhamtning_fore_mapp_lamnar_ingen_tom_mapp(tmp_path, monkeypatch):
    lokal = tmp_path / "kalla"
    lokal.mkdir()
    for suffix in ("00_RD", "14_RF", "1480_KF"):
        (lokal / f"X_{suffix}.zip").write_bytes(_bygg_zip(suffix=suffix))
    ut = tmp_path / "ut"

    def fake_hamta(url, timeout=30):
        raise hm.HamtFel(f"{url}: nätverket är nere")
    monkeypatch.setattr(hm, "hamta", fake_hamta)

    kod = _huvud(["--lokal", str(lokal), "--ut", str(ut), "--nyckel", str(tmp_path / "ny-nyckel.pem")])

    assert kod == 1
    assert [p for p in ut.iterdir() if p.is_dir()] == []
