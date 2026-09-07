import json
import math
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import linemerge, transform as geo_transform, unary_union

from scripts import bygg_historik, geo
from scripts.bygg_historik import _las_kedja_rader, bygg_geo, las_kedja, las_kedja_alla, partier_med_rader
from scripts.mandat import jamkade_uddatal
from scripts.valmyndigheten import NYCKELPARTIER

ROT = Path(__file__).resolve().parents[1]
DB = ROT / "data" / "historik" / "majorna_historik.sqlite"
finns = pytest.mark.skipif(not DB.exists(), reason="historikdatabasen saknas, bygg med scripts/historik/bygg_databas.py")
RAFIL_2006 = ROT / "data" / "historik" / "distrikt_2006_majornaomradet.geojson"
PARTIER = ["V", "S", "MP", "SD", "M", "C", "L", "KD", "D", "FI", "K", "Övriga"]


def kor(*args):
    return subprocess.run([sys.executable, "scripts/bygg_historik.py", *args], cwd=ROT, capture_output=True, text=True)


def db():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


@pytest.fixture(scope="module")
def geo2006(tmp_path_factory):
    """Bygger distrikt_2006.geojson/.js en gång för hela testmodulen, i en tmp-mapp - varje kor()
    startar en egen Python-process, och flera 2006-tester behöver bara läsa samma byggda filer."""
    ut = tmp_path_factory.mktemp("geo2006")
    r = kor("geo2006", "--ut", str(ut))
    assert r.returncode == 0, r.stdout + r.stderr
    return ut


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
    r = kor("historik", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
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
    r = kor("historik", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
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
    r = kor("historik", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    text = (tmp_path / "historik.json").read_text("utf-8")
    assert '"ar": 2002' not in text and "SUMMA_ÖVRIGA" not in text and "PP" not in text


@finns
def test_historik_partier_per_val(tmp_path):
    r = kor("historik", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
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
    r = kor("historik", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    metod = hst["meta"]["metod"]
    assert set(metod) == {"2006", "2010", "2014", "2018", "2022"}
    for ar, m in metod.items():
        assert isinstance(m, str) and m, f"{ar}: metod saknas eller tom"


@finns
def test_historik_valdeltagande_finns_antal_distrikt_bara_majorna(tmp_path):
    r = kor("historik", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
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
        r2 = kor("historik", "--ut", str(tmp_path))
        assert r2.returncode == 0, r2.stdout + r2.stderr
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


def test_las_kedja_ger_nio_jamforbara():
    kedja = las_kedja()
    assert len(kedja) == 9
    assert set(kedja) == set(JAMFORBARA_2018)
    assert kedja == JAMFORBARA_2018


def test_las_kedja_alla_ger_tjugotre_med_dubbletter_tillatna():
    alla = las_kedja_alla()
    assert len(alla) == 23
    assert set(JAMFORBARA_2018.items()) <= set(alla.items())
    # 14800530 och 14800535 kommer båda ur 2018 års 14801011: distriktet delades vid omritningen 2022.
    assert alla["14800530"] == alla["14800535"] == "14801011"


def test_las_kedja_rader_dubbel_kod_2022_ger_fel(tmp_path):
    kedjefil = tmp_path / "kedja_dubbel_2022.csv"
    kedjefil.write_text(
        "kod_2022;kod_2018;jamforbar_tillbaka_till\n"
        "14800001;14801000;2018\n"
        "14800001;14801001;2014\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        _las_kedja_rader(kedjefil)


@finns
def test_swing_2022_kedjatackning_kontrolleras(monkeypatch):
    """Om kedjefilens kod_2022-mängd inte täcker exakt 2022 års distrikt (en rad saknas, eller en
    främmande kod har smugit sig in) ska bygg_swing_2022 stoppa med FEL i stället för att bygga en
    swing-fil som saknar eller har extra distrikt."""
    monkeypatch.setattr(bygg_historik, "las_kedja_alla", lambda: {"00000000": "00000000"})
    con = bygg_historik.oppna()
    try:
        with pytest.raises(SystemExit):
            bygg_historik.bygg_swing_2022(con)
    finally:
        con.close()


@finns
def test_distrikt_ur_db_giltiga_null_utelamnar_valet(tmp_path):
    kopia = tmp_path / "giltiga_null.sqlite"
    shutil.copy(DB, kopia)
    con = sqlite3.connect(kopia)
    con.execute("UPDATE distrikt_summa SET giltiga = NULL WHERE ar=2018 AND val='rd' AND kod='14801032'")
    con.commit()
    con.row_factory = sqlite3.Row
    partier_per_val = {val: list(NYCKELPARTIER[val]) for val in NYCKELPARTIER}
    post = bygg_historik.distrikt_ur_db(con, 2018, "14801032", "Godhem", partier_per_val)
    con.close()
    assert "rd" not in post
    assert "rd" not in post["giltiga"] and "rd" not in post["rostande"] and "rd" not in post["rostberattigade"]


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


@finns
def test_geo2006_forenklad_med_17_giltiga_polygoner(geo2006):
    fc = json.loads((geo2006 / "distrikt_2006.geojson").read_text("utf-8"))
    assert len(fc["features"]) == 17 and fc["bbox"][0] < fc["bbox"][2]
    for f in fc["features"]:
        g = shape(f["geometry"])
        assert g.is_valid and g.geom_type == "Polygon", f["properties"]["kod"]
        lon, lat = f["properties"]["etikett"]
        assert g.contains(shape({"type": "Point", "coordinates": [lon, lat]}))
        assert set(f["properties"]) == {"kod", "namn", "etikett", "area_km2"}
    assert abs(sum(f["properties"]["area_km2"] for f in fc["features"]) - 4.655) < 0.02, "samma yta som 2022 på 0,04 procent när, förenklingen får kosta högst 0,4 procent"
    namn = {f["properties"]["kod"]: f["properties"]["namn"] for f in fc["features"]}
    assert namn["14805901"] == "Stigberget 1" and namn["14808504"] == "Majorna 4"


@finns
def test_geo2006_js_storlek(geo2006):
    """Sidan laddar .js (via <script>), inte .geojson - storleken mäts därför på den filen, under
    12 kB för en 170 px bred kontur (se FORENKLA_GRADER i bygg_historik.py, där måttet är uppmätt).
    .geojson är den läsbara källfilen (indenterad) och får vara större; 30 kB är en ren
    rimlighetsgräns som bara fångar en total urspårning, inte formatet."""
    js = geo2006 / "distrikt_2006.js"
    geojson = geo2006 / "distrikt_2006.geojson"
    assert js.stat().st_size < 12000, f"distrikt_2006.js: {js.stat().st_size} byte"
    assert geojson.stat().st_size < 30000, f"distrikt_2006.geojson: {geojson.stat().st_size} byte"


@finns
def test_distrikt_2006_ingen_overlapp_mellan_grannar(geo2006):
    """Topologisk förenkling (Task 3-rättningen): grannar delar samma förenklade gräns, så inget
    par polygoner i distrikt_2006 ska överlappa mer än marginellt (avrundningen till sex decimaler
    ger någon enstaka kvadratdecimeter, långt under kravet på en kvadratmeter)."""
    fc = json.loads((geo2006 / "distrikt_2006.geojson").read_text("utf-8"))
    tr = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    polygoner = [(f["properties"]["kod"], geo_transform(tr.transform, shape(f["geometry"])))
                 for f in fc["features"]]
    for i in range(len(polygoner)):
        for j in range(i + 1, len(polygoner)):
            kod_i, poly_i = polygoner[i]
            kod_j, poly_j = polygoner[j]
            overlapp = poly_i.intersection(poly_j).area
            assert overlapp < 1, f"{kod_i} och {kod_j} överlappar {overlapp:.2f} kvm"


@finns
def test_distrikt_2006_union_nara_rafilen(geo2006):
    """Unionens symmetriska differens mot unionen av råfilen (luckor och överlapp räknade var för
    sig, se geo.jamfor_union) ska ligga under 1,2 procent av ytan - det är det strikta måttet, eftersom
    nettoskillnaden ('skillnad') kan råka bli liten även vid stora lokala fel, om luckor och överlapp
    tar ut varandra i konturens många små vinklar. Nettoskillnaden får ändå inte överstiga 0,5 procent,
    som en lösare rimlighetsgräns (båda måtten är uppmätta för det valda FORENKLA_GRADER-värdet i
    bygg_historik.py)."""
    fc = json.loads((geo2006 / "distrikt_2006.geojson").read_text("utf-8"))
    rafil = json.loads(RAFIL_2006.read_text("utf-8"))
    resultat = geo.jamfor_union(rafil, fc)
    assert resultat["symmetrisk_differens"] / resultat["yta_a"] < 0.012, (
        f"symmetrisk differens {resultat['symmetrisk_differens'] / resultat['yta_a'] * 100:.2f} procent")
    assert abs(resultat["skillnad"]) / resultat["yta_a"] < 0.005, (
        f"nettoskillnad {resultat['skillnad'] / resultat['yta_a'] * 100:+.2f} procent")


@finns
def test_distrikt_2006_ytterkontur_nara_2022(geo2006):
    """Ytterkonturen (unionen av alla 17 distrikt) ska ligga nära dagens Majorna-yta (unionen av
    data/distrikt_2022.geojson), trots att valdistrikten ritades om helt inför 2022 - samma
    symmetriska differens-mått som mot råfilen ovan, samma gräns 1,2 procent."""
    fc = json.loads((geo2006 / "distrikt_2006.geojson").read_text("utf-8"))
    fc_2022 = json.loads((ROT / "data" / "distrikt_2022.geojson").read_text("utf-8"))
    resultat = geo.jamfor_union(fc, fc_2022)
    assert resultat["symmetrisk_differens"] / resultat["yta_a"] < 0.012, (
        f"symmetrisk differens {resultat['symmetrisk_differens'] / resultat['yta_a'] * 100:.2f} procent")


@finns
def test_distrikt_2006_grad3_noder_bevarade(geo2006):
    """Den topologiska förenklingen (geo._forenkla_topologiskt) förenklar bara linjerna mellan
    knutpunkter - den ska aldrig flytta en knutpunkt där tre eller fler distrikt möts. Varje
    ändpunkt i det förenklade gränsnätets linjer (unary_union av boundaries, linemerge) ska alltså
    finnas exakt (samma koordinat) bland ändpunkterna i originalnätet ur råfilen."""
    def andpunkter(featurecollection):
        polys = [shape(ft["geometry"]) for ft in featurecollection["features"]]
        granser = unary_union([p.boundary for p in polys])
        granser = granser if granser.geom_type == "LineString" else linemerge(granser)
        linjer = [granser] if granser.geom_type == "LineString" else list(granser.geoms)
        return {ln.coords[i] for ln in linjer for i in (0, -1)}

    fc = json.loads((geo2006 / "distrikt_2006.geojson").read_text("utf-8"))
    rafil = json.loads(RAFIL_2006.read_text("utf-8"))
    original = andpunkter(rafil)
    forenklat = andpunkter(fc)
    saknas = forenklat - original
    assert not saknas, f"{len(saknas)} noder i den förenklade filen saknas i originalnätet: {sorted(saknas)[:5]}"


@finns
def test_distrikt_2006_identisk_med_committad_fil(geo2006):
    """Den committade data/distrikt_2006.geojson och .js ska vara byte-identiska med byggarens
    utdata, inte bara lika som JSON - samma mönster som test_geo.test_distrikt_identisk_med_committad_fil."""
    for namn in ("distrikt_2006.geojson", "distrikt_2006.js"):
        byggd = (geo2006 / namn).read_text("utf-8")
        committad = (ROT / "data" / namn).read_text("utf-8")
        assert byggd == committad, namn


@finns
def test_distrikt_2006_samma_koder_som_rafilen(geo2006):
    fc = json.loads((geo2006 / "distrikt_2006.geojson").read_text("utf-8"))
    rafil = json.loads(RAFIL_2006.read_text("utf-8"))
    koder = {f["properties"]["kod"] for f in fc["features"]}
    koder_ra = {str(f["properties"]["kod"]).strip() for f in rafil["features"]}
    assert len(koder) == 17 and koder == koder_ra


@finns
def test_bygg_geo_2018_ger_22_giltiga_polygoner_utan_overlapp():
    """2018 förenklas inte (samma gränser som majorna_medlem-tabellens 22 distrikt); ingen
    polygon får överlappa en annan med mer än en kvadratmeter i EPSG:3006."""
    fc = bygg_geo(2018, forenkla=False)
    assert len(fc["features"]) == 22
    with db() as con:
        vantade = {r[0] for r in con.execute("SELECT kod FROM majorna_medlem WHERE ar=2018").fetchall()}
    koder = {f["properties"]["kod"] for f in fc["features"]}
    assert koder == vantade
    tr = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    polygoner = []
    for f in fc["features"]:
        g = shape(f["geometry"])
        assert g.is_valid and g.geom_type == "Polygon", f["properties"]["kod"]
        polygoner.append((f["properties"]["kod"], geo_transform(tr.transform, g)))
    for i in range(len(polygoner)):
        for j in range(i + 1, len(polygoner)):
            kod_i, poly_i = polygoner[i]
            kod_j, poly_j = polygoner[j]
            overlapp = poly_i.intersection(poly_j).area
            assert overlapp < 1, f"{kod_i} och {kod_j} överlappar {overlapp:.1f} kvm"


# ---------------------------------------------------------------- Task 4: valdata_<år> och distrikt_<år>

@finns
def test_valdata_2006_i_sidans_schema(tmp_path):
    r = kor("ar", "2006", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2006.json").read_text("utf-8"))
    assert v["meta"]["ar"] == 2006 and v["meta"]["status"] == "slutlig" and len(v["distrikt"]) == 17
    assert v["meta"]["valnatt"] == {"raknade": 17, "totalt": 17}
    assert all(set(d) >= {"kod", "namn", "raknat", "rd", "rf", "kf", "giltiga", "rostande", "rostberattigade"} for d in v["distrikt"])
    with db() as con:
        t = con.execute("SELECT roster, giltiga FROM tidsserie WHERE ar=2006 AND val='rd' AND niva='majorna' AND parti='V'").fetchone()
    assert v["aggregat"]["majorna"]["rd"]["roster"]["V"] == t[0] and v["aggregat"]["majorna"]["rd"]["giltiga"] == t[1]
    assert v["aggregat"]["goteborg"]["rd"]["valdeltagande"] == pytest.approx(0.7954, abs=0.0001)
    assert v["aggregat"]["riket"]["rd"]["namn"] == "Riket" and 0.05 < v["aggregat"]["riket"]["rd"]["andel"]["V"] < 0.07
    assert sum(v["mandat"]["riksdag_verklig"].values()) == 349 and sum(v["mandat"]["riksdag_majorna"].values()) == 349
    assert not (tmp_path / "distrikt_2006.geojson").exists(), "2006 års polygoner byggs av geo2006, förenklade"


@finns
def test_valdata_2018_och_distrikt_2018(tmp_path):
    r = kor("ar", "2018", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2018.json").read_text("utf-8"))
    assert len(v["distrikt"]) == 22
    d = {x["kod"]: x for x in v["distrikt"]}["14801032"]
    assert d["namn"] == "Godhem" and d["rd"]["V"] > 0 and sum(d["rd"].values()) == d["giltiga"]["rd"]
    fc = json.loads((tmp_path / "distrikt_2018.geojson").read_text("utf-8"))
    assert len(fc["features"]) == 22
    assert sorted(f["properties"]["kod"] for f in fc["features"]) == sorted(x["kod"] for x in v["distrikt"])


@finns
def test_valdata_partier_som_inte_fanns_utelamnas(tmp_path):
    """D fanns inte som parti före 2018, FI saknas i regionvalet 2006 och 2010 (ingen rad i roster för
    något Majornadistrikt) - de ska inte visas som 0,0 procent bland nyckelpartierna de åren."""
    r6 = kor("ar", "2006", "--ut", str(tmp_path / "2006"))
    r18 = kor("ar", "2018", "--ut", str(tmp_path / "2018"))
    assert r6.returncode == 0, r6.stdout + r6.stderr
    assert r18.returncode == 0, r18.stdout + r18.stderr
    v6 = json.loads((tmp_path / "2006" / "valdata_2006.json").read_text("utf-8"))
    v18 = json.loads((tmp_path / "2018" / "valdata_2018.json").read_text("utf-8"))
    for d in v6["distrikt"]:
        assert "D" not in d["kf"], f"{d['kod']}: D fanns inte 2006"
        assert "D" not in d["rf"], f"{d['kod']}: D fanns inte 2006"
        assert "FI" not in d["rf"], f"{d['kod']}: FI saknades i regionvalet 2006"
    for d in v18["distrikt"]:
        assert "D" in d["kf"], f"{d['kod']}: D fanns 2018"
        assert "D" in d["rf"], f"{d['kod']}: D fanns 2018"
        assert "FI" in d["rf"], f"{d['kod']}: FI fanns i regionvalet 2018"


@finns
@pytest.mark.parametrize("ar", [2006, 2010, 2014, 2018])
def test_valdata_riksdag_verklig_summerar_349(tmp_path, ar):
    r = kor("ar", str(ar), "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / f"valdata_{ar}.json").read_text("utf-8"))
    assert sum(v["mandat"]["riksdag_verklig"].values()) == 349
    assert sum(v["mandat"]["riksdag_majorna"].values()) == 349


@finns
@pytest.mark.parametrize("ar", [2006, 2010, 2014, 2018])
def test_valdata_riksdag_majorna_raknas_om_oberoende(tmp_path, ar):
    """riksdag_majorna räknas om oberoende av skriptet: summera rd-rösterna över distrikten i den
    byggda filen och kör dem genom samma jamkade_uddatal som bygg_valdata_ar - facit ska vara likadant,
    inte bara summera till 349 (test_valdata_riksdag_verklig_summerar_349 fångar inte till exempel fel
    fördelning mellan två partier som råkar ge samma summa)."""
    r = kor("ar", str(ar), "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / f"valdata_{ar}.json").read_text("utf-8"))
    rd_summa = {}
    for d in v["distrikt"]:
        for p, n in d["rd"].items():
            rd_summa[p] = rd_summa.get(p, 0) + n
    vantat = jamkade_uddatal(rd_summa, 349)
    assert v["mandat"]["riksdag_majorna"] == vantat


@finns
@pytest.mark.parametrize("ar", [2006, 2010, 2014, 2018])
def test_valdata_distrikt_roster_summerar_till_giltiga(tmp_path, ar):
    r = kor("ar", str(ar), "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / f"valdata_{ar}.json").read_text("utf-8"))
    for d in v["distrikt"]:
        for val in ("rd", "rf", "kf"):
            if val in d:
                assert sum(d[val].values()) == d["giltiga"][val], f"{ar} {val} {d['kod']}"


@finns
@pytest.mark.parametrize("ar", [2006, 2010, 2014, 2018])
def test_valdata_meta_slutlig_och_kalla_namner_aret(tmp_path, ar):
    """kalla och avgransning är publicerad text på sidan - de ska nämna valet och året, aldrig en
    sökväg i repot (databasen eller docs/historik/valdistrikt-historik.md, som bara står i
    bygg_valdata_ars docstring)."""
    r = kor("ar", str(ar), "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / f"valdata_{ar}.json").read_text("utf-8"))
    assert v["meta"]["status"] == "slutlig"
    assert str(ar) in v["meta"]["kalla"]
    assert "data/" not in v["meta"]["kalla"] and ".sqlite" not in v["meta"]["kalla"]
    assert "data/" not in v["meta"]["avgransning"] and ".md" not in v["meta"]["avgransning"]


@finns
@pytest.mark.parametrize("ar", [2006, 2010, 2014, 2018])
def test_valdata_vgregion_finns_for_regionvalet(tmp_path, ar):
    """Tabellen aggregat har en vgregion-rad för regionvalet alla fyra åren (kontrollerat mot databasen
    2026-09-07) - riket ska då alltid finnas för rf, inte utelämnas."""
    r = kor("ar", str(ar), "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / f"valdata_{ar}.json").read_text("utf-8"))
    assert "rf" in v["aggregat"]["riket"], f"{ar}: ingen vgregion-rad, riket utelämnat för regionvalet - se README"
    assert v["aggregat"]["riket"]["rf"]["namn"] == "Västra Götaland"


@finns
def test_valdata_2018_byte_identisk_oberoende_av_hashfro(tmp_path):
    """_vgregion byggde tidigare roster ur en mängd (finns), så nyckelordningen i aggregat.riket.rf.andel
    berodde på processens hashfrö och valdata_2018.json blev inte byte-identisk mellan körningar. Två
    körningar med olika PYTHONHASHSEED ska nu ge identiska filer, med nycklarna i sidans partiordning
    (NYCKELPARTIER["rf"], filtrerad till de partier som fanns)."""
    ut_a, ut_b = tmp_path / "a", tmp_path / "b"
    miljo_a = {**os.environ, "PYTHONHASHSEED": "1"}
    miljo_b = {**os.environ, "PYTHONHASHSEED": "2"}
    ra = subprocess.run([sys.executable, "scripts/bygg_historik.py", "ar", "2018", "--ut", str(ut_a)],
                         cwd=ROT, capture_output=True, text=True, env=miljo_a)
    rb = subprocess.run([sys.executable, "scripts/bygg_historik.py", "ar", "2018", "--ut", str(ut_b)],
                         cwd=ROT, capture_output=True, text=True, env=miljo_b)
    assert ra.returncode == 0, ra.stdout + ra.stderr
    assert rb.returncode == 0, rb.stdout + rb.stderr
    fa = (ut_a / "valdata_2018.json").read_bytes()
    fb = (ut_b / "valdata_2018.json").read_bytes()
    assert fa == fb, "valdata_2018.json ska vara byte-identisk oberoende av hashfrö"
    ja = (ut_a / "valdata_2018.js").read_bytes()
    jb = (ut_b / "valdata_2018.js").read_bytes()
    assert ja == jb, "valdata_2018.js ska vara byte-identisk oberoende av hashfrö"
    v = json.loads(fa.decode("utf-8"))
    andel = v["aggregat"]["riket"]["rf"]["andel"]
    forvantad_ordning = [p for p in NYCKELPARTIER["rf"] if p in andel]
    assert list(andel.keys()) == forvantad_ordning


def test_ar_2022_avvisas_av_tillatlistan(tmp_path):
    """"ar 2022" skrev tidigare över sidans kanoniska data/valdata_2022.json (ur databasen, med annan
    kalla) innan körningen dog på saknad geometri - HISTORIK_AR spärrar det innan något skrivs."""
    r = kor("ar", "2022", "--ut", str(tmp_path))
    assert r.returncode == 1
    assert "FEL:" in r.stderr and "2022" in r.stderr
    assert not any(tmp_path.iterdir()), "inget ska skrivas för ett avvisat år"


def test_ar_ickenumeriskt_ar_ger_fel_inte_traceback(tmp_path):
    r = kor("ar", "abc", "--ut", str(tmp_path))
    assert r.returncode == 1
    assert "FEL:" in r.stderr
    assert "Traceback" not in r.stderr
    assert not any(tmp_path.iterdir())


@pytest.mark.parametrize("vad", ["historik", "swing2022", "geo2006"])
def test_aren_avvisas_for_subkommandon_utan_ar(tmp_path, vad):
    """historik, swing2022 och geo2006 tar inga år - ett år som argument (till exempel av misstag,
    kopierat från en 'ar'-körning) ska avvisas med FEL, inte tyst ignoreras."""
    r = kor(vad, "2018", "--ut", str(tmp_path))
    assert r.returncode == 1
    assert "FEL:" in r.stderr and vad in r.stderr
    assert not any(tmp_path.iterdir())


@finns
def test_bygg_valdata_ar_vaktar_medlem_utan_alla_tre_valen(tmp_path):
    """raknat=False får aldrig tyst sänka meta.valnatt.raknade i en slutlig historikfil - saknar en
    Majorna-medlem summeringsrad för ett av de tre valen ska hela bygget stoppa, inte bara det distriktet."""
    kopia = tmp_path / "utan_kf_2018.sqlite"
    shutil.copy(DB, kopia)
    con = sqlite3.connect(kopia)
    con.execute("DELETE FROM distrikt_summa WHERE ar=2018 AND val='kf' AND kod='14801032'")
    con.commit()
    con.close()
    r = kor("ar", "2018", "--db", str(kopia), "--ut", str(tmp_path / "ut"))
    assert r.returncode != 0
    assert "FEL:" in r.stderr and "14801032" in r.stderr and "kf" in r.stderr
    assert not (tmp_path / "ut").exists() or not any((tmp_path / "ut").iterdir())


@finns
def test_mandat_riket_rd_vaktar_dubbelt_mandattal(tmp_path):
    """En extra mandat-rad för samma parti med ett annat mandattal (datafel i tabellen) ska stoppa
    bygget med FEL, inte tyst summera fel eller råka bli 349 av misstag."""
    kopia = tmp_path / "dubbelt_mandat_2018.sqlite"
    shutil.copy(DB, kopia)
    con = sqlite3.connect(kopia)
    con.execute("INSERT INTO mandat (ar, val, niva, valkrets, parti, mandat) VALUES (2018, 'rd', 'riket', 'riket', 'V', 999)")
    con.commit()
    con.close()
    r = kor("ar", "2018", "--db", str(kopia), "--ut", str(tmp_path / "ut"))
    assert r.returncode != 0
    assert "FEL:" in r.stderr and "olika mandattal för V" in r.stderr
    assert not (tmp_path / "ut").exists() or not any((tmp_path / "ut").iterdir())


def test_partier_med_rader_ingen_kod_ger_tom_mangd():
    assert partier_med_rader(None, 2018, "rd", []) == set()


@finns
def test_partier_med_rader_d_saknas_2006_finns_2018():
    con = bygg_historik.oppna()
    try:
        koder_2006 = [r["kod"] for r in con.execute("SELECT kod FROM majorna_medlem WHERE ar=2006 AND ingar_i_jamforbart_majorna=1")]
        koder_2018 = [r["kod"] for r in con.execute("SELECT kod FROM majorna_medlem WHERE ar=2018 AND ingar_i_jamforbart_majorna=1")]
        assert "D" not in partier_med_rader(con, 2006, "kf", koder_2006)
        assert "D" in partier_med_rader(con, 2018, "kf", koder_2018)
    finally:
        con.close()
