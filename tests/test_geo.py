import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform, unary_union

from scripts import geo
from scripts.valmyndigheten import MAJORNA_KODER

ROT = Path(__file__).resolve().parents[1]
ZIP_2026 = ROT / "Historiska dokument" / "dl_webb" / "2026" / "valdistrikt-vastra-gotaland-lan-2026.zip"
ZIP_2022 = ROT / "valdistrikt-vastra-gotalands-lan.zip"

_TR_3006 = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)


def _projicerade_distrikt(path):
    """kod -> shapely-polygon i EPSG:3006, ur en committad distrikt_<år>.geojson (WGS84)."""
    fc = json.loads(Path(path).read_text("utf-8"))
    return {f["properties"]["kod"]: transform(_TR_3006.transform, shape(f["geometry"])) for f in fc["features"]}


def test_distrikt_geojson():
    fc = geo.las_distrikt(ROT / "valdistrikt-vastra-gotalands-lan.zip", MAJORNA_KODER)
    assert fc["type"] == "FeatureCollection" and len(fc["features"]) == 23
    koder = [f["properties"]["kod"] for f in fc["features"]]
    assert koder == sorted(MAJORNA_KODER)
    for f in fc["features"]:
        g = shape(f["geometry"])
        assert g.is_valid and g.geom_type == "Polygon"
        lon, lat = f["properties"]["etikett"]
        assert 11.88 < lon < 11.95 and 57.67 < lat < 57.71
        assert g.contains(shape({"type": "Point", "coordinates": [lon, lat]}))
        assert not f["properties"]["namn"].startswith("Västra Centrum")
        assert f["properties"]["area_km2"] > 0
    assert fc["bbox"][0] < fc["bbox"][2] and fc["bbox"][1] < fc["bbox"][3]
    assert {f["properties"]["namn"] for f in fc["features"]} >= {"Mariaplan", "Svalebo", "Slottsskogsgat. m fl"}


def test_saknat_distrikt_ger_fel():
    with pytest.raises(ValueError):
        geo.las_distrikt(ROT / "valdistrikt-vastra-gotalands-lan.zip", ["14800526", "99999999"])


def test_egenskaper_2022_och_2026():
    assert geo.egenskaper({"Lkfv": " 14800526 ", "Vdnamn": "Västra Centrum, Svalebo"}) == ("14800526", "Svalebo")
    assert geo.egenskaper({"Valdistriktskod": "14800533", "Valdistriktsnamn": "Västra Centrum, Sandarna"}) == ("14800533", "Sandarna")
    assert geo.egenskaper({"annat": 1}) == ("", "")


def test_egenskaper_faller_tillbaka_pa_null_och_tom_strang():
    props = {"Lkfv": None, "Valdistriktskod": "14800526", "Vdnamn": None,
             "Valdistriktsnamn": "Västra Centrum, Svalebo"}
    assert geo.egenskaper(props) == ("14800526", "Svalebo")


def test_las_distrikt_foredrar_geojson_over_json(tmp_path):
    """Zipen kan innehålla en metadata.json (som inte är distriktsdatan) vid sidan av .geojson-filen;
    .json kommer före .geojson alfabetiskt så filvalet måste vara explicit, inte bara sorterat namn."""
    fc = {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"Lkfv": "14800526", "Vdnamn": "Test, Enda"},
        "geometry": {"type": "Polygon", "coordinates": [[[317000, 6398000], [317100, 6398000],
                                                           [317100, 6398100], [317000, 6398100],
                                                           [317000, 6398000]]]},
    }]}
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("metadata.json", json.dumps({"nagot": "annat"}))
        z.writestr("x.geojson", json.dumps(fc))
    resultat = geo.las_distrikt(zip_path, ["14800526"])
    assert len(resultat["features"]) == 1
    assert resultat["features"][0]["properties"]["kod"] == "14800526"


def test_las_distrikt_utan_features_ger_fel(tmp_path):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("x.geojson", json.dumps({"type": "FeatureCollection"}))
    with pytest.raises(ValueError, match="saknar features"):
        geo.las_distrikt(zip_path, ["14800526"])


@pytest.mark.skipif(not ZIP_2026.exists(), reason="2026 års valgeografi saknas")
def test_distrikt_2026():
    fc = geo.las_distrikt(ZIP_2026, MAJORNA_KODER)
    assert len(fc["features"]) == 23
    namn = {f["properties"]["kod"]: f["properties"]["namn"] for f in fc["features"]}
    assert namn["14800533"] == "Sandarna" and namn["14800526"] == "Svalebo"
    yta = sum(f["properties"]["area_km2"] for f in fc["features"])
    assert abs(yta - 4.6554) < 0.001, f"unionsytan ska vara samma som 2022, fick {yta}"
    for f in fc["features"]:
        g = shape(f["geometry"])
        assert g.is_valid and g.geom_type == "Polygon"
        lon, lat = f["properties"]["etikett"]
        assert 11.88 < lon < 11.95 and 57.67 < lat < 57.71 and g.contains(shape({"type": "Point", "coordinates": [lon, lat]}))


@pytest.mark.parametrize("ar,zip_path", [("2022", ZIP_2022), ("2026", ZIP_2026)])
def test_distrikt_identisk_med_committad_fil(ar, zip_path):
    """Den committade filen ska vara byte-identisk med byggarens utdata, inte bara lika som JSON:
    en ombyggnad får aldrig ge en diff i data/ av formatskäl. Samma parametrar som schema.skriv."""
    if not zip_path.exists():
        pytest.skip(f"{ar} års valgeografi saknas")
    fc = geo.las_distrikt(zip_path, MAJORNA_KODER)
    text = json.dumps(fc, ensure_ascii=False, indent=1) + "\n"
    assert text == (ROT / "data" / f"distrikt_{ar}.geojson").read_text("utf-8")


def test_2026_namn_inte_vastra_centrum_i_committad_fil():
    fc = json.loads((ROT / "data" / "distrikt_2026.geojson").read_text("utf-8"))
    assert not any(f["properties"]["namn"].startswith("Västra Centrum") for f in fc["features"])


def test_jamfor_union_2022_mot_2026():
    fc_2022 = json.loads((ROT / "data" / "distrikt_2022.geojson").read_text("utf-8"))
    fc_2026 = json.loads((ROT / "data" / "distrikt_2026.geojson").read_text("utf-8"))
    resultat = geo.jamfor_union(fc_2022, fc_2026)
    assert resultat["symmetrisk_differens"] < 10
    assert abs(resultat["skillnad"]) < 10


def test_nio_distrikt_omritade_2022_till_2026():
    """Valmyndighetens geografi för 2026 ritar om nio distrikts gränser jämfört med 2022. Marieberg
    (14800542) och Karl Johan (14800544) har därutöver bytt ett kvarter på cirka 533 kvadratmeter
    sinsemellan (vid 57,696174 N, 11,928638 E), trots att Valmyndigheten markerar båda som "Kan
    jämföras" mellan åren - se scratchpad/tasks/tillagg-geo.md. Övriga tolv distrikt är oförändrade."""
    omritade = {"14800529", "14800530", "14800531", "14800532", "14800533",
                "14800534", "14800535", "14800538", "14800541"}
    kvarterbyte = {"14800542", "14800544"}
    a = _projicerade_distrikt(ROT / "data" / "distrikt_2022.geojson")
    b = _projicerade_distrikt(ROT / "data" / "distrikt_2026.geojson")
    assert set(a) == set(b) == set(MAJORNA_KODER)
    for kod in MAJORNA_KODER:
        symdiff = a[kod].symmetric_difference(b[kod]).area
        if kod in omritade:
            assert symdiff > 100, f"{kod}: väntade en omritning, symmetrisk differens {symdiff:.0f} kvm"
        elif kod in kvarterbyte:
            assert 500 < symdiff < 600, f"{kod}: väntade kvarterbytet, fick {symdiff:.0f} kvm"
        else:
            assert symdiff < 10, f"{kod}: väntade oförändrat distrikt, fick {symdiff:.0f} kvm"


def test_unionerna_lika_2022_och_2026():
    a = _projicerade_distrikt(ROT / "data" / "distrikt_2022.geojson")
    b = _projicerade_distrikt(ROT / "data" / "distrikt_2026.geojson")
    union_a = unary_union(list(a.values()))
    union_b = unary_union(list(b.values()))
    assert union_a.symmetric_difference(union_b).area < 10


@pytest.mark.parametrize("fil", ["distrikt_2022.geojson", "distrikt_2026.geojson"])
def test_inga_overlapp_inom_aret(fil):
    polys = list(_projicerade_distrikt(ROT / "data" / fil).values())
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            overlapp = polys[i].intersection(polys[j]).area
            assert overlapp < 1, f"{fil}: distrikt {i} och {j} överlappar {overlapp:.1f} kvm"


def test_bygg_geo_okant_ar_utan_zip_ger_fel(tmp_path):
    r = subprocess.run([sys.executable, "scripts/bygg_geo.py", "--ar", "2018", "--ut", str(tmp_path)],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1
    assert "ange --zip" in r.stderr


@pytest.mark.skipif(not ZIP_2026.exists(), reason="2026 års valgeografi saknas")
def test_bygg_geo_felformaterat_ar_ger_fel(tmp_path):
    r = subprocess.run([sys.executable, "scripts/bygg_geo.py", "--ar", "2026.1", "--zip", str(ZIP_2026),
                        "--ut", str(tmp_path)], cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1


@pytest.mark.skipif(not ZIP_2026.exists(), reason="2026 års valgeografi saknas")
def test_bygg_geo_2026_med_jamfor(tmp_path):
    r = subprocess.run([sys.executable, "scripts/bygg_geo.py", "--ar", "2026", "--ut", str(tmp_path),
                        "--jamfor", str(ROT / "data" / "distrikt_2022.geojson")],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "symmetrisk differens" in r.stdout


def test_bygg_geo_saknad_jamforelsefil_ger_fel(tmp_path):
    r = subprocess.run([sys.executable, "scripts/bygg_geo.py", "--ar", "2022", "--ut", str(tmp_path),
                        "--jamfor", str(tmp_path / "finns-inte.geojson")],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1
    assert "hittar inte jämförelsefilen" in r.stderr
    assert "Traceback" not in r.stderr


@pytest.mark.parametrize("varde", ["katalog", "tom"])
def test_bygg_geo_jamfor_som_katalog_eller_tom_strang_ger_felrad(tmp_path, varde):
    """En katalog och en tom sträng finns båda som sökväg men går inte att läsa som fil."""
    jamfor = str(tmp_path) if varde == "katalog" else ""
    r = subprocess.run([sys.executable, "scripts/bygg_geo.py", "--ar", "2022", "--ut", str(tmp_path),
                        "--jamfor", jamfor], cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1
    assert "hittar inte jämförelsefilen" in r.stderr
    assert "Traceback" not in r.stderr


@pytest.mark.parametrize("varde", ["katalog", "tom"])
def test_bygg_geo_zip_som_katalog_eller_tom_strang_ger_felrad(tmp_path, varde):
    zipvarde = str(tmp_path) if varde == "katalog" else ""
    r = subprocess.run([sys.executable, "scripts/bygg_geo.py", "--ar", "2026", "--zip", zipvarde,
                        "--ut", str(tmp_path)], cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1
    assert "ange --zip" in r.stderr
    assert "Traceback" not in r.stderr


def test_bygg_geo_validerar_jamfor_fore_inlasningen(tmp_path):
    """Felet i --jamfor ska komma innan zip-filen läses, så att man inte väntar ut inläsningen
    för att få veta att jämförelsefilen inte går att läsa."""
    if not ZIP_2022.exists():
        pytest.skip("2022 års valgeografi saknas")
    r = subprocess.run([sys.executable, "scripts/bygg_geo.py", "--ar", "2022", "--zip", str(ZIP_2022),
                        "--ut", str(tmp_path), "--jamfor", str(tmp_path)],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 1
    assert "hittar inte jämförelsefilen" in r.stderr
    assert "unionsyta" not in r.stdout
    assert not list(tmp_path.iterdir())


def test_bygg_geo_utan_standardjamforelse_skriver_rad(tmp_path):
    """Utan distrikt_2022.geojson i --ut skrivs raden Ingen ytjämförelse, och bygget fortsätter."""
    if not ZIP_2026.exists():
        pytest.skip("2026 års valgeografi saknas")
    r = subprocess.run([sys.executable, "scripts/bygg_geo.py", "--ar", "2026", "--zip", str(ZIP_2026),
                        "--ut", str(tmp_path)], cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Ingen ytjämförelse" in r.stdout
    assert "symmetrisk differens" not in r.stdout
    assert (tmp_path / "distrikt_2026.geojson").is_file()


def _rutfeature(kod, koordinater):
    return {"type": "Feature", "properties": {"kod": kod},
            "geometry": {"type": "Polygon", "coordinates": [koordinater]}}


def test_jamfor_union_lagar_ogiltig_geometri():
    """En självkorsande ring (fjärilen) är ogiltig; unary_union kastar då. buffer(0) lagar den,
    så att en ytjämförelse går att göra i stället för att avbrytas."""
    ruta = [[11.900, 57.700], [11.901, 57.700], [11.901, 57.701], [11.900, 57.701], [11.900, 57.700]]
    fjaril = [[11.900, 57.700], [11.901, 57.701], [11.901, 57.700], [11.900, 57.701], [11.900, 57.700]]
    a = {"type": "FeatureCollection", "features": [_rutfeature("1", ruta)]}
    b = {"type": "FeatureCollection", "features": [_rutfeature("1", fjaril)]}
    resultat = geo.jamfor_union(a, b)
    assert resultat["yta_b"] > 0
    assert resultat["symmetrisk_differens"] > 0


def test_jamfor_union_olaglig_geometri_ger_begripligt_fel():
    """En polygon utan area går inte att laga; felet ska nämna distriktets kod."""
    ruta = [[11.900, 57.700], [11.901, 57.700], [11.901, 57.701], [11.900, 57.701], [11.900, 57.700]]
    spik = [[11.900, 57.700], [11.901, 57.700], [11.900, 57.700], [11.900, 57.700]]
    a = {"type": "FeatureCollection", "features": [_rutfeature("1", ruta)]}
    b = {"type": "FeatureCollection", "features": [_rutfeature("14800526", spik)]}
    with pytest.raises(ValueError, match="14800526"):
        geo.jamfor_union(a, b)
