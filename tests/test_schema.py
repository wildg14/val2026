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


def _d(kod, namn, raknat, rd, giltiga):
    return {"kod": kod, "namn": namn, "raknat": raknat, "rd": rd, "rf": {}, "kf": {},
            "giltiga": {"rd": giltiga} if rd else {}, "rostande": {"rd": giltiga} if rd else {}, "rostberattigade": {"rd": 1000} if rd else {}}


def _agg(distrikt):
    roster, giltiga = {}, 0
    for d in distrikt:
        if d["raknat"] and d["rd"]:
            giltiga += d["giltiga"]["rd"]
            for p, n in d["rd"].items():
                roster[p] = roster.get(p, 0) + n
    return {"majorna": {"rd": {"roster": roster, "giltiga": giltiga, "rostande": giltiga, "rostberattigade": 0}, "rf": {"roster": {}, "giltiga": 0}, "kf": {"roster": {}, "giltiga": 0}}}


def test_swing_bara_jamforbara_distrikt_och_kohort_pa_omradesnivan():
    bas_d = [_d("1", "A", True, {"V": 20, "S": 80}, 100), _d("2", "B", True, {"V": 50, "S": 50}, 100), _d("3", "C", True, {"V": 10, "S": 90}, 100)]
    bas = {"meta": {"ar": 2022}, "distrikt": bas_d, "aggregat": _agg(bas_d)}
    ny_d = [_d("1", "A", True, {"V": 30, "S": 70}, 100), _d("2", "B", False, {}, 0), _d("3", "C", True, {"V": 40, "S": 60}, 100)]
    ny = {"meta": {"ar": 2026}, "distrikt": ny_d, "aggregat": _agg(ny_d)}
    s = schema.swing(ny, bas, jamforbara=["1", "2"])
    assert s["distrikt"] == {"1": {"rd": {"V": 10.0, "S": -10.0}}}, "2 är oräknat, 3 är inte jämförbart"
    assert set(s["ej_jamforbara"]) == {"3"}
    assert s["ej_jamforbara"]["3"]["mening"] == "Gränserna för C ritades om till 2026. Siffrorna går inte att jämföra med 2022."
    assert s["ej_jamforbara"]["3"]["omradesrad"] is True
    k = s["kohort"]["rd"]
    assert k == {"antal": 1, "totalt": 3, "helomrade": False, "koder": ["1"]}
    assert s["majorna"]["rd"] == {"V": 10.0, "S": -10.0}, "kohorten är bara distrikt 1: 30 mot 20"


def test_swing_helomrade_nar_alla_ar_raknade():
    bas_d = [_d("1", "A", True, {"V": 20, "S": 80}, 100), _d("3", "C", True, {"V": 10, "S": 90}, 100)]
    bas = {"meta": {"ar": 2022}, "distrikt": bas_d, "aggregat": _agg(bas_d)}
    ny_d = [_d("1", "A", True, {"V": 30, "S": 70}, 100), _d("3", "C", True, {"V": 40, "S": 60}, 100)]
    ny = {"meta": {"ar": 2026}, "distrikt": ny_d, "aggregat": _agg(ny_d)}
    s = schema.swing(ny, bas, jamforbara=["1"])
    assert s["kohort"]["rd"]["helomrade"] is True and s["kohort"]["rd"]["antal"] == 2
    assert s["majorna"]["rd"] == {"V": 20.0, "S": -20.0}, "hela området mot hela området: 70 mot 30 av 200"
    assert "3" in s["ej_jamforbara"] and "3" not in s["distrikt"]


def test_swing_egna_meningar():
    bas_d = [_d("1", "A", True, {"V": 20, "S": 80}, 100)]
    ny_d = [_d("1", "A", True, {"V": 30, "S": 70}, 100)]
    s = schema.swing({"meta": {"ar": 2022}, "distrikt": ny_d, "aggregat": _agg(ny_d)},
                     {"meta": {"ar": 2018}, "distrikt": bas_d, "aggregat": _agg(bas_d)},
                     jamforbara=[], meningar={"1": "Gränserna såg annorlunda ut 2018."})
    assert s["ej_jamforbara"]["1"]["mening"] == "Gränserna såg annorlunda ut 2018."


def test_skriv_ar_atomisk_och_lamnar_ingen_tmp(tmp_path):
    schema.skriv(tmp_path / "x", {"a": 1})
    assert sorted(p.name for p in tmp_path.iterdir()) == ["x.js", "x.json"]


def test_konfig_standard_har_valdag_toppsvar_och_historik():
    k = schema.KONFIG_STANDARD
    assert k["valdag"] == "2026-09-13"
    assert k["toppsvar"] == {"mening": ""}
    assert k["historik"] == {"visa": True, "mening": {"rd": "", "rf": "", "kf": ""}}


def test_swing_hoppar_over_partier_som_inte_redovisas():
    bas_d = [_d("1", "A", True, {"V": 20, "S": 70, "K": 5, "Övriga": 5}, 100)]
    ny_d = [_d("1", "A", True, {"V": 30, "S": 60, "Övriga": 10}, 100)]
    s = schema.swing({"meta": {"ar": 2026}, "distrikt": ny_d, "aggregat": _agg(ny_d)},
                     {"meta": {"ar": 2022}, "distrikt": bas_d, "aggregat": _agg(bas_d)}, jamforbara=["1"])
    assert s["distrikt"]["1"]["rd"] == {"V": 10.0, "S": -10.0}, "K redovisas inte 2026 och Övriga har annan sammansättning: ingen av dem får ett tal"
    assert s["majorna"]["rd"] == {"V": 10.0, "S": -10.0}
