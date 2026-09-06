"""verktyg/forbered_tvaar.py bygger tvåårssidan: obligatoriska filer, valfria som får saknas, --kf-raknade."""
import json
import subprocess
import sys
from pathlib import Path

from scripts import schema

ROT = Path(__file__).resolve().parents[1]
SKRIPT = ROT / "verktyg" / "forbered_tvaar.py"


def _distrikt(kod, namn):
    return {"kod": kod, "namn": namn, "raknat": True,
            "rd": {"V": 300, "S": 200}, "rf": {"V": 280, "S": 210}, "kf": {"V": 260, "S": 220},
            "giltiga": {"rd": 500, "rf": 490, "kf": 480},
            "rostande": {"rd": 505, "rf": 495, "kf": 485},
            "rostberattigade": {"rd": 700, "rf": 700, "kf": 700}}


def _valnattsmapp(mapp, med_swing=True):
    """Minimal valnattsdata: fem distrikt, alla räknade i alla tre valen."""
    mapp.mkdir(parents=True, exist_ok=True)
    distrikt = [_distrikt(f"1480050{i}", f"Distrikt {i}") for i in range(1, 6)]
    schema.skriv(mapp / "valdata_2026", schema.bygg_valdata("2026", distrikt, status="preliminar"))
    if med_swing:
        schema.skriv(mapp / "swing_2026", {"bas": "2022", "majorna": {}, "distrikt": {}})
    return mapp


def _kor(kalla, ut, *extra):
    return subprocess.run([sys.executable, str(SKRIPT), "--valnatt-data", str(kalla), "--ut", str(ut), *extra],
                          cwd=ROT, capture_output=True, text=True)


def test_bygger_tradet_och_konfigen(tmp_path):
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--valnatt")
    assert r.returncode == 0, r.stdout + r.stderr
    for namn in ("index.html", "valgrafik.js", "valgrafik.css"):
        assert (ut / namn).exists(), namn
    for namn in ("distrikt_2022.js", "valdata_2022.js", "distrikt_2026.js", "valdata_2026.js", "swing_2026.js", "konfig.js"):
        assert (ut / "data" / namn).exists(), namn
    k = json.loads((ut / "data" / "konfig.json").read_text("utf-8"))
    assert k["ar"] == ["2022", "2026"] and k["standardAr"] == "2026" and k["valnatt"] is True


def test_utan_valnattsflaggan_star_valnatt_av(tmp_path):
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut)
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads((ut / "data" / "konfig.json").read_text("utf-8"))["valnatt"] is False


def test_saknad_swing_stoppar_inte_bygget(tmp_path):
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt", med_swing=False), ut)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (ut / "data" / "swing_2026.js").exists()
    assert "swing_2026.js" in r.stdout, "en valfri fil som saknas ska skrivas ut"


def test_kf_raknade_lamnar_kvar_exakt_tre_raknade_distrikt(tmp_path):
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--valnatt", "--kf-raknade", "3")
    assert r.returncode == 0, r.stdout + r.stderr
    valdata = schema.las_js(ut / "data" / "valdata_2026.js")
    raknade = [d for d in valdata["distrikt"] if d["kf"] and d["giltiga"].get("kf")]
    assert len(raknade) == 3, [d["kod"] for d in raknade]
    assert all(d["rd"] and d["giltiga"]["rd"] for d in valdata["distrikt"]), "riksdagsvalet ska vara orört"
    assert valdata["aggregat"]["majorna"]["kf"] == schema._summa(valdata["distrikt"], "kf")
    assert valdata["aggregat"]["majorna"]["kf"]["giltiga"] == 3 * 480
