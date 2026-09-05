# Historik och 2026 i "Så röstade Majorna" - plan

Skriven 2026-09-05, åtta dagar före valdagen 2026-09-13, och reviderad samma dag efter två granskningar (UX och enkelhet; varje datapåstående mot databasen och råmaterialet). Underlag: faktabladet ur historikdatabasen, en Majornabos önskelista, två designkoncept ("kvarteret först" och "berättelsen först"), valnattsredaktörens genomgång av lägen och datafiler, `docs/historik/nasta-steg-for-sidan.md` från historiksessionen och Codex-granskningen 2026-09-05. Alla tal kommer ur `data/historik/majorna_historik.sqlite` (tabellen `tidsserie`), `data/historik/kedja_majorna_2006_2022.csv`, Valmyndighetens filer under `Historiska dokument/dl_webb/` eller `data/valdata_2022.json`, och är kontrollerade av faktagranskningen. Det som fortfarande är okontrollerat står i avsnitt 10.

## 1. Vad planen bygger, i en mening

Sidan får ett svar högst upp (så röstade Majorna i år, utan knappar), historiken som en sektion med en mening, två bilder (partilinjer sedan 2006, valdeltagande mot Göteborg) och två små konturkartor som visar att kvarteren ritats om, kortet får raden "Hur har det ändrats" som bara visar förändring där Valmyndigheten eller kedjan säger att den går att räkna, och 2026 hakar på i alla delarna på valnatten utan kodändring.

## 2. Principer, ur Majornabons text

- Historiken är en mening och en bild, inte ett verktyg. Läsaren vill veta om Majorna förändrats, inte undersöka det.
- Inga nya knapprader. Räknat över hela sidan möter läsaren i dag fyra knappgrupper: Riksdagen/Om Majorna bestämde, Riksdag/Region/Kommun, Största parti/Partistyrka, och Majorna mot Sveriges egen valrad. Planen lägger inte till någon. Historiksektionen följer kartans valrad.
- Där datan inte räcker står det, i en mening på rätt ställe, som ett besked och inte som en metodförklaring. Orden jämförbarhet, areaöverlapp, crosswalk och kohort förekommer inte i gränssnittet.
- Förändring visas aldrig där den inte får räknas. Det gäller kortet, statusraden och linjerna: en linje som slutar är ärligare än en punkt räknad på en del av distrikten.
- Sidan ändrar inte siffror i block läsaren redan läst, hoppar inte när den laddar, och ingenting pulserar. Alla nya ytor har reserverad höjd i CSS innan datan finns.
- I år är i år. Historiken ligger under det aktuella.

## 3. Sidan uppifrån och ned (mobil 390 px)

| # | Sektion | Svarar på | Ändring mot i dag |
|---|---|---|---|
| 0 | **Toppsvaret** (ny) | Vad blev det i Majorna i år, innan jag trycker på något | Ny: etikett, rubrik, statusrad, de fyra största partierna i riksdagsvalet med stapel och tal, en mening om valdeltagandet. Inga val att göra. På valnatten får statusraden en textlänk "Ladda om" i högerkanten; det är den enda tryckytan. Ersätter valnattsbanderollen. |
| 1 | **Så röstade ditt kvarter** | Mitt kvarter, och skiljer sig Majorna inuti | Behålls. Kortet får raden "Hur har det ändrats" (avsnitt 5). Kartan ritar det år som visas med det årets geometri (avsnitt 4). Antalet distrikt läses ur datan överallt, aldrig hårdkodat 23. |
| 2 | **Majorna mot Sverige** | Vad gör oss annorlunda | Behålls. |
| 3 | **Röstdelningen** | Röstar vi olika i riksdag, region och kommun | Behålls oförändrad. Paret Majorna mot Sverige och Röstdelningen ligger sida vid sida på desktop i dag, och den nya sektionen läggs efter paret så att det består. |
| 4 | **Majorna sedan 2006** (ny) | Har området förändrats, och röstar vi mer än Göteborg | Ny sektion, avsnitt 6. |
| 5 | **Om Majorna bestämde** | Hur skulle riksdagen se ut om alla röstade som här | Innehållet oförändrat. Placeringen är öppen, se avsnitt 11 punkt 1: i dag ligger den överst av allt, briefen 2026-09-03 satte den ovanför kartan, Majornabon och båda koncepten vill ha kartan direkt efter toppsvaret. Tabellen visar planens rekommendation; med Daniels andra beslut blir ordningen toppsvar, Om Majorna bestämde, kartan och så vidare. |
| 6 | **Om siffrorna** | Kan jag lita på det här | Kortas. Förbehåll som gäller ett diagram står under det diagrammet. Kvar: avgränsning, källa, andelsdefinition. |

Det som inte byggs nu men som konceptet "berättelsen först" föreslog: att ersätta "Majorna mot Sverige" och "Röstdelningen" med tre påståenden med varsin liten figur (prickpar Majorna mot riket på gemensam axel, röstdelningen nedkokad till V och D, valdeltagandet över tid), och att ta bort Partistyrka-läget. Majornabon hoppar över båda sektionerna i dagens form och väljer aldrig Partistyrka frivilligt. Tas upp i avsnitt 11 som beslut för Daniel, efter valet.

## 4. Årsmodellen

**Regeln: årväljaren visar bara år som har fullständig distriktsdata på sin egen geometri.** Det är `KONFIG.ar`, i dag `["2022"]`, på valnatten `["2022", "2026"]`. Dagens årväljare (dold när listan har ett år) behålls. Historikåren 2006 till 2018 läggs aldrig i `KONFIG.ar`; de lever i historiksektionen.

**Geometri per år.** Sidan laddar `data/distrikt_<år>.js` för varje år i `KONFIG.ar` och håller `state.geo[år]`. Dagens `data/distrikt.js` döps om till `distrikt_2022.js`, utan kopia; skalet, verktygen och testerna ändras samtidigt. 2026 får `distrikt_2026.js` ur Valmyndighetens geografi (avsnitt 8). Kartan ritar alltid det visade årets polygoner med det årets siffror. **Geometribytet sker på valnatten**, när `uppdatera_2026.py --valnatt` lägger 2026 i `ar`; före valdagen visar kartan 2022 på 2022 års gränser. Bytet är därför ett eget steg i torrkörningen (avsnitt 9 punkt 6). Kartans ram räknas ur en gemensam bbox över de laddade åren så att kartan inte hoppar vid årsbyte.

**Antal distrikt** står ingenstans hårdkodat: kartans aria-text, stillbildernas alt-text, statusradens "X av Y" och tabellen läser antalet ur datan. I dag står 23 i `valgrafik.js` på fem ställen (raderna 20, 297, 571, 939 och 940 enligt faktagranskningen).

**Ditt kvarter bakåt** går via kortet, inte via kartan. Ingen årsväljare på kartan för 2006 till 2018 i den här omgången. Datafilerna för historikåren byggs ändå i sidans schema (avsnitt 8), så att ett historikår kan läggas i `ar` senare om Daniel vill se det på kartan; sidan ska då klara 17 och 22 distrikt.

## 5. Kortet: "Hur har det ändrats"

En ny rad under staplarna i resultatkortet. Vad den visar avgörs av `data/swing_<år>.json` för det visade året, aldrig av vad som råkar finnas. Exemplen nedan skrivs med nollor; alla tal kommer ur datan.

- **Jämförbart mot föregående val.** Raden "Sedan 2018: V 0,0  S 0,0  MP 0,0" (procentenheter, distriktets tre största partier) och de små talen vid staplarna som i dag. Gäller 9 av 23 distrikt 2022 mot 2018: Svalebo, Kusttorget, Chapmans Torg, Slottsskogsgat. m fl, Gråberget Västra, Godhem, Kommendörsgatan m fl, Hängmattan och Gatenhielmska (kontrollerat mot `kedja_majorna_2006_2022.csv`, kolumnen `jamforbar_tillbaka_till`), och 14 av 23 distrikt 2026 mot 2022 enligt Valmyndighetens fil `valdistrikt-jamforelser-mellan-2022-och-2026.xlsx` (kontrollerad på cellnivå, fliken Jämförelser, kolumnen Jämförbarhet).
- **Omritat distrikt, framåt (2026 mot 2022).** Ingen pil, inga små tal. I brödtext: "Gränserna för Mariaplan ritades om till 2026. Siffrorna går inte att jämföra med 2022." Följt av områdesnivån: "Hela Majorna: V 0,0 sedan 2022." Områdesraden är giltig eftersom de 23 distrikten täcker samma yta 2026 som 2022 (4 655 446 kvadratmeter 2026 mot 4 655 300 år 2022, räknat ur båda geometrierna av faktagranskningen). De nio omritade är Kungsladugård Västra, Mariaplan, Silverkällan, Sannaplan, Sandarna (2022 stavat Sandarne), Klippan, Gröna Vallen, Slottsskogsgat. m fl och Godhem.
- **Omritat distrikt, bakåt (2022 mot 2018).** "Gränserna såg annorlunda ut 2018. Siffrorna hör till det årets distrikt." Följt av "Hela Majorna: V 0,0 sedan 2018", räknat ur områdesserien (tidsserien håller området konstant, 22 distrikt 2018 mot 23 år 2022, samma yta på 0,04 procent när). Det gäller de 14 distrikt som inte når 2018.
- **Hela Majorna** (inget distrikt valt): raden "Sedan 2022: V 0,0  S 0,0  MP 0,0". Källan beror på läget, se avsnitt 7: så länge räkningen pågår räknas den på kohorten (distrikt som är räknade i år mot samma distrikt förra valet) och raden slutar med "räknat på 9 av 23 distrikt"; när alla distrikt är räknade är kohorten hela området och talet blir detsamma som områdesserien ger.
- Ett steg bakåt, inte längre. Godhem och Gatenhielmska går att följa till 2006, men två distrikt av 23 motiverar ingen egen rad.
- Areaviktad skattning för omritade distrikt görs inte. Areaandel är inte väljarandel: avvikelsen mot Valmyndighetens officiella mappning 2014 till 2018 är i genomsnitt 12,3 procentenheter och som mest 85,9 (`docs/historik/valdistrikt-historik.md`). Daniels beslut; planens rekommendation är att inte visa den.

`swing_<år>.json` får ett fast schema: `bas`, `ar`, `distrikt` (bara jämförbara distrikt, procentenheter per parti och val), `ej_jamforbara` (koder med en kort orsak och vilken mening kortet ska visa), `majorna` (förändring per val för hela området), `kohort` (per val: antal räknade distrikt som ingår och deras koder). `swing_2022.json` (bas 2018) byggs ur historikdatabasen, `swing_2026.json` (bas 2022) av `uppdatera_2026.py` med jämförbarheten ur Valmyndighetens fält `statusJamforelse`. Sidan laddar `swing_<år>` för varje år i `ar` när filen finns; basåret slutar väljas implicit som lägsta året i `ar` och läses ur `bas` i swingfilen.

## 6. Sektionen "Majorna sedan 2006"

Ligger efter Röstdelningen. Ingen egen knapprad: sektionen följer kartans val (`state.val`) och skriver ut vilket val den visar i sin mening. Byter läsaren val vid kartan byter sektionen, vilket är läsarens eget synliga val. Höjden på alla ytor är reserverad i CSS innan datan finns.

**Meningen.** En rubrikmening räknad ur datan med redaktionell överskrivning i `KONFIG.historik.mening` (en per val). Standard: "V har gått från 17,2 till 27,2 procent i riksdagsvalet sedan 2006" (kommunvalet: "från 14,5 till 34,6"). Så länge det visade året är preliminärt fryses meningen på senaste slutliga år, så att den inte ändrar sig under valnattens uppdateringar.

**Bild A, partilinjer.** Linjediagram i inline-SVG, 358 x 280 px på 390 px skärm. X-axeln sex jämnt fördelade valår (06, 10, 14, 18, 22, 26), y-axeln 0 till 40 procent med hjälplinjer var tionde. Fyra serier på mobil: V, S, MP och SD; M som femte serie från 600 px containerbredd (M gick från 17,7 till 8,9 procent i riksdagsvalet, det är en del av berättelsen, men fem linjer får inte plats på mobil). C, L och KD ligger under 9 procent hela perioden och finns bara i talraden. Partibokstav i partifärg vid linjens högra ände; etiketterna förskjuts lodrätt med samma dodge-regel som Röstdelningen använde, med kort ledarlinje, eftersom V och S slutar 1,3 procentenheter isär 2022. Vid 2006 ligger V, MP och M inom 0,5 procentenheter (17,15, 17,51 och 17,68); knuten är verklig och accepteras, talraden ger de exakta talen. Ett tryck i diagrammet flyttar en lodrät läslinje till närmaste år och byter talraden under bilden till det årets tal; läslinjen nås också med piltangenter i samma mönster som knappgrupperna. Talraden visar som standard det senaste slutliga året och ryms på en rad (uppskattat 336 px vid 16 px Arial, mäts i bygget). Under bilden i liten text: "Serien börjar 2006. Valdistrikten ritades om helt inför det valet, så 2002 går inte att räkna om till dagens Majorna. Området hålls konstant medan antalet distrikt varierar: 17 år 2006, 2010 och 2014, 22 år 2018, 23 år 2022 och 2026. Liberalerna hette Folkpartiet till och med 2014." Bilden har `role="img"` med rubrikmeningen som `aria-label`; talraden är sektionens textalternativ.

**Bild B, valdeltagandet.** Linjediagram 358 x 160 px, y-axeln 70 till 90 procent (skalan står i bildtexten). Två linjer på mobil: Majorna i slottsskogsgrön, Göteborg i sten; riket som tredje linje från 600 px. Rubrikmening ur datan: "Fram till 2018 röstade Majorna som Göteborg. 2022 drog Majorna ifrån: 82,8 mot 80,7 procent." (riksdagsvalet: 79,3 mot 79,5 år 2006, 84,3 mot 84,3 år 2018, 82,8 mot 80,7 år 2022). Göteborgs- och riketlinjerna slutar vid senaste år med känt aggregat; via CSV-reservvägen saknas aggregaten för 2026 och bildtexten säger det. Bildtexten säger också att kommunvalet ser annorlunda ut (Majorna över Göteborg alla år) och att valdeltagande i olika val inte ska jämföras med varandra eftersom röstberättigade skiljer sig. `role="img"` med rubrikmeningen som `aria-label`.

**Två konturkartor.** Sida vid sida även på 390 px, cirka 170 x 135 px var: "2006, 17 distrikt" och "I år, 23 distrikt". Bara gränser i sten på papper med gemensam yttre kontur, ingen partifärg, inga etiketter, inget att trycka på, `aria-hidden` med bildtexten som innehåll: "Samma yta, fler distrikt. Ett kvarter 2006 är ofta två i dag." Det är bilden som visar varför kvarteret inte går att följa bakåt, utan metodtext. Underlag: 2006 års 17 polygoner, förenklade för formatet, och det visade årets geometri som redan är laddad. Under kartorna, sist i sektionen, en mening som stänger Majornabons fråga om ålder: "Hur olika åldrar röstade går inte att veta. Valhemligheten gäller per distrikt, inte per person."

**Desktop (container 900 px och bredare).** Bild A över båda kolumnerna med talraden under; bild B i vänster kolumn och konturkartorna i höger; meningen ovanför spänner båda. Toppsvaret håller samma maxbredd som sidhuvudet (680 px).

**Inte med:** tabell med partier gånger år, dragreglage, animering, årsväljare, förtidsröster (finns bara 2010 till 2018), röstberättigade efter ålder och kön (finns bara 2010 till 2018).

## 7. 2026 i tre lägen

Styrs av `KONFIG.ar`, `KONFIG.standardAr`, `KONFIG.valnatt` och `meta.status`; inga kodändringar mellan lägena.

**Före valdagen.** Toppsvaret visar 2022 med statusraden "Slutligt resultat 2022. Valet 2026 är söndag 13 september." Kartan visar 2022 på 2022 års geometri. Kortet visar "Sedan 2018" för de 9 jämförbara och den bakåtvända meningen med områdesrad för de 14 övriga. Bild A och B har fem punkter och en tom ring på 2026 med texten "räknas på valnatten".

**Valnatten.** `uppdatera_2026.py --valnatt` sätter `ar: ["2022","2026"]`, `standardAr: "2026"`, `valnatt: true`; det är också då kartan börjar rita 2026 års geometri. Statusraden: "Preliminärt, 9 av 23 distrikt räknade i riksdagsvalet. Uppdaterad 21:34." med textlänken "Ladda om"; ingen automatisk hämtning, ingen snurra. Toppsvaret visar de fyra största bland räknade distrikt, utan mening om förändring, och utan redaktionell mening om `KONFIG.toppsvar.mening` är tom (ingen genererad text). Kartan visar räknade distrikt färgade och oräknade i papper med tunn kontur. Kortet: jämförbara distrikt får "Sedan 2022", de nio omritade får meningen och områdesraden räknad på kohorten. Hela Majorna: kohortraden med "räknat på 9 av 23 distrikt". **Bild A och B ritar inte 2026 förrän alla distrikt är räknade**: linjerna slutar vid 2022 och ringen på 2026 säger "räknas på valnatten". Rubrikmeningarna i historiksektionen är frysta på 2022. Röstdelningen och Majorna mot Sverige räknar på kohorten som i dag.

**Alla distrikt räknade, preliminärt.** Statusraden "Preliminärt, 23 av 23 distrikt räknade." Bild A och B får 2026 som öppen ring med heldragen linje och "preliminärt" i talraden; kohorten är nu hela området, så kortets områdesrad och linjen bygger på samma tal.

**Efter slutlig räkning.** `--status slutlig` och `valnatt: false` för hand. Statusraden: "Slutligt resultat, riksdagsvalet 2026." Ringen blir fylld punkt, "preliminärt" försvinner, konturkartan "I år" visar 2026, rubrikmeningarna räknas om på 2026 och Daniel skriver över dem i konfig om han vill.

## 8. Data och filer

Allt byggs av Python i `scripts/`, läser historikdatabasen skrivskyddat och skriver `.json` plus identisk `.js` med `scripts/schema.skriv`. Storlekar är mätta där de anges som mätta.

| Fil | Innehåll | Källa | Storlek | Laddas |
|---|---|---|---|---|
| `data/historik.json` | Områdesserien: per val, nivå (majorna, goteborg, riket) och år 2006 till 2022: röster och andel per parti (V, S, MP, SD, M, C, L, KD, D, FI, K, Övriga ur SUMMA_ÖVRIGA), giltiga, röstande, röstberättigade, valdeltagande, antal distrikt, metod. Innevarande år läses ur `valdata_<år>`. | tabellen `tidsserie` | cirka 25 kB mätt av faktagranskningen med röstantal; mäts i bygget | vid start |
| `data/distrikt_2006.geojson` | 2006 års 17 polygoner i sidans schema, förenklade för konturkartan | `data/historik/distrikt_2006_majornaomradet.geojson` (27 kB rå, 17 features) | riktvärde 10 kB, mäts i bygget | vid start |
| `data/valdata_2006.json` (och 2010, 2014, 2018) med `distrikt_2010`, `distrikt_2014`, `distrikt_2018` | Sidans befintliga schema för historikåren, så att ett år kan läggas i `ar` senare | tabellerna `roster`, `distrikt_summa`, `majorna_medlem`, `tidsserie`; `distrikt_<år>_majornaomradet.geojson` | 5 till 7 kB per valdata (uppskattat ur databasen), polygoner 27 kB råa | inte alls i den här omgången |
| `data/distrikt_2022.geojson` | Dagens `distrikt.geojson` under nytt namn | befintlig | 61 kB | vid start |
| `data/distrikt_2026.geojson` | 2026 års 23 distrikt (alla 23 koder finns i 2026 års geografi, kontrollerat) | `Historiska dokument/dl_webb/2026/valdistrikt-vastra-gotaland-lan-2026.zip` (GeoJSON, EPSG:3006, egenskaperna `Valdistriktskod` och `Valdistriktsnamn`, kontrollerat) | riktvärde 60 kB | när 2026 finns i `ar` |
| `data/swing_2022.json` | Förändring 2022 mot 2018 för de 9 jämförbara distrikten, `ej_jamforbara` för 14, områdesraden ur tidsserien | `kedja_majorna_2006_2022.csv`, tabellerna `roster` och `tidsserie` | under 5 kB | vid start |
| `data/swing_2026.json` | Samma schema, bas 2022, jämförbarhet ur `statusJamforelse` | `uppdatera_2026.py` | under 5 kB | på valnatten |
| `data/konfig.json` | Nya nycklar: `historik { visa, mening: {rd, rf, kf} }`, `toppsvar { mening }` | | | |

**Sidvikt.** Vid start ökar vikten med cirka 40 kB (historik 25, swing_2022 under 5, distrikt_2006 cirka 10), från cirka 355 kB till cirka 395 kB. Ingen lat laddning på synlighet: sidan ligger i Beehiivs iframe där hela innehållet räknas som i bild, så det skulle inte spara något och riskerar att ändra iframens höjd under läsning. 2026 års geometri lägger till riktvärdet 60 kB först när året finns i `ar`.

**Nya skript.** `scripts/bygg_historik.py` skriver `historik`, `swing_2022`, `distrikt_2006` samt valdata och polygoner för 2010 till 2018, med tester: partiernas röster summerar till giltiga per år, val och nivå; 2022 års majorna-rader i `historik.json` är identiska med aggregaten i `valdata_2022.json`; exakt 9 distrikt får swing 2022 och de 14 övriga står i `ej_jamforbara`, och skriptet skriver ut båda listorna för avstämning; 2006 års 17 polygoner har giltiga ringar. `scripts/geo.py` får läsa 2026 års egenskapsnamn, skriva `distrikt_2026` och räkna unionsytan mot 2022. `scripts/kontrollera.py` kontrollerar `historik.json` mot `valdata_2022.json`.

## 9. Valnattens pipeline (spår A, måste före 13 september)

Inte historik, men avgör om 2026 kommer in alls. Ur Codex-granskningen och valnattsredaktören, i prioritetsordning:

1. **JSON-vägen** i `uppdatera_2026.py`: hämta `index.md5` och tre zip-filer (riksdag hela landet, region län 14, kommun 1480) från `https://resultat.val.se/resultatfiler/val2026/p/`, kontrollera md5, läs `rostfordelning` och `summering`, mappa till sidans schema. Räknade distrikt ur `rapporteringsTid`, jämförbarhet ur `statusJamforelse`. Genrep-filerna i `Historiska dokument/dl_webb/genrep2026/` (fyra zip-filer, uppackade i `unz/`) har fälten `test`, `antalValdistriktRaknade`, `antalValdistriktSomSkaRaknas`, `valdistriktskod`, `rapporteringsTid`, `statusJamforelse`, `valdistriktskodForegaendeVal` och `partiRoster` med `partiforkortning` och `antalRoster` (kontrollerat i kommunfilen). Stor insats. Xlsx-vägen och CSV-vägen behålls. `meta.test` förs in i schemat så att en genrep-fil aldrig kan se ut som skarp.
2. **Tom eller mindre import får aldrig skriva över**: skriv till temporär fil, byt namn efter kontroll, vägra färre räknade distrikt än befintlig fil. Liten.
3. **Swing bara för jämförbara distrikt och Majorna på kohorten** i `schema.swing` (Codex 2 och 5). Liten.
4. **CSV-mallen läsbar tillbaka, negativa tal och okända partikoder avvisas** (Codex 4 och 6). Medel.
5. **`distrikt_2026`** ur 2026 års geografi, med unionsytan räknad mot 2022 i bygget. Medel.
6. **Torrkörning hela vägen** dagen före: `--repetera` som facit, genrep-filer genom JSON-vägen, geometribytet till 2026, uppladdning, kontroll på majposten.se. Liten.

Senare: `kontrollera.py` för aggregat och mandat, årsmärkningen i `skapa_bilder.py` (Codex 16 och 17), stillbilder av områdesserien.

## 10. Kontrollerat och okontrollerat

Kontrollerat av faktagranskningen 2026-09-05, direkt mot källorna: alla procenttal i planen; antal distrikt per år; att D saknas i riksdagsvalet; de nio jämförbara mot 2018; de nio omritade mot 2026 (fliken Jämförelser i Valmyndighetens fil, slutlig bedömning 2026-08-17); att 2026 har alla 23 koder; unionsytan 2026 mot 2022; genrep-filernas fält; 2026 års egenskapsnamn och koordinatsystem; filstorlekarna för råmaterialet; kodställena i `valgrafik.js`.

Kvar att verifiera i bygget: storlekarna på filer som inte finns än (`historik.json` mäts, `distrikt_2006` förenklad, `distrikt_2026`, valdata per historikår); att talraden ryms på 358 px; att konturkartorna är läsbara på 170 px.

Saknas och visas inte: 2002 som Majorna (ingen geografi, gränserna omritade helt till 2006); röstberättigade efter ålder och kön för 2022 (nämns i `nasta-steg-for-sidan.md` som en xlsx i projektroten, men den fanns inte där; filerna `statistik-alder-och-kon-*.xlsx` är gitignorerade och inte inlästa i databasen); förtidsröster 2022 och 2026 i databasen.

## 11. Beslut som är Daniels

**Beslut 2026-09-05 kväll:** Daniel valde rekommendationerna på alla punkter nedan, och att serien börjar 2006 (2002 utelämnas helt). Bygget beskrivs i `docs/superpowers/plans/2026-09-05-valnatt-2026.md` (spår A, först) och `docs/superpowers/plans/2026-09-05-historik-sektion.md` (spår B).

1. **"Om Majorna bestämde"**: kvar ovanför kartan (briefen) eller flyttad under "Majorna sedan 2006" (Majornabon, båda koncepten). Rekommendation: flytta, eftersom toppsvaret redan ger första skärmen ett resultat och kartan då kommer direkt efter.
2. **Ordningen mellan spåren** (avsnitt 12): valnatten först eller historiken först.
3. **Omritade distrikt**: bara mening och områdesrad (rekommendation) eller areaviktad skattning tydligt märkt.
4. **Partier med linjer**: V, S, MP, SD på mobil och M på desktop (rekommendation) eller annat urval.
5. **Valnatten**: textlänken "Ladda om" och tidsstämpel (rekommendation) eller automatisk hämtning var tredje minut.
6. **Efter valet**: om "Majorna mot Sverige" och "Röstdelningen" ska göras om till "Tre saker som skiljer Majorna" och om Partistyrka-läget ska tas bort, enligt konceptet "berättelsen först".
7. **Texter**: meningarna i toppsvaret och historiksektionen är redaktionella och skrivs av Daniel i konfig; de datamässiga standardmeningarna gäller tills dess, utom toppsvarets som utelämnas när nyckeln är tom.

## 12. Ordning och insats

Åtta dagar räcker inte till allt med marginal, och spår A avgör om 2026 kommer in alls. Planens uppdelning:

**Måste vara klart före 13 september.** Hela spår A (avsnitt 9 punkt 1 till 6), plus de delar av spår B som valnatten behöver: dynamiskt antal distrikt och geometri per år (avsnitt 4, krävs av spår A punkt 5), toppsvaret med statusraden (avsnitt 3 rad 0, ren HTML, Majornabons punkt 1 och 2 på valnatten), och kortets "Hur har det ändrats" för 2026 (meningen för de nio omritade och områdesraden, avsnitt 5) med det nya swing-schemat i `swing_2026`.

**Bör, om måste-delen är klar senast onsdag 9 september.** Sektionen "Majorna sedan 2006" (avsnitt 6) med `historik.json`, `distrikt_2006` och de två bilderna, samt `swing_2022` mot 2018 med kortets bakåtvända mening. Dessa rör laddningskoden i `valgrafik.js`; de byggs på en egen gren och mergas bara om torrkörningen i spår A punkt 6 går igenom med dem inne.

**Efter valet.** Valdata och polygoner för 2010 till 2018, årsväljare på kartan för historikåren om Daniel vill, kortningen av Om siffrorna, stillbilder av områdesserien, "Tre saker som skiljer Majorna", tvillingar, Göteborgskartan.

Daniel bad om historiken först. Planens rekommendation är ändå spår A först, eftersom det utan spår A inte finns någon 2026-punkt att haka på historiken, och eftersom felen i pipelinen (tom import som skriver över, swing på fel distrikt) blir synliga för läsarna först på valnatten.
