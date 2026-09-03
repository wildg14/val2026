# Vallokaler och mottagna förtidsröster i Göteborg 2010, 2014 och 2018

Etikett: vallokaler. Skript: `/Users/daniel/code/Temp/scripts/historik/vallokaler_fortidsroster_2010_2018.py` (körs med venv-python, behöver xlrd, openpyxl och pyproj, kan köras om när som helst och skriver om alla filer nedan). Källvägarna ligger som konstanter högst upp i skriptet.

## Källfiler och hur de lästes

| År | Innehåll | Fil | Format | Rader (riket) | Göteborg |
|----|----------|-----|--------|---------------|----------|
| 2010 | vallokaler | `Historiska dokument/vallokal (2).xls` | xls, xlrd, blad "Sheet1", rubriker på rad 0 | 5668 | 282 |
| 2014 | vallokaler | `Historiska dokument/vallokal (1).xls` | xls, xlrd, blad "Sheet1" | 5837 | 297 |
| 2018 | vallokaler | `scratchpad/repaired/2018_vallokal.xlsx` (reparerad kopia av `Historiska dokument/vallokal.xls` enligt förarbetet) | xlsx, openpyxl, blad "Sheet1" | 6004 | 350 |
| 2010 | förtidsröster | `Historiska dokument/mottagna_fortidsroster (2).xls` | xls, xlrd, blad "Sheet1" | 3346 lokaler + summarad | 105 |
| 2014 | förtidsröster | `Historiska dokument/mottagna_fortidsroster (1).xls` | xls, xlrd, blad "Sheet1" | 3095 + summarad | 72 |
| 2018 | förtidsröster | `scratchpad/repaired/2018_mottagna_fortidsroster.xlsx` (reparerad kopia av `Historiska dokument/mottagna_fortidsroster.xls`) | xlsx, openpyxl, blad "Sheet1" | 2739 + summarad | 81 |

Formaten är binära, strängarna kommer ut som Unicode, inga kodningsfrågor. Urvalet är `LAN == 14` och `KOMMUN == 80` (vallokaler) respektive `lan == 14` och `kom == 80` (förtidsröster). Tal i xls kommer som flyttal (282.0) och i xlsx som heltal; skriptet kräver heltal i alla antalskolumner och avbryter annars.

### Vallokalsfilernas kolumner

2010 (25 kolumner): `VALDAG, LAN, NAMN_LAN, KOMMUN, NAMN_KOMMUN, VALNAMND, HEMSIDA, TELNR, KLAR, VALKRETS, NAMN_VALKRETS, VALDISTRIKT, NAMN_VALDISTRIKT, LOKAL, ADRESS1, ADRESS2, ADRESS3, POSTORT, TILLGÄNGL, KLAR, STATUS, X, Y, DAG, ÖPPETPASS`.

2014 (31 kolumner): `LAN, NAMN_LAN, KOMMUN, NAMN_KOMMUN, VALNAMND, HEMSIDA, TELNR, KLAR, VALDISTRIKT, NAMN_VALDISTRIKT, AKTIV_R, VALDAG_R, AKTIV_L, VALDAG_L, AKTIV_K, VALDAG_K, KRETS_K, KRETS_NAMN_K, AKTIV_E, VALDAG_E, LOKAL, ADRESS1, ADRESS2, ADRESS3, TILLGÄNGL, KLAR, STATUS, X, Y, DAG, ÖPPETPASS`.

2018 (31 kolumner): som 2014 men `KLAR` heter `KOMMUN_KLAR` respektive `LOKAL_KLAR`, och `X, Y` har ersatts av `LATITUD, LONGITUD`.

Rubriken `KLAR` förekommer två gånger 2010 och 2014; den första står bland kommunuppgifterna (kommunens klarmarkering), den andra bland lokaluppgifterna (lokalens klarmarkering). Skriptet läser dem som `KLAR` och `KLAR_2`. En rad per valdistrikt i alla tre filerna, inga dubbletter, inga summarader, ingen rad för uppsamlingsdistrikten.

Kolumnbetydelse och vad de innehåller för Göteborg:

- `VALDISTRIKT` är distriktsnumret inom kommunen (911, 1011 osv). Koden byggs som två siffror län, två siffror kommun och fyra siffror distrikt: 14, 80, 911 blir `14800911`.
- `VALKRETS`/`NAMN_VALKRETS` (2010) och `KRETS_K`/`KRETS_NAMN_K` (2014, 2018) är kommunvalkretsen. 2010 och 2014: 1 Göteborg, Hisingen (75 respektive 81 distrikt), 2 Göteborg, Öster (70, 73), 3 Göteborg, Centrum (65, 69), 4 Göteborg, Väster (72, 74). 2018: krets 0 "Göteborg" för alla 350. Skrivs som `148001`-`148004` respektive `148000`.
- `LOKAL` är vallokalens namn, `ADRESS1` oftast rummet (Matsalen, Sal 146), `ADRESS2` gatuadressen. `ADRESS3`, `POSTORT` (finns bara 2010) och `TILLGÄNGL` är tomma för alla göteborgsrader.
- `X`, `Y` (2010, 2014) är RT90 2,5 gon V med X som nordlig och Y som östlig koordinat (X omkring 6403000, Y omkring 1269000 i Majorna). `LATITUD`, `LONGITUD` (2018) är WGS84 i decimalgrader.
- `VALDAG` (2010, 20100919), `VALDAG_R/L/K` (2014 "14-SEP-14", 2018 "2018-09-09") och `DAG` (100919, 140914, "2018-09-09") anger valdagen; alla tre valen har samma dag på varje rad (kontrolleras). `ÖPPETPASS` är "08:00-20:00" på alla rader alla år, en rad per distrikt, så filen innehåller inga extra öppetpass.
- `AKTIV_R/L/K` är J och `AKTIV_E` N (2014, 2018), `VALDAG_E` tom: inget EU-val de åren.
- Konstanter för alla göteborgsrader: `VALNAMND` "Valnämnden i Göteborgs kommun", `HEMSIDA` www.goteborg.se, `TELNR` "031 368 0000" (2010) respektive "031 365 0000" (2014, 2018), båda `KLAR` J, `STATUS` E.

### Förtidsröstfilernas kolumner

Samma uppbyggnad alla tre åren: `lan, län, kom, kommun, lokalid, lokal`, sedan en kolumn per datum (19 stycken) och sist `Totalt`. Sista raden i varje fil har tomma id-kolumner och `lokal` = "summa" med rikets summa per dag. Ingen adress, ingen typ av lokal (bibliotek, äldreboende, sjukhus) finns i filen; det får läsas ut ur namnet.

| År | Datumkolumner | Första | Sista (= valdagen) | Göteborgslokaler | Göteborg totalt | Riket (källans summarad) |
|----|---------------|--------|--------------------|------------------|-----------------|--------------------------|
| 2010 | 19 | 2010-09-01 (onsdag) | 2010-09-19 (söndag) | 105 | 138577 | 2377639 |
| 2014 | 19 | 2014-08-27 (onsdag) | 2014-09-14 (söndag) | 72 | 153111 | 2672615 |
| 2018 | 19 | 2018-08-22 (onsdag) | 2018-09-09 (söndag) | 81 | 160925 | 2918072 |

Förtidsröstningsperioden är alltså 18 dagar före valdagen till och med valdagen alla tre åren, 19 kalenderdagar. Göteborg tog emot förtidsröster alla 19 dagarna varje år. Kontroller: summan av dagkolumnerna är lika med `Totalt` för varje lokal i hela riket alla tre åren, och källans summarad är lika med summan av alla lokalrader (2377639, 2672615, 2918072). Lokal-id är unika inom Göteborg. Fem göteborgslokaler 2010 och två 2014 och 2018 har 0 röster (Asperö skola, Vrångö skola alla år; 2010 även Bokbussarna, Lillhagsparkens Äldreboende, Kärrahus); de behålls i filerna.

## Skrivna filer (alla i `/Users/daniel/code/Temp/data/historik/`, UTF-8, semikolon, punkt som decimaltecken, koder som text)

Vallokaler:

- `vallokaler_<år>.csv` (282, 297, 350 rader), en rad per göteborgsdistrikt, sorterad på kod. Kolumner: `ar;kod;namn;kommunvalkrets_kod;kommunvalkrets;lokal;adress1;adress2;adress3;postort;tillganglighet;status;x_rt90;y_rt90;latitud;longitud;koord_kalla;valdag;dag;oppetpass;aktiv_rd;aktiv_rf;aktiv_kf;aktiv_eu;valdag_eu;kommun_klar;lokal_klar;valnamnd;hemsida;telnr;kalla_fil`. Alla källkolumner är med: `namn` = NAMN_VALDISTRIKT, `x_rt90`/`y_rt90` = X/Y (tomma 2018), `latitud`/`longitud` = LATITUD/LONGITUD 2018 och för 2010 och 2014 omräknade från RT90 med pyproj (EPSG:3021 till EPSG:4326, sex decimaler), vilket `koord_kalla` anger på varje rad. Datum är normaliserade till ÅÅÅÅ-MM-DD. `aktiv_*` och `valdag_eu` är tomma 2010 (kolumnerna finns inte). Konstanterna (valnämnd, hemsida, telefon, klarmarkeringar, status) är med för fullständighetens skull.
- `vallokaler_<år>_lokaler.csv` (162, 169, 181 rader), en rad per vallokal definierad som `lokal` + `adress2` (gatuadress), med `antal_distrikt`, `koder` (mellanslagsseparerade), `distriktnamn` (separerade med " | "), `latitud`, `longitud` (minsta värdet bland raderna) och `antal_koordinater` (hur många olika koordinater lokalen har i källan, se avvikelser). Stavningsvarianter i källan gör att samma lokal kan bli två rader (2018: "Majornas vuxengymnasium" och "Majorns vuxengymnasium", båda Styrmansgatan 21; Kungsladugårdsskolan med "Birger Jarlsgatan 1" och "Birger Jarlsgat. 1, entré B"; Sannaskolan med "Jordhyttegatan 5" och "Jordhyttegatan 5, ingång C"). Inget är normaliserat.

Förtidsröster:

- `fortidsroster_<år>.csv` (2100, 1440, 1620 rader), långt format `ar;lokalid;lokal;datum;antal`, 19 datumrader per lokal (nollor behålls) och därefter en rad med `datum` = "totalt" och `antal` = källans kolumn `Totalt`. Sorterad på lokalid numeriskt. Den som summerar per lokal ska alltså utesluta raderna med `datum` = totalt.
- `fortidsroster_<år>_lokaler.csv` (105, 72, 81 rader): `ar;lokalid;lokal;totalt;antal_dagar;forsta_dag;sista_dag;rang_goteborg;andel_goteborg_procent;storsta_dag_antal;storsta_dag;antal_valdagen`. `antal_dagar` är antal dagar med minst en mottagen röst, `rang_goteborg` 1 för flest röster (lika tal ger samma rang), `andel_goteborg_procent` lokalens andel av Göteborgs förtidsröster, `antal_valdagen` antal mottagna på valdagen.
- `fortidsroster_per_dag_2010_2018.csv` (60 rader): `ar;datum;dag_nr;dagar_till_valdag;veckodag;goteborg;goteborg_lokaler_med_roster;riket_summarad_kalla`, en rad per dag och år plus en totalrad per år. `riket_summarad_kalla` är källans egen summarad.
- `fortidsroster_majornaomradet_2010_2018.csv` (23 rader): `ar;lokalid;lokal;omrade;placering;totalt;antal_dagar;rang_goteborg;andel_goteborg_procent` för lokalerna i tabellen nedan (urvalet är listan `MAJORNA_LOKALER` i skriptet).

## Förtidsröstningslokaler i eller nära Majorna

Lokal-id är stabila mellan åren när lokalen är densamma (8357 är Majornas bibliotek alla tre åren). Placeringen bygger på namnet; där samma lokal finns i vallokalsfilen anges adressen därifrån. Totalt mottagna förtidsröster, rang bland Göteborgs lokaler (antal lokaler inom parentes) och andel av Göteborg:

| Lokal (lokalid) | Placering | 2010 (105 lokaler) | 2014 (72) | 2018 (81) |
|-----------------|-----------|--------------------|-----------|-----------|
| Majornas bibliotek (8357) | Majorna, Chapmans torg (adress saknas i källan, allmän kännedom) | 4585, rang 7, 3.31 %, 16 dagar | 6667, rang 5, 4.35 %, 16 dagar | 7470, rang 7, 4.64 %, 16 dagar |
| Dalheimers hus (12807) | Majorna, Slottskogsgatan 12 (vallokal 2010 och 2014) | 1221, rang 24, 0.88 %, 13 dagar | finns inte | finns inte |
| Gråbergets vård- och äldreboende (14133 år 2010, 14228 år 2014) | Majorna, Gråberget, Stortoppsgatan 2 (vallokal 2010 och 2018), institutionsröstning | 34, rang 53, 1 dag | 28, rang 45, 2 dagar | finns inte |
| Svaleboskogens äldreboende (6929) | Kungsladugård (adress saknas i källan, allmän kännedom), institutionsröstning | 51, rang 42, 1 dag | 23, rang 51, 1 dag | 23, rang 60, 1 dag |
| Linnéstadens bibliotek (8351) | nära, Linnéstaden (adress saknas i källan) | 5244, rang 4, 3.78 %, 15 dagar | 6940, rang 4, 4.53 %, 15 dagar | 9464, rang 4, 5.88 %, 16 dagar |
| Vegahusen (14137 år 2010, 14223 år 2014) | nära, Linnéplatsen, Vegagatan 55 (vallokal 2014 och 2018), institutionsröstning | 23, rang 71 | 111, rang 29 | finns inte |
| Annedals äldreboende (6869 år 2010, 15638 år 2018) | nära, Annedal, Carl Grimbergsgatan 11 (vallokal 2014), institutionsröstning | 36, rang 50 | finns inte | 34, rang 45 |
| Änggårdsbackens äldreboende (6940) | nära, Änggården, institutionsröstning | 66, rang 36 | 61, rang 33 | 30, rang 51 |
| Stiftelsen Neuberghska ålderdomshemmet (6926) | placering inte verifierad, institutionsröstning | 19, rang 77 | 30, rang 43 | 17, rang 67 |
| Majstångshemmet äldreboende (6913) | placering inte verifierad, institutionsröstning | 9, rang 95 | finns inte | finns inte |
| Göteborg totalt | | 138577 | 153111 | 160925 |

Inga lokaler i källan har namn som pekar på Stigberget, Masthugget eller Järntorget något av åren (skriptet söker efter sådana namnledtrådar och rapporterar träffar utanför urvalet, inga fanns). De största lokalerna i Göteborg för jämförelse: Nordstan 40288 (2010), 40415 (2014), 29002 (2018); Stadsbiblioteket 15409, 15667, 19024; Frölunda bibliotek/Frölunda Kulturhus 11107, 12801, 14543. Majornas bibliotek ligger alltså strax efter de tre stora och Linnéstadens bibliotek alla tre åren. Bland de ordinarie lokalerna (bibliotek och liknande med 10 dagar eller fler) är Majornas bibliotek nummer 7, 5 och 7.

Per dag (se `fortidsroster_per_dag_2010_2018.csv`): Göteborgs största dagar var fredagen två dagar före valet 2010 (15207) och torsdagen tre dagar före 2014 (17437) och 2018 (18926). På valdagen togs förtidsröster emot i 12 göteborgslokaler 2010 (3622 röster) men bara i Nordstan 2014 (3022) och 2018 (2346). Söndagen 2010-09-12 hade 62 lokaler med röster, det var dagen då de flesta äldreboenden hade sin röstmottagning 2010; 2014 och 2018 låg institutionsröstningen på vardagar.

## Vallokaler i Majornaområdet

Urval: 2010 distrikt med namnprefix "Majorna," (17 distrikt, kommunvalkrets Centrum och Väster), 2014 och 2018 koderna 148010(1-4)x (17 respektive 22 distrikt). Distriktsnumren anges utan prefixet 1480.

2010 (10 vallokaler): Kungsladugårdsskolan, Birger Jarlsgat. 1 (0911 Svalebo, 0912 Skytteskogen, 0913 Kungsladugård); Sannaskolan, Jordhyttegatan 5 (0914 Mariaplan, 0915 Silverkällan, 0921 Sandarne); Dalheimers hus, Slottskogsgatan 12 (0916 Klippan, 0931 Slottsskogsgatan m fl); Carl Johans församlingshem, Carl Johans Kyrkoplan 1 (0932 Majorna); Miljöförvaltningen, Karl Johansgatan 23-25 (0933 Hängmattan); Gråbergets äldreboende, Stortoppsgatan 2 (0934 Gråberget); Studium/Styrmansgatan, Styrmansgatan 21 (0935 Marieberg); SK Argo klubbhus, Ekedalsgatan 26 (0936 Godhem); Karl Johansskolan, Koopmansgatan 14-16 (0941 Söderlingska ängen, 0943 Djurgårdsgatan m fl, 0944 Gatenhielmska); Majornas samverkansförening, Klareborgsgatan 10 (0942 Karl Johans torg).

2014 (9 vallokaler): samma lokaler och samma distriktsnamn som 2010 med nya nummer 1011-1044, med en skillnad: Gråberget (1032) röstade i Dalheimers hus i stället för på Gråbergets äldreboende. Det stöder bilden i den gemensamma kontexten att 2011 års omnumrering inte ändrade distrikten i Majorna.

2018 (14 vallokaler räknat med stavningsvarianter): Sannaskolan (1011 Gröna Vallen, 1015 Mariaplan, 1021 Sandarne, 1022 Silverkällan); Hotell Kusten, Kustgatan 10 (1012 Klippan, nytt); Kungsladugårdsskolan (1013 Kungsladugård Västra, 1014 Kungsladugård Östra, 1016 Skytteskogen, 1017 Svalebo, 1038 Slottsskogsgatan m fl); Carl Johans församlingshem (1031 Chapmans Torg); SK Argo klubbhus (1032 Godhem); Gråbergets äldreboende, Stortoppsgatan 2-8 (1033 Gråberget Västra, 1034 Gråberget Östra); Majornas vuxengymnasium, Styrmansgatan 21 (1035 Hängmattan, 1036 Majorna, 1037 Marieberg); Karl Johansskolan, Koopmansgatan 14-16 och Amiralitetsgatan 22 (1041 Djurgårdsgatan m fl, 1044 Klareborgsgatan m fl, 1045 Söderlingska ängen); Sjömansgården, Amerikagatan 2 (1042 Gatenhielmska); Majornas samverkansförening (1043 Karl Johans torg). Dalheimers hus och Miljöförvaltningen används inte längre.

Distriktet Stigberget (1056 år 2014, 1057 år 2018) i Masthuggsserien röstade på Fjällskolan, Fjällgatan 40 (2014) och Sjömansgården, Amerikagatan 2 (2018), samma lokal som Gatenhielmska 2018. Vallokalen avgör inte var distriktet ligger, men noteras för geometridelmomentet.

## Kontroller

- Distriktskoderna i vallokalsfilerna jämfördes med `distrikt_<år>_<val>.csv` (andra delmoment): alla 282, 297 och 350 koder finns i alla tre valens distriktfiler respektive år, och det enda som finns i distriktfilerna men inte i vallokalsfilerna är uppsamlingsdistrikten 14800001-14800004 (2010, 2014) och 14800000 (2018). Antalet stämmer också med röstberättigadefilerna (282, 297, 350).
- Koordinatomräkningen kontrollerades mot 2018 års WGS84 för lokaler med samma namn och adress 2014 och 2018: 117 gemensamma lokaler, medianavvikelse 0 m. Karl Johansskolan: 2014 omräknat 57.694912, 11.929873 mot 2018 källa 57.694911, 11.929873. Största avvikelser 669 m (Bjurslättsskolan), 365 m (Morängatans äldreboende), 113 m (Svartedalens äldrecentrum), vilket är olika placering i källorna, inte projektionsfel.

## Avvikelser

- Koordinaterna är lagrade per distriktsrad, inte per vallokal, och samma lokal har olika koordinater på olika rader: 21 lokaler 2010, 30 år 2014 och 60 år 2018 har mer än en koordinat. De flesta skillnaderna är några meter, men 1 lokal 2010 och 2014 (Trulsegårdsskolan, 727 m) och 4 lokaler 2018 (Burgårdens gymnasium 1874 m, Trulsegårdsskolan 725 m, Bjurslättsskolan 669 m, Sannaskolan 590 m) spretar mer än 300 m. Kolumnen `antal_koordinater` i lokalfilerna visar detta.
- Orsaken syns i jämförelsen mellan åren: av 296 distriktskoder som finns både 2014 och 2018 har 183 exakt samma koordinat 2018 som 2014, och för 18 av dem har vallokalen bytts utan att koordinaten uppdaterats. I Majorna gäller det 14801011 (Gröna Vallen på Sannaskolan 2018 har Dalheimers hus koordinat från 2014 då koden var Klippan) och 14801035 (Hängmattan). Den som ska sätta ut vallokaler på karta bör använda en koordinat per lokal, till exempel den vanligaste bland lokalens rader, eller geokoda gatuadressen, i stället för raden för ett enskilt distrikt.
- Vallokalsfilen 2018 saknar vallokalernas gatuadress i normaliserad form; adress- och namnvarianter finns kvar som i källan.
- 2010 och 2014 har 29 gemensamma distriktskoder som avser olika distrikt (omnumreringen 2011); inga av dem har samma koordinat, så gemensam kod mellan 2010 och 2014 säger inget om samma distrikt.
- Förtidsröstfilen saknar adress och lokaltyp. Institutionsröstning (äldreboenden, sjukhus, häkte, anstalt) känns igen på namnet och på att röster togs emot en enda dag. 2010 har 105 göteborgslokaler mot 72 och 81 senare, skillnaden är främst antalet listade äldreboenden.
- Lokal-id byter ibland trots samma namn (Gråbergets 14133 till 14228, Vegahusen 14137 till 14223, Annedals 6869 till 15638), så en sammanslagning över år bör ske på lokalid i första hand och namn i andra hand.
- Rang i `rang_goteborg` räknas över alla göteborgslokaler, även de med en enda röstmottagningsdag.

## Öppna frågor

- Placeringen av Stiftelsen Neuberghska ålderdomshemmet (6926) och Majstångshemmet (6913) är inte verifierad; de finns med i Majornafilen med `omrade` = osäker och kan strykas eller flyttas om adressen blir känd.
- Majornas biblioteks och Svaleboskogens adresser kommer inte ur någon källfil här utan ur allmän kännedom; de påverkar inga tal.
- Motsvarande filer för 2002, 2006 och 2022 ingår inte i källmaterialet för detta delmoment (2022 års röster per distrikt i projektet innehåller förtidsröster per distrikt, inte per lokal, och har inte rörts).
- Antalet förtidsröster per lokal går inte att koppla till valdistrikt; förtidsröster räknas in i väljarens hemdistrikt oavsett var de lämnades. Filerna säger alltså var göteborgarna förtidsröstade, inte hur många i Majorna som förtidsröstade.
