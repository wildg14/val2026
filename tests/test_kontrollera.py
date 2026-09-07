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
    if not (ROT / "data" / "historik.json").exists():
        pytest.skip("bygg historik.json först")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", "data/historik.json"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "historik" in r.stdout.lower()


def test_kontrollera_historik_upptacker_manipulerad_serie(tmp_path):
    src = ROT / "data" / "historik.json"
    if not src.exists():
        pytest.skip("bygg historik.json först")
    hst = json.loads(src.read_text("utf-8"))
    rad = [p for p in hst["serie"]["rd"]["majorna"] if p["ar"] == 2022][0]
    rad["roster"]["V"] += 1
    p = tmp_path / "historik.json"
    p.write_text(json.dumps(hst), "utf-8")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", str(p)],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode != 0 and "historik rd V" in r.stdout + r.stderr
