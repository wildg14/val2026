import json
import subprocess
import sys
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parents[1]
SRC = ROT / "data" / "valdata_2022.json"


def kor(*args):
    return subprocess.run([sys.executable, "scripts/kontrollera.py", *args], cwd=ROT, capture_output=True, text=True)


@pytest.mark.skipif(not SRC.exists(), reason="bygg data först")
def test_kontrollera_upptacker_manipulerad_siffra(tmp_path):
    v = json.loads(SRC.read_text("utf-8"))
    v["distrikt"][3]["rd"]["V"] += 1
    p = tmp_path / "valdata_2022.json"
    p.write_text(json.dumps(v), "utf-8")
    r = kor(str(p), "majorna-valresultat-2022.xlsx")
    assert r.returncode != 0
    assert "14800529" in r.stdout + r.stderr


@pytest.mark.skipif(not SRC.exists(), reason="bygg data först")
def test_kontrollera_godkanner_riktig_fil():
    r = kor(str(SRC), "majorna-valresultat-2022.xlsx")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK" in r.stdout


def test_kontrollera_historik_godkanner_riktig_fil():
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", "data/historik.json"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "historik" in r.stdout.lower()


def test_kontrollera_historik_upptacker_manipulerad_serie(tmp_path):
    src = ROT / "data" / "historik.json"
    hst = json.loads(src.read_text("utf-8"))
    rad = [p for p in hst["serie"]["rd"]["majorna"] if p["ar"] == 2022][0]
    rad["roster"]["V"] += 1
    p = tmp_path / "historik.json"
    p.write_text(json.dumps(hst), "utf-8")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", str(p)],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode != 0 and "historik rd V" in r.stdout + r.stderr


def test_kontrollera_historik_fil_saknas(tmp_path):
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx",
                        "--historik", str(tmp_path / "finns_inte.json")],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1
    assert "DIFF historik:" in r.stdout and "saknas eller går inte att läsa" in r.stdout
    assert "Traceback" not in r.stderr


def test_kontrollera_historik_trasig_json(tmp_path):
    p = tmp_path / "trasig.json"
    p.write_text("{inte giltig json", encoding="utf-8")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", str(p)],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1
    assert "DIFF historik:" in r.stdout and "saknas eller går inte att läsa" in r.stdout
    assert "Traceback" not in r.stderr


def test_kontrollera_historik_fil_utan_serie_eller_meta(tmp_path):
    p = tmp_path / "utan_nycklar.json"
    p.write_text(json.dumps({"nagot_annat": True}), encoding="utf-8")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", str(p)],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1
    assert "DIFF historik:" in r.stdout and "saknas eller går inte att läsa" in r.stdout
    assert "Traceback" not in r.stderr


def test_kontrollera_historik_extra_parti_i_serien_ger_diff(tmp_path):
    src = ROT / "data" / "historik.json"
    hst = json.loads(src.read_text("utf-8"))
    rad = [p for p in hst["serie"]["rd"]["majorna"] if p["ar"] == 2022][0]
    rad["roster"]["FI"] = 23
    p = tmp_path / "historik.json"
    p.write_text(json.dumps(hst), "utf-8")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", str(p)],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode != 0 and "historik rd FI" in r.stdout + r.stderr


def test_kontrollera_historik_ar_saknas_ger_tre_diffrader(tmp_path):
    src = ROT / "data" / "historik.json"
    hst = json.loads(src.read_text("utf-8"))
    for val in hst["serie"]:
        hst["serie"][val]["majorna"] = [p for p in hst["serie"][val]["majorna"] if p["ar"] != 2022]
    p = tmp_path / "historik.json"
    p.write_text(json.dumps(hst), "utf-8")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", str(p)],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode != 0
    diffrader = [rad for rad in (r.stdout + r.stderr).splitlines() if rad.startswith("DIFF historik") and "saknas i serien" in rad]
    assert len(diffrader) == 3
