from pathlib import Path

import pytest

from scripts import valmyndigheten as vm

ROT = Path(__file__).resolve().parents[1]
XLSX = ROT / "majorna-valresultat-2022.xlsx"
RAD_RD = ROT / "Roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-riksdagsvalet-2022.xlsx"
RAD_RF = ROT / "roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-regionval-2022.xlsx"


def test_partikod():
    assert vm.partikod(" Arbetarepartiet-Socialdemokraterna") == "S"
    assert vm.partikod("Liberalerna (tidigare Folkpartiet)") == "L"
    assert vm.partikod(" Demokraterna") == "D"
    assert vm.partikod("Piratpartiet") is None


def test_las_kurerad_svalebo():
    k = vm.las_kurerad(XLSX)
    d = k["distrikt"]["14800526"]
    assert d["namn"] == "Svalebo"
    assert d["rd"] == {"V": 179, "S": 217, "MP": 114, "SD": 102, "M": 60, "C": 43, "L": 42, "KD": 25, "Övriga": 15}
    assert d["giltiga"]["rd"] == 797 and d["rostande"]["rd"] == 805 and d["rostberattigade"]["rd"] == 1073
    assert d["kf"]["K"] == 10
    assert len(k["distrikt"]) == 23
    assert k["total"]["rd"]["roster"]["V"] == 5793
    assert k["total"]["kf"]["giltiga"] == 21620
    assert k["sammanfattning"]["goteborg"]["rd"]["andel"]["V"] == pytest.approx(0.1284978810, abs=1e-9)
    assert k["sammanfattning"]["riket"]["rd"]["valdeltagande"] == pytest.approx(0.842118659, abs=1e-9)
    assert k["sammanfattning"]["riket"]["rf"]["andel"]["V"] == pytest.approx(0.1004001994, abs=1e-9)
    assert "kf" not in k["sammanfattning"]["riket"]
    assert k["sammanfattning"]["goteborg"]["kf"]["valdeltagande"] == pytest.approx(0.7649, abs=1e-9)


def test_validera_huvud_avvisar_fel_huvud():
    with pytest.raises(vm.FormatFel):
        vm.validera_huvud(["Kommun", "Parti", "Röster"])


@pytest.mark.skipif(not RAD_RD.exists(), reason="rådatafil saknas")
def test_rafil_rd_matchar_kurerad():
    ra = vm.las_rafil(RAD_RD, koder=vm.MAJORNA_KODER)
    assert ra["val"] == "rd"
    assert ra["distrikt"]["14800526"]["namn"] == "Västra Centrum, Svalebo"
    d = vm.till_distrikt(ra["distrikt"]["14800526"], "rd")
    k = vm.las_kurerad(XLSX)["distrikt"]["14800526"]
    assert d["roster"] == k["rd"]
    assert (d["giltiga"], d["rostande"], d["rostberattigade"]) == (797, 805, 1073)
    agg = vm.aggregat_andelar(ra)
    assert agg["goteborg"]["andel"]["V"] == pytest.approx(0.1284978810, abs=1e-9)
    assert agg["goteborg"]["valdeltagande"] == pytest.approx(0.8071, abs=5e-5)
    assert agg["riket"]["andel"]["S"] == pytest.approx(0.3032545689, abs=1e-9)
    assert agg["riket"]["valdeltagande"] == pytest.approx(0.842118659, abs=1e-9)


@pytest.mark.skipif(not RAD_RF.exists(), reason="rådatafil saknas")
def test_rafil_rf_region_aggregat():
    ra = vm.las_rafil(RAD_RF, koder=vm.MAJORNA_KODER)
    assert ra["val"] == "rf"
    agg = vm.aggregat_andelar(ra)
    assert agg["riket"]["andel"]["V"] == pytest.approx(0.1004001994, abs=1e-9)
    assert agg["riket"]["valdeltagande"] == pytest.approx(0.8034920378, abs=1e-9)
    assert agg["goteborg"]["valdeltagande"] == pytest.approx(0.7629, abs=5e-5)
    d = vm.till_distrikt(ra["distrikt"]["14800530"], "rf")
    assert d["roster"]["D"] == 31 and d["roster"]["FI"] == 3


def test_till_distrikt_kastar_summafel():
    post = {"namn": "Test", "roster": {"vänsterpartiet": 10, "moderaterna": 5},
            "giltiga": 16, "ogiltiga": 1, "rostande": 17, "rostberattigade": 20}
    with pytest.raises(vm.SummaFel):
        vm.till_distrikt(post, "rd")
