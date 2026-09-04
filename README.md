# Så röstade Majorna

> Ny session: läs `docs/HANDOVER.md` först. Den beskriver läget, besluten, siffrorna som är facit och startpunkten.

Interaktiv valgrafik för Majposten: valresultatet per valdistrikt i klassiska Majorna (23 distrikt, riksdag, region och kommun). En statisk sida utan backend, byggd för att ta emot 2026 års siffror på valnatten utan kodändring.

Grafiken lever som en sida i Beehiivs sajtbyggare (majposten.se/val2026). Själva koden och datan hostas statiskt på en egen adress, och ett HTML-block på Beehiiv-sidan laddar dem. Ingen iframe.

## Mappen

```
valgrafik.js                  hela grafiken, renderar inuti <div class="mp-val" id="valgrafik">
valgrafik.css                 all CSS, scopad till .mp-val (Beehiivs krav för HTML-block)
index.html                    tunt skal som laddar de två filerna: lokal visning, bildläge, skärmdumpar
docs/inbaddningstest.html     simulerad värdsida med avsiktligt fientlig CSS, för att testa blocket lokalt
data/konfig.json / .js        KONFIG: ar, standardAr, valnatt, adress, inbaddad, skrivUrl, stickyTopp
data/valdata_2022.json        röster per distrikt och val, aggregat, mandat (kanonisk fil)
data/valdata_2022.js          samma data som JS, laddas av sidan (fungerar även via file://)
data/distrikt.geojson / .js   de 23 distriktspolygonerna i WGS84
data/bakgrund.json / .js      gator, spårväg, hållplatser, vatten, parker från OpenStreetMap (valfri)
data/valdata_2026.* + swing_2026.*   skrivs av uppdatera_2026.py på valnatten
scripts/bygg_data.py          xlsx + zip -> data/, med kontroller
scripts/kontrollera.py        stämmer av JSON mot xlsx, avbryter vid minsta diff
scripts/uppdatera_2026.py     rådata 2026 -> valdata_2026 + swing_2026 (och --repetera, --csv)
scripts/hamta_bakgrund.py     hämtar bakgrundslagret från Overpass
scripts/skapa_bilder.py       stillbilder (PNG) för nyhetsbrev och sociala medier ur sidans bildläge
bilder/                       genererade stillbilder
scripts/valmyndigheten.py     parser för Valmyndighetens filer, partimappning
scripts/mandat.py             jämkade uddatalsmetoden
scripts/geo.py, schema.py     geodata respektive datafilernas schema
tests/                        pytest, 27 tester
docs/superpowers/             designspec och plan
```

Källfiler som bygget läser (ligger i projektmappen, ändras inte):

- `majorna-valresultat-2022.xlsx` - kurerad sammanställning, flikarna RD, RF, KF, Sammanfattning, Metod & källor
- `valdistrikt-vastra-gotalands-lan.zip` - Valmyndighetens valgeografi 2022 (VD_14_20220910_Val_20220911.json)
- `Mandatfordelning-jamforelser-mellan-2018-och-2022.xlsx` - riksdagens verkliga mandat 2022
- `Roster-per-distrikt-...-riksdagsvalet/regionval/kommunval-2022.xlsx` - Valmyndighetens råfiler, används för kontroll och generalrepetition (kan tas bort, då hoppas det steget över)

## Komma igång

Python 3.12 rekommenderas (3.14 saknar färdiga paket för pyproj/shapely).

```bash
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -r requirements.txt
```

Utan uv: `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

Bygg datafilerna för 2022:

```bash
.venv/bin/python scripts/bygg_data.py
```

Bygget stannar vid minsta diff mellan JSON och xlsx (radsummor, kolumnsummor, totalrad, Sammanfattning, råfiler om de finns) och avslutar med `OK`. Kontrollen kan köras separat:

```bash
.venv/bin/python scripts/kontrollera.py data/valdata_2022.json majorna-valresultat-2022.xlsx
```

Bakgrundslagret (kräver nät, tar några sekunder, behöver bara göras om när kartan ska uppdateras):

```bash
.venv/bin/python scripts/hamta_bakgrund.py
```

Tester:

```bash
.venv/bin/python -m pytest -q
```

## Visa sidan lokalt

Dubbelklicka på `index.html`. Skalet laddar `valgrafik.css`, `valgrafik.js` och `.js`-filerna i `data/`, och fungerar via `file://` i Chrome, Safari och Firefox. `docs/inbaddningstest.html` visar grafiken inuti en simulerad värdsida med fientlig CSS, som Beehiiv-blocket. Vill du ha en riktig webbserver:

```bash
python3 -m http.server 8765
```

och öppna http://localhost:8765/.

## Publicera

Två delar: statisk hosting av filerna, och ett HTML-block på Beehiiv-sidan.

**1. Filerna** (`valgrafik.js`, `valgrafik.css`, `data/`, `bilder/`, gärna `index.html` och `docs/`) läggs på valfri statisk plats med HTTPS: GitHub Pages, Cloudflare Pages, Netlify eller Vercel. Ingen byggkedja. Adressen syns aldrig för läsaren, så en standardadress som `wildg14.github.io/val2026/` duger. Beehiiv-sidan är https, så hosten måste också vara det, annars blockerar webbläsaren filerna.

**2. Blocket** på Beehiiv-sidan (Website > Builder > Advanced blocks > HTML), med hostens adress i stället för platshållaren:

```html
<div class="mp-val" id="valgrafik" data-bas="https://wildg14.github.io/val2026/">
  <link rel="stylesheet" href="https://wildg14.github.io/val2026/valgrafik.css">
  <script src="https://wildg14.github.io/val2026/valgrafik.js"></script>
</div>
```

`data-bas` säger var `data/` ligger (samma mapp som skriptet). Kontrollera i Preview och sedan Live: kartan ska synas, alla tabbar fungera, och Beehiivs egen meny och sidfot ligga kvar runt omkring. Vill du dölja grafikens egen rubrik, ingress och sidfot (Beehiiv har redan sina) sätter du `"inbaddad": true` i `data/konfig.json` och skriver om `konfig.js` med `.venv/bin/python -c "from scripts import schema; schema.skriv_konfig('data', schema.las_konfig('data'))"`.

Beehiivs regler som bygget följer: koden börjar med en enda container-div, all CSS är scopad till `.mp-val`, inga regler på `*`, `body` eller `html`, inga `vh`-mått, ingen `position: fixed`. Testet `tests/test_inbaddning.py` vaktar det.

Total sidvikt är cirka 340 kB.

## Beehiiv

Majposten ligger på Beehiivs Scale-plan (enligt Beehiivs API 2026-09-03). Sajtbyggarens HTML-block kör JavaScript (verifierat 2026-09-03 på majposten.se/val2026, i Preview och Live), så grafiken ligger native på en custom page med Beehiivs meny, sidfot, prenumerationsblock och statistik. Djuplänkarna fungerar på den adressen: `majposten.se/val2026?distrikt=14800530`.

Inlägg och mejl kan inte köra script (HTML-snippeten i inlägg sparar varken `<script>` eller `<style>`, och mejl döljer iframe, video och script på alla planer). Där gäller stillbild plus länk till sidan: Image-block med alt-texten ur `.txt`-filen, länkad till sidan, och en Button-block under. Ge bild och knapp olika `utm_content`. Gmail klipper mejl med över 102 kB HTML.

Källor: Beehiivs supportartiklar "Using HTML in the Website Builder", "Using HTML in beehiiv posts", "Adding thumbnails, images, and GIFs to your posts" och "Using UTM parameter tracking with beehiiv" (alla uppdaterade sommaren 2026).

## Stillbilder för nyhetsbrevet

Mejlet kan inte visa interaktiv grafik. Skriptet renderar sektionen "Majorna mot Sverige" (skillnad mot riket, Västra Götaland respektive Göteborg i procentenheter) som PNG med Chrome headless:

```bash
.venv/bin/python scripts/skapa_bilder.py --etikett "Majposten · Inför valet"
```

Filerna hamnar i `bilder/`, per val i två format: 1200 x 630 (og:image, Facebook, Beehiiv-thumbnail) och 1080 x 1080 (Instagram och själva brevet, där värdena är läsbara i 360 px bredd). Filnamnen bär de logiska måtten, pixelmåtten är dubbla (2400 x 1260 och 2160 x 2160) för skärpa på mobil; `--skala 1` ger enkel upplösning. Bredvid varje PNG ligger en `.txt` med alt-texten, räknad ur datafilen med samma formel som sidan, att klistra in i Beehiiv och Instagram. Standardetiketten är "Majposten · Inför valet"; efter valdagen till exempel `--etikett "Majposten · Valet 2026"`. `--val rd` begränsar till riksdagsvalet, `--ar 2026` byter år.

Skriptet gör också en kartteaser per val (`majorna-karta-<val>-<år>-...png`): kartan i Största parti-läge med bara partibokstäver, legend, uppmaningen "Tryck på ditt kvarter på majposten.se/val2026" (adressen tas ur `KONFIG.adress`) och OpenStreetMap-attributionen som ODbL kräver. `--typ jamforelse` eller `--typ karta` begränsar till den ena.

Bildlägena går också att öppna direkt i webbläsaren: `index.html?bild=jamforelse&val=rd&format=kvadrat` och `index.html?bild=karta&val=rd&format=liggande`.

I Beehiiv: lägg in bilden med alt-texten och länka den till sidan (`#jamforelse` landar på grafiken, `#karta-sektion` på kartan, `?distrikt=...` på ett kvarter). Kvadraten passar i själva brevet (Beehiiv visar 600 px på desktop och cirka 360 px på mobil), liggande som og:image och för Facebook.

2026: jämförelsebilderna kräver aggregat för riket, Västra Götaland och Göteborg i `valdata_2026.json`. De finns när `uppdatera_2026.py` körts med Valmyndighetens filer, men inte när CSV-reservvägen använts. Kartan och distriktskortet på sidan fungerar däremot direkt på valnatten.

## Valnatten 13 september 2026

Allt nedan är testat mot 2022 års filer: `--repetera` reproducerar `valdata_2022.json` exakt ur råfilerna.

### Dagen innan

1. Kör testerna och generalrepetitionen:

```bash
.venv/bin/python -m pytest -q && .venv/bin/python scripts/uppdatera_2026.py --repetera
```

2. Gör en torrkörning med påhittade siffror för några distrikt, så att flödet sitter:

```bash
.venv/bin/python scripts/uppdatera_2026.py --skriv-mall torrkorning.csv
```

Fyll i några distrikt i CSV-filen (rader som börjar med `#` ignoreras, tomma rader hoppas över), kör `uppdatera_2026.py --csv torrkorning.csv --valnatt`, öppna `index.html` och titta. Ta sedan bort `data/valdata_2026.*` och `data/swing_2026.*` och sätt tillbaka `data/konfig.json` till `"ar": ["2022"], "standardAr": "2022", "valnatt": false` (skriv om `konfig.js` med `.venv/bin/python -c "from scripts import schema; schema.skriv_konfig('data', schema.las_konfig('data'))"`).

3. Konfigen ligger i `data/konfig.json` och `data/konfig.js` (inte i koden). På valnatten sätter `uppdatera_2026.py --valnatt` den automatiskt till

```json
{ "ar": ["2022", "2026"], "standardAr": "2026", "valnatt": true, ... }
```

Med `valnatt: true` visas banderollen "X av 23 distrikt räknade", oräknade distrikt gråtonas, Majorna-snittet räknas på räknade distrikt, och 2022 års staplar visas dämpade för distrikt som inte kommit in än. Årväljaren visas automatiskt när `ar` har fler än ett år.

### Under kvällen, varje gång nya distriktssiffror finns

1. Hämta Valmyndighetens fil per val från val.se (sidan för valresultat och rådata). Skriptet förväntar sig samma format som 2022 års "Röster per distrikt": ett blad `roster_RD`, `roster_RF` eller `roster_KF` med kolumnerna Valdistriktskod, Valdistriktnamn, Parti, Röster, Röstberättigade och en rad per parti, plus raderna "Summa giltiga röster" och "Valdeltagande". Ett annat format ger `FEL:` och skriptet avbryter, se reservvägen nedan.

2. Kör skriptet med de filer som finns (en, två eller tre):

```bash
.venv/bin/python scripts/uppdatera_2026.py --rd RD-FIL.xlsx --status preliminar --valnatt
```

Lägg till `--rf` och `--kf` när de filerna finns. `--valnatt` uppdaterar `data/konfig` (lägger till 2026, gör det till standardår, slår på valnattsläget) och behövs bara första gången men skadar inte. `--tid 2026-09-13T21:30:00` sätter tidsstämpeln i banderollen (annars klockslaget när skriptet kördes). Distrikt som saknas i filen markeras som oräknade. Utskriften slutar med antal räknade distrikt per val och antal varningar.

3. Läs varningarna. `VARNING:` betyder att något avviker från 2022 men att filerna skrevs: ett distrikt saknas, har bytt namn, Göteborg har ett annat antal valdistrikt än 411 (indelningen kan ha ändrats, kontrollera då att koderna 14800526 till 14800548 fortfarande är Majorna) eller ett okänt parti fick över 0,5 % i något distrikt (röster läggs i Övriga). `FEL:` betyder att inget skrevs.

4. Öppna `index.html` lokalt och kontrollera ett distrikt mot val.se.

5. Ladda upp `data/konfig.js`, `data/valdata_2026.js` och `data/swing_2026.js` till hosten (hela `data/` är enklast). Beehiiv-sidan behöver inte röras: blocket läser filerna från hosten.

### Reservväg: om filformatet är nytt

Skriv en mall, fyll i siffrorna för hand från val.se och kör med `--csv`:

```bash
.venv/bin/python scripts/uppdatera_2026.py --skriv-mall valnatt.csv
.venv/bin/python scripts/uppdatera_2026.py --csv valnatt.csv --status preliminar
```

Format: `val;kod;parti;roster` där val är rd, rf eller kf, kod är distriktskoden, parti är partikoden (V, S, MP, SD, M, C, L, KD, D, FI, K eller Övriga) och raderna `giltiga`, `rostande` och `rostberattigade` anger summorna per distrikt. Partiröster måste summera till giltiga, annars avbryter skriptet. `--csv` kan kombineras med `--rd` om riksdagsfilen fungerar men de andra inte.

23 distrikt gånger 9 rader för riksdagsvalet är cirka 200 tal att skriva in. Räkna med 20 minuter.

### Efter valet

När den slutliga rösträkningen är klar: kör om med alla tre filerna och `--status slutlig`. Vill du ha jämförelsesiffror för Göteborg och riket i panelen "Hela Majorna" räknas de ut automatiskt ur råfilerna (de saknas när bara CSV-vägen använts).

### Vanliga fel

- `FEL: ... hittar inget blad vars namn börjar med 'roster_'` - fel fil eller nytt format. Använd reservvägen.
- `FEL: ... partiröster N != giltiga M` - filen är inkonsekvent eller en partirad saknas. Skriptet skriver inget. Kontrollera distriktet på val.se.
- Sidan visar "Datafilerna kunde inte laddas" - `data/valdata_2026.js` saknas på hosten trots att konfigen listar 2026, eller `data-bas` i Beehiiv-blocket pekar fel.
- Halvcirkeln visar bara "Majornas riksdag" 2026 - väntat. Riksdagens verkliga fördelning är inte känd på valnatten. Vill du lägga in den efteråt: sätt `mandat.riksdag_verklig` i `data/valdata_2026.json` och skriv om `.js`-filen med `scripts/schema.py` (`skriv`).

## Djuplänkar

Sidan läser och skriver URL-parametrar, så ett kvarter kan länkas direkt från Beehiiv:

```
index.html?distrikt=14800530                 Mariaplan, riksdagsvalet
index.html?distrikt=14800530&val=kf          samma distrikt, kommunvalet
index.html?lage=styrka&parti=SD&val=rf       partistyrka för SD i regionvalet
index.html?ar=2026&distrikt=14800527         valet 2026 (när det finns i KONFIG.ar)
```

Sidan rullar till kartan när `distrikt` finns i länken. Distriktskoder:

| Kod | Distrikt |
|---|---|
| 14800526 | Svalebo |
| 14800527 | Skytteskogen |
| 14800528 | Kungsladugård Östra |
| 14800529 | Kungsladugård Västra |
| 14800530 | Mariaplan |
| 14800531 | Silverkällan |
| 14800532 | Sannaplan |
| 14800533 | Sandarne |
| 14800534 | Klippan |
| 14800535 | Gröna Vallen |
| 14800536 | Kusttorget |
| 14800537 | Chapmans Torg |
| 14800538 | Slottsskogsgat. m fl |
| 14800539 | Gråberget Västra |
| 14800540 | Gråberget Östra |
| 14800541 | Godhem |
| 14800542 | Marieberg |
| 14800543 | Klareborgsgatan m fl |
| 14800544 | Karl Johan |
| 14800545 | Söderlingska Ängen |
| 14800546 | Kommendörsgatan m fl |
| 14800547 | Hängmattan |
| 14800548 | Gatenhielmska |

## Dataschema

`data/valdata_<år>.json`:

```
meta        ar, status (slutlig | preliminar), uppdaterad, kalla, avgransning, val, partier, valnatt {raknade, totalt}
distrikt[]  kod, namn, raknat, rd {parti: röster}, rf, kf, giltiga {rd, rf, kf}, rostande {...}, rostberattigade {...}
aggregat    majorna {val: {roster, giltiga, rostande, rostberattigade}}   (räknade distrikt)
            goteborg {val: {andel, valdeltagande}}, riket {val: {andel, valdeltagande, namn}}  (rf: Västra Götaland)
mandat      riksdag_verklig, riksdag_majorna, metod
```

`data/swing_<år>.json`: förändring i procentenheter mot basåret, per distrikt och val samt för hela Majorna. Sidan visar den som små tal i panelen när filen finns.

Andelar räknas alltid i sidan som parti delat med giltiga röster. Inga tal är hårdkodade i `index.html`.

## Designval

Kartan är inline-SVG utan kartbibliotek: inga externa beroenden, fungerar offline, kapar inte sidscrollen på mobil. Orienteringen kommer från ett lokalt bakgrundslager (OpenStreetMap, hämtat vid byggtid). Saknas `data/bakgrund.js` ritas kartan mot enfärgad bakgrund. Färger kompletteras alltid med text: partibokstav och procent på kartan, tabellvy för alla distrikt, aria-etiketter på varje distrikt.

Utseendet följer Majpostens palett och typografi (Georgia och Arial, papper och slottsskogsgrön, inga skuggor eller gradienter).

Två layouter i en DOM, styrda av containerns bredd (CSS container queries), inte fönstrets: under 900 px en spalt som på mobil, från 900 px kartan till vänster med resultatkortet fastnaglat till höger, halvcirkeln bredvid mandattabellen och de två jämförelsegrafikerna sida vid sida. Brödtexten håller smal spalt även på desktop. Sektionen som blocket ligger i på Beehiiv behöver vara minst cirka 1 000 px bred för att desktopläget ska slå till. Ingen egen prenumerationsknapp: Beehiivs eget prenumerationsblock läggs på sidan.

Två oberoende brytpunkter: 600 px containerbredd styr kartans detaljnivå (fler hållplatser och platsnamn, procent i etiketterna), 900 px styr tvåkolumnslayouten. Mellan 600 och 900 px visas alltså den detaljerade kartan i en spalt, vilket är avsett.

Resultatkortet på desktop är fastnaglat med `position: sticky` och avståndet `stickyTopp` (px) i `data/konfig.json`, standard 16. Är Beehiivs sidhuvud klibbigt: sätt värdet till sidhuvudets höjd plus marginal. Sticky faller tyst tillbaka till vanlig placering om värdsidan lägger `overflow` eller `transform` på ett element runt blocket, vilket vi inte kan skydda oss mot i förväg; kontrollera på den publicerade sidan.

## Källor och licenser

Valdata: Valmyndigheten, slutlig rösträkning per valdistrikt 2022 (val.se, rådata). Valgeografi: Valmyndigheten. Kartunderlag: © OpenStreetMaps bidragsgivare, ODbL. Avgränsningen av klassiska Majorna beskrivs i fliken "Metod & källor" i `majorna-valresultat-2022.xlsx`.
