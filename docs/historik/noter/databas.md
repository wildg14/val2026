# Notering: bygget av historikdatabasen

Steget samlar allt tidigare arbete i en SQLite-fil och två tidsserier. Beskrivningen av
tabellerna och exempelfrågorna ligger i `/Users/daniel/code/Temp/docs/historik/datamodell.md`.
Den här noteringen redovisar vilka filer som lästes, hur, vad som skrevs, avvikelser och
öppna frågor.

## Skript

`/Users/daniel/code/Temp/scripts/historik/bygg_databas.py`. Alla källvägar ligger som
konstanter högst upp. Skriptet läser bara, förutom de filer det själv skriver, och ändrar
ingen befintlig fil i projektet. Körning tar cirka 25 sekunder.

    /Users/daniel/code/Temp/.venv/bin/python \
        /Users/daniel/code/Temp/scripts/historik/bygg_databas.py

Loggen från senaste körningen ligger i scratchpad som `bygg_databas_logg.txt`.

## Lästa filer och hur

Alla CSV-filer i `/Users/daniel/code/Temp/data/historik/` lästes som UTF-8 med semikolon som
avgränsare via `csv.DictReader`. Tomma celler blir NULL, aldrig noll.

| Källa | Lästes hur | Blev |
| --- | --- | --- |
| `roster_2002_<val>.csv` och `roster_2002_<val>_ovriga.csv` | kolumnerna kod, namn, parti, parti_kalla, roster. Raden `ÖVR` i huvudfilen hoppas över och ersätts av alla rader i ovriga-filen | tabellen `roster`, år 2002 |
| `roster_2006_<val>_xml.csv`, `roster_2010_<val>_xml.csv`, `roster_2014_<val>_xml.csv` | samma kolumner | `roster` 2006, 2010, 2014 |
| `roster_2018_<val>.csv` | samma kolumner | `roster` 2018 |
| `distrikt_<ar>_<val>.csv` för 2002-2018 | kod, namn, valkrets, giltiga, blanka, ogiltiga, rostande, rostberattigade, valdeltagande, kalla_fil | `distrikt_summa` och `distrikt` |
| `aggregat_<ar>_<val>.csv` och `aggregat_2002_<val>_ovriga.csv` | niva, parti, parti_kalla, roster, andel, giltiga, rostande, rostberattigade | `aggregat` |
| `geo_overlap_<a>_<b>.csv` för paren 2006-2010, 2010-2014, 2014-2018, 2018-2022, 2006-2022, 2010-2022, 2014-2022 | kod- och andelskolumnerna; rader med `overlapp_m2` lika med 0 hoppas över | `crosswalk`, typ `geo_overlap` |
| `kedja_<a>_<b>.csv` för de fyra på varandra följande paren | kod, kod_troligast, typ | `crosswalk`, typ `kedja:<typ>` |
| `mappning_2018_2022.csv` | kod_2018, kod_2022, procent, jamforbart | `crosswalk`, typ `mappning_officiell:jamforbart=ja/nej` |
| `granskning_2010_fgval_koppling_2006.csv`, `fgval_matchning_2010_2014.csv` | kodparen, avdubblade | `crosswalk`, typ `fgval` |
| `geo_majorna_<ar>.csv` för 2006, 2010, 2014, 2018 | kod, namn, andel_i_majorna, klass | `majorna_medlem` |
| `fgval_2010_<val>.csv`, `fgval_2010_<val>_deltagande.csv`, `fgval_2014_rd.csv`, `fgval_2014_kf.csv` | kod, parti, roster_fgval, giltiga_fgval | den alternativa FGVAL-serien |
| `rostberattigade_<ar>_<val>.csv` (2010, 2014, 2018) | alla kolumner | `rostberattigade_kategori` |
| `fortidsroster_<ar>.csv` (2010, 2014, 2018) | lokalid, lokal, datum, antal | `fortidsroster` |
| `mandat_2006_riksdag.csv`, `mandat_2010_riksdag.csv`, `mandat_2014_riksdag/kf/rf.csv`, `mandat_2018.csv`, `mandat_riksdag_riket.csv`, `mandat_valkrets_goteborg.csv` | olika kolumnuppsättningar, mappade till en gemensam form | `mandat` |
| `partier_2006.csv`, `partier_2010.csv`, `partier_2018.csv` | ar, val, parti_kalla, parti, namn | `partier` |
| `valkretsar_goteborg.csv` | raderna för 2002, kolumnen rostberattigade | röstberättigade för Göteborg 2002 i tidsserien |
| `/Users/daniel/code/Temp/data/valdata_2022.json` | `distrikt[]`, `aggregat.majorna` | enbart kontroll, inte som datakälla |
| `Roster-per-distrikt-...-riksdagsvalet-2022.xlsx` flik `roster_RD`, motsvarande regionval flik `roster_RF` och kommunval flik `roster_KF` | openpyxl med `read_only=True, data_only=True`. Kolumn B `Distrikt` (`RD-14-80-0526`) ger den åttasiffriga koden, kolumn G namn, I valkretsnamn, J parti, K röster, L röstberättigade | `roster`, `distrikt_summa`, `aggregat` för 2022 |

Valdagarna kommer ur attributen `VALDAG` och `VALDAG_FGVAL` i Valmyndighetens XML för
2002, 2006, 2010 och 2014, ur kolumnen `valdag` i `vallokaler_2018.csv` för 2018 och ur
filnamnet `VD_14_20220910_Val_20220911.json` för 2022. Källan står i kolumnen `kalla` i
tabellen `val`.

## Skrivna filer

| Fil | Innehåll |
| --- | --- |
| `data/historik/majorna_historik.sqlite` | databasen, 13 tabeller, cirka 27 MB |
| `data/historik/roster_2022_<val>.csv` | 2022 per distrikt och parti för hela Göteborg, standardformat |
| `data/historik/distrikt_2022_<val>.csv` | 2022 per distrikt, standardformat |
| `data/historik/aggregat_2022_<val>.csv` | 2022 för riket, Västra Götaland och Göteborg |
| `data/historik/majorna_tidsserie.csv` | 322 rader, `ar;val;parti;roster;andel;giltiga;rostande;rostberattigade;valdeltagande;antal_distrikt;metod` |
| `data/historik/majorna_tidsserie.json` | samma innehåll plus metadata om vilka distrikt som ingick och täckningsgrad i yta |
| `data/historik/jamforelse_tidsserie.csv` | 2487 rader, samma kolumner med `niva` tillagd: majorna, goteborg, riket |
| `data/historik/majorna_tidsserie_fgval.csv` | den alternativa serien byggd på FGVAL |
| `data/historik/majorna_metodjamforelse.csv` | skillnaden mellan areametoden och FGVAL-kedjan, parti för parti |
| `docs/historik/datamodell.md` | tabeller, kolumner, nycklar, källprioritering, luckor, tre SQL-exempel |

## Jämförbart Majorna

2022 är definitionen given: de 23 distrikten 14800526-14800548. För tidigare år tas de
distrikt med som `geo_majorna_<ar>.csv` klassar mot unionen av dessa 23 distrikt
(4,6554 km2), med regeln `andel_i_majorna >= 0,5`.

Beslutet loggas per distrikt i kolumnen `beslut` i tabellen `majorna_medlem`, till exempel
"andel_i_majorna 0,9999 >= 0,50, tas med". Inget distrikt något år hamnade i närheten av
tröskeln: geo-stegen fann inte ett enda distrikt i klassen `delvis` (0,05 till 0,95).
Lägsta värdet bland de medtagna är 0,9997 och närmaste kandidat utanför är 14801061
Majorna-Linné, Änggården med 0,0003 av sin yta i unionen. Regeln 0,5 är alltså inte
avgörande för något enskilt distrikt, men den står kvar som explicit och kontrollerbar.

| År | Distrikt | Täckning av 2022-unionen | Koder |
| --- | --- | --- | --- |
| 2006 | 17 | 99,96 procent | 14808401-14808407, 14808501-14808506, 14805901-14805904 |
| 2010 | 17 | 99,97 procent | 14800911-14800916, 14800921, 14800931-14800936, 14800941-14800944 |
| 2014 | 17 | 99,97 procent | 14801011-14801016, 14801021, 14801031-14801036, 14801041-14801044 |
| 2018 | 22 | 99,97 procent | 14801011-14801017, 14801021, 14801022, 14801031-14801038, 14801041-14801045 |
| 2022 | 23 | 100 procent | 14800526-14800548 |

Täckningsgraden är summan av kolumnen `andel_av_majorna` i respektive `geo_majorna`-fil och
finns i `majorna_tidsserie.json` under `meta.tackningsgrad_yta_mot_2022_unionen`.
Skillnaden mot 100 procent är 1588 m2 vid Söderlingska Ängen som 2018 tillhörde
Majorna-Linné, Änggården, plus digitaliseringsbrus längs kajkanten. Ingen omviktning görs:
alla distrikt går in hela.

2002 ingår inte i Majorna-serien. Det finns ingen shapefil för 2002, och `val2002.md` visar
att gränserna ritades om mellan 2002 och 2006: Karl Johan 1-12 hade 11519 giltiga
riksdagsröster mot 14396 i 2006 års 13 distrikt. Stigberget låg dessutom inne i
Masthugg 1-8 och kan inte skiljas ut. De tolv Karl Johan-distrikten finns i
`majorna_medlem` med `klass = 'ej_geo'` och `ingar_i_jamforbart_majorna = 0`, så att
avgörandet är dokumenterat i databasen och inte bara i text.

## Summor för jämförbara Majorna

| År | Val | Giltiga | Röstande | Röstberättigade | Valdeltagande |
| --- | --- | --- | --- | --- | --- |
| 2006 | rd | 18803 | 19181 | 24186 | 79,31 |
| 2010 | rd | 20452 | 20700 | 25001 | 82,80 |
| 2014 | rd | 20960 | 21131 | 25494 | 82,89 |
| 2018 | rd | 21167 | 21361 | 25331 | 84,33 |
| 2022 | rd | 21308 | 21545 | 26032 | 82,76 |
| 2006 | kf | 18807 | 19156 | 24603 | 77,86 |
| 2010 | kf | 20456 | 20678 | 25353 | 81,56 |
| 2014 | kf | 21063 | 21264 | 25835 | 82,31 |
| 2018 | kf | 21616 | 21839 | 25965 | 84,11 |
| 2022 | kf | 21620 | 21865 | 26737 | 81,78 |

Regionvalet finns i samma tabell. 2022 års rader stämmer exakt med `aggregat.majorna` i
`data/valdata_2022.json` för alla tre val, vilket kontrolleras vid varje körning.

## Areametoden mot FGVAL-kedjan

Den alternativa serien uttrycker föregående vals röster i det senare årets distrikt med
Valmyndighetens egna FGVAL-tal: 2006 läses ur `fgval_2010_<val>.csv` summerad över 2010 års
17 Majornadistrikt, och 2010 ur `fgval_2014_<val>.csv` summerad över 2014 års 17 distrikt.
Raderna GILTIGA, BLANK, OG, SUMMA_RÖSTER och RÖSTBERÄTTIGADE i fgval-filerna är summor och
räknas inte som partier.

**2006: metoderna ger identiska tal.** Alla 17 distrikt 2010 har FGVAL. Summan per parti är
exakt densamma som areametodens summa över 2006 års 17 distrikt, i alla tre valen och för
varje parti. Riksdagsvalet: M 3324, C 928, L 1674, KD 731, S 4469, V 3225, MP 3292, SD 371,
giltiga 18803. Noll rader i `majorna_metodjamforelse.csv` för 2006 har en skillnad skild
från noll. Det är ett oberoende belägg för att de 17 distrikten 2006 och de 17 distrikten
2010 täcker samma område, och att areametoden inte flyttar några röster.

**2010: FGVAL-kedjan är ofullständig och ska inte användas rakt av.** Fem av de 17
jämförbara Majornadistrikten 2014 är markerade Modifierad och saknar FGVAL helt:
14801016 Svalebo, 14801033 Hängmattan, 14801034 Majorna, 14801035 Marieberg och
14801036 Slottsskogsgatan m fl. De står för 28,5 procent av områdets giltiga röster 2014.
Summan över de 12 återstående blir därför 14638 giltiga riksdagsröster mot areametodens
20452, en skillnad som helt beror på att fem distrikt saknas, inte på metodval.

För att ändå pröva FGVAL-talens riktighet jämförs de 12 distrikten med sina egna
motsvarigheter 2010 enligt `fgval_matchning_2010_2014.csv`. Då stämmer alla stora partier
exakt. Enda avvikelser i riksdagsvalet är att 2 röster på 0979, 1 på 1052 och 1 på ND i de
faktiska 2010-talen ligger samlade som 4 röster på ÖVRIGA_FGVAL i Valmyndighetens
FGVAL-uppgift, och i kommunvalet att 1 röst på 1027 redovisas som 1 på TOP. Det är alltså
bara olika bokföring av småpartier, inte skilda röstetal. Dessa rader har `omfattning`
lika med "delmangd: bara distrikt dar FGVAL finns" i `majorna_metodjamforelse.csv`.

Slutsats: areametoden används i `majorna_tidsserie.csv`, eftersom den är komplett för alla
år och för 2006 bevisligen ger samma tal som Valmyndighetens egen översättning.
FGVAL-serien ligger kvar som kontroll i `majorna_tidsserie_fgval.csv`.

## Kontroller vid varje körning

1. Vänsterpartiet i Majorna 2022 kommunval: 7479 röster av 21620 giltiga, 34,59 procent.
   Skriptet avbryter med felutskrift om talet ändras.
2. Giltiga, röstande och röstberättigade för Majorna 2022 i alla tre valen mot
   `aggregat.majorna` i `data/valdata_2022.json`: lika.
3. 667 partital i de 23 distrikten 2022 mot `distrikt[]` i samma fil: lika.
4. Summan av partiröster per distrikt lika med `giltiga` för alla år och val: inga avvikelser.
5. `giltiga` plus `ogiltiga` lika med `rostande` för alla distrikt och år: inga avvikelser.
6. Antal distrikt per år: 2002 286, 2006 283, 2010 286, 2014 301, 2018 351, 2022 411,
   varav uppsamlings- eller onsdagsdistrikt 0, 4, 4, 4, 1 och 1.

Senaste körningen: 0 fel, 0 varningar.

## Avvikelser och val som gjordes

1. **XML före xls.** För 2006, 2010 och 2014 finns två extraktioner. Databasen använder
   XML-varianten enligt uppdragets prioritering. Granskningarna visar att röstetalen är
   identiska; skillnaden är att xls-filerna har rader med noll röster som XML saknar.
   Radantalet i `roster` är därför lägre än i xls-filerna.
2. **2002 års ÖVR är utbytt mot uppdelningen.** `roster_2002_<val>_ovriga.csv` summerar
   exakt till huvudfilens `ÖVR` i alla 286 distrikt och alla tre val. Utan bytet skulle
   SD 2002 saknas i riksdags- och regionvalet. Kolumnen `kalla` markerar de raderna.
3. **Uppsamlingsdistrikt.** Namnen skiljer sig mellan år: "I vallokal ej räknade röster"
   2006 (koder 1480VK01-1480VK04, inte åtta siffror), "Onsdagsdistrikt" 2010 och 2014
   (14800001-14800004) och "Uppsamlingsdistrikt" 2018 och 2022 (14800000). De känns igen på
   namnet eller på att koden inte är åtta siffror och flaggas med
   `distrikt.uppsamlingsdistrikt = 1`. Källans koder behålls oförändrade.
4. **2018 skriver 0 i stället för tomt** för röstberättigade och valdeltagande i
   uppsamlingsdistriktet. De värdena skrivs som NULL i databasen, eftersom 0 skulle ge ett
   falskt valdeltagande. Övriga tal är oförändrade.
5. **Röstberättigade för Göteborg 2002** saknas i 2002 års webbsidor. I tidsserien fylls de
   i från `valkretsar_goteborg.csv` (rd 357876, rf 375849, kf summan av de fyra
   kommunvalkretsarna 375849), som i sin tur läst dem ur
   `RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL` i 2006 års XML. Det ger valdeltagande 77,54
   procent i riksdagsvalet, lika med det värde 2002 års egna sidor visar (77,5).
   Kolumnen `metod` i tabellen `tidsserie` anger detta på raderna det gäller. Tabellen
   `aggregat` lämnas orörd med tomt värde.
6. **Riket 2002 saknar röstberättigade** och därmed valdeltagande. Ingen ersättningskälla
   finns i materialet.
7. **Partikoder.** Tabellen `parti_kanon` innehåller de fem harmoniseringar som är belagda
   i granskningarna, plus regeln att numeriska partikoder nollutfylls till fyra tecken
   (2014 skriver 0470, 2018 skriver 470). Kolumnen `parti_kanon` i `roster` och `aggregat`
   är den som ska användas i tidsserier. Övriga småpartier kan fortfarande ha olika koder
   olika år.
8. **2022 hämtas ur xlsx, inte ur valdata_2022.json.** Json-filen täcker bara de 23
   Majornadistrikten och slår ihop småpartier till "Övriga". Valmyndighetens xlsx-filer
   ger alla 410 distrikt plus uppsamlingsdistriktet i Göteborg, alla partier var för sig,
   och gör det möjligt att räkna riket och Västra Götaland för 2022 på samma sätt som för
   övriga år. Json-filen används i stället som facit.
9. **Partinamn 2022 översätts till koder** med en tabell i skriptet. Fjorton partinamn i
   Göteborg saknade tidigare kod och fick en egen (bland annat GBGP för Göteborgspartiet,
   SPVG för Sjukvårdspartiet - Västra Götaland, EAP för Europeiska Arbetarpartiet-EAP).
   Partinamn utanför Göteborg som bara påverkar riksnivån får en automatisk förkortning ur
   namnet; de är många och lokala och har ingen motsvarighet i tidigare år.
10. **SUMMA_ÖVRIGA i tidsserien** är giltiga minus V, S, MP, SD, M, C, L, KD, D, FI och K.
    Den behövs eftersom 2002 slår ihop småpartier medan senare år listar dem, och eftersom
    de tre nivåerna majorna, goteborg och riket annars inte har samma partiuppsättning.
11. **Kommunvalkretsar saknas 2018 och 2022.** Göteborg hade en enda kommunvalkrets båda
    åren, så kolumnen `kommunvalkrets` är tom 2018 och "Göteborg" 2022. Nivåerna
    `Göteborg 1` till `Göteborg 4` respektive `Göteborg, Centrum` med flera i tabellen
    `aggregat` finns bara 2002-2014.
12. **Crosswalk innehåller flera rader per distriktspar.** Ett par kan finnas både som
    `geo_overlap`, `kedja` och `mappning_officiell`. Frågor mot tabellen måste alltid
    filtrera på `typ`, annars dubbelräknas kopplingarna.

## Öppna frågor

- Ingen omviktning av röster mellan indelningar görs. För enskilda distrikt över tid
  behövs befolknings- eller röstberättigadedata per delyta; areaandelar duger inte, vilket
  geo-stegen visar med Sandarne och Klippan som till stor del är hamn och park.
- 2002 kan bara knytas till 2006 geografiskt om en shapefil för 2002 hittas. Utan den
  saknas åren 1998 och 2002 i Majorna-serien.
- Regionvalets FGVAL 2014 avser omvalet 2011. En serie för regionvalet 2010 till 2014 via
  FGVAL kräver att omvalet hanteras särskilt, vilket inte gjorts här.
- Mandat för kommunfullmäktige och regionfullmäktige 2006 och 2010 finns i XML-källorna men
  är inte utskrivna till CSV av de tidigare stegen och saknas därför i tabellen `mandat`.
- `rostberattigade_kategori` och `fortidsroster` finns bara 2010-2018. Motsvarande
  underlag för 2022 finns i projektets rotkatalog (statistik-alder-och-kon-*.xlsx) men är
  inte inläst.
