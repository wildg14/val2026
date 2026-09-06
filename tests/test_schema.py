import json
import math
from pathlib import Path

from scripts import schema

ROT = Path(__file__).resolve().parents[1]


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


def test_skriv_lamnar_ingen_tmp(tmp_path):
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


def test_diff_ger_inte_negativ_nolla():
    d = schema._diff({"V": 5000}, 10000, {"V": 5004}, 10000)
    # d["V"] == 0.0 är sant även för -0.0, så det bevisar inget; math.copysign avslöjar tecknet.
    assert math.copysign(1.0, d["V"]) == 1.0, "0,04 procentenhets tillbakagång ska avrundas till 0.0, inte -0.0"
    assert json.dumps(d) == '{"V": 0.0}'


def test_swing_mening_for_distrikt_som_saknas_i_basaret():
    bas_d = [_d("1", "A", True, {"V": 20, "S": 80}, 100)]
    ny_d = [_d("1", "A", True, {"V": 30, "S": 70}, 100),
            _d("2", "B", True, {"V": 10, "S": 90}, 100),
            _d("3", "C", True, {"V": 15, "S": 85}, 100)]
    bas = {"meta": {"ar": 2022}, "distrikt": bas_d, "aggregat": _agg(bas_d)}
    ny = {"meta": {"ar": 2026}, "distrikt": ny_d, "aggregat": _agg(ny_d)}
    s = schema.swing(ny, bas, jamforbara=["1", "2", "3"], meningar={"3": "Eget bortfall för C."})
    assert s["ej_jamforbara"]["2"]["orsak"] == "saknas i basåret"
    assert s["ej_jamforbara"]["2"]["mening"] == "B fanns inte som valdistrikt 2022. Siffrorna går inte att jämföra med 2022."
    assert s["ej_jamforbara"]["3"]["mening"] == "Eget bortfall för C.", "meningar ska fortfarande skriva över standardmeningen"


def test_swing_samma_yta_true_ger_helomrade_trots_fler_distrikt_i_ny():
    v = json.loads((ROT / "data" / "valdata_2022.json").read_text("utf-8"))
    ny = v
    bas = schema.bygg_valdata(2018, v["distrikt"][:-1])  # 22 distrikt, samma yta som de 23 i ny
    assert len(ny["distrikt"]) == 23 and len(bas["distrikt"]) == 22
    s = schema.swing(ny, bas, samma_yta=True)
    for val in ("rd", "rf", "kf"):
        assert s["kohort"][val]["helomrade"] is True
        assert s["majorna"][val] == schema._diff(
            ny["aggregat"]["majorna"][val]["roster"], ny["aggregat"]["majorna"][val]["giltiga"],
            bas["aggregat"]["majorna"][val]["roster"], bas["aggregat"]["majorna"][val]["giltiga"])


def test_swing_samma_yta_none_kraver_lika_antal_distrikt():
    v = json.loads((ROT / "data" / "valdata_2022.json").read_text("utf-8"))
    ny = v
    bas = schema.bygg_valdata(2018, v["distrikt"][:-1])
    s = schema.swing(ny, bas)
    for val in ("rd", "rf", "kf"):
        assert s["kohort"][val]["helomrade"] is False
        assert s["kohort"][val]["antal"] == 22, "de 22 distrikt som finns kvar i bas är jämförbara"


def test_swing_samma_yta_false_stanger_av_helomrade():
    v = json.loads((ROT / "data" / "valdata_2022.json").read_text("utf-8"))
    s = schema.swing(v, v, samma_yta=False)
    for val in ("rd", "rf", "kf"):
        assert s["kohort"][val]["helomrade"] is False


def test_swing_samma_yta_true_kraver_alla_raknade():
    bas_d = [_d("1", "A", True, {"V": 20, "S": 80}, 100), _d("2", "B", True, {"V": 50, "S": 50}, 100)]
    bas = {"meta": {"ar": 2018}, "distrikt": bas_d, "aggregat": _agg(bas_d)}
    ny_d = [_d("1", "A", True, {"V": 30, "S": 70}, 100), _d("2", "B", False, {}, 0)]
    ny = {"meta": {"ar": 2022}, "distrikt": ny_d, "aggregat": _agg(ny_d)}
    s = schema.swing(ny, bas, samma_yta=True)
    assert s["kohort"]["rd"]["helomrade"] is False, "distrikt 2 är oräknat: samma_yta=True kräver ändå att alla i ny är räknade"


def test_swing_omrade_delvis_raknat_kohort_pa_jamforbara_delmangd():
    bas_d = [_d(str(i), f"D{i}", True, {"V": 20 + i, "S": 80 - i}, 100) for i in range(1, 10)]
    bas = {"meta": {"ar": 2022}, "distrikt": bas_d, "aggregat": _agg(bas_d)}
    ny_d = [_d(str(i), f"D{i}", True, {"V": 30 + i, "S": 70 - i}, 100) for i in range(1, 10)]
    ny_d.append(_d("10", "D10", False, {}, 0))
    ny = {"meta": {"ar": 2026}, "distrikt": ny_d, "aggregat": _agg(ny_d)}
    s = schema.swing(ny, bas, jamforbara=["1", "2", "3"])
    assert s["kohort"]["rd"]["antal"] == 3, "9 distrikt räknade, bara 3 av dem jämförbara"
    forvantat_ny = schema._summa([d for d in ny_d if d["kod"] in ("1", "2", "3")], "rd")
    forvantat_bas = schema._summa([d for d in bas_d if d["kod"] in ("1", "2", "3")], "rd")
    assert s["majorna"]["rd"] == schema._diff(
        forvantat_ny["roster"], forvantat_ny["giltiga"], forvantat_bas["roster"], forvantat_bas["giltiga"])


def test_swing_omrade_dar_bara_ett_val_ar_raknat():
    bas_d = [_d("1", "A", True, {"V": 20, "S": 80}, 100)]
    ny_d = [_d("1", "A", True, {"V": 30, "S": 70}, 100)]
    bas = {"meta": {"ar": 2022}, "distrikt": bas_d, "aggregat": _agg(bas_d)}
    ny = {"meta": {"ar": 2026}, "distrikt": ny_d, "aggregat": _agg(ny_d)}
    s = schema.swing(ny, bas, jamforbara=["1"])
    assert s["kohort"]["rf"] == {"antal": 0, "totalt": 1, "helomrade": False, "koder": []}
    assert s["majorna"]["rf"] == {}
    assert "rf" not in s["distrikt"]["1"]


def test_swing_verkliga_data_mot_sig_sjalv_ger_bara_nollor():
    v = json.loads((ROT / "data" / "valdata_2022.json").read_text("utf-8"))
    s = schema.swing(v, v)
    assert len(s["distrikt"]) == 23
    assert s["ej_jamforbara"] == {}
    for val in ("rd", "rf", "kf"):
        assert s["kohort"][val]["helomrade"] is True
        assert s["majorna"][val] and all(x == 0.0 for x in s["majorna"][val].values())
    for kod, per_val in s["distrikt"].items():
        for val, diffar in per_val.items():
            assert all(x == 0.0 for x in diffar.values())
