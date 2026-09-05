"""Bygger data/historik/webbkallor.csv: en indexfil over de officiella hjalpfiler
for jamforbarhet mellan valen som hamtats fran val.se, historik.val.se,
resultat.val.se och Internet Archive, plus de kallor som eftersokts men inte finns.

Kolumner: ar;typ;adress;lokal_fil;status;kommentar

status ar ett av:
  ok        - filen finns lokalt och hamtades med HTTP 200
  finns_ej  - adressen ar kontrollerad och ger 404, eller kallan finns inte alls
  ersatt    - kallan finns inte, men en likvardig uppgift finns i en annan fil

Storlek i byte laggs till i kommentaren vid koring, direkt fran filsystemet, sa
att tabellen inte kan innehalla pahittade tal. Kor om skriptet nar nya filer
laddats ned.
"""
import csv
import os
import sys

SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"
DL = SCRATCH + "/dl_webb"
UT = "/Users/daniel/code/Temp/data/historik/webbkallor.csv"

VAL_SE = "https://www.val.se"
HIST = "https://historik.val.se"
WB = "https://web.archive.org/web"

# ar, typ, adress, lokal_fil (relativt DL eller "" om ingen), status, kommentar
KALLOR = [
    # ---------------------------------------------------------------- 2018-2022
    ("2022", "mappning_2018_2022",
     VAL_SE + "/download/18.162047b519a91d0533119148/1666857349837/"
     "jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx",
     "2022/jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx", "ok",
     "Valmyndighetens slutliga bedomning 2022-10-27. Flikar 'Fysiska valdistrikt' och "
     "'Uppsamlingsdistrikt'. Kalla till data/historik/mappning_2018_2022.csv. "
     "Lankad fran sidorna 'Analyser och jamforelser' och 'Radata fran val 2002-2022'"),
    ("2022", "mappning_2018_2022_preliminar",
     VAL_SE + "/download/18.14c1f613181ed0043d5563c/1662367533764/"
     "jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt.xlsx",
     "2022/jamforelser_2018_2022_valdistrikt_uppsamlingsdistrikt.xlsx", "ok",
     "Forsta versionen, publicerad 2022-09-05 fore valdagen. Adressen ger nu 404 pa "
     "val.se; filen finns via Internet Archive. Identisk med v2 for Goteborgs 410 rader"),
    ("2022", "mandatjamforelse_2018_2022",
     VAL_SE + "/download/18.162047b519a91d0533119cdb/1665670301237/"
     "Mandatfordelning-jamforelser-mellan-2018-och-2022.xlsx",
     "", "ok",
     "Finns redan i projektroten som Mandatfordelning-jamforelser-mellan-2018-och-2022.xlsx, "
     "hamtades inte om"),
    # ---------------------------------------------------------------- 2014-2018
    ("2018", "mappning_2014_2018",
     HIST + "/val/val2018/statistik/mappning_2014_2018.zip",
     "2018/mappning_2014_2018_historik.zip", "ok",
     "Officiell skv-mappning. Innehaller vd-mappning-2014-2018.skv, vd-indelning-2018.skv, "
     "upp-mappning-2014-2018.skv, upp-indelning-2018.skv. Samma innehall som den redan "
     "uppackade mappen scratchpad/unz/mappning_2014_2018/"),
    # ---------------------------------------------------------------- 2018 XML
    ("2018", "slutresultat_xml_fgval",
     WB + "/20210926125427id_/https://data.val.se/val/val2018/slutresultat/slutresultat.zip",
     "2018/slutresultat_2018_wayback.zip", "ok",
     "875 filer, Valmyndighetens XML for hela riket. Innehaller slutresultat_1480R/L/K.xml "
     "(Goteborg, 350 valdistrikt) och slutresultat_00R/L/K.xml (riket) med attributen "
     "ROSTER_FGVAL, PROCENT_FGVAL och PROCENT_ANDRING mot 2014 (VALDAG_FGVAL=20140914). "
     "Uppackade till 2018/unz/"),
    ("2018", "slutresultat_xml_fgval_ursprunglig",
     "https://data.val.se/val/val2018/slutresultat/slutresultat.zip",
     "", "finns_ej",
     "Ursprunglig adress ger nu 404. Finns varken pa historik.val.se/val/val2018/slutresultat/ "
     "eller lankad fran 2018 ars statistiksida. Enda kanda kopian ar Internet Archive-"
     "ogonblicksbilden fran 2021-09-26"),
    ("2018", "valnatt_xml",
     HIST + "/val/val2018/valnatt/valnatt.zip", "", "ok",
     "Finns live, 5422062 byte enligt Content-Length. Valnattsrakning, inte slutresultat. "
     "Inte hamtad, eftersom slutresultatet redan finns"),
    # ---------------------------------------------------------------- 2022 nya formatet
    ("2022", "resultat_json_fgval",
     "https://resultat.val.se/data/resultat/val2022/{path}_S.json",
     "2022/json/", "ok",
     "Valmyndighetens JSON bakom resultat.val.se. Adressmonstret ar hamtat ur webbappens "
     "JS-bundle. Varje valdistrikt har antalRosterForegaendeVal, andelRosterForegaendeVal, "
     "forandringAntalRoster, forandringAndelRoster och flaggan jamforbar. Hamtat med "
     "scripts/historik/webbkallor_hamta_2022_json.py, se manifest.csv i mappen"),
    ("2022", "valgeografi_json",
     "https://resultat.val.se/data/valgeografi/valgeografi_val2022.json",
     "2022/valgeografi_val2022.json", "ok",
     "Tradstruktur valtillfalle - valtyp - valkrets - kommun - valdistrikt med koder och "
     "namn. 410 attasiffriga koder for Goteborg, samma mangd som i jamforelsefilen"),
    ("2022", "resultat_json_kontroll",
     "https://resultat.val.se/data/resultat/val2022/KF_01_0114_01140101_S.json",
     "2022/json_kontroll/", "ok",
     "Kontrollhamtning utanfor Goteborg. Ovra Runby i Upplands Vasby, som "
     "jamforelsefilen anger som jamforbart mot samma kod 2018, har anda jamforbar=false "
     "och nollade jamforelsefalt. Aven P-varianterna, dvs preliminart rakningstillfalle, "
     "hamtade for samma kontroll"),
    ("2022", "jamforande_statistik_riksdag_prel",
     VAL_SE + "/download/18.162047b519a91d0533118d2d/1663745020932/"
     "preliminar-riksdagsval-jamforande-statistik-2018-2022-med-uppsamlingsdistrikt-ny.xlsx",
     "2022/preliminar-riksdagsval-jamforande-statistik-2018-2022-med-uppsamlingsdistrikt-ny.xlsx",
     "ok",
     "Namnet lovar uppsamlingsdistrikt men filen har bara flikarna Riksdag, Valkrets och "
     "Per Kommun. Ingen valdistriktsniva, alltsa inte anvandbar som distriktsjamforelse"),
    ("2022", "jamforande_statistik_riksdag",
     VAL_SE + "/download/18.162047b519a91d05331197bd/1786611369096/"
     "slutligt-valresultat-riksdagen-jamforande-statistik-2018-2022.xlsx",
     "", "ok",
     "Finns redan i projektroten som slutligt-valresultat-riksdagen-jamforande-statistik-"
     "2018-2022.xlsx, hamtades inte om"),
    # ---------------------------------------------------------------- saknade mappningar
    ("2014", "mappning_2010_2014",
     HIST + "/val/val2014/statistik/index.html", "index/statistik_2014.html", "ersatt",
     "Ingen officiell mappningsfil finns. 2014 ars statistiksida listar 96 lankar och "
     "ingen heter mappning eller indelning. Sokning i Internet Archive over alla val.se-"
     "domaner ger bara mappning_2014_2018.zip och mappning_ep2014_ep2019.zip. Ersatts av "
     "attributet ROSTER_FGVAL i 2014 ars XML (scratchpad/unz/slutresultat/), som anger "
     "2010 ars rostetal per parti och valdistrikt"),
    ("2010", "mappning_2006_2010",
     HIST + "/val/val2010/statistik/index.html", "index/statistik_2010.html", "ersatt",
     "Ingen officiell mappningsfil finns, samma sokning som for 2010-2014. Ersatts av "
     "ROSTER_FGVAL i 2010 ars XML (scratchpad/unz/slutresultat__1_/), som anger 2006 ars "
     "rostetal per parti och valdistrikt"),
    ("2002", "valgeografi_2002",
     VAL_SE + "/valresultat-och-statistik/statistik-och-data/radata-fran-val-2002-2022",
     "index/valse_radata_2002_2022.html", "finns_ej",
     "Ingen valgeografi finns for 2002. Radatasidan sager att 2002 ars material bara finns "
     "i rent textformat pa historik.val.se/val/val_02/. Sokning i Internet Archive over "
     "val.se-domaner ger tidigast GIS-material fran 2006 (kartor) och 2009 (EP)"),
    ("2006", "valgeografi_2006",
     HIST + "/val/val2006/slutlig_ovrigt/statistik/kartor/riksdagen_i_valdistrikt.zip",
     "index/2006_kartor.html", "ok",
     "Shapefil, 23361427 byte enligt Content-Length, redan uppackad lokalt i "
     "scratchpad/unz/riksdagen_i_valdistrikt/. Kartsidan listar aven "
     "landstingen_i_valdistrikt.zip, riksdagen_i_onsdagsdistrikt.zip, "
     "riksdagen_i_kommuner.zip och riksdagen_i_riksdagsvalkretsar.zip"),
    # ---------------------------------------------------------------- indexsidor
    ("2018", "indexsida",
     HIST + "/val/val2018/statistik/index.html", "index/statistik_2018.html", "ok",
     "Kallforteckning for 2018. Har hittas mappning_2014_2018.zip och "
     "2018_valgeografi_valdistrikt.zip"),
    ("2006", "indexsida",
     HIST + "/val/val2006/slutlig_ovrigt/statistik/index.html", "index/statistik_2006.html", "ok",
     "2006 ars statistiksida ligger under slutlig_ovrigt, inte under statistik som ovriga ar"),
    ("2006", "xml_index",
     HIST + "/val/val2006/slutlig/xml/index.html", "2006_xml_index.html", "ok",
     "Forteckning over 2006 ars XML-filer. 2006 ars XML saknar FGVAL, eftersom 2002 inte "
     "rapporterades i samma format"),
    ("2002", "indexsida",
     HIST + "/val/val_02/slutresultat/index.html", "2002/slutresultat_index_2002.html", "ok",
     "2002 ars valpresentation, enbart HTML i textformat"),
    ("2022", "sida_analyser_jamforelser",
     VAL_SE + "/valresultat-och-statistik/statistik-och-data/analyser-och-jamforelser",
     "index/valse_analyser-och-jamforelser.html", "ok",
     "Sidan dar mappningen 2018 till 2022 publiceras"),
    ("2022", "sida_radata_2002_2022",
     VAL_SE + "/valresultat-och-statistik/statistik-och-data/radata-fran-val-2002-2022",
     "index/valse_radata_2002_2022.html", "ok",
     "Sidan listar 2022 ars radata och lankar vidare till historik.val.se for 2002-2018"),
    # ---------------------------------------------------------------- 2026, for kommande val
    ("2026", "mappning_2022_2026",
     VAL_SE + "/download/18.1a2972da19f159e73fd3a47/1787064655347/"
     "valdistrikt-jamforelser-mellan-2022-och-2026.xlsx",
     "2026/valdistrikt-jamforelser-mellan-2022-och-2026.xlsx", "ok",
     "Officiell mappning 2022 till 2026, slutlig bedomning 2026-08-17. Flik 'Jamforelser' "
     "med kolumnerna Valdistriktskod 2026, Valdistriktsnamn 2026, Kommun, Lan, Jamforbarhet, "
     "Valdistriktskod 1 2022, Valdistriktskod 2 2022. 6312 rader i riket, 396 i Goteborg"),
    ("2026", "valgeografi_2026_vg",
     VAL_SE + "/download/18.332cf48819bd61ac15138b1/1785490768997/"
     "valdistrikt-vastra-gotaland-lan-2026.zip",
     "2026/valdistrikt-vastra-gotaland-lan-2026.zip", "ok",
     "Valgeografi 2026 for Vastra Gotalands lan, motsvarar 2022 ars "
     "valdistrikt-vastra-gotalands-lan.zip som redan finns i projektroten"),
    ("2026", "valdistrikt_hela_landet",
     VAL_SE + "/download/18.332cf48819bd61ac151499d/1779801380664/"
     "valdistrikt-hela-landet-2026.xlsx",
     "2026/valdistrikt-hela-landet-2026.xlsx", "ok",
     "Forteckning over samtliga valdistrikt 2026 med koder och namn"),
    ("2026", "mandatjamforelse_2022_2026",
     VAL_SE + "/download/18.3eba56b819e04244a687ae/1778508116907/"
     "fordelning-av-mandat-2022-och-2026.xlsx",
     "2026/fordelning-av-mandat-2022-och-2026.xlsx", "ok",
     "Mandatfordelning 2022 och 2026 per valkrets"),
    ("2026", "teknisk_beskrivning_json",
     VAL_SE + "/valresultat-och-statistik/statistik-och-data/teknisk-beskrivning-av-resultatfiler",
     "2026/", "ok",
     "Tio md-filer som beskriver 2026 ars resultatfiler. slut-rostfordelning.md visar att "
     "varje valdistrikt far faltet valdistriktskodForegaendeVal plus "
     "totaltAntalRosterForegaendeVal, antalRostberattigadeForegaendeVal och "
     "valdeltagandeForegaendeVal, alltsa en mappning 2022 till 2026 direkt i resultatfilen"),
]


def storlek(rel):
    """Byte for en fil, eller antal filer och summa byte for en mapp."""
    if not rel:
        return None, None
    p = os.path.join(DL, rel)
    if os.path.isdir(p):
        n = 0
        tot = 0
        for rot, _, filer in os.walk(p):
            for f in filer:
                n += 1
                tot += os.path.getsize(os.path.join(rot, f))
        return n, tot
    if os.path.exists(p):
        return 1, os.path.getsize(p)
    return 0, 0


def main():
    os.makedirs(os.path.dirname(UT), exist_ok=True)
    rader = []
    saknas = []
    for ar, typ, adress, rel, status, kommentar in KALLOR:
        n, tot = storlek(rel)
        lokal = os.path.join(DL, rel) if rel else ""
        if rel and n == 0:
            saknas.append(lokal)
            status = "saknas_lokalt"
        if n is not None and n > 0:
            if os.path.isdir(os.path.join(DL, rel)):
                kommentar += ". Lokalt: %d filer, %d byte" % (n, tot)
            else:
                kommentar += ". Lokalt: %d byte" % tot
        rader.append([ar, typ, adress, lokal, status, kommentar])
    rader.sort(key=lambda r: (r[0], r[1]))
    with open(UT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["ar", "typ", "adress", "lokal_fil", "status", "kommentar"])
        w.writerows(rader)
    from collections import Counter
    print("rader:", len(rader), Counter(r[4] for r in rader))
    if saknas:
        print("SAKNAS LOKALT:", saknas)
    print("skrev", UT)


if __name__ == "__main__":
    sys.exit(main())
