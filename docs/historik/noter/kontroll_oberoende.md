# Oberoende kontroll av siffror och polygoner

Gjord 2026-09-05 i huvudsessionen, utan agenter, med ny kod som inte återanvänder något av
skripten i `scripts/historik/`. Syftet var att avgöra om en större granskning behövs.

## Siffror: omräkning rakt ur råfilerna

Majornas summa per parti räknades om ur källfilerna för de distrikt som `geo_majorna_<år>.csv`
klassar som jämförbart Majorna (andel_i_majorna minst 0,5), och jämfördes med
`data/historik/majorna_tidsserie.csv`.

| År och val | Källa | Partier lika | Giltiga råfil | Giltiga tidsserie |
| --- | --- | --- | --- | --- |
| 2006 riksdag | shapefilens dbf `riksdagen_i_valdistrikt.dbf` | V, S, MP, M, SD lika | 18 815 | 18 803 |
| 2010 riksdag | `slutligt_valresultat_valdistrikt_R.xls` | V, S, MP, M, SD lika | 20 452 | 20 452 |
| 2014 kommun | `2014_kommunval_per_valdistrikt.xlsx` | V, S, MP, M, FI lika | 21 063 | 21 063 |
| 2018 kommun | `2018_K_per_valdistrikt.xlsx`, flik K antal | V, S, MP, M, SD, D lika | 21 616 | 21 616 |

Alla partital stämmer exakt. Skillnaden på 12 röster 2006 beror på omräkningen, inte på databasen:
dbf-filen saknar kolumn för övriga ogiltiga, så TOT_ROST minus BLANK_ROST innehåller de 12 övriga
ogiltiga rösterna. XML-källan som databasen använder särredovisar dem (`distrikt_2006_rd.csv`: giltiga
18 803, blanka 366, övriga ogiltiga 12, röstande 19 181).

## Polygoner

Alla årens Majornapolygoner (`distrikt_<år>_majornaomradet.geojson`, filtrerade till jämförbart
Majorna, samt 2026 ur Valmyndighetens fil) projicerades till SWEREF99 TM och jämfördes med unionen
av sidans egen `data/distrikt.geojson` (2022, 23 distrikt, 4,6555 km2).

| År | Distrikt | Union km2 | Inom 2022-unionen | Täcker 2022-unionen | Ogiltiga geometrier | Symmetrisk skillnad |
| --- | --- | --- | --- | --- | --- | --- |
| 2006 | 17 | 4,6541 | 99,99 % | 99,96 % | 0 | 0,2 ha |
| 2010 | 17 | 4,6540 | 99,99 % | 99,96 % | 0 | 0,2 ha |
| 2014 | 17 | 4,6540 | 99,99 % | 99,96 % | 0 | 0,2 ha |
| 2018 | 22 | 4,6541 | 99,99 % | 99,96 % | 0 | 0,2 ha |
| 2022 | 23 | 4,6555 | 100 % | 100 % | 0 | 0 |
| 2026 | 23 | 4,6554 | 100 % | 100 % | 0 | 0 |

Bilden `docs/historik/karta_kontroll_2006_2026.png` visar alla sex åren med 2022-unionen som röd
kontur: inga hål, inga överskjutningar.

## Slutsats

Ingen större granskning behövs för områdesnivån. Det som fortfarande inte är oberoende kontrollerat
är steget 2014 till 2018 per distrikt (vilar på Valmyndighetens officiella mappning, 2018 års XML är
hämtad men inte inläst) och de areaviktade skattningarna per distrikt, som ändå bara ska användas
med förbehåll.

2018 års XML har därefter lästs in (`docs/historik/noter/xml2018.md`). Kedjekontrollen bekräftar
klassningen i `kedja_2014_2018.csv` fullt ut: Valmyndigheten ger FGVAL exakt för de 122 distrikt som
klassas identisk eller namnbyte, aldrig för de 226 som klassas delad, omritad eller ny, och där FGVAL
finns matchar den den faktiska 2014-röstningen för alla riktiga partier. Areaskattningen kunde
däremot inte prövas mot ett facit, eftersom just de delade och omritade distrikten i Majorna-Linné
helt saknar FGVAL; det enda som gick att visa är att areametoden och den officiella skv-viktningen
skiljer sig från varandra med i genomsnitt 35 röster per distrikt och parti.
