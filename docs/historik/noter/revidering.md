# Revidering: rättelser av granskarens luckor

Etikett: revidering. Datum: 2026-09-04. Uppdraget var att åtgärda 16 luckor som en granskare
hade hittat i `docs/historik/valdistrikt-historik.md`, `docs/historik/inventering.md`,
`docs/historik/datamodell.md` och fyra av noteringarna under `docs/historik/noter/` (5 med
severity stor, 11 med severity liten). Ingenting i `index.html`, `data/valdata_2022.*`,
`scripts/*.py` på toppnivån, testerna eller README har rörts. Detta är den enda filen jag har
skrivit ny; övriga ändringar är redigeringar av befintliga filer under `docs/historik/`, plus
två nya datafiler under `data/historik/` och ett nytt skript under `scripts/historik/`.

## Filer jag läste

För att kontrollera varje lucka läste jag källfilerna själv i stället för att lita på
granskningstexten:

- `data/historik/kedja_majorna_2006_2022.csv` (kolumnen `jamforbar_tillbaka_till` för
  14800546) och `docs/historik/noter/kedja.md` (raden om Kommendörsgatan m fl).
- `data/historik/jamforelse_tidsserie.csv`, alla rader för `val=rd` och `val=kf` i
  Göteborg och riket 2002, samt hela raden för SD 2002 (saknas för `rd`, finns för `kf`).
  Kontrollerade dessutom hela riksdags- och kommunfullmäktigetabellen i
  `valdistrikt-historik.md` programmatiskt mot samma fil, parti för parti och år för år
  (se avsnittet "Vad jag kontrollerade men inte ändrade" nedan).
- `data/historik/rostberattigade_2010_kf.csv`, `_2014_kf.csv` och `_2018_kf.csv`
  (kategorin "Ej svenska medborgare", summerad) samt `data/historik/distrikt_2010_rd.csv`,
  `_kf.csv` och motsvarande för 2014 och 2018 (kolumnen `rostberattigade` summerad per val)
  för att räkna fram nettoskillnaden mellan kommun- och riksdagsvalets röstberättigade.
- `data/historik/distrikt_2018_rd.csv` och `distrikt_2022_rd.csv` (sökning på "Kungsten").
- `data/historik/geo_majorna_2006.csv` (kolumnen `area_m2` summerad) och samma för
  `geo_majorna_2010.csv` som kontroll.
- `data/historik/geo_mappning_2014_2018_jamforelse.csv` (kolumnen
  `diff_geo_minus_officiell`, absolutbelopp, medelvärde och andel över 0,20 för raderna med
  `status = bada`).
- `data/historik/distrikt_2010_rd.csv` och `distrikt_2014_rd.csv` (mängdjämförelse av
  kolumnen `kod`, med kontroll av vilka gemensamma koder som är onsdags- eller
  uppsamlingsdistrikt).
- `majorna-valresultat-2022.xlsx` och `fortidsroster.csv` i projektroten (öppnade båda för
  att se vad de faktiskt innehåller innan jag skrev raderna om dem).
- `/private/tmp/.../scratchpad/unz/valgeografi_2022/VD_14_20220910_Val_20220911.json`, samma
  fil som `geo2006.py`, `geo2010.py`, `geo2014.py` och `geo2018.py` redan använder för
  2022-sidan av jämförelsen (egenskaper `Lkfv`, `Vdnamn`, SWEREF99 TM).

## Vad jag ändrade

### docs/historik/valdistrikt-historik.md

1. Tabellen "De 23 distrikten 2022 och deras motsvarigheter bakåt", raden 14800546
   Kommendörsgatan m fl: kolumnen "Jämförbar bakåt till" ändrad från 2022 till 2018. Både
   källfilen och brödtexten direkt under tabellen sa redan 2018.
2. Läsanvisningen före riksdagstabellen: bindestrecksförklaringen skriver nu att ett
   bindestreck betyder att partiet inte särredovisas på den nivån det året, utan ingår i
   ÖVR eller SUMMA_ÖVRIGA, eller att partiet inte fanns, med SD 2002 som utskrivet exempel
   (ingen egen rad i riksdagsvalet, men en egen rad med 4532 röster i kommunvalet).
3. Fallgropen "Röstberättigade skiljer sig mellan valen": skriven om så att 29976, 34410 och
   38623 nu beskrivs som antalet utländska medborgare med rösträtt (vilket de är), med den
   faktiska nettoskillnaden mellan kommunvalets och riksdagsvalets röstberättigade i Göteborg
   tillagd (15212, 18529, 22758), och en mening om att utlandssvenskar drar åt andra hållet.
4. Tabellen "Definitionen jämförbart Majorna per år", 2006-raden: "Sammanlagd yta" ändrad
   från 4,6537 till 4,6541 km2, så att den stämmer med summan av `area_m2` i
   `geo_majorna_2006.csv` och med sina egna grannkolumner (4,6554 minus 1700 m2 plus 400 m2).
5. Nytt stycke direkt efter definitionen av 50 procent-regeln, som skriver ut alla tre
   trösklarna (0,1 procent för att tas med i `geo_majorna_<år>.csv`, 0,95 för klassen `inne`,
   0,5 för medlemskap) och nämner att de sammanfaller, med `geo2018.md` rad 67 som belägg.
6. Stycket "Inget distrikt något år hamnade nära tröskeln": en mening tillagd om att den
   tomma `delvis`-klassen är belagd i geo-noteringarna, som skriver ut även uteslutna
   kandidater, och inte i `majorna_medlem` självt, som bara innehåller de distrikt som togs
   med.
7. Metod 1, Areaöverlapp, stycket Svagheter: "12,4 procentenheter" ändrat till "12,3
   procentenheter", vilket är vad `geo_mappning_2014_2018_jamforelse.csv` faktiskt ger
   (medelvärde 12,3078... över de 483 raderna med `status = bada`).
8. Fallgropen "Koder återanvänds mellan år": "29 gemensamma distriktskoder" ändrat till
   "33 gemensamma distriktskoder, samtliga med olika namn, varav fyra är onsdags- och
   uppsamlingsdistrikt (14800001-14800004), så bland de riktiga valdistrikten är det 29
   koder som återanvänds". Mängdjämförelsen av `distrikt_2010_rd.csv` och
   `distrikt_2014_rd.csv` gav exakt 33 gemensamma koder.

### docs/historik/inventering.md

9. Avsnittet "Kräver förbehåll", stycket "Grannområden som jämförelse": meningen om att
   Kungsten "inte finns som valdistriktsnamn något år 2006-2022 och kan inte redovisas alls"
   ersatt med att Kungsten finns 2018 (14805043) och 2022 (14800706) men saknas som egen kod
   2006, 2010 och 2014.
10. Avsnittet "Sammanfattning": "med en avvikelse på 0,03 procent av ytan" ändrat till
    "0,03 procent av ytan från och med 2010 och 0,04 procent för 2006", i linje med
    `valdistrikt-historik.md` och `geo2006.md`.
11. Kvalitetsanmärkningar 2010: en rättelse tillagd om att uppgiften om 19 distrikt i
    stadsdelsnämnden Majorna inte går att belägga (shapefilen, XML-filen och
    `distrikt_2010_rd.csv` har alla 17), med hänvisning till `noter/geo2010.md`.
12. "Källfiler per valår", avsnittet 2022: två rader tillagda för `majorna-valresultat-2022.xlsx`
    (sidans egen sammanställning för Majorna 2022, med metod- och källflik, öppnad och
    kontrollerad) och `fortidsroster.csv` (mottagna förtidsröster per lokal och dag 2022 för
    hela riket, ISO-8859-1, samma sorts fil som `fortidsroster_<år>.csv` för 2010-2018 men
    inte inläst till `data/historik/`).
13. "Rekommenderade nästa steg", punkt 4: samma flyttvarning som punkt 1 och 2 tillagd (flytta
    `valdistrikt-jamforelser-mellan-2022-och-2026.xlsx` och de fyra andra 2026-nedladdningarna
    ut ur `scratchpad/dl_webb/2026/`), med hänvisning till `noter/webbkallor.md`.
14. "Övrigt som saknas": ny punkt om att hela 2026-materialet bara finns i scratchpad och
    saknar spår i `data/historik/`, så uppgiften om fjorton jämförbara distrikt 2022-2026
    bara är belagd i `noter/webbkallor.md`.

### docs/historik/datamodell.md

15. Avsnittet `majorna_medlem`: samma sak som punkterna 5 och 6 ovan, skrivet för
    databasperspektivet: de tre trösklarna radas upp, och det står att den tomma
    `delvis`-klassen är belagd i geo-noteringarna, inte i tabellen `majorna_medlem` själv.

### docs/historik/noter/geo2014.md

16. Rad 56: "4.6549 km2" ändrat till "4.6554 km2" (unionens yta, som alla andra ställen i
    materialet anger till 4,6554 km2; med 4.6549 stämde inte notens egen procentsats 99,97).
17. Rad 135 (nu förskjuten): "12.4 procentenheter" ändrat till "12.3 procentenheter", samma
    rättelse som punkt 7 ovan, gjord på båda ställena som upprepar talet.

### docs/historik/noter/geo2006.md

18. Rekommendationsavsnittet: meningen "Om resultatfilerna 2010 anger 19 distrikt... det får
    steget för 2010 avgöra" ersatt med en mening som säger att uppgiften om 19 distrikt inte
    går att belägga, med hänvisning till `geo2010.md`.
19. "Öppna frågor": raden om 19 mot 17 distrikt struken och ersatt med en rad som säger att
    frågan är rättad 2026-09-04, med hänvisning till rättelsen i `inventering.md`.

### data/historik/ (ny data, ren datafråga ur befintlig källa)

20. `geo_majorna_2022.csv` och `distrikt_2022_goteborg.geojson` skrivna, med samma kolumner
    och format som motsvarande filer för 2006, 2010, 2014 och 2018. Källan är exakt samma
    GeoJSON som de fyra tidigare geo-skripten redan läser för 2022-sidan
    (`VD_14_20220910_Val_20220911.json`, Västra Götalands län, SWEREF99 TM). Eftersom
    Majorna-unionen 2022 per definition är unionen av de 23 distrikten 14800526-14800548
    ligger alla 23 till exakt 100 procent i den (`andel_i_majorna = 1.0000`, klass `inne`),
    och kontrollen i skriptet visar att inget annat Göteborgsdistrikt alls overlappar unionen
    (indelningen är en ren partition, kontrollerat overlapp 0,0000 m2). Unionens yta blir
    4,6554 km2, samma tal som redan stod i `valdistrikt-historik.md` och som nu är kontrollerat
    direkt ur geometrin i stället för bara härlett ur de andra fyra årens täckningsgrad.
    Skript: `scripts/historik/revidering_geo2022.py`, körbart med
    `scratchpad/venv/bin/python`.

## Vad jag kontrollerade men inte ändrade

Sista raden i luckelistan pekade på "källraderna under riksdags- och
kommunfullmäktigetabellerna" i `valdistrikt-historik.md` utan att ange vad som var fel. Jag
kontrollerade därför programmatiskt varje siffra i båda tabellerna (alla partiandelar,
giltiga röster och valdeltagande, år för år och nivå för nivå) mot
`data/historik/jamforelse_tidsserie.csv` och fann noll avvikelser. Källraderna under
tabellerna ("Källa: `data/historik/jamforelse_tidsserie.csv`, ...") stämmer alltså och är
lämnade oförändrade. Uppgifterna om SUMMA_ÖVRIGA och Vägvalet i läsanvisningen efter
kommunfullmäktigetabellen kontrollerades inte specifikt, eftersom ingen lucka pekade dit.

## Medvetet lämnat

- Gap om att `geo_majorna_<år>.csv`-källraden under tabellen "Definitionen jämförbart
  Majorna per år" pekade på en fil som saknades är löst genom att bygga filen (punkt 20
  ovan), så själva källraden i `valdistrikt-historik.md` behövde inte ändras: mönstret
  `geo_majorna_<år>.csv` täcker nu även 2022.
- Ingen ny `docs/historik/noter/geo2022.md` skrevs. De två nya filerna är triviala att
  härleda (unionen av de 23 distrikten är per definition Majorna-unionen), så en hel
  noteringsfil bedömdes vara mer än vad luckan bad om; beskrivningen av hur filerna byggdes
  står i stället här och som docstring i skriptet.
- `docs/historik/noter/databas.md` rad 35 räknar upp `geo_majorna_<ar>.csv` för 2006, 2010,
  2014 och 2018 utan 2022. Ingen lucka i uppdraget pekade på den raden, så den är lämnad
  orörd; den är inte felaktig, bara ofullständig nu när 2022-filen finns.
- Talet 12,3 (tidigare 12,4) är beräknat med Pythons `statistics`-fria medelvärde av
  absolutbeloppet, avrundat till en decimal (12,3078... procentenheter). Ingen omräkning av
  hela `geo_mappning_2014_2018_jamforelse.csv` gjordes, bara kontrollen av det aggregerade
  talet.
- Databasen `majorna_historik.sqlite` byggdes inte om. Ändringarna i denna omgång är
  dokumentationstext plus två nya geo-filer för 2022 som inte matas in i databasen av
  `bygg_databas.py`; om filerna ska in i tabellerna `crosswalk` och `majorna_medlem` för 2022
  krävs en ändring av det skriptet, vilket ligger utanför den här luckelistan.

## Skrivregler

Bindestreck används genomgående, inga tankstreck. Inga utropstecken eller emoji. Alla nya tal
i denna not är antingen citerade direkt ur källfilerna ovan eller beräknade av mig med de
kommandon som listas här, inte uppskattade.
