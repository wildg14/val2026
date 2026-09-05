# Webbkällor: officiella hjälpfiler för jämförbarhet mellan valen

Etikett: webbkallor. Hämtning gjord 2026-09-03.

Uppdraget var att leta upp och hämta de av Valmyndighetens hjälpfiler för
jämförbarhet mellan valen som inte redan fanns lokalt i projektet. Allt nedladdat
material ligger i
`/Users/daniel/code/Temp/Historiska dokument/dl_webb/`
med undermapp per år. Indexet finns i `/Users/daniel/code/Temp/data/historik/webbkallor.csv`.

## Kort svar på de sex frågorna

| Fråga | Svar | Var |
| --- | --- | --- |
| a. Officiell mappning 2018 till 2022 | Finns, men som xlsx och inte som skv | `dl_webb/2022/jamforelser-2018-och-2022-...-v2.xlsx` |
| b. Mappning 2010 till 2014 | Finns inte, har aldrig publicerats | Ersätts av RÖSTER_FGVAL i 2014 års XML |
| c. Mappning 2006 till 2010 | Finns inte, har aldrig publicerats | Ersätts av RÖSTER_FGVAL i 2010 års XML |
| d. Valgeografi 2002 | Finns inte, tidigaste kartmaterialet är 2006 | - |
| e. 2018 års XML med RÖSTER_FGVAL | Finns, men bara i Internet Archive | `dl_webb/2018/unz/slutresultat_1480R.xml` med flera |
| f. 2022 i nya formatet med jämförelse mot 2018 | Fälten finns i JSON men är tomma för samtliga distrikt | Se avsnittet om 2022 nedan |

## Tabell över hämtningar

Storlekar är lästa ur filsystemet respektive ur svarshuvudet Content-Length,
inte uppskattade.

| År | Adress | Lokal fil | Byte | Status | Innehåll |
| --- | --- | --- | --- | --- | --- |
| 2022 | `https://www.val.se/download/18.162047b519a91d0533119148/1666857349837/jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx` | `2022/jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx` | 423331 | 200 | Slutlig jämförbarhetsbedömning 2018 mot 2022, flikarna Fysiska valdistrikt och Uppsamlingsdistrikt |
| 2022 | `https://www.val.se/download/18.14c1f613181ed0043d5563c/1662367533764/jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt.xlsx` | `2022/jamforelser_2018_2022_valdistrikt_uppsamlingsdistrikt.xlsx` | 423204 | 200 vid hämtning, 404 i dag | Första versionen, publicerad 2022-09-05 före valdagen |
| 2018 | `https://web.archive.org/web/20210926125427id_/https://data.val.se/val/val2018/slutresultat/slutresultat.zip` | `2018/slutresultat_2018_wayback.zip` | 48716326 | 200 | 875 XML-filer, hela riket, med RÖSTER_FGVAL mot 2014 |
| 2018 | `https://historik.val.se/val/val2018/statistik/mappning_2014_2018.zip` | `2018/mappning_2014_2018_historik.zip` | 60942 | 200 | Fyra skv-filer, identiska med de redan uppackade i `scratchpad/unz/mappning_2014_2018/` |
| 2022 | `https://resultat.val.se/data/resultat/val2022/<sökväg>_S.json` | `2022/json/` | se manifest.csv | 200 | Slutligt resultat per valdistrikt i nya formatet, Göteborg, samtliga tre val |
| 2022 | `https://resultat.val.se/data/valgeografi/valgeografi_val2022.json` | `2022/valgeografi_val2022.json` | 1744628 | 200 | Trädet valtillfälle, valtyp, valkrets, kommun, valdistrikt |
| 2022 | `https://www.val.se/download/18.162047b519a91d0533118d2d/1663745020932/preliminar-riksdagsval-jamforande-statistik-2018-2022-med-uppsamlingsdistrikt-ny.xlsx` | `2022/preliminar-riksdagsval-jamforande-statistik-2018-2022-med-uppsamlingsdistrikt-ny.xlsx` | 453880 | 200 | Trots namnet ingen distriktsnivå, bara riket, valkrets och kommun |
| 2026 | `https://www.val.se/download/18.1a2972da19f159e73fd3a47/1787064655347/valdistrikt-jamforelser-mellan-2022-och-2026.xlsx` | `2026/valdistrikt-jamforelser-mellan-2022-och-2026.xlsx` | 319333 | 200 | Officiell mappning 2022 mot 2026, slutlig bedömning 2026-08-17 |
| 2026 | `https://www.val.se/download/18.332cf48819bd61ac15138b1/1785490768997/valdistrikt-vastra-gotaland-lan-2026.zip` | `2026/valdistrikt-vastra-gotaland-lan-2026.zip` | 4694513 | 200 | Valgeografi 2026 för Västra Götalands län |
| 2026 | `https://www.val.se/download/18.332cf48819bd61ac151499d/1779801380664/valdistrikt-hela-landet-2026.xlsx` | `2026/valdistrikt-hela-landet-2026.xlsx` | 448114 | 200 | Samtliga valdistrikt 2026 med koder och namn |
| 2026 | `https://www.val.se/download/18.3eba56b819e04244a687ae/1778508116907/fordelning-av-mandat-2022-och-2026.xlsx` | `2026/fordelning-av-mandat-2022-och-2026.xlsx` | 34982 | 200 | Mandatfördelning 2022 och 2026 per valkrets |
| 2026 | `https://www.val.se/valresultat-och-statistik/statistik-och-data/teknisk-beskrivning-av-resultatfiler` | `2026/*.md`, tio filer | 172117 totalt | 200 | Formatbeskrivning av 2026 års resultatfiler |

Indexsidor som sparats som underlag, alla med status 200:
`index/statistik_2010.html`, `index/statistik_2014.html`, `index/statistik_2018.html`,
`index/statistik_2006.html`, `index/2006_kartor.html`,
`index/2018_slutresultat_R_rike.html`, `index/historik_root.html`,
`index/valse_radata_2002_2022.html`, `index/valse_analyser-och-jamforelser.html`,
`index/valse_teknisk-beskrivning-av-resultatfiler.html`,
`index/valse_om-var-oppna-data.html`, `index/valse_radata-val-2026.html`.

Adresser som kontrollerats och ger 404: `https://data.val.se/val/val2018/slutresultat/slutresultat.zip`,
`https://data.val.se/val/val2014/slutresultat/slutresultat.zip`,
`https://data.val.se/val/val2010/slutresultat/slutresultat.zip`,
`https://historik.val.se/val/val2018/slutresultat/slutresultat.zip`,
`https://historik.val.se/val/val2006/statistik/index.html`,
`https://historik.val.se/val/val2002/statistik/index.html`,
`https://www.val.se/download/18.14c1f613181ed0043d5563c/1662367533764/jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt.xlsx`.

## a. Mappning 2018 till 2022

Filen heter inte mappning utan "Jämförelser 2018 och 2022 - valdistrikt och
uppsamlingsdistrikt" och ligger på sidan Analyser och jämförelser, samt på
Rådata från val 2002-2022. Den finns i två versioner:

- v1, publicerad 2022-09-05, alltså före valdagen, en preliminär bedömning.
  Adressen ger i dag 404 på val.se, den lokala kopian kommer från Internet Archive.
- v2, publicerad 2022-10-27, den slutliga bedömningen. Detta är den som ska användas.

För Göteborgs 410 rader är v1 och v2 identiska rad för rad. Skillnaden mellan
versionerna rör alltså andra kommuner.

Fliken Fysiska valdistrikt har kolumnerna Kod_2022, Valdistrikt, Jämförbart,
Valdistriktskod2018, Kod 2 2018, Kod 3 2018, Valdistriktsnamn 2018, Namn 2 2018,
Namn 3 2018, Län. Fliken Uppsamlingsdistrikt har motsvarande på kommunvalkretsnivå,
315 rader.

Utdata: `/Users/daniel/code/Temp/data/historik/mappning_2018_2022.csv`, byggd av
`/Users/daniel/code/Temp/scripts/historik/webbkallor_mappning_2018_2022.py`.
Kolumner: kod_2018;kod_2022;procent;jamforbart;namn_2018;namn_2022;avvikelse;kalla_fil.
410 rader för Göteborg, varav 85 jämförbara och 325 ej jämförbara. Inget distrikt
har mer än en 2018-kod.

Kolumnen procent är tom överallt. Källan innehåller inga procentandelar, till
skillnad från skv-mappningen 2014 till 2018 som har en procentkolumn. Det går
alltså inte att vikta delade distrikt 2018 till 2022 med officiella tal.

### Avvikelse i källan

För 104 rader i riket, varav 85 i Göteborg, står 2018-koden som ett tal i kolumnen
Jämförbart i stället för texten "ja". Skriptet tolkar dessa rader som jämförbara,
eftersom kolumnen Valdistriktskod2018 samtidigt är ifylld och 2018 års namn finns.
Att exakt alla Göteborgs 85 jämförbara rader har detta fel talar för ett
formateringsfel vid framställningen av filen, inte för något innehållsligt.
Avvikelsen är noterad per rad i kolumnen avvikelse i utdatafilen.

### Majornaområdet 2018 till 2022

Av de 23 distrikten 14800526 till 14800548 är nio jämförbara mot 2018:

| 2022 | Namn 2022 | 2018 | Namn 2018 |
| --- | --- | --- | --- |
| 14800526 | Västra Centrum Svalebo | 14801017 | Majorna-Linné, Svalebo |
| 14800536 | Västra Centrum Kusttorget | 14801036 | Majorna-Linné, Majorna |
| 14800537 | Västra Centrum Chapmans Torg | 14801031 | Majorna-Linné, Chapmans Torg |
| 14800538 | Västra Centrum Slottsskogsgat. m fl | 14801038 | Majorna-Linné, Slottsskogsgatan m fl |
| 14800539 | Västra Centrum Gråberget Västra | 14801034 | Majorna-Linné, Gråberget, Östra |
| 14800541 | Västra Centrum Godhem | 14801032 | Majorna-Linné, Godhem |
| 14800546 | Västra Centrum Kommendörsgatan m fl | 14801041 | Majorna-Linné, Djurgårdsgatan m fl |
| 14800547 | Västra Centrum Hängmattan | 14801035 | Majorna-Linné, Hängmattan |
| 14800548 | Västra Centrum Gatenhielmska | 14801042 | Majorna-Linné, Gatenhielmska |

Övriga fjorton, 14800527 till 14800535, 14800540, 14800542 till 14800545, är
enligt Valmyndigheten inte jämförbara.

Två namnbyten är värda att lägga märke till. 14801034 heter Gråberget, Östra 2018
men mappas till 14800539 Gråberget Västra 2022, alltså ett väderstrecksbyte som
inte får förväxlas med det andra Gråbergsdistriktet 14800540 Gråberget Östra som
är nytt. På samma sätt heter 14801041 Djurgårdsgatan m fl 2018 och 14800546
Kommendörsgatan m fl 2022. Bygg inte matchningar på namn i det här området.

## b och c. Mappning 2010 till 2014 och 2006 till 2010

Dessa finns inte. Det är kontrollerat på tre sätt.

1. 2014 års statistiksida, `https://historik.val.se/val/val2014/statistik/index.html`,
   listar 96 länkar. Ingen heter mappning eller indelning, och orden förekommer
   inte heller i sidans brödtext. Samma sak för 2010 års sida.
2. En sökning i Internet Archive över samtliga val.se-domäner med filtret
   `original:.*mappning.*` ger bara tre träffar i hela arkivet:
   `data.val.se/val/ep2019/statistik/mappning_ep2014_ep2019.zip`,
   `data.val.se/val/val2018/statistik/mappning_2014_2018.zip` och
   `historik.val.se/val/val2018/statistik/mappning_2014_2018.zip`.
3. Filtret `original:.*indelning.*` ger enbart nutida informationssidor på
   val.se och valcentralen.val.se, inga datafiler.

Slutsatsen är att Valmyndigheten publicerade en distriktsmappning som egen fil
exakt en gång, inför 2018, och därefter övergick till jämförelsefiler i xlsx
(2022 och 2026) samt till fältet valdistriktskodForegaendeVal i resultatfilerna
(2026).

Det som finns i stället för 2010 och 2014 är attributet RÖSTER_FGVAL i
Valmyndighetens XML, som redan finns lokalt i `scratchpad/unz/slutresultat__1_/`
för 2010 och `scratchpad/unz/slutresultat/` för 2014. Där anges föregående vals
röstetal per parti och valdistrikt, vilket i praktiken är en mappning: om ett
distrikt har FGVAL-tal alls så har Valmyndigheten bedömt det som jämförbart, och
talen identifierar vilket äldre distrikt som avses.

## d. Valgeografi 2002

Finns inte. Sidan Rådata från val 2002-2022 säger uttryckligen att material från
2002 bara finns i rent textformat, och länkar till
`https://historik.val.se/val/val_02/slutresultat/00R/00-text.html`. En sökning i
Internet Archive över val.se-domäner med filtret
`original:.*(gis|valgeografi|valdistrikt).*\.zip.*` ger som äldsta kartmaterial
2006 års shapefiler under
`historik.val.se/val/val2006/slutlig_ovrigt/statistik/kartor/` och därefter
`val2010/statistik/gis/`. Ingenting från 2002.

2006 års kartsida listar fem shapefiler: riksdagen_i_valdistrikt.zip (23361427
byte, redan uppackad lokalt), landstingen_i_valdistrikt.zip (23152146 byte),
riksdagen_i_onsdagsdistrikt.zip, riksdagen_i_kommuner.zip och
riksdagen_i_riksdagsvalkretsar.zip. De två sista kan bli aktuella om
landstingsresultat per distrikt 2006 behövs som karta, men har inte hämtats
eftersom riksdagsfilen redan finns.

Observera att 2006 års statistiksida ligger under
`/val/val2006/slutlig_ovrigt/statistik/` och inte under `/statistik/` som övriga
år. Adresser byggda efter mönstret från 2010, 2014 och 2018 ger 404 för 2006.

## e. 2018 års XML med RÖSTER_FGVAL

Hittad, men bara via Internet Archive. Den ursprungliga adressen
`https://data.val.se/val/val2018/slutresultat/slutresultat.zip` ger 404 i dag, och
zip-filen är varken länkad från 2018 års statistiksida eller åtkomlig under
`historik.val.se/val/val2018/slutresultat/`. Motsvarande zip finns däremot live för
2010 (35726026 byte) och 2014 (37450316 byte), så 2018 är ett hål i
Valmyndighetens egen publicering.

Ögonblicksbilden `web/20210926125427id_/` levererar filen med Content-Length
48716326, exakt samma som den lokala kopian. Arkivet innehåller 875 filer och en
Cksum-fil med raden `1860149709 456458515`.

Uppackat till `dl_webb/2018/unz/`:

| Fil | Byte | VALDISTRIKT | Förekomster av FGVAL |
| --- | --- | --- | --- |
| slutresultat_1480R.xml | 7503540 | 350 | 5034 |
| slutresultat_1480L.xml | 9065399 | 350 | 5099 |
| slutresultat_1480K.xml | 10002691 | 350 | 5699 |
| slutresultat_00R.xml | 11634364 | 0 | 15803 |
| slutresultat_00L.xml | 15774063 | 0 | 25647 |
| slutresultat_00K.xml | 1281682 | 0 | 16794 |

Kodning ISO-8859-1, DTD "Valresultat parti person kommun 1.7". Rotelementet VAL
har `VALDAG="20180909"` och `VALDAG_FGVAL="20140914"`. Strukturen är densamma som
i 2010 och 2014 års filer, till exempel:

```
<VALDISTRIKT KOD="14806051" NAMN="Angered, Agnesberg" RÖSTER="498" RÖSTER_FGVAL="493" ...>
  <GILTIGA PARTI="M" RÖSTER="72" RÖSTER_FGVAL="99" PROCENT="14,46" PROCENT_FGVAL="20,08" PROCENT_ÄNDRING="-5,62" ...>
```

Till skillnad från 2010 års filer är distriktsnamnen inte gallrade. Riksfilerna
00R, 00L och 00K saknar valdistriktsnivå men har FGVAL på parti- och områdesnivå.

Göteborg har 350 valdistrikt 2018 i XML. Notera att den redan lokala
`2018_R_per_valdistrikt.xlsx` bör ha samma antal, det är värt att stämma av mot
den när 2018 års data byggs.

## f. 2022 i nya formatet

Två saker att skilja på.

**Adressmönstret är hittat.** Webbappen på resultat.val.se hämtar sina data från
`https://resultat.val.se/data/resultat/val2022/<sökväg>_S.json`, där sökvägen är
den som syns i webbläsarens adressfält med snedstreck utbytta mot understreck.
S betyder slutligt, P betyder preliminärt. Mönstret är läst ur webbappens
JS-bundle, sparad som `2022/bundle_index-BxMzkuyH.js`. Nivåerna skiljer sig mellan
valtyperna: riksdagsvalet adresseras via riksdagsvalkrets, `RD_16_<distriktskod>`,
regionvalet via län och regionvalkrets, `RF_14_1401_<distriktskod>`, och
kommunvalet via län och kommun, `KF_14_1480_<distriktskod>`. Adresser byggda efter
fel mönster ger 404. Hämtat med
`/Users/daniel/code/Temp/scripts/historik/webbkallor_hamta_2022_json.py`,
manifest i `2022/json/manifest.csv`. 1241 noder efterfrågades, 1238 filer hämtades
med status 200 och 3 gav 404. De tre som saknas är `KF_S.json`, `RF_S.json`
och `KF_14_S.json`, alltså valtypsnivå för kommunval och regionval samt länsnivån
för kommunval, aggregat utan egen resultatsida och inget som rör Göteborg. Antalet distriktsfiler är 410 per
valtyp, samma 410 koder som i valgeografin.

**Men jämförelsen mot 2018 är tom.** Varje distrikts-JSON har fälten
`jamforbar`, `totaltAntalRosterForegaendeVal`, `antalRostberattigadeForegaendeVal`,
`valdeltagandeForegaendeVal` samt per parti `antalRosterForegaendeVal`,
`andelRosterForegaendeVal`, `forandringAntalRoster` och `forandringAndelRoster`.
I samtliga 1238 hämtade filer är `jamforbar` false, summorna på distriktsnivå null
och partitalen 0. Ingen enda fil har `totaltAntalRosterForegaendeVal` ifyllt. Det
gäller alla tre valtyperna, både slutligt och preliminärt räkningstillfälle.

Detta är inte en effekt av att Göteborgs distrikt ändrades. Kontrollhämtning av
`KF_01_0114_01140101_S.json` och `_P.json`, Övra Runby i Upplands Väsby, som
jämförelsefilen uttryckligen anger som jämförbart mot samma kod 2018, ger också
`jamforbar` false och nollade fält. Kontrollfilerna ligger i `2022/json_kontroll/`.
Slutsatsen är att jämförelsedata mot 2018 aldrig fylldes i i 2022 års publicerade
JSON, eller togs bort i efterhand.

Konsekvensen för projektet: för 2022 finns ingen färdig officiell jämförelse mot
2018 per valdistrikt. Den måste byggas genom att lägga samman
`mappning_2018_2022.csv` med 2018 års egna resultat. Filen
`preliminar-riksdagsval-jamforande-statistik-2018-2022-med-uppsamlingsdistrikt-ny.xlsx`
har trots sitt namn bara flikarna Riksdag, Valkrets och Per Kommun, ingen
distriktsnivå, och samma sak gäller
`slutligt-valresultat-riksdagen-jamforande-statistik-2018-2022.xlsx` i projektroten.

Två kontrollsiffror som stämmer mot varandra: valgeografi-JSON:en ger 410
åttasiffriga koder som börjar på 1480, och jämförelsefilens flik Fysiska
valdistrikt har exakt samma 410 koder för Göteborg, utan avvikelse åt något håll.

## Utöver uppdraget: 2022 till 2026

Under sökningen på val.se dök `valdistrikt-jamforelser-mellan-2022-och-2026.xlsx`
upp på sidan Rådata val 2026. Den är hämtad, eftersom den är exakt samma sorts
hjälpfil som uppdraget gällde och behövs inför 13 september 2026.

Fliken Jämförelser har kolumnerna Valdistriktskod 2026, Valdistriktsnamn 2026,
Kommun, Län, Jämförbarhet, Valdistriktskod 1 2022, Valdistriktskod 2 2022.
Värdena i Jämförbarhet är "Kan jämföras" och "Ej jämförbart". 6312 datarader i
riket, 396 i Göteborg varav 243 kan jämföras och 153 inte. Västra Centrum har
fortfarande koderna 148005xx och 48 distrikt, varav 30 kan jämföras.

Fliken Information anger att bedömningen gjordes preliminärt i mars 2026 utifrån
röstberättigadestatistik, och slutligt 2026-08-17 efter kvalifikationsdagen
14 augusti, samt att ett antal distrikt ändrades mellan de två bedömningarna. Det
är samma tvåstegsmönster som 2022, så den preliminära versionen ska inte användas.

För Majornaområdet 14800526 till 14800548 är fjorton av tjugotre distrikt
jämförbara 2022 mot 2026, och de nio som inte är det är 14800529 till 14800535,
14800538 och 14800541. Där koden kan jämföras är 2022-koden alltid identisk med
2026-koden, alltså inga kodbyten inom området den här gången.

Jag har inte skrivit någon `mappning_2022_2026.csv`, eftersom uppdraget uttryckligen
begränsade utdata till `webbkallor.csv` och `mappning_2018_2022.csv`. Filen ligger
nedladdad och redo, och kan byggas med samma logik som mappningsskriptet för
2018 till 2022 men enklare, eftersom kolumnen Jämförbarhet är korrekt ifylld här.

Formatbeskrivningen för 2026 års resultatfiler är också hämtad. Enligt
`2026/slut-rostfordelning.md` får varje valdistrikt 2026 fältet
`valdistriktskodForegaendeVal` plus `totaltAntalRosterForegaendeVal`,
`antalRostberattigadeForegaendeVal` och `valdeltagandeForegaendeVal`. Om de fälten
faktiskt fylls i, till skillnad från 2022, kommer 2026 års resultatfiler att
innehålla mappningen mot 2022 direkt. Det bör kontrolleras tidigt på valnatten,
just för att 2022 års motsvarighet visade sig tom.

## Öppna frågor

1. Ska `mappning_2022_2026.csv` byggas, och i så fall av vem i arbetsflödet.
2. Ingen officiell viktning finns för att fördela röster från ett 2018-distrikt
   över flera 2022-distrikt. För 2014 till 2018 finns procentkolumnen i
   `vd-mappning-2014-2018.skv`, men motsvarande saknas både 2018 till 2022 och
   2022 till 2026. Om Majornasidan ska visa längre tidsserier per distrikt måste
   viktningen komma från de geometriska överlappen i
   `geo_overlap_2018_2022.csv` med flera, inte från Valmyndigheten.
3. Antalet valdistrikt i Göteborg går 350 år 2018, 410 år 2022 och 396 år 2026.
   Sifforna 350 och 410 är hämtade ur XML respektive jämförelsefilen och stämmer
   mot valgeografin. Att antalet ökade med 60 mellan 2018 och 2022 förklarar
   varför bara 85 av 410 distrikt är jämförbara.
4. 2018 års XML finns bara i Internet Archive. Om den behövs långsiktigt bör
   `dl_webb/2018/slutresultat_2018_wayback.zip` flyttas från scratchpad till en
   beständig plats, eftersom scratchpad är sessionsbunden.
