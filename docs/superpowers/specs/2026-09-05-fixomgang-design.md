# Fixomgång 2026-09-05 - designspec

Underlag: Daniels kommentarer 2026-09-05 på kandidatlistan i `docs/HANDOVER.md` (steg 1), plus mätningar på den publicerade sidan majposten.se/val2026 samma dag. Valdag 2026-09-13. Allt nedan följer Majpostens skrivregler (bindestreck med mellanslag, inga utropstecken, inga tre punkter, inga emoji) och Beehiivs regler för HTML-block (`tests/test_inbaddning.py`).

## Daniels beslut

- Etiketten "MAJPOSTEN · VALET 2022" blir "MAJPOSTEN · VALSPECIAL". Sidan ska snart rymma historik och 2026 års siffror; helhetsgreppet på det tas i tankesmedjan efter den här omgången, inte här.
- Jämförelsemarkörerna i kortet "Hela Majorna" är för plottriga med både Göteborg och riket. Bara en jämförelse: riket för riksdagsvalet, Västra Götaland för regionvalet, Göteborg för kommunvalet (samma områden som "Majorna mot Sverige"). När ett distrikt är valt jämförs som nu mot hela Majorna.
- Kortets textrad "Riksdagsvalet 2022: V 27,2 %, S 25,9 %, MP 15,7 %. 21 308 giltiga röster. Valdeltagande 82,8 % (riket 84,2 %)." tillför inget, det visar staplarna. Bort med topp tre-meningen. Valdeltagandet visualiseras inte någon annanstans och stannar som en enda dämpad rad.
- Röstdelningen ska jämföra riksdag, region och kommun för fler partier, och får en tydligare form (se C).
- Kandidaterna 1 till 7 i handoverns lista är godkända. 8 (sidfot och Om siffrorna) rörs inte. 9 till 12 och annat jag ser får fixas.
- Förbered ett samarbetsblock "I samarbete med Majornas Bryggeri" (logga, länk, push för deras valvaka) och en push för hjalpmigrosta.se (rösthjälp på flera språk). Texter och adresser är Daniels; blocket byggs med platshållare och är avstängt tills han fyller i.

## Fynd på den publicerade sidan (majposten.se/val2026, mätt 2026-09-05)

- Beehiiv lägger HTML-blocket i en `<iframe srcdoc>` med samma origin som sidan, bredd 100 % (1 240 px i ett 1 280 px fönster) och höjd som följer innehållet (2 743 px vid laddning, 3 655 px när tabellen fälls ut, tillbaka när den stängs). Innehållet växer alltså fritt.
- Iframens egen `location` är `about:srcdoc` utan query. `?distrikt=14800530` på majposten.se/val2026 når därför aldrig skriptet i dag: djuplänkarna fungerar inte på den publicerade sidan. `window.parent.location` går att läsa och `parent.history.replaceState` fungerar (samma origin). Det egna `history.replaceState` kastar SecurityError (fångas redan).
- `position: sticky` är verkningslös i iframen: inget rullar inuti den (`innerHeight` är hela innehållshöjden). Kortet på desktop följer alltså inte med. Det får accepteras och dokumenteras; kortet ligger ändå bredvid kartan.
- Beehiivs egen meny är `position: sticky`, 89 px hög. `scrollIntoView({block: "start"})` lägger därför kartans överkant under menyn.
- Sidan har ingen egen h1 utanför blocket: grafikens rubrik och ingress dubbleras inte. `inbaddad` behöver inte slås på.

## Ändringar

Numren 1 till 12 syftar på kandidatlistan i HANDOVER (steg 1). Varje grupp görs av en agent i tur och ordning, med tester gröna och en commit per grupp.

### A. Text, kort och djuplänkar

A1. `renderHuvud`: etiketten blir "Majposten · Valspecial" (CSS gör den till versaler). Bildlägets etikett (`renderBild`) ändras inte.

A2. Kortet (`renderPanel`): `#panel-topp` (topp tre-meningen) visas inte längre, varken för Hela Majorna eller för ett distrikt. Texten får finnas kvar i `#panel-live` (skärmläsare) och i `aria-label`. Raden `#panel-sub` blir en enda kort rad i sten: för distrikt "Valdeltagande 83,0 % (Majorna 82,8 %). 833 giltiga röster." och för Hela Majorna "Valdeltagande 82,8 % (riket 84,2 %). 21 308 giltiga röster." Valnattens "X av 23 distrikt räknade" ligger kvar först i raden när det gäller. Elementet `#panel-topp` kan tas bort ur MARKUP; `verktyg/desktop-check.js` och `valjDistrikt` refererar `#panel-topp` för scroll, byt till `#panel`.

A3. Jämförelsemarkör i Hela Majorna: en enda markör per stapel, området ur `jamforelseOmrade(val)` (Sverige, Västra Götaland eller Göteborg). Markören är svart som Majorna-markören i distriktsläget, klassen `.markor.riket`/`.goteborg` ersätts av en gemensam `.markor` (svart) och markörnoten "Snittet i Sverige" / "Snittet i Västra Götaland" / "Snittet i Göteborg". Göteborg visas inte för riksdag och region.

A4. (9) Bara en "Visa hela Majorna": knappen i rubrikraden `#panel-tillbaka` stannar; knappen i `#panel-knappar` tas bort i båda distriktslägena. "Tillbaka till kartan" stannar (döljs redan på desktop).

A5. (10) Inga tre punkter i partinamnen. `.stapel-namn small` får `white-space: normal` och `hyphens: manual`, och en hjälpfunktion `namnMedMjukaBindestreck(namn)` lägger mjukt bindestreck (U+00AD) efter "Vänster", "Social", "Miljö", "Center", "Krist", "Sverige" och i "Feministiskt initiativ" och "Kommunistiska Partiet" räcker mellanslaget. Bara den synliga texten får mjuka bindestreck, `aria-label` behåller namnet rent. Spalten på mobil får vara 104 px så att de flesta namn ryms på en rad.

A6. (12) Hållplatsnamnet ritas inte när det är identiskt med det valda distriktets namn (Mariaplan, Sannaplan). Cirkeln ritas ändå.

A7. (3) `table.mandat td.tal` får `white-space: nowrap` så att "under spärren" inte radbryts.

A8. Djuplänkar i Beehiivs iframe. En hjälpare `sidLocation()` returnerar `window.parent.location` när `window.parent !== window` och läsning lyckas (try/catch), annars `location`. `lasUrl` läser search därifrån, ankarhanteringen i `start()` läser hash därifrån, och `skrivUrl` skriver med `parent.history.replaceState` på förälderns pathname och hash när föräldern nås, annars som i dag. Ingen referens till `parent.document`. `KONFIG.skrivUrl: false` stänger som förut.

A9. Rullning under Beehiivs klibbiga meny: `#karta`, `#karta-sektion`, `#panel`, `#tabell`, `#jamforelse` får `scroll-margin-top: var(--mp-sticky-top, 16px)`. `stickyTopp` i `data/konfig.json` sätts till 105 (89 px meny plus 16). Verifiera i värdsidan nedan att förälderns rullning stannar under menyn; om `scroll-margin-top` inte respekteras genom iframen: rulla föräldern manuellt (`parent.scrollBy`) med samma avstånd i `valjDistrikt` och "Tillbaka till kartan".

A10. Ny värdsida `docs/beehiivtest.html` som efterliknar Beehiiv: klibbig meny 89 px hög, en `<iframe srcdoc>` med blocket (länkarna `../valgrafik.css` och `../valgrafik.js` blir absoluta `/valgrafik.css` och `/valgrafik.js` i srcdoc), bredd 100 %, höjd satt av en `ResizeObserver` på iframens `documentElement`, ingen egen rullning i iframen. Nytt skript `verktyg/beehiiv-check.js`: laddar `http://localhost:8765/docs/beehiivtest.html?distrikt=14800530` i 1280 px, kontrollerar att kortets rubrik är "Mariaplan", klickar Skytteskogen och kontrollerar att förälderns URL fått `distrikt=14800527`, fäller ut tabellen och kontrollerar att iframen växer, trycker "Tillbaka till kartan"-motsvarigheten i 390 px och mäter att kartans överkant ligger minst 89 px ned i fönstret. Skriver JSON och "inga JS-fel".

### B. Layout, karta och färg

B1. (6) Sektionsordning: "Om Majorna bestämde" ligger kvar ovanför kartan (briefens krav). Ändringen är att tabellknappen flyttar in i kartsektionen: `#tabell-sektion` tas bort och `#tabell-knapp` plus `#tabell` läggs sist i `#karta-sektion` (i desktopgriden får de `grid-column: 1 / -1` under kartan och kortet). Ordningen blir header, Om Majorna bestämde, Så röstade ditt kvarter (med tabell), Majorna mot Sverige, Röstdelningen, Om siffrorna, sidfot. `verktyg/shots.js` och andra verktyg som pekar på `#tabell-sektion` uppdateras.

B2. (2) Desktop, `#riksdag`: `align-items: center` i griden så att halvcirkeln centreras mot tabellens höjd, och `#mandat-metod` (räkneexemplet) ligger i kolumn 1 under halvcirkeln i stället för under hela sektionen. Kolumnerna blir `1fr 1fr`.

B3. (5) Kartans typstorlekar bestäms av kartans faktiska bredd i pixlar, inte av 600 px-tröskeln. `renderKarta` mäter `#karta`s `clientWidth` (reserv: containerns bredd) och räknar om måltyper i px till viewBox-enheter: mobil (kartbredd under 600 px) etikett 11, vald 12, namn 11, namnRad2 9,5, kontur 2,4, hållplats 9, plats 9; desktop etikett 15, vald 17, namn 15, namnRad2 12,5, kontur 2, hållplats 12, plats 12,5. `ResizeObserver` renderar om kartan även när bredden ändrats mer än 10 % sedan senaste rendering. Bildläget (`state.bild`) behåller dagens enhetsvärden i `STORLEK.mobil`, stillbilderna ska inte ändras (`tests/test_skapa_bilder.py`). Hållplatsurval och platsnamn behålls.

B4. (7) Partistyrka: toppsteget är alltid partiets egen färg, ingen mörkning mot bläck. För ljusa färger (relativ luminans över 0,35: SD, L) sprids tonerna mer så att stegen skiljer sig: fyra steg [0,22, 0,48, 0,74, 1], tre steg [0,3, 0,62, 1]. Mörka färger som i dag. Fyra steg när spännvidden är minst 6 procentenheter, annars tre. Legendens rutor (`.swatch`) har redan kantlinje.

B5. Testet `tests/test_inbaddning.py` får en kontroll på `scroll-margin-top` i CSS (A9) och på att `valgrafik.js` innehåller `sidLocation` (A8), plus att `konfig.json` har `stickyTopp` som tal.

### C. Röstdelningen: tre val, alla partier

Ersätter lutningsdiagrammet i `renderRostdelning`. Frågan sektionen svarar på: hur röstdelar Majorna mellan riksdag, region och kommun, parti för parti.

- Rader i HTML/CSS (som "Majorna mot Sverige", inte SVG): en rad per parti som har minst 1,0 % i något av valen, sorterade fallande på riksdagsandel, partier utan riksdagsröster (D, FI, K) sist sorterade på kommunandel. Övriga utelämnas.
- Varje rad: partibokstav i fetstil, sedan en gemensam procentaxel (0 till skalans max, max = närmaste 5 % över högsta värdet) där de tre valen ritas som markörer på samma linje och binds ihop av en tunn linje i sten (spannet är röstdelningen). Markörer: riksdag fylld cirkel, region fylld romb, kommun fylld kvadrat, alla i partifärgen med 1 px kantlinje i bläck så att de ljusa färgerna syns. Saknas ett val för partiet ritas ingen markör.
- Till höger om axeln tre tal med tabellsiffror i ordningen riksdag, region, kommun ("27,2  35,8  34,6"), saknat val som "-". Kolumnrubriker ovanför talen ("Riksdag Region Kommun") i 13 px sten, och en legend under rubriken som förklarar markörformerna.
- Mobil (under 600 px container): partibokstav 36 px bred, tal 3 × 44 px, axeln får resten. Desktop: partinamn får plats ("V Vänsterpartiet") och talkolumnerna 3 × 56 px.
- `aria-label` på sektionens grafik med alla värden i klartext. Ingressen: "Så röstar Majorna olika i riksdags-, region- och kommunvalet {år}. Ju längre streck, desto mer röstdelning."
- Finns bara två av valen (valnatten) ritas de två; finns ett eller inget döljs sektionen.
- Bildläget berörs inte.

### D. Samarbete och rösthjälp

D1. Konfig, nya nycklar i `data/konfig.json` och `scripts/schema.KONFIG_STANDARD` (skriv om `konfig.js` med `schema.skriv_konfig`):

```json
"samarbete": { "visa": false, "namn": "Majornas Bryggeri", "text": "I samarbete med", "lank": "", "logga": "",
               "valvaka": { "visa": false, "rubrik": "Valvaka på Majornas Bryggeri", "text": "[KOLLA] Tid, plats och vad som händer.", "lank": "" } },
"hjalp":     { "visa": false, "rubrik": "Behöver du hjälp att rösta?", "text": "hjalpmigrosta.se förklarar hur valet går till, på flera språk.", "lank": "https://hjalpmigrosta.se", "lanktext": "Till hjalpmigrosta.se" }
```

`logga` är en adress relativt `BAS` (till exempel `bilder/majornas-bryggeri.png`) eller absolut. Tom logga ger bara text. Alla `lank` är tomma platshållare tills Daniel fyller i; med tom länk renderas texten utan länk.

D2. Markup och rendering (`renderSamarbete`, anropas i `renderAllt`): i `header.topp` efter ingressen en rad `.samarbete` med loggan (max-height 44 px, `alt` = namn, länkad om `lank` finns) och texten "I samarbete med Majornas Bryggeri" (namnet länkat). Direkt efter headern ett `.rutor`-block med upp till två rutor (`.ruta`): valvakan och rösthjälpen, var och en med rubrik i Georgia 20 px, text 16 px och länk. Rutorna har 1 px kantlinje i linje-färgen på papper, ingen skugga, ingen ikon. På desktop (900 px) ligger rutorna sida vid sida, på mobil under varandra. Allt döljs med `visa: false`; hela `.rutor` döljs när ingen ruta visas. Bildläget och `inbaddad` visar inte samarbetsraden men rutorna visas även i `inbaddad`.

D3. Tester: `tests/test_inbaddning.py` kontrollerar att `konfig.json` har `samarbete.visa` och `hjalp.visa` som booleaner och att `uppdatera_2026.py --valnatt` bevarar dem (utöka befintligt test). `scripts/schema.py` får nycklarna i `KONFIG_STANDARD`.

D4. README: nytt avsnitt "Samarbete och rösthjälp" med nycklarna, hur loggan läggs i `bilder/` och hur man slår på blocken.

### E. Dokumentation

README: Beehiiv-avsnittet får fynden ovan (iframe, djuplänkar via föräldern, sticky verkningslös, `stickyTopp` som rullmarginal, `docs/beehiivtest.html`), Mappen-listan och Designval uppdateras (kortet, markören, Röstdelningen, tabellknappen i kartsektionen, typstorlek efter kartbredd, Partistyrkans färger). `verktyg/README.md` får `beehiiv-check.js`. `docs/HANDOVER.md`: nytt statusavsnitt 2026-09-05 med det som ändrats, nya beslut (14 och framåt) och att steg 1 är gjort; startpunkten blir tankesmedjan.

## Verifiering

- `.venv/bin/python -m pytest -q` grön efter varje grupp (venv: `/Users/daniel/code/Temp/.venv/bin/python`, körs från worktreen).
- `node verktyg/skal-check.js`, `node verktyg/vard-check.js`, `node verktyg/desktop-check.js http://localhost:8765/docs/inbaddningstest.html UT.png`, `node verktyg/beehiiv-check.js`, med servern `python3 -m http.server 8765 --bind 127.0.0.1` igång i worktreen (kör `NODE_PATH=verktyg/node_modules` om skriptet ligger utanför `verktyg/`).
- Skärmdumpar 390 och 1280 px av hela sidan, kartsektionen med Mariaplan valt, Partistyrka SD kommun, Röstdelningen, Om Majorna bestämde, samt `docs/beehiivtest.html` i 1280 px. Samarbetsblocken granskas med `visa: true` lokalt (ändringen i `data/konfig.*` återställs efteråt).
- Facit-siffror i HANDOVER ska synas oförändrade: Mariaplan riksdag V 34,5 %, Skytteskogen kommun MP 15,2 %, Svalebo region V 32,2 %, Hela Majorna riksdag V 27,2 %.

## Utanför den här omgången

Helhetsgreppet för historik och 2026 (årväljare, tidslinjer, vad som ska synas före och efter valdagen), Röstdelningen som karta, sidfot och Om siffrorna mot Beehiivs sidfot, halvcirkelns plats i förhållande till kartan (Daniels beslut; briefen sade ovanför). Tas i tankesmedjan.
