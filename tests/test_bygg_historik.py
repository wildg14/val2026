import json
import math
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.bygg_historik import las_kedja, las_kedja_alla
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


@finns
def test_post_upptacker_inkonsekvent_antal_distrikt(tmp_path):
    kopia = tmp_path / "doktorerad_antal.sqlite"
    shutil.copy(DB, kopia)
    con = sqlite3.connect(kopia)
    con.execute("UPDATE tidsserie SET antal_distrikt = antal_distrikt + 1 WHERE ar=2022 AND val='rd' AND niva='majorna' AND parti='V'")
    con.commit()
    con.close()
    r = kor("historik", "--db", str(kopia), "--ut", str(tmp_path / "ut"))
    assert r.returncode != 0
    assert "FEL:" in r.stderr and "antal_distrikt" in r.stderr


@finns
def test_bygg_historik_upptacker_olika_metod_mellan_valen(tmp_path):
    kopia = tmp_path / "doktorerad_metod.sqlite"
    shutil.copy(DB, kopia)
    con = sqlite3.connect(kopia)
    con.execute("UPDATE tidsserie SET metod = REPLACE(metod, 'areametod', 'annanmetod') "
                "WHERE ar=2018 AND val='rd' AND niva='majorna'")
    con.commit()
    con.close()
    r = kor("historik", "--db", str(kopia), "--ut", str(tmp_path / "ut"))
    assert r.returncode != 0
    assert "FEL:" in r.stderr and "2018" in r.stderr


def test_oppna_saknad_tabell(tmp_path):
    tom = tmp_path / "tom.sqlite"
    sqlite3.connect(tom).close()
    r = kor("historik", "--db", str(tom), "--ut", str(tmp_path / "ut"))
    assert r.returncode == 1
    assert "FEL:" in r.stderr and "tidsserie" in r.stderr


def test_oppna_ej_sqlite_fil(tmp_path):
    fil = tmp_path / "text.sqlite"
    fil.write_text("detta är en vanlig textfil, inte en databas\n" * 50, encoding="utf-8")
    r = kor("historik", "--db", str(fil), "--ut", str(tmp_path / "ut"))
    assert r.returncode == 1
    assert "FEL:" in r.stderr


def test_oppna_saknad_fil(tmp_path):
    r = kor("historik", "--db", str(tmp_path / "finns_inte.sqlite"), "--ut", str(tmp_path / "ut"))
    assert r.returncode == 1
    assert "FEL:" in r.stderr


JAMFORBARA_2018 = {"14800526": "14801017", "14800536": "14801036", "14800537": "14801031", "14800538": "14801038", "14800539": "14801034",
                   "14800541": "14801032", "14800546": "14801041", "14800547": "14801035", "14800548": "14801042"}


@finns
def test_swing_2022_nio_jamforbara_och_omradesserien(tmp_path):
    r = kor("swing2022", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    s = json.loads((tmp_path / "swing_2022.json").read_text("utf-8"))
    assert s["ar"] == 2022 and s["bas"] == 2018
    assert sorted(s["distrikt"]) == sorted(JAMFORBARA_2018)
    assert len(s["ej_jamforbara"]) == 14
    assert s["ej_jamforbara"]["14800530"]["mening"] == "Gränserna såg annorlunda ut 2018. Siffrorna hör till det årets distrikt."
    assert s["ej_jamforbara"]["14800530"]["omradesrad"] is True
    for val in ("rd", "rf", "kf"):
        assert s["kohort"][val]["metod"] == "omradesserien"
        assert s["kohort"][val]["helomrade"] is True and s["kohort"][val]["antal"] == 23 and s["kohort"][val]["totalt"] == 23
        assert len(s["kohort"][val]["koder"]) == 23
    with db() as con:
        v22 = con.execute("SELECT roster, giltiga FROM tidsserie WHERE ar=2022 AND val='rd' AND niva='majorna' AND parti='V'").fetchone()
        v18 = con.execute("SELECT roster, giltiga FROM tidsserie WHERE ar=2018 AND val='rd' AND niva='majorna' AND parti='V'").fetchone()
        vantat = round((v22[0] / v22[1] - v18[0] / v18[1]) * 100, 1)
        assert s["majorna"]["rd"]["V"] == pytest.approx(vantat, abs=0.05)
        g22 = con.execute("SELECT r.roster, s.giltiga FROM roster r JOIN distrikt_summa s ON s.ar=r.ar AND s.val=r.val AND s.kod=r.kod "
                          "WHERE r.ar=2022 AND r.val='rd' AND r.kod='14800541' AND r.parti_kanon='V'").fetchone()
        g18 = con.execute("SELECT r.roster, s.giltiga FROM roster r JOIN distrikt_summa s ON s.ar=r.ar AND s.val=r.val AND s.kod=r.kod "
                          "WHERE r.ar=2018 AND r.val='rd' AND r.kod='14801032' AND r.parti_kanon='V'").fetchone()
        assert s["distrikt"]["14800541"]["rd"]["V"] == pytest.approx(round((g22[0] / g22[1] - g18[0] / g18[1]) * 100, 1), abs=0.05)
    assert r.stdout.count("14800541") >= 1, "skriptet skriver ut listan över jämförbara distrikt för avstämning"
    # Ingen efterhandsskrivning: majorna-nivån kommer ur schema.swing(samma_yta=True) på tidsseriens
    # aggregat, så Övriga är med (partiuppsättningarna är lika) och ingen negativ nolla förekommer.
    assert "Övriga" in s["majorna"]["rd"]
    for parti, varde in s["majorna"]["rd"].items():
        assert not (varde == 0.0 and math.copysign(1.0, varde) < 0), f"{parti}: negativ nolla"
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8")) if (tmp_path / "historik.json").exists() else None
    if hst is None:
        kor("historik", "--ut", str(tmp_path))
        hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    for val in ("rd", "rf", "kf"):
        assert set(s["majorna"][val]) == set(hst["meta"]["partier_per_val"][val])


@finns
def test_swing_2022_orsak_omritade_ar_ej_jamforbart_enligt_kallan(tmp_path):
    """De fjorton omritade har en 2018-motsvarighet i kedjefilen, källan säger bara att gränserna
    ändrats för mycket - orsaken ska alltså inte vara "saknas i basåret", som gäller distrikt som
    inte fanns alls."""
    r = kor("swing2022", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    s = json.loads((tmp_path / "swing_2022.json").read_text("utf-8"))
    assert len(s["ej_jamforbara"]) == 14
    for kod, post in s["ej_jamforbara"].items():
        assert post["orsak"] == "ej jämförbart enligt källan", f"{kod}: {post['orsak']}"


@finns
def test_swing_2022_ovriga_per_distrikt_godhem(tmp_path):
    r = kor("swing2022", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    s = json.loads((tmp_path / "swing_2022.json").read_text("utf-8"))
    with db() as con:
        def ovriga_andel(ar, kod):
            giltiga = con.execute(
                "SELECT giltiga FROM distrikt_summa WHERE ar=? AND val='rd' AND kod=?", (ar, kod)).fetchone()[0]
            platshallare = ",".join("?" * len(NYCKELPARTIER["rd"]))
            nyckelroster = con.execute(
                f"SELECT COALESCE(SUM(roster), 0) FROM roster WHERE ar=? AND val='rd' AND kod=? "
                f"AND parti_kanon IN ({platshallare})",
                (ar, kod, *NYCKELPARTIER["rd"])).fetchone()[0]
            return (giltiga - nyckelroster) / giltiga
        vantat = round((ovriga_andel(2022, "14800541") - ovriga_andel(2018, "14801032")) * 100, 1) + 0.0
    assert s["distrikt"]["14800541"]["rd"]["Övriga"] == pytest.approx(vantat, abs=0.05)


@finns
def test_distrikt_ur_db_giltiga_vakt_fyrar_pa_doktorerad_databas(tmp_path):
    kopia = tmp_path / "doktorerad_swing.sqlite"
    shutil.copy(DB, kopia)
    con = sqlite3.connect(kopia)
    con.execute("UPDATE distrikt_summa SET giltiga = giltiga + 1 WHERE ar=2018 AND val='rd' AND kod='14801032'")
    con.commit()
    con.close()
    r = kor("swing2022", "--db", str(kopia), "--ut", str(tmp_path / "ut"))
    assert r.returncode != 0
    assert "FEL:" in r.stderr and "giltiga" in r.stderr


@finns
def test_las_kedja_ger_nio_jamforbara():
    kedja = las_kedja()
    assert len(kedja) == 9
    assert set(kedja) == set(JAMFORBARA_2018)
    assert kedja == JAMFORBARA_2018


@finns
def test_las_kedja_alla_ger_tjugotre_med_dubbletter_tillatna():
    alla = las_kedja_alla()
    assert len(alla) == 23
    assert set(JAMFORBARA_2018.items()) <= set(alla.items())
    # 14800530 och 14800535 kommer båda ur 2018 års 14801011: distriktet delades vid omritningen 2022.
    assert alla["14800530"] == alla["14800535"] == "14801011"


def test_las_kedja_dubbel_kod_2018_bland_jamforbara_ger_fel(tmp_path):
    kedjefil = tmp_path / "kedja_doktorerad.csv"
    kedjefil.write_text(
        "kod_2022;kod_2018;jamforbar_tillbaka_till\n"
        "14800001;14801000;2018\n"
        "14800002;14801000;2018\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        las_kedja(kedjefil)


def test_las_kedja_bom_tolereras(tmp_path):
    kedjefil = tmp_path / "kedja_bom.csv"
    kedjefil.write_bytes(
        ("﻿" + "kod_2022;kod_2018;jamforbar_tillbaka_till\n14800001;14801000;2018\n").encode("utf-8"))
    assert las_kedja(kedjefil) == {"14800001": "14801000"}


def test_las_kedja_saknad_kolumn_ger_fel(tmp_path):
    kedjefil = tmp_path / "kedja_utan_kolumn.csv"
    kedjefil.write_text("kod_2022;kod_2018\n14800001;14801000\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        las_kedja(kedjefil)


def test_las_kedja_saknad_fil_ger_fel(tmp_path):
    with pytest.raises(SystemExit):
        las_kedja(tmp_path / "finns_inte.csv")
