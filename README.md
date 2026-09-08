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
docs/beehiivtest.html         simulerad Beehiiv-sida (klibbig meny 89 px, iframe srcdoc), för djuplänkar och rullning
docs/valnatt-korschema.md     körschemat för valkvällen, punkt för punkt
data/konfig.json / .js        KONFIG: ar, standardAr, valnatt, adress, inbaddad, skrivUrl, stickyTopp,
                              valdag, toppsvar, historik, samarbete, hjalp
data/valdata_2022.json        röster per distrikt och val, aggregat, mandat (kanonisk fil)
data/valdata_2022.js          samma data som JS, laddas av sidan (fungerar även via file://)
data/distrikt_2022.geojson    de 23 distriktspolygonerna i WGS84, en fil per år i konfigens ar
data/distrikt_2022.js         samma geometri som JS
data/distrikt.js              övergångskopia av distrikt_2022.js (nyckeln "distrikt") åt läsare med
                              cachad gammal valgrafik.js, tas bort efter valet
data/distrikt_2026.*          2026 års gränser: samma yta, elva distrikt skiljer sig geometriskt men
                              bara nio är flaggade av Valmyndigheten som omritade (jämförbarhet); två
                              av de elva bytte bara ett litet kvarter och räknas ändå som jämförbara
data/bakgrund.json / .js      gator, spårväg, hållplatser, vatten, parker från OpenStreetMap (valfri)
data/valdata_2026.*           skrivs av uppdatera_2026.py på valnatten
data/swing_2026.*             förändring mot 2022 per distrikt och för hela Majorna, skrivs samtidigt
data/valnatt/                 Valmyndighetens hämtade och uppackade filer, en mapp per körning (gitignorerad)
data/historik.json / .js      områdesserien 2006 till 2022 för sektionen "Majorna sedan 2006", byggd av bygg_historik.py
data/swing_2022.json / .js    förändring 2022 mot 2018 (bas 2018 ur databasens tidsserie, samma_yta=True)
data/distrikt_2006.*          förenklad geometri (17 distrikt), bara för sektionens konturkartor
data/valdata_<år>.*           och distrikt_<år>.* för 2006, 2010, 2014 och 2018: byggda av bygg_historik.py.
                              2010, 2014 och 2018 står i konfigens ar och laddas när läsaren väljer året
                              (2022 skrivs aldrig över, 2006 hör inte hemma i ar, se Historiken)
scripts/bygg_data.py          xlsx + zip -> data/, med kontroller
scripts/bygg_geo.py           Valmyndighetens valgeografi -> data/distrikt_<år>.geojson och .js
scripts/bygg_historik.py      data/historik/majorna_historik.sqlite -> historik, swing_2022, distrikt_<år>
                              och valdata_<år> för historikåren, se Historiken
scripts/kontrollera.py        stämmer av JSON mot xlsx, avbryter vid minsta diff
scripts/hamta_2026.py         hämtar, md5-kontrollerar och signaturverifierar 2026 års resultatfiler
scripts/valnatt.py            läser Valmyndighetens JSON 2026: distrikt, aggregat, riksdagens mandat
scripts/uppdatera_2026.py     rådata 2026 -> valdata_2026 + swing_2026 (--hamta, --repetera, --csv)
scripts/hamta_bakgrund.py     hämtar bakgrundslagret från Overpass
scripts/skapa_bilder.py       stillbilder (PNG) för nyhetsbrev och sociala medier ur sidans bildläge
bilder/                       genererade stillbilder
scripts/valmyndigheten.py     parser för Valmyndighetens xlsx-filer, partimappning
scripts/mandat.py             jämkade uddatalsmetoden
scripts/geo.py, schema.py     geodata respektive datafilernas schema
verktyg/                      forbered_tvaar.py (bygger testsidor) och Puppeteer-kontrollerna (tvaar-check.js,
                              historik-check.js, bredd-check.js med flera), se verktyg/README.md
tests/                        pytest, 358 tester
docs/superpowers/             designspec och plan
```

Källfiler som bygget läser (ligger i projektmappen, ändras inte):

- `majorna-valresultat-2022.xlsx` - kurerad sammanställning, flikarna RD, RF, KF, Sammanfattning, Metod & källor
- `valdistrikt-vastra-gotalands-lan.zip` - Valmyndighetens valgeografi 2022 (VD_14_20220910_Val_20220911.json)
- `Mandatfordelning-jamforelser-mellan-2018-och-2022.xlsx` - riksdagens verkliga mandat 2022
- `Roster-per-distrikt-...-riksdagsvalet/regionval/kommunval-2022.xlsx` - Valmyndighetens råfiler, används för kontroll och generalrepetition (kan tas bort, då hoppas det steget över)
- `Historiska dokument/dl_webb/2026/valdistrikt-vastra-gotaland-lan-2026.zip` - Valmyndighetens valgeografi 2026 (gitignorerad, hämtas om från val.se) och `valdistrikt-jamforelser-mellan-2022-och-2026.xlsx` med jämförbarheten per distrikt
- `val-sign-crt.pem` och `val-sign-pub.pem` - Valmyndighetens certifikat och publika nyckel för signaturkontrollen. Gitignorerade: `hamta_2026.py` hämtar dem själv vid första körningen, och signaturtestet hoppas över tyst i en klon som saknar dem

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
python3 -m http.server 8765 --bind 127.0.0.1
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

`data-bas` säger var `data/` ligger (samma mapp som skriptet). Kontrollera i Preview och sedan Live: kartan ska synas, alla tabbar fungera, och Beehiivs egen meny och sidfot ligga kvar runt omkring. Vill du dölja grafikens egen etikett, rubrik och sidfot (Beehiiv har redan sina) sätter du `"inbaddad": true` i `data/konfig.json` och skriver om `konfig.js` med `.venv/bin/python -c "from scripts import schema; schema.skriv_konfig('data', schema.las_konfig('data'))"`.

Beehiivs regler som bygget följer: koden börjar med en enda container-div, all CSS är scopad till `.mp-val`, inga regler på `*`, `body` eller `html`, inga `vh`-mått, ingen `position: fixed`. Testet `tests/test_inbaddning.py` vaktar det.

Sidvikten vid start är 452 kB, med de filer sidan faktiskt hämtar:

```bash
du -ch valgrafik.js valgrafik.css data/konfig.js data/valdata_2022.js data/distrikt_2022.js \
       data/swing_2022.js data/bakgrund.js data/historik.js data/distrikt_2006.js
```

Bakgrundslagret är 228 kB av det, historiksektionens `historik.js` 25 kB och `distrikt_2006.js` 9,9 kB, och `swing_2022.js` 6,8 kB (den går till de små talen vid staplarna i kortet, inte till sektionen). Konfigen listar fyra år, men bara standardåret laddas vid start: hade alla fyra laddats hade samma `du`-körning gett 576 kB, alltså 124 kB mer. Varje ytterligare år kostar cirka 40 kB (valdata plus polygoner) och hämtas först när läsaren väljer det i årväljaren, se avsnittet Årväljaren och den lata laddningen. På valnatten tillkommer `distrikt_2026.js`, `valdata_2026.js` och `swing_2026.js`, tillsammans 52 kB, och jämförelseåret laddas då också vid start.

## Beehiiv

Majposten ligger på Beehiivs Scale-plan (enligt Beehiivs API 2026-09-03). Sajtbyggarens HTML-block kör JavaScript (verifierat 2026-09-03 på majposten.se/val2026, i Preview och Live), så grafiken ligger native på en custom page med Beehiivs meny, sidfot, prenumerationsblock och statistik. Djuplänkarna fungerar på den adressen: `majposten.se/val2026?distrikt=14800530`.

Inlägg och mejl kan inte köra script (HTML-snippeten i inlägg sparar varken `<script>` eller `<style>`, och mejl döljer iframe, video och script på alla planer). Där gäller stillbild plus länk till sidan: Image-block med alt-texten ur `.txt`-filen, länkad till sidan, och en Button-block under. Ge bild och knapp olika `utm_content`. Gmail klipper mejl med över 102 kB HTML.

Källor: Beehiivs supportartiklar "Using HTML in the Website Builder", "Using HTML in beehiiv posts", "Adding thumbnails, images, and GIFs to your posts" och "Using UTM parameter tracking with beehiiv" (alla uppdaterade sommaren 2026).

Mätt på den publicerade sidan (majposten.se/val2026, 2026-09-05): Beehiiv lägger HTML-blocket i en `<iframe srcdoc>` med samma ursprung som sidan, bredd 100 % och höjd som följer innehållet (blocket växer och krymper fritt, till exempel när tabellen fälls ut). Iframens egen adress är `about:srcdoc` utan query, så `?distrikt=...` når aldrig skriptet direkt: djuplänkarna läser och skriver därför mot `window.parent.location` när föräldern går att nå (samma ursprung, `parent.history.replaceState` fungerar). `position: sticky` är verkningslöst inuti iframen eftersom inget rullar där; resultatkortet på desktop följer alltså inte med vid rullning, vilket vi fått acceptera. Beehiivs egen sidmeny är klibbig och 89 px hög, så `stickyTopp` i `data/konfig.json` står på 105 (89 plus 16 px marginal) och används som `scroll-margin-top` när sidan rullar till kartan, kortet eller tabellen - annars hamnar överkanten under menyn. Sidan har ingen egen rubrik utanför blocket, så `inbaddad` behöver inte slås på. Uppsättningen testas lokalt mot `docs/beehiivtest.html` (klibbig meny plus `iframe srcdoc`) med `verktyg/beehiiv-check.js`.

## Samarbete och rösthjälp

Två redaktionella block som styrs helt från `data/konfig.json`: en samarbetsrad i sidhuvudet och upp till två rutor direkt under huvudet (valvakan och rösthjälpen). Båda är avstängda som de ligger, och texterna är platshållare som redaktören skriver om. Rader märkta `[KOLLA]` är okontrollerade.

```json
"samarbete": { "visa": false, "namn": "Majornas Bryggeri", "text": "I samarbete med", "lank": "", "logga": "",
               "valvaka": { "visa": false, "rubrik": "Valvaka på Majornas Bryggeri",
                            "text": "[KOLLA] Tid, plats och vad som händer.", "lank": "" } },
"hjalp":     { "visa": false, "rubrik": "Behöver du hjälp att rösta?",
               "text": "hjalpmigrosta.se förklarar hur valet går till, på flera språk.",
               "lank": "https://hjalpmigrosta.se", "lanktext": "Till hjalpmigrosta.se" }
```

- `samarbete.visa` slår på raden "I samarbete med Majornas Bryggeri" i sidhuvudet, under toppsvaret. Raden visas inte i bildläget och inte när `inbaddad` är på, eftersom rubriken då är dold.
- `samarbete.logga` är en adress till en bild, antingen absolut eller relativ till `data-bas` (lägg filen i `bilder/`, till exempel `bilder/majornas-bryggeri.png`). Loggan visas i högst 44 px höjd med namnet som alt-text. Tom logga ger bara text.
- `samarbete.valvaka.visa` slår på valvakerutan, och kräver att `samarbete.visa` också är på. `hjalp.visa` slår på rösthjälpsrutan för sig. Rutorna ligger sida vid sida från 900 px containerbredd, under varandra på mobil, och visas även när `inbaddad` är på.
- Alla `lank` är tomma platshållare tills adresserna är klara. Med tom länk renderas texten som ren text, aldrig som en tom länk.

Slå på ett block genom att sätta `visa` till `true` i `data/konfig.json` och skriva om `konfig.js`, så att de två filerna aldrig glider isär:

```bash
.venv/bin/python -c "from scripts import schema; schema.skriv_konfig('data', schema.las_konfig('data'))"
```

Nycklarnas standardvärden ligger i `scripts/schema.KONFIG_STANDARD` och bevaras av `uppdatera_2026.py --valnatt`.

Tre nycklar till styr sidhuvudet och historiksektionen:

- `valdag` (`"2026-09-13"`) används i statusraden före valdagen: "Slutligt resultat 2022. Valet 2026 är söndag 13 september."
- `toppsvar.mening` är en redaktionell mening under toppsvaret, tom i `schema.KONFIG_STANDARD` och satt till "Från klockan 20 på valnatten kommer siffrorna löpande här." i `data/konfig.json`. Håll den till en rad, cirka 60 tecken: sidan reserverar höjd för en rad extra (`har-mening`), en längre mening kan ge några pixlars hopp på små telefoner.
- `historik` (`visa` och en mening per val) hör till sektionen "Majorna sedan 2006".

## Årväljaren och den lata laddningen

Sidan kan visa flera valår. Vilka står i `data/konfig.json`:

```json
"ar": ["2010", "2014", "2018", "2022"],
"standardAr": "2022"
```

`ar` är åren i väljaren, `standardAr` det år sidan öppnar på. Väljaren är en `<select>` (`#arval-select`) i sidhuvudet, med åren nyast först och etiketterna "Valet 2022", "Valet 2018" och så vidare. Raden är dold när `ar` har färre än två år, och den tar plats så snart konfigen är läst (44 px) så att sidhuvudet inte hoppar.

**Bara ett år laddas vid start.** `start()` hämtar `standardAr`, plus året i URL-parametern `ar` om det är ett annat, plus - när `"valnatt": true` - det största året under standardåret (jämförelseåret, som kortet behöver för ett oräknat distrikt). Övriga år i `ar` hämtas först när läsaren väljer dem, en gång per år. Det är därför fyra år i konfigen inte gör starten tyngre: 452 kB i stället för 576 kB, se Publicera.

Under laddningen står den nuvarande vyn kvar, väljaren är `disabled` med `aria-busy`, och fokus läggs tillbaka på väljaren när året är inne. Går året inte att ladda står vyn kvar, väljaren faller tillbaka på det år som visas, och raden `#arval-fel` säger "Valet 2014 kunde inte laddas."; den försvinner vid nästa lyckade byte. Ett år som saknar filer tas alltså inte tyst ur väljaren - det går att försöka igen.

Att lägga till ett år: bygg `data/valdata_<år>.*` och `data/distrikt_<år>.*` (se Historiken), lägg året i `ar` och skriv om `konfig.js`:

```bash
.venv/bin/python -c "from scripts import schema; schema.skriv_konfig('data', schema.las_konfig('data'))"
```

2006 hör inte hemma i `ar`: `data/distrikt_2006.*` är förenklad geometri för historiksektionens konturkartor.

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

## Historiken

Sektionen "Majorna sedan 2006" ligger näst sist på sidan, ovanför "Om siffrorna" och sidfoten, och visar Majornas valresultat över tid, oberoende av vilket år kartan ovanför står på - utom konturkartorna, som följer kartans år. Den har tre delar:

- En rubrikmening per val (`#hist-mening`), antingen ur `KONFIG.historik.mening` (redaktörens egen text) eller räknad ur serien (Vänsterpartiets andel första och sista år).
- Valdeltagandebilden: Majorna mot Göteborg, och på desktop även riket streckat i riksdagsvalet. Y-axel 70 till 90 procent (vidgas i femprocentssteg om ett år ligger utanför). Över bilden står en etikett som säger vad den visar - "Valdeltagande i riksdagsvalet", utan årtal och tal, eftersom skalan 70 till 90 annars läses som partiernas andelar. Talen står i bildens `aria-label` tillsammans med serierna år för år. Noten under bilden säger var skalan börjar, och lägger till en mening om en jämförelselinje slutar tidigare än Majornas.
- Konturkartorna: 2006 (ur `data/distrikt_2006.js`, förenklad geometri, 17 distrikt) mot det visade årets geometri, som två små `figure`-element, `aria-hidden` eftersom de inte går att interagera med. Noten räknas fram ur kartorna: har det visade året fler distrikt än 2006 lyder första meningen "Samma yta, fler distrikt. Ett kvarter 2006 är ofta två i dag.", annars "Samma yta, lika många distrikt, men gränserna är omritade." Distrikt per år: 2006 17, 2010 17, 2014 17, 2018 22, 2022 23, 2026 23. Sedan följer att valhemligheten gäller per distrikt, inte per person.

Partilinjediagrammet som låg först i sektionen (bild A, med läslinje och talrad) togs bort 2026-09-07 efter Daniels genomgång: det tog mer plats än det svarade på.

Sektionen följer kartans val (riksdag, region eller kommun) men inte årväljaren: sista punkten i valdeltagandebilden kommer alltid från det senast laddade året och ritas bara när alla Majornas distrikt är räknade i det valet - för jämförelseområdena krävs dessutom att området självt är färdigräknat. Konturkartorna följer däremot årväljaren, eftersom de svarar på en fråga om det år kartan visar. Före valdagen står 2026 som en tom ring på skalans nedersta nivå med texten "räknas på valnatten"; är alla distrikt räknade men resultatet preliminärt blir ringen öppen med en streckad sista sträcka och "(preliminärt)" i beskrivningen; är resultatet slutligt blir punkten fylld och rubrikmeningen räknas på 2026. På valnatten (`KONFIG.valnatt` sant) lyder texten vid ringen "räknas just nu" i stället för "räknas på valnatten", i bilden och i dess aria-label.

Sektionen döljs när `data/historik.js` saknas eller `KONFIG.historik.visa` är `false`, vilket stänger av laddningen av `historik.js` och `distrikt_2006.js`. Båda laddas annars vid start. `swing_<år>.js` hör inte till sektionen utan till de små talen vid staplarna i resultatkortet, och laddas tillsammans med sitt år. En fil som inte går att ladda fångas av sidan: saknas `historik.js` döljs sektionen, saknas `distrikt_2006.js` utgår bara konturkartorna, och saknas `swing_<år>.js` uteblir bara de små talen för det året. (Verktygens undantag för en 404 som en valfri fil gäller bara swingfilerna.)

**Bygga om filerna.** Databasen (`scripts/historik/bygg_databas.py`, se `docs/historik/README.md`) byggs om först vid behov, sedan:

```bash
.venv/bin/python scripts/bygg_historik.py allt
```

Underkommandona `historik`, `swing2022`, `geo2006` och `ar [år ...]` går att köra var för sig. `kontrollera.py --historik data/historik.json` stämmer av områdesseriens rad för valdatas år mot `valdata_<år>.json`, för alla tre valen.

**Konfignyckeln `historik`** i `data/konfig.json`: `visa` (true/false) och `mening` (en text per val, `rd`/`rf`/`kf`, tom som standard så att sidan räknar ut meningen själv).

**2002 är utelämnat.** Valdistrikten ritades om helt inför valet 2006, så 2002 går inte att räkna om till dagens Majorna; serien börjar därför 2006.

**Historikår i kartan.** 2010, 2014 och 2018 ligger i `KONFIG.ar` sedan 2026-09-07 och fungerar som vilket annat år som helst i kartan, kortet, tabellen och Röstdelningen (17, 17 respektive 22 distrikt). De laddas när läsaren väljer dem, se Årväljaren och den lata laddningen. **2006 får däremot inte läggas där**: `data/distrikt_2006.*` är en förenklad geometri (17 distrikt) byggd bara för sektionens små konturkartor, inte den fullständiga kartans upplösning.

**Testsidor.** `verktyg/forbered_tvaar.py --partiell N` markerar de N första distrikten som räknade i alla tre valen (resten oräknade) och räknar om testsidans swingfil; `verktyg/historik-check.js --sida= --prel= --partiell= --slutlig=` kontrollerar sektionen i fyra lägen (före valdagen, allt räknat preliminärt, delvis räknat, slutligt), se `verktyg/README.md`.

## Valnatten 13 september 2026

Valmyndigheten publicerar resultatet som zip-filer med JSON på `https://resultat.val.se/resultatfiler/val2026/` (förteckningen ligger i `index.md5`, katalogen `p/` är preliminär räkning och `s/` slutlig). Formatet är kontrollerat mot simuleringarna i `genrep2026/` och beskrivet i `docs/superpowers/plans/2026-09-05-valnatt-2026.md`. Hela flödet, punkt för punkt, står i `docs/valnatt-korschema.md`. Xlsx-vägen från 2022 och CSV-vägen finns kvar som reservvägar.

### Dagen innan

1. Tester och generalrepetition:

```bash
.venv/bin/python -m pytest -q && .venv/bin/python scripts/uppdatera_2026.py --repetera
```

`--repetera` reproducerar `data/valdata_2022.json` exakt ur 2022 års råfiler och är facit på att parsern inte glidit.

2. Valmyndighetens certifikat, om det inte redan ligger i projektroten:

```bash
curl -sSo val-sign-crt.pem https://resultat.val.se/keys/val-sign-crt.pem
openssl x509 -in val-sign-crt.pem -pubkey -noout > val-sign-pub.pem
```

`hamta_2026.py` hämtar det annars själv vid första körningen. Båda pem-filerna är gitignorerade, och signaturtestet i sviten hoppas över tyst i en klon som saknar dem.

3. Torrkörning mot simuleringarna, till en tillfällig mapp och aldrig till `data/`:

```bash
.venv/bin/python scripts/uppdatera_2026.py --hamta --genrep --ut /tmp/torr --status preliminar
```

Väntat (kört 2026-09-07): `md5 ok, signatur ok` för de tre zip-filerna, `Räknade distrikt: Riksdag 23/23, Region 23/23, Kommun 23/23`, `Jämförbara mot 2022: 14 av 23`, en namnvarning för Sandarna och en `VARNING: TESTDATA`, inga FEL. Filerna i `/tmp/torr` får `meta.test: true`. Körs kommandot en gång till svarar skriptet `Inget nytt att läsa in.` och avslutar med kod 3. Testdata till repots `data/` stoppas av en spärr.

4. Den skarpa adressen svarar 404 fram till valkvällen:

```bash
.venv/bin/python scripts/hamta_2026.py --ut /tmp/torr2
```

ska ge `FEL: https://resultat.val.se/resultatfiler/val2026/index.md5 svarar 404: resultatfilerna publiceras först på valkvällen` och kod 1.

5. Testsidan med båda åren, byggd av torrkörningens data:

```bash
.venv/bin/python verktyg/forbered_tvaar.py --valnatt-data /tmp/torr --valnatt --ut tmp/tvaar
node verktyg/tvaar-check.js
```

ska sluta med `TVÅÅRSKONTROLL OK`. Testsidorna under `tmp/` innehåller kopior av `valgrafik.js` och `valgrafik.css` och måste byggas om efter varje ändring i källfilerna.

### Under kvällen

Första körningen, när `index.md5` finns:

```bash
.venv/bin/python scripts/uppdatera_2026.py --hamta --status preliminar --valnatt
```

`--hamta` laddar ned riksdagen (hela landet), regionvalet (Västra Götaland) och kommunvalet (Göteborg), kontrollerar md5 mot index och JSON-filernas signaturer mot certifikatet, packar upp till `data/valnatt/<tidsstämpel>/` och läser JSON därifrån. `--valnatt` sätter `data/konfig` till `"ar": ["2022", "2026"]`, `"standardAr": "2026"`, `"valnatt": true` och behövs bara första gången. Sedan var tionde minut:

```bash
.venv/bin/python scripts/uppdatera_2026.py --hamta --status preliminar && git add data && git commit -qm "Valnatten: uppdaterat $(date +%H:%M)" && git push origin main
```

GitHub Pages bygger från grenen med en mjuk gräns på tio bygg per timme; pushar man tätare än så hinner sidan inte hänga med. Blir ett bygge strypt landar pushen ändå i git, men sidan uppdateras inte förrän nästa bygge går igenom - kontrollera då sidan innan nästa push.

Har de tre filerna samma md5 som förra körningen skriver skriptet `Inget nytt att läsa in.` och avslutar med kod 3 utan att röra något; kedjan stannar där och ingenting committas. Alla filer skrivs atomiskt, så sidan kan aldrig läsa en halvskriven fil.

Vallokalerna stänger 20.00 och det dröjer innan Majorna syns. En körning utan räknade Majornadistrikt är inte ett fel: filerna skrivs med 0 av 23 räknade, konfigen slås över i valnattsläge och sidan säger "inget distrikt räknat än" under en statusrad som räknar upp. Det är det normala läget den första timmen.

Skriptet vägrar däremot skriva när den nya filen har färre räknade distrikt i något val än den som redan ligger, eller när den är testdata över skarp data. Efter ett sådant stopp är kommandot för att gå vidare

```bash
.venv/bin/python scripts/uppdatera_2026.py --valnatt-mapp data/valnatt/senaste --tvinga --status preliminar
```

eftersom `--hamta` med samma filer bara ger kod 3. `--tvinga` ersätter hela filen: val som saknas i den nya blir tomma, ingenting slås ihop med den gamla. Flaggan låser dessutom upp tre spärrar samtidigt (färre räknade distrikt, testdata över skarp data, testdata till repots `data/`), så ett `--tvinga` direkt efter en `--genrep`-körning kan skriva testmärkt data till `data/` utan att stoppas.

Läs varningarna. `VARNING:` betyder att filerna skrevs men att något avviker: Göteborg har ett annat antal distrikt än 397, ett distrikt saknas i filen (markeras som oräknat), ett distrikt har bytt namn sedan 2022, ett okänt parti fick över 0,5 procent i något distrikt (röster läggs i Övriga), filhuvudets antal räknade stämmer inte med Majornas, ett jämförelseaggregat kunde inte läsas, eller två filer bedömer samma distrikt olika i jämförbarhet mot 2022 ("bedöms jämförbart men en tidigare fil sa tvärtom, sätts till ej jämförbart"). `FEL:` betyder att ingenting skrevs. Kontrollera ett distrikt mot val.se första gången, och öppna majposten.se/val2026 efter första pushen.

**Jämförbarhet mot 2022** kommer ur fältet `statusJamforelse` i Valmyndighetens filer, kontrollerat mot `valdistrikt-jamforelser-mellan-2022-och-2026.xlsx`: 14 av 23 distrikt kan jämföras, 9 är omritade. Säger någon av källorna "ej jämförbart" gäller det. Kortets små tal vid staplarna visas bara för de 14; de 9 får i stället meningen om att gränserna ritats om. Hela Majornas förändring gäller ändå, eftersom de 23 distrikten täcker samma yta båda åren.

**Partier som inte förekommer i Valmyndighetens fil saknas i datan.** De skrivs varken som nollor eller markeras. I den preliminära filen betyder det att partiet inte är rapportparti och att rösterna ligger i Övriga; i den slutliga att partiet inte fick någon röst i distriktet. Ett sådant parti visas inte på sidan och får ingen förändringssiffra: hellre ingen siffra än en påhittad nolla. I genrepets filer gäller det K i kommunvalet och FI i regionvalet.

**Riksdagens verkliga mandat** läses ur mandatfördelningsfilen redan på valnatten, så halvcirkeln "Om Majorna bestämde" kan jämföra Majornas fördelning med riksdagens direkt. Fördelningen är preliminär, ändras under kvällen och efter uppsamlingsräkningen på onsdagen, och halvcirkeln skriver ut förbehållet: "Preliminärt resultat, riket: X av Y distrikt räknade." medan riket är delvis räknat, annars bara "Preliminärt resultat." Orden gäller både mandat och röstandelar, så förbehållet står oförändrat i båda lägena av enhetsväxeln - det är därför det inte längre säger "mandatfördelning". Ett delvis räknat riket finns inte i genrepsfilerna, som alltid är färdigräknade, så testsidan byggs med `verktyg/forbered_tvaar.py --riket-delvis N` och kontrolleras med `node verktyg/tvaar-check.js --riketdelvis=`.

**Valdeltagandet i aggregaten** räknas mot röstberättigade i räknade distrikt, inte mot hela områdets väljarkår; annars visar riket 12 procent klockan 20.30. Toppsvarets mening tar med riket först när även riket är färdigräknat, eftersom de distrikt som kommer först i landet är små och lantliga. "Majorna mot Sverige" och halvcirkeln säger under bilden hur långt jämförelseområdet kommit så länge det är delvis räknat.

**Sidan under kvällen:** statusraden överst säger "Preliminärt, X av 23 distrikt räknade. Uppdaterad HH:MM." med knappen "Ladda om" bredvid, och toppsvaret under den visar de största partierna i riksdagsvalet (fyra på en telefon, alla utom Övriga från 600 px containerbredd) utan någon valdeltagandemening förrän alla 23 distrikt är räknade. Byter läsaren till Valet 2022 lyder raden "Slutligt resultat 2022. Ladda om", och knappen tar tillbaka till den levande vyn. Oräknade distrikt gråtonas på kartan, Majorna-snittet räknas på räknade distrikt, och legendraden under kortets små tal säger "räknat på N jämförbara distrikt av 23" tills alla är räknade.

**Jämförelseåret laddas vid start på valnatten.** Åren i konfigen laddas annars först när läsaren väljer dem (se Årväljaren och den lata laddningen), men när `"valnatt": true` hämtar sidan också det största året under standardåret. Kortet för ett distrikt som ännu inte är räknat visar hur distriktet röstade förra valet ("Så röstade Mariaplan 2022"), och den raden slår upp basåret bland de laddade åren: utan förladdningen står kortet tomt den första timmen, när de flesta distrikt är oräknade. `verktyg/tvaar-check.js --partiell=` vaktar det.

### Reservväg

**Xlsx-vägen** om Valmyndigheten publicerar filer i 2022 års format: `--rd`, `--rf` och `--kf` med en, två eller tre filer, samma flöde i övrigt. Skriptet väntar sig ett blad `roster_RD`, `roster_RF` eller `roster_KF` i långformat.

**CSV-vägen** när inget filformat går att läsa. Skriv mallen, fyll i siffrorna för hand från val.se och kör:

```bash
.venv/bin/python scripts/uppdatera_2026.py --skriv-mall valnatt.csv
.venv/bin/python scripts/uppdatera_2026.py --csv valnatt.csv --status preliminar
```

Format: `val;kod;parti;roster` där val är `rd`, `rf` eller `kf`, kod är distriktskoden och parti är partikoden (V, S, MP, SD, M, C, L, KD, D, FI, K eller Övriga). Rader som börjar med `#` hoppas över, så mallens instruktionsrader och distriktsrubriker kan stå kvar. Mallen täcker riksdagsvalet och har 12 rader per distrikt (nio partirader inklusive Övriga plus `giltiga`, `rostande` och `rostberattigade`), alltså 276 tal för 23 distrikt. Partiordningen är sidans (V, S, MP, SD, M, C, L, KD), inte val.se:s. Region och kommun skrivs för hand i samma format.

Regler som skriptet vaktar: partirösterna måste summera till `giltiga`; negativa tal, okända partikoder och `rostande` över `rostberattigade` avvisas; `rostberattigade` ska vara ifyllt för alla räknade distrikt i ett val eller för inget (annars blir Majornas valdeltagande fel), och kontrollen gäller slutläget över alla källor, inte bara CSV-filens egna rader. Saknas `rostande` sätts det lika med `giltiga`, med en varning: valdeltagandet visas då cirka en procentenhet för lågt. Hårda mellanslag (U+00A0) i tal tolkas som tusentalsavgränsare. Alla fel anger radnumret i filen.

**Komplettering för hand medan JSON-vägen fungerar** för resten: fyll i de distrikt som fattas och kör

```bash
.venv/bin/python scripts/uppdatera_2026.py --valnatt-mapp data/valnatt/senaste --csv valnatt.csv --status preliminar
```

CSV:n vinner per distrikt och val, resten kommer från JSON-filerna och jämförelseaggregaten finns kvar. `--csv` ensam ovanpå en färdig fil stoppas av spärren mot färre räknade distrikt, och `--tvinga` ersätter hela filen i stället för att komplettera.

### Efter valet

Preliminär räkning fortsätter till och med uppsamlingsräkningen på onsdagen: samma kommando som under kvällen, en gång i timmen räcker. När den slutliga räkningen börjar publiceras (från måndagen):

```bash
.venv/bin/python scripts/uppdatera_2026.py --hamta --tillfalle s --status slutlig
```

Sätt sedan `"valnatt": false` i `data/konfig.json` och skriv om `konfig.js`:

```bash
.venv/bin/python -c "from scripts import schema; schema.skriv_konfig('data', schema.las_konfig('data'))"
```

Stillbilder till brevet: `.venv/bin/python scripts/skapa_bilder.py --ar 2026 --etikett "Majposten · Valet 2026"`.

### Vanliga fel

Hämtningen:

- `FEL: https://resultat.val.se/resultatfiler/val2026/index.md5 svarar 404: resultatfilerna publiceras först på valkvällen` - adressen är inte öppnad än. Väntat före valkvällen.
- `FEL: index.md5 är tom eller har fel form (svarar adressen 404 än?)` - indexet svarade men gick inte att tolka. Kör igen.
- `FEL: md5 stämmer inte: <a> i filen, <b> i index` - filen ändrades under hämtningen. Skriptet har redan gjort ett återförsök med paus, så kör igen om några minuter.
- `FEL: rd: signatur saknas för <fil>` och `FEL: rd: signaturen för <fil> stämmer inte` - fel certifikat eller manipulerad fil. Hämta om certifikatet först. `--utan-signatur` är reservläge och används bara om val.se bekräftar problemet: `.venv/bin/python scripts/uppdatera_2026.py --hamta --utan-signatur --status preliminar` ger utskriften "signatur ej kontrollerad".
- `FEL: data/valnatt/senaste är en katalog, inte en länk; flytta undan den` - `senaste` ska vara en symlänk.
- Nätfel under `uppdatera_2026.py --hamta` ger två rader: `FEL: <url>: <orsak>` (samma meddelande hamta_2026.py själv hade skrivit, till exempel `FEL: https://resultat.val.se/...: [Errno 8] nodename nor servname provided, or not known`) följt av `FEL: hämtningen misslyckades, inget skrivet`. Inget är skrivet; vänta och kör igen.
- `FEL: hämtningen avbröts med kod N` - hämtningen avslutades på ett sätt som inte fångades av dess egna felhantering (sällsynt). Kör igen.

`--tvinga` låser upp tre spärrar på en gång: färre räknade distrikt, testdata över skarp data, och testdata till repots `data/` - inte bara den som utlöste stoppet. En `--genrep`-körning med standard-`--ut` följd av återstartskommandot med `--tvinga` skriver alltså testmärkt data till `data/` utan att stoppas. Se avsnittet Under kvällen.

Inläsningen:

- `FEL: färre räknade distrikt än i valdata_2026.json (rd: 12 mot 18)` - Valmyndigheten har dragit tillbaka distrikt, eller en fil är trasig. En trasig fil i ett val stoppar hela skrivningen, avsiktligt. Gå vidare med `.venv/bin/python scripts/uppdatera_2026.py --valnatt-mapp data/valnatt/senaste --tvinga --status preliminar`, som ersätter hela filen.
- `FEL: <val>: <fil> har inte formen av en JSON-fil: <detalj>` - halvskriven fil hos Valmyndigheten. Kör igen.
- `FEL: <sökväg>: har inte formen av en JSON-fil: <detalj>. <råd>` - en befintlig fil i `data/` går inte att läsa (skadad eller halvskriven från en tidigare körning). Rådet skiljer mellan basårets fil och årets egen.
- `FEL: valdata_2026.json är skarp data men den nya filen är testdata` - en `--genrep`-körning mot skarp data.
- `FEL: filerna är testdata (test: true) och --ut är repots data/` - torrkörningen saknar `--ut` till en annan mapp.
- `FEL: <mapp>: inga av mapparna rd, rf, kf finns` - fel mapp angiven i `--valnatt-mapp`.
- `FEL: <fil>: hittar inget blad vars namn börjar med 'roster_'` - fel xlsx-fil eller nytt format. Använd reservvägen.

CSV-vägen:

- `FEL: <fil> rad N: fler kolumner än rubriken (ett semikolon för mycket?)`
- `FEL: rd: 'rostberattigade' saknas för <koder> men finns för andra distrikt` - fyll i för alla räknade distrikt i valet eller för inget.
- `FEL: <fil>: kunde inte läsas: <orsak>. Spara som CSV UTF-8 i Excel.` - fel teckenkodning.
- `FEL: <fil>: <val> <kod>: partiröster N != giltiga M` - filen är inkonsekvent eller en partirad saknas. Kontrollera distriktet på val.se.

Sidan:

- "Datafilerna kunde inte laddas" - standardårets `valdata_<år>.js` eller `distrikt_<år>.js` saknas på hosten, eller `data-bas` i Beehiiv-blocket pekar fel. Sidan felar bara när inget år alls gick att ladda.
- "Valet 2014 kunde inte laddas." under årväljaren - året står i `KONFIG.ar` men dess `valdata_<år>.js` eller `distrikt_<år>.js` saknas på hosten. Den vy läsaren hade står kvar, väljaren faller tillbaka på det år som visas, och raden försvinner vid nästa lyckade byte. Året tas inte ur väljaren, så ett nytt försök går att göra när filen är på plats.
- 404 på `data/swing_<år>.js` i konsolen är ofarligt: filen är valfri, och året visas då utan små tal vid staplarna.

## Djuplänkar

Sidan läser och skriver URL-parametrar, så ett kvarter kan länkas direkt från Beehiiv:

```
index.html?distrikt=14800530                 Mariaplan, riksdagsvalet
index.html?distrikt=14800530&val=kf          samma distrikt, kommunvalet
index.html?lage=styrka&parti=SD&val=rf       partistyrka för SD i regionvalet
index.html?ar=2018&distrikt=14800527         valet 2018 (året måste stå i KONFIG.ar)
```

Sidan rullar till kartan när `distrikt` finns i länken.

`ar` är den enda parametern som kostar en filhämtning. Åren laddas annars först när läsaren väljer dem i väljaren, men ett år som står i URL:en laddas vid start tillsammans med standardåret, så att länken landar rätt direkt. Ett år som inte står i `KONFIG.ar` ignoreras. Distriktskoder:

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
meta        ar, status (slutlig | preliminar), uppdaterad, kalla, avgransning, val, partier,
            valnatt {raknade, totalt}, test (bara i filer byggda av testdata, till exempel genrep)
distrikt[]  kod, namn, raknat, rd {parti: röster}, rf, kf, giltiga {rd, rf, kf}, rostande {...},
            rostberattigade {...}, jamforbar_mot_bas, grans_andrad
aggregat    majorna {val: {roster, giltiga, rostande, rostberattigade}}   (räknade distrikt)
            goteborg {val: {namn, andel, valdeltagande, giltiga, rostande, rostberattigade,
            antal_distrikt, totalt_distrikt}}, riket {val: {samma nycklar}}  (rf: Västra Götaland)
mandat      riksdag_verklig, riksdag_majorna, metod
```

`jamforbar_mot_bas` och `grans_andrad` är samma uppgift åt två håll: distriktet kan jämföras med basåret, respektive dess gränser har ritats om. `antal_distrikt` och `totalt_distrikt` i aggregaten säger hur långt jämförelseområdet kommit i räkningen; `rostberattigade` där gäller räknade distrikt. I historikårens filer (byggda av `bygg_historik.py`) utelämnas ett nyckelparti som saknar rader ett visst år och val (till exempel D före 2018) helt ur `distrikt[].rd/rf/kf` och ur `aggregat` i stället för att skrivas som noll.

`data/swing_<år>.json`: förändring i procentenheter mot basåret. Sidan visar den som små tal vid staplarna i resultatkortet, med en legendrad under.

```
ar, bas, enhet   2026, 2022, "procentenheter"
distrikt         {kod: {val: {parti: tal}}} för räknade och jämförbara distrikt
ej_jamforbara    {kod: {orsak, mening, omradesrad}} - meningen kortet visar i stället för tal
majorna          {val: {parti: tal}} för hela Majorna, räknat på kohorten
kohort           {val: {antal, totalt, helomrade, koder}} - vilka distrikt majorna-talen vilar på
```

Ett parti som saknas i något av åren utelämnas ur diffen i stället för att visas som en förändring till eller från noll. Är `helomrade` sant jämförs hela området mot hela basåret; annars bara de distrikt som är både räknade och jämförbara, och legendraden under kortets små tal skriver ut "räknat på N jämförbara distrikt av 23".

`data/konfig.json`: `ar`, `standardAr`, `valnatt`, `adress`, `inbaddad`, `skrivUrl`, `stickyTopp`, `valdag`, `toppsvar` (`mening`), `historik` (`visa`, `mening` per val), `samarbete` (med `valvaka`) och `hjalp`. Standardvärdena ligger i `scripts/schema.KONFIG_STANDARD`.

`data/historik.json`: områdesserien bakom sektionen "Majorna sedan 2006".

```
meta   byggd, kalla, ar (seriens år, 2006 till 2022), partier (alla koder som kan förekomma i något val),
       partier_per_val {val: [koder]}, noter (metodtexter), metod {år: metodbeskrivning, ett per år}
serie  {val: {niva: [{ar, roster {parti: röster}, andel {parti: andel av giltiga}, giltiga, rostande,
       rostberattigade, valdeltagande, antal_distrikt}]}}, niva är majorna, goteborg eller riket
```

Varje post i `serie` har exakt `meta.partier_per_val[val]` (fast per val, samma alla år) - aldrig färre nycklar; ett nyckelparti som saknade rader det året (till exempel D 2006) står med värdet 0 i stället för att utelämnas. Partier utanför valets uppsättning, till exempel FI i riksdagsvalet, läggs i Övriga.

`data/swing_2022.json`: samma form som `data/swing_<år>.json` ovan, men mot bas 2018 i stället för 2022: nio av de 23 distrikten är jämförbara, fjorton får den bakåtvända meningen ("Gränserna såg annorlunda ut 2018..."). `kohort` är `helomrade: true` för alla tre valen (`samma_yta=True`: 23 distrikt 2022 mot 22 distrikt 2018 täcker samma yta) och har en extra nyckel `metod: "omradesserien"` som bara är en anteckning - kortet läser den inte. Områdesnivån (`majorna`) kommer alltså inte ur kohorten av jämförbara distrikt, utan ur hela områdets aggregat båda åren, hämtat ur databasens tidsserie för 2018.

Andelar räknas alltid i sidan som parti delat med giltiga röster. Inga tal är hårdkodade i `index.html`.

## Designval

Sidhuvudet svarar på frågan innan läsaren scrollar: en statusrad ("Preliminärt, 12 av 23 distrikt räknade. Uppdaterad 21:35.", "Slutligt resultat 2022. Valet 2026 är söndag 13 september.") och under den ett toppsvar med de största partierna i riksdagsvalet som korta staplar. Under 600 px containerbredd är det fyra partier; från 600 px visas alla utom Övriga, eftersom raderna då får plats utan att sidhuvudet blir en vägg. Valdeltagandemeningen under staplarna kommer först när hela Majorna är färdigräknad i det visade valet. Banderollen och ingressen som fanns tidigare är borttagna: de sade samma sak två gånger och sköt ned kartan. Höjderna är reserverade så att sidhuvudet inte hoppar när datan kommer: statusraden 52 px under 600 px containerbredd och 26 px däröver, toppsvaret 208 px respektive 352 px, och med `har-mening` (klassen som sätts när `toppsvar.mening` är satt) 270 respektive 388 px. Årväljarens rad är 44 px med `margin: 0 0 12px` så fort konfigen listar två år. I nolläget (0 av 23 räknade) visar toppsvaret bara en rad ("Riksdagsvalet 2026: inget distrikt räknat än.") i den reserverade rutan i stället för att krympa den - avsiktligt, så att höjden är densamma före och efter att det första distriktet räknas. "Ladda om" är en `<button>` med länkutseende, inte en länk: den laddar om värdsidan, och en länk hade gått att cmd-klicka till ingenstans.

Resultatkortet visar distriktets namn och staplarna, inget mer i löptext; topp tre-meningen finns bara i skärmläsarraden (`#panel-live`). Förändringen mot förra valet står som små tal vid staplarna, med legendraden "Små tal: förändring mot 2022 i procentenheter" under dem; för hela Majorna får den raden kohorttexten "räknat på N jämförbara distrikt av 23" tills alla är räknade. Ett parti som saknar tal i swingfilen får inget litet tal, aldrig "0,0". Ett omritat distrikt har inga små tal alls och får i stället en fristående mening som säger varför - `ej_jamforbara[kod].mening` ur swingfilen, som för 2026 lyder "Gränserna för Mariaplan ritades om till 2026. Siffrorna går inte att jämföra med 2022." Skärmläsarraden slutar med den meningen. Blocket "Hur har det ändrats", som upprepade de små talen i egna rader, togs bort 2026-09-07, liksom kortets rad med valdeltagande och giltiga röster (valdeltagandet står redan i toppsvaret). Kvar i den raden står bara valnattens "X av 23 distrikt räknade."; utanför valnatten är den tom och dold.

Kartan är inline-SVG utan kartbibliotek: inga externa beroenden, fungerar offline, kapar inte sidscrollen på mobil. Orienteringen kommer från ett lokalt bakgrundslager (OpenStreetMap, hämtat vid byggtid). Saknas `data/bakgrund.js` ritas kartan mot enfärgad bakgrund. I läget Största parti skriver kartan inga partibokstäver: kartlegenden ovanför säger vilken färg som är vilket parti, och formerna får bära resten. Det valda distriktets namn ritas fortfarande ut, och läget Partistyrka har kvar sitt tal i varje distrikt. Färger kompletteras alltid med text på annat håll: legenden ovanför kartan, tabellvyn för alla distrikt och aria-etiketter på varje distrikt. Distriktsgränsen är 3 px papper, 3,5 px och bläck vid hover - samma bredd som bildläget redan använde. Kartans typstorlekar (etiketter, hållplatsnamn, kontur) räknas om löpande efter kartans faktiska pixelbredd, inte efter en fast 600 px-tröskel, så texten håller samma storlek i pixlar oavsett hur brett Beehiivs sektion råkar vara.

Utseendet följer Majpostens palett och typografi (Georgia och Arial, papper och slottsskogsgrön, inga skuggor eller gradienter). I Partistyrka är toppsteget i legenden alltid partiets egen färg, aldrig mörkad mot bläck; för ljusa partifärger (SD, Liberalerna) sprids de undre stegens toner mer så att de fortfarande syns som skilda nyanser.

Resultatkortet ("Hela Majorna" eller ett valt distrikt) visar en enda jämförelsemarkör per stapel: hela Majorna mot riket (riksdag), Västra Götaland (region) eller Göteborg (kommun), samma svarta markör som används när ett distrikt jämförs mot hela Majorna. "Röstdelningen" är byggd som HTML-rader (som "Majorna mot Sverige", inte SVG): en rad per parti med markörer för riksdag (cirkel), region (romb) och kommun (kvadrat) på en gemensam procentaxel, så att man ser hur mycket ett parti röstdelar mellan valen. Markörerna ligger på tre höjder kring linjen (riksdag på linjen, region strax över, kommun strax under) eftersom de annars täcker varandra när ett parti får nästan samma andel i alla tre valen. Axeletiketterna (0 %, 10, 20, 30, 40) glesas ut efter uppmätt bredd i stället för efter en fast brytpunkt: antalet steg följer årets högsta andel, så en fast regel spricker ett jämnare år. Gallringen mäter etiketternas egna rutor och behåller varannan, var fjärde, var åttonde och i sista hand bara axelns båda ändar; enheten sitter på den första etiketten och döljs aldrig. Talen står kvar i talspalten till höger, så en grov axel på en smal skärm kostar ingen information. Uppmätt på index i standardåret 2022, som har fem steg, i 320, 360, 390, 600, 900 och 1280 px fönsterbredd: 2, 3, 5, 5, 5 och 5 synliga etiketter, och inga krockar. Före omgången visades alla fem i alla sex bredder, med två krockar vid 320 px och en vid 360 px. En `ResizeObserver` på `#rostdelning-rader` ritar om när spalten byter bredd; att dölja etiketter ändrar inte spaltens bredd, så observatören kan inte trigga sig själv.

**"Om Majorna bestämde"** har två knapprader. Den första väljer fördelning, "Riksdagen ÅÅÅÅ" eller "Om Majorna bestämde", och styr både halvcirkeln och vilken tabellkolumn som står i fetstil. Den andra väljer enhet, Mandat eller Procent, och styr bara tabellen: halvcirkeln ritar mandat i båda lägena, eftersom det är mandat bilden visar, och dess `aria-label` räknar mandat i båda lägena av samma skäl. I mandatläget heter kolumnerna "Riksdagen ÅÅÅÅ" och "Majornas riksdag" och bär mandattal, med orden "under spärren" för ett parti som inte kom in. I procentläget heter de "Riket ÅÅÅÅ" och "Majorna" och bär **röstandelar, inte mandatandelar**: en mandatandel hade sagt samma sak som mandattalet en gång till, medan röstandelen förklarar fyraprocentsspärren - KD står med 2,3 procent i Majorna 2022 i stället för orden "under spärren". Rikets andelar kommer ur `aggregat.riket.rd.andel`, Majornas räknas ur `aggregat.majorna.rd`. Radernas urval är detsamma i båda enheterna (partier med minst ett mandat i någon av de två fördelningarna), och ett parti utan andel får tankstreck, aldrig 0,0. Saknar året rikets andelar döljs hela enhetsraden och bara mandatläget finns, på samma sätt som fördelningsraden döljs när det bara finns en fördelning. Skärmläsarraden `#mandat-live` byggs ur tabellens egna celler och kan därför inte säga mandat när tabellen visar procent. På desktop ligger enhetsraden i högerspalten strax över tabellen, med halvcirkeln till vänster om båda.

Mandattabellen ligger i en behållare med `overflow-x: auto` (`.mandat-wrap`) som yttre spärr: blir tabellen någon gång bredare än sektionen rullar den i sin egen ruta i stället för att dra med sig hela sidan i sidled. Under 372 px containerbredd döljs dessutom det långa partinamnet i CSS, så att den rullningen aldrig behövs i praktiken. Gränsen är uppmätt, inte gissad: tabellens naturliga bredd med namnet är 339 px och sektionen är containerbredden minus 32 px, alltså ryms namnet från 372 px och inte tidigare. Efteråt är tabellen exakt lika bred som sin behållare i 320, 360, 390, 600, 900 och 1280 px (288, 328, 358, 568, 414 och 524 px), och `document.documentElement.scrollWidth` är lika med `window.innerWidth` i alla sex. Före omgången var tabellen 339 px bred i en 288 px bred sektion vid 320 px, och hela sidan fick sidledsrullning (`scrollWidth` 355 mot 320). Ändras tabellen måste 339 mätas om, annars flyttar sig gränsen. `verktyg/bredd-check.js` är den enda kontroll som fångar både sidledsrullningen och krockande axeletiketter, och den körs medvetet utan mobilemulering: med `isMobile: true` blir `innerWidth` lika med layoutbredden och rullningen syns inte.

Två layouter i en DOM, styrda av containerns bredd (CSS container queries), inte fönstrets: under 900 px en spalt som på mobil, från 900 px kartan till vänster med resultatkortet fastnaglat till höger, halvcirkeln bredvid mandattabellen (räkneexemplet under halvcirkeln, inte under hela sektionen) och de två jämförelsegrafikerna sida vid sida. Tabellknappen och tabellen ligger sist i kartsektionen, under kartan och kortet, inte i en egen sektion; kartan, kartlegenden och kortet ligger i sin tur i ett eget rutnät (`#karta-yta`) så att det fastnaglade kortet inte kan följa med ned över tabellknappen och tabellen. Brödtexten håller smal spalt även på desktop. Sektionen som blocket ligger i på Beehiiv behöver vara minst cirka 1 000 px bred för att desktopläget ska slå till. Ingen egen prenumerationsknapp: Beehiivs eget prenumerationsblock läggs på sidan.

Två oberoende brytpunkter: 600 px containerbredd styr kartans detaljnivå (fler hållplatser och platsnamn, procent i etiketterna), 900 px styr tvåkolumnslayouten. Mellan 600 och 900 px visas alltså den detaljerade kartan i en spalt, vilket är avsett.

En tredje brytpunkt gäller bara "Röstdelningen": partinamnet bredvid partibokstaven ("V Vänsterpartiet") kräver 1 100 px containerbredd. Mellan 900 och 1 100 px delar sektionen rad med "Majorna mot Sverige" och blir så smal att namnen radbryter, så där visas bara partibokstaven. Under 900 px är sektionen full bredd och namnen syns igen (från 600 px containerbredd).

Resultatkortet på desktop är fastnaglat med `position: sticky` inuti `#karta-yta` (kartan, legenden och kortet), vilket är vad som håller kortet ovanför tabellknappen, och avståndet `stickyTopp` (px) i `data/konfig.json`, standard 105 (Beehiivs egen klibbiga sidmeny är 89 px hög, plus 16 px marginal). Samma värde används som `scroll-margin-top` när sidan rullar till kartan, kortet eller tabellen. I Beehiivs `iframe srcdoc` är `position: sticky` verkningslöst (inget rullar inuti iframen), så kortet följer inte med vid rullning där - det är känt och accepterat, se avsnittet Beehiiv. Sticky faller också tyst tillbaka till vanlig placering om värdsidan lägger `overflow` eller `transform` på ett element runt blocket; kontrollera på den publicerade sidan.

## Källor och licenser

Valdata: Valmyndigheten, slutlig rösträkning per valdistrikt 2022 (val.se, rådata). Valgeografi: Valmyndigheten. Kartunderlag: © OpenStreetMaps bidragsgivare, ODbL. Avgränsningen av klassiska Majorna beskrivs i fliken "Metod & källor" i `majorna-valresultat-2022.xlsx`.
