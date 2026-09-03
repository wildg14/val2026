# Granskning av 2006-filerna (motpart till val2006)

Etikett: granskning_2006. Skript: `/Users/daniel/code/Temp/scripts/historik/granskning_2006_motpart.py` (körs med venv-python, behöver xlrd, dbfread, lxml och pyshp; läser bara, skriver rapporten till `scratchpad/granskning_2006_motpart.txt`). Granskat: filerna som val2006 skrev enligt `docs/historik/noter/val2006.md`. Inga CSV-filer har ändrats.

Resultat i korthet: alla tal i de skrivna filerna går att härleda ur källfilerna, och de tre källorna (xls, XML, dbf) stämmer med varandra för alla 283 rader. Det som hittats är formfrågor och två sakfel i noteringens tolkning av 2002-uppgifterna, inte fel i siffrorna.

## Vad som lästes och hur

Egen kod, oberoende av val2006-skriptet.

| Fil | Läsning |
|-----|---------|
| `scratchpad/dl2006/slutresultat_1480R.xml`, `_1480L.xml`, `_1480K.xml` | lxml utan DTD (filen anger ISO-8859-1). Per `VALDISTRIKT` och `ONSDAGSDISTRIKT`: `RÖSTER`, egna `GILTIGA` plus `VARAV_ÖVRIGA`, `OGILTIGA BLANK` och `OG`, `VALDELTAGANDE`, `INDELNING`, `RÖSTER_FGVAL`. Per `KOMMUN` och `KRETS_KOMMUN`: samma plus `RÖSTER_FGVAL` per parti |
| `scratchpad/dl2006/slutresultat_00R.xml`, `_00L.xml`, `_00K.xml` | `NATION`, `LÄN KOD=14`, `KOMMUN KOD=1480` |
| `scratchpad/dl2006/unz/riksdagen_i_valdistrikt.xls` (blad `riksdagsvalet_vd_2006_orginal`), `landstingen_i_valdistrikt.xls` (`L_vd_2006`), `kommunerna_i_valdistrikt_14.xls` (`K_vd_14_2006`) | xlrd, rubrikrad 0, rader där `LKFV` börjar med 1480: 283 per fil. Alla `<parti>_ROST`, `<parti>_PROC`, `ÖVR_ROST`, `BLANK_ROST`, `TOT_ROST`, `ROSTB`, `VDT` |
| `scratchpad/dl2006/unz/riksdagen_i_kommuner.xls` | rad 165 (`KOM` 1480) |
| `scratchpad/unz/riksdagen_i_valdistrikt/riksdagen_i_valdistrikt.dbf` och `.shp` | dbfread latin-1 (fält `Lkfv`); pyshp med encoding latin-1 för antal geometrier |
| `data/historik/*_2006_*.csv` samt `roster_2002_*.csv`, `distrikt_2002_*.csv`, `aggregat_2002_*.csv` | csv, semikolon, UTF-8 |

## Kontroller och utfall

1. Göteborgs totaler omräknade ur källorna. Summan av distriktsraderna i `roster_2006_<val>_xml.csv` (inklusive onsdagsdistrikten) är lika med `KOMMUN`-elementet i 1480-filen för varje parti, BLANK och OG i alla tre valen. `aggregat_2006_<val>.csv` nivå `goteborg` är lika med `KOMMUN`, nivåerna `Göteborg 1` till `Göteborg 4` lika med `KRETS_KOMMUN` och med summan av kretsens distrikt, `riket` lika med `NATION` (rd 42 partier, rf 44, kf 221) och `vgregion` lika med `LÄN 14` i 00-filerna. `KOMMUN 1480` i 00-filerna är lika med 1480-filerna. `riksdagen_i_kommuner.xls` rad 1480 är lika med XML för alla partikolumner, BLANK, `TOT_ROST` 297341 och `ROSTB` 373836. Alla andelar i aggregatfilerna stämmer med röster delat med giltiga (BLANK och OG med summa röster) inom 0,01.
2. Per distrikt, alla 283 rader i alla tre valen: summan av partirader i både `roster_xml` och `roster_xls` är lika med `giltiga`; `blanka` + `ogiltiga_ovriga` = `ogiltiga`; `giltiga` + `ogiltiga` = `rostande`; `valdeltagande` = `rostande` / `rostberattigade` inom 0,01 för de 279 rader som har röstberättigade. Fälten är lika med egen XML-läsning för alla rader. Namn och valkrets lika med XML.
3. Två eller tre källor per val. xls mot XML, egen läsning: rd 3679, rf 2830, kf 2830 partivärden lika, och alla `<parti>_PROC` lika med XML:s `PROCENT` där partiet har röster. `TOT_ROST` = giltiga + BLANK + OG, `BLANK_ROST` = BLANK, `ROSTB` = `RÖSTBERÄTTIGADE`, namn lika för alla distrikt. xls `ÖVR_ROST` är i alla 283 rader och tre val lika med summan av de XML-partier som xls inte bryter ut (inklusive XML:s inre ÖVR-rest). dbf mot xls rd: 4743 värden (alla `_ROST` och `ROSTB` för 279 poster) lika. `roster_2006_<val>_xls.csv` mot `roster_2006_<val>_xml.csv` rad för rad: inga avvikelser i röster. Enda skillnaden mellan xls- och xml-filerna är att xls-filerna innehåller rader med 0 röster (rd 208, rf 63, kf 74 rader, till exempel SPI eller SJVP med 0 i ett distrikt) där XML saknar elementet, se avvikelser.
4. Koder. Alla valdistrikt har 8-siffriga textkoder, 279 distinkta i varje fil, samma mängd som XML:s `VALDISTRIKT`, dbf (279 poster) och shapefilens geometrier (279 med `Lkfv` 1480xxxx av 6150 i riket). De fyra onsdagsdistrikten har koden `1480VK01` till `1480VK04` (åtta tecken men inte åtta siffror), se avvikelser.
5. Stickprov mot råceller (slumpfrö 2006, tre Majornadistrikt, tre partital vardera), alla lika i csv, xls-cell och XML:
   - 14808502 Majorna 2, kf, `kommunerna_i_valdistrikt_14.xls` blad `K_vd_14_2006` rad 579: M kolumn C = 159, V kolumn M = 114, C kolumn E = 26.
   - 14808407 Kungsladugård-Sanna 7, kf, samma blad rad 577: KD kolumn I = 34, K kolumn BA = 21, SD kolumn Q = 43.
   - 14808402 Kungsladugård-Sanna 2, rf, `landstingen_i_valdistrikt.xls` blad `L_vd_2006` rad 4004: KD kolumn I = 29, SPI kolumn AI = 1, SD kolumn Q = 23.
   (Radnummer är Excel-rader, rubriken på rad 1.)
6. FGVAL. 2006 har inga fgval-filer, men `RÖSTER_FGVAL` i XML jämfördes med 2002-agentens filer:
   - Kommunnivå rd: alla åtta värden (M 47586, C 5115, FP 49187, KD 23519, S 90547, V 32405, MP 17657, ÖVR 7040) lika med `aggregat_2002_rd.csv` nivå `goteborg`.
   - De två distrikten utan `INDELNING` (14802701, 14802702 Bergum-Gunnilse 1 och 2) har `RÖSTER_FGVAL` per parti lika med `roster_2002_<val>.csv` för samma kod (2002-namn Bergum 1 och 2) i rd, rf och kf, med två etikettskillnader: rf SPVG (23 respektive 9) heter `SFV` i 2002-filen och kf K (4 respektive 8) heter `KPML` i 2002-filen.
   - De två `Summerad`-distrikten (14807803 och 14807804 Frölunda-Ruddalen 3 och 4) saknar sina koder i 2002-filerna, men deras `RÖSTER_FGVAL` per parti i rd är exakt summan av två 2002-distrikt: 14807803 = 14802207 Västra Frölunda 7 + 14802210 Västra Frölunda 10, och 14807804 = 14802201 Västra Frölunda 1 + 14802205 Västra Frölunda 5 (unika lösningar bland alla par och tripplar i Göteborg 4). Det bekräftar val2006-notens tolkning av `Summerad`.
   - Onsdagsdistrikten i K-filen har `RÖSTER_FGVAL` 447, 495, 953 och 698, exakt lika med `giltiga` för `ej_raknade_i_vallokal-Göteborg 1` till `4` i `aggregat_2002_kf.csv`.
   - Majornas 13 distrikt saknar `RÖSTER_FGVAL` (alla `Modifierad`), så kontrollen "fem Majornadistrikt" går inte att göra för 2006; kopplingen 2002 till 2006 för Majorna får göras geografiskt i ett senare steg. 2002 års distrikt i området heter Karl Johan 1-12 (koder 14801301-14801312, kommunvalkrets Göteborg 4) och Oskar Fredrik 1-7 (14801101-14801107) enligt `distrikt_2002_rd.csv`, alltså församlingsnamn, och inget av dem har FGVAL-koppling till 2006 års Kungsladugård-Sanna 1-7 eller Majorna 1-6.

## Avvikelser och fel

- Fel i val2006-notens tolkning (sakfel, inte i CSV): noten säger att kommunvalkretsen Göteborg 4 fanns 2002 och att riksdagsresultatet 2002 för kretsen kan läsas ur `RÖSTER_FGVAL` på kretsnivå (M 14859 osv). `RÖSTER_FGVAL` per krets stämmer inte med 2002 års kretsresultat i `aggregat_2002_rd.csv` (`valkrets-Göteborg 4` M 14734, `Göteborg 2` M 8035 mot FGVAL 7580, `Göteborg 3` S 17099 mot FGVAL 16684), varken med eller utan 2002 års onsdagsröster, medan de fyra kretsarnas FGVAL summerar exakt till kommunens (47586 för M). Samma mönster i kf. Kretsindelningen ändrades alltså mellan 2002 och 2006 och kretsvärdena i 2006-filen är 2002 års röster omräknade till 2006 års kretsgränser (Valmyndighetens jämförelsetal), inte 2002 års officiella kretsresultat. Kretsnivåns FGVAL bör därför inte användas som "2002 för Göteborg 4" utan som "2002 inom 2006 års Göteborg 4". Kommunnivån är oproblematisk.
- Kodåterbruk mellan 2002 och 2006 (viktigt för databasen): 115 av 2006 års 279 distriktskoder finns även i 2002-filerna, men ingen av dem har samma namn (till exempel 14800101 är Domkyrko 1 år 2002 och Backa-Brunnsbo 1 år 2006). Endast Bergum-Gunnilse 1 och 2 är, enligt FGVAL, samma distrikt som 2002 års kod. Koden är alltså inte en stabil nyckel över 2002-2006, nyckeln måste vara (år, kod).
- Onsdagsdistrikten har koden `1480VK01`-`1480VK04` i `roster_2006_*`, `distrikt_2006_*` (xls-koden; XML har `R-1480-01` osv). Det bryter mot regeln om åtta siffror. Inte ändrat, eftersom det är källans kod och en påhittad sifferkod vore värre; nästa steg bör filtrera på `kod` som matchar `^\d{8}$` eller på namnet `I vallokal ej räknade röster` när bara riktiga distrikt ska med.
- `roster_2006_<val>_xls.csv` innehåller rader med `roster` 0 och `andel` 0.00 för partier som har en ifylld nollcell i xls (rd 208, rf 63, kf 74 rader); `roster_2006_<val>_xml.csv` saknar dessa rader (XML har inget element för 0 röster; enda 0-raden i xml-filerna är en ÖVR-rest). Inget fel, men radantalen är därför inte jämförbara mellan xls- och xml-filerna. Vid sammanslagning bör 0-rader antingen behållas i båda eller tas bort i båda.
- `distrikt_2006_indelning.csv` har fältet `kalla_fil` med semikolon i värdet (`slutresultat_1480R/L/K.xml; riksdagen_i_valdistrikt.dbf`), vilket gör att csv-modulen citerar fältet. Korrekt CSV, men avviker från de övriga filerna som saknar citattecken. Inte ändrat.
- Partikoder: `parti` skiljer sig för samma parti mellan xls- och xml-filerna (PP mot 0524, FI mot FI men Fi i `parti_kalla`, SJVP mot SJVÅP) och mellan år (2002 SFV = 2006 SPVG, 2002 KPML = 2006 K). Regeln är följd mekaniskt, så inget att rätta här, men en gemensam partitabell över åren behövs innan tidsserier byggs.
- `mandat_2006_riksdag.csv`: summan av `mandat_totalt` (fasta mandat) över de 29 kretsarna är 310, de 39 utjämningsmandaten ligger i partiernas `mandat` per krets. Stämmer med noten.

## Vad som är verifierat utan anmärkning

- 279 valdistrikt plus 4 onsdagsdistrikt per val, samma i xls, XML, dbf och shapefil (279 geometrier).
- Alla partital i alla tre källorna lika för Göteborg; alla summor på distrikts-, krets- och kommunnivå stämmer; riket och vgregion stämmer med 00-filerna.
- Riksdagsmandat 349 på riksnivå, 349 över kretsarna, 349 för 2002; Göteborgs kommun M 5, C 1, FP 2, KD 1, S 5, V 2, MP 2 (varav 1 utjämning).
- `partier_2006.csv` har 66 rader utan dubbletter och täcker alla `parti_kalla` i xml-filerna.
- INDELNING: 275 Modifierad, 2 Summerad, 2 utan attribut, samma i rd, rf och kf; Majornas 13 distrikt alla Modifierad i Göteborg 4.

## Öppna frågor till nästa steg

- Hur 2006 års onsdagsröster (rd 8883 giltiga, ej fördelbara på distrikt) ska hanteras i Majornaserien.
- Koppling 2002 till 2006 för Majorna saknas i källorna (inga FGVAL på Modifierad-distrikt), får göras via geografi eller namn.
- Om kretsnivåns FGVAL ska skrivas ut bör den märkas som "2002 omräknat till 2006 års kretsar".
