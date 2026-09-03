# Röstberättigade per valdistrikt 2010, 2014 och 2018

Etikett: rostberattigade. Skript: `/Users/daniel/code/Temp/scripts/historik/rostberattigade_2010_2018.py` (körs med venv-python, behöver xlrd och openpyxl, kan köras om när som helst och skriver om alla filer nedan).

## Källfiler och hur de lästes

| År | Val | Fil | Format | Rader (hela riket) |
|----|-----|-----|--------|--------------------|
| 2010 | rd | `Historiska dokument/rostberattigade (6).xls` | xls, xlrd, blad "Sheet1" | 5668 |
| 2010 | rf | `Historiska dokument/rostberattigade (7).xls` | xls, xlrd, blad "Sheet1" | 5629 |
| 2010 | kf | `Historiska dokument/rostberattigade (8).xls` | xls, xlrd, blad "Sheet1" | 5668 |
| 2014 | rd | `Historiska dokument/rostberattigade (3).xls` | xls, xlrd, blad "Sheet1" | 5837 |
| 2014 | rf | `Historiska dokument/rostberattigade (4).xls` | xls, xlrd, blad "Sheet1" | 5796 |
| 2014 | kf | `Historiska dokument/rostberattigade (5).xls` | xls, xlrd, blad "Sheet1" | 5837 |
| 2018 | rd | `scratchpad/repaired/2018_rostberattigade_R.xlsx` (reparerad kopia av `rostberattigade (1).xls` enligt förarbetet) | xlsx, openpyxl, blad "Sheet1" | 6004 |
| 2018 | rf | `scratchpad/repaired/2018_rostberattigade_L.xlsx` | xlsx, openpyxl, blad "Sheet1" | 5963 |
| 2018 | kf | `scratchpad/repaired/2018_rostberattigade_K.xlsx` | xlsx, openpyxl, blad "Sheet1" | 6004 |

Alla nio filer har rubriker på rad 0 och en rad per valdistrikt, inga summarader. Rubrikerna är identiska mellan åren för respektive valtyp. Id-kolumnerna (före kategorierna) är:

- riksdag: `riksdagsvalkrets_id, riksdagsvalkrets_namn, kommun_id, kommun_namn, valdistrikt_id, valdistrikt_namn`
- landsting: `landstings_id, landstings_namn, landstingsvalkrets_id, landstingsvalkrets_namn, kommun_id, kommun_namn, valdistrikt_id, valdistrikt_namn`
- kommun: `län_id, län_namn, kommun_id, kommun_namn, kommunvalkrets_id, kommunvalkrets_namn, valdistrikt_id, valdistrikt_namn`

Därefter 20 kategorikolumner med namn på formen `Kön/Medborgarskap/Åldersgrupp`. Talen är flyttal i xls (74.0) och heltal i xlsx; skriptet kräver att varje tal är ett heltal och avbryter annars. Urvalet är `kommun_id == 1480`. `valdistrikt_id` görs om till text med åtta siffror (14800911.0 blir 14800911). Kodningsfrågor uppstår inte, formaten är binära och strängarna kommer ut som Unicode. Källorna ligger i kommunvalkretsordning, utfilerna är sorterade på kod.

Antal göteborgsdistrikt: 282 (2010), 297 (2014), 350 (2018), samma i alla tre valtyper respektive år. Alla koder är unika och åtta siffror.

## Kategorier

Exakt samma 20 kategorier finns i alla nio filerna (2 kön x 2 medborgarskap x 5 åldersgrupper), med ordagranna etiketter från källan:

- kön: `Män`, `Kvinnor`
- medborgarskap: `Svenska medborgare`, `Ej svenska medborgare`
- åldersgrupp: `18-29 förstagångsväljare`, `18-29 ej förstagångsväljare`, `30-49`, `50-64`, `65-`

Skillnaden mellan valtyperna ligger i innehållet, inte i kolumnerna: i riksdagsfilerna är alla åtta kolumner `Ej svenska medborgare` noll i hela filen (kontrollerat över alla rader i riket för 2010, 2014 och 2018), eftersom bara svenska medborgare har rösträtt till riksdagen. I landstings- och kommunfilerna finns röstberättigade utländska medborgare; för Göteborg 29976 (2010), 34410 (2014) och 38623 (2018). Landstings- och kommunfilerna ger identiska tal för varje göteborgsdistrikt (samma rösträtt i båda valen); skillnaden i rikssumman mellan dem (till exempel 392039 mot 392774 år 2010) beror på att landstingsfilen har färre rader och gäller inte Göteborg.

"Förstagångsväljare" är källans egen uppdelning av 18-29-gruppen och behålls som den är. Summan av de fem åldersgrupperna per kön och medborgarskap är alltså hela åldersspannet.

## Skrivna filer (alla i `/Users/daniel/code/Temp/data/historik/`, UTF-8, semikolon, koder som text)

Per år och val (nio uppsättningar):

- `rostberattigade_<år>_<val>.csv`, långt format `ar;val;kod;namn;kon;medborgarskap;aldersgrupp;antal`, 20 rader per distrikt (nollrader för utländska medborgare i riksdagsfilerna behålls). Rader: 5640 (2010), 5940 (2014), 7000 (2018).
- `rostberattigade_<år>_<val>_bred.csv`, en rad per distrikt med kolumnerna `ar;val` följt av källans id-kolumner med originalnamn, källans 20 kategorikolumner med originalnamn, och sist `totalt` (summan av de 20). Rader: 282, 297, 350.

Per år:

- `rostberattigade_majornaomradet_<år>.csv`, kolumner `ar;val;typ;kod;namn` + de 20 kategorikolumnerna + `totalt`. För varje val (rd, rf, kf): en rad per distrikt vars namn börjar med `Majorna,` (2010) respektive `Majorna-Linné,` (2014, 2018) med `typ=distrikt`, sedan en rad `typ=summa_urval` (kod tom) med summan av urvalet och en rad `typ=goteborg` (kod tom) med hela kommunen. Urvalet är avsiktligt brett och går att justera med kod och namn.

Kontrollfil:

- `rostberattigade_kontroll_2010_2018.csv`, `ar;val;kod;namn;summa_kategorier;rostberattigade_resultatfil;diff;kalla_fil`, 2787 rader (alla göteborgsdistrikt i alla nio uppsättningar).

## Kontroll av totalsumman per distrikt

Summan av de 20 kategorierna per distrikt jämfördes med röstberättigade i Valmyndighetens resultatfiler per valdistrikt, direkt ur originalfilerna:

| År | Val | Resultatfil (blad, rubrikrad, kolumn) | Göteborgsdistrikt i resultatfilen | Lika | Olika |
|----|-----|----------------------------------------|-----------------------------------|------|-------|
| 2010 | rd | `slutligt_valresultat_valdistrikt_R.xls` (rad 0, `Rostb`, kod = LAN+KOM+VALDIST) | 286 | 282 | 0 |
| 2010 | rf | `slutligt_valresultat_valdistrikt_L.xls` (rad 0, `Rostb`) | 282 | 282 | 0 |
| 2010 | kf | `slutligt_valresultat_valdistrikt_K_antal.xls` (rad 0, `Rostb`) | 282 | 282 | 0 |
| 2014 | rd | `2014_riksdagsval_per_valdistrikt.xls` (rad 2, `Rostb`, kod = LAN+KOM+VALDIST, KVK hoppas över) | 301 | 297 | 0 |
| 2014 | rf | `2014_landstingsval_per_valdistrikt.xls` (rad 2, `Rostb`) | 301 | 297 | 0 |
| 2014 | kf | `2014_kommunval_per_valdistrikt.xlsx` (rad 2, `Rostb`) | 301 | 297 | 0 |
| 2018 | rd | `2018_R_per_valdistrikt.xlsx` (blad "R antal", rad 0, `RÖSTBERÄTTIGADE`) | 351 | 350 | 0 |
| 2018 | rf | `2018_L_per_valdistrikt.xlsx` (blad "L antal", rad 0, `RÖSTBERÄTTIGADE`) | 351 | 350 | 0 |
| 2018 | kf | `2018_K_per_valdistrikt.xlsx` (blad "K antal", rad 0, `RÖSTBERÄTTIGADE`) | 351 | 350 | 0 |

Koden i resultatfilerna byggs som två siffror län, två siffror kommun och fyra siffror distrikt (14, 80, 911 blir 14800911). Varje distrikt i röstberättigadefilerna stämmer exakt med resultatfilen, i alla nio fallen. Det bekräftar också att de reparerade 2018-kopiorna är intakta för Göteborg.

De distrikt som bara finns i resultatfilerna är uppsamlingsdistrikt utan röstberättigade: 14800001-14800004 ("Onsdagsdistrikt" i 2010 års riksdagsfil, "Uppsamlingsdistrikt" i 2014 års tre filer) och 14800000 ("Uppsamlingsdistrikt" 2018). De saknas i röstberättigadefilerna och har 0 eller tomt i kolumnen för röstberättigade.

Göteborg totalt (summa av alla distrikt): riksdag 389821 (2010), 406851 (2014), 418425 (2018); landsting och kommun 405033 (2010), 425380 (2014), 441183 (2018).

Kontroll mot `distrikt_<år>_<val>.csv` i `data/historik/` (skrivna av andra delmoment, kolumn `rostberattigade`): vid första körningen fanns filerna inte, vid en omkörning senare samma kväll (2026-09-03) fanns alla nio och samtliga göteborgsdistrikt stämmer exakt (lika 282/282 för 2010, 297/297 för 2014, 350/350 för 2018 i alla tre valtyper, inga avvikelser, inga saknade). Skriptet letar automatiskt efter filerna (`las_historik`) och skriver ut lika/olika/saknas per fil vid varje körning.

## Majornaområdet

Urval på namnprefix ger:

- 2010, prefix `Majorna,`: 17 distrikt, koder 14800911-14800916, 14800921, 14800931-14800936, 14800941-14800944. Röstberättigade: 25001 (rd), 25353 (rf och kf).
- 2014, prefix `Majorna-Linné,`: 36 distrikt, koder 14801011-14801097. Röstberättigade: 52943 (rd), 53384 (rf och kf).
- 2018, prefix `Majorna-Linné,`: 45 distrikt, koder 14801011-14801098. Röstberättigade: 52620 (rd), 53591 (rf och kf).

Den gemensamma kontexten angav 19 distrikt för SDN Majorna 2010 och 47 för Majorna-Linné 2018; filerna innehåller 17 respektive 45, och det finns inga andra koder i serierna 148009xx (2010) eller 148010xx (2018) än de som listas. Siffrorna 19 och 47 bör kontrolleras mot den källa de kom ifrån.

Bedömning av vilka distrikt som motsvarar 2022 års 23 distrikt (14800526-14800548, Majorna, Stigberget, Kungsladugård, Sanna), utifrån namn och kodserier, inte geometri:

- 2010: alla 17 med prefix `Majorna,` (gamla SDN Majorna).
- 2014: de 17 i serierna 148010(1-4)x, det vill säga 14801011-14801016, 14801021, 14801031-14801036, 14801041-14801044, med samma namn som 2010. Serierna 105x-109x är Masthugget, Änggården, Haga, Annedal och Linnéstaden.
- 2018: de 22 i serierna 148010(1-4)x, det vill säga 14801011-14801017, 14801021-14801022, 14801031-14801038, 14801041-14801045 (Kungsladugård och Gråberget delade, Gröna Vallen, Chapmans Torg och Klareborgsgatan nya). Namnen matchar 2022 års lista med ett undantag: 2022 har 23 distrikt, bland dem Sannaplan, Kusttorget och Kommendörsgatan m fl som inte finns 2018.
- Öppen fråga: distriktet "Majorna-Linné, Stigberget" (14801056 år 2014, 14801057 år 2018) ligger i Masthuggsserien 105x, men 2022 års avgränsning nämner primärområdet Stigberget. Om det distriktet hör till området får avgöras med geometrin (annat delmoment). Inget 2022-distrikt heter Stigberget.

## Avvikelser och öppna frågor

- Kommunvalkretsar: 2010 och 2014 har fyra (148001 Göteborg, Hisingen; 148002 Göteborg, Öster; 148003 Göteborg, Centrum; 148004 Göteborg, Väster), 2018 en enda (148000 Göteborg). Riksdags- och landstingsvalkrets är "Göteborgs kommun" alla tre åren. Valkretsen finns i de breda filerna men inte i det långa formatet.
- Riksdagsfilerna saknar utlandssvenskar helt (uppsamlingsdistrikten har 0 röstberättigade i resultatfilerna), så riksdagens röstberättigade per distrikt avser folkbokförda i distriktet.
- 2018 års filer kunde inte läsas i original (trasiga för xlrd); talen kommer från de reparerade kopiorna i scratchpad, verifierade mot resultatfilerna enligt ovan. Om scratchpad rensas behöver reparationen göras om för att skriptet ska gå att köra.
- Åldersgrupperna är grova (fyra grupper plus förstagångsväljare) och lika alla tre åren, så de går att jämföra rakt av. 2022 års motsvarighet (`statistik-alder-och-kon-*-valdag-2022.xlsx` i projektmappen) är inte del av detta delmoment och har inte kontrollerats för kompatibilitet.
- Skriptet skriver bara om kommun 1480. Andra kommuner finns i källorna om grannjämförelser skulle behövas utanför Göteborg.
