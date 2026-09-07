# Handover: Så röstade Majorna

Skriven 2026-09-04 av den session som byggde grafiken, uppdaterad 2026-09-07 efter valnattsomgången och samma dag igen efter att historikplanen byggts klart (task 6 till 10). Läs den här filen i sin helhet innan du gör något. Valdagen är 2026-09-13.

## Läs i den här ordningen

1. Den här filen.
2. `README.md` i projektroten: körordning, Beehiiv, valnatten, historiken, stillbilder, dataschema.
2b. `docs/valnatt-korschema.md` om det är valveckan: allt som ska köras lördag, söndag och dagarna efter.
3. `docs/superpowers/specs/2026-09-03-majorna-valgrafik-design.md` (ursprunglig spec) och `docs/superpowers/plans/2026-09-03-majorna-valgrafik.md` (plan). Delvis inaktuella: kartan är inte längre i `index.html` utan i `valgrafik.js`, se nedan.
3b. `docs/superpowers/plans/2026-09-07-tillagg-under-bygget.md`: besluten som ändrade valnattsplanen och historikplanen under bygget, gäller före plantexten där de skiljer sig. Planfilerna under `docs/superpowers/plans/` är annars historik och ändras inte.
4. Minnesfilerna i `/Users/daniel/.claude/projects/-Users-daniel-code-Temp/memory/` (index i `MEMORY.md`): vem Daniel är, Majpostens skrivregler, Beehiiv-planen, modellval för subagenter.
5. `docs/historik/datamodell.md` och `docs/historik/noter/*.md` om du ska röra det underliggande historikspåret (se avsnittet Historikspåret) - för hur sektionen "Majorna sedan 2006" på sidan fungerar räcker README och det här dokumentet.
6. `docs/inbaddningstest.html` och `verktyg/README.md` när du ska verifiera i webbläsare.

## Vad projektet är

En interaktiv valgrafik för nyhetsbrevet Majposten (Daniel Emgård, hyperlokalt veckobrev om Majorna i Göteborg, publicerat via Beehiiv). Grafiken visar valresultatet 2022 för de 23 valdistrikten i klassiska Majorna (koder 14800526 till 14800548, valkrets Västra Centrum, primärområdena Majorna, Stigberget, Kungsladugård och Sanna), i riksdags-, region- och kommunvalet, och är byggd för att ta emot 2026 års siffror på valnatten utan kodändring.

Grafiken ligger native på en sida i Beehiivs sajtbyggare, **majposten.se/val2026**, som ett HTML-block. Koden och datan hostas på GitHub Pages: repo **github.com/wildg14/val2026**, adress **https://wildg14.github.io/val2026/**. Läsaren ser aldrig GitHub-adressen. Ingen iframe: Daniel avvisade iframe uttryckligen.

Projektmappen är `/Users/daniel/code/Temp` (git, branch `main`, remote `origin` = GitHub). Arbete sker i grenar under `.claude/worktrees/` som mergas till `main`; se Status 2026-09-07 nedan för hur det påverkar valnattsomgången. Publicering av kodändringar är `git push origin main`; Pages bygger själv inom en minut. Beehiiv-sidan behöver aldrig röras för uppdateringar.

## Arbetsregler som gäller i det här projektet

- **Inga påhittade siffror.** Allt räknas ur datafilerna, och `scripts/kontrollera.py` stämmer av `data/valdata_2022.json` mot `majorna-valresultat-2022.xlsx` (1 149 kontroller). Ändra aldrig ett tal för hand. Kör `.venv/bin/python -m pytest -q` (325 tester, alla gröna i den här mappen; i en klon utan Valmyndighetens råfiler, genrep-filerna och pem-nycklarna hoppas några över) före och efter ändringar.
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
| Grafiken | `valgrafik.js` (cirka 100 kB) | Renderar allt inuti `<div class="mp-val" id="valgrafik">`: rubrik, samarbetsrad och rutor (valvaka, rösthjälp), "Om Majorna bestämde", kartan med flikar och lägen, resultatkortet, tabellknappen och tabellen (i samma sektion som kartan), "Majorna mot Sverige", "Röstdelningen" (HTML-rader med alla tre valen per parti, inte lutningsdiagram), "Majorna sedan 2006" (historiksektionen), "Om siffrorna", sidfot. Läser `data/konfig.js` och datafilerna från adressen i `data-bas` eller skriptets egen mapp. |
| Stil | `valgrafik.css` (cirka 25 kB) | All CSS scopad till `.mp-val`. Två layouter via container queries: under 900 px containerbredd en spalt (mobil), från 900 px två kolumner. 600 px styr kartans detaljnivå (kartans typstorlekar räknas löpande om efter kartans faktiska pixelbredd, inte bara vid tröskeln). |
| Skal | `index.html` | Tunt skal för lokal visning, bildläge och skärmdumpar. Open Graph-taggar med adressen. |
| Data | `data/valdata_2022.json` + `.js`, `data/distrikt_2022.*` och `data/distrikt_2026.*` (en geometrifil per år i konfigens `ar`), `data/bakgrund.json` + `.js`, `data/konfig.json` + `.js` | `.js`-filerna är identiska kopior av `.json` som sidan laddar via `<script>` (fungerar via file:// och kräver ingen CORS). Skrivs av `scripts/schema.py`, atomiskt. På valnatten tillkommer `valdata_2026.*` och `swing_2026.*`, och `data/valnatt/` (gitignorerad) med Valmyndighetens hämtade filer. Sedan historikplanen finns också `data/historik.*` (områdesserien 2006 till 2022), `data/swing_2022.*` och `data/distrikt_2006.*` (laddas vid start), samt `data/valdata_<år>.*` och `data/distrikt_<år>.*` för 2006, 2010, 2014 och 2018 (byggda, laddas bara om året läggs i konfigens `ar`). |
| Pipeline | `scripts/bygg_data.py`, `scripts/kontrollera.py`, `scripts/valmyndigheten.py`, `scripts/mandat.py`, `scripts/geo.py`, `scripts/schema.py`, `scripts/bygg_geo.py`, `scripts/bygg_historik.py` | xlsx + zip till data/, med fem kontrollsteg. `bygg_geo.py` skriver `data/distrikt_<år>` ur Valmyndighetens valgeografi och jämför unionsytan mellan åren. `bygg_historik.py` läser `data/historik/majorna_historik.sqlite` skrivskyddat och skriver `historik`, `swing_2022`, `distrikt_<år>` och `valdata_<år>` för historikåren; `kontrollera.py --historik` stämmer av `historik.json` mot `data/valdata_2022.json`, utan att röra databasen. |
| Valnatten | `scripts/hamta_2026.py`, `scripts/valnatt.py`, `scripts/uppdatera_2026.py` | `hamta_2026.py` hämtar de tre zip-filerna, kontrollerar md5 mot `index.md5` och signaturerna mot Valmyndighetens certifikat, packar upp till `data/valnatt/<tidsstämpel>/` och pekar om `senaste`. `valnatt.py` mappar JSON till sidans schema (distrikt, aggregat, riksdagens mandat). `uppdatera_2026.py --hamta` kör hela kedjan till `valdata_2026` + `swing_2026`; `--repetera` reproducerar 2022 exakt ur 2022 års råfiler; xlsx- och CSV-vägarna finns kvar som reservvägar; `--valnatt` uppdaterar `data/konfig`. |
| Bakgrund | `scripts/hamta_bakgrund.py` | Gator, spårväg, hållplatser, vatten, parker och platsnamn från OpenStreetMap via Overpass. Valfritt lager. |
| Stillbilder | `scripts/skapa_bilder.py`, `bilder/` | Chrome headless renderar `index.html?bild=jamforelse` och `?bild=karta` i 1200 x 630 och 1080 x 1080, 2x, med alt-text i `.txt`. |
| Tester | `tests/` | 325 tester: mandatberäkning, parser mot råfiler, geometri (2022 och 2026, byte-identitet mot de committade filerna), schema och swing, kontrollskript, bygge, bakgrund, uppdatera (JSON-, xlsx- och CSV-vägarna, spärrarna), hämtning och signaturer, valnattsmappningen mot genrep-filerna, stillbilder, Beehiiv-regler (inklusive scroll-margin-top, `sidLocation`, `stickyTopp` och samarbete/hjälp-nycklarna), historikbygget (`tests/test_bygg_historik.py`: områdesserien, swing 2022, geometrin per år, valdata per år, `kontrollera.py --historik`), `forbered_tvaar.py` (`tests/test_forbered_tvaar.py`: `--kf-raknade`, `--partiell`, `--status`, `--utan-parti` och felvägarna). |
| Verktyg | `verktyg/` | Puppeteer-skript för skärmdumpar och mätningar (se `verktyg/README.md`), bland dem `beehiiv-check.js` mot `docs/beehiivtest.html`, `skal-check.js`, `tvaar-check.js` och `historik-check.js` mot testsidorna som `forbered_tvaar.py` bygger under `tmp/`. Kräver `npm install puppeteer-core` i mappen. |
| Värdsimulering | `docs/inbaddningstest.html` | Sida med avsiktligt fientlig CSS (rosa Comic Sans-rubriker, svarta runda knappar, Tailwind-liknande reset) som laddar blocket. Verifierat: inget läcker in eller ut. |
| Värdsimulering | `docs/beehiivtest.html` | Efterliknar Beehiivs sajtbyggare: klibbig meny 89 px hög, blocket i en `iframe srcdoc`, höjd satt av `ResizeObserver`. Används för att testa djuplänkar och rullning under menyn (se Beehiiv-avsnittet i README och `verktyg/beehiiv-check.js`). |
| Skärmdumpar | `docs/skarmdumpar/` | Referensbilder från bygget. |

Sidvikt (js, css och datafilerna som laddas för ett år): cirka 404 kB, varav bakgrundslagret 228 kB (samma `du`-körning). På valnatten tillkommer `distrikt_2026.js`, `valdata_2026.js` och `swing_2026.js`, tillsammans 52 kB. Historiksektionen laddar dessutom `historik.js` (25 kB), `swing_2022.js` (6,8 kB) och `distrikt_2006.js` (9,9 kB) vid start, tillsammans 48 kB i samma blockavrundade `du`-mått som ovan (404 + 48 = 452 kB, README:s totalsumma); ett historikår i `KONFIG.ar` kostar därutöver cirka 42 kB (2018 års valdata och polygoner). Miljö: `.venv` med Python 3.12 (uv), paket i `requirements.txt`. Chrome finns på `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`. Lokal server: `python3 -m http.server 8765 --bind 127.0.0.1` i projektroten, eller förhandsvisningen `valgrafik` i `.claude/launch.json`.

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
9. **Konfig i `data/konfig.js`** i stället för i koden, så att valnatten bara kräver att `data/` laddas upp. Nycklar: `ar`, `standardAr`, `valnatt`, `adress`, `inbaddad`, `skrivUrl`, `stickyTopp`, samt (sedan 2026-09-05) `samarbete` (med nästlad `valvaka`) och `hjalp` för de redaktionella blocken, se beslut 18 och README.
10. **GitHub Pages som host.** Gratis, https, statiskt, ingen Cloudflare. Repot skapades med Daniels `gh`-inloggning (konto wildg14) på hans uttryckliga begäran, namn `val2026`.
11. **Desktoplayout via container queries** (inte media queries, eftersom vi inte vet hur bred Beehiivs sektion är). Från 900 px: kartan vänster med resultatkortet fastnaglat till höger (`position: sticky`, avstånd `stickyTopp`), halvcirkeln bredvid mandattabellen, "Majorna mot Sverige" bredvid "Röstdelningen", brödtext max 680 px. Under 900 px är mobil-layouten orörd.
12. **Prenumerationsknappen borttagen.** Beehiivs eget prenumerationsblock läggs på sidan i stället.
13. **Granskningar.** Två workflows med oberoende granskare gav åtgärdslistorna bakom punkt 3, 4, 5 och 11. Den andra kördes med Sonnet efter Daniels reaktion på kostnaden.
14. **Etiketten är alltid "Majposten · Valspecial"**, oberoende av vilket år som visas (2026-09-05, Daniels beslut). Sidan ska snart rymma flera år; helhetsgreppet på etiketten och årväljaren tas i tankesmedjan, inte i en löpande fix.
15. **En enda jämförelsemarkör i "Hela Majorna"**, inte två. Riket för riksdagsvalet, Västra Götaland för regionvalet, Göteborg för kommunvalet - samma områden som "Majorna mot Sverige" använder, i stället för att visa både Göteborg och riket samtidigt (Daniel: "för plottrigt").
16. **Kortets topp tre-mening borttagen.** Den upprepade det staplarna redan visar. Kvar blir en enda dämpad rad: valdeltagande (med jämförelseområdet inom parentes) och antal giltiga röster.
17. **"Röstdelningen" ersatt helt.** Det gamla lutningsdiagrammet (SVG) byttes mot HTML-rader i samma stil som "Majorna mot Sverige": en rad per parti med markörer för riksdag (cirkel), region (romb) och kommun (kvadrat) på en gemensam procentaxel, plus exakta tal. Andelarna räknas ur en kohort av distrikt som är räknade i alla val som visas, inte ur de färdiga aggregaten, så att valnattens ofullständiga data inte blandar ihop olika distriktsmängder.
18. **Samarbetsblock och rösthjälp förberedda, avstängda.** En rad "I samarbete med Majornas Bryggeri" i sidhuvudet och upp till två rutor (valvaka, hjalpmigrosta.se) direkt under, allt styrt av `samarbete`/`hjalp` i `data/konfig.json` med `visa: false` som standard. Texter är Daniels platshållare tills han fyller i riktiga adresser och tider.
19. **Beehiivs `iframe srcdoc` kartlagd och kompenserad.** Djuplänkar och URL-skrivning går via `window.parent.location` när föräldern går att nå (`sidLocation()`/`sidHistory()`), eftersom iframens egen adress är `about:srcdoc`. `stickyTopp` höjdes från 16 till 105 px (Beehiivs klibbiga meny är 89 px) och används även som `scroll-margin-top`, eftersom `position: sticky` är verkningslöst inuti iframen (inget rullar där). Se README-avsnittet Beehiiv och `docs/beehiivtest.html`.

20. **Valnatten läser Valmyndighetens JSON, inte xlsx.** 2026 publiceras resultatet som zip-filer med JSON på `resultat.val.se/resultatfiler/val2026/`. `scripts/hamta_2026.py` hämtar de tre filer Majorna behöver (riksdagen för hela landet, regionvalet för Västra Götaland, kommunvalet för Göteborg), kontrollerar md5 mot `index.md5` och signaturerna mot Valmyndighetens certifikat, och packar upp till `data/valnatt/<tidsstämpel>/` med `senaste` som symlänk. `scripts/valnatt.py` mappar formatet till sidans schema. Xlsx- och CSV-vägarna finns kvar som reservvägar. Filval sker på katalog plus suffix, aldrig på hela filnamnet: prefixet skiljer sig mellan genrep och skarpt.
21. **Ett parti som inte förekommer i filen saknas i datan.** Det skrivs varken som 0 eller markeras. I den preliminära filen betyder det att partiet inte är rapportparti (rösterna ligger i Övriga), i den slutliga att det inte fick någon röst i distriktet. Anledningen: planens första kod fyllde alla nyckelpartier med nollor, vilket gav påhittade förändringstal (K -1,0 procentenheter i kommunvalet). Sidan hoppar över partiet i staplar, kort och swingrad i stället.
22. **Tom import är en varning, inte ett fel.** Mellan 20.00 och cirka 21.00 är inget Majornadistrikt räknat. Filerna skrivs då med `meta.valnatt.raknade: 0` och konfigen slår över i valnattsläge, så att sidan är levande från början. Spärren mot *färre* räknade distrikt än den befintliga filen finns kvar och gäller per val.
23. **Valdeltagandet i aggregaten räknas mot röstberättigade i räknade distrikt** (`antalRostberattigadeIRaknadeValdistrikt`, med `antalRostberattigade` som reserv). Med hela områdets väljarkår som nämnare visade riket 12,5 procent klockan 20.30. Av samma skäl tar toppsvarets mening med riket först när riket är färdigräknat, och "Majorna mot Sverige" och halvcirkeln skriver ut hur långt jämförelseområdet kommit.
24. **Jämförelseaggregat och mandat får aldrig stoppa distriktsimporten.** Går aggregat- eller mandatfilen inte att läsa blir det en varning och ett tomt aggregat för valet; distrikten ligger i en annan fil och ska in ändå.
25. **Riksdagens verkliga mandat läses redan på valnatten**, ur mandatfördelningsfilen, även innan något Majornadistrikt är räknat. Halvcirkeln jämför alltså mot riksdagen direkt, med förbehållet "Preliminär fördelning, riket: X av Y distrikt räknade." och ordet "riksdagen" i stället för "den verkliga riksdagen" så länge räkningen är preliminär.
26. **Geometri per år.** `data/distrikt.geojson` heter nu `data/distrikt_2022.geojson`, och `data/distrikt_2026.*` byggs av `scripts/bygg_geo.py` ur Valmyndighetens valgeografi. Sidan laddar `distrikt_<år>` för varje år i konfigen och ritar alla år i en gemensam kartram. Ytkontrollen tar unionen av de faktiska polygonerna i EPSG:3006 och jämför symmetrisk differens (tröskel 10 kvadratmeter), inte summan av avrundade `area_km2` som är blind för luckor och överlapp.
27. **Swing på kohort, med `samma_yta` som argument.** `schema.swing` ger `distrikt` (räknade och jämförbara), `ej_jamforbara` (med meningen kortet visar), `majorna` och `kohort`. Hela områdets tal jämförs mot hela basåret bara när alla distrikt är räknade och antalet stämmer; `samma_yta=True` intygar i stället att området täcker samma yta båda åren (historikplanen, 23 mot 22 distrikt 2018).
28. **Kohorttexten säger "räknat på N jämförbara distrikt av 23"**, inte "N av 23 distrikt" som specen skrev. Kohorten räknar distrikt som är både räknade och jämförbara, medan statusraden räknar alla räknade: samma tal på båda ställena hade fått läsaren att tro att bara N var räknade.
29. **Toppsvaret och statusraden ersätter banderollen och ingressen.** Sidhuvudet svarar på frågan direkt: en statusrad och under den de fyra största partierna i riksdagsvalet som korta staplar. Valdeltagandemeningen under staplarna visas först när hela Majorna är färdigräknad i det valet (och tar med riket bara när riket självt är färdigräknat); fram till dess är det bara de fyra staplarna. Höjderna är reserverade (statusraden 52 px under 600 px containerbredd, 26 px däröver; toppsvaret 208 px; årväljarens rad 44 px så fort konfigen listar två år) så att sidhuvudet inte hoppar när datan kommer. "Ladda om" är en `<button>` med länkutseende, inte en länk.
30. **Kortets rad "Hur har det ändrats" har tre grenar.** Jämförbart distrikt får tal för de tre största partier som har tal i swingfilen; omritat distrikt får meningen om omritningen plus hela Majornas tal för sitt största parti; Hela Majorna får talen med kohorttexten. Ett parti utan tal i swingfilen visas inte, aldrig som "0,0". Skärmläsarraden slutar med omritningsmeningen.
31. **`--tvinga` ersätter hela filen och låser upp tre spärrar samtidigt** (färre räknade distrikt, testdata över skarp data, testdata till repots `data/`). Den slår aldrig ihop den nya filen med den gamla: val som saknas i den nya blir tomma. Efter ett stopp är kommandot `.venv/bin/python scripts/uppdatera_2026.py --valnatt-mapp data/valnatt/senaste --tvinga --status preliminar`, eftersom `--hamta` med samma filer bara ger kod 3.
32. **`--bara-om-nytt` jämför md5 för de tre valda filerna**, inte hela indexet: hela landets index ändras varje minut oavsett Majorna, så flaggan var verkningslös förut. Ändras en fil under hämtningen gör skriptet ett återförsök med paus innan det ger upp.
33. **Testdata märks och stoppas.** Genrep-filerna har `test: true`, som följer med till `meta.test` i utdatan. Att skriva sådana filer till repots `data/` kräver `--tvinga`.

## Status 2026-09-05: fixomgången efter Daniels genomgång

Daniel gick igenom den tidigare versionens kandidatlista (se git-historiken för hur "Startpunkt för nästa session" såg ut innan den här omgången) och den publicerade sidan majposten.se/val2026, och gav en spec med sina beslut: `docs/superpowers/specs/2026-09-05-fixomgang-design.md`. Fem agenter körde specens grupper A till E i tur och ordning, var och en med gröna tester och en egen commit (`git log --oneline 8ae5f22..dfdfcbc` visar alla fem: Grupp A till D plus dokumentationsgruppen E).

**Steg 1 (städa nuvarande design) är klart.** Utöver besluten 14 till 19 ovan: kortets dubblettknapp "Visa hela Majorna" borttagen (bara en kvar, i rubrikraden), mjuka bindestreck i långa partinamn så de inte klipps med tre punkter, "under spärren" radbryts inte längre i mandattabellen, hållplatsnamn som är identiska med det valda distriktets namn ritas inte längre ovanpå kartan, tabellknappen och tabellen flyttade in i kartsektionen (ingen egen sektion), halvcirkelns räkneexempel ligger under halvcirkeln på desktop i stället för under hela sektionen, kartans typstorlekar räknas efter kartans faktiska pixelbredd, Partistyrkans toppsteg är alltid partiets egen färg med spridda toner för ljusa partier, klick på en gata eller hållplats träffar distriktet under (`pointer-events: none` på bakgrundslagren), tangentbordsnavigering (piltangenter, roving tabindex) i flikar och knappgrupper, och flera datafel som Codex-granskningen hittade i UI-lagret (fel standardår vid start, URL-parametrar som föll bort vid klick, jämförelsesektionen som doldes i onödan, valnattsbanderollen som kunde visa fel antal räknade distrikt).

**Fynd på den publicerade Beehiiv-sidan** (mätt 2026-09-05, se beslut 19 och README-avsnittet Beehiiv): blocket ligger i en `iframe srcdoc`, samma ursprung, höjden följer innehållet fritt. Djuplänkar fungerade inte tidigare eftersom iframens egen adress saknar query - det är fixat via `sidLocation()`. `position: sticky` fungerar inte inuti iframen, så resultatkortet följer inte med vid rullning på desktop; det är känt och accepterat, inte fixat (kortet ligger ändå bredvid kartan). Beehiivs egen meny är klibbig och 89 px hög, vilket är därför `stickyTopp` nu är 105.

En efterföljande granskningsomgång (samma dag) rättade: det klibbiga kortet som la sig över tabellknappen och tabellen på desktop (kartan, legenden och kortet flyttade in i `#karta-yta`), markörerna i Röstdelningen som täckte varandra (tre höjder kring linjen), talspalten i Röstdelningen som klistrade ihop kolumnrubrikerna (174 px och 8 px kolumnmellanrum), namnspalten i kortet på desktop (160 px, Sverigedemokraterna ryms på en rad), valnattsraden i kortet som räknade räknade distrikt ur `meta` i stället för ur distriktsdatan, URL-parametrarna som lästes ur iframens egen adress i stället för ur värdsidans, och `verktyg/vard-check.js` som kraschade på `getComputedStyle(null)` eftersom grafiken inte har någon länk i standardläget.

**Vad som inte rördes i den här omgången:** datafelen som Codex-granskningen hittade i data- och byggpipelinen (2026 års resultatfiler är ZIP med JSON inte xlsx, distriktsgeografin har ändrats hos Valmyndigheten och nio Majornadistrikt är "Ej jämförbart", CSV-mallen går inte att läsa tillbaka, swing för hela Majorna jämför olika distriktsmängder, negativa röster och okända partikoder accepteras, tom import skriver över befintlig data, `kontrollera.py` täcker inte aggregat och mandat, `skapa_bilder.py` kan märka fel år) - de hör till en egen valnattsomgång, se Startpunkt nedan. Historikspårets egna Codex-fynd (18 till 20) hör till den andra sessionen och rörs inte här heller.

## Status 2026-09-07: valnattsomgången är byggd

Planen `docs/superpowers/plans/2026-09-05-valnatt-2026.md` är genomförd, task 1 till 12, i 31 commits (`git log --oneline 5a1f40e..bd163ae`). Varje task kördes av en egen agent med testerna först, granskades av en oberoende agent och rättades innan nästa startade. Hela omgången ligger på grenen `claude/valnattsplanen-superpowers-b46290`, inte på `main`, tills den mergas dit; `docs/valnatt-korschema.md` förutsätter den mergen (grenkontrollen är första punkten under Lördag 12 september). Vad som byggdes:

- **`scripts/valnatt.py`** (task 1 till 3): läser Valmyndighetens JSON 2026. `las_rostfordelning` ger de 23 distrikten med röster, giltiga, röstande, röstberättigade och jämförbarhet; `aggregat_2026` ger riket, Västra Götaland och Göteborg ur mandat- och summeringsfilerna; `riksdag_verklig` ger riksdagens mandat till halvcirkeln.
- **`scripts/hamta_2026.py`** (task 4): hämtar `index.md5` och de tre zip-filerna, kontrollerar md5 och signaturer, packar upp per körning, `senaste` som atomärt bytt symlänk, `--bara-om-nytt`, `--genrep`, `--lokal`, `--utan-signatur`.
- **`scripts/schema.py`** (task 5): `swing()` med jämförbarhet, `ej_jamforbara`, kohort och `samma_yta`; atomisk skrivning; konfignycklarna `valdag`, `toppsvar`, `historik`.
- **`scripts/uppdatera_2026.py`** (task 6 och 7): JSON-vägen `--valnatt-mapp` och `--hamta`, spärrar mot tom och mindre import och mot testdata över skarp data, jämförbarhet per distrikt ur båda källorna, och en CSV-reservväg som går att läsa tillbaka (radnummer i felen, kontroll av röstberättigade på slutläget, kompletteringsläget tillsammans med JSON-vägen).
- **`scripts/bygg_geo.py`, `scripts/geo.py`** (task 8): `data/distrikt_<år>` ur Valmyndighetens valgeografi, med geometrisk ytkontroll mellan åren.
- **`valgrafik.js` och `valgrafik.css`** (task 9 till 11): geometri per år i en gemensam kartram, swing för alla år, toppsvar med statusrad och "Ladda om", och kortets rad "Hur har det ändrats".
- **Dokumentation** (task 12): README-avsnittet Valnatten omskrivet, `docs/valnatt-korschema.md` som körschema, den här filen.
- **Övergångskopian `data/distrikt.js`** (efter slutgranskningen): samma data som `distrikt_2022.js` men under nyckeln `distrikt`, kvar åt läsare som har den gamla `valgrafik.js` cachad (GitHub Pages cache kan dröja tio minuter) och annars skulle fått "Datafilerna kunde inte laddas" direkt efter mergepushen. Filen är statisk och tas bort efter valet, se Fallgropar.

**Torrkörningen är gjord** (2026-09-07, mot nätet): `uppdatera_2026.py --hamta --genrep --ut /tmp/torr --status preliminar` gav md5 och signatur ok för de tre filerna, 23/23 räknade distrikt i alla tre valen, 14 jämförbara mot 2022, en namnvarning (Sandarna mot Sandarne) och en TESTDATA-varning, inga FEL. En andra körning gav `Inget nytt att läsa in.` och kod 3. `hamta_2026.py --ut /tmp/torr2` mot den skarpa adressen gav `FEL: https://resultat.val.se/resultatfiler/val2026/index.md5 svarar 404: resultatfilerna publiceras först på valkvällen` och kod 1, som väntat. Testsidan byggd av torrkörningens data gav `TVÅÅRSKONTROLL OK`. Utskrifterna står som facit i `docs/valnatt-korschema.md`.

**Av Codex-fynden om data** (listade i den tidigare startpunkten) är JSON-formatet, distriktsgeografin, CSV-mallen, swingens distriktsmängder, negativa röster och okända partikoder samt den tomma importen åtgärdade. Kvar är två (planens "Codex 16 och 17"): `scripts/kontrollera.py` täcker fortfarande bara distriktsraderna, inte aggregat och mandat, och `scripts/skapa_bilder.py` kan märka en bild med fel år. Ingen av de två filerna rördes i den här omgången.

## Avvikelser från planen

Under bygget fattade kontrollern beslut som ändrade planen. De skrevs som sju tilläggsdokument (`tillagg-ej-redovisade`, `-aggregat`, `-hamta`, `-swing`, `-uppdatera`, `-geo`, `-js`) och gällde före plantexten där de skiljer sig. Dokumenten ligger samlade i `docs/superpowers/plans/2026-09-07-tillagg-under-bygget.md`, tillsammans med historikplanens tillägg; den här filen sammanfattar dem. Planfilerna under `docs/superpowers/plans/` ändrades inte, de är historik. Sammanfattning av det som avviker:

- **Partier som inte redovisas** fylls inte med nollor (beslut 21). Planens kod gjorde det.
- **Tom import** stoppar inte kvällens första körning (beslut 22). Planen hade det som ett fel, vilket hade gjort att konfigen aldrig slog över i valnattsläge.
- **Valdeltagandet i aggregaten** räknas mot röstberättigade i räknade distrikt (beslut 23). Planen nämnde inte fältet.
- **Aggregat och mandat** stoppar inte distriktsimporten (beslut 24), och riksdagens mandat läses redan på valnatten (beslut 25). Planen hade halvcirkeln utan verklig riksdag på valnatten.
- **`--hamta`** bygger sitt argv fullständigt (`--ut`, `--bara-om-nytt`); planens kod gjorde grenen för kod 3 död.
- **Swingens `samma_yta`** och kohorttexten (beslut 27 och 28) skiljer sig från specens formulering.
- **Geometrin:** planens steg 6 väntade "4.6554 km²" och "+146 kvadratmeter"; verkligheten är samma yta båda åren och 0 kvadratmeters skillnad. `bygg_geo.py --ar 2026 --jamfor data/distrikt_2022.geojson` skriver "unionsyta 4655452 kvadratmeter" och "skillnad +0 kvadratmeter, symmetrisk differens 0 kvadratmeter", och utdatan är byte-identisk med de committade filerna (ett test vaktar det för båda åren). Elva distrikt skiljer sig geometriskt, inte nio: Marieberg (14800542) och Karl Johan (14800544) har bytt ett kvarter på 533 kvadratmeter, men Valmyndigheten markerar båda som "Kan jämföras", så kortet visar förändring för dem. Koden följer Valmyndighetens bedömning.
- **Sidan:** banderollen och ingressen är borta (beslut 29), `geoMap()` är borttagen (planen beskriver den fortfarande), och statusraden har en fjärde gren för det andra året på valnatten ("Slutligt resultat 2022. Ladda om").
- **CSV-mallen** har 12 rader per distrikt och 276 tal för riksdagsvalet, inte "cirka 200".

## Status 2026-09-07: historiksektionen är byggd

Planen `docs/superpowers/plans/2026-09-05-historik-sektion.md` är genomförd, task 1 till 10, på samma sätt som valnattsplanen (egen agent per task med testerna först, oberoende granskning, rättning). Task 6 till 10: `git log --oneline 7bc9cbb..HEAD`. Besluten som ändrade planen står i `docs/superpowers/plans/2026-09-07-tillagg-under-bygget.md`, avsnittet om historikplanen; det är källan där det här stycket bara sammanfattar.

**Granskningsupplägget.** Task 6 (bygget av sektionen) granskades först visuellt av en Opus-agent (29 skärmdumpar, 320 till 1280 px, alla tre valen, inbäddningstestet och fyra valnattssidor) och en Opus-kodgranskare (diffen 119c2ae..16bf902), var och en med en egen motgranskare som reproducerade varje fynd innan det räknades. Sex fynd bekräftades som Important och rättades i en egen commit (3c67057). Task 7 till 10 kördes därefter i den vanliga modellen: en implementerare, en specgranskare och en kvalitetsgranskare per task, med en restlista mellan varje task som nästa agent gjorde som egen commit innan sitt eget arbete.

- **Task 6-uppföljningen (3c67057):** ringen för ett år som inte får ritas flyttad till skalans nedersta nivå med texten "räknas på valnatten"; talraden byggd som `span.hist-tal`-noder som får radbrytas i stället för att klippas; `aretsPunkt` läser det senast laddade året (max i `KONFIG.ar`) i stället för kartans årsknapp; läslinjen flyttas med piltangenter och klick utan att bilden ritas om; etiketterna i högerkanten mörkas mot bläck tills kontrasten mot papper är minst 4,5:1; ResizeObserverns referensbredd uppdateras bara när något faktiskt ritades om, så att stegvisa breddändringar ackumuleras (`histBildSlak`).
- **Task 7 (2df7a91, db40e4d, 69a9965):** bild B, valdeltagandet i Majorna mot Göteborg (och riket streckat på desktop i riksdagsvalet). Högermarginalen låstes till 70 px av ett test, efter att specgranskaren tre gånger underkände en tidigare beslutstext på 66 px (etiketten "Göteborg" är 54,2 px bred plus 13 px förskjutning): granskaren gjorde rätt, det var beslutet som var fel.
- **Task 8 (cfdfe8b, 0dfd77f):** konturkartorna, 2006 (förenklad, 17 distrikt) mot det visade året, och "Om siffrorna" kortad till två punkter (avgränsning; källa, status och andelsdefinition). Kartornas kolumner fick i Task 9:s förberedande restlista (88006e4) ett tak på 200 px så att de förblir en liten sidobild i alla bredder.
- **Task 9 (88006e4, 5f70655, 891d1cd, 2202d7d):** `--partiell N` i `forbered_tvaar.py` (distrikt oräknade i alla tre valen på en gång, till skillnad från `--kf-raknade` som bara gäller kommunvalet) och `verktyg/historik-check.js`, som kontrollerar sektionen i fyra lägen (före valdagen, allt räknat preliminärt, delvis räknat, slutligt).
- **Task 10 (7a98ce0 och den här dokumentationscommiten):** restlistan R1 till R8 från Task 9-granskningen (bland annat att `historik-check.js` nu laddar om sidan innan den läser talraden i prel-kontrollen, så att den faller om bild A börjar följa årsknappen - verifierat mot en sabotagesida), och den här filen, README och `docs/historik/README.md`.

Beslut som ändrade planen, med hänvisning till tilläggsdokumentets rubriker (sök på "Task 6", "Task 7" osv i `docs/superpowers/plans/2026-09-07-tillagg-under-bygget.md`):

- Sista punkten i bild A och B kommer ur det senast laddade året, inte kartans årsknapp; kartorna följer däremot årsknappen.
- Året som inte fått data än ritas som en tom ring på skalans nedersta nivå med texten "räknas på valnatten", inte mitt i bilden.
- Talraden är `span`-noder som får radbrytas, inte en textnod som klipps på smala skärmar.
- Etiketterna i högerkanten mörkas mot bläck till minst 4,5:1 kontrast och får en papperskontur, så de går att läsa över en hjälplinje.
- Läslinjen (klick och piltangenter) flyttar bara sig själv och skriver om talraden; hela bilden ritas inte om.
- ResizeObserverns referensbredd ackumuleras i stället för att nollställas vid varje litet utslag (`histBildSlak` kontrollerar historikbilden särskilt, eftersom dess viewBox är i pixlar).
- Bild B:s högermarginal är 70 px, inte 66 (specgranskaren stoppade rätt när det ursprungliga beslutet var för snålt tilltaget).
- Konturkartornas kolumner har ett tak på 200 px.
- "Om siffrorna" kortad till avgränsning samt källa, status och andelsdefinition.
- Feministiskt initiativs 16,5 procent i riksdagsvalet 2014 (som annars bara syns i Övriga) nämns i noten under bild A via konstanten `HIST_NOT_FI_2014`.

Task 1 till 5 (byggda innan 7bc9cbb, se `git log --oneline` för respektive commit):

- **Task 1, `scripts/bygg_historik.py historik`:** `data/historik.json` + `.js` ur `data/historik/majorna_historik.sqlite` (öppnas skrivskyddat, FEL-rad om tabellen saknas). Partiuppsättningen följer sidans `NYCKELPARTIER[val]` plus Övriga per val, inte databasens; FI ligger i Övriga i riksdagsvalet och `meta.partier_per_val` säger vad som gäller.
- **Task 2, `swing2022`:** `data/swing_2022.*` med `schema.swing(..., samma_yta=True)`, bas 2018 ur `omradespost(con, 2018, val, "majorna")` och alla 23 distrikt i basen (`las_kedja_alla`). Distrikt utan kedja får `orsak` "ej jämförbart enligt källan". Kortets bakåtvända mening 2022 mot 2018 visas nu på sidan.
- **Task 3, `geo2006`:** `data/distrikt_2006.*` med topologisk förenkling (`geo.features_till_schema`, tolerans 0,0002 grader, delade gränser förenklas en gång så att grannar varken överlappar eller lämnar glipor). Övriga år skrivs oförenklade.
- **Task 4, `ar`:** `data/valdata_<år>` och `data/distrikt_<år>` för 2006, 2010, 2014 och 2018 (`BYGGBARA_AR`); 2022 är spärrat så att den kanoniska filen inte skrivs över. Partier utan rader ett år utelämnas i stället för att fyllas med nollor. `kalla` innehåller inga repo-sökvägar.
- **Task 5, `kontrollera.py --historik`:** stämmer av `historik.json`:s majorna-rad för valdatas år mot `data/valdata_2022.json` (41 kontroller), utan att röra databasen; DIFF-rad i stället för traceback när filen saknas, partijämförelsen går åt båda hållen.

Fynd att ta med:

- **2006 får inte läggas i `KONFIG.ar`.** `distrikt_2006` är förenklad för konturkartorna (309 hörn mot 1 146 oförenklat) och passar inte den stora kartan. 2018 fungerar däremot i `ar`: kartan, kortet och tabellen klarar den filen.
- **FI 2014:** Feministiskt initiativ hade 16,5 procent i Majorna i riksdagsvalet 2014 och ligger i Övriga i tidsserien, inte som eget parti. Konstanten `HIST_NOT_FI_2014` i `valgrafik.js` bär talet till sektionens not; ändras partiuppsättningen måste noten följa med.
- **Mandattabellen i databasen** har falska residualrader (ÖVR 349 år 2006, FI 349 år 2014); `_mandat_riket_rd` filtrerar dem och vaktar att summan blir 349.
- **Kontrollskriptet rör aldrig databasen:** `--historik` jämför bara `historik.json` mot `data/valdata_2022.json`; en saknad eller trasig `historik.json` ger en DIFF-rad och kod 1, inte en traceback.

## Så hänger det ihop tekniskt

`valgrafik.js` börjar med `MARKUP` (hela sidans HTML som sträng), `KONFIG` (standardvärden), `PARTIER` (färger och namn), `SPEKTRUM` (halvcirkelns ordning V, S, MP, C, L, KD, M, SD) och `state`. `start()` monterar markupen i `.mp-main`, läser `konfig` först och sedan i ett svep `distrikt_<år>`, `valdata_<år>` och `swing_<år>` för varje år i `KONFIG.ar` (även basåret; saknad swingfil ger ingen swing) plus `bakgrund`, läser URL-parametrar (`distrikt`, `val`, `lage`, `parti`, `ar`, `inbaddad`, `bild`) och renderar allt. Ett år vars geometri eller valdata inte går att ladda hoppas över, med en varning i konsolen. `renderKarta()` projicerar WGS84 till en viewBox 1000 enheter bred (ekvirektangulär med cos(lat), ram 0,045 i longitud och 0,16 i latitud), ritar bakgrund, distrikt, etiketter med kollisionskontroll, hållplatser, platsnamn och markering. `renderPanel()` fyller kortets skelett. `divergens()` bygger "Majorna mot Sverige". `renderBild()` bygger stillbildsramarna.

Brytpunkter: `arDesktop()` (containerbredd 600 px) styr kartans typstorlekar och urval; `arBred()` (900 px) styr om kortet ligger bredvid kartan (då ingen scroll vid val). CSS-layouten styrs av `@container` på samma gränser.

Valnattsläget: `KONFIG.valnatt` sätter statusraden till "Preliminärt, X av 23 distrikt räknade. Uppdaterad HH:MM." med knappen "Ladda om", gråtonar oräknade distrikt, räknar Majorna-snittet på räknade distrikt och visar 2022 års staplar dämpade för oräknade distrikt. `swing_<år>` visas som små tal vid staplarna och som raden "Hur har det ändrats" i kortet. Halvcirkeln visar både Majornas fördelning och riksdagens verkliga, som läses ur mandatfördelningsfilen redan på valnatten och är preliminär (förbehållet skrivs under bilden). Banderollen och ingressen finns inte längre; toppsvaret överst har tagit deras plats.

Sektionen "Majorna sedan 2006" ligger sist i filen före fakta-blocket och renderas av `renderHistorik()`, som anropas sist i `renderAllt()`, i valfliksknapparnas `onclick` (`renderKontroller`) och i ResizeObservern. Den fyller `#hist-mening` (`histMening`), ritar bild A (`histLinjer`, partilinjerna) och bild B (`histDeltagande`, valdeltagandet) och konturkartorna (`histKartor`). Gemensamma hjälpare för de två linjegraferna: `histYta` (ytans bredd, golv 200 px), `histXSkala`, `histHjalplinjer`, `histArAxel`, `histRitaSerie` (en serie med hål där ett parti saknar tal, aldrig en nolla), `histEtiketter` (skjuter isär etiketter som krockar, ankrar varje etikett vid sin egen series sista punkt) och `histRing` (den tomma ringen för ett år utan data). `aretsPunkt(val, niva)` avgör om det senast laddade året (`senasteAr()`, det största talet i `KONFIG.ar`) får en punkt: bara när `raknadeIVal(val)` visar att alla Majornas distrikt är räknade, och för jämförelseområden bara när `omradeDelvis(post)` är falskt. `senasteAr()` läser alltså `KONFIG.ar`, inte `state.ar` (kartans årsknapp) - det är den regeln som gör att sektionen inte hoppar när läsaren byter till Valet 2022. `histBildSlak()` i ResizeObservern jämför bild A:s viewBox-bredd mot ytans `clientWidth` och triggar en omritning särskilt för historikbilden, utöver den vanliga breddkontrollen.

Datafilernas schema står i README under Dataschema.

## Historikspåret (separat, pågående, inte mitt)

Sektionen "Majorna sedan 2006" på sidan är sedan 2026-09-07 färdigbyggd (se statusavsnittet ovan) och läser ett urval av det här underlaget via `scripts/bygg_historik.py`. Underlaget i sig - `scripts/historik/`, `data/historik/` och `docs/historik/` - är däremot ett separat, pågående spår som en annan session äger; reglerna nedan gäller fortfarande.

Parallellt med den här sessionen har en annan session byggt ett historikunderlag i samma mapp: `scripts/historik/` (drygt 30 skript), `data/historik/` (cirka 170 CSV-filer plus `majorna_historik.sqlite`, cirka 27 MB) och `docs/historik/` (`datamodell.md`, `noter/`, `kallor/`). Databasen täcker hela Göteborgs kommun för valen 2002, 2006, 2010, 2014, 2018 och 2022 i alla tre valen, med crosswalk mellan distriktsindelningar (Valmyndighetens FGVAL-tal, officiell mappning 2014 till 2018, Göteborgs stads jämförelsefil 2018 till 2022, geometriskt överlapp), en tidsserie för Majorna, röstberättigade per kön och åldersgrupp 2010 till 2018 och förtidsröster per lokal och dag 2010 till 2018. Den byggs om från grunden av `scripts/historik/bygg_databas.py`.

Att veta:

- Delar av spåret följde med i den första commiten (de fanns i mappen då), resten är ocommittat. Committa inget av det utan att Daniel bett om det, och ta inte bort något. Läs `docs/historik/datamodell.md` och `docs/historik/noter/kedja.md` innan du använder datan.
- Skriptens dokumentation pekar på en venv i en annan sessions scratchpad (`/private/tmp/claude-501/.../f347baf2-.../scratchpad/venv`), som kan vara borta. Prova projektets `.venv` och installera det som saknas.
- 2026-09-07: sidan läser databasen via `scripts/bygg_historik.py` (se statusavsnittet om historikplanen). Databasen själv är fortfarande gitignorerad och ligger i huvudkatalogen; i arbetsträdet är den en symlänk dit.
- Historiken är det naturliga underlaget för idén "Majorna 2002 till 2026" i brainstormen nedan. Hur Majorna avgränsas per år står i `majorna_medlem`-tabellen och i noterna (2006 använder en areametod, 17 distrikt).

- 2026-09-05: skriptens sökvägar pekar nu på projektet (`Historiska dokument/unz/`, `dl2002`, `dl2006`, `dl2018`, `dl_webb`, `repaired`, alla gitignorerade) och på `.venv`; de extra paketen står i `scripts/historik/requirements-historik.txt`.
- Vad sidan kan bygga ur historiken, plus belagda fakta om valnattens filformat 2026 (simuleringsfiler hämtade) och distriktsändringarna 2022 till 2026 (14 av 23 jämförbara, samma totalyta), står i `docs/historik/nasta-steg-for-sidan.md`. Oberoende kontroll av siffror och polygoner: `docs/historik/noter/kontroll_oberoende.md` och `docs/historik/karta_kontroll_2006_2026.png`.

## Beslut och frågor som är Daniels

- Etiketten i stillbilderna: "Majposten · Inför valet" fram till valdagen, sedan till exempel "Majposten · Valet 2026" via `--etikett`.
- Vilket bildformat som ska ligga i själva brevet (kvadraten rekommenderad, liggande som og:image).
- Om Beehiiv-sidans egen rubrik gör grafikens etikett och rubrik dubbla: då `"inbaddad": true` i `data/konfig.json` och skriv om `konfig.js` (kommandot står i README under Publicera). Statusraden och toppsvaret visas alltid, även inbäddat.
- Om Beehiivs sidhuvud är klibbigt: sätt `stickyTopp` i konfig till sidhuvudets höjd plus marginal.
- Att sektionen som blocket ligger i på Beehiiv är minst cirka 1 000 px bred, annars stannar desktopläget i en spalt.
- `toppsvar.mening` i `data/konfig.json` är redaktionens egen mening under toppsvaret, tom som standard. Håll den till en rad, cirka 60 tecken.

## Startpunkt för nästa session

**Först av allt, om det är valveckan:** `docs/valnatt-korschema.md` och README-avsnittet Valnatten. Torrkörningen är gjord 2026-09-07 och dess utskrifter står som facit i körschemat. Grenen `claude/valnattsplanen-superpowers-b46290` är inte mergad till `main` - körschemats grenkontroll (första punkten under Lördag 12 september) förutsätter den mergen, så gör den innan valnatten om den inte redan är gjord.

**Efter valet**, både historikplanen och valnattsplanen är byggda och all dokumentation i den här filen och README är uppdaterad. Kandidater för nästa omgång, ingen brådskande:

- Stillbilder av områdesserien i `scripts/skapa_bilder.py` (historikplanens Task 10-lucka; sektionen finns bara interaktivt i dag).
- En årsväljare på kartan för historikåren (2018 går redan att lägga i `KONFIG.ar`, se README), om Daniel vill att fler år går att välja i den stora kartan, inte bara i historiksektionens egen linje.
- "Tre saker som skiljer Majorna" (specen `docs/superpowers/specs/2026-09-05-historik-2026-design.md`, avsnitt 11 punkt 6) - väntar på Daniels beslut, se Tankesmedjan nedan.
- FI som nyckelparti i riksdagsvalet, om Daniel vill se Feministiskt initiativs 16,5 procent 2014 som egen linje i stället för i Övriga - kräver en ändring i `NYCKELPARTIER["rd"]` i hela schemat, även för 2022 och 2026 (Daniels beslut, se fyndet om FI 2014 ovan).
- Codex 16 och 17: `scripts/kontrollera.py` täcker bara distriktsraderna, inte aggregat och mandat; `scripts/skapa_bilder.py` kan märka en bild med fel år.
- Refaktoreringarna: `main` i `scripts/uppdatera_2026.py` är lång och gör för mycket; `bygg()` läser modulglobalen `JAMFORBAR` i stället för att ta den som argument; xlsx-vägen och JSON-vägen dubblerar distriktsslingan i `uppdatera_2026.py`; `_kontrollera_valtyp` i `scripts/valnatt.py` godtar saknat eller null `valtyp`; halvcirkelns ingressmening står på ett ställe (konstant) men `MARKUP` och `renderRiksdag` delar fortfarande ansvar för sidhuvudets uppbyggnad; kartans skaldrift under tio procent vid stegvisa breddändringar (tröskeln i ResizeObservern).

Modellval för subagenter: se minnesfilen `subagenter-modellval.md` (Sonnet på mekaniska tasks, Opus på JS-tasks med visuell granskning, ingen Fable).

Frågorna nedan är Daniels och väntar på hans beslut, inte på kod.

### Tankesmedjan: helhetsgrepp och vidareutveckling

Planen för historik och 2026 är skriven och granskad 2026-09-05: `docs/superpowers/specs/2026-09-05-historik-2026-design.md`. Den väntar på Daniels beslut (avsnitt 11 i specen) innan något byggs. Underlaget (faktablad, Majornabons önskelista, två koncept, valnattsredaktörens genomgång) skapades av en workflow och ligger inte i repot.

Frågor som är för stora för en punktfix och som Daniel vill tänka igenom i ett sammanhang, inte lösa i förbigående:

- Årväljaren och etiketten när sidan ska rymma både 2022, 2026 och (senare) historik: vad ska synas före och efter valdagen, hur ser övergången ut.
- Röstdelningen som karta (vilket kvarter röstdelar mest) i stället för, eller utöver, radlistan.
- Sidfoten och "Om siffrorna" mot Beehiivs egen sidfot - dubbleras information.
- Halvcirkelns plats i förhållande till kartan (briefen sade ovanför kartan, nuvarande layout har den överst av allt; Daniel har inte tagit ställning till att flytta den).

Idéer som diskuterats sedan tidigare, med datastatus:

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
- Kartan, kartlegenden och resultatkortet ligger i `#karta-yta` inuti `#karta-sektion`. Det är den wrappern som begränsar det klibbiga kortets yta; tar man bort den lägger sig kortet över tabellknappen och tabellen vid rullning på desktop.
- CSS-lintet i `tests/test_inbaddning.py` faller på varje selektor som inte börjar med `.mp-val`, på `vh` och på `position: fixed`.
- Regler inne i `@container` kan aldrig träffa `.mp-val` själv, bara dess barn.
- `data/swing_<år>.js` är en valfri fil. `swing_2022.js` finns inte förrän historikplanen skrivit den; sidan laddar den för varje år och tål 404 (ingen förändringsrad för året), och `skal-check.js` och `beehiiv-check.js` räknar den som "valfri fil som saknas". En saknad `valdata_<år>.js` eller `distrikt_<år>.js` är däremot ett fel: året hoppas över med en varning i konsolen, och sidan felar först när inget år går att ladda.
- Stillbilderna "Majorna mot Sverige" för 2026 kräver aggregat för riket, Västra Götaland och Göteborg i `valdata_2026.json`, som bara finns när `uppdatera_2026.py` körts med Valmyndighetens filer (inte CSV-vägen).
- Facebook och Beehiiv cachar länkkortet: og-taggarna i `index.html` gäller GitHub-adressen (skalet), medan Beehiiv-sidan har sina egna SEO-inställningar i sajtbyggaren.
- Skärmdumpsverktygen i `verktyg/` behöver `puppeteer-core` installerat i mappen och servern igång.
- Den lokala förhandsvisningsservern kan dö mellan sessioner; starta om den innan verktygen körs.
- Chrome headless via kommandoraden klampar smala fönsterbredder; för mobilbilder används puppeteer med mobilemulering, för stillbilder räcker Chrome direkt (1200 och 1080 px).

Från valnattsomgången:

- `data/distrikt.geojson` heter `data/distrikt_2022.geojson` sedan 2026-09-06, och sidan laddar `distrikt_<år>` för varje år i konfigen. `scripts/hamta_bakgrund.py` och `scripts/bygg_data.py` pekar på det nya namnet.
- `data/distrikt.js` är en **övergångskopia** av `distrikt_2022.js` under nyckeln `distrikt` (samma data, kontrollerad med `schema.las_js` mot `distrikt_2022.js`), inte en fil koden längre laddar. Den finns kvar bara åt läsare med en cachad gammal `valgrafik.js` (från före denna omgång) som fortfarande försöker ladda `data/distrikt.js` direkt - utan kopian hade de fått "Datafilerna kunde inte laddas" i upp till tio minuter efter mergepushen, GitHub Pages cachetid. Filen är statisk (byggs inte om av något skript) och ska tas bort helt efter valet.
- Gitignorerat och ska aldrig committas: `data/valnatt/` (Valmyndighetens hämtade filer), `tmp/` (testsidorna), `verktyg/node_modules/`, `val-sign-crt.pem` och `val-sign-pub.pem`. Halvfärdiga tidsstämpelmappar under `data/valnatt/` efter avbrutna körningar är ofarliga: `senaste` pekar bara på lyckade körningar.
- Testsidorna under `tmp/` innehåller **kopior** av `valgrafik.js` och `valgrafik.css`. Bygg om dem med `verktyg/forbered_tvaar.py` efter varje ändring i källfilerna, annars kontrollerar `tvaar-check.js` gammal kod.
- De två signaturtesterna (`test_signatur_verifieras_med_valmyndighetens_nyckel`, `test_signatur_ger_false_vid_andrad_byte`) hoppas över tyst i en klon utan pem-filerna. `hamta_2026.py` hämtar certifikatet själv vid första körningen.
- `KONFIG_STANDARD.stickyTopp` (och `valgrafik.js`-kopian av samma standard) är 105, inte 16: Beehiivs klibbiga sidmeny är 89 px hög. Går `data/konfig.json` förlorad faller sidan tillbaka på 105, produktionsvärdet.
- `--tvinga` låser upp tre spärrar samtidigt (färre räknade distrikt, testdata över skarp data, testdata till repots `data/`) och ersätter hela filen i stället för att slå ihop. En `--tvinga` direkt efter en `--genrep`-körning kan alltså skriva testmärkt data till `data/`.
- `meta.valnatt.raknade` räknar distrikt där **något** val är räknat, inte per val. Sidan räknar per visat val med `raknadeIVal(val)`; använd den, inte metatalet, i ny kod.
- Kohorten i swingfilen räknar distrikt som är både räknade och jämförbara, statusraden räknar alla räknade. Samma tal på båda ställena är fel.
- Sidhuvudets reserverade höjd sätts när `konfig.js` lästs (årväljarens rad och toppsvarets höjd), inte vid första målningen. I det degraderade läget där ett år inte kan laddas krymper sidhuvudet 56 px när årväljaren döljs.
- `KONFIG.toppsvar.mening` bör hållas till cirka 60 tecken: sidan reserverar höjd för en rad extra.
- "Majornas 23 valdistrikt" är hårdkodat i `meta description` och `og:description` i `index.html` (rad 8 och 11); `docs/beehiivtest.html` och `docs/inbaddningstest.html` har ingen description-metatagg. Antalet är 23 båda åren, så det får stå, men det uppdateras inte av datan.
- `.forbehall` är 16 px (brödtextens minimum) medan `.not` är 14 px; det är avsiktligt.
- `docs/skarmdumpar/` är tagna före toppsvaret och kortets rad "Hur har det ändrats" och visar alltså en äldre sida.

Från historikplanen:

- `bygg_historik.py ar 2022` är spärrat: `data/valdata_2022.json` är den kanoniska filen ur xlsx:en och får inte skrivas över av databasen ("FEL: 2022 byggs inte av det här skriptet"). `BYGGBARA_AR` är 2006, 2010, 2014 och 2018.
- `data/distrikt_2006.*` är förenklad geometri för konturkartorna och får inte läggas i `KONFIG.ar`.
- `data/historik/` (databasen och CSV-filerna) ska fortfarande inte committas; de byggda filerna under `data/` (`historik`, `swing_2022`, `valdata_<år>`, `distrikt_<år>`) är däremot committade och byte-identiska med byggets utdata (tester vaktar det).
- `historik.js`, `swing_2022.js` och `distrikt_2006.js` laddas vid start i samma svep som årets filer; saknas `historik.js` döljs sektionen (laddningen fångar felet), och den döljs också i bildläget och när serien har färre än två punkter. `"historik": {"visa": false}` i `data/konfig.json` stänger av laddningen av `historik.js` och `distrikt_2006.js`, men inte av `swing_2022.js` - den filen hör till resultatkortets rad "Hur har det ändrats" och laddas så länge 2022 står i `KONFIG.ar`.
- `aretsPunkt` avgör ensam om 2026 ritas i bild A och B: alla Majornas distrikt måste vara räknade i det valet, och för ett jämförelseområde måste området självt vara färdigräknat (`omradeDelvis`). Ett halvräknat jämförelseområde får alltså ingen punkt alls, hellre än en missvisande.
- Sektionen följer kartans val (`state.val`) men **inte** kartans årsknapp (`state.ar`) - utom konturkartorna, som är den enda delen som gör det. Byter läsaren till Valet 2022 på valnatten står bild A och B kvar på 2026.
- Testsidorna under `tmp/` som `historik-check.js` kontrollerar (byggda med `forbered_tvaar.py --valnatt --partiell N` med mera) är **kopior** av `valgrafik.js` och `valgrafik.css`; bygg om dem efter varje ändring i källfilerna, som för `tvaar-check.js`.
- Kartans skaldrift under tio procent vid stegvisa breddändringar (tröskeln i ResizeObservern) kvarstår medvetet - kartkoden rördes inte under historikplanen och är kandidat för refaktoreringslistan efter valet.
- `HIST_NOT_FI_2014` (16,5 procent) är sidans enda hårdkodade tal; `tests/test_bygg_historik.py` vaktar att det stämmer med databasens `tidsserie` 2014 rd majorna FI (hoppas över utan databas).
- Agentrapporter till kontrollern ska vara korta, utan citattecken eller radbrytningar i de strukturerade fälten - en ogiltig rapport gjorde att kontrollern fick verifiera Task 9 för hand (se tilläggsdokumentet, "Efter granskningen av Task 9").
