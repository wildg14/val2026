"""verktyg/forbered_tvaar.py bygger tvåårssidan: obligatoriska filer, valfria som får saknas, --kf-raknade, --partiell, --status, --utan-parti."""
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


def _valnattsmapp(mapp, med_swing=True, kalla=None):
    """Minimal valnattsdata: fem distrikt, alla räknade i alla tre valen.

    Koderna är Majornas fem första, så att distrikten finns i data/valdata_2022.json och swingen går
    att räkna om när --kf-raknade doktorerar kommunvalet."""
    mapp.mkdir(parents=True, exist_ok=True)
    distrikt = [_distrikt(f"148005{25 + i}", f"Distrikt {i}") for i in range(1, 6)]
    schema.skriv(mapp / "valdata_2026", schema.bygg_valdata("2026", distrikt, status="preliminar", kalla=kalla))
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


def test_kf_raknade_raknar_om_swingens_kohort(tmp_path):
    """Kortets kohorttext ska säga hur många jämförbara distrikt talen vilar på, även på testsidan."""
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--valnatt", "--kf-raknade", "3")
    assert r.returncode == 0, r.stdout + r.stderr
    swing = schema.las_js(ut / "data" / "swing_2026.js")
    assert swing["kohort"]["kf"]["antal"] == 3 and swing["kohort"]["kf"]["totalt"] == 5
    assert swing["kohort"]["kf"]["helomrade"] is False
    assert swing["kohort"]["rd"]["antal"] == 5, "riksdagsvalet är orört, alla fem distrikten ingår"
    assert swing["bas"] == 2022 and swing["majorna"]["kf"], "swingen är omräknad, inte stubben ur valnattsmappen"


def test_saknad_obligatorisk_fil_avbryter(tmp_path):
    tom = tmp_path / "tom"
    tom.mkdir()
    r = _kor(tom, tmp_path / "ut")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "valdata_2026.js saknas" in r.stderr


def test_kf_raknade_over_antalet_distrikt_avbryter(tmp_path):
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), tmp_path / "ut", "--kf-raknade", "99")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "men filen har" in r.stderr


def test_negativt_kf_raknade_avbryter_utan_att_tomma_utmappen(tmp_path):
    ut = tmp_path / "ut"
    ut.mkdir()
    (ut / "gammal.txt").write_text("en tidigare testsida", "utf-8")
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--kf-raknade", "-1")
    assert r.returncode != 0, r.stdout + r.stderr
    assert "negativt" in r.stderr
    assert (ut / "gammal.txt").exists(), "argumentfelet ska fångas innan --ut töms"


def test_status_slutlig_skriver_om_metastatus(tmp_path):
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--status", "slutlig")
    assert r.returncode == 0, r.stdout + r.stderr
    valdata = schema.las_js(ut / "data" / "valdata_2026.js")
    assert valdata["meta"]["status"] == "slutlig"
    assert len(valdata["distrikt"]) == 5, "bara status ska ändras"
    assert json.loads((ut / "data" / "konfig.json").read_text("utf-8"))["valnatt"] is False


def test_status_tillsammans_med_kf_raknade(tmp_path):
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--kf-raknade", "2", "--status", "preliminar")
    assert r.returncode == 0, r.stdout + r.stderr
    valdata = schema.las_js(ut / "data" / "valdata_2026.js")
    assert valdata["meta"]["status"] == "preliminar"
    assert len([d for d in valdata["distrikt"] if d["kf"]]) == 2, "doktoreringen av kf ska överleva statusbytet"


def test_utan_parti_tar_bort_partiet_ur_swingen(tmp_path):
    """Testsidan ska kunna visa ett parti som inte redovisas båda åren: kortet hoppar då över det."""
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--valnatt", "--kf-raknade", "5", "--utan-parti", "V")
    assert r.returncode == 0, r.stdout + r.stderr
    swing = schema.las_js(ut / "data" / "swing_2026.js")
    for kod, post in swing["distrikt"].items():
        assert all("V" not in tal for tal in post.values()), kod
        assert any("S" in tal for tal in post.values()), f"{kod}: bara V skulle tas bort"
    assert all("V" not in tal for tal in swing["majorna"].values())
    assert any("S" in tal for tal in swing["majorna"].values()), "områdesnivån ska ha kvar övriga partier"
    assert "V borttaget" in r.stdout


def test_utan_parti_som_inte_finns_avbryter(tmp_path):
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), tmp_path / "ut", "--kf-raknade", "5", "--utan-parti", "XYZ")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "finns inte i swing_2026.js" in r.stderr


def test_utan_parti_utan_swingfil_avbryter(tmp_path):
    r = _kor(_valnattsmapp(tmp_path / "valnatt", med_swing=False), tmp_path / "ut", "--utan-parti", "V")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "kräver swing_2026.js" in r.stderr


def test_okand_status_avbryter(tmp_path):
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), tmp_path / "ut", "--status", "nastan")
    assert r.returncode != 0, r.stdout + r.stderr
    assert "--status" in r.stderr


def test_partiell_lamnar_kvar_exakt_tre_raknade_distrikt(tmp_path):
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--valnatt", "--partiell", "3")
    assert r.returncode == 0, r.stdout + r.stderr
    valdata = schema.las_js(ut / "data" / "valdata_2026.js")
    raknade = [d for d in valdata["distrikt"] if d["raknat"]]
    orakn = [d for d in valdata["distrikt"] if not d["raknat"]]
    assert len(raknade) == 3, [d["kod"] for d in valdata["distrikt"]]
    assert all(d["rd"] and d["rf"] and d["kf"] and d["giltiga"]["rd"] and d["giltiga"]["rf"] and d["giltiga"]["kf"] for d in raknade)
    assert len(orakn) == 2
    assert all(not d["rd"] and not d["rf"] and not d["kf"] for d in orakn)
    assert valdata["meta"]["valnatt"]["raknade"] == 3
    assert valdata["aggregat"]["majorna"]["rd"]["giltiga"] == 3 * 500
    assert valdata["meta"]["status"] == "preliminar", "status ska stå kvar oförändrad"


def test_partiell_raknar_om_swingens_kohort(tmp_path):
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--valnatt", "--partiell", "3")
    assert r.returncode == 0, r.stdout + r.stderr
    swing = schema.las_js(ut / "data" / "swing_2026.js")
    for val in ("rd", "rf", "kf"):
        assert swing["kohort"][val]["antal"] == 3 and swing["kohort"][val]["totalt"] == 5, val
        assert swing["kohort"][val]["helomrade"] is False, val


def test_partiell_over_antalet_distrikt_avbryter(tmp_path):
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), tmp_path / "ut", "--partiell", "99")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "men filen har" in r.stderr


def test_partiell_och_kf_raknade_kan_inte_kombineras(tmp_path):
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), tmp_path / "ut", "--partiell", "3", "--kf-raknade", "2")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "kan inte kombineras" in r.stderr


def test_partiell_noll_ger_inga_raknade_distrikt(tmp_path):
    ut = tmp_path / "ut"
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), ut, "--valnatt", "--partiell", "0")
    assert r.returncode == 0, r.stdout + r.stderr
    valdata = schema.las_js(ut / "data" / "valdata_2026.js")
    assert all(not d["raknat"] for d in valdata["distrikt"])
    assert valdata["meta"]["valnatt"]["raknade"] == 0


def test_status_slutlig_byter_ordet_i_kallan(tmp_path):
    """Källan i Om siffrorna säger vilken räkning talen kommer ur; statusbytet ska ta med den."""
    ut = tmp_path / "ut"
    kalla = "Valmyndigheten, preliminär rösträkning per valdistrikt 2026"
    r = _kor(_valnattsmapp(tmp_path / "valnatt", kalla=kalla), ut, "--status", "slutlig")
    assert r.returncode == 0, r.stdout + r.stderr
    valdata = schema.las_js(ut / "data" / "valdata_2026.js")
    assert valdata["meta"]["kalla"] == "Valmyndigheten, slutlig rösträkning per valdistrikt 2026"


def test_status_preliminar_byter_tillbaka_ordet_i_kallan(tmp_path):
    ut = tmp_path / "ut"
    kalla = "Valmyndigheten, slutlig rösträkning per valdistrikt 2026"
    r = _kor(_valnattsmapp(tmp_path / "valnatt", kalla=kalla), ut, "--status", "preliminar")
    assert r.returncode == 0, r.stdout + r.stderr
    valdata = schema.las_js(ut / "data" / "valdata_2026.js")
    assert valdata["meta"]["kalla"] == "Valmyndigheten, preliminär rösträkning per valdistrikt 2026"


def test_status_lamnar_en_kalla_utan_rakningsord_orord(tmp_path):
    ut = tmp_path / "ut"
    kalla = "Valmyndigheten, xlsx per valdistrikt 2022"
    r = _kor(_valnattsmapp(tmp_path / "valnatt", kalla=kalla), ut, "--status", "slutlig")
    assert r.returncode == 0, r.stdout + r.stderr
    valdata = schema.las_js(ut / "data" / "valdata_2026.js")
    assert valdata["meta"]["kalla"] == kalla


def test_partiell_tal_en_valdatafil_utan_valnattsblock(tmp_path):
    """Äldre vägar skriver ingen meta.valnatt; --partiell ska då lägga till blocket i stället för att krascha."""
    mapp = _valnattsmapp(tmp_path / "valnatt")
    valdata = schema.las_js(mapp / "valdata_2026.js")
    valdata["meta"].pop("valnatt")
    schema.skriv_js(mapp / "valdata_2026", valdata)
    ut = tmp_path / "ut"
    r = _kor(mapp, ut, "--valnatt", "--partiell", "2")
    assert r.returncode == 0, r.stdout + r.stderr
    ny = schema.las_js(ut / "data" / "valdata_2026.js")
    assert ny["meta"]["valnatt"] == {"raknade": 2, "totalt": 5}


def _med_riket(mapp, antal=6626, totalt=6626):
    """Lägger ett riksaggregat i fixturens valdata_2026, som genrepsfilerna har men fixturen saknar."""
    valdata = schema.las_js(mapp / "valdata_2026.js")
    valdata.setdefault("aggregat", {}).setdefault("riket", {})["rd"] = {
        "namn": "Riket", "giltiga": 100, "rostande": 110, "rostberattigade": 120,
        "andel": {"V": 0.1, "S": 0.3}, "antal_distrikt": antal, "totalt_distrikt": totalt}
    schema.skriv(mapp / "valdata_2026", valdata)
    return mapp


def test_riket_delvis_skruvar_ned_antalet_raknade(tmp_path):
    """Ett delvis räknat riket går inte att pröva ur genrepsdatan, som alltid är färdigräknad."""
    ut = tmp_path / "ut"
    kalla = _med_riket(_valnattsmapp(tmp_path / "valnatt"))
    r = _kor(kalla, ut, "--valnatt", "--riket-delvis", "4012")
    assert r.returncode == 0, r.stdout + r.stderr
    post = schema.las_js(ut / "data" / "valdata_2026.js")["aggregat"]["riket"]["rd"]
    assert post["antal_distrikt"] == 4012 and post["totalt_distrikt"] == 6626
    assert post["andel"] == {"V": 0.1, "S": 0.3}, "andelarna rörs inte"
    assert "4012 av 6626" in r.stdout


def test_riket_delvis_utan_riksaggregat_avbryter(tmp_path):
    r = _kor(_valnattsmapp(tmp_path / "valnatt"), tmp_path / "ut", "--riket-delvis", "10")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "saknar aggregat.riket.rd" in r.stderr


def test_riket_delvis_over_antalet_distrikt_avbryter(tmp_path):
    kalla = _med_riket(_valnattsmapp(tmp_path / "valnatt"), totalt=6626)
    r = _kor(kalla, tmp_path / "ut", "--riket-delvis", "9999")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "men riket har 6626 distrikt" in r.stderr
