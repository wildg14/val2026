# Historisk valdata 2002-2022

Underlagsarbetet bakom "Så röstade Majorna": all valdata för Göteborgs kommun (1480) i
riksdagsval, regionval och kommunfullmäktigval 2002, 2006, 2010, 2014, 2018 och 2022, plus
distriktsindelningarnas historia. Ingenting här syns på sidan; det är råmaterial och
dokumentation.

## Börja här

| Dokument | Innehåll |
| --- | --- |
| `inventering.md` | Vilka källfiler som finns per valår, hur de lästes, vad de blev, vad som saknas och vad datan möjliggör redaktionellt |
| `valdistrikt-historik.md` | Hur valdistrikten i Majorna ändrats 2002-2022, definitionen av jämförbart Majorna, tre metoder för att räkna historiskt, fallgropar och tidsserier |
| `datamodell.md` | Databasens tabeller, kolumner, nycklar, källprioritering, kända luckor och tre SQL-exempel |

## docs/historik

- `README.md` - denna fil
- `inventering.md`, `valdistrikt-historik.md`, `datamodell.md` - se ovan
- `kallor/webb/` - sparade kopior av två webbsidor på historik.val.se som används som
  kontrollkälla av `mandat_valkretsar.py`
- `noter/` - en notering per arbetssteg, skriven av det steg som gjorde jobbet. Varje
  notering anger vilka filer som lästes, exakt hur, vad som skrevs, avvikelser och öppna
  frågor.

| Notering | Steg |
| --- | --- |
| `val2002.md`, `val2006.md`, `val2010.md`, `v2014.md`, `val2018.md` | inläsning av resultat per valår |
| `granskning_2002.md`, `granskning_2006.md`, `granskning_2010.md`, `granskning_2014.md`, `granskning_2018.md` | oberoende motgranskning av respektive år |
| `granskning_2002_logg.txt` | logg från granskningen av 2002 |
| `geo2006.md`, `geo2010.md`, `geo2014.md`, `geo2018.md` | geometrisk jämförbarhet mot 2022 |
| `rostberattigade.md` | röstberättigade per distrikt, kön, medborgarskap och ålder 2010-2018 |
| `vallokaler.md` | vallokaler och mottagna förtidsröster 2010-2018 |
| `mandat.md` | mandat och valkretsar 2002-2022 |
| `webbkallor.md` | hämtningar från val.se, historik.val.se och Internet Archive |
| `kedja.md` | kedjan av distriktsmotsvarigheter 2006-2022 |
| `databas.md` | bygget av SQLite-databasen och tidsserierna |

## data/historik

Alla CSV-filer är UTF-8 utan BOM, radslut LF, semikolon som avgränsare, punkt som
decimaltecken och distriktskoder som text med åtta siffror. I löptexten i dokumenten ovan
skrivs tal däremot med decimalkomma.

| Filgrupp | Innehåll |
| --- | --- |
| `roster_<år>_<val>[_xls\|_xml].csv` | röster och andel per valdistrikt och parti. För 2006, 2010 och 2014 finns två oberoende extraktioner, xls och xml, med identiska röstetal |
| `roster_2002_<val>_ovriga.csv` | 2002 års uppdelning av raden övriga partier per distrikt |
| `distrikt_<år>_<val>.csv` | giltiga, blanka, ogiltiga, röstande, röstberättigade, valdeltagande och valkrets per distrikt |
| `aggregat_<år>_<val>.csv` | samma tal för riket, Västra Götaland, Göteborg och kommunvalkretsarna |
| `ogiltiga_2018_<val>.csv` | 2018 års tre ogiltigkategorier var för sig |
| `fgval_<år>_<val>.csv`, `fgval_matchning_2010_2014.csv`, `granskning_2010_fgval_koppling_2006.csv` | Valmyndighetens föregående-val-tal per distrikt och matchningen mot det äldre årets distrikt |
| `geo_overlap_<a>_<b>.csv` | areaöverlapp mellan två indelningar, alla distriktspar med positiv snittarea |
| `geo_majorna_<år>.csv`, `geo_crosswalk_<år>_2022_majorna.csv`, `geo_crosswalk_2018_2022_vastra_centrum.csv` | avgränsningen av Majornaområdet och vilka äldre distrikt som bygger upp varje 2022-distrikt |
| `geo_mappning_2014_2018_jamforelse.csv`, `geo_indelning_2018_jamforelse.csv` | areametoden prövad mot Valmyndighetens officiella mappning |
| `distrikt_<år>_goteborg.geojson`, `distrikt_<år>_majornaomradet.geojson` | distriktspolygoner i WGS84 för 2006, 2010, 2014 och 2018 |
| `kedja_<a>_<b>.csv`, `kedja_majorna_2006_2022.csv` | vilket distrikt i föregående val varje distrikt motsvarar, med typ och belägg |
| `mappning_2018_2022.csv` | Göteborgs stads och Valmyndighetens officiella jämförbarhetsbedömning |
| `rostberattigade_<år>_<val>.csv` och `_bred.csv`, `rostberattigade_majornaomradet_<år>.csv`, `rostberattigade_kontroll_2010_2018.csv` | röstberättigade per distrikt, kön, medborgarskap och åldersgrupp 2010, 2014 och 2018 |
| `vallokaler_<år>.csv` och `_lokaler.csv` | vallokal per distrikt med adress och koordinat |
| `fortidsroster_<år>.csv` och `_lokaler.csv`, `fortidsroster_per_dag_2010_2018.csv`, `fortidsroster_majornaomradet_2010_2018.csv` | mottagna förtidsröster per lokal och dag |
| `mandat_*.csv`, `valkretsar_goteborg.csv` | mandat per val, nivå, valkrets och parti, samt valkretsarnas mandat och röstberättigade |
| `partier_<år>.csv` | partibeteckningar per år och partikod |
| `webbkallor.csv` | index över alla adresser som hämtats eller provats, med status |
| `majorna_historik.sqlite` | hela materialet i en databas, 13 tabeller, cirka 27 MB |
| `majorna_tidsserie.csv` och `.json`, `jamforelse_tidsserie.csv` | färdiga tidsserier för Majorna, Göteborg och riket |
| `majorna_tidsserie_fgval.csv`, `majorna_metodjamforelse.csv` | den alternativa serien byggd på Valmyndighetens föregående-val-tal, och skillnaden mot areametoden |

## Så körs skripten om

Alla skript ligger i `scripts/historik/` och har källvägarna som konstanter högst upp. De
läser bara, förutom de filer de själva skriver, och de ändrar ingen befintlig fil i
projektet. Kör dem med den virtuella miljö som har xlrd, openpyxl, pyshp, dbfread, lxml,
pyproj, shapely och olefile:

Skripten behöver utöver projektets ordinarie paket även xlrd, pyshp, dbfread, lxml och olefile. Installera dem i projektets venv med `uv pip install --python .venv/bin/python -r scripts/historik/requirements-historik.txt`. Nedladdat källmaterial ligger direkt under `Historiska dokument/` (dl2002, dl2006, dl2018, dl_webb, repaired) och de uppackade zip-arkiven i `Historiska dokument/unz/`; båda är gitignorerade och kan återskapas med hämtskripten respektive genom att packa upp zip-filerna med samma mappnamn.

    PY=/Users/daniel/code/Temp/.venv/bin/python

Ordningen spelar roll bara för de sista två stegen. Kedjan och databasen läser filerna som
de tidigare stegen skriver.

| Steg | Kommando | Skriver |
| --- | --- | --- |
| 1 | `$PY scripts/historik/val2002_fetch.py` följt av `val2002_parse.py` | hämtar 908 sidor från historik.val.se och skriver 2002 års filer |
| 2 | `$PY scripts/historik/val2006_goteborg.py` | 2006 |
| 3 | `$PY scripts/historik/val2010_bygg.py` | 2010 |
| 4 | `$PY scripts/historik/v2014_gbg_xls.py`, sedan `v2014_gbg_xml.py`, sedan `v2014_gbg_kontroll.py` | 2014 |
| 5 | `$PY scripts/historik/val2018_bygg.py` | 2018 |
| 6 | `$PY scripts/historik/rostberattigade_2010_2018.py` | röstberättigade per kategori |
| 7 | `$PY scripts/historik/vallokaler_fortidsroster_2010_2018.py` | vallokaler och förtidsröster |
| 8 | `$PY scripts/historik/mandat_valkretsar.py` | mandat och valkretsar |
| 9 | `$PY scripts/historik/geo2006.py`, `geo2010.py`, `geo2014.py`, `geo2018.py` | överlapp, områdesavgränsning och geojson |
| 10 | `$PY scripts/historik/webbkallor_index.py`, `webbkallor_hamta_2022_json.py`, `webbkallor_mappning_2018_2022.py` | hämtningar från webben och mappningen 2018 till 2022 |
| 11 | `$PY scripts/historik/kedja_bygg.py` | kedjefilerna |
| 12 | `$PY scripts/historik/bygg_databas.py` | 2022 års filer, tidsserierna och `majorna_historik.sqlite`, cirka 25 sekunder |

Granskningsskripten `granskning_2002.py`, `granskning_2006_kontroll.py`,
`granskning_2006_motpart.py`, `granskning_2010_kontroll.py`,
`granskning_2010_fgval_koppling.py`, `granskning_2010_extra.py`,
`granskning_2014_kontroll.py`, `granskning_2014_verifiering.py`,
`granskning_2018_kontroll.py`, `granskning_2018_motpart.py` och
`granskning_2018_rattelse.py` räknar om resultaten ur källfilerna och avslutar med kod 0 när
inget fel hittas. De ändrar inga datafiler.

## Två saker att veta innan något körs om

**Vissa källfiler ligger i scratchpad, som är sessionsbunden.** Det gäller uppackade
zip-arkiv (`scratchpad/unz/`), de hämtade 2002-sidorna (`scratchpad/dl2002/`), 2006 års
nedladdningar (`scratchpad/dl2006/`), webbhämtningarna (`scratchpad/dl_webb/`) och de
reparerade 2018-filerna (`scratchpad/repaired/`). Försvinner de måste zip-arkiven i
`Historiska dokument/` packas upp igen, hämtningarna göras om och de fem trasiga
2018-filerna repareras på nytt enligt avsnittet om dem i `inventering.md`.

**Nyckeln är alltid paret år och kod, aldrig koden ensam.** 115 av 2006 års distriktskoder
används redan 2002 för helt andra distrikt, och samma sak gäller mellan senare år. Se
avsnittet Fallgropar i `valdistrikt-historik.md`.
