import json

from scripts import schema


def test_skriv_json_och_js(tmp_path):
    obj = {"a": [1, 2], "å": "ö"}
    schema.skriv(tmp_path / "x", obj)
    assert json.loads((tmp_path / "x.json").read_text("utf-8")) == obj
    js = (tmp_path / "x.js").read_text("utf-8")
    assert js.startswith('window.MAJPOSTEN=window.MAJPOSTEN||{data:{}};window.MAJPOSTEN.data["x"]=')
    assert js.rstrip().endswith(";")
    assert schema.las_js(tmp_path / "x.js") == obj


def test_swing():
    bas = {"meta": {"ar": 2022},
           "distrikt": [{"kod": "1", "raknat": True, "rd": {"V": 20, "S": 80}, "rf": {}, "kf": {},
                         "giltiga": {"rd": 100}}],
           "aggregat": {"majorna": {"rd": {"roster": {"V": 20, "S": 80}, "giltiga": 100}}}}
    ny = {"meta": {"ar": 2026},
          "distrikt": [{"kod": "1", "raknat": True, "rd": {"V": 30, "S": 70}, "rf": {}, "kf": {},
                        "giltiga": {"rd": 100}}],
          "aggregat": {"majorna": {"rd": {"roster": {"V": 30, "S": 70}, "giltiga": 100}}}}
    s = schema.swing(ny, bas)
    assert s["bas"] == 2022 and s["ar"] == 2026
    assert s["distrikt"]["1"]["rd"] == {"V": 10.0, "S": -10.0}
    assert s["majorna"]["rd"] == {"V": 10.0, "S": -10.0}


def test_swing_hoppar_over_oraknade():
    bas = {"meta": {"ar": 2022}, "distrikt": [{"kod": "1", "raknat": True, "rd": {"V": 1}, "giltiga": {"rd": 1}}],
           "aggregat": {"majorna": {"rd": {"roster": {"V": 1}, "giltiga": 1}}}}
    ny = {"meta": {"ar": 2026}, "distrikt": [{"kod": "1", "raknat": False, "rd": {}, "giltiga": {}}],
          "aggregat": {"majorna": {"rd": {"roster": {}, "giltiga": 0}}}}
    s = schema.swing(ny, bas)
    assert s["distrikt"] == {} and s["majorna"]["rd"] == {}


def test_bygg_valdata_aggregat_och_valnatt():
    d = [{"kod": "1", "namn": "A", "raknat": True, "rd": {"V": 1, "S": 3}, "rf": {}, "kf": {},
          "giltiga": {"rd": 4}, "rostande": {"rd": 5}, "rostberattigade": {"rd": 10}},
         {"kod": "2", "namn": "B", "raknat": False, "rd": {}, "rf": {}, "kf": {},
          "giltiga": {}, "rostande": {}, "rostberattigade": {}}]
    v = schema.bygg_valdata(2026, d, status="preliminar")
    assert v["meta"]["ar"] == 2026 and v["meta"]["status"] == "preliminar"
    assert v["aggregat"]["majorna"]["rd"] == {"roster": {"V": 1, "S": 3}, "giltiga": 4, "rostande": 5, "rostberattigade": 10}
    assert v["aggregat"]["majorna"]["kf"] == {"roster": {}, "giltiga": 0, "rostande": 0, "rostberattigade": 0}
    assert v["meta"]["valnatt"] == {"raknade": 1, "totalt": 2}
    assert v["meta"]["val"] == {"rd": "Riksdag", "rf": "Region", "kf": "Kommun"}
    assert "V" in v["meta"]["partier"]
    assert v["aggregat"]["goteborg"] == {} and v["aggregat"]["riket"] == {}
