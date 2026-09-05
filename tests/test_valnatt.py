from pathlib import Path

import pytest

from scripts import valnatt
from scripts.valmyndigheten import MAJORNA_KODER, NYCKELPARTIER, OVRIGA, SummaFel

GENREP = Path("/Users/daniel/code/Temp/Historiska dokument/dl_webb/genrep2026/unz")
KF = GENREP / "Genrep_2026_preliminar_1480_KF" / "Genrep_2026_preliminar_rostfordelning_1480_KF.json"
RD = GENREP / "Genrep_2026_preliminar_00_RD" / "Genrep_2026_preliminar_rostfordelning_00_RD.json"
finns = pytest.mark.skipif(not (KF.exists() and RD.exists()), reason="genrep-filerna saknas")


def post(forkortning, beteckning, antal):
    return {"partiforkortning": forkortning, "partibeteckning": beteckning, "antalRoster": antal, "andelRoster": 0.0}


def distrikt(kod, partier, ovriga=0, ogiltiga=0, rostberattigade=1000, tid="2026-09-13T20:10:00", status="Kan jämföras"):
    giltiga = sum(n for _, _, n in partier) + ovriga
    return {"namn": f"Västra Centrum, D{kod[-2:]}", "valdistriktstyp": "valdistrikt", "rapporteringsTid": tid,
            "totaltAntalRoster": giltiga + ogiltiga, "antalRostberattigade": rostberattigade, "valdistriktskod": kod,
            "kommunkod": "1480", "lankod": "14", "valdistriktskodForegaendeVal": [kod], "statusJamforelse": status,
            "rostfordelning": {"rosterPaverkaMandat": {"antalRoster": giltiga, "partiRoster": [post(f, b, n) for f, b, n in partier],
                                                        "rosterOvrigaPartier": {"antalRoster": ovriga}},
                               "rosterEjPaverkaMandat": {"antalRoster": ogiltiga}}}


def fil(valtyp, distrikt_lista, test=True):
    return {"valtillfalle": "Test", "rakningstillfalle": "preliminär", "valtyp": valtyp, "valdatum": "2026-09-13",
            "tidigareValdatum": "2022-09-11", "test": test, "senasteUppdateringstid": "2026-09-13T20:15:00",
            "antalValdistriktRaknade": sum(1 for d in distrikt_lista if d["rapporteringsTid"]),
            "antalValdistriktSomSkaRaknas": len(distrikt_lista), "valdistrikt": distrikt_lista}


def test_parti_2026_mappar_beteckning_forkortning_och_okant():
    assert valnatt.parti_2026(post("S", "Arbetarepartiet-Socialdemokraterna", 1)) == "S"
    assert valnatt.parti_2026(post("L", "Liberalerna (tidigare Folkpartiet)", 1)) == "L"
    assert valnatt.parti_2026(post("DEM", "Demokraterna", 1)) == "D"
    assert valnatt.parti_2026(post("DEM", "Något annat namn", 1)) == "D", "förkortningen räcker när beteckningen är okänd"
    assert valnatt.parti_2026(post("K", "Kommunistiska Partiet", 1)) == "K"
    assert valnatt.parti_2026(post("PNy", "Partiet Nyans", 1)) is None


def test_las_rostfordelning_syntetisk_kf():
    obj = fil("KF", [distrikt("14800526", [("V", "Vänsterpartiet", 300), ("S", "Arbetarepartiet-Socialdemokraterna", 200),
                                           ("DEM", "Demokraterna", 30), ("PNy", "Partiet Nyans", 10)], ovriga=5, ogiltiga=7),
                     distrikt("14800530", [], tid=None, status="Ej jämförbart")])
    ra = valnatt.las_rostfordelning(obj, koder=["14800526", "14800530"])
    assert ra["val"] == "kf" and ra["meta"]["test"] is True and ra["meta"]["raknade"] == 1 and ra["meta"]["totalt"] == 2
    d = ra["distrikt"]["14800526"]
    assert d["raknat"] is True and d["namn"] == "D26" and d["jamforbar"] is True and d["kod_forra"] == ["14800526"]
    assert d["roster"]["V"] == 300 and d["roster"]["D"] == 30 and d["roster"][OVRIGA] == 15, "PNy och rosterOvrigaPartier hamnar i Övriga"
    assert d["giltiga"] == 545 and d["rostande"] == 552 and d["rostberattigade"] == 1000
    assert d["okanda"] == {"PNy": 10}
    assert set(d["roster"]) == {"V", "S", "D", OVRIGA}, "bara partier som står i partiRoster; K, MP med flera redovisas inte i filen och saknas därför"
    o = ra["distrikt"]["14800530"]
    assert o["raknat"] is False and o["jamforbar"] is False and o["roster"] == {}


def test_las_rostfordelning_avvisar_fel_summa():
    d = distrikt("14800526", [("V", "Vänsterpartiet", 300)])
    d["rostfordelning"]["rosterPaverkaMandat"]["antalRoster"] = 301
    with pytest.raises(SummaFel):
        valnatt.las_rostfordelning(fil("KF", [d]), koder=["14800526"])


def test_las_rostfordelning_avvisar_fel_valtyp_och_saknad_lista():
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_rostfordelning({"valtyp": "E", "valdistrikt": []}, koder=MAJORNA_KODER)
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_rostfordelning({"valtyp": "RD"}, koder=MAJORNA_KODER)


def test_raknat_regeln_ar_defensiv():
    d = distrikt("14800526", [("V", "Vänsterpartiet", 10)])
    assert valnatt.ar_raknat(d)
    assert not valnatt.ar_raknat({**d, "rapporteringsTid": ""})
    assert not valnatt.ar_raknat({**d, "totaltAntalRoster": 0})
    assert not valnatt.ar_raknat({**d, "rostfordelning": {"rosterPaverkaMandat": {"antalRoster": 0, "partiRoster": []}}})


@finns
def test_genrep_kf_svalebo():
    ra = valnatt.las_rostfordelning(KF)
    assert ra["val"] == "kf" and ra["meta"]["raknade"] == 397 and ra["meta"]["totalt"] == 397
    assert ra["meta"]["antal_i_omradet"] == 397, "hela Göteborg i kommunfilen"
    assert len(ra["distrikt"]) == 23
    d = ra["distrikt"]["14800526"]
    assert d["namn"] == "Svalebo" and d["giltiga"] == 905 and d["rostande"] == 919 and d["rostberattigade"] == 1102
    assert d["roster"]["V"] == 46 and d["roster"]["S"] == 283 and d["roster"]["M"] == 165
    assert sum(d["roster"].values()) == 905
    assert "K" not in d["roster"] and "FI" in d["roster"], "K är inte rapportparti i den preliminära kommunfilen"
    assert ra["distrikt"]["14800533"]["namn"] == "Sandarna"
    assert sum(1 for d in ra["distrikt"].values() if d["jamforbar"]) == 14
    assert sorted(k for k, d in ra["distrikt"].items() if not d["jamforbar"]) == \
        ["14800529", "14800530", "14800531", "14800532", "14800533", "14800534", "14800535", "14800538", "14800541"]


@finns
def test_genrep_rd_goteborg_antal():
    ra = valnatt.las_rostfordelning(RD, kommunkod="1480")
    assert ra["val"] == "rd" and ra["meta"]["totalt"] == 6626 and ra["meta"]["antal_i_omradet"] == 397
    assert len(ra["distrikt"]) == 23 and ra["distrikt"]["14800526"]["roster"]["S"] == 275
    assert set(NYCKELPARTIER["rd"]) <= set(ra["distrikt"]["14800526"]["roster"]), "alla åtta riksdagspartier är rapportpartier i riksdagsfilen"


def test_las_rostfordelning_rot_ej_dict_ger_formatfel():
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_rostfordelning([], koder=MAJORNA_KODER)


def test_las_rostfordelning_dubblerad_kod_ger_formatfel():
    d1 = distrikt("14800526", [("V", "Vänsterpartiet", 10)])
    d2 = distrikt("14800526", [("S", "Arbetarepartiet-Socialdemokraterna", 20)])
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_rostfordelning(fil("KF", [d1, d2]), koder=["14800526"])


def test_las_rostfordelning_avvisar_fel_summa_rostande():
    d = distrikt("14800526", [("V", "Vänsterpartiet", 300)], ogiltiga=7)
    d["totaltAntalRoster"] = 999
    with pytest.raises(SummaFel):
        valnatt.las_rostfordelning(fil("KF", [d]), koder=["14800526"])


def test_las_rostfordelning_kod_forra_strang_och_none():
    d_strang = distrikt("14800526", [("V", "Vänsterpartiet", 10)])
    d_strang["valdistriktskodForegaendeVal"] = "14800999"
    d_none = distrikt("14800527", [("V", "Vänsterpartiet", 10)])
    d_none["valdistriktskodForegaendeVal"] = None
    ra = valnatt.las_rostfordelning(fil("KF", [d_strang, d_none]), koder=["14800526", "14800527"])
    assert ra["distrikt"]["14800526"]["kod_forra"] == ["14800999"], "sträng blir en lista med ett element"
    assert ra["distrikt"]["14800527"]["kod_forra"] == [], "None blir en tom lista"


def test_las_rostfordelning_rostberattigade_null_ger_noll():
    d = distrikt("14800526", [("V", "Vänsterpartiet", 10)])
    d["antalRostberattigade"] = None
    ra = valnatt.las_rostfordelning(fil("KF", [d]), koder=["14800526"])
    assert ra["distrikt"]["14800526"]["rostberattigade"] == 0
