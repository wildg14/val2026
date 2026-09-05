# Notering: de två huvuddokumenten och mappens README

Etikett: dokument. Datum: 2026-09-04. Steget skriver ingen ny data. Uppgiften var att
sammanfatta hela det tidigare arbetet i två dokument plus en innehållsförteckning.

## Lästa filer och hur

Alla noteringar i `/Users/daniel/code/Temp/docs/historik/noter/` lästes i sin helhet:
`val2002.md`, `val2006.md`, `val2010.md`, `v2014.md`, `val2018.md`, `geo2006.md`,
`geo2010.md`, `geo2014.md`, `geo2018.md`, `rostberattigade.md`, `vallokaler.md`,
`mandat.md`, `webbkallor.md`, `kedja.md`, `databas.md` och `granskning_2018.md`, samt
`docs/historik/datamodell.md`. Granskningarna för 2002, 2006, 2010 och 2014 lästes i den
sammanfattning som arbetsflödet lämnade över.

Följande datafiler lästes direkt, som UTF-8 med semikolon via `csv.DictReader` om inget
annat anges:

| Fil | Kolumner som användes | Vad de blev |
| --- | --- | --- |
| `data/historik/kedja_majorna_2006_2022.csv` | samtliga 18 kolumner | tabellen över de 23 distriktens motsvarigheter bakåt i `valdistrikt-historik.md` |
| `data/historik/jamforelse_tidsserie.csv` | ar, val, niva, parti, andel, giltiga, valdeltagande | de två partitabellerna i `valdistrikt-historik.md` |
| `data/historik/majorna_tidsserie.json` | `meta` | täckningsgrad och distriktslistor per år |
| `data/historik/distrikt_2006_rd.csv` | kod, namn, valkrets | kontroll av kommunvalkrets för Majornaområdet 2006 |
| `data/historik/distrikt_2022_rd.csv` | kod, namn | listan över Västra Centrums 48 distrikt |
| `data/historik/roster_2014_rd_xml.csv`, `distrikt_2014_rd.csv` | kod, parti, roster, giltiga | kontrollräkning av FI i Majorna 2014 |
| `data/historik/roster_2010_kf_xml.csv`, `distrikt_2010_kf.csv` | samma | uppdelning av raden SUMMA_ÖVRIGA för Majorna 2010 |
| `data/historik/webbkallor.csv` | ar, typ, adress, status | avsnittet om filer som saknas |
| `data/historik/majorna_historik.sqlite` | radantal i fem tabeller | kontroll av talen i sammanfattningen |

Följande originalfiler öppnades för att belägga avsnittet om de trasiga 2018-filerna:
`Historiska dokument/rostberattigade.xls`, `rostberattigade (1).xls`, `rostberattigade (2).xls`,
`vallokal.xls` och `mottagna_fortidsroster.xls` med `olefile` och `xlrd` med argumentet
`file_contents`, samt de fem kopiorna i `scratchpad/repaired/` med `openpyxl`. Även
`rostberattigade (3).xls` till `(8).xls` öppnades med xlrd för att kontrollera 2010 och 2014
års filmappning. `scratchpad/unz/slutresultat/slutresultat_1480R.xml` och
`scratchpad/unz/slutresultat__1_/slutresultat_1480R.xml` lästes de första 400 bytena av för
att belägga vilket år respektive zip-arkiv innehåller.

## Skrivna filer

| Fil | Innehåll |
| --- | --- |
| `docs/historik/inventering.md` | sammanfattning i tio meningar, källfilstabell per valår, de fem trasiga 2018-filerna och reparationen, saknade filer med de adresser som provats, vad datan möjliggör redaktionellt indelat i säkert, med förbehåll och går inte, samt nio rekommenderade nästa steg i prioritetsordning |
| `docs/historik/valdistrikt-historik.md` | indelningarna år för år, vad som drev förändringen, tabell över de 23 distrikten 2022 med motsvarigheter bakåt, definitionen av jämförbart Majorna per år, de tre metoderna med styrkor och svagheter och en rekommendation, fallgropar och tidsserier för riksdags- och kommunvalet |
| `docs/historik/README.md` | innehållsförteckning över `docs/historik` och `data/historik` samt körordning för skripten |
| `docs/historik/noter/dokument.md` | denna notering |

Inga befintliga filer har ändrats. Ingen ny data har skrivits.

## Kontroller

- Alla tal i de två dokumenten kommer ur en notering eller en datafil. Talen i tabellerna är
  genererade programmatiskt ur `kedja_majorna_2006_2022.csv` respektive
  `jamforelse_tidsserie.csv`, inte avskrivna.
- FI:s 16,50 procent i Majorna i riksdagsvalet 2014 kontrollräknades från grunden ur
  `roster_2014_rd_xml.csv` och `distrikt_2014_rd.csv` eftersom talet är ovanligt högt: 3458
  röster av 20960 giltiga, alltså 16,50 procent. Talet stämmer.
- Radantalen 1918 distrikt, 92333 röster, 11961 crosswalkrader, 2487 tidsserierader och 108
  medlemsrader lästes direkt ur `majorna_historik.sqlite` och stämmer med `datamodell.md`.
- Skrivreglerna kontrollerades med `grep` på tankstreck, utropstecken och emoji i alla tre
  dokumenten: inga träffar.

## Avvikelser som hittades under skrivandet

1. **Filmappningen för de trasiga 2018-filerna är fel i `rostberattigade.md`.** Noteringen
   skriver att `2018_rostberattigade_R.xlsx` är en kopia av `rostberattigade (1).xls`.
   Rubrikraden i originalen visar att `rostberattigade.xls` börjar med
   `riksdagsvalkrets_id` (6005 rader gånger 26 kolumner) och alltså är R,
   `rostberattigade (1).xls` börjar med `landstings_id` (5964 gånger 28) och är L, och
   `rostberattigade (2).xls` börjar med `län_id` (6005 gånger 28) och är K. De reparerade
   kopiorna har rätt innehåll under rätt namn, så inga tal berörs. Meningen i
   `rostberattigade.md` bör rättas; den ligger som punkt 8 bland de rekommenderade nästa
   stegen i `inventering.md`.
2. **`geo2006.md` anger fel kommunvalkrets för Stigberget 1-4.** Noteringen skriver att alla
   17 distrikt i Majornaområdet 2006 låg i kommunvalkrets Göteborg 4. Kolumnen `valkrets` i
   `distrikt_2006_rd.csv` visar att 14805901 till 14805904 Stigberget 1-4 låg i Göteborg 3
   och att bara Kungsladugård-Sanna 1-7 och Majorna 1-6 låg i Göteborg 4. `mandat.md` har
   rätt uppgift. Ingen beräkning berörs, eftersom områdesdefinitionen bygger på geometri.
   Rättelsen står i avsnittet Fallgropar i `valdistrikt-historik.md`.
3. **Exakt felmeddelande för de trasiga xls-filerna.** Reparationsmetoden var beskriven i
   uppdraget men inte i någon notering. Felet är
   `xlrd.compdoc.CompDocError: Workbook corruption: seen[2] == 4`, och strömmen `Workbook`
   går att läsa med olefile och skicka vidare till xlrd med `file_contents`, vilket
   kontrollerades genom att öppna `vallokal.xls` den vägen. De reparerade kopiorna är
   skrivna med openpyxl 3.1.5 den 2026-09-03 klockan 19.13 enligt `docProps/core.xml`.
4. **Årsmappningen av de två XML-arkiven kontrollerades.** `slutresultat.zip` innehåller
   valet 2014 (`VALDAG="20140914"`) och `slutresultat (1).zip` valet 2010
   (`VALDAG="20100919"`), i enlighet med hur de packats upp i
   `scratchpad/unz/slutresultat/` respektive `scratchpad/unz/slutresultat__1_/`.

## Öppna frågor

- 2018 års XML från Internet Archive är hämtad men inte inläst. Det är den enda återstående
  luckan i sifferunderlaget och skulle ge en oberoende kontroll av steget 2014 till 2018.
- Röstberättigade efter ålder och kön för 2022 ligger i projektroten men är inte inlästa, så
  den demografiska serien slutar 2018.
- Ingen områdesdefinition finns för Masthugget eller Linnéstaden. Grannjämförelser kräver
  att en sådan byggs med samma metod som för Majorna.
- Kungsten finns inte som valdistriktsnamn något år 2006-2022 och kan inte redovisas.
- Om scratchpad rensas måste zip-arkiven packas upp igen, webbhämtningarna göras om och de
  fem trasiga 2018-filerna repareras på nytt innan dokumenten går att belägga i alla delar.
