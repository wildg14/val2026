from pathlib import Path

import pytest

from scripts import valnatt
from scripts.valmyndigheten import MAJORNA_KODER, NYCKELPARTIER, OVRIGA, SummaFel

GENREP = Path("/Users/daniel/code/Temp/Historiska dokument/dl_webb/genrep2026/unz")
KF = GENREP / "Genrep_2026_preliminar_1480_KF" / "Genrep_2026_preliminar_rostfordelning_1480_KF.json"
RD = GENREP / "Genrep_2026_preliminar_00_RD" / "Genrep_2026_preliminar_rostfordelning_00_RD.json"
RF = GENREP / "Genrep_2026_preliminar_14_RF" / "Genrep_2026_preliminar_rostfordelning_14_RF.json"
finns = pytest.mark.skipif(not (KF.exists() and RD.exists() and RF.exists()), reason="genrep-filerna saknas")


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


def test_las_rostfordelning_ogiltiga_fel_form_ger_formatfel():
    d = distrikt("14800526", [("V", "Vänsterpartiet", 10)])
    d["rostfordelning"]["rosterEjPaverkaMandat"] = "x"
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_rostfordelning(fil("KF", [d]), koder=["14800526"])


MANDAT_RD = GENREP / "Genrep_2026_preliminar_00_RD" / "Genrep_2026_preliminar_mandatfordelning_00_RD.json"
SUMM_RD = GENREP / "Genrep_2026_preliminar_00_RD" / "Genrep_2026_preliminar_summering_RD.json"
MANDAT_RF = GENREP / "Genrep_2026_preliminar_14_RF" / "Genrep_2026_preliminar_mandatfordelning_14_RF.json"
SUMM_RF = GENREP / "Genrep_2026_preliminar_14_RF" / "Genrep_2026_preliminar_summering_RF.json"
MANDAT_KF = GENREP / "Genrep_2026_preliminar_1480_KF" / "Genrep_2026_preliminar_mandatfordelning_1480_KF.json"


def omrade(namn, partier, ovriga=0, ogiltiga=0, rostberattigade=10000, raknade=5, totalt=5, **extra):
    giltiga = sum(n for _, _, n in partier) + ovriga
    return {"namn": namn, "totaltAntalRoster": giltiga + ogiltiga, "antalRostberattigade": rostberattigade,
            "antalValdistriktRaknade": raknade, "antalValdistriktSomSkaRaknas": totalt,
            "rostfordelning": {"rosterPaverkaMandat": {"antalRoster": giltiga, "partiRoster": [post(f, b, n) for f, b, n in partier],
                                                        "rosterOvrigaPartier": {"antalRoster": ovriga}},
                               "rosterEjPaverkaMandat": {"antalRoster": ogiltiga}}, **extra}


def test_aggregat_2026_syntetiskt_rd():
    mandat = {"valomrade": omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 600), ("M", "Moderaterna", 400)], ovriga=0, ogiltiga=10)}
    summering = {"kommuner": [{"kommunkod": "0114", **omrade("Upplands Väsby", [("S", "Arbetarepartiet-Socialdemokraterna", 1)])},
                              {"kommunkod": "1480", **omrade("Göteborg", [("S", "Arbetarepartiet-Socialdemokraterna", 60), ("M", "Moderaterna", 40)], ogiltiga=2, rostberattigade=125)}]}
    agg = valnatt.aggregat_2026("rd", mandat, summering)
    assert agg["riket"]["namn"] == "Riket" and agg["riket"]["andel"]["S"] == pytest.approx(0.6)
    assert "V" not in agg["riket"]["andel"], "V redovisas inte i det syntetiska objektets partiRoster och saknas därför"
    assert agg["riket"]["giltiga"] == 1000 and agg["riket"]["rostande"] == 1010 and agg["riket"]["valdeltagande"] == pytest.approx(0.101)
    assert "Övriga" not in agg["riket"]["andel"]
    assert agg["goteborg"]["namn"] == "Göteborg" and agg["goteborg"]["giltiga"] == 100 and agg["goteborg"]["valdeltagande"] == pytest.approx(102 / 125)
    assert agg["riket"]["antal_distrikt"] == 5


def test_aggregat_2026_rf_och_kf():
    mandat = {"valomrade": omrade("Västra Götaland", [("V", "Vänsterpartiet", 10)])}
    agg = valnatt.aggregat_2026("rf", mandat, None)
    assert agg["riket"]["namn"] == "Västra Götaland" and "goteborg" not in agg
    agg = valnatt.aggregat_2026("kf", {"valomrade": omrade("Göteborg", [("V", "Vänsterpartiet", 10)])})
    assert list(agg) == ["goteborg"] and agg["goteborg"]["andel"]["V"] == 1.0


def test_aggregat_avvisar_fel_summa():
    mandat = {"valomrade": omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 600)])}
    mandat["valomrade"]["rostfordelning"]["rosterPaverkaMandat"]["antalRoster"] = 601
    with pytest.raises(SummaFel):
        valnatt.aggregat_2026("rd", mandat)


def test_omrade_avvisar_fel_summa_rostande():
    v = omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 100)])
    v["totaltAntalRoster"] = 999
    with pytest.raises(SummaFel):
        valnatt.aggregat_2026("rd", {"valomrade": v})


def test_omrade_utan_ogiltigfalt_hoppar_over_summakontroll():
    v = omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 100)])
    v["totaltAntalRoster"] = 999
    del v["rostfordelning"]["rosterEjPaverkaMandat"]
    agg = valnatt.aggregat_2026("rd", {"valomrade": v})
    assert agg["riket"]["giltiga"] == 100, "utan rosterEjPaverkaMandat görs ingen summakontroll av röstande"


def test_omrade_ogiltiga_tomt_dict_eller_lista_hoppar_over_summakontroll():
    v = omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 100)])
    v["totaltAntalRoster"] = 999
    v["rostfordelning"]["rosterEjPaverkaMandat"] = {}
    agg = valnatt.aggregat_2026("rd", {"valomrade": v})
    assert agg["riket"]["giltiga"] == 100, "tomt rosterEjPaverkaMandat ska inte ge SummaFel eller AttributeError"

    v2 = omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 100)])
    v2["totaltAntalRoster"] = 999
    v2["rostfordelning"]["rosterEjPaverkaMandat"] = []
    agg2 = valnatt.aggregat_2026("rd", {"valomrade": v2})
    assert agg2["riket"]["giltiga"] == 100, "rosterEjPaverkaMandat som lista ska inte ge SummaFel eller AttributeError"

    v3 = omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 100)], ogiltiga=5)
    v3["rostfordelning"]["rosterEjPaverkaMandat"] = [{"antalRoster": 5}]
    agg3 = valnatt.aggregat_2026("rd", {"valomrade": v3})
    assert agg3["riket"]["giltiga"] == 100, "en icke-tom lista ska också hoppa över summakontrollen, inte ge AttributeError"


def test_aggregat_valdeltagande_mot_raknade_distrikt():
    """Nämnaren ska vara röstberättigade i räknade distrikt, inte hela väljarkåren, annars blir kvoten
    fel så länge räkningen pågår (t ex 12,5 procent i stället för 83 tidigt på valkvällen)."""
    mandat = {"valomrade": omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 833000)],
                                   rostberattigade=7996396, raknade=900, totalt=6626,
                                   antalRostberattigadeIRaknadeValdistrikt=1000000)}
    agg = valnatt.aggregat_2026("rd", mandat)
    assert agg["riket"]["rostberattigade"] == 1000000
    assert agg["riket"]["valdeltagande"] == pytest.approx(0.833)


def test_aggregat_giltiga_noll_ger_ingen_nyckel():
    mandat = {"valomrade": omrade("Riket", [])}
    agg = valnatt.aggregat_2026("rd", mandat)
    assert "riket" not in agg


def test_aggregat_rostberattigade_null_ger_ingen_kvot():
    mandat = {"valomrade": omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 100)],
                                   rostberattigade=None, antalRostberattigadeIRaknadeValdistrikt=None)}
    agg = valnatt.aggregat_2026("rd", mandat)
    assert agg["riket"]["valdeltagande"] is None and agg["riket"]["rostberattigade"] == 0


def test_las_valomrade_rot_ej_dict_ger_formatfel():
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_valomrade([], "rd")


def test_las_kommun_rot_ej_dict_ger_formatfel():
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_kommun([], "rd")


def test_las_kommun_kommun_saknas_ger_formatfel():
    summering = {"kommuner": [{"kommunkod": "0114",
                               **omrade("Upplands Väsby", [("S", "Arbetarepartiet-Socialdemokraterna", 1)])}]}
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_kommun(summering, "rd")


def test_las_kommun_hoppar_over_icke_dict_element():
    summering = {"kommuner": ["felformat element",
                              {"kommunkod": "1480", **omrade("Göteborg", [("S", "Arbetarepartiet-Socialdemokraterna", 1)])}]}
    agg = valnatt.las_kommun(summering, "rd")
    assert agg["namn"] == "Göteborg"


def test_las_valomrade_avvisar_fel_valtyp():
    mandat = {"valtyp": "RF", "valomrade": omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 100)])}
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_valomrade(mandat, "rd")


def test_las_kommun_avvisar_fel_valtyp():
    summering = {"valtyp": "KF", "kommuner": [{"kommunkod": "1480",
                                               **omrade("Göteborg", [("S", "Arbetarepartiet-Socialdemokraterna", 1)])}]}
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_kommun(summering, "rd")


def test_las_valomrade_valtyp_null_behandlas_som_saknad():
    mandat = {"valtyp": None, "valomrade": omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 100)])}
    agg = valnatt.las_valomrade(mandat, "rd")
    assert agg["giltiga"] == 100


def test_las_valomrade_okant_val_ger_formatfel_inte_keyerror():
    mandat = {"valomrade": omrade("Riket", [("S", "Arbetarepartiet-Socialdemokraterna", 100)])}
    with pytest.raises(valnatt.FormatFel):
        valnatt.las_valomrade(mandat, "ogiltigt")


@finns
def test_genrep_aggregat_stammer_med_filerna():
    agg = valnatt.aggregat_2026("rd", MANDAT_RD, SUMM_RD)
    assert agg["riket"]["giltiga"] == 6877640 and agg["riket"]["antal_distrikt"] == 6626
    assert agg["goteborg"]["giltiga"] == 383788 and agg["goteborg"]["rostande"] == 388547 and agg["goteborg"]["rostberattigade"] == 458909
    assert agg["riket"]["andel"]["S"] == pytest.approx(2106282 / 6877640)
    agg = valnatt.aggregat_2026("rf", MANDAT_RF, SUMM_RF)
    assert agg["riket"]["namn"] == "Västra Götaland" and agg["riket"]["giltiga"] == 1189467 and agg["goteborg"]["giltiga"] == 402846
    assert "FI" not in agg["riket"]["andel"], "FI redovisas inte i regionfilens valomrade (bara DEM och PNy utöver riksdagspartierna)"
    agg = valnatt.aggregat_2026("kf", MANDAT_KF)
    assert agg["goteborg"]["giltiga"] == 403007 and agg["goteborg"]["andel"]["D"] == 0.0
    assert "K" not in agg["goteborg"]["andel"], "K redovisas inte i kommunfilens valomrade (bara DEM, FI och PNy utöver riksdagspartierna, alla noll)"


@finns
def test_genrep_rf_saknar_fi():
    ra = valnatt.las_rostfordelning(RF, kommunkod="1480")
    assert ra["val"] == "rf"
    assert len(ra["distrikt"]) == 23
    assert all("FI" not in d["roster"] for d in ra["distrikt"].values() if d["raknat"]), \
        "FI förekommer inte i något distrikt i regionfilens röstfördelning"
    assert "D" in ra["distrikt"]["14800526"]["roster"], "DEM står med i Svalebos partiRoster (0 röster)"


def test_riksdag_verklig_syntetiskt():
    obj = {"valomrade": {"totaltAntalMandat": 5, "mandatfordelning": {"partiLista": [
        {"partiforkortning": "S", "partibeteckning": "Arbetarepartiet-Socialdemokraterna", "antalMandat": 3},
        {"partiforkortning": "M", "partibeteckning": "Moderaterna", "antalMandat": 2},
        {"partiforkortning": "PNy", "partibeteckning": "Partiet Nyans", "antalMandat": 0}]}}}
    assert valnatt.riksdag_verklig(obj) == {"S": 3, "M": 2}


def test_riksdag_verklig_tom_nar_mandatfordelning_saknas():
    assert valnatt.riksdag_verklig({"valomrade": {"mandatfordelning": None}}) == {}


def test_riksdag_verklig_rot_ej_dict_ger_formatfel():
    with pytest.raises(valnatt.FormatFel):
        valnatt.riksdag_verklig([])


def test_riksdag_verklig_avvisar_fel_valtyp():
    obj = {"valtyp": "RF", "valomrade": {"mandatfordelning": {"partiLista": [
        {"partiforkortning": "S", "partibeteckning": "Arbetarepartiet-Socialdemokraterna", "antalMandat": 3}]}}}
    with pytest.raises(valnatt.FormatFel):
        valnatt.riksdag_verklig(obj)


def test_riksdag_verklig_partilista_fel_form_ger_tomt():
    assert valnatt.riksdag_verklig({"valomrade": {"mandatfordelning": {"partiLista": "sönder"}}}) == {}


def test_riksdag_verklig_hoppar_over_icke_dict_element():
    obj = {"valomrade": {"mandatfordelning": {"partiLista": [
        "felformat element",
        {"partiforkortning": "S", "partibeteckning": "Arbetarepartiet-Socialdemokraterna", "antalMandat": 3}]}}}
    assert valnatt.riksdag_verklig(obj) == {"S": 3}


def test_riksdag_verklig_reservkod_aldrig_tom():
    obj = {"valomrade": {"mandatfordelning": {"partiLista": [
        {"partibeteckning": "Nytt Parti", "antalMandat": 15}]}}}
    assert valnatt.riksdag_verklig(obj) == {"Nytt Parti": 15}


@finns
def test_genrep_riksdag_verklig_summerar_349():
    m = valnatt.riksdag_verklig(MANDAT_RD)
    assert sum(m.values()) == 349 and set(m) <= {"V", "S", "MP", "SD", "M", "C", "L", "KD"}
