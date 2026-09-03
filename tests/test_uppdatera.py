import json
import subprocess
import sys
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parents[1]
RD = ROT / "Roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-riksdagsvalet-2022.xlsx"
RF = ROT / "roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-regionval-2022.xlsx"
KF = ROT / "roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-kommunval-2022.xlsx"


def kor(*args):
    return subprocess.run([sys.executable, "scripts/uppdatera_2026.py", *args], cwd=ROT, capture_output=True, text=True)


@pytest.mark.skipif(not RD.exists(), reason="rådatafil saknas")
def test_bara_rd_ger_tomma_rf_kf_och_swing(tmp_path):
    r = kor("--rd", str(RD), "--ut", str(tmp_path), "--ar", "2026", "--status", "preliminar", "--tid", "2026-09-13T20:45:00")
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["ar"] == 2026 and v["meta"]["status"] == "preliminar"
    assert v["meta"]["uppdaterad"] == "2026-09-13T20:45:00"
    assert v["meta"]["valnatt"] == {"raknade": 23, "totalt": 23}
    d = {x["kod"]: x for x in v["distrikt"]}["14800530"]
    assert d["rd"]["V"] == 287 and d["rf"] == {} and d["kf"] == {}
    assert v["aggregat"]["majorna"]["rd"]["giltiga"] == 21308
    assert v["aggregat"]["riket"]["rd"]["andel"]["S"] == pytest.approx(0.3032545689, abs=1e-9)
    assert v["mandat"]["riksdag_majorna"] == {"V": 99, "S": 94, "MP": 57, "SD": 37, "M": 32, "C": 15, "L": 15}
    assert v["mandat"].get("riksdag_verklig", {}) == {}
    s = json.loads((tmp_path / "swing_2026.json").read_text("utf-8"))
    assert s["bas"] == 2022 and s["ar"] == 2026
    assert s["distrikt"]["14800530"]["rd"]["V"] == 0.0
    assert s["distrikt"]["14800530"].get("kf") is None
    assert (tmp_path / "valdata_2026.js").exists() and (tmp_path / "swing_2026.js").exists()


def test_csv_reservvag(tmp_path):
    csv = tmp_path / "valnatt.csv"
    csv.write_text("val;kod;parti;roster\n"
                   "rd;14800530;V;300\nrd;14800530;S;200\nrd;14800530;giltiga;500\n"
                   "rd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026")
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["valnatt"] == {"raknade": 1, "totalt": 23}
    d = {x["kod"]: x for x in v["distrikt"]}
    assert d["14800530"]["rd"] == {"V": 300, "S": 200} and d["14800530"]["raknat"] is True
    assert d["14800526"]["raknat"] is False and d["14800526"]["rd"] == {}
    assert v["aggregat"]["majorna"]["rd"]["giltiga"] == 500


def test_csv_med_felaktig_summa_avbryter(tmp_path):
    csv = tmp_path / "fel.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;giltiga;500\nrd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026")
    assert r.returncode != 0
    assert "14800530" in r.stdout + r.stderr


def test_fel_format_avbryter(tmp_path):
    r = kor("--rd", str(ROT / "majorna-valresultat-2022.xlsx"), "--ut", str(tmp_path), "--ar", "2026")
    assert r.returncode != 0
    assert "roster_" in r.stdout + r.stderr


@pytest.mark.skipif(not (RD.exists() and RF.exists() and KF.exists()), reason="rådatafiler saknas")
def test_repetera_mot_2022():
    r = kor("--repetera")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "REPETITION OK" in r.stdout
