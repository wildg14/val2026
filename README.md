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
data/distrikt_2026.*          2026 års gränser: samma yta, elva distrikt ritade på nytt
data/bakgrund.json / .js      gator, spårväg, hållplatser, vatten, parker från OpenStreetMap (valfri)
data/valdata_2026.*           skrivs av uppdatera_2026.py på valnatten
data/swing_2026.*             förändring mot 2022 per distrikt och för hela Majorna, skrivs samtidigt
data/valnatt/                 Valmyndighetens hämtade och uppackade filer, en mapp per körning (gitignorerad)
scripts/bygg_data.py          xlsx + zip -> data/, med kontroller
scripts/bygg_geo.py           Valmyndighetens valgeografi -> data/distrikt_<år>.geojson och .js
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
verktyg/                      forbered_tvaar.py och Puppeteer-kontrollerna (bland dem tvaar-check.js), se verktyg/README.md
tests/                        pytest, 224 tester
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

`data-bas` säger var `data/` ligger (samma mapp som skriptet). Kontrollera i Preview och sedan Live: kartan ska synas, alla tabbar fungera, och Beehiivs egen meny och sidfot ligga kvar runt omkring. Vill du dölja grafikens egen etikett, rubrik och sidfot (Beehiiv har redan sina) sätter du `"inbaddad": true` i `data/konfig.json` och skriver om `konfig.js` med `.venv/bin/python -c "from scripts import schema; schema.skriv_konfig('data', schema.las_konfig('data'))"`.

Beehiivs regler som bygget följer: koden börjar med en enda container-div, all CSS är scopad till `.mp-val`, inga regler på `*`, `body` eller `html`, inga `vh`-mått, ingen `position: fixed`. Testet `tests/test_inbaddning.py` vaktar det.

Total sidvikt är cirka 376 kB för ett år: `du -ch valgrafik.js valgrafik.css data/konfig.js data/valdata_2022.js data/distrikt_2022.js data/bakgrund.js`. Bakgrundslagret är 228 kB av det. På valnatten tillkommer `distrikt_2026.js`, `valdata_2026.js` och `swing_2026.js`, tillsammans 52 kB.

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
- `toppsvar.mening` är en redaktionell mening under toppsvaret, tom som standard. Håll den till en rad, cirka 60 tecken: sidan reserverar höjd för en rad extra, en längre mening kan ge några pixlars hopp på små telefoner.
- `historik` (`visa` och en mening per val) hör till sektionen "Majorna sedan 2006", som byggs i en egen plan.

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

`--hamta` laddar ned riksdagen (hela landet), regionvalet (Västra Götaland) och kommunvalet (Göteborg), kontrollerar md5 mot index och JSON-filernas signaturer mot certifikatet, packar upp till `data/valnatt/<tidsstämpel>/` och läser JSON därifrån. `--valnatt` sätter `data/konfig` till `"ar": ["2022", "2026"]`, `"standardAr": "2026"`, `"valnatt": true` och behövs bara första gången. Sedan var femte till tionde minut:

```bash
.venv/bin/python scripts/uppdatera_2026.py --hamta --status preliminar && git add data && git commit -qm "Valnatten: uppdaterat $(date +%H:%M)" && git push origin main
```

Har de tre filerna samma md5 som förra körningen skriver skriptet `Inget nytt att läsa in.` och avslutar med kod 3 utan att röra något; kedjan stannar där och ingenting committas. Alla filer skrivs atomiskt, så sidan kan aldrig läsa en halvskriven fil.

Vallokalerna stänger 20.00 och det dröjer innan Majorna syns. En körning utan räknade Majornadistrikt är inte ett fel: filerna skrivs med 0 av 23 räknade, konfigen slås över i valnattsläge och sidan säger "inget distrikt räknat än" under en statusrad som räknar upp. Det är det normala läget den första timmen.

Skriptet vägrar däremot skriva när den nya filen har färre räknade distrikt i något val än den som redan ligger, eller när den är testdata över skarp data. Efter ett sådant stopp är kommandot för att gå vidare

```bash
.venv/bin/python scripts/uppdatera_2026.py --valnatt-mapp data/valnatt/senaste --status preliminar --tvinga
```

eftersom `--hamta` med samma filer bara ger kod 3. `--tvinga` ersätter hela filen: val som saknas i den nya blir tomma, ingenting slås ihop med den gamla. Flaggan låser dessutom upp tre spärrar samtidigt (färre räknade distrikt, testdata över skarp data, testdata till repots `data/`), så ett `--tvinga` direkt efter en `--genrep`-körning kan skriva testmärkt data till `data/` utan att stoppas.

Läs varningarna. `VARNING:` betyder att filerna skrevs men att något avviker: Göteborg har ett annat antal distrikt än 397, ett distrikt saknas i filen (markeras som oräknat), ett distrikt har bytt namn sedan 2022, ett okänt parti fick röster (de läggs i Övriga), filhuvudets antal räknade stämmer inte med Majornas, eller ett jämförelseaggregat kunde inte läsas. `FEL:` betyder att ingenting skrevs. Kontrollera ett distrikt mot val.se första gången, och öppna majposten.se/val2026 efter första pushen.

**Jämförbarhet mot 2022** kommer ur fältet `statusJamforelse` i Valmyndighetens filer, kontrollerat mot `valdistrikt-jamforelser-mellan-2022-och-2026.xlsx`: 14 av 23 distrikt kan jämföras, 9 är omritade. Säger någon av källorna "ej jämförbart" gäller det. Kortets rad "Hur har det ändrats" visar tal bara för de 14; de 9 får en mening och hela Majornas förändring, som är giltig eftersom de 23 distrikten täcker samma yta båda åren.

**Partier som inte förekommer i Valmyndighetens fil saknas i datan.** De skrivs varken som nollor eller markeras. I den preliminära filen betyder det att partiet inte är rapportparti och att rösterna ligger i Övriga; i den slutliga att partiet inte fick någon röst i distriktet. Ett sådant parti visas inte på sidan och får ingen förändringssiffra: hellre ingen siffra än en påhittad nolla. I genrepets filer gäller det K i kommunvalet och FI i regionvalet.

**Riksdagens verkliga mandat** läses ur mandatfördelningsfilen redan på valnatten, så halvcirkeln "Om Majorna bestämde" kan jämföra Majornas fördelning med riksdagens direkt. Fördelningen är preliminär, ändras under kvällen och efter uppsamlingsräkningen på onsdagen, och halvcirkeln skriver ut förbehållet ("Preliminär fördelning, riket: X av Y distrikt räknade.").

**Valdeltagandet i aggregaten** räknas mot röstberättigade i räknade distrikt, inte mot hela områdets väljarkår; annars visar riket 12 procent klockan 20.30. Toppsvarets mening tar med riket först när även riket är färdigräknat, eftersom de distrikt som kommer först i landet är små och lantliga. "Majorna mot Sverige" och halvcirkeln säger under bilden hur långt jämförelseområdet kommit så länge det är delvis räknat.

**Sidan under kvällen:** statusraden överst säger "Preliminärt, X av 23 distrikt räknade. Uppdaterad HH:MM." med knappen "Ladda om" bredvid, och toppsvaret under den visar de fyra största partierna i riksdagsvalet. Byter läsaren till Valet 2022 lyder raden "Slutligt resultat 2022. Ladda om", och knappen tar tillbaka till den levande vyn. Oräknade distrikt gråtonas på kartan, Majorna-snittet räknas på räknade distrikt, och kortets rad "Hur har det ändrats" säger "räknat på N jämförbara distrikt av 23" tills alla är räknade.

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
- `FEL: rd: signatur saknas för <fil>` och `FEL: rd: signaturen för <fil> stämmer inte` - fel certifikat eller manipulerad fil. Hämta om certifikatet först. `--utan-signatur` är reservläge och används bara om val.se bekräftar problemet; utskriften säger då "signatur ej kontrollerad".
- `FEL: data/valnatt/senaste är en katalog, inte en länk; flytta undan den` - `senaste` ska vara en symlänk.
- `FEL: hämtningen misslyckades: <typ>: <text>` - nätfel eller oväntad form. Inget är skrivet; vänta och kör igen.

Inläsningen:

- `FEL: färre räknade distrikt än i valdata_2026.json (rd: 12 mot 18)` - Valmyndigheten har dragit tillbaka distrikt, eller en fil är trasig. En trasig fil i ett val stoppar hela skrivningen, avsiktligt. Gå vidare med `--valnatt-mapp data/valnatt/senaste --tvinga`, som ersätter hela filen.
- `--tvinga` låser upp tre spärrar på en gång: färre räknade distrikt, testdata över skarp data, och testdata till repots `data/` - inte bara den som utlöste stoppet. En `--genrep`-körning med standard-`--ut` följd av återstartskommandot med `--tvinga` skriver alltså testmärkt data till `data/` utan att stoppas. Se avsnittet Under kvällen.
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

- "Datafilerna kunde inte laddas" - `data/valdata_2026.js` eller `data/distrikt_2026.js` saknas på hosten trots att konfigen listar 2026, eller `data-bas` i Beehiiv-blocket pekar fel. Ett år vars filer inte går att ladda hoppas över med en varning i konsolen; sidan felar först när inget år går att ladda.
- 404 på `data/swing_<år>.js` i konsolen är ofarligt: filen är valfri, och året visas då utan förändringstal.

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
meta        ar, status (slutlig | preliminar), uppdaterad, kalla, avgransning, val, partier,
            valnatt {raknade, totalt}, test (bara i filer byggda av testdata, till exempel genrep)
distrikt[]  kod, namn, raknat, rd {parti: röster}, rf, kf, giltiga {rd, rf, kf}, rostande {...},
            rostberattigade {...}, jamforbar_mot_bas, grans_andrad
aggregat    majorna {val: {roster, giltiga, rostande, rostberattigade}}   (räknade distrikt)
            goteborg {val: {namn, andel, valdeltagande, giltiga, rostande, rostberattigade,
            antal_distrikt, totalt_distrikt}}, riket {val: {samma nycklar}}  (rf: Västra Götaland)
mandat      riksdag_verklig, riksdag_majorna, metod
```

`jamforbar_mot_bas` och `grans_andrad` är samma uppgift åt två håll: distriktet kan jämföras med basåret, respektive dess gränser har ritats om. `antal_distrikt` och `totalt_distrikt` i aggregaten säger hur långt jämförelseområdet kommit i räkningen; `rostberattigade` där gäller räknade distrikt.

`data/swing_<år>.json`: förändring i procentenheter mot basåret. Sidan visar den som små tal vid staplarna och som raden "Hur har det ändrats" i kortet.

```
ar, bas, enhet   2026, 2022, "procentenheter"
distrikt         {kod: {val: {parti: tal}}} för räknade och jämförbara distrikt
ej_jamforbara    {kod: {orsak, mening, omradesrad}} - meningen kortet visar i stället för tal
majorna          {val: {parti: tal}} för hela Majorna, räknat på kohorten
kohort           {val: {antal, totalt, helomrade, koder}} - vilka distrikt majorna-talen vilar på
```

Ett parti som saknas i något av åren utelämnas ur diffen i stället för att visas som en förändring till eller från noll. Är `helomrade` sant jämförs hela området mot hela basåret; annars bara de distrikt som är både räknade och jämförbara, och kortet skriver ut "räknat på N jämförbara distrikt av 23".

`data/konfig.json`: `ar`, `standardAr`, `valnatt`, `adress`, `inbaddad`, `skrivUrl`, `stickyTopp`, `valdag`, `toppsvar` (`mening`), `historik` (`visa`, `mening` per val), `samarbete` (med `valvaka`) och `hjalp`. Standardvärdena ligger i `scripts/schema.KONFIG_STANDARD`.

Andelar räknas alltid i sidan som parti delat med giltiga röster. Inga tal är hårdkodade i `index.html`.

## Designval

Sidhuvudet svarar på frågan innan läsaren scrollar: en statusrad ("Preliminärt, 12 av 23 distrikt räknade. Uppdaterad 21:35.", "Slutligt resultat 2022. Valet 2026 är söndag 13 september.") och under den ett toppsvar med de fyra största partierna i riksdagsvalet som korta staplar, plus valdeltagandet i en mening. Banderollen och ingressen som fanns tidigare är borttagna: de sade samma sak två gånger och sköt ned kartan. Statusraden och toppsvaret har reserverad höjd (52 px respektive 208 px, statusraden 26 px från 600 px containerbredd) och årväljarens rad reserveras så fort konfigen listar två år, så att sidhuvudet inte hoppar när datan kommer. I nolläget (0 av 23 räknade) visar toppsvaret bara en rad ("Riksdagsvalet 2026: inget distrikt räknat än.") i den 208 px höga rutan i stället för att krympa den - avsiktligt, så att höjden är densamma före och efter att det första distriktet räknas. "Ladda om" är en `<button>` med länkutseende, inte en länk: den laddar om värdsidan, och en länk hade gått att cmd-klicka till ingenstans.

Resultatkortet har raden "Hur har det ändrats" i tre grenar. Ett jämförbart distrikt får tal för de tre största partier som har tal i swingfilen. Ett omritat distrikt får meningen "Gränserna för Mariaplan ritades om till 2026" och hela Majornas förändring för distriktets största parti. Hela Majorna får talen med kohorttexten "räknat på N jämförbara distrikt av 23" tills alla är räknade. Partier som saknar tal i swingfilen visas inte alls, aldrig som "0,0".

Kartan är inline-SVG utan kartbibliotek: inga externa beroenden, fungerar offline, kapar inte sidscrollen på mobil. Orienteringen kommer från ett lokalt bakgrundslager (OpenStreetMap, hämtat vid byggtid). Saknas `data/bakgrund.js` ritas kartan mot enfärgad bakgrund. Färger kompletteras alltid med text: partibokstav och procent på kartan, tabellvy för alla distrikt, aria-etiketter på varje distrikt. Kartans typstorlekar (etiketter, hållplatsnamn, kontur) räknas om löpande efter kartans faktiska pixelbredd, inte efter en fast 600 px-tröskel, så texten håller samma storlek i pixlar oavsett hur brett Beehiivs sektion råkar vara.

Utseendet följer Majpostens palett och typografi (Georgia och Arial, papper och slottsskogsgrön, inga skuggor eller gradienter). I Partistyrka är toppsteget i legenden alltid partiets egen färg, aldrig mörkad mot bläck; för ljusa partifärger (SD, Liberalerna) sprids de undre stegens toner mer så att de fortfarande syns som skilda nyanser.

Resultatkortet ("Hela Majorna" eller ett valt distrikt) visar en enda jämförelsemarkör per stapel: hela Majorna mot riket (riksdag), Västra Götaland (region) eller Göteborg (kommun), samma svarta markör som används när ett distrikt jämförs mot hela Majorna. "Röstdelningen" är byggd som HTML-rader (som "Majorna mot Sverige", inte SVG): en rad per parti med markörer för riksdag (cirkel), region (romb) och kommun (kvadrat) på en gemensam procentaxel, så att man ser hur mycket ett parti röstdelar mellan valen. Markörerna ligger på tre höjder kring linjen (riksdag på linjen, region strax över, kommun strax under) eftersom de annars täcker varandra när ett parti får nästan samma andel i alla tre valen.

Två layouter i en DOM, styrda av containerns bredd (CSS container queries), inte fönstrets: under 900 px en spalt som på mobil, från 900 px kartan till vänster med resultatkortet fastnaglat till höger, halvcirkeln bredvid mandattabellen (räkneexemplet under halvcirkeln, inte under hela sektionen) och de två jämförelsegrafikerna sida vid sida. Tabellknappen och tabellen ligger sist i kartsektionen, under kartan och kortet, inte i en egen sektion; kartan, kartlegenden och kortet ligger i sin tur i ett eget rutnät (`#karta-yta`) så att det fastnaglade kortet inte kan följa med ned över tabellknappen och tabellen. Brödtexten håller smal spalt även på desktop. Sektionen som blocket ligger i på Beehiiv behöver vara minst cirka 1 000 px bred för att desktopläget ska slå till. Ingen egen prenumerationsknapp: Beehiivs eget prenumerationsblock läggs på sidan.

Två oberoende brytpunkter: 600 px containerbredd styr kartans detaljnivå (fler hållplatser och platsnamn, procent i etiketterna), 900 px styr tvåkolumnslayouten. Mellan 600 och 900 px visas alltså den detaljerade kartan i en spalt, vilket är avsett.

En tredje brytpunkt gäller bara "Röstdelningen": partinamnet bredvid partibokstaven ("V Vänsterpartiet") kräver 1 100 px containerbredd. Mellan 900 och 1 100 px delar sektionen rad med "Majorna mot Sverige" och blir så smal att namnen radbryter, så där visas bara partibokstaven. Under 900 px är sektionen full bredd och namnen syns igen (från 600 px containerbredd).

Resultatkortet på desktop är fastnaglat med `position: sticky` inuti `#karta-yta` (kartan, legenden och kortet), vilket är vad som håller kortet ovanför tabellknappen, och avståndet `stickyTopp` (px) i `data/konfig.json`, standard 105 (Beehiivs egen klibbiga sidmeny är 89 px hög, plus 16 px marginal). Samma värde används som `scroll-margin-top` när sidan rullar till kartan, kortet eller tabellen. I Beehiivs `iframe srcdoc` är `position: sticky` verkningslöst (inget rullar inuti iframen), så kortet följer inte med vid rullning där - det är känt och accepterat, se avsnittet Beehiiv. Sticky faller också tyst tillbaka till vanlig placering om värdsidan lägger `overflow` eller `transform` på ett element runt blocket; kontrollera på den publicerade sidan.

## Källor och licenser

Valdata: Valmyndigheten, slutlig rösträkning per valdistrikt 2022 (val.se, rådata). Valgeografi: Valmyndigheten. Kartunderlag: © OpenStreetMaps bidragsgivare, ODbL. Avgränsningen av klassiska Majorna beskrivs i fliken "Metod & källor" i `majorna-valresultat-2022.xlsx`.
