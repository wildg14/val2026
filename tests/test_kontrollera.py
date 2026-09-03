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
