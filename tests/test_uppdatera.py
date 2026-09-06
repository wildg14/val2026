import json
import subprocess
import sys
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parents[1]
RD = ROT / "Roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-riksdagsvalet-2022.xlsx"
RF = ROT / "roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-regionval-2022.xlsx"
KF = ROT / "roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-kommunval-2022.xlsx"
GENREP = Path("/Users/daniel/code/Temp/Historiska dokument/dl_webb/genrep2026")
JAMFORELSE = Path("/Users/daniel/code/Temp/Historiska dokument/dl_webb/2026/valdistrikt-jamforelser-mellan-2022-och-2026.xlsx")
genrep_finns = pytest.mark.skipif(not (GENREP / "index_genrep2026.md5").exists(), reason="genrep-filerna saknas")
EJ_JAMFORBARA = ["14800529", "14800530", "14800531", "14800532", "14800533", "14800534", "14800535", "14800538", "14800541"]


def kor(*args):
    return subprocess.run([sys.executable, "scripts/uppdatera_2026.py", *args], cwd=ROT, capture_output=True, text=True)


def hamta_lokalt(tmp_path):
    r = subprocess.run([sys.executable, "scripts/hamta_2026.py", "--lokal", str(GENREP), "--ut", str(tmp_path / "h"), "--utan-signatur"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return Path(r.stdout.strip().splitlines()[-1].split("MAPP: ", 1)[1])


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
    # xlsx-vägen får flaggor ur jämförelsefilen när den finns (--jamforelsefil), annars antas allt jämförbart
    assert "14800530" in s["ej_jamforbara"] or s["distrikt"].get("14800530", {}).get("rd", {}).get("V") == 0.0
    # 14800530 kan ha hamnat i ej_jamforbara i stället för distrikt (samma orsak som ovan)
    assert s["distrikt"].get("14800530", {}).get("kf") is None
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


@genrep_finns
def test_valnattsmapp_genrep_ger_komplett_valdata_swing_och_konfig(tmp_path):
    mapp = hamta_lokalt(tmp_path)
    ut = tmp_path / "data"
    ut.mkdir()
    (ut / "konfig.json").write_text(json.dumps({"ar": ["2022"], "standardAr": "2022", "valnatt": False, "adress": "x"}), "utf-8")
    r = kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026", "--status", "preliminar", "--tid", "2026-09-13T21:00:00", "--valnatt")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "TESTDATA" in r.stdout + r.stderr, "genrep-filerna har test: true och det ska synas"
    v = json.loads((ut / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["ar"] == 2026 and v["meta"]["status"] == "preliminar" and v["meta"]["test"] is True
    assert v["meta"]["valnatt"] == {"raknade": 23, "totalt": 23}
    d = {x["kod"]: x for x in v["distrikt"]}
    assert d["14800526"]["kf"]["V"] == 46 and d["14800526"]["rd"]["S"] == 275 and d["14800526"]["giltiga"]["kf"] == 905
    assert d["14800533"]["namn"] == "Sandarna"
    assert sum(1 for x in v["distrikt"] if x["jamforbar_mot_bas"]) == 14
    assert sorted(k for k, x in d.items() if x["grans_andrad"]) == EJ_JAMFORBARA
    assert v["aggregat"]["riket"]["rd"]["giltiga"] == 6877640 and v["aggregat"]["riket"]["rd"]["namn"] == "Riket"
    assert v["aggregat"]["riket"]["rf"]["namn"] == "Västra Götaland" and v["aggregat"]["goteborg"]["kf"]["giltiga"] == 403007
    assert sum(v["mandat"]["riksdag_verklig"].values()) == 349 and sum(v["mandat"]["riksdag_majorna"].values()) == 349
    s = json.loads((ut / "swing_2026.json").read_text("utf-8"))
    assert s["bas"] == 2022 and len(s["distrikt"]) == 14 and sorted(s["ej_jamforbara"]) == EJ_JAMFORBARA
    assert "ritades om till 2026" in s["ej_jamforbara"]["14800530"]["mening"]
    assert s["kohort"]["rd"]["helomrade"] is True and "V" in s["majorna"]["rd"]
    k = json.loads((ut / "konfig.json").read_text("utf-8"))
    assert k["ar"] == ["2022", "2026"] and k["standardAr"] == "2026" and k["valnatt"] is True and k["adress"] == "x"
    assert not list(ut.glob("*.tmp"))


@genrep_finns
def test_mindre_eller_tom_import_skriver_inte_over(tmp_path):
    mapp = hamta_lokalt(tmp_path)
    ut = tmp_path / "data"
    ut.mkdir()
    assert kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026").returncode == 0
    fore = (ut / "valdata_2026.json").read_bytes()
    bara_rd = tmp_path / "bara_rd"
    bara_rd.mkdir()
    (bara_rd / "rd").symlink_to(mapp / "rd")
    r = kor("--valnatt-mapp", str(bara_rd), "--ut", str(ut), "--ar", "2026")
    assert r.returncode != 0 and "färre räknade" in r.stdout + r.stderr
    assert (ut / "valdata_2026.json").read_bytes() == fore, "filen får inte röras"
    r = kor("--valnatt-mapp", str(bara_rd), "--ut", str(ut), "--ar", "2026", "--tvinga")
    assert r.returncode == 0 and (ut / "valdata_2026.json").read_bytes() != fore


@pytest.mark.skipif(not JAMFORELSE.exists(), reason="Valmyndighetens jämförelsefil saknas")
def test_csv_vagen_far_flaggor_ur_jamforelsefilen(tmp_path):
    csv = tmp_path / "v.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;S;200\nrd;14800530;giltiga;500\nrd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026", "--jamforelsefil", str(JAMFORELSE))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2026.json").read_text("utf-8"))
    d = {x["kod"]: x for x in v["distrikt"]}
    assert d["14800530"]["grans_andrad"] is True and d["14800526"]["grans_andrad"] is False
    s = json.loads((tmp_path / "swing_2026.json").read_text("utf-8"))
    assert "14800530" in s["ej_jamforbara"] and s["distrikt"] == {}


def test_utan_jamforbarhet_varnar_och_antar_alla(tmp_path):
    csv = tmp_path / "v.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;S;200\nrd;14800530;giltiga;500\nrd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026", "--jamforelsefil", str(tmp_path / "finns-inte.xlsx"))
    assert r.returncode == 0
    assert "jämförbarhet" in (r.stdout + r.stderr).lower()


@genrep_finns
def test_hamta_bygger_argv_fullstandigt_och_nollstaller_globalt_tillstand(tmp_path, monkeypatch, capsys):
    """--hamta körs aldrig mot nätet i tester: scripts.uppdatera_2026 importeras som modul och
    hamta_2026.main monkeypatchas. Samma import används för att köra JSON-vägen två gånger i
    samma process, för att visa att VARNINGAR, JAMFORBAR och META_TEST nollställs mellan anrop."""
    from scripts import uppdatera_2026

    mapp = hamta_lokalt(tmp_path)
    ut = tmp_path / "data"
    ut.mkdir()

    sparat_argv = sys.argv
    try:
        sys.argv = ["uppdatera_2026.py", "--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026"]
        assert uppdatera_2026.main() == 0
        varningar_forsta = len(uppdatera_2026.VARNINGAR)
        assert uppdatera_2026.main() == 0
        assert len(uppdatera_2026.VARNINGAR) == varningar_forsta, "varningar ska nollställas mellan anrop i samma process"

        sett = {}

        def attrapp_kod3():
            sett["argv"] = list(sys.argv)
            return 3

        monkeypatch.setattr(uppdatera_2026.hamta_2026, "main", attrapp_kod3)
        ut2 = tmp_path / "hamta-ut"
        sys.argv = ["uppdatera_2026.py", "--hamta", "--ut", str(ut2), "--ar", "2026"]
        assert uppdatera_2026.main() == 3
        argv = sett["argv"]
        assert argv[argv.index("--tillfalle") + 1] == "p"
        assert "--bara-om-nytt" in argv
        assert argv[argv.index("--ut") + 1] == str(ut2 / "valnatt")

        def attrapp_fel():
            raise RuntimeError("x")

        monkeypatch.setattr(uppdatera_2026.hamta_2026, "main", attrapp_fel)
        sys.argv = ["uppdatera_2026.py", "--hamta", "--ut", str(ut2), "--ar", "2026"]
        with pytest.raises(SystemExit):
            uppdatera_2026.main()
        utskrift = capsys.readouterr()
        assert "hämtningen misslyckades" in utskrift.out + utskrift.err
    finally:
        sys.argv = sparat_argv
