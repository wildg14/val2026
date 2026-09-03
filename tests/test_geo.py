from pathlib import Path

from shapely.geometry import shape

from scripts import geo
from scripts.valmyndigheten import MAJORNA_KODER

ROT = Path(__file__).resolve().parents[1]


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
    import pytest
    with pytest.raises(ValueError):
        geo.las_distrikt(ROT / "valdistrikt-vastra-gotalands-lan.zip", ["14800526", "99999999"])
