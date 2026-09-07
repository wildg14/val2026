import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.valmyndigheten import NYCKELPARTIER

ROT = Path(__file__).resolve().parents[1]
DB = ROT / "data" / "historik" / "majorna_historik.sqlite"
finns = pytest.mark.skipif(not DB.exists(), reason="historikdatabasen saknas, bygg med scripts/historik/bygg_databas.py")
PARTIER = ["V", "S", "MP", "SD", "M", "C", "L", "KD", "D", "FI", "K", "Övriga"]


def kor(*args):
    return subprocess.run([sys.executable, "scripts/bygg_historik.py", *args], cwd=ROT, capture_output=True, text=True)


def db():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


@finns
def test_historik_json_form_och_summor(tmp_path):
    r = kor("historik", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    assert hst["meta"]["ar"] == [2006, 2010, 2014, 2018, 2022] and hst["meta"]["partier"] == PARTIER
    assert set(hst["serie"]) == {"rd", "rf", "kf"} and set(hst["serie"]["rd"]) == {"majorna", "goteborg", "riket"}
    for val, nivaer in hst["serie"].items():
        for niva, rader in nivaer.items():
            assert [p["ar"] for p in rader] == [2006, 2010, 2014, 2018, 2022], f"{val} {niva}"
            for p in rader:
                assert set(p["roster"]) == set(NYCKELPARTIER[val]) | {"Övriga"}
                assert sum(p["roster"].values()) == p["giltiga"], f"{val} {niva} {p['ar']}: partiernas röster ska summera till giltiga"
                for q in p["roster"]:
                    assert p["andel"][q] == pytest.approx(p["roster"][q] / p["giltiga"])
                if p["rostberattigade"]:
                    assert p["valdeltagande"] == pytest.approx(p["rostande"] / p["rostberattigade"])
    m = {p["ar"]: p for p in hst["serie"]["rd"]["majorna"]}
    assert m[2006]["roster"]["V"] == 3225 and m[2006]["giltiga"] == 18803 and m[2006]["antal_distrikt"] == 17
    assert m[2022]["roster"]["V"] == 5793 and m[2022]["antal_distrikt"] == 23
    assert m[2022]["valdeltagande"] == pytest.approx(0.8276, abs=0.0001)
    assert hst["serie"]["rd"]["goteborg"][4]["valdeltagande"] == pytest.approx(0.8071, abs=0.0001)
    assert hst["serie"]["rd"]["goteborg"][0]["antal_distrikt"] is None
    assert (tmp_path / "historik.js").exists() and (tmp_path / "historik.json").stat().st_size < 60000


@finns
def test_historik_2022_ar_identisk_med_valdata_2022(tmp_path):
    kor("historik", "--ut", str(tmp_path))
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    v = json.loads((ROT / "data" / "valdata_2022.json").read_text("utf-8"))
    for val in ("rd", "rf", "kf"):
        h = [p for p in hst["serie"][val]["majorna"] if p["ar"] == 2022][0]
        agg = v["aggregat"]["majorna"][val]
        for p, n in agg["roster"].items():
            assert h["roster"][p] == n, f"{val} {p}"
        assert h["giltiga"] == agg["giltiga"] and h["rostande"] == agg["rostande"] and h["rostberattigade"] == agg["rostberattigade"]


@finns
def test_historik_ovriga_foljer_sidans_partiuppsattning(tmp_path):
    kor("historik", "--ut", str(tmp_path))
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    con = db()
    rader = con.execute(
        "SELECT parti, roster FROM tidsserie WHERE ar=2014 AND val='rd' AND niva='majorna' AND parti IN ('SUMMA_ÖVRIGA', 'FI')"
    ).fetchall()
    vantat = sum(r[1] for r in rader)
    post = [p for p in hst["serie"]["rd"]["majorna"] if p["ar"] == 2014][0]
    assert post["roster"]["Övriga"] == vantat
    for p in hst["serie"]["rd"]["majorna"]:
        assert "FI" not in p["roster"]
    for p in hst["serie"]["rf"]["majorna"]:
        assert "FI" in p["roster"]


@finns
def test_historik_utelamnar_2002_och_smapartier(tmp_path):
    kor("historik", "--ut", str(tmp_path))
    text = (tmp_path / "historik.json").read_text("utf-8")
    assert '"ar": 2002' not in text and "SUMMA_ÖVRIGA" not in text and "PP" not in text


@finns
def test_historik_partier_per_val(tmp_path):
    kor("historik", "--ut", str(tmp_path))
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    ppv = hst["meta"]["partier_per_val"]
    assert list(ppv) == ["rd", "rf", "kf"]
    for val in ("rd", "rf", "kf"):
        assert ppv[val] == NYCKELPARTIER[val] + ["Övriga"]
    assert len(ppv["rd"]) == 9 and ppv["rd"][-1] == "Övriga"
    for val, nivaer in hst["serie"].items():
        for niva, rader in nivaer.items():
            for p in rader:
                assert set(p["roster"]) == set(ppv[val]), f"{val} {niva} {p['ar']}"


@finns
def test_historik_metod_deterministisk(tmp_path):
    kor("historik", "--ut", str(tmp_path))
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    metod = hst["meta"]["metod"]
    assert set(metod) == {"2006", "2010", "2014", "2018", "2022"}
    for ar, m in metod.items():
        assert isinstance(m, str) and m, f"{ar}: metod saknas eller tom"


@finns
def test_historik_valdeltagande_finns_antal_distrikt_bara_majorna(tmp_path):
    kor("historik", "--ut", str(tmp_path))
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    for val, nivaer in hst["serie"].items():
        for niva, rader in nivaer.items():
            for p in rader:
                assert p["valdeltagande"] is not None, f"{val} {niva} {p['ar']}: valdeltagande saknas"
                if niva in ("goteborg", "riket"):
                    assert p["antal_distrikt"] is None, f"{val} {niva} {p['ar']}: antal_distrikt ska vara null"


@finns
def test_post_upptacker_inkonsekventa_gruppvarden(tmp_path):
    kopia = tmp_path / "doktorerad.sqlite"
    shutil.copy(DB, kopia)
    con = sqlite3.connect(kopia)
    con.execute("UPDATE tidsserie SET giltiga = giltiga + 1 WHERE ar=2022 AND val='rd' AND niva='majorna' AND parti='V'")
    con.commit()
    con.close()
    r = kor("historik", "--db", str(kopia), "--ut", str(tmp_path / "ut"))
    assert r.returncode != 0
    assert "FEL:" in r.stderr and "giltiga" in r.stderr


def test_oppna_saknad_tabell(tmp_path):
    tom = tmp_path / "tom.sqlite"
    sqlite3.connect(tom).close()
    r = kor("historik", "--db", str(tom), "--ut", str(tmp_path / "ut"))
    assert r.returncode == 1
    assert "FEL:" in r.stderr and "tidsserie" in r.stderr


def test_oppna_saknad_fil(tmp_path):
    r = kor("historik", "--db", str(tmp_path / "finns_inte.sqlite"), "--ut", str(tmp_path / "ut"))
    assert r.returncode == 1
    assert "FEL:" in r.stderr
