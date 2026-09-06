from pathlib import Path

import pytest
from shapely.geometry import shape

from scripts import geo
from scripts.valmyndigheten import MAJORNA_KODER

ROT = Path(__file__).resolve().parents[1]
ZIP_2026 = Path("/Users/daniel/code/Temp/Historiska dokument/dl_webb/2026/valdistrikt-vastra-gotaland-lan-2026.zip")


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
