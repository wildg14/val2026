import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import openpyxl
import pytest

from scripts.valmyndigheten import MAJORNA_KODER

ROT = Path(__file__).resolve().parents[1]
RD = ROT / "Roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-riksdagsvalet-2022.xlsx"
RF = ROT / "roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-regionval-2022.xlsx"
KF = ROT / "roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-kommunval-2022.xlsx"
GENREP = Path("/Users/daniel/code/Temp/Historiska dokument/dl_webb/genrep2026")
GENREP_SLUTLIG_KF = GENREP / "Genrep_2026_slutlig_1480_KF.zip"
JAMFORELSE = Path("/Users/daniel/code/Temp/Historiska dokument/dl_webb/2026/valdistrikt-jamforelser-mellan-2022-och-2026.xlsx")
genrep_finns = pytest.mark.skipif(not (GENREP / "index_genrep2026.md5").exists(), reason="genrep-filerna saknas")
genrep_slutlig_kf_finns = pytest.mark.skipif(not GENREP_SLUTLIG_KF.exists(), reason="slutliga KF-genrepfilen saknas")
EJ_JAMFORBARA = ["14800529", "14800530", "14800531", "14800532", "14800533", "14800534", "14800535", "14800538", "14800541"]


def kor(*args):
    return subprocess.run([sys.executable, "scripts/uppdatera_2026.py", *args], cwd=ROT, capture_output=True, text=True)


def hamta_lokalt(tmp_path):
    r = subprocess.run([sys.executable, "scripts/hamta_2026.py", "--lokal", str(GENREP), "--ut", str(tmp_path / "h"), "--utan-signatur"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return Path(r.stdout.strip().splitlines()[-1].split("MAPP: ", 1)[1])


def doktorera_raknade(mapp, ut, noll):
    """Kopierar en valnattsmapp (rd/, rf/, kf/) från hamta_lokalt till `ut` och nollställer räkningen
    (rapporteringsTid till "" och totaltAntalRoster till 0) för de distriktskoder som anges per val i
    `noll` ({val: {koder}}). antalValdistriktRaknade i filhuvudet minskas med antalet distrikt som
    faktiskt var räknade innan ändringen, så filhuvudet stämmer med det doktorerade innehållet."""
    shutil.copytree(mapp, ut)
    for val, koder in noll.items():
        koder = {str(k) for k in koder}
        for path in sorted((ut / val).glob("*_rostfordelning_*.json")):
            obj = json.loads(path.read_text("utf-8"))
            paverkade = 0
            for d in obj.get("valdistrikt", []):
                if str(d.get("valdistriktskod")) in koder:
                    if d.get("rapporteringsTid"):
                        paverkade += 1
                    d["rapporteringsTid"] = ""
                    d["totaltAntalRoster"] = 0
            if paverkade:
                obj["antalValdistriktRaknade"] = max(0, int(obj.get("antalValdistriktRaknade", 0)) - paverkade)
            path.write_text(json.dumps(obj, ensure_ascii=False), "utf-8")
    return ut


@pytest.mark.skipif(not RD.exists(), reason="rådatafil saknas")
def test_bara_rd_ger_tomma_rf_kf_och_swing(tmp_path):
    r = kor("--rd", str(RD), "--ut", str(tmp_path), "--ar", "2026", "--status", "preliminar", "--tid", "2026-09-13T20:45:00")
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["ar"] == 2026 and v["meta"]["status"] == "preliminar"
    assert v["meta"]["uppdaterad"] == "2026-09-13T20:45:00"
    assert v["meta"]["valnatt"] == {"raknade": 23, "totalt": 23}
    d = {x["kod"]: x for x in v["distrikt"]}["14800530"]
    assert d["rd"]["V"] == 287 and d["rf"] == {} and d["kf"] == {}
    assert v["aggregat"]["majorna"]["rd"]["giltiga"] == 21308
    assert v["aggregat"]["riket"]["rd"]["andel"]["S"] == pytest.approx(0.3032545689, abs=1e-9)
    assert v["mandat"]["riksdag_majorna"] == {"V": 99, "S": 94, "MP": 57, "SD": 37, "M": 32, "C": 15, "L": 15}
    assert v["mandat"].get("riksdag_verklig", {}) == {}
    s = json.loads((tmp_path / "swing_2026.json").read_text("utf-8"))
    assert s["bas"] == 2022 and s["ar"] == 2026
    # xlsx-vägen får flaggor ur jämförelsefilen när den finns (--jamforelsefil), annars antas allt jämförbart
    assert "14800530" in s["ej_jamforbara"] or s["distrikt"].get("14800530", {}).get("rd", {}).get("V") == 0.0
    # 14800530 kan ha hamnat i ej_jamforbara i stället för distrikt (samma orsak som ovan)
    assert s["distrikt"].get("14800530", {}).get("kf") is None
    assert (tmp_path / "valdata_2026.js").exists() and (tmp_path / "swing_2026.js").exists()


def test_csv_reservvag(tmp_path):
    csv = tmp_path / "valnatt.csv"
    csv.write_text("val;kod;parti;roster\n"
                   "rd;14800530;V;300\nrd;14800530;S;200\nrd;14800530;giltiga;500\n"
                   "rd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026")
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["valnatt"] == {"raknade": 1, "totalt": 23}
    d = {x["kod"]: x for x in v["distrikt"]}
    assert d["14800530"]["rd"] == {"V": 300, "S": 200} and d["14800530"]["raknat"] is True
    assert d["14800526"]["raknat"] is False and d["14800526"]["rd"] == {}
    assert v["aggregat"]["majorna"]["rd"]["giltiga"] == 500


def test_csv_med_felaktig_summa_avbryter(tmp_path):
    csv = tmp_path / "fel.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;giltiga;500\nrd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026")
    assert r.returncode != 0
    assert "14800530" in r.stdout + r.stderr


def test_skadad_valdata_ger_fel_rad_inte_traceback(tmp_path):
    (tmp_path / "valdata_2026.json").write_text('{"meta": {', "utf-8")   # halvskriven under en tidigare körning
    csv = tmp_path / "v.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;giltiga;300\n"
                   "rd;14800530;rostande;300\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026")
    assert r.returncode == 1
    assert "har inte formen av en JSON-fil" in r.stdout + r.stderr
    assert "Traceback" not in r.stdout + r.stderr


def test_skadad_konfig_ger_fel_rad_inte_traceback(tmp_path):
    (tmp_path / "konfig.json").write_text('{"ar": [', "utf-8")   # halvskriven under en tidigare körning
    csv = tmp_path / "v.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;giltiga;300\n"
                   "rd;14800530;rostande;300\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026", "--valnatt")
    assert r.returncode == 1
    assert "konfig.json" in r.stdout + r.stderr and "kunde inte läsas" in r.stdout + r.stderr
    assert "Traceback" not in r.stdout + r.stderr


def test_fel_format_avbryter(tmp_path):
    r = kor("--rd", str(ROT / "majorna-valresultat-2022.xlsx"), "--ut", str(tmp_path), "--ar", "2026")
    assert r.returncode != 0
    assert "roster_" in r.stdout + r.stderr


@pytest.mark.skipif(not (RD.exists() and RF.exists() and KF.exists()), reason="rådatafiler saknas")
def test_repetera_mot_2022():
    r = kor("--repetera")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "REPETITION OK" in r.stdout


@genrep_finns
def test_valnattsmapp_genrep_ger_komplett_valdata_swing_och_konfig(tmp_path):
    mapp = hamta_lokalt(tmp_path)
    ut = tmp_path / "data"
    ut.mkdir()
    (ut / "konfig.json").write_text(json.dumps({"ar": ["2022"], "standardAr": "2022", "valnatt": False, "adress": "x"}), "utf-8")
    r = kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026", "--status", "preliminar", "--tid", "2026-09-13T21:00:00", "--valnatt")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "TESTDATA" in r.stdout + r.stderr, "genrep-filerna har test: true och det ska synas"
    v = json.loads((ut / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["ar"] == 2026 and v["meta"]["status"] == "preliminar" and v["meta"]["test"] is True
    assert v["meta"]["valnatt"] == {"raknade": 23, "totalt": 23}
    d = {x["kod"]: x for x in v["distrikt"]}
    assert d["14800526"]["kf"]["V"] == 46 and d["14800526"]["rd"]["S"] == 275 and d["14800526"]["giltiga"]["kf"] == 905
    assert d["14800533"]["namn"] == "Sandarna"
    assert sum(1 for x in v["distrikt"] if x["jamforbar_mot_bas"]) == 14
    assert sorted(k for k, x in d.items() if x["grans_andrad"]) == EJ_JAMFORBARA
    assert v["aggregat"]["riket"]["rd"]["giltiga"] == 6877640 and v["aggregat"]["riket"]["rd"]["namn"] == "Riket"
    assert v["aggregat"]["riket"]["rf"]["namn"] == "Västra Götaland" and v["aggregat"]["goteborg"]["kf"]["giltiga"] == 403007
    assert sum(v["mandat"]["riksdag_verklig"].values()) == 349 and sum(v["mandat"]["riksdag_majorna"].values()) == 349
    s = json.loads((ut / "swing_2026.json").read_text("utf-8"))
    assert s["bas"] == 2022 and len(s["distrikt"]) == 14 and sorted(s["ej_jamforbara"]) == EJ_JAMFORBARA
    assert "ritades om till 2026" in s["ej_jamforbara"]["14800530"]["mening"]
    assert s["kohort"]["rd"]["helomrade"] is True and "V" in s["majorna"]["rd"]
    k = json.loads((ut / "konfig.json").read_text("utf-8"))
    assert k["ar"] == ["2022", "2026"] and k["standardAr"] == "2026" and k["valnatt"] is True and k["adress"] == "x"
    assert not list(ut.glob("*.tmp"))


@genrep_finns
def test_mindre_eller_tom_import_skriver_inte_over(tmp_path):
    mapp = hamta_lokalt(tmp_path)
    ut = tmp_path / "data"
    ut.mkdir()
    assert kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026").returncode == 0
    fore = (ut / "valdata_2026.json").read_bytes()
    bara_rd = tmp_path / "bara_rd"
    bara_rd.mkdir()
    (bara_rd / "rd").symlink_to(mapp / "rd")
    r = kor("--valnatt-mapp", str(bara_rd), "--ut", str(ut), "--ar", "2026")
    assert r.returncode != 0 and "färre räknade" in r.stdout + r.stderr
    utskrift = r.stdout + r.stderr
    assert "rf: 0 mot 23, kf: 0 mot 23" in utskrift, "valen med talen ska stå samlade på en rad"
    assert utskrift.count("--valnatt-mapp data/valnatt/senaste --tvinga") == 1, "instruktionen ska stå en gång, inte en gång per val"
    assert (ut / "valdata_2026.json").read_bytes() == fore, "filen får inte röras"
    r = kor("--valnatt-mapp", str(bara_rd), "--ut", str(ut), "--ar", "2026", "--tvinga")
    assert r.returncode == 0 and (ut / "valdata_2026.json").read_bytes() != fore


@genrep_finns
def test_skarp_fil_skyddas_mot_ny_testdata(tmp_path):
    """Genrep-filerna har alltid test: true. Tas den flaggan bort ur en befintlig fil (som om den
    vore skarp data) ska en ny testdatakörning stoppas, inte skriva över den i tysthet."""
    mapp = hamta_lokalt(tmp_path)
    ut = tmp_path / "data"
    ut.mkdir()
    assert kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026").returncode == 0
    p = ut / "valdata_2026.json"
    v = json.loads(p.read_text("utf-8"))
    del v["meta"]["test"]
    p.write_text(json.dumps(v, ensure_ascii=False), "utf-8")
    fore = p.read_bytes()
    r = kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026")
    assert r.returncode != 0
    assert "skarp data men den nya filen är testdata" in r.stdout + r.stderr
    assert p.read_bytes() == fore, "filen får inte röras"
    r = kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026", "--tvinga")
    assert r.returncode == 0
    assert p.read_bytes() != fore


@genrep_finns
def test_tom_import_ar_bara_en_varning_och_skriver_med_noll_raknade(tmp_path):
    """Kvällens första körningar (cirka 20.00-21.00) har inget Majornadistrikt räknat i något val.
    Det ska aldrig stoppa skrivningen: filerna skrivs med 0 räknade och valnattsläget slås på."""
    mapp = hamta_lokalt(tmp_path)
    doktorerad = tmp_path / "doktorerad"
    doktorera_raknade(mapp, doktorerad, {val: set(MAJORNA_KODER) for val in ("rd", "rf", "kf")})
    ut = tmp_path / "data"
    r = kor("--valnatt-mapp", str(doktorerad), "--ut", str(ut), "--ar", "2026", "--valnatt")
    assert r.returncode == 0, r.stdout + r.stderr
    utskrift = r.stdout + r.stderr
    assert "inget Majornadistrikt räknat i något val" in utskrift
    assert "FEL:" not in utskrift
    v = json.loads((ut / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["valnatt"] == {"raknade": 0, "totalt": 23}
    k = json.loads((ut / "konfig.json").read_text("utf-8"))
    assert k["ar"] == ["2022", "2026"] and k["standardAr"] == "2026" and k["valnatt"] is True
    s = json.loads((ut / "swing_2026.json").read_text("utf-8"))
    assert s["distrikt"] == {}
    assert all(s["kohort"][val]["antal"] == 0 for val in ("rd", "rf", "kf"))


@genrep_finns
def test_riksdag_verklig_foljer_med_utan_rakade_rd_distrikt(tmp_path):
    """riksdag_verklig (halvcirkeln) ska skrivas så snart mandatfördelningen finns, även innan något
    Majornadistrikt är räknat i riksdagsvalet: den preliminära nationella fördelningen är intressant
    hela kvällen, inte bara efter att Majorna räknats."""
    mapp = hamta_lokalt(tmp_path)
    doktorerad = tmp_path / "doktorerad"
    doktorera_raknade(mapp, doktorerad, {val: set(MAJORNA_KODER) for val in ("rd", "rf", "kf")})
    ut = tmp_path / "data"
    r = kor("--valnatt-mapp", str(doktorerad), "--ut", str(ut), "--ar", "2026")
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((ut / "valdata_2026.json").read_text("utf-8"))
    assert sum(v["mandat"]["riksdag_verklig"].values()) == 349
    assert "riksdag_majorna" not in v["mandat"], "inga Majornaröster räknade i rd: ingen jämkad Majorna-fördelning att visa"


@genrep_finns
def test_delvis_rakat_ger_ratt_antal_och_kohort(tmp_path):
    mapp = hamta_lokalt(tmp_path)
    kvar = sorted(MAJORNA_KODER)[-9:]
    noll = set(MAJORNA_KODER) - set(kvar)
    doktorerad = tmp_path / "doktorerad"
    doktorera_raknade(mapp, doktorerad, {val: noll for val in ("rd", "rf", "kf")})
    ut = tmp_path / "data"
    r = kor("--valnatt-mapp", str(doktorerad), "--ut", str(ut), "--ar", "2026")
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((ut / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["valnatt"]["raknade"] == 9
    s = json.loads((ut / "swing_2026.json").read_text("utf-8"))
    forvantat = sum(1 for k in kvar if k not in EJ_JAMFORBARA)
    assert s["kohort"]["rd"]["antal"] == forvantat


@genrep_finns
def test_mandat_som_inte_summerar_349_varnar(tmp_path):
    mapp = hamta_lokalt(tmp_path)
    andrad = tmp_path / "andrad"
    shutil.copytree(mapp, andrad)
    p = sorted((andrad / "rd").glob("*_mandatfordelning_*.json"))[0]
    obj = json.loads(p.read_text("utf-8"))
    obj["valomrade"]["mandatfordelning"]["partiLista"][0]["antalMandat"] += 1
    p.write_text(json.dumps(obj, ensure_ascii=False), "utf-8")
    ut = tmp_path / "data"
    r = kor("--valnatt-mapp", str(andrad), "--ut", str(ut), "--ar", "2026")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "inte 349" in r.stdout + r.stderr


def test_jamforelsefil_trasig_ger_fel_inte_traceback(tmp_path):
    skrap = tmp_path / "skrap.xlsx"
    skrap.write_text("det här är inte en xlsx-fil, bara skräptext", "utf-8")
    csv = tmp_path / "v.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;giltiga;300\n"
                   "rd;14800530;rostande;300\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026", "--jamforelsefil", str(skrap))
    assert r.returncode == 1
    assert "kunde inte läsas" in r.stdout + r.stderr


@genrep_finns
def test_konflikt_i_jamforbarhet_ger_varning_och_ej_jamforbart_vinner(tmp_path):
    mapp = hamta_lokalt(tmp_path)
    xlsx = tmp_path / "jamforelse.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Jämförelser"
    ws.append(["Valdistriktskod 2026", "Jämförbarhet"])
    ws.append(["14800530", "Kan jämföras"])  # JSON-filerna säger "Ej jämförbart" för 14800530
    wb.save(xlsx)
    ut = tmp_path / "data"
    r = kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026", "--jamforelsefil", str(xlsx))
    assert r.returncode == 0, r.stdout + r.stderr
    utskrift = r.stdout + r.stderr
    assert "14800530" in utskrift and "tvärtom" in utskrift
    v = json.loads((ut / "valdata_2026.json").read_text("utf-8"))
    d = {x["kod"]: x for x in v["distrikt"]}
    assert d["14800530"]["jamforbar_mot_bas"] is False, "konflikt mellan källorna ska avgöras till ej jämförbart"


@genrep_finns
def test_flera_filer_i_valmappen_varnar_med_filnamn(tmp_path):
    mapp = hamta_lokalt(tmp_path)
    kopia = tmp_path / "flera"
    shutil.copytree(mapp, kopia)
    orig = sorted((kopia / "rd").glob("*_rostfordelning_*.json"))[0]
    extra = orig.with_name(orig.stem + "_kopia.json")
    shutil.copy(orig, extra)
    ut = tmp_path / "data"
    r = kor("--valnatt-mapp", str(kopia), "--ut", str(ut), "--ar", "2026")
    assert r.returncode == 0, r.stdout + r.stderr
    utskrift = r.stdout + r.stderr
    assert "2 röstfördelningsfiler" in utskrift
    assert orig.name in utskrift and extra.name in utskrift


@genrep_finns
def test_namnvarning_bara_en_gang_per_distrikt(tmp_path):
    """Sandarna (och andra distrikt vars namn skiljer sig mot 2022) förekommer i rd-, rf- och
    kf-filen; namnvarningen ska ändå bara ges en gång per distrikt och körning, inte en gång per fil."""
    mapp = hamta_lokalt(tmp_path)
    ut = tmp_path / "data"
    r = kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026")
    assert r.returncode == 0, r.stdout + r.stderr
    rader = [rad for rad in (r.stdout + r.stderr).splitlines() if "VARNING" in rad and "Sandarna" in rad]
    assert len(rader) == 1, rader


@genrep_slutlig_kf_finns
def test_okanda_partier_varnas_per_parti_inte_per_distrikt(tmp_path):
    """Genrep_2026_slutlig_1480_KF.zip saknar rd och rf (den finns bara för kf i slutligt läge), så
    den packas upp för hand här i stället för via hamta_2026.py, till en mapp med bara kf/."""
    mapp = tmp_path / "kf_mapp"
    kf = mapp / "kf"
    kf.mkdir(parents=True)
    with zipfile.ZipFile(GENREP_SLUTLIG_KF) as z:
        z.extractall(kf)
    ut = tmp_path / "data"
    r = kor("--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026")
    assert r.returncode == 0, r.stdout + r.stderr
    rader = [rad for rad in (r.stdout + r.stderr).splitlines() if rad.startswith("VARNING: kf: okänt parti")]
    partier = {rad.split("'")[1] for rad in rader}
    assert rader, "genrepfilen ska innehålla minst ett okänt parti över tröskeln"
    assert len(rader) == len(partier), "en varning per parti, inte en per distrikt partiet förekommer i"


@genrep_finns
def test_hamta_lasar_senaste_efter_lyckad_hamtning(tmp_path, monkeypatch):
    """--hamta körs aldrig mot nätet: hamta_2026.main monkeypatchas till att bara returnera 0, och
    en senaste-symlänk till en redan uppackad genrep-mapp läggs dit --hamta förväntar sig den."""
    from scripts import uppdatera_2026

    mapp = hamta_lokalt(tmp_path)
    (tmp_path / "valnatt").mkdir()
    (tmp_path / "valnatt" / "senaste").symlink_to(mapp)
    monkeypatch.setattr(uppdatera_2026.hamta_2026, "main", lambda: 0)
    sparat_argv = sys.argv
    try:
        sys.argv = ["uppdatera_2026.py", "--hamta", "--ut", str(tmp_path), "--ar", "2026"]
        assert uppdatera_2026.main() == 0
    finally:
        sys.argv = sparat_argv
    assert (tmp_path / "valdata_2026.json").exists()


@genrep_finns
def test_testdata_till_repots_data_krav_tvinga(tmp_path, monkeypatch, capsys):
    """Skriptet får aldrig skriva testdata (genrep, test: true) till repots skarpa data/ utan
    --tvinga. ROT monkeypatchas till en tom mapp i tmp_path i stället för den riktiga repo-roten, så
    testet aldrig kan skriva i det riktiga repots data/ ens om spärren skulle vara trasig."""
    from scripts import uppdatera_2026

    mapp = hamta_lokalt(tmp_path)
    fejkrot = tmp_path / "fejkrot"
    fejk_data = fejkrot / "data"
    fejk_data.mkdir(parents=True)
    monkeypatch.setattr(uppdatera_2026, "ROT", fejkrot)
    sparat_argv = sys.argv
    try:
        sys.argv = ["uppdatera_2026.py", "--valnatt-mapp", str(mapp), "--ut", str(fejk_data), "--ar", "2026"]
        with pytest.raises(SystemExit):
            uppdatera_2026.main()
    finally:
        sys.argv = sparat_argv
        for kvarliggande in (fejk_data / "valdata_2026.json", fejk_data / "valdata_2026.js"):
            if kvarliggande.exists():
                kvarliggande.unlink()
    utskrift = capsys.readouterr()
    text = (utskrift.out + utskrift.err).lower()
    assert "testdata" in text and "--tvinga" in text
    assert not (fejk_data / "valdata_2026.json").exists()


@pytest.mark.skipif(not JAMFORELSE.exists(), reason="Valmyndighetens jämförelsefil saknas")
def test_csv_vagen_far_flaggor_ur_jamforelsefilen(tmp_path):
    csv = tmp_path / "v.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;S;200\nrd;14800530;giltiga;500\nrd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026", "--jamforelsefil", str(JAMFORELSE))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2026.json").read_text("utf-8"))
    d = {x["kod"]: x for x in v["distrikt"]}
    assert d["14800530"]["grans_andrad"] is True and d["14800526"]["grans_andrad"] is False
    s = json.loads((tmp_path / "swing_2026.json").read_text("utf-8"))
    assert "14800530" in s["ej_jamforbara"] and s["distrikt"] == {}


def test_utan_jamforbarhet_varnar_och_antar_alla(tmp_path):
    csv = tmp_path / "v.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;S;200\nrd;14800530;giltiga;500\nrd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = kor("--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026", "--jamforelsefil", str(tmp_path / "finns-inte.xlsx"))
    assert r.returncode == 0
    assert "jämförbarhet" in (r.stdout + r.stderr).lower()


@genrep_finns
def test_hamta_bygger_argv_fullstandigt_och_nollstaller_globalt_tillstand(tmp_path, monkeypatch, capsys):
    """--hamta körs aldrig mot nätet i tester: scripts.uppdatera_2026 importeras som modul och
    hamta_2026.main monkeypatchas. Samma import används för att köra JSON-vägen två gånger i
    samma process, för att visa att VARNINGAR, JAMFORBAR och META_TEST nollställs mellan anrop."""
    from scripts import uppdatera_2026

    mapp = hamta_lokalt(tmp_path)
    ut = tmp_path / "data"
    ut.mkdir()

    sparat_argv = sys.argv
    try:
        sys.argv = ["uppdatera_2026.py", "--valnatt-mapp", str(mapp), "--ut", str(ut), "--ar", "2026"]
        assert uppdatera_2026.main() == 0
        varningar_forsta = len(uppdatera_2026.VARNINGAR)
        assert uppdatera_2026.main() == 0
        assert len(uppdatera_2026.VARNINGAR) == varningar_forsta, "varningar ska nollställas mellan anrop i samma process"

        sett = {}

        def attrapp_kod3():
            sett["argv"] = list(sys.argv)
            return 3

        monkeypatch.setattr(uppdatera_2026.hamta_2026, "main", attrapp_kod3)
        ut2 = tmp_path / "hamta-ut"
        sys.argv = ["uppdatera_2026.py", "--hamta", "--ut", str(ut2), "--ar", "2026"]
        assert uppdatera_2026.main() == 3
        argv = sett["argv"]
        assert argv[argv.index("--tillfalle") + 1] == "p"
        assert "--bara-om-nytt" in argv
        assert argv[argv.index("--ut") + 1] == str(ut2 / "valnatt")

        def attrapp_fel():
            raise RuntimeError("x")

        monkeypatch.setattr(uppdatera_2026.hamta_2026, "main", attrapp_fel)
        sys.argv = ["uppdatera_2026.py", "--hamta", "--ut", str(ut2), "--ar", "2026"]
        with pytest.raises(SystemExit):
            uppdatera_2026.main()
        utskrift = capsys.readouterr()
        assert "hämtningen misslyckades" in utskrift.out + utskrift.err

        def attrapp_avslutar():
            raise SystemExit(5)

        monkeypatch.setattr(uppdatera_2026.hamta_2026, "main", attrapp_avslutar)
        sys.argv = ["uppdatera_2026.py", "--hamta", "--ut", str(ut2), "--ar", "2026"]
        with pytest.raises(SystemExit):
            uppdatera_2026.main()
        utskrift = capsys.readouterr()
        assert "hämtningen avbröts med kod 5" in utskrift.out + utskrift.err
    finally:
        sys.argv = sparat_argv
