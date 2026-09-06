import json
import subprocess
import sys
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parents[1]


def test_bygg_data_skriver_filer_och_mandat(tmp_path):
    r = subprocess.run([sys.executable, "scripts/bygg_data.py", "--ut", str(tmp_path), "--utan-rafiler"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2022.json").read_text("utf-8"))
    assert v["meta"]["ar"] == 2022 and v["meta"]["status"] == "slutlig"
    assert len(v["distrikt"]) == 23 and all(d["raknat"] for d in v["distrikt"])
    assert v["mandat"]["riksdag_majorna"] == {"V": 99, "S": 94, "MP": 57, "SD": 37, "M": 32, "C": 15, "L": 15}
    assert v["mandat"]["riksdag_verklig"] == {"S": 107, "SD": 73, "M": 68, "V": 24, "C": 24, "KD": 19, "MP": 18, "L": 16}
    assert v["mandat"]["metod"].startswith("Räkneexempel")
    assert v["aggregat"]["majorna"]["rd"]["giltiga"] == 21308
    assert v["aggregat"]["riket"]["rd"]["valdeltagande"] == pytest.approx(0.842118659, abs=1e-9)
    assert v["aggregat"]["riket"]["rf"]["namn"] == "Västra Götaland"
    assert v["aggregat"]["goteborg"]["kf"]["andel"]["V"] == pytest.approx(0.1582096615, abs=1e-9)
    g = json.loads((tmp_path / "distrikt_2022.geojson").read_text("utf-8"))
    assert len(g["features"]) == 23
    for namn in ("valdata_2022.js", "distrikt_2022.js"):
        assert (tmp_path / namn).exists()
    assert "OK" in r.stdout
