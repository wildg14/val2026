# Handover: Så röstade Majorna

Skriven 2026-09-04 av den session som byggde grafiken, för nästa session. Läs den här filen i sin helhet innan du gör något. Valdagen är 2026-09-13.

## Läs i den här ordningen

1. Den här filen.
2. `README.md` i projektroten: körordning, Beehiiv, valnatten, stillbilder, dataschema.
3. `docs/superpowers/specs/2026-09-03-majorna-valgrafik-design.md` (ursprunglig spec) och `docs/superpowers/plans/2026-09-03-majorna-valgrafik.md` (plan). Delvis inaktuella: kartan är inte längre i `index.html` utan i `valgrafik.js`, se nedan.
4. Minnesfilerna i `/Users/daniel/.claude/projects/-Users-daniel-code-Temp/memory/` (index i `MEMORY.md`): vem Daniel är, Majpostens skrivregler, Beehiiv-planen, modellval för subagenter.
5. `docs/historik/datamodell.md` och `docs/historik/noter/*.md` om du ska röra historikspåret (se avsnittet Historikspåret).
6. `docs/inbaddningstest.html` och `verktyg/README.md` när du ska verifiera i webbläsare.

## Vad projektet är

En interaktiv valgrafik för nyhetsbrevet Majposten (Daniel Emgård, hyperlokalt veckobrev om Majorna i Göteborg, publicerat via Beehiiv). Grafiken visar valresultatet 2022 för de 23 valdistrikten i klassiska Majorna (koder 14800526 till 14800548, valkrets Västra Centrum, primärområdena Majorna, Stigberget, Kungsladugård och Sanna), i riksdags-, region- och kommunvalet, och är byggd för att ta emot 2026 års siffror på valnatten utan kodändring.

Grafiken ligger native på en sida i Beehiivs sajtbyggare, **majposten.se/val2026**, som ett HTML-block. Koden och datan hostas på GitHub Pages: repo **github.com/wildg14/val2026**, adress **https://wildg14.github.io/val2026/**. Läsaren ser aldrig GitHub-adressen. Ingen iframe: Daniel avvisade iframe uttryckligen.

Projektmappen är `/Users/daniel/code/Temp` (git, branch `main`, remote `origin` = GitHub). Publicering av kodändringar är `git push origin main`; Pages bygger själv inom en minut. Beehiiv-sidan behöver aldrig röras för uppdateringar.

## Arbetsregler som gäller i det här projektet

- **Inga påhittade siffror.** Allt räknas ur datafilerna, och `scripts/kontrollera.py` stämmer av `data/valdata_2022.json` mot `majorna-valresultat-2022.xlsx` (1 149 kontroller). Ändra aldrig ett tal för hand. Kör `.venv/bin/python -m pytest -q` (38 tester) före och efter ändringar.
- **Majpostens skrivregler** i all text, även UI-etiketter och README: bindestreck med mellanslag ( - ), aldrig tankstreck; inga utropstecken, inga emoji, inga superlativ; kollade fakta skrivs platt, okollat märks [KOLLA]. Palett: papper #FAF6EE, bläck #2A241E, sten #6E6152, linje #E6DECF, slottsskogsgrön #3F5A3A, mörkgrön #2E4A2C, ockra #C58A34, falurött #8C3B2B. Georgia för rubriker, Arial för brödtext, minst 16 px löptext. Aldrig skuggor, gradienter, ikoner eller dekorelement.
- **Beehiivs regler för HTML-block**: en enda container-div, all CSS scopad till `.mp-val`, inga regler på `*`, `body`, `html` eller `:root`, inga `vh`-mått, ingen `position: fixed`. `tests/test_inbaddning.py` vaktar detta; kör det efter varje CSS-ändring.
- **Subagenter och workflows**: Daniel vill inte att de kör Fable (kontextförbrukningen). Sätt `model: 'sonnet'` (eller haiku för mekaniskt arbete) och `effort: 'medium'`, håll antalet agenter till två till fyra, och nämn modellvalet när en workflow startas.
- **Testdrivet** för Python-skripten: skriv testet först, se det falla, implementera. För `valgrafik.js` och `valgrafik.css` verifieras i webbläsare med skripten i `verktyg/`.
- **Verifiera före påståenden.** Säg inte att något fungerar utan att ha kört testet eller sett skärmdumpen.
- **Git**: identitet är satt lokalt i repot (Daniel Emgård, daniel@tvartom.win). Committa bara det du själv ändrat. Historikspårets filer ska inte committas utan att Daniel bett om det. Repot är publikt.
- **Frågor till Daniel**: han tar beslut om redaktion, adresser och prioritering själv. Fråga när ett val är hans, gör inte antaganden om vad han vill se.
- **Minnesfiler**: uppdatera `majorna-valgrafik-projekt.md` när något viktigt ändras.

## Status 2026-09-04: vad som finns

| Del | Fil | Vad |
|---|---|---|
| Grafiken | `valgrafik.js` (cirka 53 kB) | Renderar allt inuti `<div class="mp-val" id="valgrafik">`: rubrik, "Om Majorna bestämde", kartan med flikar och lägen, resultatkortet, tabellen, "Majorna mot Sverige", "Röstdelningen", "Om siffrorna", sidfot. Läser `data/konfig.js` och datafilerna från adressen i `data-bas` eller skriptets egen mapp. |
| Stil | `valgrafik.css` (cirka 17 kB) | All CSS scopad till `.mp-val`. Två layouter via container queries: under 900 px containerbredd en spalt (mobil), från 900 px två kolumner. 600 px styr kartans detaljnivå. |
| Skal | `index.html` | Tunt skal för lokal visning, bildläge och skärmdumpar. Open Graph-taggar med adressen. |
| Data | `data/valdata_2022.json` + `.js`, `data/distrikt.geojson` + `.js`, `data/bakgrund.json` + `.js`, `data/konfig.json` + `.js` | `.js`-filerna är identiska kopior av `.json` som sidan laddar via `<script>` (fungerar via file:// och kräver ingen CORS). Skrivs av `scripts/schema.py`. |
| Pipeline | `scripts/bygg_data.py`, `scripts/kontrollera.py`, `scripts/valmyndigheten.py`, `scripts/mandat.py`, `scripts/geo.py`, `scripts/schema.py` | xlsx + zip till data/, med fem kontrollsteg. |
| Valnatten | `scripts/uppdatera_2026.py` | Valmyndighetens råfiler (blad `roster_RD`, `roster_RF`, `roster_KF`) till `valdata_2026` + `swing_2026`. `--repetera` reproducerar 2022 exakt ur 2022 års råfiler. `--csv` är reservväg med handifylld fil. `--valnatt` uppdaterar `data/konfig`. |
| Bakgrund | `scripts/hamta_bakgrund.py` | Gator, spårväg, hållplatser, vatten, parker och platsnamn från OpenStreetMap via Overpass. Valfritt lager. |
| Stillbilder | `scripts/skapa_bilder.py`, `bilder/` | Chrome headless renderar `index.html?bild=jamforelse` och `?bild=karta` i 1200 x 630 och 1080 x 1080, 2x, med alt-text i `.txt`. |
| Tester | `tests/` | 38 tester: mandatberäkning, parser mot råfiler, geometri, schema, kontrollskript, bygge, bakgrund, uppdatera, stillbilder, Beehiiv-regler. |
| Verktyg | `verktyg/` | Puppeteer-skript för skärmdumpar och mätningar (se `verktyg/README.md`). Kräver `npm install puppeteer-core` i mappen. |
| Värdsimulering | `docs/inbaddningstest.html` | Sida med avsiktligt fientlig CSS (rosa Comic Sans-rubriker, svarta runda knappar, Tailwind-liknande reset) som laddar blocket. Verifierat: inget läcker in eller ut. |
| Skärmdumpar | `docs/skarmdumpar/` | Referensbilder från bygget. |

Sidvikt (js, css och datafilerna som laddas): cirka 341 kB. Miljö: `.venv` med Python 3.12 (uv), paket i `requirements.txt`. Chrome finns på `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`. Lokal server: `python3 -m http.server 8765` i projektroten, eller förhandsvisningen `valgrafik` i `.claude/launch.json`.

Källfiler i projektroten som inte ändras: `majorna-valresultat-2022.xlsx` (kurerad, flikarna RD, RF, KF, Sammanfattning, Metod & källor), `valdistrikt-vastra-gotalands-lan.zip` (Valmyndighetens valgeografi 2022, SWEREF99 TM), `Mandatfordelning-jamforelser-mellan-2018-och-2022.xlsx`, tre råfiler `Roster-per-distrikt-...-2022.xlsx` (gitignorerade, 15 till 20 MB var), `fortidsroster.csv` (mottagna förtidsröster per lokal och dag 2022), tre `statistik-alder-och-kon-...-2022.xlsx` (röstberättigade per distrikt, kön, medborgarskap och åldersgrupp), `slutligt-valresultat-riksdagen-jamforande-statistik-2018-2022.xlsx`. Två redaktionella dokument ligger i mappen men är gitignorerade: `interaktiv-valgrafik-brief.md` (ursprungsbriefen med brainstorm) och `majorna-valanalys-2022.md` (analysen, med tvillingdistrikt och känslighetstest av avgränsningen).

## Siffror som är verifierade

Alla tal nedan är räknade ur `data/valdata_2022.json`, som i sin tur är avstämd mot xlsx:en och mot Valmyndighetens råfiler. Andel = partiets röster delat med giltiga röster. Använd dem som facit när du kontrollerar att ingenting gått sönder.

Hela Majorna, riksdagsvalet 2022: 21 308 giltiga röster, 21 545 röstande, 26 032 röstberättigade, valdeltagande 82,8 % (riket 84,2 %, Göteborg 80,7 %). V 27,2 %, S 25,9 %, MP 15,7 %, SD 10,1 %, M 8,9 %, C 4,3 %, L 4,2 %, KD 2,3 %, Övriga 1,5 %.

Regionvalet: 21 570 giltiga, 21 832 röstande, 26 737 röstberättigade, valdeltagande 81,7 % (Västra Götaland 80,3 %, Göteborg 76,3 %). V 35,8 %, S 25,6 %, MP 8,2 %, M 8,1 %, SD 7,5 %, L 3,8 %, C 3,2 %, KD 2,9 %, D 2,6 %, FI 0,7 %, Övriga 1,7 %.

Kommunvalet: 21 620 giltiga, 21 865 röstande, 26 737 röstberättigade, valdeltagande 81,8 % (Göteborg 76,5 %). V 34,6 %, S 23,1 %, MP 9,6 %, M 8,2 %, SD 7,3 %, L 3,9 %, D 3,9 %, C 2,9 %, KD 2,2 %, FI 1,7 %, K 1,0 %, Övriga 1,5 %.

"Om Majorna bestämde" (jämkade uddatalsmetoden, första delningstal 1,2, 4 %-spärr, på Majornas riksdagsröster): V 99, S 94, MP 57, SD 37, M 32, C 15, L 15, KD under spärren. Verklig riksdag 2022: S 107, SD 73, M 68, V 24, C 24, KD 19, MP 18, L 16. Summa 349 i båda.

"Majorna mot Sverige", riksdagsvalet, skillnad i procentenheter mot riket: V +20,4, MP +10,6, L -0,5, C -2,4, KD -3,0, S -4,4, M -10,2, SD -10,4.

Största parti per distrikt: riksdag V i 14, S i 9; region V i 22, S i 1; kommun V i 23. Valdeltagande i riksdagsvalet spänner från 75,0 % (Svalebo) till 88,4 % (Skytteskogen). V i riksdagsvalet spänner från 15,9 % (Skytteskogen) till 34,5 % (Mariaplan).

Stickprov som testerna använder: Mariaplan riksdag V 34,5 % (287 av 833), Skytteskogen kommun MP 15,2 % (152 av 1 002), Svalebo region V 32,2 % (260 av 808).

Göteborg hade 411 valdistrikt 2022 inklusive uppsamlingsdistriktet. `uppdatera_2026.py` varnar om antalet ändrats, eftersom indelningen då kan ha gjorts om.

## Beslut och varför, i ordning

1. **Kartan är inline-SVG utan Leaflet eller MapLibre.** Ett kartbibliotek kapar sidscrollen på mobil, kräver CDN och blir tungt. 23 polygoner behöver varken zoom eller panorering. Orientering kommer i stället från OpenStreetMap-lagret som hämtas vid byggtid.
2. **Data som `.js` bredvid `.json`.** Sidan fungerar då via file:// och i Beehiiv utan fetch och CORS. Båda skrivs av samma funktion och kan inte glida isär (`kontrollera.py` jämför dem).
3. **Etikettregler på kartan.** Daniel tyckte procenttalen blev "väldigt plottrigt". Nu: på mobil bara partibokstav i Största parti och bara talet i Partistyrka (enheten står i legendtiteln), åtta kurerade hållplatser (tolv på desktop), stadsdelsnamn bara utanför Majorna, tre eller fyra färgsteg med heltalsgränser som matchar etiketterna, valt distrikt får sitt namn på kartan och övriga etiketter dämpas. Enfärgade kartor (kommunvalet, V i alla 23) får inga bokstäver alls på mobil.
4. **Resultatkortet direkt under kartan, legenden ovanför.** Daniel såg inte att något uppdaterades vid tryck och hittade inte tillbaka. Kortet visar namn, "Visa hela Majorna" och topp tre direkt under kartan, med hjälptext innan något valts. Scroll sker bara om kortet är utanför bild (`scrollIntoView` med `block: nearest`). En skärmfast 3 px markering ritas i eget lager ovanpå gatorna.
5. **"Majorna mot Sverige" som sektion och stillbild.** Daniel visade en egen skiss (divergerande staplar mot riket) och ville ha den typen av jämförelse in. Byggd som HTML-staplar (16 px text på mobil), med egen väljare riksdag/region/kommun (mot riket, Västra Götaland respektive Göteborg).
6. **Stillbilder ur sidan.** `?bild=jamforelse` och `?bild=karta` renderar fasta ramar som Chrome headless fotograferar. 2x-upplösning, alt-text ur datan. Bilderna används i mejlet och för delningar; mejl kan aldrig visa interaktivt innehåll.
7. **Native i Beehiiv, inte iframe.** Beehiivs dokumentation säger att HTML-block i sajtbyggaren kör interaktiva widgets och att script bara körs i Preview och Live; Daniel verifierade själv att JavaScript kör på majposten.se/val2026. Inlägg och mejl kan inte (HTML-snippeten i inlägg sparar varken script eller style). Därför: sida på sajten, filer på GitHub Pages, block med `<link>` och `<script src>` inuti containern. Daniel avvisade iframe uttryckligen ("fungerar kass").
8. **Inbäddningsbygget.** `index.html` delades i `valgrafik.js` och `valgrafik.css`; all CSS prefixas med `.mp-val`, inga vh, `document`-referenser bara för att hitta containern. En defensiv grundstil sätter färg, typsnitt, transform och länkstil uttryckligen så att värdsidans globala regler inte slår igenom (verifierat i `docs/inbaddningstest.html`). `data-bas` på containern anger var `data/` ligger, som reserv om `document.currentScript` saknas.
9. **Konfig i `data/konfig.js`** i stället för i koden, så att valnatten bara kräver att `data/` laddas upp. Nycklar: `ar`, `standardAr`, `valnatt`, `adress`, `inbaddad`, `skrivUrl`, `stickyTopp`.
10. **GitHub Pages som host.** Gratis, https, statiskt, ingen Cloudflare. Repot skapades med Daniels `gh`-inloggning (konto wildg14) på hans uttryckliga begäran, namn `val2026`.
11. **Desktoplayout via container queries** (inte media queries, eftersom vi inte vet hur bred Beehiivs sektion är). Från 900 px: kartan vänster med resultatkortet fastnaglat till höger (`position: sticky`, avstånd `stickyTopp`), halvcirkeln bredvid mandattabellen, "Majorna mot Sverige" bredvid "Röstdelningen", brödtext max 680 px. Under 900 px är mobil-layouten orörd.
12. **Prenumerationsknappen borttagen.** Beehiivs eget prenumerationsblock läggs på sidan i stället.
13. **Granskningar.** Två workflows med oberoende granskare gav åtgärdslistorna bakom punkt 3, 4, 5 och 11. Den andra kördes med Sonnet efter Daniels reaktion på kostnaden.

## Så hänger det ihop tekniskt

`valgrafik.js` börjar med `MARKUP` (hela sidans HTML som sträng), `KONFIG` (standardvärden), `PARTIER` (färger och namn), `SPEKTRUM` (halvcirkelns ordning V, S, MP, C, L, KD, M, SD) och `state`. `start()` monterar markupen i `.mp-main`, laddar `konfig`, `distrikt`, `valdata_<år>` för varje år i `KONFIG.ar`, sedan `bakgrund` och `swing_<år>` (utom för basåret), läser URL-parametrar (`distrikt`, `val`, `lage`, `parti`, `ar`, `inbaddad`, `bild`) och renderar allt. `renderKarta()` projicerar WGS84 till en viewBox 1000 enheter bred (ekvirektangulär med cos(lat), ram 0,045 i longitud och 0,16 i latitud), ritar bakgrund, distrikt, etiketter med kollisionskontroll, hållplatser, platsnamn och markering. `renderPanel()` fyller kortets skelett. `divergens()` bygger "Majorna mot Sverige". `renderBild()` bygger stillbildsramarna.

Brytpunkter: `arDesktop()` (containerbredd 600 px) styr kartans typstorlekar och urval; `arBred()` (900 px) styr om kortet ligger bredvid kartan (då ingen scroll vid val). CSS-layouten styrs av `@container` på samma gränser.

Valnattsläget: `KONFIG.valnatt` visar banderoll med räknade distrikt, gråtonar oräknade, räknar Majorna-snittet på räknade distrikt och visar 2022 års staplar dämpade för oräknade distrikt. `swing_<år>` visas som små tal i kortet. Halvcirkeln visar bara Majornas fördelning 2026 (verklig riksdag okänd på valnatten).

Datafilernas schema står i README under Dataschema.

## Historikspåret (separat, pågående, inte mitt)

Parallellt med den här sessionen har en annan session byggt ett historikunderlag i samma mapp: `scripts/historik/` (drygt 30 skript), `data/historik/` (cirka 170 CSV-filer plus `majorna_historik.sqlite`, cirka 27 MB) och `docs/historik/` (`datamodell.md`, `noter/`, `kallor/`). Databasen täcker hela Göteborgs kommun för valen 2002, 2006, 2010, 2014, 2018 och 2022 i alla tre valen, med crosswalk mellan distriktsindelningar (Valmyndighetens FGVAL-tal, officiell mappning 2014 till 2018, Göteborgs stads jämförelsefil 2018 till 2022, geometriskt överlapp), en tidsserie för Majorna, röstberättigade per kön och åldersgrupp 2010 till 2018 och förtidsröster per lokal och dag 2010 till 2018. Den byggs om från grunden av `scripts/historik/bygg_databas.py`.

Att veta:

- Delar av spåret följde med i den första commiten (de fanns i mappen då), resten är ocommittat. Committa inget av det utan att Daniel bett om det, och ta inte bort något. Läs `docs/historik/datamodell.md` och `docs/historik/noter/kedja.md` innan du använder datan.
- Skriptens dokumentation pekar på en venv i en annan sessions scratchpad (`/private/tmp/claude-501/.../f347baf2-.../scratchpad/venv`), som kan vara borta. Prova projektets `.venv` och installera det som saknas.
- Historiken är det naturliga underlaget för idén "Majorna 2002 till 2026" i brainstormen nedan. Hur Majorna avgränsas per år står i `majorna_medlem`-tabellen och i noterna (2006 använder en areametod, 17 distrikt).

## Beslut och frågor som är Daniels

- Etiketten i stillbilderna: "Majposten · Inför valet" fram till valdagen, sedan till exempel "Majposten · Valet 2026" via `--etikett`.
- Vilket bildformat som ska ligga i själva brevet (kvadraten rekommenderad, liggande som og:image).
- Om Beehiiv-sidans egen rubrik gör grafikens rubrik och ingress dubbla: då `"inbaddad": true` i `data/konfig.json` och skriv om `konfig.js` (kommandot står i README under Publicera).
- Om Beehiivs sidhuvud är klibbigt: sätt `stickyTopp` i konfig till sidhuvudets höjd plus marginal.
- Att sektionen som blocket ligger i på Beehiiv är minst cirka 1 000 px bred, annars stannar desktopläget i en spalt.
- Ingressen på sidan är en placeholder som redaktören ska skriva om.

## Startpunkt för nästa session

### Steg 1: städa nuvarande design, med Daniels input

Börja med att fråga Daniel vad han vill ändra, gärna med en kort lista att reagera på. Kandidater som kommit upp eller som jag ser själv:

- Rubrik och ingress i grafiken mot Beehiiv-sidans egen rubrik (dubbelt?), och etiketten "MAJPOSTEN · VALET 2022".
- Halvcirkelns kolumn på desktop har tomrum under sig eftersom tabellen är högre.
- "under spärren" radbryts i mandattabellen i smala spalter.
- Kortets underrad är 16 px sten; Daniel kan vilja ha annan hierarki.
- Kartetiketternas storlek på desktop, hållplatsurvalet (åtta på mobil, tolv på desktop), platsnamnen utanför Majorna.
- Sektionsordningen: Om Majorna bestämde, kartan, tabellknappen, Majorna mot Sverige, Röstdelningen, Om siffrorna.
- Legenden i Partistyrka (tre eller fyra steg) och färgvalen för ljusa partifärger (SD, L mörkas 22 % mot bläck i toppsteget).
- Sidfoten och "Om siffrorna" när Beehiiv redan har sidfot.

Gör ändringarna i `valgrafik.css` och `valgrafik.js`, kör `tests/test_inbaddning.py`, verifiera med `verktyg/sektion.js` på 390 och 1280 px (och `docs/inbaddningstest.html` för läckage), pusha.

### Steg 2: brainstorma vidareutveckling

Daniel vill bryta isär statistiken på fler sätt. Idéer som diskuterats, med datastatus:

- **Förtidsröstningsmätare.** `fortidsroster.csv` har mottagna röster per lokal och dag för 2022 (Majornas bibliotek var stor lokal). Förtidsröstningen 2026 pågår sedan 26 augusti. Om Valmyndigheten publicerar samma fil dagligen kan sidan visa "så många har förtidsröstat i Majorna, dag för dag, mot 2022". Aktuellt varje dag fram till valet. [KOLLA] 2026 års publicering.
- **Valdeltagande som kartläge.** Datan finns i sidan. Ett tredje läge i växeln.
- **Förstagångsväljare och åldersstruktur** per distrikt ur `statistik-alder-och-kon-*.xlsx` (röstberättigade, inte valdeltagande per ålder).
- **Tvillingar och topplistor.** Riksdagsråfilen har alla 6 305 distrikt: varje Majornadistrikt kan få sin närmaste tvilling i Sverige och sin placering per parti (analysen: Mariaplan är plats 13 av 6 305 för V; Majornas tvillingar på områdesnivå är Bagarmossen, Gamlestaden, Möllevången, Rörsjöstaden).
- **Zooma ut till hela Göteborg.** Zip-filen har hela länets polygoner, råfilerna alla distrikt.
- **Historik 2002 till 2026.** Historikspåret ovan. Tidslinje per parti för hela Majorna, per kvarter där kedjan är ren.
- **Röstdelarkartan.** Vilket kvarter röstdelar mest mellan riksdag och kommun.
- **"Om Majorna bestämde" för kommun (81 mandat) och region (149).**
- **Interaktion:** sidan minns ditt kvarter (localStorage), två distrikt sida vid sida, tidslinje att dra i, "veckans kvarter" i brevet via djuplänk.
- Fas 2 från briefen som inte byggts: adresssök, "gissa först"-quiz, distriktskort per kvarter som delningsbild, tvillingkarta, halvcirkeln som Instagram-bild, animerad GIF till mejlet, automatisk pollning på valnatten (rekommendation: manuellt 2026).

Prioritera efter tid till valdagen: det som är aktuellt nu (förtidsröstning, valdeltagande, tvillingar) före det som blir bättre efter valet (historik med 2026 som femte punkt, Göteborgskartan).

## Fallgropar

- `index.html` innehåller inte sidan längre. Ändra i `valgrafik.js` (MARKUP-strängen) och `valgrafik.css`.
- CSS-lintet i `tests/test_inbaddning.py` faller på varje selektor som inte börjar med `.mp-val`, på `vh` och på `position: fixed`.
- Regler inne i `@container` kan aldrig träffa `.mp-val` själv, bara dess barn.
- `swing_2022.js` finns inte och ska inte finnas; basåret hoppas över vid laddning.
- Stillbilderna "Majorna mot Sverige" för 2026 kräver aggregat för riket, Västra Götaland och Göteborg i `valdata_2026.json`, som bara finns när `uppdatera_2026.py` körts med Valmyndighetens filer (inte CSV-vägen).
- Facebook och Beehiiv cachar länkkortet: og-taggarna i `index.html` gäller GitHub-adressen (skalet), medan Beehiiv-sidan har sina egna SEO-inställningar i sajtbyggaren.
- Skärmdumpsverktygen i `verktyg/` behöver `puppeteer-core` installerat i mappen och servern igång.
- Den lokala förhandsvisningsservern kan dö mellan sessioner; starta om den innan verktygen körs.
- Chrome headless via kommandoraden klampar smala fönsterbredder; för mobilbilder används puppeteer med mobilemulering, för stillbilder räcker Chrome direkt (1200 och 1080 px).
